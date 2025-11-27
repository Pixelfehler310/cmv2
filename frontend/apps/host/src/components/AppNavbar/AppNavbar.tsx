import React from 'react';
import { SearchBar } from './SearchBar';
import { NavbarActions } from './NavbarActions';
import { cn } from '../../lib/utils';
import { Button } from '@rpg/ui';
import { useNavigate } from 'react-router-dom';

export function AppNavbar() {
  const navigate = useNavigate();

  return (
    <nav
      className={cn(
        "h-14 border-b flex items-center justify-between px-4 bg-background",
        "sticky top-0 z-50"
      )}
    >
      {/* Left: Logo/Branding */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          onClick={() => navigate('/')}
          className="font-bold text-lg hover:bg-accent"
        >
          Open RPG Engine
        </Button>
      </div>

      {/* Center: Search Bar */}
      <SearchBar />

      {/* Right: Actions */}
      <NavbarActions />
    </nav>
  );
}



