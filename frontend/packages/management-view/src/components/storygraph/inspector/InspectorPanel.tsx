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
      className="flex flex-col bg-surface-100 rounded-xl shadow-2xl overflow-hidden border border-border z-[100] text-foreground"
    >
      {/* Drag Handle & Header */}
      <div className="inspector-drag-handle flex justify-between items-center px-4 py-3 bg-surface-200 border-b border-border cursor-grab">
        <div className="font-bold text-sm tracking-wide text-foreground">Inspector</div>
        <button onClick={() => setSelectedNodeId(null)} className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-300 transition-colors">
          <X size={16} />
        </button>
      </div>

      <div className="flex-grow overflow-y-auto flex flex-col">
        <div className="p-4 border-b border-border bg-surface-50">
          <h2 className="m-0 text-lg capitalize font-heading text-foreground">{selectedNode.type?.replace("Node", "")} Node</h2>
          <div className="text-xs text-muted-foreground mt-1 font-mono">ID: {selectedNode.id}</div>
        </div>

        <div className="p-4 flex flex-col gap-4">
          <div>
            <label className="block mb-1.5 text-sm font-bold text-foreground">Label</label>
            <input type="text" value={(selectedNode.data.label as string) || ""} onChange={handleChangeLabel} className="input w-full" />
          </div>

          {selectedNode.type === "noteNode" && (
            <div>
              <label className="block mb-1.5 text-sm font-bold text-foreground">Content</label>
              <textarea value={(selectedNode.data.noteContent as string) || ""} onChange={handleChangeNote} rows={6} className="input w-full resize-y" />
            </div>
          )}
        </div>

        {selectedNode.type === "encounterNode" && (
          <div className="border-t border-border mt-auto">
            <EncounterBuilder />
          </div>
        )}

        {selectedNode.type === "sceneNode" && (
          <div className="p-4 border-t border-border mt-auto bg-surface-50">
            <h3 className="m-0 mb-2 font-heading text-lg text-foreground">Scene Properties</h3>
            <p className="text-sm text-muted-foreground">Scene features like background image and ambient music will be configured here.</p>
          </div>
        )}
      </div>
    </Rnd>
  );
};
