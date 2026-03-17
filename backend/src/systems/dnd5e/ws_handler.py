"""
D&D 5e WebSocket Handler.

Routes inbound WebSocket events to the Phase 2–4 engine and returns
outbound events for broadcasting.

Per architecture doc 09 § 7.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from src.config import settings
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
    RequestAttackPreviewPayload,
    RequestExecutableActionsPayload,
    RequestMovePreviewPayload,
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
from .schemas.enums import Ability, ActionType, ConditionType, DamageType, ActorType
from .schemas.common import AbilityScores, SaveRequirement, SpeedBlock, Position
from .schemas.definitions import ActionDefinition

from .engine.combat_state import (
    start_combat,
    next_turn,
    get_active_combatant,
)
from .engine.initiative import InitiativeEntry
from .engine.dice import DiceService
from .engine.damage import apply_damage
from .engine.action_resolver import resolve_attack, resolve_healing, resolve_save_action
from .services.combat_service import CombatService

logger = logging.getLogger(__name__)

COMMAND_EVENT_TYPES = {
    "action",
    "request_action",
    "request_executable_actions",
    "request_attack_preview",
    "request_move_preview",
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

TURN_DENIED_REASON_INVALID_PHASE = "invalid_turn_phase"
TURN_DENIED_REASON_NOT_ACTIVE_ACTOR = "not_your_turn"
TURN_DENIED_REASON_NO_ACTIVE_ACTOR = "no_active_actor"

ACTION_FAMILY_ATTACK = "attack"
ACTION_FAMILY_SAVE = "save"
ACTION_FAMILY_HEALING = "healing"
ACTION_FAMILY_UTILITY = "utility"


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

    @staticmethod
    def _resolve_impersonated_ctx(ctx: SessionContext, acting_as_user_id: Optional[str]) -> SessionContext:
        """Allow DMs to simulate player-level auth checks for debug tooling."""
        if ctx.role != UserRole.DM:
            return ctx

        candidate = (acting_as_user_id or "").strip()
        if not candidate:
            return ctx

        return SessionContext(
            campaign_id=ctx.campaign_id,
            user_id=candidate,
            display_name=ctx.display_name,
            role=UserRole.PLAYER,
            game_system=ctx.game_system,
        )

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

            elif event_type == "request_executable_actions":
                results = await self._handle_request_executable_actions(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "request_attack_preview":
                results = await self._handle_request_attack_preview(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "request_move_preview":
                results = await self._handle_request_move_preview(encounter, encounter_session, service, envelope, ctx)

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

        return await self._execute_action_command(
            encounter,
            encounter_session,
            service,
            actor_id=payload.actor_id,
            action_type=service.normalize_action_type(payload.action_type),
            action_name=payload.action_name,
            target_ids=payload.target_ids,
            action_payload={},
            request_id=envelope.request_id,
            ctx=ctx,
            response_ctx=ctx,
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

        effective_ctx = self._resolve_impersonated_ctx(
            ctx, payload.acting_as_user_id)

        requested_target_ids = []
        raw_target_ids = payload.payload.get(
            "target_ids", []) if isinstance(payload.payload, dict) else []
        if isinstance(raw_target_ids, list):
            requested_target_ids = [
                str(target_id) for target_id in raw_target_ids if isinstance(target_id, str)]

        return await self._execute_action_command(
            encounter,
            encounter_session,
            service,
            actor_id=payload.actor_id,
            action_type=service.normalize_action_type(payload.action_type),
            action_name=payload.action_name,
            target_ids=requested_target_ids,
            action_payload=payload.payload,
            request_id=envelope.request_id,
            ctx=effective_ctx,
            response_ctx=ctx,
            raw_payload=payload.model_dump(mode="json"),
            require_canonical_action_id=not settings.ALLOW_LEGACY_ACTION_NAMES,
        )

    async def _execute_action_command(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        actor_id: str,
        action_type: str,
        action_name: str,
        target_ids: list[str],
        action_payload: dict[str, Any],
        request_id: str | None,
        ctx: SessionContext,
        response_ctx: SessionContext,
        raw_payload: dict,
        require_canonical_action_id: bool = False,
    ) -> list[WsOutbound]:
        auth = await service.check_can_act(
            encounter_session,
            encounter,
            actor_id=actor_id,
            action_type=action_type,
            ctx=ctx,
        )
        if not auth.allowed:
            if encounter_session is not None:
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
                    response_ctx,
                    request_id,
                    actor_id=actor_id,
                    action_type=action_type,
                )
            ]

        actor = self._find_actor(encounter, actor_id)
        if actor is None:
            return [
                self._denied(
                    "action",
                    f"Actor {actor_id} not found",
                    "invalid_target",
                    response_ctx,
                    request_id,
                    actor_id=actor_id,
                    action_type=action_type,
                )
            ]

        requested_template_origin = None
        requested_template_direction = None
        if isinstance(action_payload, dict):
            raw_template_origin = action_payload.get("template_origin")
            raw_template_direction = action_payload.get("template_direction")
            if isinstance(raw_template_origin, dict):
                requested_template_origin = raw_template_origin
            if isinstance(raw_template_direction, dict):
                requested_template_direction = raw_template_direction

        canonical_meta = await service.get_action_execution_metadata(
            encounter,
            actor_id,
            action_name,
        )
        if require_canonical_action_id and not canonical_meta.found:
            if encounter_session is not None:
                await service.log_action_attempt(
                    encounter_session,
                    request_id=request_id,
                    actor_id=actor_id,
                    action_type=action_type,
                    action_state="denied",
                    payload=raw_payload,
                    checks=auth.checks or {},
                    denial_reason="invalid_action",
                )
            return [
                self._denied(
                    "action",
                    "Unknown canonical action_id for actor",
                    "invalid_action",
                    response_ctx,
                    request_id,
                    actor_id=actor_id,
                    action_type=action_type,
                )
            ]

        resolved_action_type = action_type
        if canonical_meta.found and canonical_meta.action_type_cost:
            resolved_action_type = service.normalize_action_type(
                canonical_meta.action_type_cost)
            if resolved_action_type != action_type:
                budget_check = await service.check_can_act(
                    encounter_session,
                    encounter,
                    actor_id=actor_id,
                    action_type=resolved_action_type,
                    ctx=ctx,
                )
                if not budget_check.allowed:
                    if encounter_session is not None:
                        await service.log_action_attempt(
                            encounter_session,
                            request_id=request_id,
                            actor_id=actor_id,
                            action_type=resolved_action_type,
                            action_state="denied",
                            payload=raw_payload,
                            checks=budget_check.checks or {},
                            denial_reason=budget_check.reason_code,
                        )
                    return [
                        self._denied(
                            "action",
                            budget_check.message or "Action denied",
                            budget_check.reason_code or "invalid_action",
                            response_ctx,
                            request_id,
                            actor_id=actor_id,
                            action_type=resolved_action_type,
                        )
                    ]

        should_validate_preview = bool(
            target_ids) or requested_template_origin is not None
        if should_validate_preview:
            preview = await service.get_attack_preview(
                encounter_session,
                encounter,
                ctx,
                actor_id,
                action_name,
                template_origin=requested_template_origin,
                template_direction=requested_template_direction,
            )
            if preview.allowed:
                eligible_target_ids = set(preview.eligible_target_ids or [])
                if target_ids:
                    invalid_targets = [
                        target_id for target_id in target_ids if target_id not in eligible_target_ids]
                    if invalid_targets:
                        return [
                            self._denied(
                                "action",
                                f"Selected target is not eligible for action '{action_name}'",
                                "invalid_target",
                                response_ctx,
                                request_id,
                                actor_id=actor_id,
                                action_type=action_type,
                            )
                        ]
                elif requested_template_origin is not None and eligible_target_ids:
                    target_ids = list(preview.eligible_target_ids or [])

                if requested_template_origin is not None and preview.template_projection is None:
                    return [
                        self._denied(
                            "action",
                            "Action template selection is not valid for this action",
                            "invalid_target",
                            response_ctx,
                            request_id,
                            actor_id=actor_id,
                            action_type=action_type,
                        )
                    ]
            elif preview.reason_code != "invalid_action":
                return [
                    self._denied(
                        "action",
                        preview.message or "Target eligibility check failed",
                        preview.reason_code or "invalid_action",
                        response_ctx,
                        request_id,
                        actor_id=actor_id,
                        action_type=action_type,
                    )
                ]

        targets: list[ActorInstance] = []
        for target_id in target_ids:
            target = self._find_actor(encounter, target_id)
            if target is None:
                return [
                    self._denied(
                        "action",
                        f"Target actor {target_id} not found",
                        "invalid_target",
                        response_ctx,
                        request_id,
                        actor_id=actor_id,
                        action_type=action_type,
                    )
                ]
            targets.append(target)

        family = canonical_meta.family if canonical_meta.found and canonical_meta.family else self._resolve_action_family(
            action_name, action_payload, targets)
        if family is None:
            if encounter_session is not None:
                await service.log_action_attempt(
                    encounter_session,
                    request_id=request_id,
                    actor_id=actor_id,
                    action_type=action_type,
                    action_state="denied",
                    payload=raw_payload,
                    checks=auth.checks or {},
                    denial_reason="unsupported_action",
                )
            return [
                self._denied(
                    "action",
                    "Unsupported action family",
                    "unsupported_action",
                    response_ctx,
                    request_id,
                    actor_id=actor_id,
                    action_type=resolved_action_type,
                )
            ]

        await service.consume_budget(encounter_session, encounter, actor_id, resolved_action_type)

        budget_snapshot = await service.get_turn_budget_snapshot(encounter_session, encounter)

        events: list[WsOutbound] = [
            WsOutbound(
                type="action_authorized",
                payload={
                    "actor_id": actor_id,
                    "action_type": resolved_action_type,
                    "action_name": action_name,
                    "family": family,
                    "turn_budget": budget_snapshot,
                },
                visibility=Visibility.ALL,
            )
        ]

        family_events = self._resolve_action_family_events(
            family,
            encounter,
            actor,
            targets,
            action_name,
            action_payload,
        )
        events.extend(family_events)

        if encounter_session is not None:
            await service.log_action_attempt(
                encounter_session,
                request_id=request_id,
                actor_id=actor_id,
                action_type=resolved_action_type,
                action_state="resolved",
                payload=raw_payload,
                checks=auth.checks or {},
                denial_reason=None,
            )
            await service.save_full_state(encounter_session, encounter)

        return events

    def _resolve_action_family(
        self,
        action_name: str,
        action_payload: dict[str, Any],
        targets: list[ActorInstance],
    ) -> str | None:
        family_value = str(action_payload.get("family", "")).strip().lower()
        if family_value in {ACTION_FAMILY_ATTACK, ACTION_FAMILY_SAVE, ACTION_FAMILY_HEALING, ACTION_FAMILY_UTILITY}:
            return family_value

        resolution_hint = str(action_payload.get(
            "resolution", "")).strip().lower()
        if resolution_hint in {ACTION_FAMILY_ATTACK, ACTION_FAMILY_SAVE, ACTION_FAMILY_HEALING, ACTION_FAMILY_UTILITY}:
            return resolution_hint

        if "save" in action_payload or "save_dc" in action_payload or "save_ability" in action_payload:
            return ACTION_FAMILY_SAVE

        if any(key in action_payload for key in {"condition", "remove_condition", "condition_op"}):
            return ACTION_FAMILY_UTILITY

        lowered_name = action_name.strip().lower()
        if any(token in lowered_name for token in {"heal", "cure", "mend"}):
            return ACTION_FAMILY_HEALING
        if any(token in lowered_name for token in {"save", "breath", "blast", "fireball"}):
            return ACTION_FAMILY_SAVE
        if any(token in lowered_name for token in {"condition", "stun", "poison", "prone", "grapple"}):
            return ACTION_FAMILY_UTILITY
        if targets:
            return ACTION_FAMILY_ATTACK

        return ACTION_FAMILY_UTILITY

    def _resolve_action_family_events(
        self,
        family: str,
        encounter: EncounterState,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
    ) -> list[WsOutbound]:
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
    ) -> list[WsOutbound]:
        if not targets:
            return [self._error_raw("Attack action requires at least one target", WsErrorCode.INVALID_MESSAGE)]

        target = targets[0]
        action_def = self._build_action_definition(
            ACTION_FAMILY_ATTACK, actor, action_name, action_payload)

        roll_override = self._safe_int(action_payload.get("roll_override"))
        roll_overrides = self._safe_int_list(
            action_payload.get("roll_overrides"))
        advantage = bool(action_payload.get("advantage", False))
        disadvantage = bool(action_payload.get("disadvantage", False))

        attack_result = resolve_attack(
            actor,
            target,
            action_def,
            roll_override=roll_override,
            roll_overrides=roll_overrides,
            advantage=advantage,
            disadvantage=disadvantage,
        )

        events: list[WsOutbound] = [
            WsOutbound(
                type="attack_result",
                payload={
                    "attacker_id": actor.id,
                    "target_id": target.id,
                    "action_name": action_name,
                    "hit": attack_result.hit,
                    "is_critical": attack_result.is_critical,
                    "roll_used": attack_result.roll_used,
                    "roll_count": attack_result.roll_count,
                    "damage": attack_result.total_damage,
                    "damage_type": (action_def.damage_type.value if action_def.damage_type else DamageType.BLUDGEONING.value),
                },
                visibility=Visibility.ALL,
            )
        ]

        if attack_result.hit and attack_result.total_damage > 0:
            events.append(
                WsOutbound(
                    type="actor_damaged",
                    payload={
                        "actor_id": target.id,
                        "amount": attack_result.total_damage,
                        "new_hp": target.current_hp,
                        "source": action_name,
                    },
                    visibility=Visibility.ALL,
                )
            )
            if target.current_hp <= 0:
                events.append(
                    WsOutbound(
                        type="actor_died",
                        payload={"actor_id": target.id},
                        visibility=Visibility.ALL,
                    )
                )

        return events

    def _resolve_save_events(
        self,
        encounter: EncounterState,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
    ) -> list[WsOutbound]:
        if not targets:
            return [self._error_raw("Save action requires at least one target", WsErrorCode.INVALID_MESSAGE)]

        action_def = self._build_action_definition(
            ACTION_FAMILY_SAVE, actor, action_name, action_payload)

        damage_roll_override = self._safe_int(
            action_payload.get("damage_roll_override"))
        save_overrides = self._safe_int_list(
            action_payload.get("save_overrides"))

        save_result = resolve_save_action(
            actor,
            targets,
            action_def,
            damage_roll_override=damage_roll_override,
            save_overrides=save_overrides,
        )

        save_payload_results = []
        events: list[WsOutbound] = []
        for target_result in save_result.results:
            save_payload_results.append(
                {
                    "target_id": target_result.target_id,
                    "passed": target_result.passed,
                    "save_roll": target_result.save_roll,
                    "damage": target_result.damage,
                }
            )

            if target_result.damage > 0:
                target = self._find_actor(encounter, target_result.target_id)
                if target is not None:
                    events.append(
                        WsOutbound(
                            type="actor_damaged",
                            payload={
                                "actor_id": target.id,
                                "amount": target_result.damage,
                                "new_hp": target.current_hp,
                                "source": action_name,
                            },
                            visibility=Visibility.ALL,
                        )
                    )
                    if target.current_hp <= 0:
                        events.append(
                            WsOutbound(
                                type="actor_died",
                                payload={"actor_id": target.id},
                                visibility=Visibility.ALL,
                            )
                        )

        save_req = action_def.save
        events.insert(
            0,
            WsOutbound(
                type="save_result",
                payload={
                    "caster_id": actor.id,
                    "action_name": action_name,
                    "save_ability": save_req.ability.value if save_req else Ability.DEX.value,
                    "save_dc": save_req.dc if save_req else 10,
                    "results": save_payload_results,
                },
                visibility=Visibility.ALL,
            ),
        )

        return events

    def _resolve_healing_events(
        self,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
    ) -> list[WsOutbound]:
        target = targets[0] if targets else actor
        action_def = self._build_action_definition(
            ACTION_FAMILY_HEALING, actor, action_name, action_payload)
        dice_override = self._safe_int(action_payload.get("dice_override"))

        healing_result = resolve_healing(
            target, action_def, dice_override=dice_override)

        return [
            WsOutbound(
                type="effect_applied",
                payload={
                    "actor_id": actor.id,
                    "target_id": target.id,
                    "action_name": action_name,
                    "effect_type": "healing",
                    "amount": healing_result.hp_restored,
                },
                visibility=Visibility.ALL,
            ),
            WsOutbound(
                type="actor_healed",
                payload={
                    "actor_id": target.id,
                    "amount": healing_result.hp_restored,
                    "new_hp": healing_result.new_hp,
                },
                visibility=Visibility.ALL,
            ),
        ]

    def _resolve_utility_events(
        self,
        encounter: EncounterState,
        actor: ActorInstance,
        targets: list[ActorInstance],
        action_name: str,
        action_payload: dict[str, Any],
    ) -> list[WsOutbound]:
        target = targets[0] if targets else actor
        condition = self._parse_condition(action_payload.get("condition"))
        condition_op = str(action_payload.get(
            "condition_op", "add")).strip().lower()
        should_remove = bool(action_payload.get(
            "remove_condition", False)) or condition_op in {"remove", "delete"}

        if condition is None:
            return [
                WsOutbound(
                    type="effect_applied",
                    payload={
                        "actor_id": actor.id,
                        "target_id": target.id,
                        "action_name": action_name,
                        "effect_type": "utility",
                    },
                    visibility=Visibility.ALL,
                )
            ]

        if should_remove:
            target.conditions = [
                entry for entry in target.conditions if entry.condition != condition]
            condition_event = WsOutbound(
                type="condition_removed",
                payload={
                    "actor_id": target.id,
                    "condition": condition.value,
                },
                visibility=Visibility.ALL,
            )
            effect_type = "condition_removed"
        else:
            target.conditions.append(
                ConditionInstance(
                    condition=condition,
                    source_id=actor.id,
                )
            )
            condition_event = WsOutbound(
                type="condition_added",
                payload={
                    "actor_id": target.id,
                    "condition": condition.value,
                    "source": actor.id,
                },
                visibility=Visibility.ALL,
            )
            effect_type = "condition_added"

        return [
            WsOutbound(
                type="effect_applied",
                payload={
                    "actor_id": actor.id,
                    "target_id": target.id,
                    "action_name": action_name,
                    "effect_type": effect_type,
                    "condition": condition.value,
                },
                visibility=Visibility.ALL,
            ),
            condition_event,
        ]

    def _build_action_definition(
        self,
        family: str,
        actor: ActorInstance,
        action_name: str,
        action_payload: dict[str, Any],
    ) -> ActionDefinition:
        attack_bonus = self._safe_int(action_payload.get(
            "attack_bonus"), default=actor.proficiency_bonus)
        damage_dice = str(action_payload.get("damage_dice") or "1d8")
        damage_bonus = self._safe_int(
            action_payload.get("damage_bonus"), default=0)
        damage_type = self._parse_damage_type(
            action_payload.get("damage_type"))

        if family == ACTION_FAMILY_SAVE:
            save_data = action_payload.get("save", {}) if isinstance(
                action_payload.get("save"), dict) else {}
            ability = self._parse_ability(save_data.get(
                "ability") or action_payload.get("save_ability"))
            save_dc = self._safe_int(save_data.get("dc") or action_payload.get(
                "save_dc"), default=10 + actor.proficiency_bonus)
            on_success = str(save_data.get("on_success") or action_payload.get(
                "save_on_success") or "half_damage")
            on_fail = str(save_data.get("on_fail") or action_payload.get(
                "save_on_fail") or "full_damage")
            return ActionDefinition(
                name=action_name,
                action_type=ActionType.SAVE_EFFECT,
                damage_dice=damage_dice,
                damage_bonus=damage_bonus,
                damage_type=damage_type,
                save=SaveRequirement(
                    ability=ability,
                    dc=save_dc,
                    on_success=on_success,
                    on_fail=on_fail,
                ),
            )

        if family == ACTION_FAMILY_HEALING:
            return ActionDefinition(
                name=action_name,
                action_type=ActionType.HEALING,
                damage_dice=str(action_payload.get(
                    "heal_dice") or damage_dice),
                damage_bonus=self._safe_int(action_payload.get(
                    "heal_bonus"), default=damage_bonus),
            )

        if family == ACTION_FAMILY_UTILITY:
            return ActionDefinition(
                name=action_name,
                action_type=ActionType.UTILITY,
            )

        attack_mode = str(action_payload.get("attack_mode") or action_payload.get(
            "attack_type") or "").strip().lower()
        action_type = ActionType.MELEE_WEAPON
        if attack_mode in {"ranged", "ranged_weapon"}:
            action_type = ActionType.RANGED_WEAPON
        elif attack_mode in {"melee_spell", "spell_melee"}:
            action_type = ActionType.MELEE_SPELL
        elif attack_mode in {"ranged_spell", "spell_ranged"}:
            action_type = ActionType.RANGED_SPELL

        return ActionDefinition(
            name=action_name,
            action_type=action_type,
            attack_bonus=attack_bonus,
            damage_dice=damage_dice,
            damage_bonus=damage_bonus,
            damage_type=damage_type,
        )

    @staticmethod
    def _safe_int(value: Any, default: int | None = None) -> int | None:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_int_list(value: Any) -> list[int] | None:
        if not isinstance(value, list):
            return None

        parsed: list[int] = []
        for entry in value:
            try:
                parsed.append(int(entry))
            except (TypeError, ValueError):
                return None
        return parsed

    @staticmethod
    def _parse_damage_type(raw_value: Any) -> DamageType:
        if isinstance(raw_value, DamageType):
            return raw_value

        normalized = str(raw_value or "").strip().lower()
        for candidate in DamageType:
            if candidate.value == normalized:
                return candidate
        return DamageType.BLUDGEONING

    @staticmethod
    def _parse_ability(raw_value: Any) -> Ability:
        normalized = str(raw_value or "").strip().lower()
        mapping = {
            "str": Ability.STR,
            "strength": Ability.STR,
            "dex": Ability.DEX,
            "dexterity": Ability.DEX,
            "con": Ability.CON,
            "constitution": Ability.CON,
            "int": Ability.INT,
            "intelligence": Ability.INT,
            "wis": Ability.WIS,
            "wisdom": Ability.WIS,
            "cha": Ability.CHA,
            "charisma": Ability.CHA,
        }
        return mapping.get(normalized, Ability.DEX)

    @staticmethod
    def _parse_condition(raw_value: Any) -> ConditionType | None:
        if isinstance(raw_value, ConditionType):
            return raw_value

        normalized = str(raw_value or "").strip().lower()
        if not normalized:
            return None

        for condition in ConditionType:
            if condition.value.lower() == normalized:
                return condition

        return None

    async def _handle_end_turn(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        try:
            payload = EndTurnPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error("Invalid end_turn payload", WsErrorCode.INVALID_MESSAGE, ctx, envelope.request_id)]

        if encounter.turn_phase != "active":
            return [
                self._denied(
                    "end_turn",
                    "Cannot end turn when combat is not active",
                    TURN_DENIED_REASON_INVALID_PHASE,
                    ctx,
                    envelope.request_id,
                )
            ]

        active_actor = get_active_combatant(encounter)
        if active_actor is None:
            return [
                self._denied(
                    "end_turn",
                    "No active combatant available",
                    TURN_DENIED_REASON_NO_ACTIVE_ACTOR,
                    ctx,
                    envelope.request_id,
                    actor_id=payload.actor_id,
                )
            ]

        if payload.actor_id != active_actor.id:
            return [
                self._denied(
                    "end_turn",
                    "Only the active combatant can end the turn",
                    TURN_DENIED_REASON_NOT_ACTIVE_ACTOR,
                    ctx,
                    envelope.request_id,
                    actor_id=payload.actor_id,
                )
            ]

        if encounter_session is None:
            next_turn(encounter)
            await service.on_turn_started(encounter_session, encounter)
            active = get_active_combatant(encounter)
            active_id = active.id if active else ""
        else:
            active_id, _ = await service.advance_turn(encounter_session, encounter)

        budget_snapshot = await service.get_turn_budget_snapshot(encounter_session, encounter)

        return [
            WsOutbound(
                type="turn_advanced",
                payload={
                    "active_actor_id": active_id,
                    "round": encounter.round_number,
                    "turn_budget": budget_snapshot,
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

        effective_ctx = self._resolve_impersonated_ctx(
            ctx, payload.acting_as_user_id)

        if not payload.path:
            return [self._error_raw("move_token path cannot be empty", WsErrorCode.INVALID_MESSAGE)]

        actor = self._find_actor(encounter, payload.actor_id)
        if actor is None:
            return [self._error_raw(f"Actor {payload.actor_id} not found", WsErrorCode.INVALID_TARGET)]

        auth = await service.apply_movement(
            encounter_session,
            encounter,
            effective_ctx,
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

        budget_snapshot = await service.get_turn_budget_snapshot(encounter_session, encounter)

        return [
            WsOutbound(
                type="actor_moved",
                payload={
                    "actor_id": payload.actor_id,
                    "path": validated_path,
                    "position": final_step,
                    "turn_budget": budget_snapshot,
                },
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_request_move_preview(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        try:
            payload = RequestMovePreviewPayload.model_validate(
                envelope.payload)
        except Exception:
            return [self._error_raw("Invalid request_move_preview payload", WsErrorCode.INVALID_MESSAGE)]

        effective_ctx = self._resolve_impersonated_ctx(
            ctx, payload.acting_as_user_id)
        preview = await service.get_movement_preview(
            encounter_session,
            encounter,
            effective_ctx,
            payload.actor_id,
        )

        if not preview.allowed:
            return [
                self._denied(
                    "request_move_preview",
                    preview.message or "Movement preview denied",
                    preview.reason_code or "invalid_action",
                    ctx,
                    envelope.request_id,
                    actor_id=payload.actor_id,
                    action_type="move",
                )
            ]

        return [
            WsOutbound(
                type="movement_preview",
                payload={
                    "actor_id": preview.actor_id,
                    "origin": preview.origin,
                    "movement_remaining": preview.movement_remaining,
                    "reachable": preview.reachable or [],
                },
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_request_executable_actions(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        try:
            payload = RequestExecutableActionsPayload.model_validate(
                envelope.payload)
        except Exception:
            return [self._error_raw("Invalid request_executable_actions payload", WsErrorCode.INVALID_MESSAGE)]

        effective_ctx = self._resolve_impersonated_ctx(
            ctx, payload.acting_as_user_id)
        snapshot = await service.get_executable_actions_snapshot(
            encounter_session,
            encounter,
            effective_ctx,
            payload.actor_id,
        )

        if not snapshot.allowed:
            return [
                self._denied(
                    "request_executable_actions",
                    snapshot.message or "Executable actions request denied",
                    snapshot.reason_code or "invalid_action",
                    ctx,
                    envelope.request_id,
                    actor_id=payload.actor_id,
                    action_type="action",
                )
            ]

        return [
            WsOutbound(
                type="executable_actions_snapshot",
                payload={
                    "actor_id": snapshot.actor_id,
                    "actions": snapshot.actions or [],
                    "turn_budget": snapshot.turn_budget,
                },
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_request_attack_preview(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        try:
            payload = RequestAttackPreviewPayload.model_validate(
                envelope.payload)
        except Exception:
            return [self._error_raw("Invalid request_attack_preview payload", WsErrorCode.INVALID_MESSAGE)]

        effective_ctx = self._resolve_impersonated_ctx(
            ctx, payload.acting_as_user_id)
        preview = await service.get_attack_preview(
            encounter_session,
            encounter,
            effective_ctx,
            payload.actor_id,
            payload.action_id,
            template_origin=payload.template_origin,
            template_direction=payload.template_direction,
        )

        if not preview.allowed:
            return [
                self._denied(
                    "request_attack_preview",
                    preview.message or "Attack preview denied",
                    preview.reason_code or "invalid_action",
                    ctx,
                    envelope.request_id,
                    actor_id=payload.actor_id,
                    action_type="action",
                )
            ]

        return [
            WsOutbound(
                type="attack_preview",
                payload={
                    "actor_id": preview.actor_id,
                    "action_id": preview.action_id,
                    "origin": preview.origin,
                    "eligible_target_ids": preview.eligible_target_ids or [],
                    "eligible_cells": preview.eligible_cells or [],
                    "template_projection": preview.template_projection,
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

        budget_snapshot = await service.get_turn_budget_snapshot(encounter_session, encounter)

        return [
            WsOutbound(
                type="combat_started",
                payload={
                    "initiative_order": order,
                    "turn_budget": budget_snapshot,
                },
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
