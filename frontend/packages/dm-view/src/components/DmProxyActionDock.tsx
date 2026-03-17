import React, { useMemo } from "react";
import { ContractActionSurface, useCombatStore } from "@rpg/shared";

type DmProxyActionDockProps = {
  selectedCombatantId: string | null;
};

export const DmProxyActionDock: React.FC<DmProxyActionDockProps> = ({ selectedCombatantId }) => {
  const { gameState, actingAsUserId } = useCombatStore();

  const selectedCombatant = useMemo(() => {
    if (!selectedCombatantId) {
      return null;
    }

    return gameState?.combatants.find((combatant) => combatant.id === selectedCombatantId) ?? null;
  }, [gameState, selectedCombatantId]);

  if (!gameState) {
    return <div className="h-full w-full p-4 text-sm text-on-muted">Waiting for combat state...</div>;
  }

  if (!selectedCombatant) {
    return (
      <div className="h-full w-full p-4">
        <div className="flex h-full flex-col rounded-xl border border-(--border-default) bg-surface-2 p-5 text-on-surface shadow-md">
          <h3 className="text-base font-bold text-(--primary-text)">DM Proxy Actions</h3>
          <p className="mt-2 text-sm text-on-muted">Select a combatant on the map or initiative panel to proxy contract actions.</p>
        </div>
      </div>
    );
  }

  const ownerUserId = (selectedCombatant.owner_user_id ?? "").trim();
  const ownershipLabel = ownerUserId ? `player-owned (${ownerUserId})` : "unowned or monster";
  const identityLabel = actingAsUserId ? `player:${actingAsUserId}` : "DM";

  return (
    <div className="h-full w-full overflow-y-auto p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2 text-[11px] text-on-muted">
        <span className="rounded border border-(--border-subtle) bg-surface-1 px-2 py-1">Actor: {selectedCombatant.public_name}</span>
        <span className="rounded border border-(--border-subtle) bg-surface-1 px-2 py-1">Ownership: {ownershipLabel}</span>
        <span className="rounded border border-(--border-subtle) bg-surface-1 px-2 py-1">Dispatch identity: {identityLabel}</span>
      </div>

      <ContractActionSurface
        actorId={selectedCombatant.id}
        actorName={selectedCombatant.public_name}
        actorOwnerUserId={ownerUserId || null}
        identityBadgeLabel={identityLabel}
        emptyActorMessage="Select a combatant to load proxy actions."
      />
    </div>
  );
};
