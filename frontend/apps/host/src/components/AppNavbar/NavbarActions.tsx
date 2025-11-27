import React from 'react';
import { ConnectionStatus } from './ConnectionStatus';
import { UserMenu } from './UserMenu';
import { Button } from '@rpg/ui';
import { QrCode, Settings } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@rpg/ui';

export function NavbarActions() {
  return (
    <div className="flex items-center gap-2">
      <ConnectionStatus />
      
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className="h-9 w-9">
              <QrCode className="h-5 w-5" />
              <span className="sr-only">Friend Management</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Friend Management - Coming Soon</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className="h-9 w-9">
              <Settings className="h-5 w-5" />
              <span className="sr-only">Settings</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Settings - Coming Soon</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <UserMenu />
    </div>
  );
}



