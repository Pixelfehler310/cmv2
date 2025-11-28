import { Search, Bell, Menu, User, Settings } from 'lucide-react';
import { cn } from '@rpg/ui/src/lib/utils';
import { IConnectionState, UserProfile } from '@rpg/bridge';

interface AppNavbarProps {
  user: UserProfile | null;
  connection: IConnectionState;
  onLogout: () => void;
}

export const AppNavbar = ({ user, connection, onLogout }: AppNavbarProps) => {
  return (
    <nav className="h-14 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 flex items-center justify-between">
      {/* Left: Logo */}
      <div className="flex items-center gap-2 font-heading text-xl text-primary cursor-pointer hover:text-primary/80 transition-colors">
        <span className="text-2xl">🐉</span>
        <span>Mythic VTT</span>
      </div>

      {/* Center: Global Search */}
      <div className="flex-1 max-w-xl mx-4">
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
          <input 
            type="text" 
            placeholder="Search library, compendium, or campaign... (Ctrl+K)"
            className="w-full h-9 bg-muted/50 border border-input rounded-md pl-9 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-ring transition-all"
          />
        </div>
      </div>

      {/* Right: Status & User */}
      <div className="flex items-center gap-4">
        {/* Connection Status */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground" title={`Latency: ${connection.latency}ms`}>
          <div className={cn(
            "w-2 h-2 rounded-full",
            connection.isConnected ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" : "bg-red-500 animate-pulse"
          )} />
          {connection.isConnected ? "Connected" : "Reconnecting..."}
        </div>

        {/* Actions */}
        <button className="p-2 hover:bg-accent hover:text-accent-foreground rounded-full transition-colors relative">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full" />
        </button>

        <button className="p-2 hover:bg-accent hover:text-accent-foreground rounded-full transition-colors">
          <Settings className="h-5 w-5" />
        </button>

        {/* User Menu */}
        <div className="flex items-center gap-3 pl-2 border-l border-border">
          <div className="text-right hidden md:block">
            <div className="text-sm font-medium leading-none">{user?.username || 'Guest'}</div>
          </div>
          <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center border border-primary/50 cursor-pointer hover:shadow-[0_0_12px_rgba(var(--palette-gold),0.3)] transition-all">
            {user?.avatarUrl ? (
              <img src={user.avatarUrl} alt={user.username} className="h-full w-full rounded-full object-cover" />
            ) : (
              <User className="h-4 w-4 text-primary" />
            )}
          </div>
          
          <button 
            onClick={onLogout}
            className="ml-2 p-2 hover:bg-destructive/10 hover:text-destructive rounded-full transition-colors"
            title="Log Out"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
          </button>
        </div>
      </div>
    </nav>
  );
};
