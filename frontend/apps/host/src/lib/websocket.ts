import { IConnectionState } from '@rpg/bridge';
import { logger } from './logger';

type MessageHandler = (data: any) => void;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval = 1000;
  private maxReconnectInterval = 30000;
  private handlers: Set<MessageHandler> = new Set();
  private isIntentionalClose = false;

  public state: IConnectionState = {
    isConnected: false,
    latency: 0
  };

  constructor(baseUrl: string = 'ws://localhost:8000') {
    this.url = baseUrl;
  }

  connect(campaignId: string, token: string) {
    this.isIntentionalClose = false;
    const wsUrl = `${this.url}/campaigns/${campaignId}/ws?token=${token}`;
    
    logger.info(`Connecting to WebSocket: ${wsUrl}`);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      logger.info('WS Connected');
      this.state.isConnected = true;
      this.reconnectInterval = 1000; // Reset backoff
    };

    this.ws.onclose = () => {
      logger.info('WS Disconnected');
      this.state.isConnected = false;
      if (!this.isIntentionalClose) {
        this.scheduleReconnect(campaignId, token);
      }
    };

    this.ws.onerror = (err) => {
      logger.error('WS Error', err);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handlers.forEach(handler => handler(data));
      } catch (e) {
        logger.error('Failed to parse WS message', e);
      }
    };
  }

  disconnect() {
    this.isIntentionalClose = true;
    this.ws?.close();
    this.ws = null;
  }

  sendAction(type: string, payload: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
      return Promise.resolve({ success: true });
    } else {
      logger.warn('Attempted to send action while WebSocket is not connected');
      return Promise.reject(new Error('WebSocket not connected'));
    }
  }

  onMessage(handler: MessageHandler) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  private scheduleReconnect(campaignId: string, token: string) {
    setTimeout(() => {
      logger.info('Reconnecting...');
      this.connect(campaignId, token);
      this.reconnectInterval = Math.min(this.reconnectInterval * 2, this.maxReconnectInterval);
    }, this.reconnectInterval);
  }
}
