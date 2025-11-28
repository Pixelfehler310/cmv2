export interface IHostBridge {
  // 1. Communication
  events: IEventBus;
  actions: IActionDispatcher;

  // 2. State Access (Read-Only)
  auth: IAuthService;
  connection: IConnectionState;

  // 3. UI Utilities
  toast: (message: string, type: 'info' | 'error' | 'success' | 'warning') => void;
  openModal: (id: string, props?: any) => void;
}

export interface IEventBus {
  emit(event: string, payload: any): void;
  on(event: string, handler: (payload: any) => void): () => void; // Returns unsubscribe function
}

export interface IActionDispatcher {
  dispatch(actionType: string, payload: any): Promise<ActionResult>;
}

export interface ActionResult {
  success: boolean;
  error?: string;
  data?: any;
}

export interface IAuthService {
  getUser(): Promise<UserProfile | null>;
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
  roles: string[];
}
