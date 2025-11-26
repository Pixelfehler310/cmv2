import { eventBus } from "../eventBus/EventBus";

export type ActionType = "ATTACK" | "CAST_SPELL" | "USE_ITEM" | "USE_ABILITY" | "USE_FEATURE" | "MOVE" | "END_TURN" | "REST" | "SPAWN_MONSTER" | "UPDATE_HP" | "ROLL_DICE" | string;

export interface ActionPayload {
  [key: string]: any;
}

export interface Action {
  type: ActionType;
  payload: ActionPayload;
}

/**
 * Legacy dispatchAction - now handled by ActionDispatchContext
 * Kept for backward compatibility during migration
 */
export function dispatchAction(type: ActionType, payload: ActionPayload = {}) {
  const action: Action = { type, payload };

  // Emit on event bus for local UI updates
  eventBus.emit("action:dispatched", action);

  console.warn("Using legacy dispatchAction. Use ActionDispatchContext instead.");
}

/**
 * Subscribe to all actions (useful for debugging)
 */
export function onAction(callback: (action: Action) => void) {
  return eventBus.on("action:dispatched", callback);
}
