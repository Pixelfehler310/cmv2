from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.sessions.models import SessionContext, UserRole
from src.data.lib.monster import Monster
from src.campaigns.lib.campaign import Campaign
from src.campaigns.lib.character import Character
from ..engine.stat_calculator import calculate_proficiency_bonus

from ..engine.combat_state import get_active_combatant, next_turn, start_combat
from ..engine.initiative import InitiativeEntry
from ..engine.dice import DiceService
from ..engine.action_resolver import resolve_attack, resolve_healing, resolve_save_action
from ..engine.damage import apply_damage as engine_apply_damage
from ..engine.effect_engine import add_effect, remove_effect, tick_effects
from ..lib.content_models import ActionDefinitionRecord
from ..schemas.common import AbilityScores, Position, SpeedBlock
from ..schemas.encounter import EncounterState, MapState, MapToken
from ..schemas.instances import ActorInstance, ConditionInstance, EffectInstance
from ..schemas.enums import Ability, ActionType, ActorType, ConditionType, DamageType, DurationType
from ..schemas.definitions import ActionDefinition
from ..schemas.contracts import EffectDefinition as CanonicalEffectDefinition
from ..lib.combat_models import ActionLog, CombatantState, EncounterSession, TurnBudgetRecord
from ..lib.context_models import EncounterCatalogRecord, SceneCatalogRecord
from ..repositories.context_repository import ContextReadRepository, ContextReadRepositoryProtocol
from ..repositories.action_catalog_repository import (
    ActionCatalogRepository,
    ActionCatalogRepositoryProtocol,
)
from ..repositories.action_execution_repository import (
    ActionExecutionRepository,
    ActionExecutionRepositoryProtocol,
)
from ..repositories.encounter_session_repository import (
    EncounterSessionRepository,
    EncounterSessionRepositoryProtocol,
)
from ..domain.authorization import (
    AuthorizationResult,
    check_actor_exists,
    check_actor_alive,
    check_user_role_allowed,
    check_actor_ownership,
    check_turn_ownership,
    combine_authorization_checks,
)
from ..domain.action_economy import (
    normalize_action_type as normalize_domain_action_type,
    can_spend_action_budget,
    apply_action_budget_consumption,
    get_or_create_in_memory_budget,
)
from .validation import (
    resolve_action_family,
    build_action_definition,
    parse_condition,
    parse_damage_type,
    safe_int,
    safe_int_list,
    display_name_from_slug,
    next_actor_id,
    normalize_preview_denial_reason,
    effect_provenance_payload,
    effect_instance_canonical_id,
    collect_effect_provenance_by_instance,
    ACTION_FAMILY_ATTACK,
    ACTION_FAMILY_SAVE,
    ACTION_FAMILY_HEALING,
    ACTION_FAMILY_UTILITY,
)


@dataclass
class MovementPreviewResult:
    allowed: bool
    reason_code: str | None = None
    message: str | None = None
    actor_id: str | None = None
    origin: dict[str, int] | None = None
    movement_remaining: int = 0
    reachable: list[dict[str, int]] | None = None


@dataclass
class ExecutableActionsSnapshotResult:
    allowed: bool
    reason_code: str | None = None
    message: str | None = None
    actor_id: str | None = None
    actions: list[dict[str, Any]] | None = None
    turn_budget: dict[str, Any] | None = None


@dataclass
class AttackPreviewResult:
    allowed: bool
    reason_code: str | None = None
    message: str | None = None
    actor_id: str | None = None
    action_id: str | None = None
    origin: dict[str, int] | None = None
    eligible_target_ids: list[str] | None = None
    eligible_cells: list[dict[str, int]] | None = None
    template_projection: dict[str, Any] | None = None


@dataclass
class ActionExecutionMetadataResult:
    found: bool
    actor_id: str | None = None
    action_id: str | None = None
    action_type_cost: str | None = None
    family: str | None = None
    targeting_mode: str | None = None
    range: int | None = None
    save_context: dict[str, Any] | None = None
    attack_context: dict[str, Any] | None = None
    effect_intents: list[dict[str, Any]] | None = None


