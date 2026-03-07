import React, { useState, useEffect } from "react";
import { useCombatStore } from "@rpg/shared";
import { MapBoard } from "../components/MapBoard";
import { DmCommandDeck } from "../components/CommandDeck";
import { InitiativePanel } from "../components/InitiativePanel";
import { ActionDeck } from "../components/ActionDeck";

export const DmDashboard = () => {
  const { isConnected, connect } = useCombatStore();
  const [selectedCombatantId, setSelectedCombatantId] = useState<string | null>(null);

  useEffect(() => {
    // Connect to a hardcoded campaign for MVP
    connect("test_123", "dm");
  }, [connect]);

  if (!isConnected) {
    return <div style={{ color: "white", padding: "20px" }}>Connecting to Backend Engine from DmDashboard...</div>;
  }

  return (
    <div style={styles.dashboard}>
      <InitiativePanel selectedCombatantId={selectedCombatantId} onSelectCombatant={setSelectedCombatantId} />
      <MapBoard selectedCombatantId={selectedCombatantId} onSelectCombatant={setSelectedCombatantId} />
      {/* The CommandDeck renders conditionally on having a selection, or handles null internally. We pass the ID down. */}
      {selectedCombatantId && <DmCommandDeck selectedCombatantId={selectedCombatantId} />}

      {/* Raw ActionDeck for Walking Skeleton */}
      <div className="absolute top-10 right-10 w-96 z-50">
        <ActionDeck />
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
