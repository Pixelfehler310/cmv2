import { Bell, User, Settings, LogOut } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@rpg/ui";
import { IConnectionState, UserProfile } from "@rpg/bridge";

interface AppNavbarProps {
  user: UserProfile | null;
  connection: IConnectionState;
  onLogout: () => void;
}

export const AppNavbar = ({ user, connection, onLogout }: AppNavbarProps) => {
  return (
    <nav className="h-14 border-b border-border bg-surface-100 backdrop-blur supports-[backdrop-filter]:bg-surface-100/90 px-4 flex items-center justify-between shadow-sm">
      {/* Left: Logo */}
      <div className="flex items-center gap-2 font-heading text-xl cursor-pointer hover:scale-105 transition-transform">
        <div className="w-8 h-8 rounded-lg outline-none gradient-vtt flex items-center justify-center shadow-sm">
          <span className="text-xl text-white">🎲</span>
        </div>
        <span className="bg-clip-text text-transparent gradient-vtt font-bold">Civic VTT</span>
      </div>

      {/* Center: Navigation Links */}
      <div className="flex-1 flex justify-center items-center gap-6">
        <NavLink to="/campaigns" className={({ isActive }) => cn("text-sm font-bold transition-colors", isActive ? "text-primary" : "text-muted-foreground hover:text-foreground")}>
          Campaigns
        </NavLink>
        <NavLink to="/content" className={({ isActive }) => cn("text-sm font-bold transition-colors", isActive ? "text-primary" : "text-muted-foreground hover:text-foreground")}>
          Content Manager
        </NavLink>
      </div>

      {/* Right: Status & User */}
      <div className="flex items-center gap-4">
        {/* Connection Status */}
        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground mr-2" title={`Latency: ${connection.latency}ms`}>
          <div className={cn("w-2.5 h-2.5 rounded-full", connection.isConnected ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 animate-pulse")} />
          {connection.isConnected ? "Connected" : "Reconnecting..."}
        </div>

        {/* Actions */}
        <button className="btn btn-secondary p-2 rounded-full relative">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1 right-1 w-2 h-2 gradient-alert rounded-full" />
        </button>

        <button className="btn btn-secondary p-2 rounded-full">
          <Settings className="h-4 w-4" />
        </button>

        {/* User Menu */}
        <div className="flex items-center gap-3 pl-4 ml-2 border-l border-border">
          <div className="text-right hidden md:block">
            <div className="text-sm font-bold text-foreground leading-none">{user?.username || "Guest"}</div>
          </div>
          <div className="h-9 w-9 rounded-full gradient-quest flex items-center justify-center shadow-sm cursor-pointer hover:scale-105 transition-transform active-scale-95">
            {user?.avatarUrl ? (
              <img src={user.avatarUrl} alt={user.username} className="h-full w-full rounded-full object-cover border-2 border-surface-100" />
            ) : (
              <User className="h-4 w-4 text-white" />
            )}
          </div>

          <button onClick={onLogout} className="btn p-2 hover:bg-red-500/10 hover:text-red-500 text-muted-foreground rounded-full transition-colors ml-1" title="Log Out">
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </nav>
  );
};
