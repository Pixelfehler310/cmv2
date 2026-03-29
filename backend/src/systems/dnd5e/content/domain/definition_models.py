__production_status__ = "gold"
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, model_validator

from .primitives import (
    DefinitionFamily, 
    LifecycleState, 
    ModifierSpec, 
    ActionOperationSpec
)
from .invariants import CompendiumErrorCode

class DefinitionRecord(BaseModel):
    id: str
    family: DefinitionFamily
    slug: str
    name: str
    lifecycle_state: LifecycleState
    content_version: int
    schema_version: int
    pack_id: str
    provenance_source: str
    provenance_author: Optional[str] = None
    provenance_updated_at: datetime

    @model_validator(mode="after")
    def validate_content_version(self) -> 'DefinitionRecord':
        if self.content_version < 1:
            raise ValueError(
                f"{CompendiumErrorCode.VALIDATION_FAILED.value}: content_version must be >= 1"
            )
        return self


# --- Simple Definitions ---

class LoreDefinition(DefinitionRecord):
    family: Literal[DefinitionFamily.LORE] = DefinitionFamily.LORE
    lore_type: Literal["faction", "region", "place", "deity"]
    rich_text_content: str

class SpeciesDefinition(DefinitionRecord):
    family: Literal[DefinitionFamily.SPECIES] = DefinitionFamily.SPECIES
    speed: int
    size: str

class BackgroundDefinition(DefinitionRecord):
    family: Literal[DefinitionFamily.BACKGROUND] = DefinitionFamily.BACKGROUND
    skill_proficiencies: List[str]

class ClassDefinition(DefinitionRecord):
    family: Literal[DefinitionFamily.CLASS] = DefinitionFamily.CLASS
    hit_die: str
    saving_throw_proficiencies: List[str]


# --- Complex Definitions ---

class ConditionDefinition(DefinitionRecord):
    family: Literal[DefinitionFamily.CONDITION] = DefinitionFamily.CONDITION
    condition_type: Literal["buff", "debuff", "status"]
    has_levels: bool
    modifier_specs: List[ModifierSpec]

class AbilityDefinition(DefinitionRecord):
    family: Literal[DefinitionFamily.ABILITY] = DefinitionFamily.ABILITY
    ability_type: Literal["feature", "feat"]
    action_operation_specs: List[ActionOperationSpec]
    passive_effects: List[ModifierSpec]

class SpellDefinition(DefinitionRecord):
    family: Literal[DefinitionFamily.SPELL] = DefinitionFamily.SPELL
    level: int
    school: str
    casting_time: str
    action_operation_specs: List[ActionOperationSpec]

class ItemDefinition(DefinitionRecord):
    family: Literal[DefinitionFamily.ITEM] = DefinitionFamily.ITEM
    item_type: Literal["weapon", "armor", "gear", "consumable"]
    weight: float
    cost: int
    action_operation_specs: List[ActionOperationSpec]

class MonsterDefinition(DefinitionRecord):
    family: Literal[DefinitionFamily.MONSTER] = DefinitionFamily.MONSTER
    challenge_rating: float
    armor_class: int
    hit_points_formula: str
    action_operation_specs: List[ActionOperationSpec]
