"""
D&D 5e Effect Engine.

Functions for adding, removing, and ticking effect durations on actors
within an encounter. Handles automatic cleanup of linked conditions
when effects expire.
"""

from __future__ import annotations

from typing import Optional

from ..schemas.instances import ActorInstance, EffectInstance
from ..schemas.encounter import EncounterState


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def add_effect(encounter: EncounterState, effect: EffectInstance) -> None:
    """Add an effect to the target actor in the encounter.

    The effect's target_id determines which actor receives it.

    Args:
        encounter: The active encounter.
        effect: The effect to apply.
    """
    for actor in encounter.combatants:
        if actor.id == effect.target_id:
            actor.effects.append(effect)
            return


def remove_effect(encounter: EncounterState, effect_id: str) -> None:
    """Remove an effect by ID from any actor in the encounter.

    Also removes any conditions linked to this effect via source_effect_id.

    Args:
        encounter: The active encounter.
        effect_id: The ID of the effect to remove.
    """
    for actor in encounter.combatants:
        # Remove the effect
        actor.effects = [e for e in actor.effects if e.id != effect_id]

        # Remove linked conditions
        actor.conditions = [
            c for c in actor.conditions
            if c.source_effect_id != effect_id
        ]


def has_effect(actor: ActorInstance, effect_id: str) -> bool:
    """Check if an actor has a specific effect by ID.

    Args:
        actor: The actor to check.
        effect_id: The effect ID to look for.

    Returns:
        True if the actor has the effect.
    """
    return any(e.id == effect_id for e in actor.effects)


def tick_effects(encounter: EncounterState, *, source_id: str) -> None:
    """Tick effect durations for effects from a specific source.

    Called at the start/end of a turn. Only decrements effects whose
    source_id matches. Effects that reach 0 remaining rounds are
    automatically removed, along with any linked conditions.

    Args:
        encounter: The active encounter.
        source_id: The actor whose effects should be ticked.
    """
    effects_to_remove: list[str] = []

    for actor in encounter.combatants:
        for effect in actor.effects:
            if effect.source_id == source_id and effect.remaining_rounds is not None:
                effect.remaining_rounds -= 1
                if effect.remaining_rounds <= 0:
                    effects_to_remove.append(effect.id)

    for effect_id in effects_to_remove:
        remove_effect(encounter, effect_id)
