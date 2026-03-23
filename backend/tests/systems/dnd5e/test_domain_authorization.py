from __future__ import annotations

from dataclasses import dataclass

from src.core.sessions.models import UserRole
from src.systems.dnd5e.domain.authorization import (
    check_actor_exists,
    check_user_role_allowed,
    check_actor_ownership,
    check_actor_alive,
    check_turn_ownership,
    combine_authorization_checks,
)


@dataclass
class DummyActor:
    current_hp: int


def test_check_actor_exists_denies_missing_actor() -> None:
    result = check_actor_exists("a1", None)
    assert result.allowed is False
    assert result.reason_code == "invalid_target"


def test_check_user_role_allowed_denies_spectator() -> None:
    result = check_user_role_allowed(UserRole.SPECTATOR)
    assert result.allowed is False
    assert result.reason_code == "unauthorized"


def test_check_actor_ownership_denies_non_owner_player() -> None:
    result = check_actor_ownership(UserRole.PLAYER, "user-1", "user-2")
    assert result.allowed is False
    assert result.reason_code == "unauthorized"
    assert result.checks is not None
    assert result.checks["ownership_ok"] is False


def test_check_actor_alive_denies_dead_actor() -> None:
    result = check_actor_alive(DummyActor(current_hp=0))
    assert result.allowed is False
    assert result.reason_code == "invalid_action"


def test_check_turn_ownership_denies_not_active_turn_for_non_reaction() -> None:
    result = check_turn_ownership(
        action_type="action",
        turn_phase="active",
        active_actor_id="a1",
        requesting_actor_id="a2",
    )
    assert result.allowed is False
    assert result.reason_code == "not_your_turn"


def test_check_turn_ownership_allows_reaction_outside_active_actor() -> None:
    result = check_turn_ownership(
        action_type="reaction",
        turn_phase="active",
        active_actor_id="a1",
        requesting_actor_id="a2",
    )
    assert result.allowed is True


def test_combine_authorization_checks_short_circuits_denial() -> None:
    role_result = check_user_role_allowed(UserRole.PLAYER)
    deny_result = check_actor_ownership(UserRole.PLAYER, "user-1", "user-2")
    alive_result = check_actor_alive(DummyActor(current_hp=10))

    combined = combine_authorization_checks(role_result, deny_result, alive_result)
    assert combined.allowed is False
    assert combined.reason_code == "unauthorized"
