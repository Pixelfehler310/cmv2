"""
Phase 3 — Combat State Tests (TDD).

Tests for turn/round advancement, TurnBudget management, and reaction timing.
Uses the dnd5e EncounterState schema, NOT the legacy engine/combat_state.py.
"""

import pytest

from src.systems.dnd5e.schemas.enums import ActorType
from src.systems.dnd5e.schemas.common import AbilityScores, SpeedBlock
from src.systems.dnd5e.schemas.instances import ActorInstance
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.engine.initiative import InitiativeEntry
from src.systems.dnd5e.engine.combat_state import (
    TurnBudget,
    start_combat,
    next_turn,
    get_active_combatant,
    get_turn_budget,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_actor(id: str, name: str, dexterity: int = 10) -> ActorInstance:
    return ActorInstance(
        id=id,
        name=name,
        abilities=AbilityScores(dexterity=dexterity),
        current_hp=20,
        max_hp=20,
    )


def _create_encounter_with_3() -> EncounterState:
    """Create an encounter with 3 combatants at known initiative order."""
    enc = EncounterState(id="test_encounter")
    enc.combatants = [
        _make_actor("dragon", "Dragon", dexterity=10),
        _make_actor("fighter", "Fighter", dexterity=14),
        _make_actor("wizard", "Wizard", dexterity=16),
    ]
    initiatives = [
        InitiativeEntry(actor_id="dragon", roll=18, dex_score=10),
        InitiativeEntry(actor_id="fighter", roll=15, dex_score=14),
        InitiativeEntry(actor_id="wizard", roll=12, dex_score=16),
    ]
    start_combat(enc, initiatives)
    return enc


# ---------------------------------------------------------------------------
# Turn Advancement
# ---------------------------------------------------------------------------

class TestTurnAdvancement:
    def test_start_combat_sets_round_1(self):
        enc = _create_encounter_with_3()
        assert enc.round_number == 1

    def test_start_combat_active_is_first_in_initiative(self):
        enc = _create_encounter_with_3()
        active = get_active_combatant(enc)
        assert active.name == "Dragon"

    def test_turn_advancement_cycles(self):
        """After all combatants act, round increments."""
        enc = _create_encounter_with_3()
        assert enc.round_number == 1

        next_turn(enc)  # Fighter
        next_turn(enc)  # Wizard
        next_turn(enc)  # Back to Dragon → round 2

        assert enc.round_number == 2
        assert enc.active_index == 0
        assert get_active_combatant(enc).name == "Dragon"

    def test_next_turn_moves_to_next_combatant(self):
        enc = _create_encounter_with_3()
        assert get_active_combatant(enc).name == "Dragon"

        next_turn(enc)
        assert get_active_combatant(enc).name == "Fighter"

        next_turn(enc)
        assert get_active_combatant(enc).name == "Wizard"

    def test_combatant_order_follows_initiative(self):
        """Combatants are reordered by initiative, not insertion order."""
        enc = _create_encounter_with_3()
        names = [c.name for c in enc.combatants]
        assert names == ["Dragon", "Fighter", "Wizard"]


# ---------------------------------------------------------------------------
# Turn Budget
# ---------------------------------------------------------------------------

class TestTurnBudget:
    def test_turn_budget_resets_on_new_turn(self):
        """When a combatant's turn comes back, their budget is fresh."""
        enc = _create_encounter_with_3()
        budget = get_turn_budget(enc, "dragon")
        budget.use_action()
        assert budget.action_available is False

        # Cycle through everyone and back
        next_turn(enc)
        next_turn(enc)
        next_turn(enc)

        new_budget = get_turn_budget(enc, "dragon")
        assert new_budget.action_available is True

    def test_budget_tracks_action(self):
        budget = TurnBudget()
        assert budget.action_available is True
        budget.use_action()
        assert budget.action_available is False

    def test_budget_tracks_bonus_action(self):
        budget = TurnBudget()
        assert budget.bonus_action_available is True
        budget.use_bonus_action()
        assert budget.bonus_action_available is False

    def test_budget_tracks_reaction(self):
        budget = TurnBudget()
        assert budget.reaction_available is True
        budget.use_reaction()
        assert budget.reaction_available is False

    def test_budget_tracks_movement(self):
        budget = TurnBudget(movement_remaining=30)
        budget.use_movement(10)
        assert budget.movement_remaining == 20

    def test_movement_cannot_go_negative(self):
        budget = TurnBudget(movement_remaining=30)
        budget.use_movement(50)
        assert budget.movement_remaining == 0


# ---------------------------------------------------------------------------
# Reaction Timing
# ---------------------------------------------------------------------------

class TestReactionTiming:
    def test_reaction_persists_between_turns(self):
        """Reaction resets at start of YOUR turn, not others'."""
        enc = _create_encounter_with_3()
        dragon_budget = get_turn_budget(enc, "dragon")
        dragon_budget.use_reaction()

        next_turn(enc)  # Fighter's turn
        assert get_turn_budget(enc, "dragon").reaction_available is False

        next_turn(enc)  # Wizard's turn
        assert get_turn_budget(enc, "dragon").reaction_available is False

        next_turn(enc)  # Back to Dragon → reaction resets
        assert get_turn_budget(enc, "dragon").reaction_available is True

    def test_reaction_resets_only_on_own_turn(self):
        """Mid-round: dragon used reaction, fighter's turn — dragon still can't react."""
        enc = _create_encounter_with_3()

        # Dragon uses reaction during their turn
        dragon_budget = get_turn_budget(enc, "dragon")
        dragon_budget.use_reaction()

        # Move to fighter
        next_turn(enc)

        # Dragon's reaction should still be spent
        assert get_turn_budget(enc, "dragon").reaction_available is False
