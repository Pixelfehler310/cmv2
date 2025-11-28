import { UserProfile, IAuthService } from '@rpg/bridge';

export class AuthService implements IAuthService {
  private user: UserProfile | null = null;
  private token: string | null = null;
  private readonly STORAGE_KEY = 'mythic_auth_token';

  constructor() {
    this.token = localStorage.getItem(this.STORAGE_KEY);
    if (this.token) {
      this.getUser();
    }
  }

  async login(username: string, password?: string): Promise<boolean> {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ 
          username, 
          password: password || 'password' 
        })
      });
      
      if (!res.ok) return false;
      
      const data = await res.json();
      this.setToken(data.access_token);
      return true;
    } catch (e) {
      console.error('Login failed', e);
      return false;
    }
  }

  async register(username: string, password: string): Promise<boolean> {
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      if (!res.ok) return false;
      return true;
    } catch (e) {
      console.error('Registration failed', e);
      return false;
    }
  }

  async devLogin(username: string): Promise<boolean> {
    console.log('AuthService.devLogin called with:', username);
    this.setToken('dev-token');
    this.user = {
      id: 'dev-user',
      username: username,
      roles: ['admin']
    };
    return true;
  }

  async logout(): Promise<void> {
    this.user = null;
    this.token = null;
    localStorage.removeItem(this.STORAGE_KEY);
  }

  async getUser(): Promise<UserProfile | null> {
    if (this.user) return this.user;
    if (!this.token) return null;

    try {
      const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      
      if (res.ok) {
        this.user = await res.json();
        return this.user;
      } else {
        // Token invalid or expired
        this.logout();
      }
    } catch (e) {
      console.error('Failed to fetch user', e);
    }
    return null;
  }

  getToken() {
    return this.token;
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem(this.STORAGE_KEY, token);
    this.getUser();
  }
}
