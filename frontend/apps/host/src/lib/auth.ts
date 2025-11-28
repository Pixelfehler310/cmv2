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

  async devLogin(username: string): Promise<boolean> {
    logger.info(`AuthService.devLogin called with: ${username}`);
    this.setToken('dev-token');
    localStorage.setItem('mythic_dev_user', JSON.stringify({ username }));
    this.user = {
      id: 'dev-user',
      username: username,
      is_superuser: true // Dev user is superuser
    };
    return true;
  }

  async logout(): Promise<void> {
    logger.info('AuthService.logout called');
    this.user = null;
    this.token = null;
    localStorage.removeItem(this.STORAGE_KEY);
    localStorage.removeItem('mythic_dev_user');
  }

  async getUser(): Promise<UserProfile | null> {
    if (this.user) return this.user;
    if (!this.token) return null;

    if (this.token === 'dev-token') {
        const stored = localStorage.getItem('mythic_dev_user');
        if (stored) {
            const { username } = JSON.parse(stored);
            this.user = {
                id: 'dev-user',
                username,
                is_superuser: true
            };
            return this.user;
        } else {
            logger.warn('AuthService: dev-token present but no user data found. Logging out.');
            this.logout();
            return null;
        }
    }

    try {
      const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      
      if (res.ok) {
        this.user = await res.json();
        logger.debug(`User retrieved: ${this.user?.username} (${this.user?.id})`);
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
