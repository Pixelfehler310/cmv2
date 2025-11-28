import React, { Suspense } from 'react';
import { IHostBridge } from '@rpg/bridge';

// Lazy load MFEs (Placeholder for now, will be real imports later)
// const PlayerView = React.lazy(() => import('@rpg/player-view'));
// const DMView = React.lazy(() => import('@rpg/dm-view'));

// Mock components for now
const PlayerViewMock = () => <div className="p-10 text-center text-2xl text-primary">Player View Loaded</div>;
const DMViewMock = () => <div className="p-10 text-center text-2xl text-destructive">DM View Loaded</div>;

interface ViewContainerProps {
  viewType: 'player' | 'dm' | 'campaign_creator';
  bridge: IHostBridge;
  campaignId: string;
}

export const ViewContainer = ({ viewType, bridge, campaignId }: ViewContainerProps) => {
  const renderView = () => {
    switch (viewType) {
      case 'player':
        return <PlayerViewMock />; // <PlayerView bridge={bridge} campaignId={campaignId} />
      case 'dm':
        return <DMViewMock />; // <DMView bridge={bridge} campaignId={campaignId} />
      case 'campaign_creator':
        return <div>Campaign Creator</div>;
      default:
        return <div>Unknown View</div>;
    }
  };

  return (
    <div className="flex-1 relative overflow-hidden bg-background">
      <Suspense fallback={
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
        </div>
      }>
        {renderView()}
      </Suspense>
    </div>
  );
};
