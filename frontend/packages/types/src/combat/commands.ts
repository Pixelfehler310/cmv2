export interface RequestActionCommandPayload {
  actor_id: string;
  action_type: string;
  action_name: string;
  payload: Record<string, unknown>;
  acting_as_user_id?: string;
}

export interface ActionCommandPayload {
  actor_id: string;
  action_name: string;
  action_type: string;
  target_ids?: string[];
}

export interface MoveTokenCommandPayload {
  actor_id: string;
  path: Array<{ x: number; y: number }>;
  acting_as_user_id?: string;
}

export interface RequestMovePreviewCommandPayload {
  actor_id: string;
  acting_as_user_id?: string;
}

export interface EndTurnCommandPayload {
  actor_id: string;
}

export interface ApplyDamageCommandPayload {
  actor_id: string;
  amount: number;
  damage_type: string;
}

export interface ApplyHealingCommandPayload {
  actor_id: string;
  amount: number;
}

export interface RemoveActorCommandPayload {
  actor_id: string;
}

export interface AddActorCommandPayload {
  definition_slug: string;
  name?: string;
  position?: { x: number; y: number };
  owner_user_id?: string;
}

export interface ApplyConditionCommandPayload {
  actor_id: string;
  condition: string;
  source_id?: string;
}

export interface RemoveConditionCommandPayload {
  actor_id: string;
  condition: string;
}

export interface RollDiceCommandPayload {
  expression: string;
  purpose?: string;
}

export interface ChatMessageCommandPayload {
  message: string;
}

export interface EmptyCommandPayload {
  [key: string]: never;
}

export interface CommandEnvelope<TType extends string, TPayload> {
  type: TType;
  payload: TPayload;
  request_id?: string;
}

export interface CommandLikeEnvelope<TType extends string, TPayload> extends CommandEnvelope<TType, TPayload> {
  request_id: string;
}

export type RequestActionCommand = CommandLikeEnvelope<"request_action", RequestActionCommandPayload>;
export type LegacyActionCommand = CommandLikeEnvelope<"action", ActionCommandPayload>;
export type MoveTokenCommand = CommandLikeEnvelope<"move_token", MoveTokenCommandPayload>;
export type RequestMovePreviewCommand = CommandLikeEnvelope<"request_move_preview", RequestMovePreviewCommandPayload>;
export type EndTurnCommand = CommandLikeEnvelope<"end_turn", EndTurnCommandPayload>;
export type ApplyDamageCommand = CommandLikeEnvelope<"apply_damage", ApplyDamageCommandPayload>;
export type ApplyHealingCommand = CommandLikeEnvelope<"apply_healing", ApplyHealingCommandPayload>;
export type AddActorCommand = CommandLikeEnvelope<"add_actor", AddActorCommandPayload>;
export type RemoveActorCommand = CommandLikeEnvelope<"remove_actor", RemoveActorCommandPayload>;
export type StartCombatCommand = CommandLikeEnvelope<"start_combat", EmptyCommandPayload>;
export type EndCombatCommand = CommandLikeEnvelope<"end_combat", EmptyCommandPayload>;
export type ApplyConditionCommand = CommandLikeEnvelope<"apply_condition", ApplyConditionCommandPayload>;
export type RemoveConditionCommand = CommandLikeEnvelope<"remove_condition", RemoveConditionCommandPayload>;

export type PingCommand = CommandEnvelope<"ping", EmptyCommandPayload>;
export type RequestSyncCommand = CommandEnvelope<"request_sync", EmptyCommandPayload>;
export type RollDiceCommand = CommandEnvelope<"roll_dice", RollDiceCommandPayload>;
export type ChatMessageCommand = CommandEnvelope<"chat_message", ChatMessageCommandPayload>;

export type CommandLikeWsInboundEnvelope =
  | RequestActionCommand
  | LegacyActionCommand
  | RequestMovePreviewCommand
  | MoveTokenCommand
  | EndTurnCommand
  | ApplyDamageCommand
  | ApplyHealingCommand
  | AddActorCommand
  | RemoveActorCommand
  | StartCombatCommand
  | EndCombatCommand
  | ApplyConditionCommand
  | RemoveConditionCommand;

export type UtilityWsInboundEnvelope = PingCommand | RequestSyncCommand | RollDiceCommand | ChatMessageCommand;

export type KnownWsInboundEnvelope = CommandLikeWsInboundEnvelope | UtilityWsInboundEnvelope;

export type WsInboundEnvelope = KnownWsInboundEnvelope | CommandEnvelope<string, Record<string, unknown>>;

export const COMMAND_LIKE_WS_INBOUND_TYPES = [
  "action",
  "request_action",
  "request_move_preview",
  "move_token",
  "add_actor",
  "remove_actor",
  "start_combat",
  "end_combat",
  "end_turn",
  "apply_damage",
  "apply_healing",
  "apply_condition",
  "remove_condition",
] as const;

export const UTILITY_WS_INBOUND_TYPES = ["ping", "request_sync", "roll_dice", "chat_message"] as const;

export type CommandLikeWsInboundType = (typeof COMMAND_LIKE_WS_INBOUND_TYPES)[number];
export type UtilityWsInboundType = (typeof UTILITY_WS_INBOUND_TYPES)[number];
