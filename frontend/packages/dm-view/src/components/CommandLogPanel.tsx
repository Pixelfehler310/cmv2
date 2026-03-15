import React from "react";
import { useCombatStore } from "@rpg/shared";

export const CommandLogPanel: React.FC = () => {
  const { commandLog, clearCommandLog } = useCombatStore();

  const renderPayloadPreview = (payload: unknown): string => {
    try {
      const serialized = JSON.stringify(payload);
      if (!serialized) {
        return "null";
      }
      return serialized.length > 140 ? serialized.slice(0, 140) + "..." : serialized;
    } catch {
      return "[unserializable payload]";
    }
  };

  return (
    <div className="h-full w-full">
      <div className="flex h-full min-h-0 flex-col rounded-xl border border-[var(--border-default)] bg-surface-2 p-4 text-on-surface shadow-md">
        <div className="mb-2 flex items-center justify-between gap-2">
          <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--info-text)]">Command Log</h3>
          <button type="button" onClick={clearCommandLog} className="btn btn-ghost btn-sm px-3! py-1! text-[11px] text-on-muted">
            Clear Logs
          </button>
        </div>

        <div className="flex-1 min-h-0 space-y-1 overflow-y-auto overflow-x-hidden rounded-lg border border-[var(--border-subtle)] bg-inset p-2 font-mono text-[11px]">
          {commandLog.length === 0 && <div className="text-on-muted">No log entries yet.</div>}
          {commandLog.map((entry, index) => (
            <div key={entry.timestamp + "-" + entry.type + "-" + index} className="rounded-md border border-[var(--border-subtle)] bg-surface-1 p-2">
              <div className="flex items-center justify-between gap-2 text-on-subtle">
                <span className="truncate">
                  [{entry.direction}] {entry.type}
                </span>
                <span className="shrink-0 text-[10px] text-on-muted">{entry.timestamp}</span>
              </div>
              <div className="mt-1 break-all text-on-muted">{renderPayloadPreview(entry.payload)}</div>
              {entry.message && <div className="mt-1 text-[var(--error-text)]">{entry.message}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
