import { useEffect } from 'react';
import { wsManager } from '../lib/websocket';
import { eventBus } from '../lib/eventBus';
import { useGameStore } from '../stores/gameStore';
import type { Character, Monster } from '@rpg/types';

export function useWebSocketEvents() {
  const {
    updateCharacter,
    updateMonster,
    setInitiativeOrder,
    setCurrentTurn,
  } = useGameStore();

  useEffect(() => {
    // Subscribe to WebSocket events
    const unsubscribeActionResult = wsManager.on('ACTION_RESULT', (message) => {
      const { type, payload } = message.payload;
      
      switch (type) {
        case 'CHARACTER_UPDATE':
          updateCharacter(payload.characterId, payload.updates);
          break;
        case 'MONSTER_UPDATE':
          updateMonster(payload.monsterId, payload.updates);
          break;
        case 'INITIATIVE_UPDATE':
          setInitiativeOrder(payload.order);
          break;
        case 'TURN_UPDATE':
          setCurrentTurn(payload.turn);
          break;
        default:
          // Emit to event bus for other handlers
          eventBus.emit(`ws:${type}`, payload);
      }
    });

    const unsubscribeStateUpdate = wsManager.on('STATE_UPDATE', (message) => {
      // Handle full state updates from backend
      eventBus.emit('state:update', message.payload);
    });

    return () => {
      unsubscribeActionResult();
      unsubscribeStateUpdate();
    };
  }, [updateCharacter, updateMonster, setInitiativeOrder, setCurrentTurn]);
}

