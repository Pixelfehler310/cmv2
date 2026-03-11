import { Handle, Position } from "@xyflow/react";
import React from "react";

// Assuming we want some basic styling with standard HTML or design system
// Using generic inline or simple classes until specific ui components are integrated.
export const SceneNode = ({ data, selected }: { data: any; selected?: boolean }) => {
  return (
    <div
      className={`px-5 py-3 rounded-xl shadow-md min-w-[150px] text-center border-2 transition-colors backdrop-blur-sm ${
        selected ? "border-blue-500 bg-blue-500/20" : "border-surface-300 bg-surface-200"
      } text-foreground`}
    >
      <Handle type="target" position={Position.Top} />
      <div className="text-xs uppercase tracking-wider font-semibold opacity-70">Scene</div>
      <div className="font-bold mt-1 text-lg">{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
