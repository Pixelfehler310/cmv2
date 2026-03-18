import { useEffect, useMemo, useState } from "react";
import {
  selectAttackAffectedCellSetForActorAction,
  selectAttackEligibleCellSetForActorAction,
  selectAttackEligibleTargetSetForActorAction,
  selectAttackPreviewForActorAction,
  selectExecutableActionsForActor,
} from "../../selectors/combatSelectors";
import { useCombatStore } from "../../stores/useCombatStore";

type ActionUiMode = "idle" | "action_selected" | "target_preview" | "executing";

const ACTION_REFRESH_TRIGGER_SENT_TYPES = new Set([
  "request_action",
  "move_token",
  "end_turn",
  "start_combat",
  "end_combat",
  "add_actor",
  "remove_actor",
  "apply_damage",
  "apply_healing",
  "apply_condition",
  "remove_condition",
]);

type ContractActionSurfaceProps = {
  actorId: string | null;
  actorName?: string | null;
  actorOwnerUserId?: string | null;
  identityBadgeLabel?: string;
  emptyActorMessage?: string;
};

export function ContractActionSurface({
  actorId,
  actorName,
  actorOwnerUserId,
  identityBadgeLabel,
  emptyActorMessage = "Select an actor to load executable actions.",
}: ContractActionSurfaceProps): JSX.Element {
  const gameState = useCombatStore((state) => state.gameState);
  const isConnected = useCombatStore((state) => state.isConnected);
  const latestCommandOutcome = useCombatStore((state) => state.latestCommandOutcome);
  const latestDenied = useCombatStore((state) => state.latestDenied);
  const requestExecutableActions = useCombatStore((state) => state.requestExecutableActions);
  const requestAttackPreview = useCombatStore((state) => state.requestAttackPreview);
  const requestAction = useCombatStore((state) => state.requestAction);

  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const [selectedTargetId, setSelectedTargetId] = useState<string>("");
  const [selectedTemplateCell, setSelectedTemplateCell] = useState<string>("");
  const [actionHint, setActionHint] = useState<string | null>(null);
  const [actionMode, setActionMode] = useState<ActionUiMode>("idle");

  const executableActions = useCombatStore((state) => selectExecutableActionsForActor(state, actorId));
  const selectedAction = useMemo(() => executableActions.find((action) => action.action_id === selectedActionId) ?? null, [executableActions, selectedActionId]);
  const attackPreview = useCombatStore((state) => selectAttackPreviewForActorAction(state, actorId, selectedActionId));
  const attackEligibleTargetSet = useCombatStore((state) => selectAttackEligibleTargetSetForActorAction(state, actorId, selectedActionId));
  const attackEligibleCellSet = useCombatStore((state) => selectAttackEligibleCellSetForActorAction(state, actorId, selectedActionId));
  const attackAffectedCellSet = useCombatStore((state) => selectAttackAffectedCellSetForActorAction(state, actorId, selectedActionId));

  const eligibleTargetIds = useMemo(() => Array.from(attackEligibleTargetSet.values()).sort((a, b) => a.localeCompare(b)), [attackEligibleTargetSet]);
  const eligibleCellKeys = useMemo(() => Array.from(attackEligibleCellSet.values()).sort((a, b) => a.localeCompare(b)), [attackEligibleCellSet]);
  const affectedCellKeys = useMemo(() => Array.from(attackAffectedCellSet.values()).sort((a, b) => a.localeCompare(b)), [attackAffectedCellSet]);

  useEffect(() => {
    if (!isConnected || !actorId) {
      return;
    }

    requestExecutableActions(actorId);
  }, [actorId, isConnected, requestExecutableActions]);

  useEffect(() => {
    if (!isConnected || !actorId || !latestCommandOutcome?.ok) {
      return;
    }

    if (!ACTION_REFRESH_TRIGGER_SENT_TYPES.has(latestCommandOutcome.sentType)) {
      return;
    }

    requestExecutableActions(actorId);
  }, [actorId, isConnected, latestCommandOutcome, requestExecutableActions]);

  useEffect(() => {
    setSelectedActionId(null);
    setSelectedTargetId("");
    setSelectedTemplateCell("");
    setActionHint(null);
    setActionMode("idle");
  }, [actorId]);

  useEffect(() => {
    if (!selectedAction) {
      if (actionMode !== "executing") {
        setActionMode("idle");
      }
      return;
    }

    if (attackPreview && actionMode !== "executing") {
      setActionMode("target_preview");
      return;
    }

    if (!attackPreview && actionMode !== "executing") {
      setActionMode("action_selected");
    }
  }, [actionMode, attackPreview, selectedAction]);

  useEffect(() => {
    if (!latestCommandOutcome) {
      return;
    }

    if (latestCommandOutcome.sentType === "request_action") {
      setActionMode("idle");
      if (latestCommandOutcome.ok) {
        setSelectedActionId(null);
        setSelectedTargetId("");
        setSelectedTemplateCell("");
      }
      return;
    }

    if (latestCommandOutcome.sentType === "request_attack_preview" && !latestCommandOutcome.ok) {
      setActionMode("idle");
      setSelectedActionId(null);
      setSelectedTargetId("");
      setSelectedTemplateCell("");
    }
  }, [latestCommandOutcome]);

  useEffect(() => {
    if (!latestDenied) {
      return;
    }

    setActionMode("idle");
    setSelectedActionId(null);
    setSelectedTargetId("");
    setSelectedTemplateCell("");
    setActionHint(latestDenied.message ?? `Denied (${latestDenied.reasonCode}).`);
  }, [latestDenied]);

  const runAction = (actionId: string, actionTypeCost: string, targetingMode: string): void => {
    if (!actorId) {
      return;
    }

    if (targetingMode !== "self") {
      setActionMode("action_selected");
      setSelectedActionId(actionId);
      setSelectedTargetId("");
      setSelectedTemplateCell("");
      requestAttackPreview(actorId, actionId);
      setActionHint(`Previewing ${actionId}.`);
      return;
    }

    setActionMode("executing");
    requestAction(actorId, actionTypeCost, actionId, {});
    setSelectedActionId(null);
    setActionHint(`Sent ${actionId}.`);
  };

  const commitTargetedAction = (): void => {
    if (!actorId || !selectedAction || !selectedTargetId) {
      return;
    }

    if (!attackEligibleTargetSet.has(selectedTargetId)) {
      setActionHint("That target is not eligible for the selected action.");
      return;
    }

    setActionMode("executing");
    requestAction(actorId, selectedAction.action_type_cost, selectedAction.action_id, {
      target_ids: [selectedTargetId],
    });
    setActionHint(`Submitted ${selectedAction.action_id} against ${selectedTargetId}.`);
  };

  const commitAoeTemplateAction = (): void => {
    if (!actorId || !selectedAction || selectedAction.targeting_mode !== "aoe" || !selectedTemplateCell) {
      return;
    }

    if (!attackEligibleCellSet.has(selectedTemplateCell)) {
      setActionHint("That cell is not eligible for this template.");
      return;
    }

    const [xRaw, yRaw] = selectedTemplateCell.split(",");
    const x = Number.parseInt(xRaw ?? "", 10);
    const y = Number.parseInt(yRaw ?? "", 10);
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      setActionHint("Invalid template origin.");
      return;
    }

    const projectedOrigin = attackPreview?.template_projection?.origin;
    const projectedOriginKey = projectedOrigin ? `${projectedOrigin.x},${projectedOrigin.y}` : null;
    if (!projectedOriginKey || projectedOriginKey !== selectedTemplateCell) {
      requestAttackPreview(actorId, selectedAction.action_id, { x, y });
      setActionHint("Projection updated. Confirm the same origin to execute.");
      return;
    }

    const targetIds = (gameState?.combatants ?? [])
      .filter((combatant) => {
        if (combatant.id === actorId) {
          return false;
        }

        const key = `${combatant.x},${combatant.y}`;
        return attackAffectedCellSet.has(key);
      })
      .map((combatant) => combatant.id);

    setActionMode("executing");
    requestAction(actorId, selectedAction.action_type_cost, selectedAction.action_id, {
      target_ids: targetIds,
      template_origin: { x, y },
      ...(attackPreview?.template_projection?.direction ? { template_direction: attackPreview.template_projection.direction } : {}),
    });

    setActionHint(`Submitted ${selectedAction.action_id} at ${x},${y}.`);
  };

  const deniedReason = latestDenied ? `${latestDenied.reasonCode}${latestDenied.message ? `: ${latestDenied.message}` : ""}` : null;

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-300">Contract Actions</h3>
          {actorId ? (
            <p className="mt-1 text-xs text-slate-400">
              {actorName ?? actorId} ({actorId})
            </p>
          ) : (
            <p className="mt-1 text-xs text-amber-300">{emptyActorMessage}</p>
          )}
        </div>
        <div className="flex items-center gap-2 text-[11px]">
          {actorOwnerUserId && <span className="rounded border border-slate-600 bg-slate-800 px-2 py-1 text-slate-300">owner:{actorOwnerUserId}</span>}
          {identityBadgeLabel && <span className="rounded border border-cyan-700 bg-cyan-900/30 px-2 py-1 text-cyan-200">as {identityBadgeLabel}</span>}
          <button
            type="button"
            className="rounded border border-slate-500 bg-slate-800 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!actorId}
            onClick={() => {
              if (actorId) {
                requestExecutableActions(actorId);
              }
            }}
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {executableActions.length === 0 && <div className="rounded border border-slate-700 bg-slate-950 p-3 text-xs text-slate-400">No action snapshot yet.</div>}
        {executableActions.map((action) => {
          const isAvailable = action.is_available;
          const isSelected = selectedActionId === action.action_id;

          return (
            <div key={action.action_id} className={`rounded border bg-slate-950 p-3 ${isSelected ? "border-cyan-700" : "border-slate-700"}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-slate-100">{action.label}</p>
                  <p className="text-[11px] text-slate-400">
                    id: {action.action_id} | family: {action.family} | cost: {action.action_type_cost}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    targeting: {action.targeting_mode}
                    {typeof action.range === "number" ? ` | range: ${action.range}` : ""}
                  </p>
                </div>
                <button
                  type="button"
                  className="rounded border border-cyan-700 bg-cyan-900/30 px-2 py-1 text-xs text-cyan-200 hover:bg-cyan-800/40 disabled:cursor-not-allowed disabled:border-slate-700 disabled:bg-slate-800 disabled:text-slate-500"
                  disabled={!isAvailable || !actorId}
                  onClick={() => runAction(action.action_id, action.action_type_cost, action.targeting_mode)}
                  title={
                    !isAvailable
                      ? (action.unavailable_reason ?? "Unavailable")
                      : action.targeting_mode === "self"
                        ? "Execute now"
                        : action.targeting_mode === "aoe"
                          ? "Request projection and choose a template origin"
                          : "Request preview and choose target"
                  }
                >
                  {action.targeting_mode === "self" ? "Execute" : "Preview"}
                </button>
              </div>
              {!isAvailable && <p className="mt-2 text-[11px] text-amber-300">Unavailable: {action.unavailable_reason ?? "unknown_reason"}</p>}
            </div>
          );
        })}
      </div>

      {selectedAction && selectedAction.targeting_mode !== "self" && (
        <div className="mt-3 rounded border border-cyan-800/60 bg-cyan-900/20 p-3 text-xs text-cyan-100">
          <p className="font-semibold">
            Targeting {selectedAction.action_id} ({selectedAction.targeting_mode})
          </p>

          {selectedAction.targeting_mode === "single" && (
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <label htmlFor="contract-target-select" className="text-cyan-200">
                Target
              </label>
              <select
                id="contract-target-select"
                value={selectedTargetId}
                onChange={(event) => setSelectedTargetId(event.target.value)}
                className="min-w-44 rounded border border-cyan-700 bg-slate-950 px-2 py-1 text-xs text-slate-100"
              >
                <option value="">Select target</option>
                {eligibleTargetIds.map((targetId) => (
                  <option key={targetId} value={targetId}>
                    {targetId}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="rounded border border-cyan-700 bg-cyan-900/35 px-2 py-1 text-xs text-cyan-200 hover:bg-cyan-800/40 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!selectedTargetId}
                onClick={commitTargetedAction}
              >
                Execute targeted action
              </button>
            </div>
          )}

          {selectedAction.targeting_mode === "aoe" && (
            <div className="mt-2 space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <label htmlFor="contract-cell-select" className="text-cyan-200">
                  Template origin
                </label>
                <select
                  id="contract-cell-select"
                  value={selectedTemplateCell}
                  onChange={(event) => setSelectedTemplateCell(event.target.value)}
                  className="min-w-44 rounded border border-cyan-700 bg-slate-950 px-2 py-1 text-xs text-slate-100"
                >
                  <option value="">Select origin cell</option>
                  {eligibleCellKeys.map((cellKey) => (
                    <option key={cellKey} value={cellKey}>
                      {cellKey}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="rounded border border-cyan-700 bg-cyan-900/35 px-2 py-1 text-xs text-cyan-200 hover:bg-cyan-800/40 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={!selectedTemplateCell}
                  onClick={commitAoeTemplateAction}
                >
                  Confirm template
                </button>
              </div>
              <p className="text-[11px] text-cyan-200">Projected affected cells: {affectedCellKeys.length > 0 ? affectedCellKeys.join(" ") : "none"}</p>
            </div>
          )}

          <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-cyan-200/90">
            <span>Mode: {actionMode}</span>
            <span>Eligible targets: {attackPreview?.eligible_target_ids.length ?? 0}</span>
            <span>Eligible cells: {attackPreview?.eligible_cells?.length ?? 0}</span>
            <span>Affected cells: {attackPreview?.template_projection?.affected_cells.length ?? 0}</span>
            <span>AoE shape: {attackPreview?.template_projection?.shape ?? "n/a"}</span>
            <button
              type="button"
              className="rounded border border-slate-500 px-2 py-0.5 text-xs text-slate-100 hover:bg-slate-700"
              onClick={() => {
                setSelectedActionId(null);
                setSelectedTargetId("");
                setSelectedTemplateCell("");
                setActionMode("idle");
                setActionHint("Cancelled targeting.");
              }}
            >
              Cancel targeting
            </button>
          </div>
        </div>
      )}

      {actionHint && <div className="mt-3 rounded border border-cyan-800/60 bg-cyan-900/20 p-2 text-xs text-cyan-200">{actionHint}</div>}
      {deniedReason && <div className="mt-2 rounded border border-amber-800/70 bg-amber-900/20 p-2 text-xs text-amber-200">Denied (backend): {deniedReason}</div>}
    </section>
  );
}
