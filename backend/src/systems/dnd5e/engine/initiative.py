"""
D&D 5e Initiative Engine.

Pure functions for rolling initiative and sorting combatants
with DEX-based tie-breaking per PHB rules.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel

from ..schemas.instances import ActorInstance
from .dice import DiceService
from .stat_calculator import calculate_modifier


# ---------------------------------------------------------------------------
# Result Model
# ---------------------------------------------------------------------------

class InitiativeEntry(BaseModel):
    """A single combatant's initiative result."""

    actor_id: str
    roll: int       # d20 + DEX modifier
    dex_score: int   # Raw DEX score for tie-breaking


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def roll_initiative(
    actor: ActorInstance,
    *,
    seed: Optional[int] = None,
) -> InitiativeEntry:
    """Roll initiative for an actor: d20 + DEX modifier.

    Args:
        actor: The actor rolling initiative.
        seed: Optional RNG seed for deterministic results.

    Returns:
        InitiativeEntry with the roll result and DEX score.
    """
    dex_mod = calculate_modifier(actor.abilities.dexterity)
    result = DiceService.roll_d20(modifier=dex_mod, seed=seed)

    return InitiativeEntry(
        actor_id=actor.id,
        roll=result.total,
        dex_score=actor.abilities.dexterity,
    )


def sort_combatants(entries: List[InitiativeEntry]) -> List[InitiativeEntry]:
    """Sort initiative entries descending by roll, then by DEX score for ties.

    Per PHB: ties are broken by the higher DEX score.

    Args:
        entries: List of InitiativeEntry to sort.

    Returns:
        New sorted list (does not mutate input).
    """
    return sorted(entries, key=lambda e: (e.roll, e.dex_score), reverse=True)
