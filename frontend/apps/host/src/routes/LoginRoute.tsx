import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AuthService } from '../lib/auth';
import { config } from '../config';
import { Gamepad2 } from 'lucide-react';

import { logger } from '../lib/logger';

export const LoginRoute = ({ auth }: { auth: AuthService }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      logger.info('LoginRoute: Token found in URL, logging in');
      auth.setToken(token);
      navigate('/campaigns');
    } else if (auth.getToken()) {
      // Check if we already have a token (from localStorage)
      logger.debug('LoginRoute: Token found in localStorage, redirecting');
      navigate('/campaigns');
    }
  }, [searchParams, auth, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    logger.info(`LoginRoute: handleSubmit called, isLogin=${isLogin}, username=${username}`);
    if (isLogin) {
      const success = await auth.login(username, password);
      if (success) {
        navigate('/campaigns');
      } else {
        alert('Login failed');
      }
    } else {
      const success = await auth.register(username, password);
      if (success) {
        // Auto login after register or ask user to login
        const loginSuccess = await auth.login(username, password);
        if (loginSuccess) {
          navigate('/campaigns');
        } else {
          setIsLogin(true);
          alert('Registration successful! Please log in.');
        }
      } else {
        alert('Registration failed');
      }
    }
  };

  const handleOAuthLogin = (provider: string) => {
    logger.info(`LoginRoute: handleOAuthLogin called for provider ${provider}`);
    window.location.href = `/api/auth/${provider}/authorize`;
  };

  const handleDevLogin = async () => {
    logger.info(`LoginRoute: handleDevLogin called`);
    
    let effectiveUsername = username;
    if (!effectiveUsername) {
        logger.info(`LoginRoute: Username empty, using default "DevUser"`);
        effectiveUsername = 'DevUser';
        setUsername(effectiveUsername); // Update state for consistency
    }
    
    logger.info(`LoginRoute: Calling auth.devLogin with ${effectiveUsername}`);
    await auth.devLogin(effectiveUsername);
    navigate('/campaigns');
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center bg-cover bg-center"
      style={{ backgroundImage: "url('https://images.unsplash.com/photo-1605806616949-1e87b487bc2a?q=80&w=2574&auto=format&fit=crop')" }}
    >
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />
      
      <div className="relative z-10 w-full max-w-md p-8 bg-card border border-border rounded-lg shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-heading text-primary mb-2">Mythic VTT</h1>
          <p className="text-muted-foreground">Enter the realm.</p>
        </div>

        <div className="space-y-4 mb-8">
          <button
            onClick={() => handleOAuthLogin('google')}
            className="w-full h-10 bg-white text-black border border-gray-300 font-medium rounded hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
            Sign in with Google
          </button>
          <button
            onClick={() => handleOAuthLogin('discord')}
            className="w-full h-10 bg-[#5865F2] text-white font-medium rounded hover:bg-[#4752C4] transition-colors flex items-center justify-center gap-2"
          >
            <Gamepad2 className="w-5 h-5" />
            Sign in with Discord
          </button>
        </div>

        <div className="relative mb-8">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full h-10 bg-input border border-input rounded px-3 focus:ring-1 focus:ring-primary outline-none"
              placeholder="Gandalf"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full h-10 bg-input border border-input rounded px-3 focus:ring-1 focus:ring-primary outline-none"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            className="w-full h-10 bg-primary text-primary-foreground font-medium rounded hover:bg-primary/90 transition-colors"
          >
            {isLogin ? 'Enter' : 'Sign Up'}
          </button>
          
          <div className="text-center text-sm">
            <span className="text-muted-foreground">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
            </span>
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-primary hover:underline font-medium"
            >
              {isLogin ? 'Sign up' : 'Log in'}
            </button>
          </div>

          <div className="relative my-4">
             <div className="absolute inset-0 flex items-center">
               <span className="w-full border-t border-border" />
             </div>
             <div className="relative flex justify-center text-xs uppercase">
               <span className="bg-card px-2 text-muted-foreground">Dev</span>
             </div>
           </div>

          <button
            type="button"
            onClick={() => handleDevLogin()}
            className="w-full h-10 bg-secondary text-secondary-foreground font-medium rounded hover:bg-secondary/90 transition-colors"
          >
            Dev Login
          </button>
        </form>
      </div>
    </div>
  );
};
