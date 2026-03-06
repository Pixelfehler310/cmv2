"""
D&D 5e State Filter — Fog of War.

Filters EncounterState snapshots based on user role.
DM sees everything; players see a sanitized view.
Per architecture doc 09 § 5.
"""

from __future__ import annotations

from typing import Any

from src.core.sessions.models import UserRole, SessionContext
from .schemas.encounter import EncounterState
from .schemas.enums import ActorType


# ---------------------------------------------------------------------------
# Health descriptors
# ---------------------------------------------------------------------------

def _health_descriptor(current_hp: int, max_hp: int) -> str:
    """Convert HP values to a vague description for players."""
    if max_hp <= 0:
        return "unknown"
    ratio = current_hp / max_hp
    if ratio >= 1.0:
        return "healthy"
    if ratio >= 0.75:
        return "lightly wounded"
    if ratio >= 0.50:
        return "bloodied"
    if ratio >= 0.25:
        return "badly wounded"
    if current_hp > 0:
        return "near death"
    return "dead"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def filter_state_for_role(
    encounter: EncounterState,
    ctx: SessionContext,
) -> dict[str, Any]:
    """Produce a state snapshot filtered by the user's role.

    DM: full state.
    Player/Spectator: monster HP hidden, replaced with descriptor.
    """
    if ctx.role == UserRole.DM:
        return _dm_view(encounter)
    return _player_view(encounter, ctx.user_id)


def _dm_view(encounter: EncounterState) -> dict[str, Any]:
    """DM gets the complete, unfiltered encounter state."""
    return encounter.model_dump(mode="json")


def _player_view(encounter: EncounterState, user_id: str) -> dict[str, Any]:
    """Players get filtered state — monster HP hidden, etc."""
    data = encounter.model_dump(mode="json")

    filtered_combatants = []
    for combatant in data.get("combatants", []):
        actor_type = combatant.get("actor_type", "")

        # Monsters and NPCs: hide exact HP, show descriptor
        if actor_type in (ActorType.MONSTER.value, ActorType.NPC.value):
            current_hp = combatant.get("current_hp", 0)
            max_hp = combatant.get("max_hp", 1)
            combatant["health_status"] = _health_descriptor(current_hp, max_hp)
            # Remove exact HP values
            combatant.pop("current_hp", None)
            combatant.pop("max_hp", None)
            combatant.pop("temp_hp", None)
            # Remove internal stats players shouldn't see
            combatant.pop("abilities", None)
            combatant.pop("spellcasting", None)
            combatant.pop("resources", None)
            combatant.pop("exhaustion_level", None)

        filtered_combatants.append(combatant)

    data["combatants"] = filtered_combatants
    return data
