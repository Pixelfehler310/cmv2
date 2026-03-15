import { IConnectionState } from "./index";
import type { WsInboundEnvelope, WsOutboundEnvelope } from "@rpg/types";

type MessageHandler = (data: WsOutboundEnvelope) => void;

export class WsClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval = 1000;
  private maxReconnectInterval = 30000;
  private handlers: Set<MessageHandler> = new Set();
  private isIntentionalClose = false;

  public state: IConnectionState = {
    isConnected: false,
    latency: 0,
  };

  constructor(baseUrl: string = "ws://localhost:8000") {
    this.url = baseUrl;
  }

  connect(campaignId: string, token: string, role: "player" | "dm" | "spectator" = "player") {
    this.isIntentionalClose = false;
    // Connects to the main ws_dispatcher.py route: /ws/{campaign_id}
    const wsUrl = `${this.url}/ws/${campaignId}?token=${token}&role=${role}`;

    console.info(`[WsClient] Connecting to WebSocket: ${wsUrl}`);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.info("[WsClient] WS Connected");
      this.state.isConnected = true;
      this.reconnectInterval = 1000; // Reset backoff
    };

    this.ws.onclose = () => {
      console.info("[WsClient] WS Disconnected");
      this.state.isConnected = false;
      if (!this.isIntentionalClose) {
        this.scheduleReconnect(campaignId, token, role);
      }
    };

    this.ws.onerror = (err) => {
      console.error("[WsClient] WS Error", err);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsOutboundEnvelope;
        this.handlers.forEach((handler) => handler(data));
      } catch (e) {
        console.error("[WsClient] Failed to parse WS message", e);
      }
    };
  }

  disconnect() {
    this.isIntentionalClose = true;
    this.ws?.close();
    this.ws = null;
  }

  sendAction(command: WsInboundEnvelope): Promise<{ success: true }>;
  sendAction(type: string, payload: Record<string, unknown>): Promise<{ success: true }>;
  sendAction(typeOrCommand: string | WsInboundEnvelope, payload?: Record<string, unknown>) {
    const envelope: WsInboundEnvelope = typeof typeOrCommand === "string" ? { type: typeOrCommand, payload: payload ?? {} } : typeOrCommand;

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(envelope));
      return Promise.resolve({ success: true });
    } else {
      console.warn("[WsClient] Attempted to send action while WebSocket is not connected");
      return Promise.reject(new Error("WebSocket not connected"));
    }
  }

  onMessage(handler: MessageHandler) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  private scheduleReconnect(campaignId: string, token: string, role: "player" | "dm" | "spectator") {
    setTimeout(() => {
      console.info("[WsClient] Reconnecting...");
      this.connect(campaignId, token, role);
      this.reconnectInterval = Math.min(this.reconnectInterval * 2, this.maxReconnectInterval);
    }, this.reconnectInterval);
  }
}
