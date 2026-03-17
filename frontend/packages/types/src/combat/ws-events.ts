import type { EncounterStateWire, ActorInstanceWire, MapTokenWire } from "./encounter";

export interface WsEnvelope<TType extends string, TPayload> {
  type: TType;
  payload: TPayload;
  request_id?: string;
}

export interface ActorMovedPayload {
  actor_id: string;
  path?: Array<{ x: number; y: number }>;
  position?: { x: number; y: number };
  turn_budget?: TurnBudgetSnapshotPayload;
}

export interface MovementPreviewPayload {
  actor_id: string;
  origin: { x: number; y: number };
  movement_remaining: number;
  reachable: Array<{ x: number; y: number }>;
}

export interface ExecutableActionPayload {
  action_id: string;
  name?: string;
  label: string;
  family: "attack" | "save" | "healing" | "utility" | string;
  action_type_cost: "action" | "bonus_action" | "reaction" | "move" | string;
  is_available: boolean;
  unavailable_reason?: string | null;
  targeting_mode: "single_target" | "aoe" | "self" | string;
  range?: number | null;
  save_context?: Record<string, unknown> | null;
  attack_context?: Record<string, unknown> | null;
  resource_costs?: Array<Record<string, unknown>>;
  effect_intents?: Array<Record<string, unknown>>;
  tags?: string[];
  source_ref?: string;
  content_version?: string;
  enabled?: boolean;
}

export interface ExecutableActionsSnapshotPayload {
  actor_id: string;
  actions: ExecutableActionPayload[];
  turn_budget?: TurnBudgetSnapshotPayload;
}

export interface AttackPreviewPayload {
  actor_id: string;
  action_id: string;
  origin: { x: number; y: number };
  eligible_target_ids: string[];
  eligible_cells?: Array<{ x: number; y: number }>;
  template_projection?: AttackTemplateProjection;
}

export interface AttackTemplateProjection {
  shape: "line" | "cone" | "sphere" | "cube" | "cylinder" | string;
  size: number;
  origin: { x: number; y: number };
  direction?: { x: number; y: number };
  affected_cells: Array<{ x: number; y: number }>;
}

export interface ActorAddedPayload {
  actor: ActorInstanceWire;
  token?: MapTokenWire;
}

export interface ActorRemovedPayload {
  actor_id: string;
}

export interface HpChangedPayload {
  actor_id: string;
  amount?: number;
  new_hp: number;
}

export interface ActorDiedPayload {
  actor_id: string;
}

export interface TurnAdvancedPayload {
  active_actor_id: string;
  round: number;
  turn_budget?: TurnBudgetSnapshotPayload;
}

export interface ErrorPayload {
  message: string;
  code: string;
}

export interface ActionAuthorizedPayload {
  actor_id: string;
  action_type: string;
  action_name: string;
  family?: "attack" | "save" | "healing" | "utility" | string;
  turn_budget?: TurnBudgetSnapshotPayload;
}

export interface ActionDeniedPayload {
  event_type?: string;
  actor_id: string;
  action_type: string;
  reason_code: string;
  message: string;
}

export interface CommandDeniedPayload {
  event_type: string;
  actor_id?: string;
  action_type?: string;
  reason_code: string;
  message: string;
}

export interface CombatStartedPayload {
  initiative_order: Array<{ actor_id: string; name: string }>;
  turn_budget?: TurnBudgetSnapshotPayload;
}

export interface CombatEndedPayload {
  [key: string]: never;
}

export interface ConditionAddedPayload {
  actor_id: string;
  condition: string;
  source?: string;
}

export interface ConditionRemovedPayload {
  actor_id: string;
  condition: string;
}

export interface AttackResultPayload {
  attacker_id: string;
  target_id: string;
  action_name: string;
  hit: boolean;
  is_critical: boolean;
  roll_used: number;
  roll_count: number;
  damage: number;
  damage_type: string;
}

export interface SaveResultTargetPayload {
  target_id: string;
  passed: boolean;
  save_roll: number;
  damage: number;
}

export interface SaveResultPayload {
  caster_id: string;
  action_name: string;
  save_ability: string;
  save_dc: number;
  results: SaveResultTargetPayload[];
}

export interface EffectAppliedPayload {
  actor_id: string;
  target_id: string;
  action_name: string;
  effect_type: "healing" | "utility" | "condition_added" | "condition_removed" | string;
  amount?: number;
  condition?: string;
}

export interface DiceRolledPayload {
  roller_id: string;
  expression: string;
  result: number;
  purpose?: string | null;
}

