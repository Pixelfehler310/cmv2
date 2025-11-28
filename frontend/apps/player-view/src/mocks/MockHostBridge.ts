import { IHostBridge, IEventBus, IActionDispatcher, ActionResult, IAuthService, IConnectionState, UserProfile } from '@rpg/bridge';
import { characterFull } from './character_full';
import { campaignState } from './campaign_state';
import { chatHistory } from './chat_history';
import { campaigns } from './campaigns';

class MockEventBus implements IEventBus {
  private listeners: { [key: string]: ((payload: any) => void)[] } = {};

  emit(event: string, payload: any): void {
    if (this.listeners[event]) {
      this.listeners[event].forEach(handler => handler(payload));
    }
  }

  on(event: string, handler: (payload: any) => void): () => void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(handler);
    return () => {
      this.listeners[event] = this.listeners[event].filter(h => h !== handler);
    };
  }
}

class MockActionDispatcher implements IActionDispatcher {
  async dispatch(actionType: string, payload: any): Promise<ActionResult> {
    console.log(`[MockBridge] Dispatching action: ${actionType}`, payload);
    
    // Simulate latency
    await new Promise(resolve => setTimeout(resolve, 200));

    switch (actionType) {
      case 'ROLL_DICE':
        return { success: true, data: { total: 15, breakdown: '1d20+5 = [10]+5' } };
      case 'MOVE_TOKEN':
        return { success: true };
      default:
        return { success: true };
    }
  }
}

class MockAuthService implements IAuthService {
  private user: UserProfile | null = null;

  constructor() {
    // Check local storage for dev user to persist across reloads
    const stored = localStorage.getItem('mythic_dev_user');
    if (stored) {
        const { username, roles } = JSON.parse(stored);
        this.user = {
            id: 'dev-user',
            username,
            roles,
            avatarUrl: 'https://github.com/shadcn.png'
        };
    } else {
        this.user = null;
    }
  }

  async getUser(): Promise<UserProfile | null> {
    return this.user;
  }

  async login(username: string): Promise<boolean> {
    this.user = {
        id: 'user-1',
        username,
        avatarUrl: 'https://github.com/shadcn.png'
    };
    return true;
  }

  async devLogin(username: string, roles: string[] = ['user']): Promise<boolean> {
    console.log(`[MockAuth] devLogin: ${username}, roles: ${roles}`);
    this.user = {
        id: 'dev-user',
        username,
        avatarUrl: 'https://github.com/shadcn.png',
        is_superuser: roles.includes('admin')
    };
    localStorage.setItem('mythic_dev_user', JSON.stringify({ username, roles }));
    return true;
  }

  async logout(): Promise<void> {
    console.log('[MockAuth] Logout');
    this.user = null;
    localStorage.removeItem('mythic_dev_user');
    // todo navigate to login
  }
}

export class MockHostBridge implements IHostBridge {
  events: IEventBus;
  actions: IActionDispatcher;
  auth: IAuthService;
  connection: IConnectionState;

  constructor() {
    this.events = new MockEventBus();
    this.actions = new MockActionDispatcher();
    this.auth = new MockAuthService();
    this.connection = {
      isConnected: true,
      latency: 15
    };

    // Simulate incoming events
    this.startSimulation();
  }

  toast(message: string, type: 'info' | 'error' | 'success' | 'warning') {
    console.log(`[MockBridge] Toast (${type}): ${message}`);
  }

  openModal(id: string, props?: any) {
    console.log(`[MockBridge] Open Modal: ${id}`, props);
  }

  private startSimulation() {
    // Emit initial state after a short delay
    setTimeout(() => {
      this.events.emit('STATE_UPDATE', {
        character: characterFull,
        campaign: campaignState,
        chat: chatHistory
      });
    }, 500);

    // Simulate random chat messages
    setInterval(() => {
        if (Math.random() > 0.8) {
            this.events.emit('CHAT_MESSAGE', {
                id: `msg-${Date.now()}`,
                sender: 'System',
                content: 'Something happened in the dungeon...',
                timestamp: new Date().toLocaleTimeString(),
                type: 'system'
            });
        }
    }, 10000);
  }
  
  // Helper to access mock data directly if needed
  getMockData() {
      return {
          character: characterFull,
          campaign: campaignState,
          chat: chatHistory,
          campaigns: campaigns
      };
  }
}
