"""
D&D 5e WebSocket Handler.

Routes inbound WebSocket events to the Phase 2–4 engine and returns
outbound events for broadcasting.

Per architecture doc 09 § 7.

This handler follows the Single Responsibility Principle: it exclusively
handles WebSocket protocol concerns (deserializing → delegating → serializing).
All domain logic lives in CombatService and services/validation.py.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

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
from .application.action_execution_service import (
    ActionExecutionApplicationService,
    ActionExecutionRequest,
)
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

MUTATING_COMMAND_TYPES = {
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


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

class Dnd5eWsHandler(ISystemHandler):
    """D&D 5e WebSocket event handler.

    Thin transport layer that:
    1. Deserializes WsEnvelope payloads into Pydantic models
    2. Checks role-based permissions
    3. Delegates to CombatService
    4. Wraps service results into WsOutbound envelopes
    """

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
        _results: list[WsOutbound] | None = None
        print(f"DEBUG: handler.handle using AsyncSessionLocal ID={id(AsyncSessionLocal)}")
        async with AsyncSessionLocal() as db:
            service = CombatService(db)
            action_execution_service = ActionExecutionApplicationService(service)
            encounter_session, encounter = await service.load_or_create_encounter_state(ctx.campaign_id)

            if event_type == "ping":
                _results = self._handle_ping(ctx)

            elif event_type == "request_sync":
                _results = self._handle_request_sync(encounter, ctx)

            elif event_type == "roll_dice":
                _results = self._handle_roll_dice(service, envelope, ctx)

            elif event_type == "chat_message":
                _results = self._handle_chat_message(envelope, ctx)

            elif event_type == "action":
                _results = await self._handle_action(
                    encounter,
                    encounter_session,
                    action_execution_service,
                    service,
                    envelope,
                    ctx,
                )

            elif event_type == "request_action":
                _results = await self._handle_request_action(
                    encounter,
                    encounter_session,
                    action_execution_service,
                    service,
                    envelope,
                    ctx,
                )

            elif event_type == "request_executable_actions":
                _results = await self._handle_request_executable_actions(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "request_attack_preview":
                _results = await self._handle_request_attack_preview(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "request_move_preview":
                _results = await self._handle_request_move_preview(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "move_token":
                _results = await self._handle_move_token(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "add_actor":
                _results = await self._handle_add_actor(encounter, encounter_session, service, envelope)

            elif event_type == "remove_actor":
                _results = await self._handle_remove_actor(encounter, encounter_session, service, envelope)

            elif event_type == "end_turn":
                _results = await self._handle_end_turn(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "start_combat":
                _results = await self._handle_start_combat(encounter, encounter_session, service, envelope)

            elif event_type == "end_combat":
                _results = self._handle_end_combat(encounter, encounter_session, service)

            elif event_type == "apply_damage":
                _results = await self._handle_apply_damage(encounter, encounter_session, service, envelope)

            elif event_type == "apply_healing":
                _results = await self._handle_apply_healing(encounter, encounter_session, service, envelope)

            elif event_type == "apply_condition":
                _results = await self._handle_apply_condition(encounter, encounter_session, service, envelope, ctx)

            elif event_type == "remove_condition":
                _results = await self._handle_remove_condition(encounter, encounter_session, service, envelope)

            if _results is not None:
                await self._save_if_persistent(encounter_session, service, encounter, _results, event_type)

        if _results is not None:
            return self._attach_request_id(_results, envelope.request_id)

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
    # Event Handlers — thin delegation to CombatService
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
        self, service: CombatService, envelope: WsEnvelope, ctx: SessionContext
    ) -> list[WsOutbound]:
        try:
            payload = RollDicePayload.model_validate(envelope.payload)
        except Exception:
            return [self._error("Invalid roll_dice payload", WsErrorCode.INVALID_MESSAGE, ctx)]

        result = service.handle_roll_dice(payload.expression, payload.purpose, ctx.user_id)
        return [
            WsOutbound(
                type="dice_rolled",
                payload=result,
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
        action_execution_service: ActionExecutionApplicationService,
        service: CombatService,
        envelope: WsEnvelope,
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        try:
            payload = ActionPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error("Invalid action payload", WsErrorCode.INVALID_MESSAGE, ctx)]

        request = ActionExecutionRequest(
            actor_id=payload.actor_id,
            action_type=payload.action_type,
            action_name=payload.action_name,
            target_ids=payload.target_ids,
            action_payload={},
            request_id=envelope.request_id,
            raw_payload=payload.model_dump(mode="json"),
            require_canonical_action_id=True,
        )
        execution = await action_execution_service.execute(
            request=request,
            encounter=encounter,
            encounter_session=encounter_session,
            ctx=ctx,
        )
        domain_events = execution.events
        return self._domain_events_to_outbound(domain_events, ctx)

    async def _handle_request_action(
        self,
        encounter: EncounterState,
        encounter_session,
        action_execution_service: ActionExecutionApplicationService,
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

        request = ActionExecutionRequest(
            actor_id=payload.actor_id,
            action_type=payload.action_type,
            action_name=payload.action_name,
            target_ids=requested_target_ids,
            action_payload=payload.payload,
            request_id=envelope.request_id,
            raw_payload=payload.model_dump(mode="json"),
            require_canonical_action_id=True,
        )
        execution = await action_execution_service.execute(
            request=request,
            encounter=encounter,
            encounter_session=encounter_session,
            ctx=effective_ctx,
        )
        domain_events = execution.events
        return self._domain_events_to_outbound(domain_events, ctx)

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
            encounter_session, encounter, effective_ctx, payload.actor_id,
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
                    "turn_budget": snapshot.turn_budget["budgets"] if snapshot.turn_budget else {},
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
            encounter_session, encounter, effective_ctx,
            payload.actor_id, payload.action_id,
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
            encounter_session, encounter, effective_ctx, payload.actor_id,
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

        result = await service.handle_move_token(
            encounter, encounter_session, effective_ctx,
            payload.actor_id, payload.path, envelope.request_id,
            acting_as_user_id=payload.acting_as_user_id,
        )

        if not result.get("allowed"):
            reason = result.get("reason_code")
            if reason == "invalid_target":
                return [self._error_raw(result.get("error", "Target not found"), WsErrorCode.INVALID_TARGET)]
            if reason:
                return [
                    self._denied(
                        "move_token",
                        result.get("message", "Movement denied"),
                        reason,
                        ctx,
                        envelope.request_id,
                        actor_id=payload.actor_id,
                    )
                ]
            return [self._error_raw(result.get("error", "Movement failed"), WsErrorCode.INVALID_ACTION)]


        return [
            WsOutbound(
                type="actor_moved",
                payload={
                    "actor_id": result["actor_id"],
                    "path": result["path"],
                    "position": result["position"],
                    "turn_budget": result["turn_budget"],
                },
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_add_actor(
        self, encounter: EncounterState, encounter_session, service: CombatService, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = AddActorPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid add_actor payload", WsErrorCode.INVALID_MESSAGE)]

        result = service.handle_add_actor(
            encounter,
            definition_slug=payload.definition_slug,
            name=payload.name,
            owner_user_id=payload.owner_user_id,
            position_data=payload.position,
        )

        if "error" in result:
            return [self._error_raw(result["error"], WsErrorCode.INVALID_ACTION)]

        return [
            WsOutbound(
                type="actor_added",
                payload=result,
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_remove_actor(
        self, encounter: EncounterState, encounter_session, service: CombatService, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = RemoveActorPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid remove_actor payload", WsErrorCode.INVALID_MESSAGE)]

        result = service.handle_remove_actor(encounter, actor_id=payload.actor_id)

        if "error" in result:
            return [self._error_raw(result["error"], WsErrorCode.INVALID_TARGET)]


        return [
            WsOutbound(
                type="actor_removed",
                payload={"actor_id": result["actor_id"]},
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
        try:
            payload = EndTurnPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error("Invalid end_turn payload", WsErrorCode.INVALID_MESSAGE, ctx, envelope.request_id)]

        result = await service.handle_end_turn(
            encounter, encounter_session,
            actor_id=payload.actor_id,
            request_id=envelope.request_id,
        )

        if not result.get("allowed"):
            return [
                self._denied(
                    "end_turn",
                    result.get("message", "Cannot end turn"),
                    result.get("reason_code", "invalid_action"),
                    ctx,
                    envelope.request_id,
                    actor_id=payload.actor_id,
                )
            ]

        tick_events = [
            WsOutbound(
                type=event["type"],
                payload=event.get("payload", {}),
                visibility=Visibility.ALL,
            )
            for event in result.get("tick_events", [])
        ]


        turn_event = WsOutbound(
            type="turn_advanced",
            payload={
                "active_actor_id": result["active_actor_id"],
                "round": result["round"],
                "turn_budget": result["turn_budget"]["budgets"] if result.get("turn_budget") else {},
            },
            visibility=Visibility.ALL,
        )

        return [*tick_events, turn_event]

    async def _handle_start_combat(
        self,
        encounter: EncounterState,
        encounter_session,
        service: CombatService,
        envelope: WsEnvelope,
    ) -> list[WsOutbound]:
        result = await service.handle_start_combat(encounter, encounter_session)

        if "error" in result:
            return [self._error_raw(result["error"], WsErrorCode.INVALID_ACTION, envelope.request_id)]

        return [
            WsOutbound(
                type="combat_started",
                payload={
                    "initiative_order": result["initiative_order"],
                    "turn_budget": result["turn_budget"],
                },
                visibility=Visibility.ALL,
            )
        ]

    def _handle_end_combat(
        self, encounter: EncounterState, encounter_session, service: CombatService
    ) -> list[WsOutbound]:
        service.handle_end_combat(encounter)

        if encounter_session is not None:
            # Save triggered by async context in handle()
            pass

        return [
            WsOutbound(
                type="combat_ended",
                payload={},
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_apply_damage(
        self, encounter: EncounterState, encounter_session, service: CombatService, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = ApplyDamagePayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid apply_damage payload", WsErrorCode.INVALID_MESSAGE)]

        result = service.handle_apply_damage(
            encounter, payload.actor_id, payload.amount, payload.damage_type,
        )

        if "error" in result:
            return [self._error_raw(result["error"], WsErrorCode.INVALID_TARGET)]

        events: list[WsOutbound] = [
            WsOutbound(
                type="actor_damaged",
                payload={
                    "actor_id": result["actor_id"],
                    "amount": result["damage_dealt"],
                    "new_hp": result["new_hp"],
                    "source": "dm_override",
                },
                visibility=Visibility.ALL,
            )
        ]

        if result.get("is_dead"):
            events.append(
                WsOutbound(
                    type="actor_died",
                    payload={"actor_id": result["actor_id"]},
                    visibility=Visibility.ALL,
                )
            )

        return events

    async def _handle_apply_healing(
        self, encounter: EncounterState, encounter_session, service: CombatService, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = ApplyHealingPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid apply_healing payload", WsErrorCode.INVALID_MESSAGE)]

        result = service.handle_apply_healing(encounter, payload.actor_id, payload.amount)

        if "error" in result:
            return [self._error_raw(result["error"], WsErrorCode.INVALID_TARGET)]


        return [
            WsOutbound(
                type="actor_healed",
                payload={
                    "actor_id": result["actor_id"],
                    "amount": result["amount"],
                    "new_hp": result["new_hp"],
                },
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_apply_condition(
        self, encounter: EncounterState, encounter_session, service: CombatService, envelope: WsEnvelope, ctx: SessionContext
    ) -> list[WsOutbound]:
        try:
            payload = ApplyConditionPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid apply_condition payload", WsErrorCode.INVALID_MESSAGE)]

        # Determine source (actor owned by the current user)
        source_id = next((c.id for c in encounter.combatants if c.owner_user_id == ctx.user_id), None)


        result = service.handle_apply_condition(
            encounter, payload.actor_id, payload.condition, source_id=source_id
        )

        if "error" in result:
            return [self._error_raw(result["error"], WsErrorCode.INVALID_ACTION)]


        return [
            WsOutbound(
                type="condition_added",
                payload={
                    "actor_id": result["actor_id"],
                    "condition": result["condition"],
                    "source": result["source"],
                },
                visibility=Visibility.ALL,
            )
        ]

    async def _handle_remove_condition(
        self, encounter: EncounterState, encounter_session, service: CombatService, envelope: WsEnvelope
    ) -> list[WsOutbound]:
        try:
            payload = RemoveConditionPayload.model_validate(envelope.payload)
        except Exception:
            return [self._error_raw("Invalid remove_condition payload", WsErrorCode.INVALID_MESSAGE)]

        result = service.handle_remove_condition(encounter, payload.actor_id, payload.condition)

        if "error" in result:
            return [self._error_raw(result["error"], WsErrorCode.INVALID_ACTION)]


        return [
            WsOutbound(
                type="condition_removed",
                payload={
                    "actor_id": result["actor_id"],
                    "condition": result["condition"],
                },
                visibility=Visibility.ALL,
            )
        ]

    # ------------------------------------------------------------------
    # Domain event → WsOutbound conversion
    # ------------------------------------------------------------------

    def _domain_events_to_outbound(
        self,
        domain_events: list[dict[str, Any]],
        ctx: SessionContext,
    ) -> list[WsOutbound]:
        """Convert domain event dicts from CombatService into WsOutbound envelopes."""
        outbound: list[WsOutbound] = []

        for event in domain_events:
            event_type = event.get("type", "")

            if event_type == "denied":
                outbound.append(
                    self._denied(
                        "request_action",
                        event.get("message", "Action denied"),
                        event.get("reason_code", "invalid_action"),
                        ctx,
                        None,
                        actor_id=event.get("actor_id"),
                        action_type=event.get("action_type"),
                    )
                )
            elif event_type == "error":
                outbound.append(self._error_raw(
                    event.get("message", "Unknown error"),
                    WsErrorCode.INVALID_ACTION,
                ))
            elif event_type in {"action_authorized", "attack_result", "save_result",
                                "actor_damaged", "actor_died", "actor_healed",
                                "effect_applied", "effect_removed", "effect_refreshed",
                                "effect_denied", "effect_tick_resolved",
                                "condition_added", "condition_removed"}:
                outbound.append(
                    WsOutbound(
                        type=event_type,
                        payload=event.get("payload", {}),
                        visibility=Visibility.ALL,
                    )
                )
            else:
                outbound.append(
                    WsOutbound(
                        type=event_type,
                        payload=event.get("payload", event),
                        visibility=Visibility.ALL,
                    )
                )

        return outbound

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    async def _save_if_persistent(
        self,
        encounter_session,
        service: CombatService,
        encounter: EncounterState,
        events: list[WsOutbound],
        event_type: str,
    ) -> None:
        """Save encounter state if we have a persistent session, it's a mutating command, and no errors."""
        should_save = (
            encounter_session is not None 
            and event_type in MUTATING_COMMAND_TYPES 
            and not self._is_error_only(events)
        )
        if should_save:
            await service.save_full_state(encounter_session, encounter)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
        if service is not None:
            _, encounter = await service.load_or_create_encounter_state(campaign_id)
            return encounter

        async with AsyncSessionLocal() as db:
            local_service = CombatService(db)
            _, encounter = await local_service.load_or_create_encounter_state(campaign_id)
            return encounter

    @staticmethod
    def _is_error_only(events: list[WsOutbound]) -> bool:
        return bool(events) and all(event.type in {"error", "action_denied", "command_denied"} for event in events)
