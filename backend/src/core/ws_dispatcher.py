"""
WebSocket Dispatcher.

The single WebSocket endpoint for the application. Handles:
1. JWT authentication from query param
2. Connection registration in SessionManager
3. Message loop with dispatch to system-specific handlers
4. Graceful disconnect cleanup

Per architecture doc 09 § 7.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt

from src.config import settings
from .ws_protocol import WsEnvelope, WsOutbound, WsErrorCode, Visibility
from .sessions.models import ConnectedUser, SessionContext, UserRole
from .sessions.manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton session manager — shared across the application
session_manager = SessionManager()


# ---------------------------------------------------------------------------
# System handler interface
# ---------------------------------------------------------------------------

class ISystemHandler:
    """Interface that each game system's WS handler must implement."""

    async def on_connect(
        self, ctx: SessionContext, mgr: SessionManager
    ) -> list[WsOutbound]:
        """Called when a user connects. Return initial events (e.g., state_sync)."""
        return []

    async def on_disconnect(self, ctx: SessionContext, mgr: SessionManager) -> None:
        """Called when a user disconnects."""
        pass

    async def handle(
        self, envelope: WsEnvelope, ctx: SessionContext, mgr: SessionManager
    ) -> list[WsOutbound]:
        """Process an inbound event. Return outbound events to broadcast."""
        return []


# ---------------------------------------------------------------------------
# System registry (MVP: inline dnd5e)
# ---------------------------------------------------------------------------

_system_handlers: dict[str, ISystemHandler] = {}


def register_system_handler(system_name: str, handler: ISystemHandler) -> None:
    """Register a game system handler for WebSocket dispatch."""
    _system_handlers[system_name] = handler


def _get_handler(system_name: str) -> Optional[ISystemHandler]:
    return _system_handlers.get(system_name)


# ---------------------------------------------------------------------------
# JWT helper
# ---------------------------------------------------------------------------

def _validate_token(token: str) -> Optional[dict]:
    """Validate a JWT token and return the payload, or None on failure."""
    if token == "dev-token":
        # Handle the frontend sandbox fake login
        return {"sub": "simon", "display_name": "Simon (Dev)"}

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/{campaign_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    campaign_id: str,
    token: str = Query(default=""),
    role: str = Query(default="player"),
):
    """Main WebSocket endpoint.

    Connection flow:
    1. Extract JWT from query params
    2. Validate token
    3. Register in SessionManager
    4. Send initial state_sync via system handler
    5. Enter message loop
    """
    # --- Auth ---
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = _validate_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    user_id = payload.get("sub", "unknown")
    display_name = payload.get("display_name", user_id)

    # Map role string to enum
    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.PLAYER

    # --- Accept & Register ---
    await websocket.accept()

    connected_user = ConnectedUser(
        user_id=user_id,
        display_name=display_name,
        role=user_role,
        ws=websocket,
    )

    ctx = session_manager.register_connection(campaign_id, connected_user)
    logger.info(
        "Registered WS connection campaign=%s user=%s role=%s game_system=%s",
        campaign_id,
        user_id,
        user_role.value,
        ctx.game_system,
    )

    # --- System handler ---
    handler = _get_handler(ctx.game_system)
    if handler is None:
        await websocket.send_json({
            "type": "error",
            "payload": {"message": f"Unknown game system: {ctx.game_system}", "code": WsErrorCode.INTERNAL_ERROR},
        })
        await websocket.close(code=4002, reason="Unknown game system")
        session_manager.unregister_connection(campaign_id, user_id)
        return

    # --- Initial state sync ---
    try:
        connect_events = await handler.on_connect(ctx, session_manager)
        for event in connect_events:
            logger.debug(
                "Sending on_connect event type=%s campaign=%s user=%s",
                event.type,
                campaign_id,
                user_id,
            )
            await session_manager.send_to_user(campaign_id, user_id, event)
            logger.debug(
                "Sent on_connect event type=%s campaign=%s user=%s",
                event.type,
                campaign_id,
                user_id,
            )
    except Exception:
        logger.exception(
            "Error in on_connect campaign=%s user=%s",
            campaign_id,
            user_id,
        )

    # --- Message loop ---
    try:
        while True:
            raw = await websocket.receive_text()

            # Parse envelope
            try:
                envelope = WsEnvelope.model_validate_json(raw)
            except Exception:
                error_event = WsOutbound(
                    type="error",
                    payload={"message": "Invalid message format", "code": WsErrorCode.INVALID_MESSAGE},
                    visibility=Visibility.ALL,
                )
                await session_manager.send_to_user(campaign_id, user_id, error_event)
                continue

            # Dispatch to handler
            try:
                results = await handler.handle(envelope, ctx, session_manager)
            except Exception:
                logger.exception("Error handling event %s", envelope.type)
                error_event = WsOutbound(
                    type="error",
                    request_id=envelope.request_id,
                    payload={"message": "Internal server error", "code": WsErrorCode.INTERNAL_ERROR},
                    visibility=Visibility.ALL,
                )
                await session_manager.send_to_user(campaign_id, user_id, error_event)
                continue

            # Broadcast results
            for event in results:
                if event.request_id is None:
                    event.request_id = envelope.request_id
                await session_manager.broadcast(campaign_id, event)

    except WebSocketDisconnect:
        logger.info("User %s disconnected from %s", user_id, campaign_id)
    except Exception:
        logger.exception("Unexpected error in WS loop for user %s", user_id)
    finally:
        # --- Cleanup ---
        try:
            await handler.on_disconnect(ctx, session_manager)
        except Exception:
            logger.exception("Error in on_disconnect")
        session_manager.unregister_connection(campaign_id, user_id)
