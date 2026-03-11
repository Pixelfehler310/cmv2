import { Handle, Position } from "@xyflow/react";
import React from "react";

export const NoteNode = ({ data, selected }: { data: any; selected?: boolean }) => {
  return (
    <div
      className={`px-5 py-3 rounded-xl shadow-md min-w-[150px] max-w-[250px] border-2 transition-colors backdrop-blur-sm ${
        selected ? "border-amber-500 bg-amber-500/20" : "border-amber-900/50 bg-surface-200"
      } text-foreground`}
    >
      <Handle type="target" position={Position.Top} />
      <div className="text-xs uppercase tracking-wider font-semibold opacity-70 mb-1">Note</div>
      <div className="font-bold mb-1 text-lg text-amber-500">{data.label}</div>
      {data.noteContent && <div className="text-sm whitespace-pre-wrap text-muted-foreground">{data.noteContent}</div>}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
