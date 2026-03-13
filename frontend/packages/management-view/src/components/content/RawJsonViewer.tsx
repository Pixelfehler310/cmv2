import React from "react";

interface RawJsonViewerProps {
  data: any;
}

export const RawJsonViewer: React.FC<RawJsonViewerProps> = ({ data }) => {
  return (
    <pre className="bg-surface-200 p-4 rounded-lg overflow-auto max-h-[500px] text-xs font-mono text-foreground border border-border">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
};
