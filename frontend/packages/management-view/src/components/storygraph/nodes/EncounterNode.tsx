import { Handle, Position } from "@xyflow/react";
import React from "react";

const badgeColors: Record<string, string> = {
  Easy: "bg-green-500/20 text-green-400 border-green-500/30",
  Medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  Hard: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  Deadly: "bg-red-500/20 text-red-400 border-red-500/30",
};

export const EncounterNode = ({ data, selected }: { data: any; selected?: boolean }) => {
  const badgeClass = data.difficultyBadge ? badgeColors[data.difficultyBadge as string] || "bg-surface-300 text-muted-foreground border-border" : "bg-surface-300 text-muted-foreground border-border";

  return (
    <div
      className={`px-5 py-3 rounded-xl shadow-md min-w-[160px] text-center border-2 transition-colors backdrop-blur-sm ${
        selected ? "border-purple-500 bg-purple-500/20" : "border-purple-900/50 bg-surface-200"
      } text-foreground`}
    >
      <Handle type="target" position={Position.Top} />
      <div className="flex justify-between items-center mb-1">
        <div className="text-xs uppercase tracking-wider font-semibold opacity-70">Encounter</div>
        {data.difficultyBadge && <div className={`text-[0.65rem] px-1.5 py-0.5 rounded border font-bold ${badgeClass}`}>{data.difficultyBadge}</div>}
      </div>
      <div className="font-bold text-lg">{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
