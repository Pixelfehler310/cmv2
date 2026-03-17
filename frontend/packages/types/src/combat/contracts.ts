export type ActionTypeCost = "action" | "bonus_action" | "reaction" | "move" | "free";
export type TargetingMode = "single_target" | "aoe" | "self";

export interface ActionDefinitionContract {
  action_id: string;
  name: string;
  family: string;
  action_type_cost: ActionTypeCost;
  targeting_mode: TargetingMode;
  range?: number | null;
  save_context?: Record<string, unknown> | null;
  attack_context?: Record<string, unknown> | null;
  resource_costs: Array<Record<string, unknown>>;
  effect_intents: Array<Record<string, unknown>>;
  tags: string[];
  source_ref: string;
  content_version: string;
  enabled: boolean;
}

export interface AbilityBindingContract {
  binding_id: string;
  action_id: string;
  actor_template_id?: string | null;
  actor_id?: string | null;
  unlock_conditions: Array<Record<string, unknown>>;
  override_payload?: Record<string, unknown> | null;
}

export interface EffectDurationSpecContract {
  type: "instant" | "rounds" | "turns" | "until_removed" | "concentration";
  value?: number | null;
  timing: "immediate" | "start_of_turn" | "end_of_turn";
}

export interface EffectStackingSpecContract {
  mode: "replace" | "stack" | "refresh_duration" | "highest_only";
  max_stacks?: number | null;
}

export interface EffectModifierSpecContract {
  operation: "set" | "bonus" | "multiply";
  stat_key: string;
  value: number | string;
}

export interface EffectPeriodicSpecContract {
  trigger: "start_of_turn" | "end_of_turn";
  operation: "apply_damage" | "apply_heal" | "apply_condition" | "remove_condition";
  payload: Record<string, unknown>;
}

export interface EffectRemovalTriggerSpecContract {
  trigger: "on_save_success" | "on_damage_taken" | "on_turn_end" | "dispel";
}

export interface EffectDefinitionContract {
  effect_id: string;
  name: string;
  family: string;
  duration: EffectDurationSpecContract;
  stacking: EffectStackingSpecContract;
  tags: string[];
  modifiers: EffectModifierSpecContract[];
  grants_conditions: string[];
  periodic: EffectPeriodicSpecContract[];
  removal_triggers: EffectRemovalTriggerSpecContract[];
  metadata: Record<string, unknown>;
}

export interface EffectInstanceContract {
  instance_id: string;
  effect_id: string;
  source_actor_id?: string | null;
  target_actor_id: string;
  applied_at_round: number;
  remaining_duration?: number | null;
  concentration_owner_actor_id?: string | null;
  stack_count: number;
  snapshot_payload: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface ContentPackContract {
  pack_id: string;
  system: string;
  version: string;
  actions: ActionDefinitionContract[];
  abilities: AbilityBindingContract[];
  effects: EffectDefinitionContract[];
  dependencies: string[];
  migration_notes: string;
}
