import React from "react";
import { useStoryGraphStore, StoryNode } from "../../../store/StoryGraphStore";

export const EncounterBuilder: React.FC = () => {
  const selectedNodeId = useStoryGraphStore((state) => state.selectedNodeId);
  const nodes = useStoryGraphStore((state) => state.nodes);
  const setNodes = useStoryGraphStore((state) => state.setNodes);

  const node = nodes.find((n) => n.id === selectedNodeId);

  if (!node || node.type !== "encounterNode") return null;

  const handleChangeDifficulty = (difficulty: "Easy" | "Medium" | "Hard" | "Deadly") => {
    setNodes(nodes.map((n) => (n.id === node.id ? { ...n, data: { ...n.data, difficultyBadge: difficulty } } : n)));
  };

  return (
    <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
      <h3 style={{ margin: 0 }}>Encounter Builder</h3>
      <div style={{ fontSize: "0.9rem", color: "#666" }}>
        Editing: <strong>{node.data.label as string}</strong>
      </div>

      <div>
        <label style={{ display: "block", marginBottom: "8px", fontWeight: "bold" }}>Difficulty</label>
        <div style={{ display: "flex", gap: "8px" }}>
          {["Easy", "Medium", "Hard", "Deadly"].map((diff) => (
            <button
              key={diff}
              onClick={() => handleChangeDifficulty(diff as any)}
              style={{
                padding: "6px 12px",
                borderRadius: "4px",
                border: "1px solid #ccc",
                background: node.data.difficultyBadge === diff ? "#3498db" : "#fff",
                color: node.data.difficultyBadge === diff ? "#fff" : "#333",
                cursor: "pointer",
              }}
            >
              {diff}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginTop: "16px", padding: "12px", background: "#f8f9fa", borderRadius: "4px", border: "1px solid #eee" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
          <span>Total XP:</span>
          <strong>1250 XP</strong>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Party Level:</span>
          <strong>Level 3 (4 PCs)</strong>
        </div>
        <p style={{ marginTop: "12px", fontSize: "0.85rem", color: "#666" }}>
          <em>Mock data: In a real implementation, you would add monsters to this encounter to calculate these values.</em>
        </p>
      </div>
    </div>
  );
};
