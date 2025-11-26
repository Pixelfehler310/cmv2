import { wsManager } from '../websocket/WebSocketManager';
import { eventBus } from '../eventBus/EventBus';

export type ActionType = 
  | 'ATTACK'
  | 'CAST_SPELL'
  | 'USE_ITEM'
  | 'USE_ABILITY'
  | 'USE_FEATURE'
  | 'MOVE'
  | 'END_TURN'
  | 'REST'
  | string;

export interface ActionPayload {
  [key: string]: any;
}

export interface Action {
  type: ActionType;
  payload: ActionPayload;
}

/**
 * Dispatches an action to the backend via WebSocket.
 * This is the primary way for MFEs to send commands to the backend.
 */
export function dispatchAction(type: ActionType, payload: ActionPayload = {}) {
  const action: Action = { type, payload };
  
  // Send via WebSocket if connected
  if (wsManager.isConnected()) {
    wsManager.send('ACTION', action);
  } else {
    console.warn('WebSocket not connected. Action queued:', action);
    // TODO: Queue actions for when WebSocket reconnects
  }

  // Also emit on event bus for local UI updates
  eventBus.emit('action:dispatched', action);
}

/**
 * Subscribe to action results from the backend
 */
export function onActionResult(callback: (result: any) => void) {
  return wsManager.on('ACTION_RESULT', (message) => {
    callback(message.payload);
  });
}

/**
 * Subscribe to all actions (useful for debugging)
 */
export function onAction(callback: (action: Action) => void) {
  return eventBus.on('action:dispatched', callback);
}

