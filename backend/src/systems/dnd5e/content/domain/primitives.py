__production_status__ = "gold"
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

# --- Foundational Enums ---

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
    ATTACK_ROLL = "attack_roll"
    SAVE = "save"
    HEAL = "heal"
    EFFECT_APPLICATION = "effect_application"


# --- Result Piping Mechanics (v1 Draft - Extensible) ---

class ResultAttribute(str, Enum):
    """
    Identifies specific data points output by an operation in the V2 graph.
    NOTE: This list is an initial draft and will be extended as V2 mechanics evolve.
    """
    TOTAL_DAMAGE = "total_damage"                # Resolved damage (after resistances)
    ACTUAL_HEAL = "actual_heal"                  # Resolved healing (not exceeding max HP)
    BASE_DIE_ROLL = "base_die_roll"              # Raw roll (before modifiers)
    SAVING_THROW_MARGIN = "saving_throw_margin"  # How much they failed/passed by
    TARGET_COUNT = "target_count"                # Number of successfully hit targets

class ResultReference(BaseModel):
    """A pointer from a consumer operation to a source operation's result."""
    source_operation_id: str
    attribute: ResultAttribute
    multiplier: float = 1.0
    bonus: int = 0

# Union for fields that can be static OR dynamic references
# Supports raw dice strings ("1d8"), static numbers (5), or pipes
DynamicValueSource = Union[str, int, ResultReference]


# --- Modifier Mechanics ---

class FlatModifierSpec(BaseModel):
    modifier_type: Literal["flat"] = "flat"
    target_stat: str
    value: DynamicValueSource  # Refactored to support result piping (e.g. Max HP Drain)
    stack_group: str

class DiceModifierSpec(BaseModel):
    modifier_type: Literal["dice"] = "dice"
    target_stat: str
    dice_notation: str
    condition_gate: Optional[str] = None

class RuleOverrideModifierSpec(BaseModel):
    modifier_type: Literal["rule_override"] = "rule_override"
    target_stat: str
    override_value: str

ModifierSpec = Union[FlatModifierSpec, DiceModifierSpec, RuleOverrideModifierSpec]


# --- Action Execution Sub-Components ---

class ActivationCost(str, Enum):
    ACTION = "action"
    BONUS_ACTION = "bonus_action"
    REACTION = "reaction"
    FREE = "free"

class TargetingType(str, Enum):
    SINGLE = "single"
    SELF = "self"
    AOE_SPHERE = "aoe_sphere"
    AOE_CONE = "aoe_cone"
    LINE = "line"

class ResourceConsumption(BaseModel):
    resource_type: str
    count: int

class TargetingSpec(BaseModel):
    type: TargetingType
    range_feet: int
    max_targets: int
    radius_feet: Optional[int] = None

class DamageInstance(BaseModel):
    value: DynamicValueSource  # Refactored for piping (e.g. Divine Smite scaling)
    damage_type: str
    add_stat_modifier: bool


# --- Polymorphic Operation Payloads ---

class AttackRollPayload(BaseModel):
    operation_type: Literal[OperationType.ATTACK_ROLL] = OperationType.ATTACK_ROLL
    attack_type: Literal["melee_weapon", "ranged_weapon", "melee_spell", "ranged_spell"]
    stat_override: Optional[str] = None
    damage_instances: List[DamageInstance]
    on_hit_effects: List[Dict[str, Any]] = Field(default_factory=list)  # Mocking nested effects list
    critical_threshold: int = 20

class SavePayload(BaseModel):
    operation_type: Literal[OperationType.SAVE] = OperationType.SAVE
    save_stat: str
    save_dc_override: Optional[int] = None
    failure_damage: List[DamageInstance]
    success_rule: Literal["half_damage", "no_damage"]
    apply_conditions_on_fail: List[str] = Field(default_factory=list)

class HealPayload(BaseModel):
    operation_type: Literal[OperationType.HEAL] = OperationType.HEAL
    amount: DynamicValueSource  # Refactored for piping (e.g. Life Drain)
    add_stat_modifier: bool
    stat_used: str
    temp_hp: bool
    removes_conditions: List[str] = Field(default_factory=list)

class EffectApplicationPayload(BaseModel):
    operation_type: Literal[OperationType.EFFECT_APPLICATION] = OperationType.EFFECT_APPLICATION
    applied_condition_id: str
    duration_rounds: int
    requires_concentration: bool
    allow_save_ends: bool


# The payload union is automatically discriminated by "operation_type"
OperationPayload = Union[
    AttackRollPayload, 
    SavePayload, 
    HealPayload, 
    EffectApplicationPayload
]


# --- The Root Execution Container ---

class ActionOperationSpec(BaseModel):
    operation_id: str  # Mandatory for graphing and result referencing
    activation_cost: ActivationCost
    activation_trigger: Optional[str] = None
    resource_consumption: Optional[ResourceConsumption] = None
    targeting_spec: TargetingSpec
    payload: OperationPayload = Field(..., discriminator='operation_type')
