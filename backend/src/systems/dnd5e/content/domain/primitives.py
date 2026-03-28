from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel

class DefinitionFamily(str, Enum):
    CLASS = "class"
    SPECIES = "species"
    BACKGROUND = "background"
    ABILITY = "ability"
    SPELL = "spell"
    ITEM = "item"
    MONSTER = "monster"
    LORE = "lore"
    CONDITION = "condition"

class LifecycleState(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"

class OperationType(str, Enum):
    ATTACK = "attack"
    SAVE = "save"
    HEAL = "heal"
    UTILITY = "utility"

class ModifierType(str, Enum):
    FLAT = "flat"
    DICE = "dice"
    MULTIPLIER = "multiplier"

class ModifierSpec(BaseModel):
    target_stat: str
    modifier_type: ModifierType
    value: str

class ActionOperationSpec(BaseModel):
    operation_type: OperationType
    target_criteria: str
    range: str
    duration: str
    payload: Dict[str, Any]
