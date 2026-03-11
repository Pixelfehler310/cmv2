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
    <div className="p-4 flex flex-col gap-3">
      <h3 className="m-0 font-heading text-lg text-foreground">Encounter Builder</h3>
      <div className="text-sm text-muted-foreground">
        Editing: <strong className="text-foreground">{node.data.label as string}</strong>
      </div>

      <div>
        <label className="block mb-2 font-bold text-sm text-foreground">Difficulty</label>
        <div className="flex gap-2">
          {["Easy", "Medium", "Hard", "Deadly"].map((diff) => (
            <button
              key={diff}
              onClick={() => handleChangeDifficulty(diff as any)}
              className={`px-3 py-1.5 rounded border transition-colors text-sm font-medium ${
                node.data.difficultyBadge === diff ? "bg-primary border-primary text-primary-foreground" : "bg-surface-200 border-border text-foreground hover:bg-surface-300"
              }`}
            >
              {diff}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 p-3 bg-surface-200 rounded-md border border-border">
        <div className="flex justify-between mb-2 text-foreground">
          <span className="text-sm font-medium">Total XP:</span>
          <strong className="text-primary font-bold">1250 XP</strong>
        </div>
        <div className="flex justify-between text-foreground">
          <span className="text-sm font-medium">Party Level:</span>
          <strong className="font-bold">Level 3 (4 PCs)</strong>
        </div>
        <p className="mt-3 text-xs text-muted-foreground italic">Mock data: In a real implementation, you would add monsters to this encounter to calculate these values.</p>
      </div>
    </div>
  );
};
