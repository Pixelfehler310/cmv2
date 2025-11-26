import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useWebSocket } from './WebSocketContext';
import { useEventBus } from './EventBusContext';

export interface Action {
  type: string;
  payload: Record<string, any>;
  timestamp: number;
  id: string;
}

export interface ActionResult {
  success: boolean;
  data?: any;
  error?: string;
  actionId: string;
}

interface ActionDispatchContextType {
  dispatchAction: (type: string, payload?: Record<string, any>) => Promise<ActionResult>;
  actionQueue: Action[];
  lastActionResult: ActionResult | null;
}

const ActionDispatchContext = createContext<ActionDispatchContextType | undefined>(undefined);

export function ActionDispatchProvider({ children }: { children: ReactNode }) {
  const [actionQueue, setActionQueue] = useState<Action[]>([]);
  const [lastActionResult, setLastActionResult] = useState<ActionResult | null>(null);
  const { connectionState, send } = useWebSocket();
  const { on } = useEventBus();

  // Listen for action results
  useEffect(() => {
    const unsubscribe = on('action:result', (result: ActionResult) => {
      setLastActionResult(result);
    });

    return unsubscribe;
  }, [on]);

  // Process queued actions when connection is restored
  useEffect(() => {
    if (connectionState === 'connected' && actionQueue.length > 0) {
      actionQueue.forEach((action) => {
        send('ACTION', action);
      });
      setActionQueue([]);
    }
  }, [connectionState, actionQueue, send]);

  const dispatchAction = async (
    type: string,
    payload: Record<string, any> = {}
  ): Promise<ActionResult> => {
    const action: Action = {
      type,
      payload,
      timestamp: Date.now(),
      id: `${type}-${Date.now()}-${Math.random()}`,
    };

    // If WebSocket is connected, send immediately
    if (connectionState === 'connected') {
      send('ACTION', action);
      
      // Wait for result via event bus
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          const timeoutResult: ActionResult = {
            success: false,
            error: 'Action timeout',
            actionId: action.id,
          };
          setLastActionResult(timeoutResult);
          resolve(timeoutResult);
        }, 5000);

        const unsubscribe = on('action:result', (result: ActionResult) => {
          if (result.actionId === action.id) {
            clearTimeout(timeout);
            setLastActionResult(result);
            unsubscribe();
            resolve(result);
          }
        });
      });
    } else {
      // Queue action for when connection is restored
      setActionQueue((prev) => [...prev, action]);
      return {
        success: false,
        error: 'WebSocket not connected. Action queued.',
        actionId: action.id,
      };
    }
  };

  return (
    <ActionDispatchContext.Provider value={{ dispatchAction, actionQueue, lastActionResult }}>
      {children}
    </ActionDispatchContext.Provider>
  );
}

export function useActionDispatch() {
  const context = useContext(ActionDispatchContext);
  if (context === undefined) {
    throw new Error('useActionDispatch must be used within an ActionDispatchProvider');
  }
  return context;
}
