export interface RequestActionCommandPayload {
  actor_id: string;
  action_type: string;
  action_name: string;
  payload: Record<string, unknown>;
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

export interface CommandEnvelope<TType extends string, TPayload> {
  type: TType;
  payload: TPayload;
  request_id?: string;
}

export type RequestActionCommand = CommandEnvelope<"request_action", RequestActionCommandPayload>;
export type LegacyActionCommand = CommandEnvelope<"action", ActionCommandPayload>;
export type MoveTokenCommand = CommandEnvelope<"move_token", MoveTokenCommandPayload>;
export type EndTurnCommand = CommandEnvelope<"end_turn", EndTurnCommandPayload>;
export type ApplyDamageCommand = CommandEnvelope<"apply_damage", ApplyDamageCommandPayload>;
export type ApplyHealingCommand = CommandEnvelope<"apply_healing", ApplyHealingCommandPayload>;
export type RemoveActorCommand = CommandEnvelope<"remove_actor", RemoveActorCommandPayload>;

export type KnownWsInboundEnvelope = RequestActionCommand | LegacyActionCommand | MoveTokenCommand | EndTurnCommand | ApplyDamageCommand | ApplyHealingCommand | RemoveActorCommand;

export type WsInboundEnvelope = KnownWsInboundEnvelope | CommandEnvelope<string, Record<string, unknown>>;
