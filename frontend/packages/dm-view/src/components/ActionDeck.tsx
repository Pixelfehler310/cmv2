import React, { useMemo, useState } from "react";
import { useCombatStore } from "@rpg/shared";
import { IHostBridge } from "@rpg/bridge";

interface ActionDeckProps {
  bridge?: IHostBridge;
  selectedCombatantId: string | null;
  campaignId: string;
}

export const ActionDeck = ({ bridge, selectedCombatantId, campaignId }: ActionDeckProps) => {
  const { dispatchAction, dispatchRawEnvelope, endTurn, applyDamage, removeActor, moveToken, clearCommandLog, commandLog } = useCombatStore();
  const [manualActorId, setManualActorId] = useState("");
  const [damageAmount, setDamageAmount] = useState(5);
  const [healingAmount, setHealingAmount] = useState(5);
  const [moveX, setMoveX] = useState(0);
  const [moveY, setMoveY] = useState(0);
  const [rawType, setRawType] = useState("end_turn");
  const [rawPayloadText, setRawPayloadText] = useState('{\n  "actor_id": ""\n}');
  const [rawParseError, setRawParseError] = useState<string | null>(null);

  const activeActorId = useMemo(() => {
    const trimmed = manualActorId.trim();
    return trimmed || selectedCombatantId || "";
  }, [manualActorId, selectedCombatantId]);

  const runEndTurn = () => {
    endTurn();
  };

  const runApplyDamage = () => {
    if (!activeActorId) {
      return;
    }
    applyDamage(activeActorId, Math.max(0, damageAmount), "force");
  };

  const runApplyHealing = () => {
    if (!activeActorId) {
      return;
    }
    dispatchAction("apply_healing", { actor_id: activeActorId, amount: Math.max(0, healingAmount) });
  };

  const runRemoveActor = () => {
    if (!activeActorId) {
      return;
    }
    removeActor(activeActorId);
  };

  const runMoveToken = () => {
    if (!activeActorId) {
      return;
    }
    moveToken(activeActorId, [[moveX, moveY]]);
  };

  const runRawEnvelope = async () => {
    setRawParseError(null);

    let parsedPayload: any;
    try {
      parsedPayload = rawPayloadText.trim() ? JSON.parse(rawPayloadText) : {};
    } catch (error) {
      const message = error instanceof Error ? error.message : "Invalid JSON payload";
      setRawParseError(message);
      return;
    }

    try {
      await dispatchRawEnvelope(rawType.trim(), parsedPayload);
    } catch {
      // Errors are logged in combat store commandLog; no local handling needed.
    }
  };

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
    <div className="m-4 rounded-md border border-slate-700 bg-slate-900/95 p-4 text-slate-100 shadow-lg">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wide text-cyan-300">DM Command Test Console</h3>
        <span className="text-[10px] text-slate-400">campaign: {campaignId}</span>
      </div>

      <div className="mb-3 rounded border border-slate-700 bg-slate-950/60 p-2 text-xs">
        <div>Selected from map: {selectedCombatantId ?? "none"}</div>
        <div className="mt-1">Bridge passed: {bridge ? "yes" : "no"}</div>
      </div>

      <div className="mb-4 space-y-2">
        <label className="block text-xs font-semibold text-slate-300">Target Actor ID (optional override)</label>
        <input
          type="text"
          value={manualActorId}
          onChange={(e) => setManualActorId(e.target.value)}
          placeholder="uses selected token when empty"
          className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-slate-100"
        />
        <div className="text-[11px] text-slate-400">Effective target: {activeActorId || "none"}</div>
      </div>

      <div className="mb-4 rounded border border-slate-700 bg-slate-950/40 p-3">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-300">Typed Commands</div>
        <div className="grid grid-cols-2 gap-2">
          <button type="button" onClick={runEndTurn} className="rounded bg-indigo-600 px-2 py-1 text-xs font-medium hover:bg-indigo-500">
            end_turn
          </button>
          <button
            type="button"
            onClick={runApplyDamage}
            disabled={!activeActorId}
            className="rounded bg-rose-700 px-2 py-1 text-xs font-medium hover:bg-rose-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            apply_damage
          </button>
          <button
            type="button"
            onClick={runApplyHealing}
            disabled={!activeActorId}
            className="rounded bg-emerald-700 px-2 py-1 text-xs font-medium hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            apply_healing
          </button>
          <button
            type="button"
            onClick={runRemoveActor}
            disabled={!activeActorId}
            className="rounded bg-amber-700 px-2 py-1 text-xs font-medium hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            remove_actor
          </button>
        </div>

        <div className="mt-3 grid grid-cols-2 gap-2">
          <label className="text-[11px] text-slate-300">
            damage
            <input
              type="number"
              min={0}
              value={damageAmount}
              onChange={(e) => setDamageAmount(Number(e.target.value))}
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
            />
          </label>
          <label className="text-[11px] text-slate-300">
            healing
            <input
              type="number"
              min={0}
              value={healingAmount}
              onChange={(e) => setHealingAmount(Number(e.target.value))}
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
            />
          </label>
        </div>

        <div className="mt-3 grid grid-cols-3 gap-2">
          <label className="text-[11px] text-slate-300">
            x
            <input
              type="number"
              value={moveX}
              onChange={(e) => setMoveX(Number(e.target.value))}
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
            />
          </label>
          <label className="text-[11px] text-slate-300">
            y
            <input
              type="number"
              value={moveY}
              onChange={(e) => setMoveY(Number(e.target.value))}
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
            />
          </label>
          <button
            type="button"
            onClick={runMoveToken}
            disabled={!activeActorId}
            className="mt-5 rounded bg-sky-700 px-2 py-1 text-xs font-medium hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            move_token
          </button>
        </div>
      </div>

      <div className="mb-4 rounded border border-slate-700 bg-slate-950/40 p-3">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-300">Raw Envelope</div>
        <label className="mb-2 block text-[11px] text-slate-300">
          type
          <input
            type="text"
            value={rawType}
            onChange={(e) => setRawType(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
          />
        </label>
        <label className="block text-[11px] text-slate-300">
          payload (json)
          <textarea
            value={rawPayloadText}
            onChange={(e) => setRawPayloadText(e.target.value)}
            rows={5}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 font-mono text-xs"
          />
        </label>
        {rawParseError && <div className="mt-2 text-xs text-rose-300">JSON parse error: {rawParseError}</div>}
        <button
          type="button"
          onClick={() => {
            void runRawEnvelope();
          }}
          className="mt-2 rounded bg-cyan-700 px-2 py-1 text-xs font-medium hover:bg-cyan-600"
        >
          Send Raw Envelope
        </button>
      </div>

      <div className="rounded border border-slate-700 bg-slate-950/40 p-3">
        <div className="mb-2 flex items-center justify-between">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-300">Command Log</div>
          <button type="button" onClick={clearCommandLog} className="rounded bg-slate-700 px-2 py-1 text-[11px] hover:bg-slate-600">
            Clear Logs
          </button>
        </div>
        <div className="max-h-48 space-y-1 overflow-y-auto rounded border border-slate-800 bg-black/40 p-2 font-mono text-[11px]">
          {commandLog.length === 0 && <div className="text-slate-500">No log entries yet.</div>}
          {commandLog.map((entry, index) => (
            <div key={entry.timestamp + "-" + entry.type + "-" + index} className="rounded border border-slate-800 bg-slate-900/70 p-1">
              <div className="flex items-center justify-between gap-2 text-slate-300">
                <span>
                  [{entry.direction}] {entry.type}
                </span>
                <span className="text-[10px] text-slate-500">{entry.timestamp}</span>
              </div>
              <div className="mt-1 break-all text-slate-400">{renderPayloadPreview(entry.payload)}</div>
              {entry.message && <div className="mt-1 text-rose-300">{entry.message}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
