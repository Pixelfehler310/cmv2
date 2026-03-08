import React from "react";
import { Rnd } from "react-rnd";
import { X } from "lucide-react";
import { useStoryGraphStore } from "../../../store/StoryGraphStore";
import { EncounterBuilder } from "./EncounterBuilder";

export const InspectorPanel: React.FC = () => {
  const selectedNodeId = useStoryGraphStore((state) => state.selectedNodeId);
  const nodes = useStoryGraphStore((state) => state.nodes);
  const setNodes = useStoryGraphStore((state) => state.setNodes);
  const setSelectedNodeId = useStoryGraphStore((state) => state.setSelectedNodeId);

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  if (!selectedNodeId || !selectedNode) {
    return null; // Return null so the window completely disappears when not selecting a node
  }

  const handleChangeLabel = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNodes(nodes.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...n.data, label: e.target.value } } : n)));
  };

  const handleChangeNote = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNodes(nodes.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...n.data, noteContent: e.target.value } } : n)));
  };

  return (
    <Rnd
      default={{
        x: window.innerWidth - 350,
        y: 80,
        width: 320,
        height: 500,
      }}
      minWidth={250}
      minHeight={300}
      bounds="parent"
      dragHandleClassName="inspector-drag-handle"
      style={{
        display: "flex",
        flexDirection: "column",
        background: "#fff",
        borderRadius: "8px",
        boxShadow: "0 10px 25px rgba(0,0,0,0.2)",
        overflow: "hidden",
        border: "1px solid #e0e0e0",
        zIndex: 100,
      }}
    >
      {/* Drag Handle & Header */}
      <div
        className="inspector-drag-handle"
        style={{
          padding: "12px 16px",
          background: "#2c3e50",
          color: "white",
          cursor: "grab",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ fontWeight: "bold", fontSize: "0.95rem" }}>Inspector</div>
        <button
          onClick={() => setSelectedNodeId(null)}
          style={{
            background: "transparent",
            border: "none",
            color: "white",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "4px",
            borderRadius: "4px",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.1)")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
        >
          <X size={16} />
        </button>
      </div>

      <div style={{ flexGrow: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
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
    </Rnd>
  );
};
