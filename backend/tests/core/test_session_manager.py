"""
Tests for core SessionManager.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.core.sessions.manager import SessionManager
from src.core.sessions.models import ConnectedUser, UserRole
from src.core.ws_protocol import WsOutbound, Visibility


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id: str, role: UserRole = UserRole.PLAYER, display_name: str = "") -> ConnectedUser:
    """Create a ConnectedUser with a mock WebSocket."""
    ws = AsyncMock()
    return ConnectedUser(
        user_id=user_id,
        display_name=display_name or user_id,
        role=role,
        ws=ws,
    )


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------

class TestRegistration:

    def test_register_and_unregister(self):
        sm = SessionManager()
        user = _make_user("user_1")

        ctx = sm.register_connection("campaign_1", user)
        assert ctx.campaign_id == "campaign_1"
        assert ctx.user_id == "user_1"
        assert len(sm.get_connected_users("campaign_1")) == 1

        sm.unregister_connection("campaign_1", "user_1")
        assert len(sm.get_connected_users("campaign_1")) == 0

    def test_room_created_on_first_connection(self):
        sm = SessionManager()
        user = _make_user("user_1")
        sm.register_connection("campaign_1", user)
        room = sm.get_room("campaign_1")
        assert room is not None
        assert room.campaign_id == "campaign_1"

    def test_room_removed_when_empty(self):
        sm = SessionManager()
        user = _make_user("user_1")
        sm.register_connection("campaign_1", user)
        sm.unregister_connection("campaign_1", "user_1")
        assert sm.get_room("campaign_1") is None

    def test_multiple_users_in_room(self):
        sm = SessionManager()
        user_a = _make_user("user_a")
        user_b = _make_user("user_b")

        sm.register_connection("c1", user_a)
        sm.register_connection("c1", user_b)
        assert len(sm.get_connected_users("c1")) == 2

        sm.unregister_connection("c1", "user_a")
        assert len(sm.get_connected_users("c1")) == 1

    def test_unregister_nonexistent_room(self):
        """Should not raise when unregistering from a room that doesn't exist."""
        sm = SessionManager()
        sm.unregister_connection("nonexistent", "user_1")  # no error

    def test_get_connected_users_empty_room(self):
        sm = SessionManager()
        assert sm.get_connected_users("nonexistent") == []


# ---------------------------------------------------------------------------
# Broadcast Tests
# ---------------------------------------------------------------------------

class TestBroadcast:

    @pytest.mark.anyio
    async def test_broadcast_sends_to_all_in_room(self):
        sm = SessionManager()
        user_a = _make_user("user_a")
        user_b = _make_user("user_b")
        sm.register_connection("c1", user_a)
        sm.register_connection("c1", user_b)

        event = WsOutbound(type="test", payload={"data": 1}, visibility=Visibility.ALL)
        await sm.broadcast("c1", event)

        user_a.ws.send_json.assert_called_once()
        user_b.ws.send_json.assert_called_once()

    @pytest.mark.anyio
    async def test_dm_only_visibility(self):
        sm = SessionManager()
        dm_user = _make_user("dm", UserRole.DM)
        player_user = _make_user("player", UserRole.PLAYER)
        sm.register_connection("c1", dm_user)
        sm.register_connection("c1", player_user)

        event = WsOutbound(type="secret", payload={}, visibility=Visibility.DM_ONLY)
        await sm.broadcast("c1", event)

        dm_user.ws.send_json.assert_called_once()
        player_user.ws.send_json.assert_not_called()

    @pytest.mark.anyio
    async def test_actor_owner_visibility(self):
        sm = SessionManager()
        dm_user = _make_user("dm", UserRole.DM)
        player_a = _make_user("player_a", UserRole.PLAYER)
        player_b = _make_user("player_b", UserRole.PLAYER)
        sm.register_connection("c1", dm_user)
        sm.register_connection("c1", player_a)
        sm.register_connection("c1", player_b)

        event = WsOutbound(
            type="personal",
            payload={},
            visibility=Visibility.ACTOR_OWNER,
            target_user_id="player_a",
        )
        await sm.broadcast("c1", event)

        # DM always sees; target user sees; other player doesn't
        dm_user.ws.send_json.assert_called_once()
        player_a.ws.send_json.assert_called_once()
        player_b.ws.send_json.assert_not_called()

    @pytest.mark.anyio
    async def test_exclude_actor_visibility(self):
        sm = SessionManager()
        player_a = _make_user("player_a", UserRole.PLAYER)
        player_b = _make_user("player_b", UserRole.PLAYER)
        sm.register_connection("c1", player_a)
        sm.register_connection("c1", player_b)

        event = WsOutbound(
            type="hidden_roll",
            payload={},
            visibility=Visibility.EXCLUDE_ACTOR,
            target_user_id="player_a",
        )
        await sm.broadcast("c1", event)

        player_a.ws.send_json.assert_not_called()
        player_b.ws.send_json.assert_called_once()


# ---------------------------------------------------------------------------
# Send-to-user Tests
# ---------------------------------------------------------------------------

class TestSendToUser:

    @pytest.mark.anyio
    async def test_send_to_specific_user(self):
        sm = SessionManager()
        user_a = _make_user("user_a")
        user_b = _make_user("user_b")
        sm.register_connection("c1", user_a)
        sm.register_connection("c1", user_b)

        event = WsOutbound(type="personal", payload={"msg": "hi"})
        await sm.send_to_user("c1", "user_a", event)

        user_a.ws.send_json.assert_called_once()
        user_b.ws.send_json.assert_not_called()

    @pytest.mark.anyio
    async def test_send_to_nonexistent_user(self):
        sm = SessionManager()
        user_a = _make_user("user_a")
        sm.register_connection("c1", user_a)

        event = WsOutbound(type="test", payload={})
        await sm.send_to_user("c1", "nonexistent", event)
        # Should not raise, just silently skip
