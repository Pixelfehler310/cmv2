import type { WsInboundEnvelope, WsOutboundEnvelope } from "@rpg/types";

export interface IHostBridge {
  // 1. Communication
  events: IEventBus;
  actions: IActionDispatcher;

  // 2. State Access (Read-Only)
  auth: IAuthService;
  connection: IConnectionState;

  // 3. UI Utilities
  toast: (message: string, type: "info" | "error" | "success" | "warning") => void;
  openModal: (id: string, props?: any) => void;
}

export interface IEventBus {
  emit(event: string, payload: unknown): void;
  on(event: string, handler: (payload: unknown) => void): () => void; // Returns unsubscribe function
}

export interface IActionDispatcher {
  dispatch(command: WsInboundEnvelope): Promise<ActionResult>;
  dispatch(actionType: string, payload: any): Promise<ActionResult>;
}

export interface ActionResult {
  success: boolean;
  error?: string;
  data?: unknown;
}

export type { WsInboundEnvelope, WsOutboundEnvelope };

export interface IAuthService {
  getUser(): Promise<UserProfile | null>;
  getToken(): string | null;
  login(username: string): Promise<boolean>;
  logout(): Promise<void>;
}

export interface IConnectionState {
  isConnected: boolean;
  latency: number;
}

export interface UserProfile {
  id: string;
  username: string;
  avatarUrl?: string;
  is_superuser?: boolean;
}

export * from "./WsClient";
export * from "./apiClient";
export * from "./requestId";
