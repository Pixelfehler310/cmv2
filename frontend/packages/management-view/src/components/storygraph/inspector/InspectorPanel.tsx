import React from "react";
import { useStoryGraphStore } from "../../../store/StoryGraphStore";
import { EncounterBuilder } from "./EncounterBuilder";

export const InspectorPanel: React.FC = () => {
  const selectedNodeId = useStoryGraphStore((state) => state.selectedNodeId);
  const nodes = useStoryGraphStore((state) => state.nodes);
  const setNodes = useStoryGraphStore((state) => state.setNodes);

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  if (!selectedNodeId || !selectedNode) {
    return (
      <div
        style={{
          width: "300px",
          borderLeft: "1px solid #eee",
          background: "#fff",
          padding: "20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#aaa",
          height: "100%",
        }}
      >
        Select a node to inspect
      </div>
    );
  }

  const handleChangeLabel = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNodes(nodes.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...n.data, label: e.target.value } } : n)));
  };

  const handleChangeNote = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNodes(nodes.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...n.data, noteContent: e.target.value } } : n)));
  };

  return (
    <div
      style={{
        width: "300px",
        borderLeft: "1px solid #e0e0e0",
        background: "#fff",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        boxShadow: "-2px 0 10px rgba(0,0,0,0.05)",
        overflowY: "auto",
      }}
    >
      <div style={{ padding: "16px", borderBottom: "1px solid #e0e0e0", background: "#f8f9fa" }}>
        <h2 style={{ margin: 0, fontSize: "1.1rem", textTransform: "capitalize" }}>{selectedNode.type?.replace("Node", "")} Node</h2>
        <div style={{ fontSize: "0.8rem", color: "#888", marginTop: "4px" }}>ID: {selectedNode.id}</div>
      </div>

      <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "16px" }}>
        <div>
          <label style={{ display: "block", marginBottom: "4px", fontSize: "0.9rem", fontWeight: "bold" }}>Label</label>
          <input
            type="text"
            value={(selectedNode.data.label as string) || ""}
            onChange={handleChangeLabel}
            style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc", boxSizing: "border-box" }}
          />
        </div>

        {selectedNode.type === "noteNode" && (
          <div>
            <label style={{ display: "block", marginBottom: "4px", fontSize: "0.9rem", fontWeight: "bold" }}>Content</label>
            <textarea
              value={(selectedNode.data.noteContent as string) || ""}
              onChange={handleChangeNote}
              rows={6}
              style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc", resize: "vertical", boxSizing: "border-box" }}
            />
          </div>
        )}
      </div>

      {selectedNode.type === "encounterNode" && (
        <div style={{ borderTop: "1px solid #eee", marginTop: "auto" }}>
          <EncounterBuilder />
        </div>
      )}

      {selectedNode.type === "sceneNode" && (
        <div style={{ padding: "16px", borderTop: "1px solid #eee", marginTop: "auto", background: "#fafafa" }}>
          <h3 style={{ margin: "0 0 8px 0", fontSize: "1rem" }}>Scene Properties</h3>
          <p style={{ fontSize: "0.85rem", color: "#666" }}>Scene features like background image and ambient music will be configured here.</p>
        </div>
      )}
    </div>
  );
};
