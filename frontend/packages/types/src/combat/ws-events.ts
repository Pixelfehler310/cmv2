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
}

export interface ErrorPayload {
  message: string;
  code: string;
}

export interface ActionAuthorizedPayload {
  actor_id: string;
  action_type: string;
  action_name: string;
}

export interface ActionDeniedPayload {
  actor_id: string;
  action_type: string;
  reason_code: string;
  message: string;
}

export type StateSyncEvent = WsEnvelope<"state_sync", EncounterStateWire>;
export type ActorMovedEvent = WsEnvelope<"actor_moved", ActorMovedPayload>;
export type ActorAddedEvent = WsEnvelope<"actor_added", ActorAddedPayload>;
export type ActorRemovedEvent = WsEnvelope<"actor_removed", ActorRemovedPayload>;
export type TurnAdvancedEvent = WsEnvelope<"turn_advanced", TurnAdvancedPayload>;
export type ActorDamagedEvent = WsEnvelope<"actor_damaged", HpChangedPayload>;
export type ActorHealedEvent = WsEnvelope<"actor_healed", HpChangedPayload>;
export type ActorDiedEvent = WsEnvelope<"actor_died", ActorDiedPayload>;
export type ErrorEvent = WsEnvelope<"error", ErrorPayload>;
export type ActionAuthorizedEvent = WsEnvelope<"action_authorized", ActionAuthorizedPayload>;
export type ActionDeniedEvent = WsEnvelope<"action_denied", ActionDeniedPayload>;

export type KnownWsOutboundEnvelope =
  | StateSyncEvent
  | ActorMovedEvent
  | ActorAddedEvent
  | ActorRemovedEvent
  | TurnAdvancedEvent
  | ActorDamagedEvent
  | ActorHealedEvent
  | ActorDiedEvent
  | ErrorEvent
  | ActionAuthorizedEvent
  | ActionDeniedEvent;

export type WsOutboundEnvelope = KnownWsOutboundEnvelope | WsEnvelope<string, Record<string, unknown>>;

export const KNOWN_WS_OUTBOUND_TYPES = [
  "state_sync",
  "actor_moved",
  "actor_added",
  "actor_removed",
  "turn_advanced",
  "actor_damaged",
  "actor_healed",
  "actor_died",
  "error",
  "action_authorized",
  "action_denied",
] as const;

export type KnownWsOutboundType = (typeof KNOWN_WS_OUTBOUND_TYPES)[number];
