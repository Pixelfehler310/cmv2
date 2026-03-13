import React from "react";
import { X } from "lucide-react";
import { RawJsonViewer } from "./RawJsonViewer";
import { cn } from "@rpg/ui";

interface EntityDetailPanelProps {
  entity: any | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EntityDetailPanel: React.FC<EntityDetailPanelProps> = ({ entity, isOpen, onClose }) => {
  if (!entity && isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          "fixed inset-0 bg-black/40 backdrop-blur-sm z-40 transition-opacity duration-300",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={onClose}
      />

      {/* Slide-over Panel */}
      <div
        className={cn(
          "fixed right-0 top-0 h-full w-[400px] md:w-[600px] bg-background border-l border-border shadow-2xl z-50 transition-transform duration-300 ease-in-out transform",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div>
              <h2 className="text-2xl font-heading text-foreground">{entity?.name || "Entity Details"}</h2>
              <p className="text-muted-foreground text-sm">{entity?.type || "Unknown Type"}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-surface-200 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            <section>
              <h3 className="text-lg font-semibold mb-2">Overview</h3>
              <p className="text-foreground">{entity?.description || "No description available."}</p>
            </section>

            <section>
              <h3 className="text-lg font-semibold mb-2">Technical Details</h3>
              <div className="grid grid-cols-2 gap-4">
                {entity && Object.entries(entity).map(([key, value]) => {
                  if (typeof value === 'object' || Array.isArray(value) || key === 'name' || key === 'description') return null;
                  return (
                    <div key={key} className="bg-surface-100 p-3 rounded-lg border border-border">
                      <p className="text-xs text-muted-foreground uppercase">{key.replace(/_/g, ' ')}</p>
                      <p className="font-mono text-foreground">{String(value)}</p>
                    </div>
                  );
                })}
              </div>
            </section>

            <section>
              <h3 className="text-lg font-semibold mb-2">Raw JSON</h3>
              <RawJsonViewer data={entity} />
            </section>
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-border bg-surface-50">
            <button
              onClick={onClose}
              className="w-full py-3 bg-surface-200 hover:bg-surface-300 text-foreground font-semibold rounded-xl transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
