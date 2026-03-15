"""
D&D 5e WebSocket Handler.

Routes inbound WebSocket events to the Phase 2–4 engine and returns
outbound events for broadcasting.

Per architecture doc 09 § 7.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from src.database import AsyncSessionLocal
from src.core.ws_dispatcher import ISystemHandler
from src.core.ws_protocol import WsEnvelope, WsOutbound, WsErrorCode, Visibility
from src.core.sessions.models import SessionContext, UserRole
from src.core.sessions.manager import SessionManager

from .permissions import check_permission, PermissionDenied
from .state_filter import filter_state_for_role
from .event_types import (
    ActionPayload,
    AddActorPayload,
    ChatMessagePayload,
    EndTurnPayload,
    MoveTokenPayload,
    RequestActionPayload,
    RemoveActorPayload,
    ApplyDamagePayload,
    ApplyHealingPayload,
    ApplyConditionPayload,
    RemoveConditionPayload,
    RollDicePayload,
)

from .schemas.encounter import EncounterState
from .schemas.encounter import MapToken
from .schemas.instances import ActorInstance, ConditionInstance
from .schemas.enums import ConditionType, DamageType, ActorType
from .schemas.common import AbilityScores, SpeedBlock, Position

from .engine.combat_state import (
    start_combat,
    next_turn,
    get_active_combatant,
)
from .engine.initiative import InitiativeEntry
from .engine.dice import DiceService
from .engine.damage import apply_damage
from .services.combat_service import CombatService

logger = logging.getLogger(__name__)

COMMAND_EVENT_TYPES = {
    "action",
    "request_action",
    "move_token",
    "add_actor",
    "remove_actor",
    "start_combat",
    "end_combat",
    "end_turn",
    "apply_damage",
    "apply_healing",
    "apply_condition",
    "remove_condition",
}

ACTION_EVENT_TYPES = {"action", "request_action"}


# ---------------------------------------------------------------------------
# In-memory encounter storage (MVP — single-process, no DB yet)
# ---------------------------------------------------------------------------

_encounters: dict[str, EncounterState] = {}


def get_or_create_encounter(campaign_id: str) -> EncounterState:
    """Get the encounter for a campaign, or create a default one."""
    if campaign_id not in _encounters:
        from .schemas.instances import ActorInstance
        from .schemas.encounter import MapState, MapToken

        arannis = ActorInstance(
            id="hero_1",
            name="Arannis",
            current_hp=45,
            max_hp=45
        )
        goblin = ActorInstance(
            id="goblin_1",
            name="Goblin",
            current_hp=7,
            max_hp=7
        )

        _encounters[campaign_id] = EncounterState(
            id=f"enc_{campaign_id}",
            campaign_id=campaign_id,
            combatants=[arannis, goblin],
            map=MapState(
                width=40,
                height=40,
                tokens=[
                    MapToken(actor_id="hero_1", position={"x": 5, "y": 10}),
                    MapToken(actor_id="goblin_1", position={"x": 6, "y": 11})
                ]
            )
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
        encounter = await self._load_encounter(ctx.campaign_id)
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
        """Route inbound events through permission, validation, execution, and terminal publish.

        Lifecycle:
        1) envelope accepted
        2) role permission gate
        3) command request_id gate (for command-like events)
        4) payload/domain validation and authorization
        5) state mutation + optional persistence
        6) terminal outbound event(s): success, denied, or error
        """

        event_type = envelope.type

        # --- Permission check ---
        try:
            check_permission(event_type, ctx)
        except PermissionDenied as e:
            return self._attach_request_id(
                [
                    self._denied(
                        event_type,
                        str(e),
                        e.code.value,
                        ctx,
                        envelope.request_id,
                    )
                ],
                envelope.request_id,
            )

        if event_type in COMMAND_EVENT_TYPES and not envelope.request_id:
            return [
                self._error(
                    "request_id is required for command events",
                    WsErrorCode.INVALID_MESSAGE,
                    ctx,
                    envelope.request_id,
                )
            ]

        # --- Dispatch ---
        results: list[WsOutbound] | None = None

        async with AsyncSessionLocal() as db:
            service = CombatService(db)
            encounter = await self._load_encounter(ctx.campaign_id, service)
            if ctx.campaign_id in _encounters:
                encounter_session = None
            else:
                try:
                    encounter_session = await service._load_session(ctx.campaign_id)
                except Exception:
                    logger.exception(
                        "Falling back to in-memory encounter session for campaign=%s", ctx.campaign_id)
                    encounter_session = None

            if event_type == "ping":
                results = self._handle_ping(ctx)

            elif event_type == "request_sync":
                results = self._handle_request_sync(encounter, ctx)

            elif event_type == "roll_dice":
                results = self._handle_roll_dice(envelope, ctx)

            elif event_type == "chat_message":
                results = self._handle_chat_message(envelope, ctx)

            elif event_type == "action":
                results = await self._handle_action(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "request_action":
                results = await self._handle_request_action(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "move_token":
                events = await self._handle_move_token(encounter, encounter_session, service, envelope, ctx)
                if encounter_session is not None and not self._is_error_only(events):
                    await service.save_full_state(encounter_session, encounter)
                results = events

            elif event_type == "add_actor":
                events = self._handle_add_actor(encounter, envelope)
                if encounter_session is not None and not self._is_error_only(events):
                    await service.save_full_state(encounter_session, encounter)
                results = events

            elif event_type == "remove_actor":
                events = self._handle_remove_actor(encounter, envelope)
                if encounter_session is not None and not self._is_error_only(events):
                    await service.save_full_state(encounter_session, encounter)
                results = events

            elif event_type == "end_turn":
                results = await self._handle_end_turn(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "start_combat":
                results = await self._handle_start_combat(encounter, encounter_session, service, envelope)

            elif event_type == "end_combat":
                events = self._handle_end_combat(encounter)
                if encounter_session is not None:
                    await service.save_full_state(encounter_session, encounter)
                results = events

            elif event_type == "apply_damage":
                events = self._handle_apply_damage(encounter, envelope)
                if encounter_session is not None and not self._is_error_only(events):
                    await service.save_full_state(encounter_session, encounter)
                results = events

            elif event_type == "apply_healing":
                events = self._handle_apply_healing(encounter, envelope)
                if encounter_session is not None and not self._is_error_only(events):
                    await service.save_full_state(encounter_session, encounter)
                results = events

            elif event_type == "apply_condition":
                events = self._handle_apply_condition(encounter, envelope)
                if encounter_session is not None and not self._is_error_only(events):
                    await service.save_full_state(encounter_session, encounter)
                results = events

            elif event_type == "remove_condition":
                events = self._handle_remove_condition(encounter, envelope)
                if encounter_session is not None and not self._is_error_only(events):
                    await service.save_full_state(encounter_session, encounter)
                results = events

        if results is not None:
            return self._attach_request_id(results, envelope.request_id)

        # Unknown event
        return self._attach_request_id(
            [
                WsOutbound(
                    type="error",
                    payload={
                        "message": f"Unknown event type: {event_type}",
                        "code": WsErrorCode.INVALID_MESSAGE.value,
                    },
                    visibility=Visibility.ALL,
                    target_user_id=ctx.user_id,
                )
            ],
            envelope.request_id,
        )

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

    def _handle_chat_message(
        self, envelope: WsEnvelope, ctx: SessionContext
    ) -> list[WsOutbound]:
        try:
            payload = ChatMessagePayload.model_validate(envelope.payload)
        except Exception:
            return [self._error("Invalid chat_message payload", WsErrorCode.INVALID_MESSAGE, ctx)]

        message = payload.message.strip()
        if not message:
            return [self._error("chat_message cannot be empty", WsErrorCode.INVALID_MESSAGE, ctx)]

        return [
            WsOutbound(
                type="chat_message",
                payload={
                    "sender_id": ctx.user_id,
                    "sender_name": ctx.display_name,
                    "sender_role": ctx.role.value,
                    "message": message,
                },
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_action(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        try:
            payload = ActionPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error("Invalid action payload", WsErrorCode.INVALID_MESSAGE, ctx)]

        return await self._authorize_and_log_action(
            encounter,
            encounter_session,
            service,
            actor_id=payload.actor_id,
            action_type=payload.action_type,
            action_name=payload.action_name,
            request_id=envelope.request_id,
            ctx=ctx,
            raw_payload=payload.model_dump(mode="json"),
        )

    async def _handle_request_action(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        try:
            payload = RequestActionPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error("Invalid request_action payload", WsErrorCode.INVALID_MESSAGE, ctx)]

        return await self._authorize_and_log_action(
            encounter,
            encounter_session,
            service,
            actor_id=payload.actor_id,
            action_type=payload.action_type,
            action_name=payload.action_name,
            request_id=envelope.request_id,
            ctx=ctx,
            raw_payload=payload.model_dump(mode="json"),
        )

    async def _authorize_and_log_action(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        actor_id: str,
        action_type: str,
        action_name: str,
        request_id: str | None,
        ctx: SessionContext,
        raw_payload: dict,
    ) -> list[WsOutbound]:
        if encounter_session is None:
            return [
                WsOutbound(
                    type="action_authorized",
                    payload={
                        "actor_id": actor_id,
                        "action_type": action_type,
                        "action_name": action_name,
                    },
                    visibility=Visibility.ALL,
                )
            ]

        auth = await service.check_can_act(
            encounter_session,
            encounter,
            actor_id=actor_id,
            action_type=action_type,
            ctx=ctx,
        )
        if not auth.allowed:
            await service.log_action_attempt(
                encounter_session,
                request_id=request_id,
                actor_id=actor_id,
                action_type=action_type,
                action_state="denied",
                payload=raw_payload,
                checks=auth.checks or {},
                denial_reason=auth.reason_code,
            )
            return [
                self._denied(
                    "action",
                    auth.message or "Action denied",
                    auth.reason_code or "invalid_action",
                    ctx,
                    request_id,
                    actor_id=actor_id,
                    action_type=action_type,
                )
            ]

        await service.consume_budget(encounter_session, encounter, actor_id, action_type)
        await service.log_action_attempt(
            encounter_session,
            request_id=request_id,
            actor_id=actor_id,
            action_type=action_type,
            action_state="authorized",
            payload=raw_payload,
            checks=auth.checks or {},
            denial_reason=None,
        )
        await service.save_full_state(encounter_session, encounter)
        return [
            WsOutbound(
                type="action_authorized",
                payload={
                    "actor_id": actor_id,
                    "action_type": action_type,
                    "action_name": action_name,
                },
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_end_turn(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        if encounter.turn_phase != "active":
            return [
                self._denied(
                    "end_turn",
                    "Cannot end turn when combat is not active",
                    "invalid_action",
                    ctx,
                    envelope.request_id,
                )
            ]

        if encounter_session is None:
            next_turn(encounter)
            active = get_active_combatant(encounter)
            active_id = active.id if active else ""
        else:
            active_id, _ = await service.advance_turn(encounter_session, encounter)

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

    async def _handle_move_token(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        try:
            payload = MoveTokenPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid move_token payload", WsErrorCode.INVALID_MESSAGE)]

        if not payload.path:
            return [self._error_raw("move_token path cannot be empty", WsErrorCode.INVALID_MESSAGE)]

        actor = self._find_actor(encounter, payload.actor_id)
        if actor is None:
            return [self._error_raw(f"Actor {payload.actor_id} not found", WsErrorCode.INVALID_TARGET)]

        if encounter_session is not None:
            auth = await service.apply_movement(
                encounter_session,
                encounter,
                ctx,
                payload.actor_id,
                payload.path,
                envelope.request_id,
            )
            if not auth.allowed:
                return [
                    self._denied(
                        "move_token",
                        auth.message or "Movement denied",
                        auth.reason_code or "invalid_action",
                        ctx,
                        envelope.request_id,
                        actor_id=payload.actor_id,
                    )
                ]

        validated_path: list[dict[str, int]] = []
        for step in payload.path:
            try:
                pos = Position.model_validate(step)
            except Exception:
                return [self._error_raw("move_token path contains invalid coordinates", WsErrorCode.INVALID_MESSAGE)]

            if pos.x < 0 or pos.y < 0 or pos.x >= encounter.map.width or pos.y >= encounter.map.height:
                return [self._error_raw("move_token target is out of map bounds", WsErrorCode.INVALID_ACTION)]

            validated_path.append({"x": pos.x, "y": pos.y})

        final_step = validated_path[-1]
        actor.position = Position(x=final_step["x"], y=final_step["y"])

        token = self._find_map_token(encounter, payload.actor_id)
        if token is None:
            token = MapToken(actor_id=payload.actor_id,
                             position=actor.position)
            encounter.map.tokens.append(token)
        else:
            token.position = actor.position

        return [
            WsOutbound(
                type="actor_moved",
                payload={
                    "actor_id": payload.actor_id,
                    "path": validated_path,
                    "position": final_step,
                },
                visibility=Visibility.ALL,
            )
        ]

    def _handle_add_actor(
        self, encounter: EncounterState, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = AddActorPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid add_actor payload", WsErrorCode.INVALID_MESSAGE)]

        definition_slug = payload.definition_slug.strip()
        if not definition_slug:
            return [self._error_raw("add_actor definition_slug cannot be empty", WsErrorCode.INVALID_MESSAGE)]

        if payload.position is not None:
            try:
                position = Position.model_validate(payload.position)
            except Exception:
                return [self._error_raw("Invalid add_actor position", WsErrorCode.INVALID_MESSAGE)]
        else:
            position = Position()

        if (
            position.x < 0
            or position.y < 0
            or position.x >= encounter.map.width
            or position.y >= encounter.map.height
        ):
            return [self._error_raw("add_actor target is out of map bounds", WsErrorCode.INVALID_ACTION)]

        actor_id = self._next_actor_id(encounter, definition_slug)
        actor_name = (payload.name or "").strip(
        ) or self._display_name_from_slug(definition_slug)

        actor = ActorInstance(
            id=actor_id,
            owner_user_id=payload.owner_user_id,
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

        return [
            WsOutbound(
                type="actor_added",
                payload={
                    "actor": {
                        "id": actor.id,
                        "owner_user_id": actor.owner_user_id,
                        "definition_slug": actor.definition_slug,
                        "name": actor.name,
                        "actor_type": actor.actor_type.value,
                        "position": token.position.model_dump(mode="json"),
                    },
                    "token": token.model_dump(mode="json"),
                },
                visibility=Visibility.ALL,
            )
        ]

    def _handle_remove_actor(
        self, encounter: EncounterState, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = RemoveActorPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid remove_actor payload", WsErrorCode.INVALID_MESSAGE)]

        actor = self._find_actor(encounter, payload.actor_id)
        if actor is None:
            return [self._error_raw(f"Actor {payload.actor_id} not found", WsErrorCode.INVALID_TARGET)]

        encounter.combatants = [
            c for c in encounter.combatants if c.id != payload.actor_id]
        encounter.map.tokens = [
            t for t in encounter.map.tokens if t.actor_id != payload.actor_id]

        if not encounter.combatants:
            encounter.active_index = 0
            encounter.turn_phase = "post_combat"
        elif encounter.active_index >= len(encounter.combatants):
            encounter.active_index = 0

        return [
            WsOutbound(
                type="actor_removed",
                payload={"actor_id": payload.actor_id},
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_start_combat(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
    ) -> list[WsOutbound]:
        if not encounter.combatants:
            return [self._error_raw("No combatants to start combat", WsErrorCode.INVALID_ACTION, envelope.request_id)]

        if encounter_session is None:
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
        else:
            order = await service.start_combat(encounter_session, encounter)

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

        result = apply_damage(actor, amount=payload.amount,
                              damage_type=damage_type)

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
    def _find_map_token(encounter: EncounterState, actor_id: str) -> Optional[MapToken]:
        for token in encounter.map.tokens:
            if token.actor_id == actor_id:
                return token
        return None

    @staticmethod
    def _display_name_from_slug(definition_slug: str) -> str:
        cleaned = re.sub(r"[_-]+", " ", definition_slug).strip()
        if not cleaned:
            return "Monster"
        return " ".join(part.capitalize() for part in cleaned.split())

    @staticmethod
    def _next_actor_id(encounter: EncounterState, definition_slug: str) -> str:
        slug_base = re.sub(r"[^a-z0-9]+", "_",
                           definition_slug.lower()).strip("_")
        if not slug_base:
            slug_base = "actor"

        existing_ids = {actor.id for actor in encounter.combatants}
        index = 1
        while f"{slug_base}_{index}" in existing_ids:
            index += 1
        return f"{slug_base}_{index}"

    @staticmethod
    def _error(message: str, code: WsErrorCode, ctx: SessionContext, request_id: str | None = None) -> WsOutbound:
        return WsOutbound(
            type="error",
            request_id=request_id,
            payload={"message": message, "code": code.value},
            visibility=Visibility.ACTOR_OWNER,
            target_user_id=ctx.user_id,
        )

    @staticmethod
    def _error_raw(message: str, code: WsErrorCode, request_id: str | None = None) -> WsOutbound:
        return WsOutbound(
            type="error",
            request_id=request_id,
            payload={"message": message, "code": code.value},
            visibility=Visibility.ALL,
        )

    @staticmethod
    def _denied_event_type(event_type: str) -> str:
        return "action_denied" if event_type in ACTION_EVENT_TYPES else "command_denied"

    @classmethod
    def _denied(
        cls,
        event_type: str,
        message: str,
        reason_code: str,
        ctx: SessionContext,
        request_id: str | None,
        actor_id: str | None = None,
        action_type: str | None = None,
    ) -> WsOutbound:
        payload: dict[str, str] = {
            "event_type": event_type,
            "reason_code": reason_code,
            "message": message,
        }
        if actor_id:
            payload["actor_id"] = actor_id
        if action_type:
            payload["action_type"] = action_type

        return WsOutbound(
            type=cls._denied_event_type(event_type),
            request_id=request_id,
            payload=payload,
            visibility=Visibility.ACTOR_OWNER,
            target_user_id=ctx.user_id,
        )

    @staticmethod
    def _attach_request_id(events: list[WsOutbound], request_id: str | None) -> list[WsOutbound]:
        for event in events:
            if event.request_id is None:
                event.request_id = request_id
        return events

    async def _load_encounter(
        self,
        campaign_id: str,
        service: CombatService | None = None,
    ) -> EncounterState:
        if campaign_id in _encounters:
            return _encounters[campaign_id]

        if service is not None:
            try:
                _, encounter = await service.load_or_create_encounter_state(campaign_id)
                return encounter
            except Exception:
                logger.exception(
                    "Falling back to in-memory encounter loading for campaign=%s", campaign_id)
                return get_or_create_encounter(campaign_id)

        try:
            async with AsyncSessionLocal() as db:
                local_service = CombatService(db)
                _, encounter = await local_service.load_or_create_encounter_state(campaign_id)
                return encounter
        except Exception:
            logger.exception(
                "Falling back to in-memory encounter loading for campaign=%s", campaign_id)
            return get_or_create_encounter(campaign_id)

    @staticmethod
    def _is_error_only(events: list[WsOutbound]) -> bool:
        return bool(events) and all(event.type in {"error", "action_denied", "command_denied"} for event in events)
