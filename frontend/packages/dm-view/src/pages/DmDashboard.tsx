import React from "react";
import { IHostBridge } from "@rpg/bridge";
import { DmWorkspace } from "../workspace/DmWorkspace";

interface DmDashboardProps {
  bridge?: IHostBridge;
  campaignId: string;
}

export const DmDashboard = ({ bridge, campaignId }: DmDashboardProps) => {
  return <DmWorkspace bridge={bridge} campaignId={campaignId} />;
};
