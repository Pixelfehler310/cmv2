import React, { useState } from "react";
import { useCombatStore } from "@rpg/shared";
import { IHostBridge } from "@rpg/bridge";
import { MapBoard } from "../components/MapBoard";
import { DmCommandDeck } from "../components/CommandDeck";
import { InitiativePanel } from "../components/InitiativePanel";
import { ActionDeck } from "../components/ActionDeck";

interface DmDashboardProps {
  bridge?: IHostBridge;
  campaignId: string;
}

export const DmDashboard = ({ bridge, campaignId }: DmDashboardProps) => {
  const { isConnected } = useCombatStore();
  const [selectedCombatantId, setSelectedCombatantId] = useState<string | null>(null);

  if (!isConnected) {
    return <div style={{ color: "white", padding: "20px" }}>Waiting for Host connection for campaign {campaignId}...</div>;
  }

  return (
    <div style={styles.dashboard}>
      <InitiativePanel selectedCombatantId={selectedCombatantId} onSelectCombatant={setSelectedCombatantId} />
      <MapBoard selectedCombatantId={selectedCombatantId} onSelectCombatant={setSelectedCombatantId} />
      {/* The CommandDeck renders conditionally on having a selection, or handles null internally. We pass the ID down. */}
      {selectedCombatantId && <DmCommandDeck selectedCombatantId={selectedCombatantId} onRemoveSelected={() => setSelectedCombatantId(null)} />}

      {/* Raw ActionDeck for Walking Skeleton */}
      <div className="absolute top-10 right-10 w-96 z-50">
        <ActionDeck bridge={bridge} selectedCombatantId={selectedCombatantId} campaignId={campaignId} />
      </div>
    </div>
  );
};

const styles = {
  dashboard: {
    display: "flex",
    width: "100vw",
    height: "100vh",
    backgroundColor: "#000",
    color: "#fff",
    overflow: "hidden",
  },
};
