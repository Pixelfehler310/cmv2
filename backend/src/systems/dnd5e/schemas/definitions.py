"""
D&D 5e Compendium Definitions (Read-Only Templates).

These models represent SRD compendium data loaded from Open5e JSON.
They are never mutated during play — runtime state uses Instance models.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from .enums import (
    ActionType,
    AoeShape,
    DamageType,
    ItemCategory,
    MagicSchool,
    Rarity,
    Size,
    Ability,
)
from .common import (
    AbilityScores,
    AreaOfEffect,
    Components,
    EffectDefinition,
    LevelFeature,
    RechargeRule,
    SaveRequirement,
    SavingThrows,
    SkillChoice,
    SpeedBlock,
    SpellcastingProgression,
    UsageLimit,
    AbilityScoreBonus,
)


# ---------------------------------------------------------------------------
# Trait Definition
# ---------------------------------------------------------------------------

class TraitDefinition(BaseModel):
    """A special ability or racial trait (e.g. Legendary Resistance)."""

    name: str
    desc: str = ""
    usage: Optional[UsageLimit] = None


# ---------------------------------------------------------------------------
# Action Definition
# ---------------------------------------------------------------------------

class ActionDefinition(BaseModel):
    """A single action a creature can take (attack, breath weapon, etc.).

    Fields are nullable because not all actions have all properties:
    - Multiattack has only name + desc
    - Melee attacks have attack_bonus + damage_dice
    - Breath weapons have save DCs instead of attack rolls
    """

    name: str
    desc: str = ""
    action_type: Optional[ActionType] = None
    attack_bonus: Optional[int] = None
    damage_dice: Optional[str] = None
    damage_bonus: Optional[int] = None
    damage_type: Optional[DamageType] = None
    reach: Optional[int] = None
    save: Optional[SaveRequirement] = None
    aoe: Optional[AreaOfEffect] = None
    recharge: Optional[RechargeRule] = None


# ---------------------------------------------------------------------------
# Monster Definition
# ---------------------------------------------------------------------------

class MonsterDefinition(BaseModel):
    """A full SRD monster stat block."""

    model_config = ConfigDict(populate_by_name=True)

    slug: str
    name: str
    size: Size
    type: str
    subtype: str = ""
    alignment: str = ""
    armor_class: int
    armor_desc: Optional[str] = None
    hit_points: int
    hit_dice: str
    speed: SpeedBlock
    abilities: AbilityScores
    saves: SavingThrows = Field(default_factory=SavingThrows)
    skills: dict[str, int] = Field(default_factory=dict)

    # Defense strings — stored as-is from SRD, parsed on demand
    damage_vulnerabilities: str = ""
    damage_resistances: str = ""
    damage_immunities: str = ""
    condition_immunities: str = ""

    senses: str = ""
    languages: str = ""
    challenge_rating: float = Field(0.0, alias="cr")
    xp: int = 0

    # Action lists
    actions: List[ActionDefinition] = Field(default_factory=list)
    bonus_actions: Optional[List[ActionDefinition]] = None
    reactions: Optional[List[ActionDefinition]] = None
    legendary_actions: List[ActionDefinition] = Field(default_factory=list)
    special_abilities: List[TraitDefinition] = Field(default_factory=list)

    legendary_desc: str = ""
    legendary_action_count: int = 0
    spell_list: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Spell Definition
# ---------------------------------------------------------------------------

class SpellDefinition(BaseModel):
    """A full SRD spell entry."""

    model_config = ConfigDict(populate_by_name=True)

    slug: str
    name: str
    level: int = Field(alias="level_int")
    school: MagicSchool
    casting_time: str = ""
    range: str = ""
    target_range_sort: int = 0
    components: Components = Field(default_factory=Components)
    material: str = ""
    duration: str = ""
    requires_concentration: bool = False
    can_be_cast_as_ritual: bool = Field(False, alias="ritual")
    desc: str = ""
    higher_level: str = ""
    spell_lists: List[str] = Field(default_factory=list)
    aoe: Optional[AreaOfEffect] = None


# ---------------------------------------------------------------------------
# Item Definition
# ---------------------------------------------------------------------------

class ItemDefinition(BaseModel):
    """A weapon, armor, or equipment entry from the SRD."""

    model_config = ConfigDict(populate_by_name=True)

    slug: str
    name: str
    category: str = ""
    cost: str = ""
    damage_dice: Optional[str] = None
    damage_type: Optional[str] = None
    weight: str = ""
    properties: List[str] = Field(default_factory=list)
    rarity: Optional[Rarity] = None
    requires_attunement: bool = False
    effects: List[EffectDefinition] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Character-Building Definitions (Phase 5, but type-defined here)
# ---------------------------------------------------------------------------

class SubraceDefinition(BaseModel):
    slug: str
    name: str
    desc: str = ""
    ability_bonuses: List[AbilityScoreBonus] = Field(default_factory=list)
    racial_traits: List[TraitDefinition] = Field(default_factory=list)
    proficiencies: List[str] = Field(default_factory=list)


class RaceDefinition(BaseModel):
    slug: str
    name: str
    desc: str = ""
    speed: SpeedBlock = Field(default_factory=SpeedBlock)
    size: Size = Size.MEDIUM
    ability_bonuses: List[AbilityScoreBonus] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    racial_traits: List[TraitDefinition] = Field(default_factory=list)
    proficiencies: List[str] = Field(default_factory=list)
    subraces: List[SubraceDefinition] = Field(default_factory=list)


class SubclassDefinition(BaseModel):
    slug: str
    name: str
    desc: str = ""
    parent_class_slug: str = ""
    level_features: List[LevelFeature] = Field(default_factory=list)
    bonus_spell_list: List[str] = Field(default_factory=list)


class ClassDefinition(BaseModel):
    slug: str
    name: str
    desc: str = ""
    hit_die: str = "d8"
    saving_throw_proficiencies: List[Ability] = Field(default_factory=list)
    armor_proficiencies: List[str] = Field(default_factory=list)
    weapon_proficiencies: List[str] = Field(default_factory=list)
    tool_proficiencies: List[str] = Field(default_factory=list)
    skill_choices: Optional[SkillChoice] = None
    starting_equipment: List[str] = Field(default_factory=list)
    level_features: List[LevelFeature] = Field(default_factory=list)
    spellcasting: Optional[SpellcastingProgression] = None
    subclasses: List[SubclassDefinition] = Field(default_factory=list)


class BackgroundDefinition(BaseModel):
    slug: str
    name: str
    desc: str = ""
    skill_proficiencies: List[str] = Field(default_factory=list)
    tool_proficiencies: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    starting_equipment: List[str] = Field(default_factory=list)
    feature: Optional[TraitDefinition] = None
