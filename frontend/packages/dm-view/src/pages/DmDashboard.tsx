import React from "react";
import { IHostBridge } from "@rpg/bridge";
import { DmWorkspace } from "../workspace/DmWorkspace";

interface DmDashboardProps {
  bridge?: IHostBridge;
  campaignId: string;
  frontendTesting?: {
    dmProxyDock?: boolean;
  };
}

export const DmDashboard = ({ bridge, campaignId, frontendTesting }: DmDashboardProps) => {
  return <DmWorkspace bridge={bridge} campaignId={campaignId} frontendTesting={frontendTesting} />;
};
