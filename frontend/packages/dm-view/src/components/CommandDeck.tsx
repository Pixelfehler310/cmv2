import React from "react";
import { useCombatStore } from "@rpg/shared";

type DmCommandDeckProps = {
  selectedCombatantId: string | null;
  onRemoveSelected?: () => void;
};

export const DmCommandDeck: React.FC<DmCommandDeckProps> = ({ selectedCombatantId, onRemoveSelected }) => {
  const { gameState, endTurn, applyDamage, removeActor } = useCombatStore();

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

  const handleDamage = (amount: number) => {
    if (!selectedCombatantId) {
      return;
    }
    applyDamage(selectedCombatantId, amount, "slashing");
  };

  const handleRemove = () => {
    if (!selectedCombatantId) {
      return;
    }
    removeActor(selectedCombatantId);
    onRemoveSelected?.();
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
        <button style={{ ...styles.attackBtn, opacity: action_used ? 0.3 : 1 }} disabled={action_used} onClick={() => handleDamage(5)}>
          ⚔️ Apply 5 Damage
        </button>
        <button style={{ ...styles.castBtn, opacity: action_used ? 0.3 : 1 }} disabled={action_used} onClick={() => handleDamage(10)}>
          ✨ Apply 10 Damage
        </button>
        <button style={styles.btn} onClick={() => endTurn()}>
          End Turn
        </button>
        <button style={styles.removeBtn} onClick={handleRemove}>
          Remove Token
        </button>
      </div>
    </div>
  );
};

const styles = {
  deckContainer: {
    height: "100%",
    width: "100%",
    backgroundColor: "#1e1e1e",
    color: "#fff",
    padding: "20px",
    boxSizing: "border-box" as const,
    fontFamily: "sans-serif",
    overflowY: "auto" as const,
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
  removeBtn: {
    padding: "10px 15px",
    backgroundColor: "#5a2020",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
};
