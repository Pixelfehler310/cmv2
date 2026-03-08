import { Handle, Position } from "@xyflow/react";
import React from "react";

export const NoteNode = ({ data, selected }: { data: any; selected?: boolean }) => {
  return (
    <div
      style={{
        padding: "10px 20px",
        borderRadius: "4px",
        background: "#f1c40f",
        color: "#2c3e50",
        border: selected ? "2px solid #e67e22" : "2px solid #d4ac0d",
        boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
        minWidth: "150px",
        maxWidth: "250px",
      }}
    >
      <Handle type="target" position={Position.Top} />
      <div style={{ fontSize: "0.8rem", opacity: 0.8, textTransform: "uppercase", marginBottom: "4px" }}>Note</div>
      <div style={{ fontWeight: "bold", marginBottom: "4px" }}>{data.label}</div>
      {data.noteContent && <div style={{ fontSize: "0.85rem", whiteSpace: "pre-wrap" }}>{data.noteContent}</div>}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
