import { UserProfile, IAuthService } from '@rpg/bridge';

export class AuthService implements IAuthService {
  private user: UserProfile | null = null;
  private token: string | null = null;

  async login(username: string): Promise<boolean> {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      });
      
      if (!res.ok) return false;
      
      const data = await res.json();
      this.token = data.access_token;
      // Fetch profile immediately after login
      await this.getUser();
      return true;
    } catch (e) {
      console.error('Login failed', e);
      return false;
    }
  }

  async logout(): Promise<void> {
    this.user = null;
    this.token = null;
    // Optional: Call backend logout
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
      }
    } catch (e) {
      console.error('Failed to fetch user', e);
    }
    return null;
  }

  getToken() {
    return this.token;
  }
}
