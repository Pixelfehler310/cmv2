"""
Phase 3 — Initiative Tests (TDD).

Tests for initiative rolling, sorting, and DEX-based tie-breaking.
"""

import pytest

from src.systems.dnd5e.schemas.enums import ActorType
from src.systems.dnd5e.schemas.common import AbilityScores, SpeedBlock
from src.systems.dnd5e.schemas.instances import ActorInstance
from src.systems.dnd5e.engine.initiative import (
    InitiativeEntry,
    roll_initiative,
    sort_combatants,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_actor(
    id: str,
    name: str,
    dexterity: int = 10,
    **kwargs,
) -> ActorInstance:
    return ActorInstance(
        id=id,
        name=name,
        abilities=AbilityScores(dexterity=dexterity),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Initiative Sorting
# ---------------------------------------------------------------------------

class TestInitiativeSorting:
    def test_initiative_sorted_descending(self):
        """Highest initiative goes first."""
        entries = [
            InitiativeEntry(actor_id="wizard", roll=12, dex_score=14),
            InitiativeEntry(actor_id="dragon", roll=18, dex_score=10),
            InitiativeEntry(actor_id="fighter", roll=15, dex_score=16),
        ]
        sorted_entries = sort_combatants(entries)

        assert sorted_entries[0].actor_id == "dragon"
        assert sorted_entries[1].actor_id == "fighter"
        assert sorted_entries[2].actor_id == "wizard"

    def test_initiative_tie_higher_dex_goes_first(self):
        """PHB rule: ties broken by DEX score (higher goes first)."""
        entries = [
            InitiativeEntry(actor_id="fighter", roll=15, dex_score=14),
            InitiativeEntry(actor_id="rogue", roll=15, dex_score=18),
        ]
        sorted_entries = sort_combatants(entries)

        assert sorted_entries[0].actor_id == "rogue"
        assert sorted_entries[1].actor_id == "fighter"

    def test_single_combatant(self):
        """Edge case: single combatant."""
        entries = [
            InitiativeEntry(actor_id="hero", roll=10, dex_score=12),
        ]
        sorted_entries = sort_combatants(entries)
        assert len(sorted_entries) == 1
        assert sorted_entries[0].actor_id == "hero"

    def test_empty_list(self):
        """Edge case: no combatants."""
        assert sort_combatants([]) == []


# ---------------------------------------------------------------------------
# Initiative Rolling
# ---------------------------------------------------------------------------

class TestInitiativeRolling:
    def test_roll_initiative_returns_entry(self):
        """roll_initiative returns an InitiativeEntry with correct actor_id."""
        actor = _make_actor(id="fighter_1", name="Theron", dexterity=14)
        entry = roll_initiative(actor, seed=42)

        assert entry.actor_id == "fighter_1"
        assert entry.dex_score == 14
        # DEX 14 → modifier +2, so roll is d20 result + 2
        assert 3 <= entry.roll <= 22  # 1+2 to 20+2

    def test_roll_initiative_is_deterministic_with_seed(self):
        """Same seed → same roll."""
        actor = _make_actor(id="wizard_1", name="Elara", dexterity=16)
        entry1 = roll_initiative(actor, seed=99)
        entry2 = roll_initiative(actor, seed=99)

        assert entry1.roll == entry2.roll

    def test_roll_initiative_includes_dex_modifier(self):
        """DEX 18 → +4 modifier. Roll range should be [5, 24]."""
        actor = _make_actor(id="rogue_1", name="Shadow", dexterity=18)
        # Run multiple rolls to verify range
        rolls = [roll_initiative(actor, seed=i).roll for i in range(100)]
        assert min(rolls) >= 5   # 1 + 4
        assert max(rolls) <= 24  # 20 + 4

    def test_roll_initiative_negative_modifier(self):
        """DEX 6 → -2 modifier. Roll range should be [-1, 18]."""
        actor = _make_actor(id="orc_1", name="Gruk", dexterity=6)
        rolls = [roll_initiative(actor, seed=i).roll for i in range(100)]
        assert min(rolls) >= -1  # 1 + (-2)
        assert max(rolls) <= 18  # 20 + (-2)
