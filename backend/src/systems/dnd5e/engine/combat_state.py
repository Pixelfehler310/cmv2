"""
D&D 5e Combat State Engine.

Operations on EncounterState for turn management, round tracking,
and TurnBudget lifecycle. Works with the dnd5e schema models.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel

from ..schemas.instances import ActorInstance
from ..schemas.encounter import EncounterState
from .initiative import InitiativeEntry, sort_combatants


# ---------------------------------------------------------------------------
# Turn Budget
# ---------------------------------------------------------------------------

class TurnBudget(BaseModel):
    """Tracks available resources for a combatant's turn."""

    action_available: bool = True
    bonus_action_available: bool = True
    reaction_available: bool = True
    movement_remaining: int = 30  # Default; should be set from speed

    def use_action(self) -> None:
        self.action_available = False

    def use_bonus_action(self) -> None:
        self.bonus_action_available = False

    def use_reaction(self) -> None:
        self.reaction_available = False

    def use_movement(self, amount: int) -> None:
        self.movement_remaining = max(0, self.movement_remaining - amount)

    def reset_full(self) -> None:
        """Reset all resources for a new turn."""
        self.action_available = True
        self.bonus_action_available = True
        self.reaction_available = True
        self.movement_remaining = 30

    def reset_reaction(self) -> None:
        """Reset only reaction (resets at start of your turn)."""
        self.reaction_available = True


# ---------------------------------------------------------------------------
# Budget Storage (keyed by actor_id)
# ---------------------------------------------------------------------------

# Module-level storage for turn budgets, keyed by encounter_id:actor_id
_turn_budgets: dict[str, TurnBudget] = {}


def _budget_key(encounter_id: str, actor_id: str) -> str:
    return f"{encounter_id}:{actor_id}"


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def start_combat(
    encounter: EncounterState,
    initiatives: List[InitiativeEntry],
) -> None:
    """Initialize combat with sorted initiative order.

    Reorders encounter.combatants to match initiative order.
    Sets round 1, active_index 0.

    Args:
        encounter: The encounter to start.
        initiatives: Initiative entries for each combatant.
    """
    # Sort by initiative
    sorted_init = sort_combatants(initiatives)

    # Build actor lookup
    actor_map = {a.id: a for a in encounter.combatants}

    # Reorder combatants to match initiative
    encounter.combatants = [
        actor_map[entry.actor_id]
        for entry in sorted_init
        if entry.actor_id in actor_map
    ]

    encounter.round_number = 1
    encounter.active_index = 0
    encounter.turn_phase = "active"

    # Initialize budgets for all combatants
    for actor in encounter.combatants:
        key = _budget_key(encounter.id, actor.id)
        _turn_budgets[key] = TurnBudget()

    # Trigger start of first turn (reset reaction for active combatant)
    _on_turn_start(encounter)


def next_turn(encounter: EncounterState) -> None:
    """Advance to the next combatant's turn.

    Wraps around to the next round when all combatants have acted.
    Resets turn budget for the new active combatant.
    Reaction resets only at the start of YOUR turn per PHB.
    """
    if not encounter.combatants:
        return

    encounter.active_index += 1

    if encounter.active_index >= len(encounter.combatants):
        encounter.active_index = 0
        encounter.round_number += 1

    _on_turn_start(encounter)


def get_active_combatant(encounter: EncounterState) -> Optional[ActorInstance]:
    """Return the combatant whose turn it currently is."""
    if not encounter.combatants or encounter.round_number == 0:
        return None
    return encounter.combatants[encounter.active_index]


def get_turn_budget(encounter: EncounterState, actor_id: str) -> TurnBudget:
    """Get the TurnBudget for a specific combatant.

    Creates a new budget if one doesn't exist yet.
    """
    key = _budget_key(encounter.id, actor_id)
    if key not in _turn_budgets:
        _turn_budgets[key] = TurnBudget()
    return _turn_budgets[key]


# ---------------------------------------------------------------------------
# Internal Hooks
# ---------------------------------------------------------------------------

def _on_turn_start(encounter: EncounterState) -> None:
    """Reset resources for the new active combatant.

    Per PHB: reaction resets at the start of YOUR turn.
    Action, bonus action, and movement reset each turn.
    """
    active = get_active_combatant(encounter)
    if not active:
        return

    budget = get_turn_budget(encounter, active.id)
    budget.reset_full()
