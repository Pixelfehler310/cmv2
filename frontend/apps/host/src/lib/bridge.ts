import { IHostBridge, IEventBus, IActionDispatcher, IAuthService, IConnectionState, ActionResult } from "@rpg/bridge";
import { WsClient } from "@rpg/bridge";
import { ensureRequestId } from "@rpg/bridge";
import { QueryClient } from "@tanstack/react-query";
import type { WsInboundEnvelope, WsOutboundEnvelope } from "@rpg/types";

class EventEmitter implements IEventBus {
  private listeners: Map<string, Set<(payload: unknown) => void>> = new Map();

  emit(event: string, payload: unknown): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.forEach((h) => h(payload));
    }
  }

  on(event: string, handler: (payload: unknown) => void): () => void {
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

    this.ws.onMessage((data: WsOutboundEnvelope) => {
      this.events.emit("ws:recv", data);
    });

    this.actions = {
      dispatch: async (commandOrType: WsInboundEnvelope | string, payload?: Record<string, unknown>): Promise<ActionResult> => {
        const rawEnvelope: WsInboundEnvelope = typeof commandOrType === "string" ? { type: commandOrType, payload: payload ?? {} } : commandOrType;
        const envelope = ensureRequestId(rawEnvelope);

        try {
          this.events.emit("ws:send", envelope);
          // Optimistic updates could go here
          await this.ws.sendAction(envelope);
          this.events.emit("ws:send_result", { success: true, ...envelope });
          return { success: true };
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : "Unknown websocket error";
          this.events.emit("ws:error", { ...envelope, error: message });
          return { success: false, error: message };
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