class CombatService:
    """Authoritative combat lifecycle + persistence orchestration for DnD5e."""

    DEFAULT_SCENE_ID = "scene.default"
    FIXTURE_ENCOUNTERS_DIR = Path(__file__).resolve(
    ).parents[4] / "data" / "fixtures" / "encounters"

    def __init__(
        self,
        db: AsyncSession,
        context_read_repository: ContextReadRepositoryProtocol | None = None,
        encounter_session_repository: EncounterSessionRepositoryProtocol | None = None,
        action_catalog_repository: ActionCatalogRepositoryProtocol | None = None,
        action_execution_repository: ActionExecutionRepositoryProtocol | None = None,
    ):
        self.db = db
        self._context_read_repository = context_read_repository or ContextReadRepository(db)
        self._encounter_session_repository = encounter_session_repository or EncounterSessionRepository(db)
        self._action_catalog_repository = action_catalog_repository or ActionCatalogRepository(db)
        self._action_execution_repository = action_execution_repository or ActionExecutionRepository(db)

    async def load_or_create_encounter_state(self, campaign_id: str) -> tuple[EncounterSession, EncounterState]:
        campaign = await self._load_campaign_with_characters(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign {campaign_id} does not exist")

        await self._ensure_context_catalog(campaign)
        if not campaign.active_encounter_id:
            raise RuntimeError(
                "No active encounter selected for this campaign. DM must select campaign context first."
            )

        active_scene_id = campaign.current_scene or self.DEFAULT_SCENE_ID
        selected_catalog = await self._load_catalog_encounter(
            campaign_id,
            active_scene_id,
            campaign.active_encounter_id,
        )
        if selected_catalog is None:
            raise RuntimeError(
                "Selected encounter is not available in catalog. DM must select a valid encounter first."
            )

        session = await self._load_session(campaign_id)
        if session is None:
            encounter = EncounterState.model_validate(
                selected_catalog.state_json)
            session = EncounterSession(
                campaign_id=campaign_id,
                scene_id=active_scene_id,
                encounter_id=encounter.id,
                phase=encounter.turn_phase,
                round_number=encounter.round_number,
                active_index=encounter.active_index,
                combat_state_json=encounter.model_dump(mode="json"),
            )
            self.db.add(session)
            await self.db.flush()
            await self._sync_combatants(session, encounter)
            await self.db.commit()
            return session, encounter

        if session.encounter_id != campaign.active_encounter_id or session.scene_id != active_scene_id:
            encounter = EncounterState.model_validate(
                selected_catalog.state_json)
            session.scene_id = active_scene_id
            await self._persist_encounter(session, encounter)
            return session, encounter

        # If session exists, load the campaign to ensure we have character context
        # (Though character instances are already in combat_state_json or combatants table)
        if session.combat_state_json:
            encounter = EncounterState.model_validate(
                session.combat_state_json)
        else:
            encounter = self._encounter_from_rows(session)

        await self._refresh_turn_budgets_on_encounter(encounter, session)
        return session, encounter

    async def list_scenes(self, campaign_id: str) -> list[SceneCatalogRecord]:
        campaign = await self._load_campaign_with_characters(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign {campaign_id} does not exist")

        await self._ensure_context_catalog(campaign)
        return await self._context_read_repository.list_scenes(campaign_id)

    async def list_encounters(self, campaign_id: str, scene_id: str) -> list[EncounterCatalogRecord]:
        campaign = await self._load_campaign_with_characters(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign {campaign_id} does not exist")

        await self._ensure_context_catalog(campaign)
        return await self._context_read_repository.list_scene_encounters(campaign_id, scene_id)

    async def select_context(self, campaign_id: str, scene_id: str, encounter_id: str) -> Campaign:
        campaign = await self._load_campaign_with_characters(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign {campaign_id} does not exist")

        await self._ensure_context_catalog(campaign)
        if not await self._context_read_repository.encounter_exists(campaign_id, scene_id, encounter_id):
            raise ValueError(
                "Scene/encounter combination does not exist for campaign")

        return await self._encounter_session_repository.persist_context_selection(
            campaign=campaign,
            scene_id=scene_id,
            encounter_id=encounter_id,
        )

    async def get_context(self, campaign_id: str) -> Campaign:
        campaign = await self._load_campaign_with_characters(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign {campaign_id} does not exist")

        await self._ensure_context_catalog(campaign)
        return campaign

    async def reset_encounter_state(self, campaign_id: str) -> bool:
        """Deletes the existing encounter session for a campaign, forcing an initialization refresh."""
        from src.systems.dnd5e.lib.combat_models import EncounterSession
        from sqlalchemy import delete

        stmt = delete(EncounterSession).where(
            EncounterSession.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def start_combat(self, encounter_session: EncounterSession, encounter: EncounterState) -> list[dict[str, str]]:
        initiatives: list[InitiativeEntry] = []
        for idx, actor in enumerate(encounter.combatants):
            # Deterministic fallback keeps behavior stable in tests.
            initiatives.append(
                InitiativeEntry(actor_id=actor.id, roll=max(
                    1, 20 - idx), dex_score=actor.abilities.dexterity)
            )

        start_combat(encounter, initiatives)
        await self._persist_encounter(encounter_session, encounter)
        await self._ensure_round_budgets(encounter_session, encounter)

        return [{"actor_id": actor.id, "name": actor.name} for actor in encounter.combatants]

    async def advance_turn(self, encounter_session: EncounterSession, encounter: EncounterState) -> tuple[str, int]:
        next_turn(encounter)
        await self.on_turn_started(encounter_session, encounter)
        await self._persist_encounter(encounter_session, encounter)
        await self._ensure_round_budgets(encounter_session, encounter)

        active = get_active_combatant(encounter)
        active_id = active.id if active else ""
        return active_id, encounter.round_number

    async def apply_movement(
        self,
        encounter_session: EncounterSession | None,
        encounter: EncounterState,
        ctx: SessionContext,
        actor_id: str,
        path: list[dict[str, int]],
        request_id: str | None,
    ) -> AuthorizationResult:
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return AuthorizationResult(False, "invalid_target", f"Actor {actor_id} not found")

        checks = await self._base_actor_checks(encounter_session, encounter, actor_id, "move", ctx)
        if not checks.allowed:
            if encounter_session is not None:
                await self.log_action_attempt(
                    encounter_session,
                    request_id=request_id,
                    actor_id=actor_id,
                    action_type="move",
                    action_state="denied",
                    payload={"path": path},
                    checks=checks.checks or {},
                    denial_reason=checks.reason_code,
                )
            return checks

        distance = self._path_distance(actor.position, path)
        if encounter_session is None:
            budget_state = self._get_or_create_in_memory_budget(
                encounter, actor_id)
            movement_remaining = max(
                int(budget_state["max_movement"]) - int(budget_state["movement_used"]), 0)
        else:
            budget = await self._get_or_create_budget(encounter_session, actor_id, encounter.round_number, actor.speed.walk)
            movement_remaining = max(
                budget.max_movement - budget.movement_used, 0)

        if distance > movement_remaining:
            checks_data = checks.checks or {}
            checks_data["movement_remaining"] = movement_remaining
            checks_data["movement_required"] = distance
            if encounter_session is not None:
                await self.log_action_attempt(
                    encounter_session,
                    request_id=request_id,
                    actor_id=actor_id,
                    action_type="move",
                    action_state="denied",
                    payload={"path": path},
                    checks=checks_data,
                    denial_reason="movement_exceeded",
                )
            return AuthorizationResult(
                False,
                "movement_exhausted",
                "Movement exceeds remaining budget",
                checks=checks_data,
            )

        if encounter_session is None:
            budget_state["movement_used"] = int(
                budget_state["movement_used"]) + distance
            budget_state["movement_remaining"] = max(
                int(budget_state["max_movement"]) -
                int(budget_state["movement_used"]),
                0,
            )
        else:
            budget.movement_used += distance
            await self.db.flush()
            await self.log_action_attempt(
                encounter_session,
                request_id=request_id,
                actor_id=actor_id,
                action_type="move",
                action_state="authorized",
                payload={"path": path},
                checks={
                    **(checks.checks or {}),
                    "movement_required": distance,
                    "movement_remaining": max(budget.max_movement - budget.movement_used, 0),
                },
                denial_reason=None,
            )

        return AuthorizationResult(True, checks=checks.checks)

    async def get_movement_preview(
        self,
        encounter_session: EncounterSession | None,
        encounter: EncounterState,
        ctx: SessionContext,
        actor_id: str,
    ) -> MovementPreviewResult:
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return MovementPreviewResult(False, "invalid_target", f"Actor {actor_id} not found")

        checks = await self._base_actor_checks(encounter_session, encounter, actor_id, "move", ctx)
        if not checks.allowed:
            return MovementPreviewResult(False, checks.reason_code, checks.message)

        if encounter_session is None:
            budget_state = self._get_or_create_in_memory_budget(
                encounter, actor_id)
            movement_remaining = max(
                int(budget_state.get("max_movement", actor.speed.walk)) -
                int(budget_state.get("movement_used", 0)),
                0,
            )
        else:
            budget = await self._get_or_create_budget(
                encounter_session,
                actor_id,
                encounter.round_number,
                actor.speed.walk,
            )
            movement_remaining = max(
                budget.max_movement - budget.movement_used, 0)

        origin_x = int(actor.position.x)
        origin_y = int(actor.position.y)

        reachable: list[dict[str, int]] = []
        for x in range(encounter.map.width):
            for y in range(encounter.map.height):
                distance = abs(origin_x - x) + abs(origin_y - y)
                if distance <= movement_remaining:
                    reachable.append({"x": x, "y": y})

        return MovementPreviewResult(
            allowed=True,
            actor_id=actor_id,
            origin={"x": origin_x, "y": origin_y},
            movement_remaining=movement_remaining,
            reachable=reachable,
        )

    async def get_executable_actions_snapshot(
        self,
        encounter_session: EncounterSession | None,
        encounter: EncounterState,
        ctx: SessionContext,
        actor_id: str,
    ) -> ExecutableActionsSnapshotResult:
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return ExecutableActionsSnapshotResult(False, "invalid_target", f"Actor {actor_id} not found")

        if ctx.role == UserRole.SPECTATOR:
            return ExecutableActionsSnapshotResult(False, "unauthorized", "Spectators cannot request executable actions")

        combatant = None
        if encounter_session is not None:
            combatant = await self._load_combatant(encounter_session.id, actor_id)

        owner_user_id = combatant.owner_user_id if combatant else actor.owner_user_id
        if ctx.role == UserRole.PLAYER and owner_user_id and owner_user_id != ctx.user_id:
            return ExecutableActionsSnapshotResult(False, "unauthorized", "Player does not own this actor")

        candidates = await self._build_bound_action_candidates(actor)

        actions: list[dict[str, Any]] = []
        for candidate in candidates:
            action_type_cost = self.normalize_action_type(
                str(candidate.get("action_type_cost") or "action")
            )
            availability = await self.check_can_act(
                encounter_session,
                encounter,
                actor_id,
                action_type_cost,
                ctx,
            )
            actions.append(
                {
                    "action_id": candidate["action_id"],
                    "label": candidate["label"],
                    "family": candidate["family"],
                    "action_type_cost": action_type_cost,
                    "is_available": availability.allowed,
                    "unavailable_reason": None if availability.allowed else availability.reason_code,
                    "targeting_mode": candidate["targeting_mode"],
                    "range": candidate["range"],
                    "name": str(candidate.get("name") or candidate["label"]),
                    "save_context": candidate.get("save_context"),
                    "attack_context": candidate.get("attack_context"),
                    "resource_costs": list(candidate.get("resource_costs") or []),
                    "effect_intents": list(candidate.get("effect_intents") or []),
                    "tags": list(candidate.get("tags") or []),
                    "source_ref": str(candidate.get("source_ref") or "custom"),
                    "content_version": str(candidate.get("content_version") or "1"),
                    "enabled": bool(candidate.get("enabled", True)),
                }
            )

        turn_budget = await self.get_turn_budget_snapshot(encounter_session, encounter)
        return ExecutableActionsSnapshotResult(
            allowed=True,
            actor_id=actor_id,
            actions=actions,
            turn_budget=turn_budget,
        )

    async def get_attack_preview(
        self,
        encounter_session: EncounterSession | None,
        encounter: EncounterState,
        ctx: SessionContext,
        actor_id: str,
        action_id: str,
        template_origin: dict[str, int] | None = None,
        template_direction: dict[str, int] | None = None,
    ) -> AttackPreviewResult:
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return AttackPreviewResult(False, "invalid_target", f"Actor {actor_id} not found")

        candidates = await self._build_bound_action_candidates(actor)
        candidate = next((entry for entry in candidates if str(
            entry.get("action_id")) == action_id), None)
        if candidate is None:
            return AttackPreviewResult(False, "invalid_action", f"Unknown action_id '{action_id}' for actor {actor_id}")

        action_type_cost = self.normalize_action_type(
            str(candidate.get("action_type_cost") or "action"))
        checks = await self.check_can_act(
            encounter_session,
            encounter,
            actor_id,
            action_type_cost,
            ctx,
        )
        if not checks.allowed:
            return AttackPreviewResult(False, checks.reason_code, checks.message)

        origin_x = int(actor.position.x)
        origin_y = int(actor.position.y)

        targeting_mode = str(candidate.get(
            "targeting_mode") or "single_target")
        raw_range = candidate.get("range")
        action_range: int | None
        if isinstance(raw_range, (int, float)):
            action_range = int(raw_range)
        elif isinstance(raw_range, str) and raw_range.strip().isdigit():
            action_range = int(raw_range.strip())
        else:
            action_range = None

        eligible_target_ids: list[str] = []
        eligible_cells: list[dict[str, int]] = []
        template_projection: dict[str, Any] | None = None

        if targeting_mode == "self":
            eligible_target_ids.append(actor_id)
            eligible_cells.append({"x": origin_x, "y": origin_y})
        elif targeting_mode == "aoe":
            template_shape = str(candidate.get("aoe_shape")
                                 or "sphere").strip().lower() or "sphere"
            template_size = self._coerce_positive_int(
                candidate.get("aoe_size"), fallback=1)

            potential_origins = self._cells_within_range(
                encounter.map.width,
                encounter.map.height,
                origin_x,
                origin_y,
                action_range,
            )
            eligible_cells = [{"x": x, "y": y} for (x, y) in potential_origins]

            selected_origin = self._normalize_cell(template_origin)
            if selected_origin is None:
                selected_origin = {"x": origin_x, "y": origin_y}

            if not self._is_cell_in_bounds(encounter.map.width, encounter.map.height, selected_origin["x"], selected_origin["y"]):
                return AttackPreviewResult(False, "invalid_template_origin", "Template origin is out of map bounds")

            if (selected_origin["x"], selected_origin["y"]) not in potential_origins:
                return AttackPreviewResult(False, "template_out_of_range", "Template origin is out of action range")

            normalized_direction = self._normalize_direction(
                template_direction)
            if normalized_direction is None:
                normalized_direction = self._direction_from_points(
                    {"x": origin_x, "y": origin_y},
                    selected_origin,
                )

            affected_points = self._project_template_cells(
                encounter.map.width,
                encounter.map.height,
                template_shape,
                template_size,
                selected_origin,
                normalized_direction,
            )
            affected_cells = [{"x": x, "y": y} for (x, y) in affected_points]

            affected_set = set(affected_points)
            for target in encounter.combatants:
                if target.current_hp <= 0:
                    continue
                target_cell = (int(target.position.x), int(target.position.y))
                if target_cell in affected_set:
                    eligible_target_ids.append(target.id)

            template_projection = {
                "shape": template_shape,
                "size": template_size,
                "origin": {"x": selected_origin["x"], "y": selected_origin["y"]},
                "direction": {"x": normalized_direction["x"], "y": normalized_direction["y"]},
                "affected_cells": affected_cells,
            }
        else:
            for target in encounter.combatants:
                if target.id == actor_id:
                    continue
                if target.current_hp <= 0:
                    continue

                target_x = int(target.position.x)
                target_y = int(target.position.y)
                distance = abs(origin_x - target_x) + abs(origin_y - target_y)
                if action_range is not None and distance > action_range:
                    continue

                eligible_target_ids.append(target.id)
                eligible_cells.append({"x": target_x, "y": target_y})

        return AttackPreviewResult(
            allowed=True,
            actor_id=actor_id,
            action_id=action_id,
            origin={"x": origin_x, "y": origin_y},
            eligible_target_ids=eligible_target_ids,
            eligible_cells=eligible_cells,
            template_projection=template_projection,
        )

    async def get_action_execution_metadata(
        self,
        encounter: EncounterState,
        actor_id: str,
        action_id: str,
    ) -> ActionExecutionMetadataResult:
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return ActionExecutionMetadataResult(found=False, actor_id=actor_id, action_id=action_id)

        candidates = await self._build_bound_action_candidates(actor)

        candidate = next((entry for entry in candidates if str(
            entry.get("action_id")) == action_id), None)
        if candidate is None:
            return ActionExecutionMetadataResult(found=False, actor_id=actor_id, action_id=action_id)

        raw_family = str(candidate.get("family") or "").strip().lower()
        if raw_family not in {"attack", "save", "healing", "utility"}:
            raw_family = "utility"

        raw_range = candidate.get("range")
        normalized_range: int | None = None
        if isinstance(raw_range, (int, float)):
            normalized_range = int(raw_range)
        elif isinstance(raw_range, str) and raw_range.strip().isdigit():
            normalized_range = int(raw_range.strip())

        save_context = candidate.get("save_context")
        attack_context = candidate.get("attack_context")
        effect_intents = candidate.get("effect_intents")

        return ActionExecutionMetadataResult(
            found=True,
            actor_id=actor_id,
            action_id=action_id,
            action_type_cost=self.normalize_action_type(
                str(candidate.get("action_type_cost") or "action")),
            family=raw_family,
            targeting_mode=self._normalize_targeting_mode(
                str(candidate.get("targeting_mode") or "single_target")),
            range=normalized_range,
            save_context=save_context if isinstance(
                save_context, dict) else None,
            attack_context=attack_context if isinstance(
                attack_context, dict) else None,
            effect_intents=list(effect_intents) if isinstance(
                effect_intents, list) else [],
        )

    async def check_can_act(
        self,
        encounter_session: EncounterSession | None,
        encounter: EncounterState,
        actor_id: str,
        action_type: str,
        ctx: SessionContext,
    ) -> AuthorizationResult:
        action_type_normalized = self.normalize_action_type(action_type)
        checks = await self._base_actor_checks(encounter_session, encounter, actor_id, action_type_normalized, ctx)
        if not checks.allowed:
            return checks

        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return AuthorizationResult(False, "invalid_target", f"Actor {actor_id} not found")

        if encounter_session is None:
            budget_state = self._get_or_create_in_memory_budget(
                encounter, actor_id)
            action_available = bool(budget_state.get("action_available", True))
            bonus_action_available = bool(
                budget_state.get("bonus_action_available", True))
            reaction_available = bool(
                budget_state.get("reaction_available", True))
        else:
            budget = await self._get_or_create_budget(
                encounter_session,
                actor_id,
                encounter.round_number,
                actor.speed.walk,
            )
            action_available = budget.action_available
            bonus_action_available = budget.bonus_action_available
            reaction_available = budget.reaction_available

        checks_data = checks.checks or {}
        budget_check = can_spend_action_budget(
            action_type=action_type_normalized,
            action_available=action_available,
            bonus_action_available=bonus_action_available,
            reaction_available=reaction_available,
        )
        if not budget_check.allowed:
            if budget_check.check_key:
                checks_data[budget_check.check_key] = False
            return AuthorizationResult(False, budget_check.reason_code, budget_check.message, checks_data)

        return AuthorizationResult(True, checks=checks_data)

    async def consume_budget(
        self,
        encounter_session: EncounterSession | None,
        encounter: EncounterState,
        actor_id: str,
        action_type: str,
    ) -> None:
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return

        normalized = self.normalize_action_type(action_type)

        if encounter_session is None:
            budget_state = self._get_or_create_in_memory_budget(
                encounter, actor_id)
            apply_action_budget_consumption(normalized, budget_state)
            return

        budget = await self._get_or_create_budget(encounter_session, actor_id, encounter.round_number, actor.speed.walk)
        budget_state = {
            "action_available": budget.action_available,
            "bonus_action_available": budget.bonus_action_available,
            "reaction_available": budget.reaction_available,
            "max_movement": budget.max_movement,
            "movement_used": budget.movement_used,
        }
        updated_budget = apply_action_budget_consumption(normalized, budget_state)
        budget.action_available = bool(updated_budget.get("action_available", budget.action_available))
        budget.bonus_action_available = bool(updated_budget.get("bonus_action_available", budget.bonus_action_available))
        budget.reaction_available = bool(updated_budget.get("reaction_available", budget.reaction_available))

        await self._action_execution_repository.flush()

    async def on_turn_started(self, encounter_session: EncounterSession | None, encounter: EncounterState) -> None:
        """Sync turn budget semantics when a new active actor's turn begins."""
        active = get_active_combatant(encounter)
        if active is None:
            return

        if encounter_session is None:
            budget_state = self._get_or_create_in_memory_budget(
                encounter, active.id)
            budget_state["reaction_available"] = True
            return

        budget = await self._get_or_create_budget(
            encounter_session,
            active.id,
            encounter.round_number,
            active.speed.walk,
        )
        budget.reaction_available = True
        await self._action_execution_repository.flush()

    async def get_turn_budget_snapshot(self, encounter_session: EncounterSession | None, encounter: EncounterState) -> dict[str, Any]:
        if encounter_session is None:
            for actor in encounter.combatants:
                self._get_or_create_in_memory_budget(encounter, actor.id)
        else:
            await self._refresh_turn_budgets_on_encounter(encounter, encounter_session)

        active = get_active_combatant(encounter)
        return {
            "round": encounter.round_number,
            "turn_phase": encounter.turn_phase,
            "active_actor_id": active.id if active else None,
            "budgets": encounter.turn_budgets,
        }

    @staticmethod
    def normalize_action_type(action_type: str) -> str:
        return normalize_domain_action_type(action_type)

    async def log_action_attempt(
        self,
        encounter_session: EncounterSession,
        request_id: str | None,
        actor_id: str,
        action_type: str,
        action_state: str,
        payload: dict[str, Any],
        checks: dict[str, Any],
        denial_reason: str | None,
    ) -> None:
        await self._action_execution_repository.create_action_log(
            encounter_session=encounter_session,
            request_id=request_id,
            actor_id=actor_id,
            action_type=action_type,
            action_state=action_state,
            payload=payload,
            checks=checks,
            denial_reason=denial_reason,
        )

    async def get_action_log(self, campaign_id: str, limit: int = 100) -> list[ActionLog]:
        return await self._action_execution_repository.list_action_logs(campaign_id, limit)

    async def save_full_state(self, encounter_session: EncounterSession, encounter: EncounterState) -> None:
        await self._persist_encounter(encounter_session, encounter)

    async def _load_session(self, campaign_id: str) -> EncounterSession | None:
        stmt = (
            select(EncounterSession)
            .options(
                selectinload(EncounterSession.combatants),
                selectinload(EncounterSession.turn_budgets),
            )
            .where(EncounterSession.campaign_id == campaign_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _persist_encounter(self, encounter_session: EncounterSession, encounter: EncounterState) -> None:
        await self._action_execution_repository.persist_encounter(encounter_session, encounter)

    async def _sync_combatants(self, encounter_session: EncounterSession, encounter: EncounterState) -> None:
        # Load existing combatant states to avoid unnecessary delete-orphans of turn budgets
        existing_result = await self.db.execute(
            select(CombatantState).where(
                CombatantState.encounter_session_id == encounter_session.id
            )
        )
        existing_combatants = {
            c.actor_id: c for c in existing_result.scalars().all()}

        current_actor_ids = {actor.id for actor in encounter.combatants}

        # 1. Remove combatants no longer in the encounter
        for aid, combatant in list(existing_combatants.items()):
            if aid not in current_actor_ids:
                # Some async wrappers might return a coroutine for delete,
                # but in standard SQLAlchemy it's synchronous.
                # To be safe and satisfy lints if it IS a coroutine (rare):
                res = self.db.delete(combatant)
                if hasattr(res, "__await__"):
                    await res
                del existing_combatants[aid]

        # 2. Update or Create
        for index, actor in enumerate(encounter.combatants):
            combatant = existing_combatants.get(actor.id)
            if combatant is None:
                combatant = CombatantState(
                    encounter_session_id=encounter_session.id,
                    actor_id=actor.id,
                )
                self.db.add(combatant)

            combatant.initiative_order = index
            combatant.owner_user_id = actor.owner_user_id
            combatant.current_hp = actor.current_hp
            combatant.max_hp = actor.max_hp
            combatant.pos_x = actor.position.x
            combatant.pos_y = actor.position.y
            combatant.actor_snapshot = actor.model_dump(mode="json")

        await self.db.flush()

    async def _ensure_round_budgets(self, encounter_session: EncounterSession, encounter: EncounterState) -> None:
        for actor in encounter.combatants:
            await self._get_or_create_budget(encounter_session, actor.id, encounter.round_number, actor.speed.walk)

        await self._action_execution_repository.commit()

    async def _refresh_turn_budgets_on_encounter(
        self,
        encounter: EncounterState,
        encounter_session: EncounterSession,
    ) -> None:
        for actor in encounter.combatants:
            budget = await self._get_or_create_budget(
                encounter_session,
                actor.id,
                encounter.round_number,
                actor.speed.walk,
            )
            remaining = max(budget.max_movement - budget.movement_used, 0)
            encounter.turn_budgets[actor.id] = {
                "action_available": budget.action_available,
                "bonus_action_available": budget.bonus_action_available,
                "reaction_available": budget.reaction_available,
                "max_movement": budget.max_movement,
                "movement_used": budget.movement_used,
                "movement_remaining": remaining,
            }

    async def _get_or_create_budget(
        self,
        encounter_session: EncounterSession,
        actor_id: str,
        round_number: int,
        max_movement: int,
    ) -> TurnBudgetRecord:
        return await self._action_execution_repository.get_or_create_budget(
            encounter_session=encounter_session,
            actor_id=actor_id,
            round_number=round_number,
            max_movement=max_movement,
        )

    async def _load_combatant(self, encounter_session_id: str, actor_id: str) -> CombatantState | None:
        return await self._action_execution_repository.load_combatant(encounter_session_id, actor_id)

    async def _load_monster_for_actor(self, actor: ActorInstance) -> Monster | None:
        candidates: list[str] = []
        if actor.name.strip():
            candidates.append(actor.name.strip())

        definition_slug = actor.definition_slug.strip()
        if definition_slug:
            candidates.append(self._display_name_from_slug(definition_slug))

        lowered_candidates = {value.lower() for value in candidates if value}
        if not lowered_candidates:
            return None

        predicates = [func.lower(Monster.name).in_(list(lowered_candidates))]
        if definition_slug:
            lowered_slug = definition_slug.lower()
            predicates.append(func.lower(func.replace(
                Monster.name, " ", "_")) == lowered_slug)
            predicates.append(func.lower(func.replace(
                Monster.name, " ", "-")) == lowered_slug)

        stmt = select(Monster).where(or_(*predicates)).limit(1)
        try:
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            # Snapshot projection must still work in in-memory/offline modes.
            return None

    async def _build_bound_action_candidates(self, actor: ActorInstance) -> list[dict[str, Any]]:
        template_candidates = self._binding_template_candidates(actor)

        try:
            bindings = await self._action_catalog_repository.list_bindings_for_actor(
                actor_id=actor.id,
                template_candidates=template_candidates,
            )
        except Exception:
            # Fallback is handled by legacy candidate projection.
            return []

        if not bindings:
            return []

        # Runtime actor-specific bindings win over template-level bindings.
        bindings.sort(
            key=lambda binding: (
                1 if binding.actor_id == actor.id else 0,
                1 if binding.actor_template_id and binding.actor_template_id in template_candidates else 0,
            ),
            reverse=True,
        )

        action_ids = [
            binding.action_id for binding in bindings if binding.action_id]
        if not action_ids:
            return []

        try:
            action_defs = await self._action_catalog_repository.list_action_definitions_by_ids(action_ids)
        except Exception:
            return []

        action_by_id = {action.action_id: action for action in action_defs}
        projected: list[dict[str, Any]] = []
        seen_action_ids: set[str] = set()

        for binding in bindings:
            action = action_by_id.get(binding.action_id)
            if action is None:
                continue
            if action.action_id in seen_action_ids:
                continue

            projected.append(
                self._build_candidate_from_action_definition(
                    action,
                    binding.override_payload,
                )
            )
            seen_action_ids.add(action.action_id)

        return projected

    @staticmethod
    def _binding_template_candidates(actor: ActorInstance) -> list[str]:
        candidates: list[str] = []

        definition_slug = (actor.definition_slug or "").strip().lower()
        if definition_slug:
            candidates.append(definition_slug)

        name = (actor.name or "").strip().lower()
        if name:
            name_slug = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
            if name_slug:
                candidates.append(name_slug)

            first_word_slug = re.sub(
                r"[^a-z0-9]+", "_", name.split()[0]).strip("_")
            if first_word_slug:
                candidates.append(first_word_slug)

        # Keep deterministic order while removing duplicates.
        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            deduped.append(candidate)
            seen.add(candidate)
        return deduped

    def _build_candidate_from_action_definition(
        self,
        action: ActionDefinitionRecord,
        override_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        attack_context = action.attack_context if isinstance(
            action.attack_context, dict) else None
        save_context = action.save_context if isinstance(
            action.save_context, dict) else None

        template_shape: str | None = None
        template_size: int | None = None
        for context_payload in (attack_context, save_context):
            if not isinstance(context_payload, dict):
                continue
            raw_shape = context_payload.get(
                "aoe_shape") or context_payload.get("shape")
            raw_size = context_payload.get(
                "aoe_size") or context_payload.get("size")
            if isinstance(raw_shape, str) and raw_shape.strip() and template_shape is None:
                template_shape = raw_shape.strip().lower()
            if raw_size is not None and template_size is None:
                template_size = self._coerce_positive_int(raw_size, fallback=1)

        candidate: dict[str, Any] = {
            "action_id": action.action_id,
            "name": action.name,
            "label": action.name,
            "family": action.family,
            "action_type_cost": self.normalize_action_type(action.action_type_cost),
            "targeting_mode": self._normalize_targeting_mode(action.targeting_mode),
            "range": action.range,
            "save_context": save_context,
            "attack_context": attack_context,
            "resource_costs": list(action.resource_costs or []),
            "effect_intents": list(action.effect_intents or []),
            "tags": list(action.tags or []),
            "source_ref": action.source_ref,
            "content_version": action.content_version,
            "enabled": bool(action.enabled),
            "aoe_shape": template_shape,
            "aoe_size": template_size,
        }

        if isinstance(override_payload, dict):
            override_name = override_payload.get("name")
            if isinstance(override_name, str) and override_name.strip():
                candidate["name"] = override_name.strip()
                candidate["label"] = override_name.strip()

            override_label = override_payload.get("label")
            if isinstance(override_label, str) and override_label.strip():
                candidate["label"] = override_label.strip()

            override_family = override_payload.get("family")
            if isinstance(override_family, str) and override_family.strip():
                candidate["family"] = override_family.strip().lower()

            override_action_type = override_payload.get("action_type_cost")
            if isinstance(override_action_type, str) and override_action_type.strip():
                candidate["action_type_cost"] = self.normalize_action_type(
                    override_action_type)

            override_targeting_mode = override_payload.get("targeting_mode")
            if isinstance(override_targeting_mode, str) and override_targeting_mode.strip():
                candidate["targeting_mode"] = self._normalize_targeting_mode(
                    override_targeting_mode)

            override_range = override_payload.get("range")
            if isinstance(override_range, (int, float)):
                candidate["range"] = int(override_range)

            if isinstance(override_payload.get("save_context"), dict):
                candidate["save_context"] = override_payload["save_context"]
            if isinstance(override_payload.get("attack_context"), dict):
                candidate["attack_context"] = override_payload["attack_context"]
            if isinstance(override_payload.get("resource_costs"), list):
                candidate["resource_costs"] = override_payload["resource_costs"]
            if isinstance(override_payload.get("effect_intents"), list):
                candidate["effect_intents"] = override_payload["effect_intents"]
            if isinstance(override_payload.get("tags"), list):
                candidate["tags"] = [str(tag)
                                     for tag in override_payload["tags"]]

            override_source_ref = override_payload.get("source_ref")
            if isinstance(override_source_ref, str) and override_source_ref.strip():
                candidate["source_ref"] = override_source_ref.strip()

            override_version = override_payload.get("content_version")
            if isinstance(override_version, str) and override_version.strip():
                candidate["content_version"] = override_version.strip()

            override_shape = override_payload.get(
                "aoe_shape") or override_payload.get("shape")
            if isinstance(override_shape, str) and override_shape.strip():
                candidate["aoe_shape"] = override_shape.strip().lower()
            if override_payload.get("aoe_size") is not None:
                candidate["aoe_size"] = self._coerce_positive_int(
                    override_payload.get("aoe_size"), fallback=1)

        return candidate

    def _build_action_candidates(self, actor: ActorInstance, monster: Monster | None) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []

        if monster is not None:
            for index, entry in enumerate(monster.actions or []):
                if not isinstance(entry, dict):
                    continue
                label = str(entry.get("name") or "").strip(
                ) or f"Action {index + 1}"
                description = str(entry.get("description")
                                  or entry.get("desc") or "")
                aoe_template = self._infer_aoe_template(description)
                candidates.append(
                    {
                        "action_id": f"action_{index + 1}_{self._slugify(label)}",
                        "label": label,
                        "family": self._infer_action_family(label, description),
                        "action_type_cost": "action",
                        "targeting_mode": self._infer_targeting_mode(description),
                        "range": self._infer_action_range(description),
                        "aoe_shape": aoe_template[0] if aoe_template else None,
                        "aoe_size": aoe_template[1] if aoe_template else None,
                    }
                )

            for index, entry in enumerate(monster.special_abilities or []):
                if not isinstance(entry, dict):
                    continue
                label = str(entry.get("name") or "").strip(
                ) or f"Special {index + 1}"
                description = str(entry.get("description")
                                  or entry.get("desc") or "")
                lowered = description.lower()
                action_type_cost = ""
                if "bonus action" in lowered:
                    action_type_cost = "bonus_action"
                elif "reaction" in lowered:
                    action_type_cost = "reaction"

                if not action_type_cost:
                    continue

                aoe_template = self._infer_aoe_template(description)
                candidates.append(
                    {
                        "action_id": f"special_{index + 1}_{self._slugify(label)}",
                        "label": label,
                        "family": self._infer_action_family(label, description),
                        "action_type_cost": action_type_cost,
                        "targeting_mode": self._infer_targeting_mode(description),
                        "range": self._infer_action_range(description),
                        "aoe_shape": aoe_template[0] if aoe_template else None,
                        "aoe_size": aoe_template[1] if aoe_template else None,
                    }
                )

        if candidates:
            return candidates

        return [
            {
                "action_id": "basic_attack",
                "label": f"{actor.name or 'Actor'} Attack",
                "family": "attack",
                "action_type_cost": "action",
                "targeting_mode": "single_target",
                "range": 5,
                "aoe_shape": None,
                "aoe_size": None,
            }
        ]

    @staticmethod
    def _display_name_from_slug(definition_slug: str) -> str:
        cleaned = re.sub(r"[_-]+", " ", definition_slug).strip()
        if not cleaned:
            return ""
        return " ".join(part.capitalize() for part in cleaned.split())

    @staticmethod
    def _slugify(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "action"

    @staticmethod
    def _infer_action_family(label: str, description: str) -> str:
        text = f"{label} {description}".lower()
        if any(token in text for token in ("weapon attack", "spell attack", "to hit", "hit:")):
            return "attack"
        if "save" in text or "saving throw" in text:
            return "save"
        if any(token in text for token in ("heal", "regain", "restore")):
            return "healing"
        return "utility"

    @staticmethod
    def _infer_targeting_mode(description: str) -> str:
        lowered = description.lower()
        if "one target" in lowered:
            return "single_target"
        if "each creature" in lowered or "all creatures" in lowered:
            return "aoe"
        if "line" in lowered or "cone" in lowered or "sphere" in lowered or "cube" in lowered or "cylinder" in lowered:
            return "aoe"
        if "self" in lowered:
            return "self"
        return "single_target"

    @staticmethod
    def _normalize_targeting_mode(value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized in {"single_target", "aoe", "self"}:
            return normalized
        return "single_target"

    @staticmethod
    def _infer_action_range(description: str) -> int | None:
        reach_match = re.search(r"reach\s+(\d+)\s*ft",
                                description, flags=re.IGNORECASE)
        if reach_match:
            return int(reach_match.group(1))

        range_match = re.search(
            r"range\s+(\d+)(?:\s*/\s*\d+)?\s*ft", description, flags=re.IGNORECASE)
        if range_match:
            return int(range_match.group(1))

        return None

    @staticmethod
    def _infer_aoe_template(description: str) -> tuple[str, int] | None:
        lowered = description.lower()

        radius_match = re.search(
            r"(\d+)\s*-\s*foot\s*-\s*radius\s*(sphere|cylinder)", lowered)
        if radius_match:
            feet = int(radius_match.group(1))
            shape = radius_match.group(2)
            return shape, max(1, feet // 5)

        size_shape_match = re.search(
            r"(\d+)\s*-\s*foot\s*(line|cone|sphere|cube|cylinder)", lowered)
        if size_shape_match:
            feet = int(size_shape_match.group(1))
            shape = size_shape_match.group(2)
            return shape, max(1, feet // 5)

        if "line" in lowered:
            return "line", 3
        if "cone" in lowered:
            return "cone", 3
        if "sphere" in lowered:
            return "sphere", 2
        if "cube" in lowered:
            return "cube", 2
        if "cylinder" in lowered:
            return "cylinder", 2

        return None

    @staticmethod
    def _coerce_positive_int(value: Any, fallback: int) -> int:
        if isinstance(value, (int, float)):
            return max(1, int(value))
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.isdigit():
                return max(1, int(stripped))
        return max(1, fallback)

    @staticmethod
    def _normalize_cell(value: Any) -> dict[str, int] | None:
        if not isinstance(value, dict):
            return None
        raw_x = value.get("x")
        raw_y = value.get("y")
        if not isinstance(raw_x, (int, float)) or not isinstance(raw_y, (int, float)):
            return None
        return {"x": int(raw_x), "y": int(raw_y)}

    @staticmethod
    def _normalize_direction(value: Any) -> dict[str, int] | None:
        cell = CombatService._normalize_cell(value)
        if cell is None:
            return None

        dx = 0 if cell["x"] == 0 else (1 if cell["x"] > 0 else -1)
        dy = 0 if cell["y"] == 0 else (1 if cell["y"] > 0 else -1)
        if dx == 0 and dy == 0:
            return None
        return {"x": dx, "y": dy}

    @staticmethod
    def _direction_from_points(origin: dict[str, int], target: dict[str, int]) -> dict[str, int]:
        dx = target["x"] - origin["x"]
        dy = target["y"] - origin["y"]
        nx = 0 if dx == 0 else (1 if dx > 0 else -1)
        ny = 0 if dy == 0 else (1 if dy > 0 else -1)
        if nx == 0 and ny == 0:
            return {"x": 1, "y": 0}
        return {"x": nx, "y": ny}

    @staticmethod
    def _is_cell_in_bounds(width: int, height: int, x: int, y: int) -> bool:
        return 0 <= x < width and 0 <= y < height

    @staticmethod
    def _cells_within_range(
        width: int,
        height: int,
        origin_x: int,
        origin_y: int,
        action_range: int | None,
    ) -> set[tuple[int, int]]:
        cells: set[tuple[int, int]] = set()
        for x in range(width):
            for y in range(height):
                if action_range is not None:
                    distance = abs(origin_x - x) + abs(origin_y - y)
                    if distance > action_range:
                        continue
                cells.add((x, y))
        return cells

    @staticmethod
    def _project_template_cells(
        width: int,
        height: int,
        shape: str,
        size: int,
        origin: dict[str, int],
        direction: dict[str, int],
    ) -> list[tuple[int, int]]:
        normalized_shape = (shape or "sphere").strip().lower()
        ox = int(origin["x"])
        oy = int(origin["y"])
        dx = int(direction["x"])
        dy = int(direction["y"])
        points: set[tuple[int, int]] = set()

        def add(x: int, y: int) -> None:
            if 0 <= x < width and 0 <= y < height:
                points.add((x, y))

        if normalized_shape in {"sphere", "cylinder"}:
            for x in range(ox - size, ox + size + 1):
                for y in range(oy - size, oy + size + 1):
                    if abs(x - ox) + abs(y - oy) <= size:
                        add(x, y)
        elif normalized_shape == "cube":
            for x in range(ox - size, ox + size + 1):
                for y in range(oy - size, oy + size + 1):
                    if max(abs(x - ox), abs(y - oy)) <= size:
                        add(x, y)
        elif normalized_shape == "line":
            step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
            step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
            for step in range(1, size + 1):
                add(ox + (step_x * step), oy + (step_y * step))
            add(ox, oy)
        elif normalized_shape == "cone":
            forward_x = 0 if dx == 0 else (1 if dx > 0 else -1)
            forward_y = 0 if dy == 0 else (1 if dy > 0 else -1)
            for step in range(1, size + 1):
                center_x = ox + (forward_x * step)
                center_y = oy + (forward_y * step)
                if forward_x != 0 and forward_y == 0:
                    for offset in range(-(step - 1), step):
                        add(center_x, center_y + offset)
                elif forward_y != 0 and forward_x == 0:
                    for offset in range(-(step - 1), step):
                        add(center_x + offset, center_y)
                else:
                    for offset in range(-(step - 1), step):
                        add(center_x + offset, center_y)
                        add(center_x, center_y + offset)
            add(ox, oy)
        else:
            add(ox, oy)

        return sorted(points)

    async def _base_actor_checks(
        self,
        encounter_session: EncounterSession | None,
        encounter: EncounterState,
        actor_id: str,
        action_type: str,
        ctx: SessionContext,
    ) -> AuthorizationResult:
        actor = self._find_actor(encounter, actor_id)
        actor_check = check_actor_exists(actor_id, actor)
        if not actor_check.allowed:
            return actor_check

        role_check = check_user_role_allowed(ctx.role)
        if not role_check.allowed:
            return role_check

        checks: dict[str, Any] = {
            "role": ctx.role.value,
            "actor_exists": True,
        }

        combatant = None
        if encounter_session is not None:
            combatant = await self._load_combatant(encounter_session.id, actor_id)

        owner_user_id = combatant.owner_user_id if combatant else actor.owner_user_id
        checks["owner_user_id"] = owner_user_id
        ownership_check = check_actor_ownership(ctx.role, ctx.user_id, owner_user_id)
        alive_check = check_actor_alive(actor)

        active = get_active_combatant(encounter)
        active_id = active.id if active else None
        turn_check = check_turn_ownership(
            action_type=action_type,
            turn_phase=encounter.turn_phase,
            active_actor_id=active_id,
            requesting_actor_id=actor_id,
        )

        return combine_authorization_checks(
            AuthorizationResult(True, checks=checks),
            ownership_check,
            alive_check,
            turn_check,
        )

    @staticmethod
    def _get_or_create_in_memory_budget(encounter: EncounterState, actor_id: str) -> dict[str, Any]:
        actor = CombatService._find_actor(encounter, actor_id)
        max_movement = actor.speed.walk if actor is not None else 30
        return get_or_create_in_memory_budget(
            turn_budgets=encounter.turn_budgets,
            actor_id=actor_id,
            max_movement=max_movement,
            round_number=encounter.round_number,
        )

    @staticmethod
    def _find_actor(encounter: EncounterState, actor_id: str) -> ActorInstance | None:
        for actor in encounter.combatants:
            if actor.id == actor_id:
                return actor
        return None

    @staticmethod
    def _path_distance(origin: Position, path: list[dict[str, int]]) -> int:
        if not path:
            return 0

        distance = 0
        prev_x = origin.x
        prev_y = origin.y
        for step in path:
            x = int(step.get("x", prev_x))
            y = int(step.get("y", prev_y))
            distance += abs(x - prev_x) + abs(y - prev_y)
            prev_x = x
            prev_y = y
        return distance

    def _actor_from_character(self, character: Character) -> ActorInstance:
        """Map a Character database model to an ActorInstance for the combat engine."""
        return ActorInstance(
            id=character.id,
            owner_user_id=character.player_name,  # Mapping player_name to owner_user_id
            definition_slug=character.class_id or "custom",
            name=character.name,
            actor_type=ActorType.PLAYER_CHARACTER,
            abilities=AbilityScores(
                strength=character.strength,
                dexterity=character.dexterity,
                constitution=character.constitution,
                intelligence=character.intelligence,
                wisdom=character.wisdom,
                charisma=character.charisma,
            ),
            current_hp=character.current_hp,
            max_hp=character.max_hp,
            temp_hp=character.temp_hp,
            armor_class=character.armor_class,
            speed=SpeedBlock(walk=character.speed),
            proficiency_bonus=calculate_proficiency_bonus(character.level),
            # Position will be assigned by the caller
        )

    def _default_encounter(self, campaign_id: str, campaign: Campaign | None = None) -> EncounterState:
        combatants: list[ActorInstance] = []
        tokens: list[MapToken] = []

        if campaign and campaign.characters:
            for i, character in enumerate(campaign.characters):
                actor = self._actor_from_character(character)
                # Assign a simple spread for positions
                actor.position = Position(x=5 + i, y=10)
                combatants.append(actor)
                tokens.append(MapToken(actor_id=actor.id,
                              position=actor.position))

        return EncounterState(
            id=f"enc_{campaign_id}",
            campaign_id=campaign_id,
            combatants=combatants,
            map=MapState(
                width=40,
                height=40,
                tokens=tokens,
            ),
        )

    @staticmethod
    def _encounter_from_rows(session: EncounterSession) -> EncounterState:
        if session.combat_state_json:
            return EncounterState.model_validate(session.combat_state_json)
        return EncounterState(
            id=session.encounter_id,
            campaign_id=session.campaign_id,
            turn_phase=session.phase,
            round_number=session.round_number,
            active_index=session.active_index,
            combatants=[],
        )

    async def _load_campaign_with_characters(self, campaign_id: str) -> Campaign | None:
        return await self._context_read_repository.get_campaign_with_characters(campaign_id)

    async def _ensure_context_catalog(self, campaign: Campaign) -> None:
        scenes = await self._context_read_repository.list_scenes(campaign.id)

        default_scene = next(
            (scene for scene in scenes if scene.scene_id == self.DEFAULT_SCENE_ID), None)
        if default_scene is None:
            default_scene = SceneCatalogRecord(
                campaign_id=campaign.id,
                scene_id=self.DEFAULT_SCENE_ID,
                name="Default Scene",
            )
            self.db.add(default_scene)

        existing_catalog = await self._context_read_repository.list_campaign_encounters(campaign.id)
        existing_ids = {item.encounter_id for item in existing_catalog}

        fixture_states = self._load_fixture_states(campaign.id)
        for state in fixture_states:
            if state.id in existing_ids:
                continue
            self.db.add(
                EncounterCatalogRecord(
                    campaign_id=campaign.id,
                    scene_id=self.DEFAULT_SCENE_ID,
                    encounter_id=state.id,
                    name=state.id,
                    source="fixture",
                    state_json=state.model_dump(mode="json"),
                )
            )

        if not fixture_states and campaign.characters and not existing_ids:
            party_state = self._default_encounter(campaign.id, campaign)
            self.db.add(
                EncounterCatalogRecord(
                    campaign_id=campaign.id,
                    scene_id=self.DEFAULT_SCENE_ID,
                    encounter_id=party_state.id,
                    name="Party Encounter",
                    source="campaign",
                    state_json=party_state.model_dump(mode="json"),
                )
            )
            existing_ids.add(party_state.id)

        if campaign.current_scene is None:
            campaign.current_scene = self.DEFAULT_SCENE_ID

        if campaign.active_encounter_id is None:
            available = await self._context_read_repository.list_campaign_encounters(campaign.id)
            if available:
                campaign.active_encounter_id = available[0].encounter_id

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(campaign)

    def _load_fixture_states(self, campaign_id: str) -> list[EncounterState]:
        if not self.FIXTURE_ENCOUNTERS_DIR.exists():
            return []

        states: list[EncounterState] = []
        for file_path in sorted(self.FIXTURE_ENCOUNTERS_DIR.glob("*.json")):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                state = EncounterState.model_validate(data)
            except Exception:
                continue

            if state.campaign_id == campaign_id:
                states.append(state)
        return states

    async def _load_catalog_encounter(
        self,
        campaign_id: str,
        scene_id: str,
        encounter_id: str,
    ) -> EncounterCatalogRecord | None:
        return await self._context_read_repository.get_scene_encounter(campaign_id, scene_id, encounter_id)

    # ------------------------------------------------------------------
    # Action execution pipeline  (extracted from ws_handler)
    # ------------------------------------------------------------------

    async def execute_action(
        self,
        encounter: EncounterState,
        encounter_session,
        actor_id: str,
        action_type: str,
        action_name: str,
        target_ids: list[str],
        action_payload: dict[str, Any],
        request_id: str | None,
        ctx: SessionContext,
        raw_payload: dict,
        require_canonical_action_id: bool = False,
    ) -> list[dict[str, Any]]:
        """Full action lifecycle: auth → metadata → preview → resolve → persist.

        Returns a list of domain-event dicts (not WsOutbound).  The handler
        wraps these into WsOutbound envelopes.
        """
        auth = await self.check_can_act(
            encounter_session, encounter,
            actor_id=actor_id, action_type=action_type, ctx=ctx,
        )
        if not auth.allowed:
            if encounter_session is not None:
                await self.log_action_attempt(
                    encounter_session, request_id=request_id,
                    actor_id=actor_id, action_type=action_type,
                    action_state="denied", payload=raw_payload,
                    checks=auth.checks or {}, denial_reason=auth.reason_code,
                )
            return [{"type": "denied", "reason_code": auth.reason_code or "invalid_action",
                     "message": auth.message or "Action denied",
                     "actor_id": actor_id, "action_type": action_type}]

        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return [{"type": "denied", "reason_code": "invalid_target",
                     "message": f"Actor {actor_id} not found",
                     "actor_id": actor_id, "action_type": action_type}]

        requested_template_origin = None
        requested_template_direction = None
        if isinstance(action_payload, dict):
            raw_template_origin = action_payload.get("template_origin")
            raw_template_direction = action_payload.get("template_direction")
            if isinstance(raw_template_origin, dict):
                requested_template_origin = raw_template_origin
            if isinstance(raw_template_direction, dict):
                requested_template_direction = raw_template_direction

        canonical_meta = await self.get_action_execution_metadata(
            encounter, actor_id, action_name,
        )
        if require_canonical_action_id and not canonical_meta.found:
            if encounter_session is not None:
                await self.log_action_attempt(
                    encounter_session, request_id=request_id,
                    actor_id=actor_id, action_type=action_type,
                    action_state="denied", payload=raw_payload,
                    checks=auth.checks or {}, denial_reason="invalid_action",
                )
            return [{"type": "denied", "reason_code": "invalid_action",
                     "message": "Unknown canonical action_id for actor",
                     "actor_id": actor_id, "action_type": action_type}]

        resolved_action_type = action_type
        if canonical_meta.found and canonical_meta.action_type_cost:
            resolved_action_type = self.normalize_action_type(
                canonical_meta.action_type_cost)
            if resolved_action_type != action_type:
                budget_check = await self.check_can_act(
                    encounter_session, encounter,
                    actor_id=actor_id, action_type=resolved_action_type, ctx=ctx,
                )
                if not budget_check.allowed:
                    if encounter_session is not None:
                        await self.log_action_attempt(
                            encounter_session, request_id=request_id,
                            actor_id=actor_id, action_type=resolved_action_type,
                            action_state="denied", payload=raw_payload,
                            checks=budget_check.checks or {},
                            denial_reason=budget_check.reason_code,
                        )
                    return [{"type": "denied",
                             "reason_code": budget_check.reason_code or "invalid_action",
                             "message": budget_check.message or "Action denied",
                             "actor_id": actor_id, "action_type": resolved_action_type}]

        targeting_mode = (
            canonical_meta.targeting_mode
            if canonical_meta.found and canonical_meta.targeting_mode
            else None
        )
        is_authoritative_targeting = targeting_mode in {
            "single_target", "aoe", "self"}
        is_aoe_targeting = targeting_mode == "aoe"

        should_validate_preview = is_authoritative_targeting or bool(
            target_ids) or requested_template_origin is not None
        if should_validate_preview:
            preview = await self.get_attack_preview(
                encounter_session, encounter, ctx, actor_id, action_name,
                template_origin=requested_template_origin,
                template_direction=requested_template_direction,
            )
            if preview.allowed:
                derived_target_ids = list(preview.eligible_target_ids or [])
                eligible_target_ids = set(derived_target_ids)

                if is_aoe_targeting and requested_template_origin is not None and not derived_target_ids:
                    return [{"type": "denied", "reason_code": "no_resolved_targets",
                             "message": "No valid targets resolved for selected template",
                             "actor_id": actor_id, "action_type": action_type}]

                if target_ids:
                    invalid_targets = [
                        tid for tid in target_ids if tid not in eligible_target_ids]
                    if invalid_targets:
                        denial_reason = "target_not_in_template" if is_aoe_targeting else "invalid_target"
                        return [{"type": "denied", "reason_code": denial_reason,
                                 "message": f"Selected target is not eligible for action '{action_name}'",
                                 "actor_id": actor_id, "action_type": action_type}]
                if is_authoritative_targeting:
                    target_ids = derived_target_ids
                elif requested_template_origin is not None and eligible_target_ids:
                    target_ids = derived_target_ids

                if requested_template_origin is not None and preview.template_projection is None:
                    return [{"type": "denied", "reason_code": "invalid_template_origin",
                             "message": "Action template selection is not valid for this action",
                             "actor_id": actor_id, "action_type": action_type}]
            elif preview.reason_code != "invalid_action":
                return [{"type": "denied",
                         "reason_code": normalize_preview_denial_reason(
                             preview.reason_code, preview.message),
                         "message": preview.message or "Target eligibility check failed",
                         "actor_id": actor_id, "action_type": action_type}]

        targets: list[ActorInstance] = []
        for tid in target_ids:
            target = self._find_actor(encounter, tid)
            if target is None:
                return [{"type": "denied", "reason_code": "invalid_target",
                         "message": f"Target actor {tid} not found",
                         "actor_id": actor_id, "action_type": action_type}]
            targets.append(target)

        family = canonical_meta.family if canonical_meta.found and canonical_meta.family else resolve_action_family(
            action_name, action_payload, targets)
        if family is None:
            if encounter_session is not None:
                await self.log_action_attempt(
                    encounter_session, request_id=request_id,
                    actor_id=actor_id, action_type=action_type,
                    action_state="denied", payload=raw_payload,
                    checks=auth.checks or {}, denial_reason="unsupported_action",
                )
            return [{"type": "denied", "reason_code": "unsupported_action",
                     "message": "Unsupported action family",
                     "actor_id": actor_id, "action_type": resolved_action_type}]

        await self.consume_budget(encounter_session, encounter, actor_id, resolved_action_type)
        budget_snapshot = await self.get_turn_budget_snapshot(encounter_session, encounter)

        events: list[dict[str, Any]] = [
            {"type": "action_authorized", "payload": {
                "actor_id": actor_id,
                "action_type": resolved_action_type,
                "action_name": action_name,
                "family": family,
                "turn_budget": budget_snapshot,
            }},
        ]

        family_events = self.resolve_action_family_events(
            family, encounter, actor, targets, action_name, action_payload,
        )
        events.extend(family_events)

        effect_events = await self.resolve_effect_intents(
            encounter, encounter_session, self.db,
            actor, targets, action_name, action_payload,
            canonical_meta.effect_intents if canonical_meta.found else None,
            request_id,
        )
        events.extend(effect_events)

        if encounter_session is not None:
            await self.sync_effect_instance_records(
                self.db, encounter_session, encounter,
                provenance_by_instance=collect_effect_provenance_by_instance(
                    events),
            )

        if encounter_session is not None:
            await self.log_action_attempt(
                encounter_session, request_id=request_id,
                actor_id=actor_id, action_type=resolved_action_type,
                action_state="resolved", payload=raw_payload,
                checks=auth.checks or {}, denial_reason=None,
            )
            await self.save_full_state(encounter_session, encounter)

        return events

    # ------------------------------------------------------------------
    # Action family resolution  (extracted from ws_handler)
    # ------------------------------------------------------------------

    def resolve_action_family_events(
        self,
        family: str,
        encounter: EncounterState,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Dispatch to the correct family resolver and return domain event dicts."""
        if family == ACTION_FAMILY_ATTACK:
            return self._resolve_attack_events(actor, targets, action_name, action_payload)
        if family == ACTION_FAMILY_SAVE:
            return self._resolve_save_events(encounter, actor, targets, action_name, action_payload)
        if family == ACTION_FAMILY_HEALING:
            return self._resolve_healing_events(actor, targets, action_name, action_payload)
        return self._resolve_utility_events(encounter, actor, targets, action_name, action_payload)

    def _resolve_attack_events(
        self,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not targets:
            return [{"type": "error", "message": "Attack action requires at least one target"}]

        target = targets[0]
        action_def = build_action_definition(
            ACTION_FAMILY_ATTACK, actor, action_name, action_payload)

        roll_override = safe_int(action_payload.get("roll_override"))
        roll_overrides = safe_int_list(action_payload.get("roll_overrides"))
        advantage = bool(action_payload.get("advantage", False))
        disadvantage = bool(action_payload.get("disadvantage", False))

        attack_result = resolve_attack(
            actor, target, action_def,
            roll_override=roll_override, roll_overrides=roll_overrides,
            advantage=advantage, disadvantage=disadvantage,
        )

        events: list[dict[str, Any]] = [
            {"type": "attack_result", "payload": {
                "attacker_id": actor.id, "target_id": target.id,
                "action_name": action_name,
                "hit": attack_result.hit,
                "is_critical": attack_result.is_critical,
                "roll_used": attack_result.roll_used,
                "roll_count": attack_result.roll_count,
                "damage": attack_result.total_damage,
                "damage_type": (action_def.damage_type.value if action_def.damage_type else DamageType.BLUDGEONING.value),
            }},
        ]

        if attack_result.hit and attack_result.total_damage > 0:
            events.append({"type": "actor_damaged", "payload": {
                "actor_id": target.id, "amount": attack_result.total_damage,
                "new_hp": target.current_hp, "source": action_name,
            }})
            if target.current_hp <= 0:
                events.append(
                    {"type": "actor_died", "payload": {"actor_id": target.id}})

        return events

    def _resolve_save_events(
        self,
        encounter: EncounterState,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not targets:
            return [{"type": "error", "message": "Save action requires at least one target"}]

        action_def = build_action_definition(
            ACTION_FAMILY_SAVE, actor, action_name, action_payload)
        damage_roll_override = safe_int(
            action_payload.get("damage_roll_override"))
        save_overrides = safe_int_list(action_payload.get("save_overrides"))

        save_result = resolve_save_action(
            actor, targets, action_def,
            damage_roll_override=damage_roll_override, save_overrides=save_overrides,
        )

        save_payload_results = []
        events: list[dict[str, Any]] = []
        for target_result in save_result.results:
            save_payload_results.append({
                "target_id": target_result.target_id,
                "passed": target_result.passed,
                "save_roll": target_result.save_roll,
                "damage": target_result.damage,
            })
            if target_result.damage > 0:
                target = self._find_actor(encounter, target_result.target_id)
                if target is not None:
                    events.append({"type": "actor_damaged", "payload": {
                        "actor_id": target.id, "amount": target_result.damage,
                        "new_hp": target.current_hp, "source": action_name,
                    }})
                    if target.current_hp <= 0:
                        events.append(
                            {"type": "actor_died", "payload": {"actor_id": target.id}})

        save_req = action_def.save
        events.insert(0, {"type": "save_result", "payload": {
            "caster_id": actor.id, "action_name": action_name,
            "save_ability": save_req.ability.value if save_req else Ability.DEX.value,
            "save_dc": save_req.dc if save_req else 10,
            "results": save_payload_results,
        }})

        return events

    def _resolve_healing_events(
        self,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        target = targets[0] if targets else actor
        action_def = build_action_definition(
            ACTION_FAMILY_HEALING, actor, action_name, action_payload)
        dice_override = safe_int(action_payload.get("dice_override"))
        healing_result = resolve_healing(
            target, action_def, dice_override=dice_override)

        return [
            {"type": "effect_applied", "payload": {
                "actor_id": actor.id, "target_id": target.id,
                "action_name": action_name, "effect_type": "healing",
                "amount": healing_result.hp_restored,
            }},
            {"type": "actor_healed", "payload": {
                "actor_id": target.id, "amount": healing_result.hp_restored,
                "new_hp": healing_result.new_hp,
            }},
        ]

    def _resolve_utility_events(
        self,
        encounter: EncounterState,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        target = targets[0] if targets else actor
        condition = parse_condition(action_payload.get("condition"))
        condition_op = str(action_payload.get(
            "condition_op", "add")).strip().lower()
        should_remove = bool(action_payload.get(
            "remove_condition", False)) or condition_op in {"remove", "delete"}

        if condition is None:
            return [{"type": "effect_applied", "payload": {
                "actor_id": actor.id, "target_id": target.id,
                "action_name": action_name, "effect_type": "utility",
            }}]

        if should_remove:
            target.conditions = [
                entry for entry in target.conditions if entry.condition != condition]
            condition_event = {"type": "condition_removed", "payload": {
                "actor_id": target.id, "condition": condition.value,
            }}
            effect_type = "condition_removed"
        else:
            target.conditions.append(ConditionInstance(
                condition=condition, source_id=actor.id,
            ))
            condition_event = {"type": "condition_added", "payload": {
                "actor_id": target.id, "condition": condition.value, "source": actor.id,
            }}
            effect_type = "condition_added"

        return [
            {"type": "effect_applied", "payload": {
                "actor_id": actor.id, "target_id": target.id,
                "action_name": action_name, "effect_type": effect_type,
                "condition": condition.value,
            }},
            condition_event,
        ]

    # ------------------------------------------------------------------
    # Effect intent resolution  (extracted from ws_handler)
    # ------------------------------------------------------------------

    async def resolve_effect_intents(
        self,
        encounter: EncounterState,
        encounter_session,
        db_session,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
        canonical_effect_intents: list[dict[str, Any]] | None,
        request_id: str | None,
    ) -> list[dict[str, Any]]:
        """Process effect intents (inline and canonical) and return domain event dicts."""
        intents = canonical_effect_intents if isinstance(
            canonical_effect_intents, list) else []
        if not intents and isinstance(action_payload.get("effect_intents"), list):
            intents = [intent for intent in action_payload.get(
                "effect_intents", []) if isinstance(intent, dict)]

        if not intents:
            return []

        events: list[dict[str, Any]] = []
        for intent in intents:
            effect_id = str(intent.get("effect_id") or "").strip()
            if effect_id:
                events.extend(
                    await self._apply_canonical_effect_intent(
                        encounter, encounter_session, db_session,
                        actor, targets, action_name, intent, request_id,
                    )
                )
                continue

            operation = str(intent.get("operation") or "").strip().lower()
            if operation not in {"apply_condition", "remove_condition"}:
                continue

            condition = parse_condition(intent.get(
                "condition") or intent.get("value"))
            if condition is None:
                continue

            resolved_targets = self._resolve_effect_targets(
                encounter, targets, intent.get("target_ids"))
            for target in resolved_targets:
                if operation == "remove_condition":
                    target.conditions = [
                        entry for entry in target.conditions if entry.condition != condition
                    ]
                    events.append({"type": "condition_removed", "payload": {
                        "actor_id": target.id, "condition": condition.value,
                    }})
                    events.append({"type": "effect_removed", "payload": {
                        "effect_id": f"inline:{operation}:{condition.value}",
                        "target_actor_id": target.id,
                        "source_actor_id": actor.id,
                        "reason": "removed",
                        "provenance": effect_provenance_payload(request_id, action_name, actor.id),
                    }})
                else:
                    if not any(existing.condition == condition and existing.source_id == actor.id for existing in target.conditions):
                        target.conditions.append(ConditionInstance(
                            condition=condition, source_id=actor.id,
                        ))
                    events.append({"type": "effect_applied", "payload": {
                        "effect_id": f"inline:{operation}:{condition.value}",
                        "target_actor_id": target.id,
                        "source_actor_id": actor.id,
                        "provenance": effect_provenance_payload(request_id, action_name, actor.id),
                    }})
                    events.append({"type": "condition_added", "payload": {
                        "actor_id": target.id, "condition": condition.value,
                        "source": actor.id,
                    }})

        return events

    def _resolve_effect_targets(
        self,
        encounter: EncounterState,
        base_targets: list[ActorInstance],
        explicit_target_ids: Any,
    ) -> list[ActorInstance]:
        if not isinstance(explicit_target_ids, list):
            return base_targets
        resolved: list[ActorInstance] = []
        for target_id in explicit_target_ids:
            if not isinstance(target_id, str):
                continue
            actor = self._find_actor(encounter, target_id)
            if actor is not None:
                resolved.append(actor)
        return resolved

    async def _apply_canonical_effect_intent(
        self,
        encounter: EncounterState,
        encounter_session,
        db_session,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        intent: dict[str, Any],
        request_id: str | None,
    ) -> list[dict[str, Any]]:
        effect_id = str(intent.get("effect_id") or "").strip()
        if not effect_id:
            return []

        effect_record = await self._action_catalog_repository.get_effect_definition(effect_id)

        if effect_record is None:
            return [{"type": "effect_denied", "payload": {
                "effect_id": effect_id, "reason_code": "effect_not_found",
                "message": f"Unknown effect_id '{effect_id}'",
                "provenance": effect_provenance_payload(request_id, action_name, actor.id),
            }}]

        definition = CanonicalEffectDefinition(
            effect_id=effect_record.effect_id,
            name=effect_record.name,
            family=effect_record.family,
            duration=effect_record.duration or {},
            stacking=effect_record.stacking or {},
            tags=effect_record.tags or [],
            modifiers=effect_record.modifiers or [],
            grants_conditions=effect_record.grants_conditions or [],
            periodic=effect_record.periodic or [],
            removal_triggers=effect_record.removal_triggers or [],
            metadata=effect_record.metadata_json or {},
        )

        events: list[dict[str, Any]] = []
        resolved_targets = self._resolve_effect_targets(
            encounter, targets, intent.get("target_ids"))
        if not resolved_targets:
            return [{"type": "effect_denied", "payload": {
                "effect_id": effect_id, "reason_code": "target_invalid",
                "message": "No valid targets for effect intent",
                "provenance": effect_provenance_payload(request_id, action_name, actor.id),
            }}]

        duration_type = str(definition.duration.type)
        requires_concentration = duration_type == "concentration"
        duration_value = safe_int(intent.get(
            "duration_override"), default=definition.duration.value)

        for target in resolved_targets:
            existing_instances = [
                effect for effect in target.effects
                if (effect_instance_canonical_id(effect) == definition.effect_id)
            ]

            stack_mode = definition.stacking.mode
            max_stacks = definition.stacking.max_stacks

            if requires_concentration and actor.concentration.is_concentrating and actor.concentration.effect_id:
                if all(effect.id != actor.concentration.effect_id for effect in existing_instances):
                    previous_effect_id = actor.concentration.effect_id
                    remove_effect(encounter, previous_effect_id)
                    events.append({"type": "effect_removed", "payload": {
                        "effect_instance_id": previous_effect_id,
                        "effect_id": "concentration",
                        "source_actor_id": actor.id,
                        "reason": "concentration_replaced",
                        "provenance": effect_provenance_payload(request_id, action_name, actor.id),
                    }})
                    actor.concentration.is_concentrating = False
                    actor.concentration.effect_id = None

            if stack_mode == "stack" and existing_instances:
                existing = existing_instances[0]
                current_stacks = safe_int(existing.value, default=1) or 1
                if max_stacks is not None and current_stacks >= max_stacks:
                    events.append({"type": "effect_denied", "payload": {
                        "effect_id": definition.effect_id,
                        "target_actor_id": target.id,
                        "reason_code": "stacking_limit_reached",
                        "message": "Effect stacking limit reached",
                        "provenance": effect_provenance_payload(request_id, action_name, actor.id),
                    }})
                    continue

                existing.value = current_stacks + 1
                if duration_type in {"rounds", "turns"}:
                    existing.remaining_rounds = duration_value
                events.append({"type": "effect_refreshed", "payload": {
                    "effect_instance_id": existing.id,
                    "effect_id": definition.effect_id,
                    "target_actor_id": target.id,
                    "source_actor_id": actor.id,
                    "stack_count": existing.value,
                    "remaining_duration": existing.remaining_rounds,
                    "provenance": effect_provenance_payload(request_id, action_name, actor.id),
                }})
                continue

            if stack_mode in {"replace", "highest_only"} and existing_instances:
                for existing in existing_instances:
                    remove_effect(encounter, existing.id)
                    events.append({"type": "effect_removed", "payload": {
                        "effect_instance_id": existing.id,
                        "effect_id": definition.effect_id,
                        "target_actor_id": target.id,
                        "source_actor_id": actor.id,
                        "reason": "replaced",
                        "provenance": effect_provenance_payload(request_id, action_name, actor.id),
                    }})

            if stack_mode == "refresh_duration" and existing_instances:
                existing = existing_instances[0]
                if duration_type in {"rounds", "turns"}:
                    existing.remaining_rounds = duration_value
                events.append({"type": "effect_refreshed", "payload": {
                    "effect_instance_id": existing.id,
                    "effect_id": definition.effect_id,
                    "target_actor_id": target.id,
                    "source_actor_id": actor.id,
                    "remaining_duration": existing.remaining_rounds,
                    "provenance": effect_provenance_payload(request_id, action_name, actor.id),
                }})
                continue

            from uuid import uuid4
            instance_id = f"eff_{uuid4().hex}"
            remaining_rounds: int | None = None
            if duration_type in {"rounds", "turns"}:
                remaining_rounds = duration_value

            new_effect = EffectInstance(
                id=instance_id,
                effect_id=definition.effect_id,
                name=definition.name,
                source_id=actor.id,
                target_id=target.id,
                duration_type=DurationType.ROUNDS if remaining_rounds is not None else DurationType.UNTIL_DISPELLED,
                remaining_rounds=remaining_rounds,
                requires_concentration=requires_concentration,
                value=1,
            )
            add_effect(encounter, new_effect)

            if requires_concentration:
                actor.concentration.is_concentrating = True
                actor.concentration.effect_id = new_effect.id

            events.append({"type": "effect_applied", "payload": {
                "effect_instance_id": new_effect.id,
                "effect_id": definition.effect_id,
                "target_actor_id": target.id,
                "source_actor_id": actor.id,
                "remaining_duration": new_effect.remaining_rounds,
                "requires_concentration": requires_concentration,
                "provenance": effect_provenance_payload(request_id, action_name, actor.id),
            }})

            for condition_name in definition.grants_conditions:
                condition = parse_condition(condition_name)
                if condition is None:
                    continue
                if any(entry.condition == condition and entry.source_effect_id == new_effect.id for entry in target.conditions):
                    continue
                target.conditions.append(ConditionInstance(
                    condition=condition, source_id=actor.id,
                    source_effect_id=new_effect.id,
                ))
                events.append({"type": "condition_added", "payload": {
                    "actor_id": target.id, "condition": condition.value, "source": actor.id,
                }})

        return events

    # ------------------------------------------------------------------
    # Effect persistence sync  (extracted from ws_handler)
    # ------------------------------------------------------------------
    async def sync_effect_instance_records(
        self,
        db_session,
        encounter_session,
        encounter: EncounterState,
        provenance_by_instance: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Upsert effect instance records via repository-owned persistence."""
        await self._action_execution_repository.sync_effect_instance_records(
            encounter_session=encounter_session,
            encounter=encounter,
            provenance_by_instance=provenance_by_instance,
        )

    def _sync_effect_instance_records_from_events(
        self,
        encounter_session,
        encounter: EncounterState,
        effect_events: list[dict[str, Any]],
    ) -> None:
        """Schedule effect instance record sync (called at end of action pipeline)."""
        # This is a no-op marker; actual sync happens via sync_effect_instance_records
        # after the handler calls it with the collected provenance.
        pass

    # ------------------------------------------------------------------
    # Effect tick helpers  (extracted from ws_handler)
    # ------------------------------------------------------------------

    @staticmethod
    def build_effect_tick_events(
        tick_outcome: dict[str, list[dict[str, int | str | None]]],
        source_actor_id: str,
        request_id: str | None,
    ) -> list[dict[str, Any]]:
        """Build domain event dicts from effect tick outcomes."""
        events: list[dict[str, Any]] = []
        provenance = effect_provenance_payload(
            request_id, None, source_actor_id)

        for entry in tick_outcome.get("ticked", []):
            events.append({"type": "effect_tick_resolved", "payload": {
                "effect_instance_id": entry.get("effect_instance_id"),
                "effect_id": entry.get("effect_id"),
                "target_actor_id": entry.get("target_actor_id"),
                "source_actor_id": source_actor_id,
                "remaining_duration": entry.get("remaining_duration"),
                "trigger": "end_turn",
                "provenance": provenance,
            }})

        for entry in tick_outcome.get("expired", []):
            events.append({"type": "effect_removed", "payload": {
                "effect_instance_id": entry.get("effect_instance_id"),
                "effect_id": entry.get("effect_id"),
                "target_actor_id": entry.get("target_actor_id"),
                "source_actor_id": source_actor_id,
                "reason": "expired",
                "provenance": provenance,
            }})

        return events

    @staticmethod
    def clear_expired_concentration(encounter: EncounterState, expired_effect_instance_ids: set[str]) -> None:
        """Clear concentration state for combatants whose concentration effect expired."""
        if not expired_effect_instance_ids:
            return
        for combatant in encounter.combatants:
            if combatant.concentration.effect_id in expired_effect_instance_ids:
                combatant.concentration.is_concentrating = False
                combatant.concentration.effect_id = None

    # ------------------------------------------------------------------
    # Combat lifecycle handlers  (extracted from ws_handler)
    # ------------------------------------------------------------------

    async def handle_end_turn(
        self,
        encounter: EncounterState,
        encounter_session,
        actor_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        """End turn: tick effects, advance turn, return result dict.

        Returns {"allowed": True/False, ...} with events or denial info.
        """
        if encounter.turn_phase != "active":
            return {"allowed": False, "reason_code": "invalid_turn_phase",
                    "message": "Cannot end turn when combat is not active"}

        active_actor = get_active_combatant(encounter)
        if active_actor is None:
            return {"allowed": False, "reason_code": "no_active_actor",
                    "message": "No active combatant available", "actor_id": actor_id}

        if actor_id != active_actor.id:
            return {"allowed": False, "reason_code": "not_your_turn",
                    "message": "Only the active combatant can end the turn", "actor_id": actor_id}

        tick_outcome = tick_effects(encounter, source_id=active_actor.id)
        expired_effect_ids = {
            str(entry.get("effect_instance_id"))
            for entry in tick_outcome.get("expired", [])
            if entry.get("effect_instance_id")
        }
        self.clear_expired_concentration(encounter, expired_effect_ids)
        tick_events = self.build_effect_tick_events(
            tick_outcome, source_actor_id=active_actor.id, request_id=request_id,
        )

        if encounter_session is None:
            next_turn(encounter)
            await self.on_turn_started(encounter_session, encounter)
            active = get_active_combatant(encounter)
            active_id = active.id if active else ""
        else:
            active_id, _ = await self.advance_turn(encounter_session, encounter)
            await self.sync_effect_instance_records(
                self.db, encounter_session, encounter,
                provenance_by_instance=collect_effect_provenance_by_instance(
                    tick_events),
            )

        budget_snapshot = await self.get_turn_budget_snapshot(encounter_session, encounter)

        return {
            "allowed": True,
            "tick_events": tick_events,
            "active_actor_id": active_id,
            "round": encounter.round_number,
            "turn_budget": budget_snapshot,
        }

    async def handle_move_token(
        self,
        encounter: EncounterState,
        encounter_session,
        ctx: SessionContext,
        actor_id: str,
        path: list[dict[str, int]],
        request_id: str | None,
        acting_as_user_id: str | None = None,
    ) -> dict[str, Any]:
        """Validate and apply movement. Returns result dict."""
        if not path:
            return {"allowed": False, "error": "move_token path cannot be empty"}

        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return {"allowed": False, "reason_code": "invalid_target",
                    "error": f"Actor {actor_id} not found"}

        auth = await self.apply_movement(
            encounter_session, encounter, ctx,
            actor_id, path, request_id,
        )
        if not auth.allowed:
            return {"allowed": False, "reason_code": auth.reason_code or "invalid_action",
                    "message": auth.message or "Movement denied", "actor_id": actor_id}

        validated_path: list[dict[str, int]] = []
        for step in path:
            try:
                pos = Position.model_validate(step)
            except Exception:
                return {"allowed": False, "error": "move_token path contains invalid coordinates"}

            if pos.x < 0 or pos.y < 0 or pos.x >= encounter.map.width or pos.y >= encounter.map.height:
                return {"allowed": False, "error": "move_token target is out of map bounds"}

            validated_path.append({"x": pos.x, "y": pos.y})

        final_step = validated_path[-1]
        actor.position = Position(x=final_step["x"], y=final_step["y"])

        token = self._find_map_token(encounter, actor_id)
        if token is None:
            token = MapToken(actor_id=actor_id, position=actor.position)
            encounter.map.tokens.append(token)
        else:
            token.position = actor.position

        budget_snapshot = await self.get_turn_budget_snapshot(encounter_session, encounter)

        return {
            "allowed": True,
            "actor_id": actor_id,
            "path": validated_path,
            "position": final_step,
            "turn_budget": budget_snapshot,
        }

    def handle_add_actor(
        self,
        encounter: EncounterState,
        definition_slug: str,
        name: str | None,
        owner_user_id: str | None,
        position_data: dict | None,
    ) -> dict[str, Any]:
        """Add an actor to the encounter. Returns result dict."""
        definition_slug = definition_slug.strip()
        if not definition_slug:
            return {"error": "add_actor definition_slug cannot be empty"}

        if position_data is not None:
            try:
                position = Position.model_validate(position_data)
            except Exception:
                return {"error": "Invalid add_actor position"}
        else:
            position = Position()

        if (position.x < 0 or position.y < 0
                or position.x >= encounter.map.width
                or position.y >= encounter.map.height):
            return {"error": "add_actor target is out of map bounds"}

        actor_id = next_actor_id(encounter, definition_slug)
        actor_name = (name or "").strip(
        ) or display_name_from_slug(definition_slug)

        actor = ActorInstance(
            id=actor_id,
            owner_user_id=owner_user_id,
            definition_slug=definition_slug,
            name=actor_name,
            actor_type=ActorType.MONSTER,
            current_hp=1,
            max_hp=1,
            armor_class=10,
            abilities=AbilityScores(),
            speed=SpeedBlock(),
            position=Position(x=position.x, y=position.y),
        )
        encounter.combatants.append(actor)

        token = MapToken(actor_id=actor.id, position=Position(
            x=position.x, y=position.y))
        encounter.map.tokens.append(token)

        return {
            "actor": {
                "id": actor.id,
                "owner_user_id": actor.owner_user_id,
                "definition_slug": actor.definition_slug,
                "name": actor.name,
                "actor_type": actor.actor_type.value,
                "position": token.position.model_dump(mode="json"),
            },
            "token": token.model_dump(mode="json"),
        }

    def handle_remove_actor(
        self,
        encounter: EncounterState,
        actor_id: str,
    ) -> dict[str, Any]:
        """Remove an actor from the encounter. Returns result dict."""
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return {"error": f"Actor {actor_id} not found"}

        encounter.combatants = [
            c for c in encounter.combatants if c.id != actor_id]
        encounter.map.tokens = [
            t for t in encounter.map.tokens if t.actor_id != actor_id]

        if not encounter.combatants:
            encounter.active_index = 0
            encounter.turn_phase = "post_combat"
        elif encounter.active_index >= len(encounter.combatants):
            encounter.active_index = 0

        return {"actor_id": actor_id}

    async def handle_start_combat(
        self,
        encounter: EncounterState,
        encounter_session,
    ) -> dict[str, Any]:
        """Start combat. Returns result dict with initiative order."""
        if not encounter.combatants:
            return {"error": "No combatants to start combat"}

        if encounter_session is None:
            initiatives = []
            for idx, actor in enumerate(encounter.combatants):
                # Use same deterministic logic as start_combat to keep tests stable
                initiatives.append(InitiativeEntry(
                    actor_id=actor.id,
                    roll=max(1, 20 - idx),
                    dex_score=actor.abilities.dexterity,
                ))
            start_combat(encounter, initiatives)
            order = [{"actor_id": a.id, "name": a.name}
                     for a in encounter.combatants]
        else:
            order = await self.start_combat(encounter_session, encounter)

        budget_snapshot = await self.get_turn_budget_snapshot(encounter_session, encounter)
        return {"initiative_order": order, "turn_budget": budget_snapshot}

    @staticmethod
    def handle_end_combat(encounter: EncounterState) -> dict[str, Any]:
        """End combat. Returns result dict."""
        encounter.turn_phase = "post_combat"
        encounter.round_number = 0
        encounter.active_index = 0
        return {}

    def handle_apply_damage(
        self,
        encounter: EncounterState,
        actor_id: str,
        amount: int,
        damage_type_str: str,
    ) -> dict[str, Any]:
        """Apply DM damage override. Returns result dict."""
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return {"error": f"Actor {actor_id} not found"}

        try:
            damage_type = DamageType(damage_type_str)
        except ValueError:
            damage_type = DamageType.SLASHING

        result = engine_apply_damage(
            actor, amount=amount, damage_type=damage_type)
        actor.current_hp = result.remaining_hp
        actor.temp_hp = result.remaining_temp_hp

        return {
            "actor_id": actor_id,
            "damage_dealt": result.damage_dealt,
            "new_hp": actor.current_hp,
            "is_dead": result.is_dead,
        }

    def handle_apply_healing(
        self,
        encounter: EncounterState,
        actor_id: str,
        amount: int,
    ) -> dict[str, Any]:
        """Apply healing to an actor. Returns result dict."""
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return {"error": f"Actor {actor_id} not found"}

        old_hp = actor.current_hp
        actor.current_hp = min(actor.max_hp, actor.current_hp + amount)
        healed = actor.current_hp - old_hp

        return {"actor_id": actor_id, "amount": healed, "new_hp": actor.current_hp}

    def handle_apply_condition(
        self,
        encounter: EncounterState,
        actor_id: str,
        condition_str: str,
        source_id: str | None,
    ) -> dict[str, Any]:
        """Apply a condition to an actor. Returns result dict."""
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return {"error": f"Actor {actor_id} not found"}

        try:
            condition = ConditionType(condition_str)
        except ValueError:
            return {"error": f"Unknown condition: {condition_str}"}

        actor.conditions.append(ConditionInstance(
            condition=condition, source_id=source_id or "",
        ))

        return {"actor_id": actor_id, "condition": condition.value, "source": source_id or ""}

    def handle_remove_condition(
        self,
        encounter: EncounterState,
        actor_id: str,
        condition_str: str,
    ) -> dict[str, Any]:
        """Remove a condition from an actor. Returns result dict."""
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return {"error": f"Actor {actor_id} not found"}

        try:
            condition = ConditionType(condition_str)
        except ValueError:
            return {"error": f"Unknown condition: {condition_str}"}

        actor.conditions = [
            c for c in actor.conditions if c.condition != condition]
        return {"actor_id": actor_id, "condition": condition.value}

    def handle_roll_dice(self, expression: str, purpose: str | None, user_id: str) -> dict[str, Any]:
        """Roll dice and return result dict."""
        result = DiceService.roll(expression)
        return {
            "roller_id": user_id,
            "expression": expression,
            "result": result.total,
            "purpose": purpose,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_map_token(encounter: EncounterState, actor_id: str) -> MapToken | None:
        for token in encounter.map.tokens:
            if token.actor_id == actor_id:
                return token
        return None
