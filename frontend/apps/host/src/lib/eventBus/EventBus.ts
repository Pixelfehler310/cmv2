type EventHandler<T = any> = (data: T) => void;

class EventBus {
  private handlers: Map<string, Set<EventHandler>> = new Map();

  on<T = any>(event: string, handler: EventHandler<T>): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.off(event, handler);
    };
  }

  off<T = any>(event: string, handler: EventHandler<T>) {
    const handlers = this.handlers.get(event);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.handlers.delete(event);
      }
    }
  }

  emit<T = any>(event: string, data?: T) {
    const handlers = this.handlers.get(event);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in event handler for "${event}":`, error);
        }
      });
    }
  }

  once<T = any>(event: string, handler: EventHandler<T>): () => void {
    const wrappedHandler: EventHandler<T> = (data) => {
      handler(data);
      this.off(event, wrappedHandler);
    };
    return this.on(event, wrappedHandler);
  }

  clear() {
    this.handlers.clear();
  }
}

// Singleton instance
export const eventBus = new EventBus();



