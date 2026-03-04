import React, { useEffect } from "react";
import { useCombatStore } from "@rpg/shared";

// In a real app, campaignId would come from the router URL parameter.
const HARDCODED_CAMPAIGN_ID = "test_123";

// @ts-ignore
export const DmCommandDeck = ({ selectedCombatantId }) => {
  const { gameState, endTurn } = useCombatStore();

  if (!gameState) {
    return null;
  }

  // Find the selected combatant from the live synced state
  const selectedCombatant = gameState.combatants.find((c: any) => c.id === selectedCombatantId);

  if (!selectedCombatant) {
    return (
      <div style={styles.deckContainer}>
        <h3>Global Scene Controls</h3>
        <p>No token selected. Select a token to view Action Economy.</p>
        <div style={styles.actionGrid}>
          <button style={styles.btn} onClick={() => endTurn()}>
            Next Turn
          </button>
        </div>
      </div>
    );
  }

  const { public_name, hp_current, hp_max, action_used, bonus_action_used, movement_remaining } = selectedCombatant;

  const handleAction = (actionType: string) => {
    useCombatStore.getState().dispatchAction(actionType, { target_id: selectedCombatantId });
  };

  return (
    <div style={styles.deckContainer}>
      <div style={styles.header}>
        <h3>{public_name} (DM View)</h3>
        <span style={styles.secretHp}>
          HP: {hp_current} / {hp_max}
        </span>
      </div>

      <div style={styles.economyDashboard}>
        <div style={{ ...styles.resource, opacity: action_used ? 0.3 : 1 }}>
          <strong>Action</strong> {action_used ? "(Used)" : "(Available)"}
        </div>
        <div style={{ ...styles.resource, opacity: bonus_action_used ? 0.3 : 1 }}>
          <strong>Bonus Action</strong> {bonus_action_used ? "(Used)" : "(Available)"}
        </div>
        <div style={styles.resource}>
          <strong>Movement:</strong> {movement_remaining} ft
        </div>
      </div>

      <div style={styles.actionGrid}>
        <button style={{ ...styles.attackBtn, opacity: action_used ? 0.3 : 1 }} disabled={action_used} onClick={() => handleAction("ATTACK")}>
          ⚔️ Basic Attack
        </button>
        <button style={{ ...styles.castBtn, opacity: action_used ? 0.3 : 1 }} disabled={action_used} onClick={() => handleAction("CAST_SPELL")}>
          ✨ Cast Spell
        </button>
        <button style={styles.btn} onClick={() => handleAction("DASH")}>
          Dash
        </button>
        <button style={styles.btn} onClick={() => handleAction("DISENGAGE")}>
          Disengage
        </button>
      </div>
    </div>
  );
};

const styles = {
  deckContainer: {
    position: "fixed" as const,
    bottom: 0,
    left: "20%",
    width: "60%",
    backgroundColor: "#1e1e1e",
    color: "#fff",
    padding: "20px",
    borderTopLeftRadius: "12px",
    borderTopRightRadius: "12px",
    boxShadow: "0 -4px 20px rgba(0,0,0,0.5)",
    fontFamily: "sans-serif",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "10px",
    borderBottom: "1px solid #444",
    paddingBottom: "10px",
  },
  secretHp: {
    color: "#ff4444",
    fontWeight: "bold",
    fontFamily: "monospace",
  },
  economyDashboard: {
    display: "flex",
    gap: "20px",
    marginBottom: "15px",
  },
  resource: {
    backgroundColor: "#333",
    padding: "8px 12px",
    borderRadius: "4px",
    fontSize: "0.9em",
  },
  actionGrid: {
    display: "flex",
    gap: "10px",
  },
  btn: {
    padding: "10px 15px",
    backgroundColor: "#444",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
  attackBtn: {
    padding: "10px 15px",
    backgroundColor: "#8b0000",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
  castBtn: {
    padding: "10px 15px",
    backgroundColor: "#00008b",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
};
