import React, { useEffect } from "react";
import { useCombatStore } from "@rpg/shared";

const HARDCODED_CAMPAIGN_ID = "test_123";

export const StageView = () => {
  const { gameState, isConnected, connect } = useCombatStore();

  useEffect(() => {
    // Automatically connect as observer when mounting the Stage view
    connect(HARDCODED_CAMPAIGN_ID, "observer");
  }, [connect]);

  if (!isConnected || !gameState) return <div style={styles.loading}>Awaiting Engine connection...</div>;

  return (
    <div style={styles.stageContainer}>
      {/* 1. The Map & Fog Container */}
      <div style={styles.mapArea}>
        <div style={styles.fogOverlay}>
          <p style={styles.fogText}>[ Opaque Fog of War Layer ]</p>
        </div>

        {/* Render Tokens (Sanitized) */}
        {gameState.combatants.map((token: any) => (
          <SanitizedToken key={token.id} data={token} />
        ))}
      </div>

      {/* 2. Public Initiative Tracker */}
      <div style={styles.initiativeSidebar}>
        <h3>Initiative Output</h3>
        {gameState.combatants.map((token: any, index: number) => (
          <div
            key={token.id}
            style={{
              ...styles.initItem,
              borderLeft: index === gameState.activeIndex ? "4px solid #00ff00" : "4px solid transparent",
            }}
          >
            {token.public_name}
          </div>
        ))}
      </div>
    </div>
  );
};

// @ts-ignore
const SanitizedToken = ({ data }) => {
  // Determine health ring color without showing actual numbers using the observer payload
  const healthPercent = data.hp_percent || 1.0;
  let ringColor = "#00ff00"; // Healthy
  if (healthPercent < 0.75) ringColor = "#aaaa00"; // Wounded
  if (healthPercent < 0.25) ringColor = "#ff0000"; // Bloodied

  // Evaluate Size
  let sizeSquares = 1;
  if (data.size === "Large") sizeSquares = 2;
  if (data.size === "Huge") sizeSquares = 3;
  if (data.size === "Gargantuan") sizeSquares = 4;
  if (data.size === "Tiny") sizeSquares = 0.5;

  const baseTokenSizePx = 50;
  const tokenWidth = baseTokenSizePx * sizeSquares;

  return (
    <div
      style={{
        ...styles.token,
        left: `${data.x * baseTokenSizePx}px`,
        top: `${data.y * baseTokenSizePx}px`,
        width: `${tokenWidth - 10}px`,
        height: `${tokenWidth - 10}px`,
        borderColor: ringColor,
      }}
    >
      <div style={styles.tokenLabel}>{data.public_name}</div>
    </div>
  );
};

const styles = {
  stageContainer: {
    width: "100vw",
    height: "100vh",
    display: "flex",
    backgroundColor: "#000",
    color: "#fff",
    fontFamily: "sans-serif",
    overflow: "hidden",
  },
  mapArea: {
    flexGrow: 1,
    position: "relative" as const,
    backgroundColor: "#111",
    backgroundImage: "linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)",
    backgroundSize: "50px 50px",
  },
  fogOverlay: {
    position: "absolute" as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.85)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    pointerEvents: "none" as const,
    zIndex: 10,
  },
  fogText: {
    color: "#555",
    fontSize: "2rem",
  },
  initiativeSidebar: {
    width: "250px",
    backgroundColor: "#1e1e1e",
    borderLeft: "1px solid #333",
    padding: "20px",
    zIndex: 20,
  },
  initItem: {
    padding: "10px",
    marginBottom: "8px",
    backgroundColor: "#2a2a2a",
    borderRadius: "4px",
    transition: "all 0.3s",
  },
  token: {
    position: "absolute" as const,
    borderRadius: "50%",
    border: "4px solid",
    backgroundColor: "#444",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.3s ease-in-out",
    zIndex: 5,
    margin: "5px", // Center nicely in the grid chunk
  },
  tokenLabel: {
    position: "absolute" as const,
    bottom: "-25px",
    whiteSpace: "nowrap" as const,
    backgroundColor: "rgba(0,0,0,0.7)",
    padding: "2px 6px",
    borderRadius: "4px",
    fontSize: "0.8rem",
  },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100vh",
    color: "#fff",
    backgroundColor: "#000",
  },
};
