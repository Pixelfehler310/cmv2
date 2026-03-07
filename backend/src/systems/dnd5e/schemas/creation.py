"""
D&D 5e Character Creation Blueprint.

Input DTO for the CharacterBuilder — describes the player's choices
before racial bonuses, class features, and background proficiencies
are applied.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field

from .common import AbilityScores


class CharacterCreationBlueprint(BaseModel):
    """Everything a player chooses when creating a character."""

    name: str
    race_slug: str
    class_slug: str
    background_slug: str
    level: int = 1

    # Raw ability scores BEFORE racial bonuses
    base_abilities: AbilityScores = Field(default_factory=AbilityScores)

    # Skills the player chose (from class skill list)
    chosen_skills: List[str] = Field(default_factory=list)

    # Optional specialisation
    subrace_slug: Optional[str] = None
    subclass_slug: Optional[str] = None
