import { Handle, Position } from "@xyflow/react";
import React from "react";

const badgeColors: Record<string, string> = {
  Easy: "#27ae60",
  Medium: "#f39c12",
  Hard: "#e67e22",
  Deadly: "#c0392b",
};

export const EncounterNode = ({ data, selected }: { data: any; selected?: boolean }) => {
  const badgeColor = data.difficultyBadge ? badgeColors[data.difficultyBadge as string] || "#7f8c8d" : "#7f8c8d";

  return (
    <div
      style={{
        padding: "10px 20px",
        borderRadius: "8px",
        background: "#8e44ad",
        color: "white",
        border: selected ? "2px solid #9b59b6" : "2px solid #5b2c6f",
        boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
        minWidth: "150px",
        textAlign: "center",
      }}
    >
      <Handle type="target" position={Position.Top} />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
        <div style={{ fontSize: "0.8rem", opacity: 0.9, textTransform: "uppercase" }}>Encounter</div>
        {data.difficultyBadge && (
          <div
            style={{
              fontSize: "0.65rem",
              background: badgeColor,
              padding: "2px 6px",
              borderRadius: "4px",
              fontWeight: "bold",
            }}
          >
            {data.difficultyBadge}
          </div>
        )}
      </div>
      <div style={{ fontWeight: "bold" }}>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
