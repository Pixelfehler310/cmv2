import { UserProfile, IAuthService } from '@rpg/bridge';
import { logger } from './logger';

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
    logger.info(`AuthService.login called for user: ${username}`);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ 
          username, 
          password: password || 'password' 
        })
      });
      
      if (!res.ok) {
        logger.warn(`Login failed with status: ${res.status}`);
        return false;
      }
      
      const data = await res.json();
      this.setToken(data.access_token);
      logger.info('Login successful');
      return true;
    } catch (e) {
      logger.error('Login failed with exception', e);
      return false;
    }
  }

  async register(username: string, password: string): Promise<boolean> {
    logger.info(`AuthService.register called for user: ${username}`);
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      if (!res.ok) {
        logger.warn(`Registration failed with status: ${res.status}`);
        return false;
      }
      logger.info('Registration successful');
      return true;
    } catch (e) {
      logger.error('Registration failed with exception', e);
      return false;
    }
  }

  async devLogin(username: string, roles: string[] = ['admin']): Promise<boolean> {
    logger.info(`AuthService.devLogin called with: ${username}, roles: ${roles.join(', ')}`);
    this.setToken('dev-token');
    this.user = {
      id: 'dev-user',
      username: username,
      roles: roles
    };
    return true;
  }

  async logout(): Promise<void> {
    logger.info('AuthService.logout called');
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
        logger.warn('Token invalid or expired, logging out');
        this.logout();
      }
    } catch (e) {
      logger.error('Failed to fetch user', e);
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
