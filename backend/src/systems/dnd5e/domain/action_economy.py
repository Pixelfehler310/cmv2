from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActionBudgetCheckResult:
    allowed: bool
    reason_code: str | None = None
    message: str | None = None
    check_key: str | None = None


def normalize_action_type(action_type: str) -> str:
    normalized = (action_type or "").strip().lower()
    if normalized in {"", "action", "attack", "cast_spell", "cast-spell", "spell", "main_action"}:
        return "action"
    if normalized in {"bonus_action", "bonus-action", "bonus"}:
        return "bonus_action"
    if normalized in {"reaction"}:
        return "reaction"
    if normalized in {"move", "movement", "move_token"}:
        return "move"
    return normalized


def can_spend_action_budget(
    action_type: str,
    action_available: bool,
    bonus_action_available: bool,
    reaction_available: bool,
) -> ActionBudgetCheckResult:
    if action_type == "action" and not action_available:
        return ActionBudgetCheckResult(False, "action_exhausted", "Action already spent this turn", "action_available")
    if action_type == "bonus_action" and not bonus_action_available:
        return ActionBudgetCheckResult(False, "bonus_action_exhausted", "Bonus action already spent this turn", "bonus_action_available")
    if action_type == "reaction" and not reaction_available:
        return ActionBudgetCheckResult(False, "reaction_exhausted", "Reaction already spent", "reaction_available")
    return ActionBudgetCheckResult(True)


def apply_action_budget_consumption(action_type: str, budget_state: dict[str, Any]) -> dict[str, Any]:
    if action_type == "action":
        budget_state["action_available"] = False
    elif action_type == "bonus_action":
        budget_state["bonus_action_available"] = False
    elif action_type == "reaction":
        budget_state["reaction_available"] = False

    max_movement = int(budget_state.get("max_movement", 30))
    movement_used = int(budget_state.get("movement_used", 0))
    budget_state["movement_remaining"] = max(max_movement - movement_used, 0)
    return budget_state


def get_or_create_in_memory_budget(
    turn_budgets: dict[str, dict[str, Any]],
    actor_id: str,
    max_movement: int,
    round_number: int,
) -> dict[str, Any]:
    budget = turn_budgets.get(actor_id)
    if budget is None:
        budget = {
            "action_available": True,
            "bonus_action_available": True,
            "reaction_available": True,
            "max_movement": max_movement,
            "movement_used": 0,
            "movement_remaining": max_movement,
            "round_number": round_number,
        }
        turn_budgets[actor_id] = budget

    budget["max_movement"] = max_movement
    if int(budget.get("round_number", round_number)) != round_number:
        budget["action_available"] = True
        budget["bonus_action_available"] = True
        budget["reaction_available"] = True
        budget["movement_used"] = 0
        budget["round_number"] = round_number

    budget["movement_remaining"] = max(
        int(budget.get("max_movement", max_movement)) -
        int(budget.get("movement_used", 0)),
        0,
    )
    return budget
