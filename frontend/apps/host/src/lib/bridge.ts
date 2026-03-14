import { IHostBridge, IEventBus, IActionDispatcher, IAuthService, IConnectionState, ActionResult } from "@rpg/bridge";
import { WsClient } from "@rpg/bridge";
import { QueryClient } from "@tanstack/react-query";

class EventEmitter implements IEventBus {
  private listeners: Map<string, Set<(payload: any) => void>> = new Map();

  emit(event: string, payload: any): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.forEach((h) => h(payload));
    }
  }

  on(event: string, handler: (payload: any) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler);
    return () => {
      this.listeners.get(event)?.delete(handler);
    };
  }
}

export class ReactHostBridge implements IHostBridge {
  public events: IEventBus;
  public actions: IActionDispatcher;
  public auth: IAuthService;

  constructor(
    private ws: WsClient,
    private queryClient: QueryClient,
    authService: IAuthService,
  ) {
    this.events = new EventEmitter();
    this.auth = authService;

    this.ws.onMessage((data) => {
      this.events.emit("ws:recv", data);
    });

    this.actions = {
      dispatch: async (type: string, payload: any): Promise<ActionResult> => {
        try {
          this.events.emit("ws:send", { type, payload });
          // Optimistic updates could go here
          await this.ws.sendAction(type, payload);
          this.events.emit("ws:send_result", { success: true, type, payload });
          return { success: true };
        } catch (e: any) {
          this.events.emit("ws:error", { type, payload, error: e?.message ?? "Unknown websocket error" });
          return { success: false, error: e.message };
        }
      },
    };
  }

  get connection(): IConnectionState {
    return this.ws.state;
  }

  toast(message: string, type: "info" | "error" | "success" | "warning") {
    console.log(`[TOAST] ${type}: ${message}`);
    // In a real app, this would trigger a UI toast component
  }

  openModal(id: string, props?: any) {
    console.log(`[MODAL] Open ${id}`, props);
    // In a real app, this would update global modal state
  }
}
