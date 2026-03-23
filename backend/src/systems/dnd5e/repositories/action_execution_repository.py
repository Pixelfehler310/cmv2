from __future__ import annotations

from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.systems.dnd5e.lib.combat_models import (
    ActionLog,
    CombatantState,
    EncounterSession,
    TurnBudgetRecord,
)
from src.systems.dnd5e.lib.content_models import EffectInstanceRecord
from src.systems.dnd5e.schemas.encounter import EncounterState


class ActionExecutionRepositoryProtocol(Protocol):
    async def flush(self) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def create_action_log(
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
        ...

    async def list_action_logs(self, campaign_id: str, limit: int = 100) -> list[ActionLog]:
        ...

    async def load_combatant(self, encounter_session_id: str, actor_id: str) -> CombatantState | None:
        ...

    async def get_or_create_budget(
        self,
        encounter_session: EncounterSession,
        actor_id: str,
        round_number: int,
        max_movement: int,
    ) -> TurnBudgetRecord:
        ...

    async def persist_encounter(
        self,
        encounter_session: EncounterSession,
        encounter: EncounterState,
    ) -> None:
        ...

    async def sync_effect_instance_records(
        self,
        encounter_session: EncounterSession,
        encounter: EncounterState,
        provenance_by_instance: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        ...


class ActionExecutionRepository(ActionExecutionRepositoryProtocol):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def flush(self) -> None:
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def create_action_log(
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
        self._db.add(
            ActionLog(
                encounter_session_id=encounter_session.id,
                request_id=request_id,
                actor_id=actor_id,
                action_type=action_type,
                action_state=action_state,
                denial_reason=denial_reason,
                authorization_checks=checks,
                payload=payload,
            )
        )
        await self._db.flush()

    async def list_action_logs(self, campaign_id: str, limit: int = 100) -> list[ActionLog]:
        stmt = (
            select(ActionLog)
            .join(EncounterSession, ActionLog.encounter_session_id == EncounterSession.id)
            .where(EncounterSession.campaign_id == campaign_id)
            .order_by(ActionLog.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def load_combatant(self, encounter_session_id: str, actor_id: str) -> CombatantState | None:
        stmt = select(CombatantState).where(
            CombatantState.encounter_session_id == encounter_session_id,
            CombatantState.actor_id == actor_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_or_create_combatant(self, encounter_session: EncounterSession, actor_id: str) -> CombatantState:
        combatant = await self.load_combatant(encounter_session.id, actor_id)
        if combatant is not None:
            return combatant

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
        self._db.add(combatant)
        await self._db.flush()
        return combatant

    async def get_or_create_budget(
        self,
        encounter_session: EncounterSession,
        actor_id: str,
        round_number: int,
        max_movement: int,
    ) -> TurnBudgetRecord:
        combatant = await self._get_or_create_combatant(encounter_session, actor_id)

        stmt = select(TurnBudgetRecord).where(
            TurnBudgetRecord.encounter_session_id == encounter_session.id,
            TurnBudgetRecord.combatant_id == combatant.id,
            TurnBudgetRecord.round_number == round_number,
        )
        result = await self._db.execute(stmt)
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
        self._db.add(budget)
        await self._db.flush()
        return budget

    async def persist_encounter(
        self,
        encounter_session: EncounterSession,
        encounter: EncounterState,
    ) -> None:
        encounter_session.encounter_id = encounter.id
        encounter_session.phase = encounter.turn_phase
        encounter_session.round_number = encounter.round_number
        encounter_session.active_index = encounter.active_index
        encounter_session.combat_state_json = encounter.model_dump(mode="json")

        await self._sync_combatants(encounter_session, encounter)
        await self._db.flush()
        await self._db.commit()

    async def _sync_combatants(
        self,
        encounter_session: EncounterSession,
        encounter: EncounterState,
    ) -> None:
        existing_result = await self._db.execute(
            select(CombatantState).where(
                CombatantState.encounter_session_id == encounter_session.id
            )
        )
        existing_combatants = {
            c.actor_id: c for c in existing_result.scalars().all()
        }

        current_actor_ids = {actor.id for actor in encounter.combatants}

        for aid, combatant in list(existing_combatants.items()):
            if aid not in current_actor_ids:
                res = self._db.delete(combatant)
                if hasattr(res, "__await__"):
                    await res
                del existing_combatants[aid]

        for index, actor in enumerate(encounter.combatants):
            combatant = existing_combatants.get(actor.id)
            if combatant is None:
                combatant = CombatantState(
                    encounter_session_id=encounter_session.id,
                    actor_id=actor.id,
                )
                self._db.add(combatant)

            combatant.initiative_order = index
            combatant.owner_user_id = actor.owner_user_id
            combatant.current_hp = actor.current_hp
            combatant.max_hp = actor.max_hp
            combatant.pos_x = actor.position.x
            combatant.pos_y = actor.position.y
            combatant.actor_snapshot = actor.model_dump(mode="json")

        await self._db.flush()

    async def sync_effect_instance_records(
        self,
        encounter_session: EncounterSession,
        encounter: EncounterState,
        provenance_by_instance: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        existing_result = await self._db.execute(
            select(EffectInstanceRecord).where(
                EffectInstanceRecord.encounter_session_id == encounter_session.id,
            )
        )
        existing_rows = {
            row.instance_id: row for row in existing_result.scalars().all()
        }

        current_instances = []
        for actor in encounter.combatants:
            current_instances.extend(actor.effects)
        current_instance_ids = {eff.id for eff in current_instances}

        provenance_by_instance = provenance_by_instance or {}

        for instance_id, row in list(existing_rows.items()):
            if instance_id not in current_instance_ids:
                res = self._db.delete(row)
                if hasattr(res, "__await__"):
                    await res
                del existing_rows[instance_id]

        for actor in encounter.combatants:
            for effect in actor.effects:
                row = existing_rows.get(effect.id)
                if row is None:
                    row = EffectInstanceRecord(
                        id=f"eff_rec_{uuid4().hex[:8]}",
                        encounter_session_id=encounter_session.id,
                        instance_id=effect.id,
                        applied_at_round=encounter.round_number,
                    )
                    self._db.add(row)

                row.effect_id = effect.effect_id
                row.source_actor_id = effect.source_id
                row.target_actor_id = effect.target_id
                row.remaining_duration = effect.remaining_rounds
                row.stack_count = effect.value if isinstance(effect.value, int) else 1
                row.snapshot_payload = effect.model_dump(mode="json")

                if effect.id in provenance_by_instance:
                    row.provenance = provenance_by_instance[effect.id]

        await self._db.flush()
