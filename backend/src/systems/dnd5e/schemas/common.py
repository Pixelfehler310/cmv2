"""
D&D 5e Common Value Types.

Reusable Pydantic models for ability scores, speed, positions,
spell components, and other shared data structures.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field

from .enums import (
    Ability,
    AoeShape,
    EffectType,
    ResetOn,
)


# ---------------------------------------------------------------------------
# Core Stat Blocks
# ---------------------------------------------------------------------------

class AbilityScores(BaseModel):
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10


class SavingThrows(BaseModel):
    strength_save: Optional[int] = None
    dexterity_save: Optional[int] = None
    constitution_save: Optional[int] = None
    intelligence_save: Optional[int] = None
    wisdom_save: Optional[int] = None
    charisma_save: Optional[int] = None


class SpeedBlock(BaseModel):
    walk: int = 30
    fly: Optional[int] = None
    swim: Optional[int] = None
    climb: Optional[int] = None
    burrow: Optional[int] = None
    hover: bool = False


# ---------------------------------------------------------------------------
# Spatial
# ---------------------------------------------------------------------------

class Position(BaseModel):
    x: int = 0
    y: int = 0
    elevation: int = 0


# ---------------------------------------------------------------------------
# Spell Components
# ---------------------------------------------------------------------------

class Components(BaseModel):
    verbal: bool = False
    somatic: bool = False
    material: bool = False
    material_desc: Optional[str] = None


# ---------------------------------------------------------------------------
# Action / Effect Sub-types
# ---------------------------------------------------------------------------

class AreaOfEffect(BaseModel):
    shape: AoeShape
    size: int  # feet


class SaveRequirement(BaseModel):
    ability: Ability
    dc: int
    on_fail: str = "full_damage"
    on_success: str = "half_damage"


class RechargeRule(BaseModel):
    min_roll: int  # e.g. 5 for "Recharge 5-6"
    max_roll: int = 6


class UsageLimit(BaseModel):
    uses: int
    reset_on: ResetOn


# ---------------------------------------------------------------------------
# Character Building Sub-types
# ---------------------------------------------------------------------------

class AbilityScoreBonus(BaseModel):
    ability: Ability
    bonus: int


class SkillChoice(BaseModel):
    options: List[str] = Field(default_factory=list)
    choose: int = 2


class ResourceCounter(BaseModel):
    name: str
    max: int
    current: int
    resets_on: ResetOn


class SpellSlots(BaseModel):
    max: int
    current: int


class SpellcastingProgression(BaseModel):
    ability: Ability
    type: str = "full"  # full, half, third, pact
    cantrips_known_at_1: int = 0
    slots_by_level: dict[int, SpellSlots] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Forward-declared types used in LevelFeature
# (EffectDefinition and ActionDefinition are defined in definitions.py;
#  LevelFeature needs to be here because common.py is imported first.
#  We use deferred string annotations via __future__.annotations.)
# ---------------------------------------------------------------------------

class EffectDefinition(BaseModel):
    """Lightweight version for embedding in LevelFeature / ItemDefinition."""

    name: str
    type: EffectType
    target_stat: str = ""
    value: int | str = 0
    source: Optional[str] = None


class LevelFeature(BaseModel):
    level: int
    feature_slug: str
    effects: List[EffectDefinition] = Field(default_factory=list)
    granted_actions: list = Field(default_factory=list)  # list[ActionDefinition] — resolved at runtime
    granted_resource: Optional[ResourceCounter] = None
