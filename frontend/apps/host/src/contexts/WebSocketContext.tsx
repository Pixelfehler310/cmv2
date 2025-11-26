import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { wsManager } from '../lib/websocket/WebSocketManager';

type WebSocketState = 'disconnected' | 'connecting' | 'connected' | 'error';

interface WebSocketContextType {
  connectionState: WebSocketState;
  send: (type: string, payload: any) => void;
  subscribe: (event: string, handler: (message: any) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export function WebSocketProvider({ children, token }: { children: ReactNode; token: string | null }) {
  const [connectionState, setConnectionState] = useState<WebSocketState>('disconnected');

  useEffect(() => {
    if (!token) {
      setConnectionState('disconnected');
      return;
    }

    setConnectionState('connecting');
    wsManager
      .connect(token)
      .then(() => {
        setConnectionState('connected');
      })
      .catch(() => {
        setConnectionState('error');
      });

    // Subscribe to connection state changes
    const unsubscribeOpen = wsManager.on('open', () => {
      setConnectionState('connected');
    });

    const unsubscribeClose = wsManager.on('close', () => {
      setConnectionState('disconnected');
    });

    const unsubscribeError = wsManager.on('error', () => {
      setConnectionState('error');
    });

    return () => {
      unsubscribeOpen();
      unsubscribeClose();
      unsubscribeError();
      wsManager.disconnect();
    };
  }, [token]);

  const send = (type: string, payload: any) => {
    wsManager.send(type, payload);
  };

  const subscribe = (event: string, handler: (message: any) => void) => {
    return wsManager.on(event, (message) => {
      handler(message.payload);
    });
  };

  return (
    <WebSocketContext.Provider value={{ connectionState, send, subscribe }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}

