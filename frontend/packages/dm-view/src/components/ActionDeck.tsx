import React, { useMemo, useState } from "react";
import { ActionCommandLab, useCombatStore } from "@rpg/shared";

interface ActionDeckProps {
  selectedCombatantId: string | null;
  campaignId: string;
}

export const ActionDeck = ({ selectedCombatantId, campaignId }: ActionDeckProps) => {
  const actingAsUserId = useCombatStore((state) => state.actingAsUserId);
  const [manualActorId, setManualActorId] = useState("");
  const [advancedMode, setAdvancedMode] = useState(false);

  const activeActorId = useMemo(() => {
    const trimmed = manualActorId.trim();
    return trimmed || selectedCombatantId || "";
  }, [manualActorId, selectedCombatantId]);

  return (
    <div className="space-y-4">
      <div className="m-4 rounded-md border border-slate-700 bg-slate-900/95 p-4 text-slate-100 shadow-lg">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-sm font-bold uppercase tracking-wide text-cyan-300">Action Command Lab (DM)</h3>
          <div className="text-right text-[10px] text-slate-400">
            <div>campaign: {campaignId}</div>
            <div>auth mode: {actingAsUserId ? `player:${actingAsUserId}` : "dm"}</div>
          </div>
        </div>

        <div className="mb-4 grid gap-3 md:grid-cols-[1fr_auto] md:items-end">
          <label className="block text-xs font-semibold text-slate-300">Target Actor ID (optional override)</label>
          <div className="space-y-2">
            <input
              type="text"
              value={manualActorId}
              onChange={(event) => setManualActorId(event.target.value)}
              placeholder="uses selected token when empty"
              className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-slate-100"
            />
            <p className="text-[11px] text-slate-400">Effective target: {activeActorId || "none"}</p>
          </div>
          <label className="flex items-center gap-2 text-xs text-slate-300">
            <input type="checkbox" checked={advancedMode} onChange={(event) => setAdvancedMode(event.target.checked)} className="h-4 w-4 rounded border border-slate-500 bg-slate-950" />
            Enable DM advanced mode (raw envelope preset)
          </label>
        </div>

        <p className="mb-3 text-[11px] text-slate-400">Phase 7 cleanup active: legacy parity controls removed. Use the shared lab below for all command testing.</p>

        <ActionCommandLab role="dm" actorId={activeActorId || undefined} title="Action Command Lab (DM)" allowRawMode={advancedMode} />

        {!advancedMode && (
          <div className="mt-3 rounded border border-slate-700 bg-slate-950/50 px-3 py-2 text-[11px] text-slate-400">
            Raw envelope is hidden. Turn on DM advanced mode to expose the `raw_envelope` preset.
          </div>
        )}
      </div>
    </div>
  );
};