export interface ChatMessagePayload {
  sender_id: string;
  sender_name: string;
  sender_role: string;
  message: string;
}

export interface PongPayload {
  [key: string]: never;
}

export interface TurnBudgetSnapshotPayload {
  round: number;
  turn_phase: "pre_combat" | "active" | "post_combat" | string;
  active_actor_id: string | null;
  budgets: Record<string, Record<string, unknown>>;
}

export type StateSyncEvent = WsEnvelope<"state_sync", EncounterStateWire>;
export type ActorMovedEvent = WsEnvelope<"actor_moved", ActorMovedPayload>;
export type MovementPreviewEvent = WsEnvelope<"movement_preview", MovementPreviewPayload>;
export type ExecutableActionsSnapshotEvent = WsEnvelope<"executable_actions_snapshot", ExecutableActionsSnapshotPayload>;
export type AttackPreviewEvent = WsEnvelope<"attack_preview", AttackPreviewPayload>;
export type ActorAddedEvent = WsEnvelope<"actor_added", ActorAddedPayload>;
export type ActorRemovedEvent = WsEnvelope<"actor_removed", ActorRemovedPayload>;
export type TurnAdvancedEvent = WsEnvelope<"turn_advanced", TurnAdvancedPayload>;
export type ActorDamagedEvent = WsEnvelope<"actor_damaged", HpChangedPayload>;
export type ActorHealedEvent = WsEnvelope<"actor_healed", HpChangedPayload>;
export type ActorDiedEvent = WsEnvelope<"actor_died", ActorDiedPayload>;
export type ErrorEvent = WsEnvelope<"error", ErrorPayload>;
export type ActionAuthorizedEvent = WsEnvelope<"action_authorized", ActionAuthorizedPayload>;
export type ActionDeniedEvent = WsEnvelope<"action_denied", ActionDeniedPayload>;
export type CommandDeniedEvent = WsEnvelope<"command_denied", CommandDeniedPayload>;
export type CombatStartedEvent = WsEnvelope<"combat_started", CombatStartedPayload>;
export type CombatEndedEvent = WsEnvelope<"combat_ended", CombatEndedPayload>;
export type ConditionAddedEvent = WsEnvelope<"condition_added", ConditionAddedPayload>;
export type ConditionRemovedEvent = WsEnvelope<"condition_removed", ConditionRemovedPayload>;
export type AttackResultEvent = WsEnvelope<"attack_result", AttackResultPayload>;
export type SaveResultEvent = WsEnvelope<"save_result", SaveResultPayload>;
export type EffectAppliedEvent = WsEnvelope<"effect_applied", EffectAppliedPayload>;
export type DiceRolledEvent = WsEnvelope<"dice_rolled", DiceRolledPayload>;
export type ChatMessageEvent = WsEnvelope<"chat_message", ChatMessagePayload>;
export type PongEvent = WsEnvelope<"pong", PongPayload>;

export type KnownWsOutboundEnvelope =
  | StateSyncEvent
  | ActorMovedEvent
  | MovementPreviewEvent
  | ExecutableActionsSnapshotEvent
  | AttackPreviewEvent
  | ActorAddedEvent
  | ActorRemovedEvent
  | TurnAdvancedEvent
  | ActorDamagedEvent
  | ActorHealedEvent
  | ActorDiedEvent
  | ErrorEvent
  | ActionAuthorizedEvent
  | ActionDeniedEvent
  | CommandDeniedEvent
  | CombatStartedEvent
  | CombatEndedEvent
  | ConditionAddedEvent
  | ConditionRemovedEvent
  | AttackResultEvent
  | SaveResultEvent
  | EffectAppliedEvent
  | DiceRolledEvent
  | ChatMessageEvent
  | PongEvent;

export type WsOutboundEnvelope = KnownWsOutboundEnvelope | WsEnvelope<string, Record<string, unknown>>;

export const KNOWN_WS_OUTBOUND_TYPES = [
  "state_sync",
  "actor_moved",
  "movement_preview",
  "executable_actions_snapshot",
  "attack_preview",
  "actor_added",
  "actor_removed",
  "turn_advanced",
  "actor_damaged",
  "actor_healed",
  "actor_died",
  "error",
  "action_authorized",
  "action_denied",
  "command_denied",
  "combat_started",
  "combat_ended",
  "condition_added",
  "condition_removed",
  "attack_result",
  "save_result",
  "effect_applied",
  "dice_rolled",
  "chat_message",
  "pong",
] as const;

export type KnownWsOutboundType = (typeof KNOWN_WS_OUTBOUND_TYPES)[number];
