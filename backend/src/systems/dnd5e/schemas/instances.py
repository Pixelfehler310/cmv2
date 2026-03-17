"""
D&D 5e Live Instances (Mutable Game State).

These models represent runtime state during a game session.
Created when DM places a monster, a player equips an item, or a spell is cast.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field

from .enums import (
    ActorType,
    ConditionType,
    DurationType,
    EffectType,
    ResetOn,
    Ability,
)
from .common import (
    AbilityScores,
    Position,
    ResourceCounter,
    SpeedBlock,
    SpellSlots,
)


# ---------------------------------------------------------------------------
# Effect Instance
# ---------------------------------------------------------------------------

class EffectInstance(BaseModel):
    """A live effect applied to an actor or the encounter."""

    id: str
    effect_id: str = ""
    name: str = ""
    source_id: str = ""  # actor who created this effect
    target_id: str = ""  # actor affected by this effect
    type: EffectType = EffectType.BONUS
    target_stat: str = ""
    value: int | str = 0
    duration_type: DurationType = DurationType.INSTANTANEOUS
    remaining_rounds: Optional[int] = None
    requires_concentration: bool = False


# ---------------------------------------------------------------------------
# Condition Instance
# ---------------------------------------------------------------------------

class ConditionInstance(BaseModel):
    """A condition currently affecting an actor."""

    condition: ConditionType
    source_id: str = ""
    source_effect_id: str = ""
    remaining_rounds: Optional[int] = None


# ---------------------------------------------------------------------------
# Item Instance
# ---------------------------------------------------------------------------

class ItemInstance(BaseModel):
    """A specific item in an actor's inventory."""

    id: str
    definition_slug: str
    custom_name: Optional[str] = None
    quantity: int = 1
    equipped: bool = False
    attuned: bool = False
    current_charges: Optional[int] = None
    max_charges: Optional[int] = None


# ---------------------------------------------------------------------------
# Spellcasting State
# ---------------------------------------------------------------------------

class PreparedSpell(BaseModel):
    spell_slug: str
    always_prepared: bool = False


class SpellcastingState(BaseModel):
    slots: dict[int, SpellSlots] = Field(default_factory=dict)
    prepared_spells: List[PreparedSpell] = Field(default_factory=list)
    spellcasting_ability: Optional[Ability] = None
    spell_save_dc: int = 0
    spell_attack_bonus: int = 0


# ---------------------------------------------------------------------------
# Concentration State
# ---------------------------------------------------------------------------

class ConcentrationState(BaseModel):
    is_concentrating: bool = False
    effect_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Resource Pool
# ---------------------------------------------------------------------------

class ResourcePool(BaseModel):
    counters: dict[str, ResourceCounter] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Actor Instance
# ---------------------------------------------------------------------------

class ActorInstance(BaseModel):
    """A live creature or character on the battlefield."""

    id: str
    owner_user_id: Optional[str] = None
    definition_slug: str = ""
    name: str = ""
    actor_type: ActorType = ActorType.MONSTER

    abilities: AbilityScores = Field(default_factory=AbilityScores)
    current_hp: int = 0
    max_hp: int = 0
    temp_hp: int = 0
    armor_class: int = 10
    speed: SpeedBlock = Field(default_factory=SpeedBlock)
    proficiency_bonus: int = 2
    position: Position = Field(default_factory=Position)

    conditions: List[ConditionInstance] = Field(default_factory=list)
    effects: List[EffectInstance] = Field(default_factory=list)
    inventory: List[ItemInstance] = Field(default_factory=list)
    spellcasting: Optional[SpellcastingState] = None
    resources: ResourcePool = Field(default_factory=ResourcePool)
    concentration: ConcentrationState = Field(
        default_factory=ConcentrationState)
    exhaustion_level: int = 0

    # Proficiencies (populated by CharacterBuilder for PCs)
    saving_throw_proficiencies: List[Ability] = Field(default_factory=list)
    skill_proficiencies: List[str] = Field(default_factory=list)
