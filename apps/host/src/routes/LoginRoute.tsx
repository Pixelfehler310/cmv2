import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthService } from '../../lib/auth';

export const LoginRoute = ({ auth }: { auth: AuthService }) => {
  const [username, setUsername] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await auth.login(username);
    if (success) {
      navigate('/campaigns');
    } else {
      alert('Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[url('https://images.unsplash.com/photo-1605806616949-1e87b487bc2a?q=80&w=2574&auto=format&fit=crop')] bg-cover bg-center">
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />
      
      <div className="relative z-10 w-full max-w-md p-8 bg-card border border-border rounded-lg shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-heading text-primary mb-2">Mythic VTT</h1>
          <p className="text-muted-foreground">Enter the realm.</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
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
          <button
            type="submit"
            className="w-full h-10 bg-primary text-primary-foreground font-medium rounded hover:bg-primary/90 transition-colors"
          >
            Enter
          </button>
        </form>
      </div>
    </div>
  );
};
