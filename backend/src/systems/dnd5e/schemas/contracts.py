"""Canonical data-driven contracts for actions, abilities, and effects.

These models are additive foundations for the data-driven roadmap and are not
yet wired into resolver execution in this phase.
"""

from __future__ import annotations

from typing import Optional, Literal

from pydantic import BaseModel, Field


class ActionDefinition(BaseModel):
    """Canonical action schema for runtime-authoritative projection."""

    action_id: str
    name: str
    family: str = "utility"
    action_type_cost: Literal["action", "bonus_action",
                              "reaction", "move", "free"] = "action"
    targeting_mode: Literal["single_target", "aoe", "self"] = "single_target"
    range: Optional[int] = None
    save_context: Optional[dict] = None
    attack_context: Optional[dict] = None
    resource_costs: list[dict] = Field(default_factory=list)
    effect_intents: list[dict] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_ref: str = "custom"
    content_version: str = "1"
    enabled: bool = True


class AbilityBinding(BaseModel):
    """Links a canonical action to an actor template or runtime actor."""

    binding_id: str
    action_id: str
    actor_template_id: Optional[str] = None
    actor_id: Optional[str] = None
    unlock_conditions: list[dict] = Field(default_factory=list)
    override_payload: Optional[dict] = None


class EffectDurationSpec(BaseModel):
    type: Literal["instant", "rounds", "turns",
                  "until_removed", "concentration"] = "instant"
    value: Optional[int] = None
    timing: Literal["immediate", "start_of_turn", "end_of_turn"] = "immediate"


class EffectStackingSpec(BaseModel):
    mode: Literal["replace", "stack",
                  "refresh_duration", "highest_only"] = "replace"
    max_stacks: Optional[int] = None


class EffectModifierSpec(BaseModel):
    operation: Literal["set", "bonus", "multiply"]
    stat_key: str
    value: int | float | str


class EffectPeriodicSpec(BaseModel):
    trigger: Literal["start_of_turn", "end_of_turn"]
    operation: Literal["apply_damage", "apply_heal",
                       "apply_condition", "remove_condition"]
    payload: dict = Field(default_factory=dict)


class EffectRemovalTriggerSpec(BaseModel):
    trigger: Literal["on_save_success",
                     "on_damage_taken", "on_turn_end", "dispel"]


class EffectDefinition(BaseModel):
    """Canonical effect schema for data-driven execution."""

    effect_id: str
    name: str
    family: str = "utility"
    duration: EffectDurationSpec = Field(default_factory=EffectDurationSpec)
    stacking: EffectStackingSpec = Field(default_factory=EffectStackingSpec)
    tags: list[str] = Field(default_factory=list)
    modifiers: list[EffectModifierSpec] = Field(default_factory=list)
    grants_conditions: list[str] = Field(default_factory=list)
    periodic: list[EffectPeriodicSpec] = Field(default_factory=list)
    removal_triggers: list[EffectRemovalTriggerSpec] = Field(
        default_factory=list)
    metadata: dict = Field(default_factory=dict)


class EffectInstance(BaseModel):
    """Canonical applied effect state for runtime persistence."""

    instance_id: str
    effect_id: str
    source_actor_id: Optional[str] = None
    target_actor_id: str
    applied_at_round: int
    remaining_duration: Optional[int] = None
    concentration_owner_actor_id: Optional[str] = None
    stack_count: int = 1
    snapshot_payload: dict = Field(default_factory=dict)
    provenance: dict = Field(default_factory=dict)


class ContentPack(BaseModel):
    """Transport shape for JSON import/export of data-driven content."""

    pack_id: str
    system: str = "dnd5e"
    version: str
    actions: list[ActionDefinition] = Field(default_factory=list)
    abilities: list[AbilityBinding] = Field(default_factory=list)
    effects: list[EffectDefinition] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    migration_notes: str = ""
