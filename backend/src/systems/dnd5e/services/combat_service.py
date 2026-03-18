from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.sessions.models import SessionContext, UserRole
from src.data.lib.monster import Monster

from ..engine.combat_state import get_active_combatant, next_turn, start_combat
from ..engine.initiative import InitiativeEntry
from ..lib.content_models import AbilityBindingRecord, ActionDefinitionRecord
from ..schemas.common import Position
from ..schemas.encounter import EncounterState, MapState, MapToken
from ..schemas.instances import ActorInstance
from ..lib.combat_models import ActionLog, CombatantState, EncounterSession, TurnBudgetRecord


@dataclass
class AuthorizationResult:
    allowed: bool
    reason_code: str | None = None
    message: str | None = None
    checks: dict[str, Any] | None = None


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

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_or_create_encounter_state(self, campaign_id: str) -> tuple[EncounterSession, EncounterState]:
        session = await self._load_session(campaign_id)
        if session is None:
            encounter = self._default_encounter(campaign_id)
            session = EncounterSession(
                campaign_id=campaign_id,
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

        if session.combat_state_json:
            encounter = EncounterState.model_validate(
                session.combat_state_json)
        else:
            encounter = self._encounter_from_rows(session)

        await self._refresh_turn_budgets_on_encounter(encounter, session)
        return session, encounter

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
        if action_type_normalized == "action" and not action_available:
            checks_data["action_available"] = False
            return AuthorizationResult(False, "action_exhausted", "Action already spent this turn", checks_data)

        if action_type_normalized == "bonus_action" and not bonus_action_available:
            checks_data["bonus_action_available"] = False
            return AuthorizationResult(False, "bonus_action_exhausted", "Bonus action already spent this turn", checks_data)

        if action_type_normalized == "reaction" and not reaction_available:
            checks_data["reaction_available"] = False
            return AuthorizationResult(False, "reaction_exhausted", "Reaction already spent", checks_data)

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
            if normalized == "action":
                budget_state["action_available"] = False
            elif normalized == "bonus_action":
                budget_state["bonus_action_available"] = False
            elif normalized == "reaction":
                budget_state["reaction_available"] = False

            budget_state["movement_remaining"] = max(
                int(budget_state.get("max_movement", actor.speed.walk)) -
                int(budget_state.get("movement_used", 0)),
                0,
            )
            return

        budget = await self._get_or_create_budget(encounter_session, actor_id, encounter.round_number, actor.speed.walk)

        if normalized == "action":
            budget.action_available = False
        elif normalized == "bonus_action":
            budget.bonus_action_available = False
        elif normalized == "reaction":
            budget.reaction_available = False

        await self.db.flush()

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
        await self.db.flush()

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
        normalized = (action_type or "").strip().lower()
        if normalized in {"", "action", "attack", "cast_spell", "cast-spell", "spell", "main_action"}:
            return "action"
        if normalized in {"bonus_action", "bonus-action", "bonus"}:
            return "bonus_action"
        if normalized in {"reaction"}:
            return "reaction"
        if normalized in {"move", "movement", "move_token"}:
            return "move"
        return normalized

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
        entry = ActionLog(
            encounter_session_id=encounter_session.id,
            request_id=request_id,
            actor_id=actor_id,
            action_type=action_type,
            action_state=action_state,
            denial_reason=denial_reason,
            authorization_checks=checks,
            payload=payload,
        )
        self.db.add(entry)
        await self.db.flush()

    async def get_action_log(self, campaign_id: str, limit: int = 100) -> list[ActionLog]:
        stmt = (
            select(ActionLog)
            .join(EncounterSession, ActionLog.encounter_session_id == EncounterSession.id)
            .where(EncounterSession.campaign_id == campaign_id)
            .order_by(ActionLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

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
        encounter_session.encounter_id = encounter.id
        encounter_session.phase = encounter.turn_phase
        encounter_session.round_number = encounter.round_number
        encounter_session.active_index = encounter.active_index
        encounter_session.combat_state_json = encounter.model_dump(mode="json")

        await self._sync_combatants(encounter_session, encounter)
        await self.db.flush()
        await self.db.commit()

    async def _sync_combatants(self, encounter_session: EncounterSession, encounter: EncounterState) -> None:
        await self.db.execute(
            delete(CombatantState).where(
                CombatantState.encounter_session_id == encounter_session.id)
        )

        for index, actor in enumerate(encounter.combatants):
            self.db.add(
                CombatantState(
                    encounter_session_id=encounter_session.id,
                    actor_id=actor.id,
                    initiative_order=index,
                    owner_user_id=actor.owner_user_id,
                    current_hp=actor.current_hp,
                    max_hp=actor.max_hp,
                    pos_x=actor.position.x,
                    pos_y=actor.position.y,
                    actor_snapshot=actor.model_dump(mode="json"),
                )
            )

    async def _ensure_round_budgets(self, encounter_session: EncounterSession, encounter: EncounterState) -> None:
        for actor in encounter.combatants:
            await self._get_or_create_budget(encounter_session, actor.id, encounter.round_number, actor.speed.walk)

        await self.db.commit()

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
        combatant = await self._load_combatant(encounter_session.id, actor_id)
        if combatant is None:
            combatant = CombatantState(
                encounter_session_id=encounter_session.id,
                actor_id=actor_id,
                initiative_order=0,
                owner_user_id=None,
                current_hp=0,
                max_hp=0,
                pos_x=0,
                pos_y=0,
                actor_snapshot={},
            )
            self.db.add(combatant)
            await self.db.flush()

        stmt = select(TurnBudgetRecord).where(
            TurnBudgetRecord.encounter_session_id == encounter_session.id,
            TurnBudgetRecord.combatant_id == combatant.id,
            TurnBudgetRecord.round_number == round_number,
        )
        result = await self.db.execute(stmt)
        budget = result.scalar_one_or_none()
        if budget is not None:
            return budget

        budget = TurnBudgetRecord(
            encounter_session_id=encounter_session.id,
            combatant_id=combatant.id,
            round_number=round_number,
            action_available=True,
            bonus_action_available=True,
            reaction_available=True,
            max_movement=max_movement,
            movement_used=0,
        )
        self.db.add(budget)
        await self.db.flush()
        return budget

    async def _load_combatant(self, encounter_session_id: str, actor_id: str) -> CombatantState | None:
        stmt = select(CombatantState).where(
            CombatantState.encounter_session_id == encounter_session_id,
            CombatantState.actor_id == actor_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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
        definition_slug = actor.definition_slug.strip()
        binding_filters = [AbilityBindingRecord.actor_id == actor.id]
        if template_candidates:
            binding_filters.append(
                AbilityBindingRecord.actor_template_id.in_(template_candidates)
            )

        stmt = select(AbilityBindingRecord).where(
            AbilityBindingRecord.system == "dnd5e",
            or_(*binding_filters),
        )

        try:
            binding_result = await self.db.execute(stmt)
            bindings = list(binding_result.scalars().all())
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

        action_stmt = select(ActionDefinitionRecord).where(
            ActionDefinitionRecord.system == "dnd5e",
            ActionDefinitionRecord.enabled.is_(True),
            ActionDefinitionRecord.action_id.in_(action_ids),
        )

        try:
            action_result = await self.db.execute(action_stmt)
            action_defs = list(action_result.scalars().all())
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
        if actor is None:
            return AuthorizationResult(False, "invalid_target", f"Actor {actor_id} not found")

        if ctx.role == UserRole.SPECTATOR:
            return AuthorizationResult(False, "unauthorized", "Spectators cannot perform combat actions")

        checks: dict[str, Any] = {
            "role": ctx.role.value,
            "actor_exists": True,
        }

        combatant = None
        if encounter_session is not None:
            combatant = await self._load_combatant(encounter_session.id, actor_id)

        owner_user_id = combatant.owner_user_id if combatant else actor.owner_user_id
        checks["owner_user_id"] = owner_user_id

        if ctx.role == UserRole.PLAYER and owner_user_id and owner_user_id != ctx.user_id:
            checks["ownership_ok"] = False
            return AuthorizationResult(False, "unauthorized", "Player does not own this actor", checks)
        checks["ownership_ok"] = True

        if actor.current_hp <= 0:
            checks["alive"] = False
            return AuthorizationResult(False, "invalid_action", "Dead combatants cannot act", checks)
        checks["alive"] = True

        active = get_active_combatant(encounter)
        active_id = active.id if active else None
        checks["active_actor_id"] = active_id

        if action_type != "reaction" and encounter.turn_phase == "active" and active_id and active_id != actor_id:
            return AuthorizationResult(False, "not_your_turn", "This actor is not the active turn", checks)

        return AuthorizationResult(True, checks=checks)

    @staticmethod
    def _get_or_create_in_memory_budget(encounter: EncounterState, actor_id: str) -> dict[str, Any]:
        actor = CombatService._find_actor(encounter, actor_id)
        max_movement = actor.speed.walk if actor is not None else 30

        budget = encounter.turn_budgets.get(actor_id)
        if budget is None:
            budget = {
                "action_available": True,
                "bonus_action_available": True,
                "reaction_available": True,
                "max_movement": max_movement,
                "movement_used": 0,
                "movement_remaining": max_movement,
                "round_number": encounter.round_number,
            }
            encounter.turn_budgets[actor_id] = budget

        # Ensure movement max follows actor speed and reset if round changed.
        budget["max_movement"] = max_movement
        if int(budget.get("round_number", encounter.round_number)) != encounter.round_number:
            budget["action_available"] = True
            budget["bonus_action_available"] = True
            budget["reaction_available"] = True
            budget["movement_used"] = 0
            budget["round_number"] = encounter.round_number

        budget["movement_remaining"] = max(
            int(budget.get("max_movement", max_movement)) -
            int(budget.get("movement_used", 0)),
            0,
        )
        return budget

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

    @staticmethod
    def _default_encounter(campaign_id: str) -> EncounterState:
        arannis = ActorInstance(
            id="hero_1",
            name="Arannis",
            current_hp=45,
            max_hp=45,
            owner_user_id="simon",
        )
        goblin = ActorInstance(
            id="goblin_1",
            name="Goblin",
            current_hp=7,
            max_hp=7,
        )
        return EncounterState(
            id=f"enc_{campaign_id}",
            campaign_id=campaign_id,
            combatants=[arannis, goblin],
            map=MapState(
                width=40,
                height=40,
                tokens=[
                    MapToken(actor_id="hero_1", position={"x": 5, "y": 10}),
                    MapToken(actor_id="goblin_1", position={"x": 6, "y": 11}),
                ],
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
