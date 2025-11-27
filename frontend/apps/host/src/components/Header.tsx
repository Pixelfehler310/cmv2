import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { cn } from '../lib/utils';

export function Header() {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <header className={cn(
      "h-12 border-b flex items-center justify-between px-4 bg-background",
      "sticky top-0 z-50"
    )}>
      <div className="flex items-center gap-4">
        <h1 className="font-bold text-lg">Open RPG Engine</h1>
      </div>
      
      <div className="flex items-center gap-4">
        {isAuthenticated && user && (
          <>
            <span className="text-sm text-muted-foreground">
              {user.name}
            </span>
            <button
              onClick={logout}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Logout
            </button>
          </>
        )}
        {!isAuthenticated && (
          <span className="text-sm text-muted-foreground">
            Not authenticated
          </span>
        )}
      </div>
    </header>
  );
}



