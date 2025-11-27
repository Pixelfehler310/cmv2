import React, { createContext, useContext, ReactNode } from 'react';
import { eventBus } from '../lib/eventBus/EventBus';

interface EventBusContextType {
  emit: (event: string, data?: any) => void;
  on: (event: string, handler: (data?: any) => void) => () => void;
  off: (event: string, handler: (data?: any) => void) => void;
}

const EventBusContext = createContext<EventBusContextType | undefined>(undefined);

export function EventBusProvider({ children }: { children: ReactNode }) {
  const emit = (event: string, data?: any) => {
    eventBus.emit(event, data);
  };

  const on = (event: string, handler: (data?: any) => void) => {
    return eventBus.on(event, handler);
  };

  const off = (event: string, handler: (data?: any) => void) => {
    eventBus.off(event, handler);
  };

  return (
    <EventBusContext.Provider value={{ emit, on, off }}>
      {children}
    </EventBusContext.Provider>
  );
}

export function useEventBus() {
  const context = useContext(EventBusContext);
  if (context === undefined) {
    throw new Error('useEventBus must be used within an EventBusProvider');
  }
  return context;
}



