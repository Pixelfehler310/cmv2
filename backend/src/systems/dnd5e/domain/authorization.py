from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.sessions.models import UserRole


@dataclass
class AuthorizationResult:
    allowed: bool
    reason_code: str | None = None
    message: str | None = None
    checks: dict[str, Any] | None = None


def check_actor_exists(actor_id: str, actor: Any) -> AuthorizationResult:
    if actor is None:
        return AuthorizationResult(False, "invalid_target", f"Actor {actor_id} not found")
    return AuthorizationResult(True, checks={"actor_exists": True})


def check_user_role_allowed(user_role: UserRole) -> AuthorizationResult:
    if user_role == UserRole.SPECTATOR:
        return AuthorizationResult(False, "unauthorized", "Spectators cannot perform combat actions")
    return AuthorizationResult(True, checks={"role": user_role.value})


def check_actor_ownership(
    user_role: UserRole,
    user_id: str,
    actor_owner_user_id: str | None,
) -> AuthorizationResult:
    checks: dict[str, Any] = {
        "owner_user_id": actor_owner_user_id,
        "ownership_ok": True,
    }
    if user_role == UserRole.PLAYER and actor_owner_user_id and actor_owner_user_id != user_id:
        checks["ownership_ok"] = False
        return AuthorizationResult(False, "unauthorized", "Player does not own this actor", checks)
    return AuthorizationResult(True, checks=checks)


def check_actor_alive(actor: Any) -> AuthorizationResult:
    if actor.current_hp <= 0:
        return AuthorizationResult(
            False,
            "invalid_action",
            "Dead combatants cannot act",
            {"alive": False},
        )
    return AuthorizationResult(True, checks={"alive": True})


def check_turn_ownership(
    action_type: str,
    turn_phase: str,
    active_actor_id: str | None,
    requesting_actor_id: str,
) -> AuthorizationResult:
    checks = {"active_actor_id": active_actor_id}
    if action_type != "reaction" and turn_phase == "active" and active_actor_id and active_actor_id != requesting_actor_id:
        return AuthorizationResult(False, "not_your_turn", "This actor is not the active turn", checks)
    return AuthorizationResult(True, checks=checks)


def combine_authorization_checks(*results: AuthorizationResult) -> AuthorizationResult:
    combined_checks: dict[str, Any] = {}
    for result in results:
        if result.checks:
            combined_checks.update(result.checks)
        if not result.allowed:
            return AuthorizationResult(
                False,
                result.reason_code,
                result.message,
                combined_checks or result.checks,
            )
    return AuthorizationResult(True, checks=combined_checks or None)
