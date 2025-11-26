import React from 'react';
import { useView } from '../../contexts/ViewContext';
import { PlayerViewLoader } from './PlayerViewLoader';
import { DMViewLoader } from './DMViewLoader';
import { Button } from '@rpg/ui';
import { cn } from '../../lib/utils';

export function ViewContainer() {
  const { currentView, selectedCampaign, switchView } = useView();

  if (!selectedCampaign) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-semibold">No Campaign Selected</h2>
          <p className="text-muted-foreground">
            Please select a campaign to continue
          </p>
          {/* TODO: Add campaign selection UI */}
        </div>
      </div>
    );
  }

  if (!currentView) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-semibold">Select a View</h2>
          <p className="text-muted-foreground mb-4">
            Choose Player or DM view to start
          </p>
          <div className="flex gap-4 justify-center">
            <Button onClick={() => switchView('player')} size="lg">
              Player View
            </Button>
            <Button onClick={() => switchView('dm')} size="lg" variant="outline">
              DM View
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("h-full w-full")}>
      {currentView === 'player' && <PlayerViewLoader />}
      {currentView === 'dm' && <DMViewLoader />}
    </div>
  );
}

