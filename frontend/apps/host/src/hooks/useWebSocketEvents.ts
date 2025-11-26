import { useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useEventBus } from '../contexts/EventBusContext';

export function useWebSocketEvents() {
  const { subscribe } = useWebSocket();
  const { emit } = useEventBus();

  useEffect(() => {
    // Subscribe to WebSocket events and forward to event bus
    const unsubscribeActionResult = subscribe('ACTION_RESULT', (payload) => {
      emit('action:result', payload);
    });

    const unsubscribeStateUpdate = subscribe('STATE_UPDATE', (payload) => {
      // Handle full state updates from backend
      emit('state:update', payload);
    });

    return () => {
      unsubscribeActionResult();
      unsubscribeStateUpdate();
    };
  }, [subscribe, emit]);
}

