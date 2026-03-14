import React, { useState } from "react";
import { useCombatStore } from "@rpg/shared";

interface MapBoardProps {
  selectedCombatantId: string | null;
  onSelectCombatant: (id: string | null) => void;
}

export const MapBoard: React.FC<MapBoardProps> = ({ selectedCombatantId, onSelectCombatant }) => {
  const { gameState, moveToken } = useCombatStore();
  const [draggedTokenId, setDraggedTokenId] = useState<string | null>(null);
  const GRID_SIZE = 50;

  if (!gameState) {
    return <div style={styles.mapContainer}>Waiting for map data...</div>;
  }

  const handleDragStart = (e: React.DragEvent, tokenId: string) => {
    setDraggedTokenId(tokenId);
    e.dataTransfer.setData("text/plain", tokenId);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedTokenId) return;

    // Snap drops to grid coordinates for deterministic server payloads.
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.max(0, Math.floor((e.clientX - rect.left) / GRID_SIZE));
    const y = Math.max(0, Math.floor((e.clientY - rect.top) / GRID_SIZE));

    // The store applies optimistic position and reconciles against server updates.
    moveToken(draggedTokenId, [[x, y]]);
    setDraggedTokenId(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div style={styles.mapContainer} onDrop={handleDrop} onDragOver={handleDragOver} onClick={() => onSelectCombatant(null)}>
      {/* Grid Background */}
      <div style={styles.gridLayer} />

      {/* Fog Reveal Tools Header */}
      <div style={styles.toolbar}>
        <button style={styles.toolBtn}>🖌️ Reveal Fog</button>
        <button style={styles.toolBtn}>⬛ Hide Fog</button>
        <button style={styles.toolBtn}>📏 Measure</button>
      </div>

      {/* Tokens */}
      {gameState.combatants.map((token: any) => (
        <div
          key={token.id}
          draggable
          onDragStart={(e) => handleDragStart(e, token.id)}
          onClick={(e) => {
            e.stopPropagation();
            onSelectCombatant(token.id);
          }}
          style={{
            ...styles.token,
            left: `${token.x * GRID_SIZE}px`,
            top: `${token.y * GRID_SIZE}px`,
            border: selectedCombatantId === token.id ? "3px solid #00ff00" : "3px solid #888",
          }}
        >
          {token.public_name[0]}
        </div>
      ))}
    </div>
  );
};

const styles = {
  mapContainer: {
    position: "relative" as const,
    flexGrow: 1,
    height: "100%",
    backgroundColor: "#222",
    overflow: "hidden",
  },
  gridLayer: {
    position: "absolute" as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundImage: "linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)",
    backgroundSize: "50px 50px",
    opacity: 0.5,
  },
  toolbar: {
    position: "absolute" as const,
    top: 10,
    left: 10,
    display: "flex",
    gap: "10px",
    zIndex: 10,
    backgroundColor: "rgba(0,0,0,0.6)",
    padding: "5px",
    borderRadius: "6px",
  },
  toolBtn: {
    backgroundColor: "#444",
    color: "#fff",
    border: "none",
    padding: "8px 12px",
    borderRadius: "4px",
    cursor: "pointer",
  },
  token: {
    position: "absolute" as const,
    width: "40px",
    height: "40px",
    borderRadius: "50%",
    backgroundColor: "#555",
    color: "#fff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "grab",
    userSelect: "none" as const,
    zIndex: 5,
    margin: "5px", // To center 40px inside 50px grid
    transition: "left 0.2s, top 0.2s",
  },
};
