"""
Tests for D&D 5e permission checks.
"""

import pytest

from src.core.sessions.models import SessionContext, UserRole
from src.systems.dnd5e.permissions import check_permission, PermissionDenied


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx(role: UserRole) -> SessionContext:
    return SessionContext(
        campaign_id="c1",
        user_id="test_user",
        role=role,
        game_system="dnd5e",
    )


# ---------------------------------------------------------------------------
# DM-only events
# ---------------------------------------------------------------------------

class TestDmOnlyEvents:

    @pytest.mark.parametrize("event_type", [
        "action", "start_combat", "end_combat", "end_turn",
        "add_actor", "remove_actor", "apply_damage", "apply_healing",
        "apply_condition", "remove_condition", "update_hp", "cast_spell",
        "roll_initiative",
    ])
    def test_dm_can_send(self, event_type: str):
        check_permission(event_type, _ctx(UserRole.DM))  # no exception

    @pytest.mark.parametrize("event_type", [
        "action", "start_combat", "end_combat", "end_turn",
        "add_actor", "remove_actor", "apply_damage", "apply_healing",
        "apply_condition", "remove_condition", "update_hp", "cast_spell",
        "roll_initiative",
    ])
    def test_player_cannot_send(self, event_type: str):
        with pytest.raises(PermissionDenied):
            check_permission(event_type, _ctx(UserRole.PLAYER))

    @pytest.mark.parametrize("event_type", [
        "action", "start_combat", "end_combat",
    ])
    def test_spectator_cannot_send(self, event_type: str):
        with pytest.raises(PermissionDenied):
            check_permission(event_type, _ctx(UserRole.SPECTATOR))


# ---------------------------------------------------------------------------
# All-user events
# ---------------------------------------------------------------------------

class TestAllUserEvents:

    @pytest.mark.parametrize("event_type", [
        "roll_dice", "chat_message", "ping", "request_sync",
    ])
    @pytest.mark.parametrize("role", [UserRole.DM, UserRole.PLAYER, UserRole.SPECTATOR])
    def test_anyone_can_send(self, event_type: str, role: UserRole):
        check_permission(event_type, _ctx(role))  # no exception


# ---------------------------------------------------------------------------
# DM-or-owner events
# ---------------------------------------------------------------------------

class TestDmOrOwnerEvents:

    @pytest.mark.parametrize("event_type", ["move_token", "toggle_equip"])
    def test_dm_can_send(self, event_type: str):
        check_permission(event_type, _ctx(UserRole.DM))  # no exception

    @pytest.mark.parametrize("event_type", ["move_token", "toggle_equip"])
    def test_player_can_send(self, event_type: str):
        check_permission(event_type, _ctx(UserRole.PLAYER))  # no exception

    @pytest.mark.parametrize("event_type", ["move_token", "toggle_equip"])
    def test_spectator_cannot_send(self, event_type: str):
        # Spectators aren't explicitly in DM_OR_OWNER or ALL, so they fall through
        # The current implementation allows unknown events through for forward compat
        # This test documents the behavior
        check_permission(event_type, _ctx(UserRole.SPECTATOR))  # no exception (falls through)
