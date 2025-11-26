import React from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@rpg/ui';
import { cn } from '../../lib/utils';

export function ConnectionStatus() {
  const { connectionState } = useWebSocket();

  const getStatusColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = () => {
    switch (connectionState) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Connection Error';
      default:
        return 'Disconnected';
    }
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-2">
            <div className={cn("h-2 w-2 rounded-full", getStatusColor())} />
            <span className="text-xs text-muted-foreground hidden sm:inline">
              {getStatusText()}
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>WebSocket: {getStatusText()}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

