from __future__ import annotations

from src.systems.dnd5e.domain.action_economy import (
    normalize_action_type,
    can_spend_action_budget,
    apply_action_budget_consumption,
    get_or_create_in_memory_budget,
)


def test_normalize_action_type_maps_known_aliases() -> None:
    assert normalize_action_type("attack") == "action"
    assert normalize_action_type("cast-spell") == "action"
    assert normalize_action_type("bonus") == "bonus_action"
    assert normalize_action_type("move_token") == "move"


def test_can_spend_action_budget_denies_exhausted_action() -> None:
    result = can_spend_action_budget(
        action_type="action",
        action_available=False,
        bonus_action_available=True,
        reaction_available=True,
    )
    assert result.allowed is False
    assert result.reason_code == "action_exhausted"
    assert result.check_key == "action_available"


def test_can_spend_action_budget_denies_exhausted_bonus_action() -> None:
    result = can_spend_action_budget(
        action_type="bonus_action",
        action_available=True,
        bonus_action_available=False,
        reaction_available=True,
    )
    assert result.allowed is False
    assert result.reason_code == "bonus_action_exhausted"


def test_can_spend_action_budget_denies_exhausted_reaction() -> None:
    result = can_spend_action_budget(
        action_type="reaction",
        action_available=True,
        bonus_action_available=True,
        reaction_available=False,
    )
    assert result.allowed is False
    assert result.reason_code == "reaction_exhausted"


def test_apply_action_budget_consumption_updates_budget_flags() -> None:
    budget = {
        "action_available": True,
        "bonus_action_available": True,
        "reaction_available": True,
        "max_movement": 6,
        "movement_used": 2,
    }
    updated = apply_action_budget_consumption("bonus_action", budget)
    assert updated["bonus_action_available"] is False
    assert updated["movement_remaining"] == 4


def test_get_or_create_in_memory_budget_creates_default_budget() -> None:
    budgets = {}
    budget = get_or_create_in_memory_budget(
        turn_budgets=budgets,
        actor_id="a1",
        max_movement=6,
        round_number=1,
    )
    assert budget["action_available"] is True
    assert budget["movement_remaining"] == 6


def test_get_or_create_in_memory_budget_resets_on_round_change() -> None:
    budgets = {
        "a1": {
            "action_available": False,
            "bonus_action_available": False,
            "reaction_available": False,
            "max_movement": 6,
            "movement_used": 5,
            "movement_remaining": 1,
            "round_number": 1,
        }
    }
    budget = get_or_create_in_memory_budget(
        turn_budgets=budgets,
        actor_id="a1",
        max_movement=6,
        round_number=2,
    )
    assert budget["action_available"] is True
    assert budget["bonus_action_available"] is True
    assert budget["reaction_available"] is True
    assert budget["movement_used"] == 0
    assert budget["movement_remaining"] == 6
