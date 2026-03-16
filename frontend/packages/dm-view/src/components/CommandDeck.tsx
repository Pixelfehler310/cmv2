import React from "react";
import { useCombatStore } from "@rpg/shared";

type DmCommandDeckProps = {
  selectedCombatantId: string | null;
  onRemoveSelected?: () => void;
};

export const DmCommandDeck: React.FC<DmCommandDeckProps> = ({ selectedCombatantId, onRemoveSelected }) => {
  const { gameState, endTurn, applyDamage, removeActor } = useCombatStore();

  if (!gameState) {
    return null;
  }

  // Find the selected combatant from the live synced state
  const selectedCombatant = gameState.combatants.find((c: any) => c.id === selectedCombatantId);

  if (!selectedCombatant) {
    return (
      <div className="h-full w-full p-4">
        <div className="flex h-full flex-col rounded-xl border border-(--border-default) bg-surface-2 p-5 text-on-surface shadow-md">
          <h3 className="text-base font-bold text-(--primary-text)">Global Scene Controls</h3>
          <p className="mt-2 text-sm text-on-muted">No token selected. Select a token to view Action Economy.</p>
          <div className="mt-4 flex gap-2">
            <button className="btn btn-primary btn-sm" onClick={() => endTurn()}>
              Next Turn
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { public_name, hp_current, hp_max, action_used, bonus_action_used, movement_remaining } = selectedCombatant;

  const handleDamage = (amount: number) => {
    if (!selectedCombatantId) {
      return;
    }
    applyDamage(selectedCombatantId, amount, "slashing");
  };

  const handleRemove = () => {
    if (!selectedCombatantId) {
      return;
    }
    removeActor(selectedCombatantId);
    onRemoveSelected?.();
  };

  return (
    <div className="h-full w-full p-4">
      <div className="flex h-full min-h-0 flex-col rounded-xl border border-(--border-default) bg-surface-2 p-5 text-on-surface shadow-md">
        <div className="mb-4 flex items-center justify-between gap-3 border-b border-(--border-subtle) pb-3">
          <h3 className="text-base font-bold text-(--primary-text)">{public_name} (DM View)</h3>
          <span className="font-mono text-sm font-semibold text-(--error-text)">
            HP: {hp_current} / {hp_max}
          </span>
        </div>

        <div className="mb-4 grid grid-cols-1 gap-2 md:grid-cols-3">
          <div className="rounded-lg border border-(--border-subtle) bg-surface-1 px-3 py-2 text-sm" style={{ opacity: action_used ? 0.35 : 1 }}>
            <strong>Action</strong> {action_used ? "(Used)" : "(Available)"}
          </div>
          <div className="rounded-lg border border-(--border-subtle) bg-surface-1 px-3 py-2 text-sm" style={{ opacity: bonus_action_used ? 0.35 : 1 }}>
            <strong>Bonus Action</strong> {bonus_action_used ? "(Used)" : "(Available)"}
          </div>
          <div className="rounded-lg border border-(--border-subtle) bg-surface-1 px-3 py-2 text-sm">
            <strong>Movement:</strong> {movement_remaining} ft
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
          <button className="btn btn-danger btn-sm" style={{ opacity: action_used ? 0.35 : 1 }} disabled={action_used} onClick={() => handleDamage(5)}>
            Apply 5 Damage
          </button>
          <button className="btn btn-info btn-sm" style={{ opacity: action_used ? 0.35 : 1 }} disabled={action_used} onClick={() => handleDamage(10)}>
            Apply 10 Damage
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => endTurn()}>
            End Turn
          </button>
          <button className="btn btn-warning btn-sm" onClick={handleRemove}>
            Remove Token
          </button>
        </div>
      </div>
    </div>
  );
};
