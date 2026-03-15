import React from "react";

export interface PublicCombatLogProps {
  logs: any[];
}

export const PublicCombatLog: React.FC<PublicCombatLogProps> = ({ logs }) => {
  if (!logs || logs.length === 0) return null;

  return (
    <div className="absolute bottom-4 left-4 w-96 max-h-64 overflow-y-auto bg-gray-950/80 backdrop-blur-md border border-gray-800 rounded-lg shadow-2xl p-4 pointer-events-none z-50">
      <h3 className="text-xs text-gray-500 font-bold uppercase tracking-widest mb-3">
        Combat Log
      </h3>
      <div className="space-y-2 flex flex-col justify-end">
        {logs.map((log) => (
          <div
            key={log.id}
            className="text-sm text-gray-300 border-b border-gray-800/50 pb-2 last:border-0 last:pb-0"
          >
            <span className="text-gray-600 text-xs mr-2 font-mono">
              [{new Date(log.timestamp).toLocaleTimeString()}]
            </span>
            {log.message}
          </div>
        ))}
      </div>
    </div>
  );
};
