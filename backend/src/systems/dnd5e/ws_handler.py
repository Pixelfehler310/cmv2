"""
D&D 5e WebSocket Handler.

Routes inbound WebSocket events to the Phase 2–4 engine and returns
outbound events for broadcasting.

Per architecture doc 09 § 7.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.core.ws_dispatcher import ISystemHandler
from src.core.ws_protocol import WsEnvelope, WsOutbound, WsErrorCode, Visibility
from src.core.sessions.models import SessionContext, UserRole
from src.core.sessions.manager import SessionManager

from .permissions import check_permission, PermissionDenied
from .state_filter import filter_state_for_role
from .event_types import (
    EndTurnPayload,
    ApplyDamagePayload,
    ApplyHealingPayload,
    ApplyConditionPayload,
    RemoveConditionPayload,
    RollDicePayload,
)

from .schemas.encounter import EncounterState
from .schemas.instances import ActorInstance, ConditionInstance
from .schemas.enums import ConditionType, DamageType, ActorType
from .schemas.common import AbilityScores, SpeedBlock

from .engine.combat_state import (
    start_combat,
    next_turn,
    get_active_combatant,
    get_turn_budget,
)
from .engine.initiative import InitiativeEntry
from .engine.dice import DiceService
from .engine.damage import apply_damage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory encounter storage (MVP — single-process, no DB yet)
# ---------------------------------------------------------------------------

_encounters: dict[str, EncounterState] = {}


def get_or_create_encounter(campaign_id: str) -> EncounterState:
    """Get the encounter for a campaign, or create a default one."""
    if campaign_id not in _encounters:
        _encounters[campaign_id] = EncounterState(
            id=f"enc_{campaign_id}",
            campaign_id=campaign_id,
        )
    return _encounters[campaign_id]


def set_encounter(campaign_id: str, encounter: EncounterState) -> None:
    """Replace the encounter state for a campaign (for testing)."""
    _encounters[campaign_id] = encounter


def clear_encounters() -> None:
    """Clear all encounters (for testing)."""
    _encounters.clear()


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

class Dnd5eWsHandler(ISystemHandler):
    """D&D 5e WebSocket event handler."""

    async def on_connect(
        self, ctx: SessionContext, mgr: SessionManager
    ) -> list[WsOutbound]:
        """Send initial state_sync on connection."""
        encounter = get_or_create_encounter(ctx.campaign_id)
        state_data = filter_state_for_role(encounter, ctx)

        return [
            WsOutbound(
                type="state_sync",
                payload=state_data,
                visibility=Visibility.ALL,
            )
        ]

    async def on_disconnect(self, ctx: SessionContext, mgr: SessionManager) -> None:
        """Cleanup on disconnect — nothing needed for MVP."""
        pass

    async def handle(
        self, envelope: WsEnvelope, ctx: SessionContext, mgr: SessionManager
    ) -> list[WsOutbound]:
        """Route an inbound event to the appropriate engine function."""

        # --- Permission check ---
        try:
            check_permission(envelope.type, ctx)
        except PermissionDenied as e:
            return [
                WsOutbound(
                    type="error",
                    payload={"message": str(e), "code": e.code.value},
                    visibility=Visibility.ALL,
                    target_user_id=ctx.user_id,
                )
            ]

        # --- Dispatch ---
        event_type = envelope.type
        encounter = get_or_create_encounter(ctx.campaign_id)

        if event_type == "ping":
            return self._handle_ping(ctx)

        if event_type == "request_sync":
            return self._handle_request_sync(encounter, ctx)

        if event_type == "roll_dice":
            return self._handle_roll_dice(envelope, ctx)

        if event_type == "end_turn":
            return self._handle_end_turn(encounter, envelope)

        if event_type == "start_combat":
            return self._handle_start_combat(encounter)

        if event_type == "end_combat":
            return self._handle_end_combat(encounter)

        if event_type == "apply_damage":
            return self._handle_apply_damage(encounter, envelope)

        if event_type == "apply_healing":
            return self._handle_apply_healing(encounter, envelope)

        if event_type == "apply_condition":
            return self._handle_apply_condition(encounter, envelope)

        if event_type == "remove_condition":
            return self._handle_remove_condition(encounter, envelope)

        # Unknown event
        return [
            WsOutbound(
                type="error",
                payload={
                    "message": f"Unknown event type: {event_type}",
                    "code": WsErrorCode.INVALID_MESSAGE.value,
                },
                visibility=Visibility.ALL,
                target_user_id=ctx.user_id,
            )
        ]

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def _handle_ping(self, ctx: SessionContext) -> list[WsOutbound]:
        return [
            WsOutbound(
                type="pong",
                payload={},
                visibility=Visibility.ACTOR_OWNER,
                target_user_id=ctx.user_id,
            )
        ]

    def _handle_request_sync(
        self, encounter: EncounterState, ctx: SessionContext
    ) -> list[WsOutbound]:
        state_data = filter_state_for_role(encounter, ctx)
        return [
            WsOutbound(
                type="state_sync",
                payload=state_data,
                visibility=Visibility.ACTOR_OWNER,
                target_user_id=ctx.user_id,
            )
        ]

    def _handle_roll_dice(
        self, envelope: WsEnvelope, ctx: SessionContext
    ) -> list[WsOutbound]:
        try:
            payload = RollDicePayload.model_validate(envelope.payload)
        except Exception:
            return [self._error("Invalid roll_dice payload", WsErrorCode.INVALID_MESSAGE, ctx)]

        result = DiceService.roll(payload.expression)

        return [
            WsOutbound(
                type="dice_rolled",
                payload={
                    "roller_id": ctx.user_id,
                    "expression": payload.expression,
                    "result": result.total,
                    "purpose": payload.purpose,
                },
                visibility=Visibility.ALL,
            )
        ]

    def _handle_end_turn(
        self, encounter: EncounterState, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        if encounter.turn_phase != "active":
            return []

        next_turn(encounter)
        active = get_active_combatant(encounter)
        active_id = active.id if active else ""

        return [
            WsOutbound(
                type="turn_advanced",
                payload={
                    "active_actor_id": active_id,
                    "round": encounter.round_number,
                },
                visibility=Visibility.ALL,
            )
        ]

    def _handle_start_combat(self, encounter: EncounterState) -> list[WsOutbound]:
        if not encounter.combatants:
            return [self._error_raw("No combatants to start combat", WsErrorCode.INVALID_ACTION)]

        # Roll initiative for all combatants
        initiatives = []
        for actor in encounter.combatants:
            roll = DiceService.roll("1d20")
            dex_mod = (actor.abilities.dexterity - 10) // 2
            initiatives.append(
                InitiativeEntry(
                    actor_id=actor.id,
                    roll=roll.total + dex_mod,
                    dex_score=actor.abilities.dexterity,
                )
            )

        start_combat(encounter, initiatives)

        order = [
            {"actor_id": a.id, "name": a.name}
            for a in encounter.combatants
        ]

        return [
            WsOutbound(
                type="combat_started",
                payload={"initiative_order": order},
                visibility=Visibility.ALL,
            )
        ]

    def _handle_end_combat(self, encounter: EncounterState) -> list[WsOutbound]:
        encounter.turn_phase = "post_combat"
        encounter.round_number = 0
        encounter.active_index = 0

        return [
            WsOutbound(
                type="combat_ended",
                payload={},
                visibility=Visibility.ALL,
            )
        ]

    def _handle_apply_damage(
        self, encounter: EncounterState, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = ApplyDamagePayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid apply_damage payload", WsErrorCode.INVALID_MESSAGE)]

        actor = self._find_actor(encounter, payload.actor_id)
        if actor is None:
            return [self._error_raw(f"Actor {payload.actor_id} not found", WsErrorCode.INVALID_TARGET)]

        try:
            damage_type = DamageType(payload.damage_type)
        except ValueError:
            damage_type = DamageType.SLASHING

        result = apply_damage(actor, amount=payload.amount, damage_type=damage_type)

        # apply_damage returns a result but doesn't mutate the actor
        actor.current_hp = result.remaining_hp
        actor.temp_hp = result.remaining_temp_hp

        events: list[WsOutbound] = [
            WsOutbound(
                type="actor_damaged",
                payload={
                    "actor_id": payload.actor_id,
                    "amount": result.damage_dealt,
                    "new_hp": actor.current_hp,
                    "source": "dm_override",
                },
                visibility=Visibility.ALL,
            )
        ]

        if result.is_dead:
            events.append(
                WsOutbound(
                    type="actor_died",
                    payload={"actor_id": payload.actor_id},
                    visibility=Visibility.ALL,
                )
            )

        return events

    def _handle_apply_healing(
        self, encounter: EncounterState, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = ApplyHealingPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid apply_healing payload", WsErrorCode.INVALID_MESSAGE)]

        actor = self._find_actor(encounter, payload.actor_id)
        if actor is None:
            return [self._error_raw(f"Actor {payload.actor_id} not found", WsErrorCode.INVALID_TARGET)]

        old_hp = actor.current_hp
        actor.current_hp = min(actor.max_hp, actor.current_hp + payload.amount)
        healed = actor.current_hp - old_hp

        return [
            WsOutbound(
                type="actor_healed",
                payload={
                    "actor_id": payload.actor_id,
                    "amount": healed,
                    "new_hp": actor.current_hp,
                },
                visibility=Visibility.ALL,
            )
        ]

    def _handle_apply_condition(
        self, encounter: EncounterState, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = ApplyConditionPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid apply_condition payload", WsErrorCode.INVALID_MESSAGE)]

        actor = self._find_actor(encounter, payload.actor_id)
        if actor is None:
            return [self._error_raw(f"Actor {payload.actor_id} not found", WsErrorCode.INVALID_TARGET)]

        try:
            condition = ConditionType(payload.condition)
        except ValueError:
            return [self._error_raw(f"Unknown condition: {payload.condition}", WsErrorCode.INVALID_ACTION)]

        actor.conditions.append(
            ConditionInstance(
                condition=condition,
                source_id=payload.source_id or "",
            )
        )

        return [
            WsOutbound(
                type="condition_added",
                payload={
                    "actor_id": payload.actor_id,
                    "condition": condition.value,
                    "source": payload.source_id or "",
                },
                visibility=Visibility.ALL,
            )
        ]

    def _handle_remove_condition(
        self, encounter: EncounterState, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = RemoveConditionPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid remove_condition payload", WsErrorCode.INVALID_MESSAGE)]

        actor = self._find_actor(encounter, payload.actor_id)
        if actor is None:
            return [self._error_raw(f"Actor {payload.actor_id} not found", WsErrorCode.INVALID_TARGET)]

        try:
            condition = ConditionType(payload.condition)
        except ValueError:
            return [self._error_raw(f"Unknown condition: {payload.condition}", WsErrorCode.INVALID_ACTION)]

        actor.conditions = [
            c for c in actor.conditions if c.condition != condition
        ]

        return [
            WsOutbound(
                type="condition_removed",
                payload={
                    "actor_id": payload.actor_id,
                    "condition": condition.value,
                },
                visibility=Visibility.ALL,
            )
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_actor(encounter: EncounterState, actor_id: str) -> Optional[ActorInstance]:
        for actor in encounter.combatants:
            if actor.id == actor_id:
                return actor
        return None

    @staticmethod
    def _error(message: str, code: WsErrorCode, ctx: SessionContext) -> WsOutbound:
        return WsOutbound(
            type="error",
            payload={"message": message, "code": code.value},
            visibility=Visibility.ACTOR_OWNER,
            target_user_id=ctx.user_id,
        )

    @staticmethod
    def _error_raw(message: str, code: WsErrorCode) -> WsOutbound:
        return WsOutbound(
            type="error",
            payload={"message": message, "code": code.value},
            visibility=Visibility.ALL,
        )
