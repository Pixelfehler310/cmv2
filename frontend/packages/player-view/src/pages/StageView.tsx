import React from "react";

// Using inline styles for the prototype to avoid complex CSS setups initially.
// In a real implementation this would use Tailwind / our Design System.

export const StageView = ({ gameState }) => {
  // The StageView receives a sanitized state object from the backend/bridge.

  if (!gameState) return <div style={styles.loading}>Awaiting DM connection...</div>;

  return (
    <div style={styles.stageContainer}>
      {/* 1. The Map & Fog Container */}
      <div style={styles.mapArea}>
        <div style={styles.fogOverlay}>
          <p style={styles.fogText}>[ Opaque Fog of War Layer ]</p>
        </div>

        {/* Render Tokens (Sanitized) */}
        {gameState.combatants.map((token) => (
          <SanitizedToken key={token.id} data={token} />
        ))}
      </div>

      {/* 2. Public Initiative Tracker */}
      <div style={styles.initiativeSidebar}>
        <h3>Initiative Output</h3>
        {gameState.combatants.map((token, index) => (
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

const SanitizedToken = ({ data }) => {
  // Determine health ring color without showing actual numbers
  const healthPercent = data.hp_current / data.hp_max;
  let ringColor = "#00ff00"; // Healthy
  if (healthPercent < 0.75) ringColor = "#aaaa00"; // Wounded
  if (healthPercent < 0.25) ringColor = "#ff0000"; // Bloodied

  return (
    <div
      style={{
        ...styles.token,
        left: `${data.x * 50}px`, // Assuming 50px grid squares
        top: `${data.y * 50}px`,
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
    position: "relative",
    backgroundColor: "#111", // Dark background for the map
    backgroundImage: "linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)",
    backgroundSize: "50px 50px", // The Grid
  },
  fogOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.85)", // Very dark, opaque fog
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    pointerEvents: "none",
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
    position: "absolute",
    width: "40px",
    height: "40px",
    borderRadius: "50%",
    border: "4px solid",
    backgroundColor: "#444",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.3s ease-in-out",
    zIndex: 5,
  },
  tokenLabel: {
    position: "absolute",
    bottom: "-25px",
    whiteSpace: "nowrap",
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
