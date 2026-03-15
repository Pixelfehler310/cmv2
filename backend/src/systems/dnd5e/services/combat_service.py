from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.sessions.models import SessionContext, UserRole

from ..engine.combat_state import get_active_combatant, next_turn, start_combat
from ..engine.initiative import InitiativeEntry
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
        await self._persist_encounter(encounter_session, encounter)
        await self._ensure_round_budgets(encounter_session, encounter)

        active = get_active_combatant(encounter)
        active_id = active.id if active else ""
        return active_id, encounter.round_number

    async def apply_movement(
        self,
        encounter_session: EncounterSession,
        encounter: EncounterState,
        ctx: SessionContext,
        actor_id: str,
        path: list[dict[str, int]],
    ) -> AuthorizationResult:
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return AuthorizationResult(False, "invalid_target", f"Actor {actor_id} not found")

        checks = await self._base_actor_checks(encounter_session, encounter, actor_id, "move", ctx)
        if not checks.allowed:
            await self.log_action_attempt(
                encounter_session,
                request_id=None,
                actor_id=actor_id,
                action_type="move",
                action_state="denied",
                payload={"path": path},
                checks=checks.checks or {},
                denial_reason=checks.reason_code,
            )
            return checks

        distance = self._path_distance(actor.position, path)
        budget = await self._get_or_create_budget(encounter_session, actor_id, encounter.round_number, actor.speed.walk)
        movement_remaining = max(budget.max_movement - budget.movement_used, 0)
        if distance > movement_remaining:
            checks_data = checks.checks or {}
            checks_data["movement_remaining"] = movement_remaining
            checks_data["movement_required"] = distance
            await self.log_action_attempt(
                encounter_session,
                request_id=None,
                actor_id=actor_id,
                action_type="move",
                action_state="denied",
                payload={"path": path},
                checks=checks_data,
                denial_reason="movement_exceeded",
            )
            return AuthorizationResult(
                False,
                "resource_exhausted",
                "Movement exceeds remaining budget",
                checks=checks_data,
            )

        budget.movement_used += distance
        await self.db.flush()
        await self.log_action_attempt(
            encounter_session,
            request_id=None,
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

    async def check_can_act(
        self,
        encounter_session: EncounterSession,
        encounter: EncounterState,
        actor_id: str,
        action_type: str,
        ctx: SessionContext,
    ) -> AuthorizationResult:
        action_type_normalized = action_type.lower().strip() or "action"
        checks = await self._base_actor_checks(encounter_session, encounter, actor_id, action_type_normalized, ctx)
        if not checks.allowed:
            return checks

        budget = await self._get_or_create_budget(
            encounter_session,
            actor_id,
            encounter.round_number,
            self._find_actor(encounter, actor_id).speed.walk,
        )

        checks_data = checks.checks or {}
        if action_type_normalized in {"action", "attack", "cast_spell"} and not budget.action_available:
            checks_data["action_available"] = False
            return AuthorizationResult(False, "resource_exhausted", "Action already spent this turn", checks_data)

        if action_type_normalized in {"bonus_action", "bonus"} and not budget.bonus_action_available:
            checks_data["bonus_action_available"] = False
            return AuthorizationResult(False, "resource_exhausted", "Bonus action already spent this turn", checks_data)

        if action_type_normalized == "reaction" and not budget.reaction_available:
            checks_data["reaction_available"] = False
            return AuthorizationResult(False, "resource_exhausted", "Reaction already spent", checks_data)

        return AuthorizationResult(True, checks=checks_data)

    async def consume_budget(
        self,
        encounter_session: EncounterSession,
        encounter: EncounterState,
        actor_id: str,
        action_type: str,
    ) -> None:
        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return

        budget = await self._get_or_create_budget(encounter_session, actor_id, encounter.round_number, actor.speed.walk)
        normalized = action_type.lower().strip() or "action"

        if normalized in {"action", "attack", "cast_spell"}:
            budget.action_available = False
        elif normalized in {"bonus_action", "bonus"}:
            budget.bonus_action_available = False
        elif normalized == "reaction":
            budget.reaction_available = False

        await self.db.flush()

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

    async def _base_actor_checks(
        self,
        encounter_session: EncounterSession,
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
