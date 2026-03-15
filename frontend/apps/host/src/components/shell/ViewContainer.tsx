import React, { Suspense, useEffect } from "react";
import { IHostBridge } from "@rpg/bridge";
import { logger } from "../../lib/logger";
import { JSONDebugger } from "../JSONDebugger";

// Lazy load MFEs
const PlayerView = React.lazy(() => import("@rpg/player-view").then((module) => ({ default: module.PlayerView })));
const DMView = React.lazy(() => import("@rpg/dm-view").then((module) => ({ default: module.DmDashboard })));

// Mock components for now
// const DMViewMock = () => <div className="p-10 text-center text-2xl text-destructive">ASDF View Loaded</div>;

interface ViewContainerProps {
  viewType: "player" | "dm" | "campaign_creator";
  bridge: IHostBridge;
  campaignId: string;
}

export const ViewContainer = ({ viewType, bridge, campaignId }: ViewContainerProps) => {
  useEffect(() => {
    logger.info("ViewContainer rendering view: " + viewType + " for campaign: " + campaignId);
  }, [viewType, campaignId]);

  const renderView = () => {
    switch (viewType) {
      case "player":
        return <PlayerView bridge={bridge} campaignId={campaignId} />;
      case "dm":
        return <DMView bridge={bridge} campaignId={campaignId} />;
      case "campaign_creator":
        return <div>Campaign Creator</div>;
      default:
        return <div>Unknown View</div>;
    }
  };

  return (
    <div className="flex-1 relative overflow-hidden bg-background h-full">
      <Suspense
        fallback={
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="spinner spinner-lg" />
          </div>
        }
      >
        {renderView()}
        {viewType !== "dm" && (
          <div className="absolute top-0 right-0 z-50 pointer-events-none opacity-80 backdrop-blur-sm">
            <JSONDebugger />
          </div>
        )}
      </Suspense>
    </div>
  );
};
