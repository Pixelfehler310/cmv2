import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AuthService } from '../lib/auth';
import { Chrome, Gamepad2 } from 'lucide-react';

export const LoginRoute = ({ auth }: { auth: AuthService }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      auth.setToken(token);
      navigate('/campaigns');
    } else if (auth.getToken()) {
      // Check if we already have a token (from localStorage)
      navigate('/campaigns');
    }
  }, [searchParams, auth, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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
    window.location.href = `http://localhost:8000/auth/${provider}/authorize`;
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
            <Chrome className="w-5 h-5" />
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
            onClick={async () => {
              if (!username) return;
              await auth.devLogin(username);
              navigate('/campaigns');
            }}
            className="w-full h-10 bg-secondary text-secondary-foreground font-medium rounded hover:bg-secondary/90 transition-colors"
          >
            Dev Login (No Backend)
          </button>
        </form>
      </div>
    </div>
  );
};
