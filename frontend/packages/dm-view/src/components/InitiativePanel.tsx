import React from "react";
import { useCombatStore } from "@rpg/shared";

interface InitiativePanelProps {
  onSelectCombatant: (id: string) => void;
  selectedCombatantId: string | null;
}

export const InitiativePanel: React.FC<InitiativePanelProps> = ({ onSelectCombatant, selectedCombatantId }) => {
  const { gameState, endTurn, actingAsUserId, interactionMode } = useCombatStore();

  if (!gameState) {
    return <div className="h-full w-full p-4 text-sm text-on-muted">Loading...</div>;
  }

  return (
    <div className="h-full w-full p-4">
      <div className="flex h-full min-h-0 flex-col rounded-xl border border-(--border-default) bg-surface-2 text-on-surface shadow-md">
        <div className="flex items-center justify-between gap-3 border-b border-(--border-subtle) p-4">
          <h3 className="text-sm font-bold uppercase tracking-wide text-(--primary-text)">Initiative (Round {gameState.round})</h3>
          <div className="flex items-center gap-2">
            <span className="rounded-md border border-(--border-subtle) bg-surface-1 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-on-muted">
              {actingAsUserId ? `Play as ${actingAsUserId}` : "Play as DM"}
            </span>
            <button className="btn btn-primary btn-sm" onClick={endTurn}>
              Next Turn
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1 space-y-2 overflow-y-auto p-3">
          {gameState.combatants.map((combatant: any, index: number) => {
            const isActive = index === gameState.activeIndex;
            const isSelected = combatant.id === selectedCombatantId;

            return (
              <button
                key={combatant.id}
                type="button"
                onClick={() => {
                  if (interactionMode === "idle") {
                    onSelectCombatant(combatant.id);
                  }
                }}
                className={[
                  "w-full rounded-lg border px-3 py-2 text-left transition-colors",
                  "border-(--border-subtle) bg-surface-1 hover:bg-surface-3",
                  isSelected ? "border-(--border-default) bg-surface-3" : "",
                  isActive ? "ring-2 ring-(--color-primary) ring-offset-0" : "",
                ].join(" ")}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="font-semibold text-on-surface">{combatant.public_name}</div>
                  <div className="text-xs text-(--error-text)">
                    HP: {combatant.hp_current}/{combatant.hp_max}
                  </div>
                </div>
                <div className="mt-1 text-[11px] uppercase tracking-wide text-on-muted">{isActive ? "Active turn" : "Waiting"}</div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
