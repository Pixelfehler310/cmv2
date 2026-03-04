import React from "react";
import { useCombatStore } from "@rpg/shared";

interface InitiativePanelProps {
  onSelectCombatant: (id: string) => void;
  selectedCombatantId: string | null;
}

export const InitiativePanel: React.FC<InitiativePanelProps> = ({ onSelectCombatant, selectedCombatantId }) => {
  const { gameState, endTurn } = useCombatStore();

  if (!gameState) {
    return <div style={styles.panel}>Loading...</div>;
  }

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <h3>Initiative (Round {gameState.round})</h3>
        <button style={styles.nextBtn} onClick={endTurn}>
          Next Turn
        </button>
      </div>

      <div style={styles.roster}>
        {gameState.combatants.map((combatant: any, index: number) => {
          const isActive = index === gameState.activeIndex;
          const isSelected = combatant.id === selectedCombatantId;

          return (
            <div
              key={combatant.id}
              onClick={() => onSelectCombatant(combatant.id)}
              style={{
                ...styles.combatantRow,
                borderLeft: isActive ? "4px solid #00ff00" : "4px solid transparent",
                backgroundColor: isSelected ? "#333" : "#222",
              }}
            >
              <div style={styles.name}>{combatant.public_name}</div>
              <div style={styles.stats}>
                HP: {combatant.hp_current}/{combatant.hp_max}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const styles = {
  panel: {
    width: "300px",
    backgroundColor: "#1a1a1a",
    borderLeft: "1px solid #333",
    color: "#fff",
    fontFamily: "sans-serif",
    display: "flex",
    flexDirection: "column" as const,
  },
  header: {
    padding: "20px",
    borderBottom: "1px solid #333",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  nextBtn: {
    backgroundColor: "#444",
    color: "#00ff00",
    border: "1px solid #00ff00",
    padding: "6px 12px",
    borderRadius: "4px",
    cursor: "pointer",
  },
  roster: {
    flexGrow: 1,
    overflowY: "auto" as const,
    padding: "10px",
  },
  combatantRow: {
    padding: "10px",
    marginBottom: "5px",
    borderRadius: "4px",
    cursor: "pointer",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  name: {
    fontWeight: "bold",
  },
  stats: {
    fontSize: "0.8em",
    color: "#ff4444",
  },
};
