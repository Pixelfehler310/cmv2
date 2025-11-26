import React from 'react';
import { ErrorBoundary } from '../ErrorBoundary';
import { useView } from '../../contexts/ViewContext';
import { useActionDispatch } from '../../contexts/ActionDispatchContext';
import { useEventBus } from '../../contexts/EventBusContext';
import { useWebSocket } from '../../contexts/WebSocketContext';

export function DMViewLoader() {
  const { selectedCampaign } = useView();
  const { dispatchAction } = useActionDispatch();
  const eventBus = useEventBus();
  const { connectionState } = useWebSocket();

  // TODO: Load actual DM View MFE when it's implemented
  // For now, show placeholder
  return (
    <ErrorBoundary>
      <div className="h-full w-full flex items-center justify-center bg-muted/30">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-semibold">DM View</h2>
          <p className="text-muted-foreground">
            DM View MFE will be loaded here
          </p>
          <p className="text-sm text-muted-foreground">
            Campaign: {selectedCampaign?.name || 'Unknown'}
          </p>
        </div>
      </div>
    </ErrorBoundary>
  );
}

