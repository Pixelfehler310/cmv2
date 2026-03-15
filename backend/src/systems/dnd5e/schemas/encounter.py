"""
D&D 5e Encounter State Container.

The top-level state object that holds all actors, effects, and map state
during combat.
"""

from __future__ import annotations

from typing import Optional, List, Set

from pydantic import BaseModel, Field

from .enums import Size
from .common import Position
from .instances import ActorInstance, EffectInstance


# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------

class MapToken(BaseModel):
    actor_id: str
    position: Position = Field(default_factory=Position)
    size: Size = Size.MEDIUM


class MapState(BaseModel):
    width: int = 40   # grid squares
    height: int = 40
    grid_type: str = "square"
    difficult_terrain: List[Position] = Field(default_factory=list)
    tokens: List[MapToken] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------

class EncounterState(BaseModel):
    """Top-level combat state container."""

    id: str
    campaign_id: str = ""
    round_number: int = 0
    turn_phase: str = "pre_combat"  # pre_combat, active, post_combat
    active_index: int = 0
    combatants: List[ActorInstance] = Field(default_factory=list)
    turn_budgets: dict[str, dict] = Field(default_factory=dict)
    global_effects: List[EffectInstance] = Field(default_factory=list)
    map: MapState = Field(default_factory=MapState)
