import React, { useState, useEffect } from 'react';
import { ChatLog, DiceRoller, type ChatMessage, type DiceRollResult } from '@rpg/ui';
import { Card, CardContent, CardHeader, CardTitle } from '@rpg/ui';
import { eventBus } from '../lib/eventBus';
import { dispatchAction } from '../lib/actions';

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  useEffect(() => {
    // Subscribe to dice roll events
    const unsubscribeDice = eventBus.on('dice:roll', (result: DiceRollResult) => {
      addMessage({
        id: Date.now().toString(),
        timestamp: new Date(),
        type: 'dice',
        content: `Rolled ${result.expression}: ${result.total}`,
        metadata: result,
      });
    });

    // Subscribe to action events
    const unsubscribeAction = eventBus.on('action:dispatched', (action: any) => {
      addMessage({
        id: Date.now().toString(),
        timestamp: new Date(),
        type: 'action',
        content: `Action: ${action.type}`,
        metadata: action.payload,
      });
    });

    // Subscribe to WebSocket events
    const unsubscribeWS = eventBus.on('ws:*', (data: any) => {
      addMessage({
        id: Date.now().toString(),
        timestamp: new Date(),
        type: 'system',
        content: 'Game state updated',
        metadata: data,
      });
    });

    return () => {
      unsubscribeDice();
      unsubscribeAction();
      unsubscribeWS();
    };
  }, []);

  const addMessage = (message: ChatMessage) => {
    setMessages((prev) => [...prev, message]);
  };

  const handleDiceRoll = (expression: string, result: DiceRollResult) => {
    // Emit to event bus
    eventBus.emit('dice:roll', result);
    
    // Send to backend via action
    dispatchAction('ROLL_DICE', { expression, result });
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>Chat & Dice</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-4">
        <div className="flex-1 min-h-0">
          <ChatLog messages={messages} />
        </div>
        <div>
          <DiceRoller onRoll={handleDiceRoll} />
        </div>
      </CardContent>
    </Card>
  );
}



