"""
D&D 5e Permission Checks.

Role-based validation for inbound WebSocket events.
Per architecture doc 09 § 4 (Who Can Send column).
"""

from __future__ import annotations

from src.core.sessions.models import UserRole, SessionContext
from src.core.ws_protocol import WsErrorCode


# ---------------------------------------------------------------------------
# Permission map
# ---------------------------------------------------------------------------

# Events only the DM can send
_DM_ONLY_EVENTS: set[str] = {
    "action",
    "delegate_start",
    "delegate_stop",
    "delegate_status",
    "start_combat",
    "end_combat",
    "end_turn",
    "add_actor",
    "remove_actor",
    "apply_damage",
    "apply_healing",
    "apply_condition",
    "remove_condition",
}

# Events DM or the actor owner can send
_DM_OR_OWNER_EVENTS: set[str] = {
    "move_token",
    "request_action",
    "request_move_preview",
    "request_executable_actions",
    "request_attack_preview",
}

# Events anyone can send
_ALL_USER_EVENTS: set[str] = {
    "roll_dice",
    "chat_message",
    "ping",
    "request_sync",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class PermissionDenied(Exception):
    """Raised when a user attempts an action they're not allowed to perform."""

    def __init__(self, message: str, code: WsErrorCode = WsErrorCode.UNAUTHORIZED):
        super().__init__(message)
        self.code = code


def check_permission(event_type: str, ctx: SessionContext) -> None:
    """Validate whether the user's role allows sending this event type.

    Raises PermissionDenied if the user is not allowed.
    """
    # DM can always send anything
    if ctx.role == UserRole.DM:
        return

    # All-user events: anyone can send
    if event_type in _ALL_USER_EVENTS:
        return

    # DM-or-owner events: players can send
    if event_type in _DM_OR_OWNER_EVENTS and ctx.role == UserRole.PLAYER:
        return

    # DM-only events: only DM
    if event_type in _DM_ONLY_EVENTS:
        raise PermissionDenied(
            f"Event '{event_type}' requires DM role",
            WsErrorCode.UNAUTHORIZED,
        )

    # Unknown event type — allow for forward compatibility but log
    # (the handler will reject if it can't process it)
    return
