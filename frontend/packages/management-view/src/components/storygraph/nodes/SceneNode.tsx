import { Handle, Position } from "@xyflow/react";
import React from "react";

// Assuming we want some basic styling with standard HTML or design system
// Using generic inline or simple classes until specific ui components are integrated.
export const SceneNode = ({ data, selected }: { data: any; selected?: boolean }) => {
  return (
    <div
      style={{
        padding: "10px 20px",
        borderRadius: "8px",
        background: "#2c3e50",
        color: "white",
        border: selected ? "2px solid #3498db" : "2px solid #1a252f",
        boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
        minWidth: "150px",
        textAlign: "center",
      }}
    >
      <Handle type="target" position={Position.Top} />
      <div style={{ fontSize: "0.8rem", opacity: 0.8, textTransform: "uppercase" }}>Scene</div>
      <div style={{ fontWeight: "bold", marginTop: "4px" }}>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
