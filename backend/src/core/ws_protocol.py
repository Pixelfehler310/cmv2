"""
Core WebSocket Protocol Models.

System-agnostic envelope and visibility types for all WS communication.
Per architecture doc 09_session_and_websocket_architecture.md.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------

class Visibility(str, Enum):
    """Controls which connected clients receive an outbound event."""
    ALL = "all"
    DM_ONLY = "dm_only"
    ACTOR_OWNER = "actor_owner"
    EXCLUDE_ACTOR = "exclude_actor"


# ---------------------------------------------------------------------------
# Error Codes
# ---------------------------------------------------------------------------

class WsErrorCode(str, Enum):
    """Structured error codes sent to clients on failure."""
    INVALID_MESSAGE = "invalid_message"
    UNAUTHORIZED = "unauthorized"
    INVALID_TARGET = "invalid_target"
    NOT_YOUR_TURN = "not_your_turn"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    INVALID_ACTION = "invalid_action"
    INTERNAL_ERROR = "internal_error"


# ---------------------------------------------------------------------------
# Envelopes
# ---------------------------------------------------------------------------

class WsEnvelope(BaseModel):
    """Inbound message from a client."""
    type: str
    request_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class WsOutbound(BaseModel):
    """Outbound message to client(s)."""
    type: str
    request_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    visibility: Visibility = Visibility.ALL

    # Optional: when visibility is ACTOR_OWNER, specify whose owner sees it
    target_user_id: Optional[str] = None
