"""
Session Management Models.

System-agnostic models for tracking connected users, rooms, and session context.
Per architecture doc 09_session_and_websocket_architecture.md § 3.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import WebSocket
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# User Role
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    """Role of a connected user within a campaign."""
    DM = "dm"
    PLAYER = "player"
    SPECTATOR = "spectator"


# ---------------------------------------------------------------------------
# Connected User
# ---------------------------------------------------------------------------

class ConnectedUser(BaseModel):
    """Represents a single user connected via WebSocket."""

    model_config = {"arbitrary_types_allowed": True}

    user_id: str
    display_name: str
    role: UserRole
    ws: object  # WebSocket or mock — skip strict type validation
    connected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Campaign Room
# ---------------------------------------------------------------------------

class CampaignRoom(BaseModel):
    """In-memory room tracking all connections to a campaign."""

    model_config = {"arbitrary_types_allowed": True}

    campaign_id: str
    game_system: str = "dnd5e"
    users: dict[str, ConnectedUser] = Field(default_factory=dict)

    def is_empty(self) -> bool:
        return len(self.users) == 0


# ---------------------------------------------------------------------------
# Session Context
# ---------------------------------------------------------------------------

class SessionContext(BaseModel):
    """Lightweight context passed to handlers on every event."""
    campaign_id: str
    user_id: str
    display_name: str = ""
    role: UserRole = UserRole.PLAYER
    game_system: str = "dnd5e"
