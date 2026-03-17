import { useEffect, useMemo, useState } from "react";
import type { IHostBridge } from "@rpg/bridge";
import {
  ActionCommandLab,
  selectAttackAffectedCellSetForActorAction,
  selectAttackEligibleCellSetForActorAction,
  selectAttackEligibleTargetSetForActorAction,
  selectAttackPreviewForActorAction,
  selectExecutableActionsForActor,
  selectMovementPreviewForActor,
  selectReachableCellSetForActor,
  useCombatStore,
} from "@rpg/shared";

type FrontendTestingConfig = {
  playerActionLab?: boolean;
};

type PlayerViewProps = {
  bridge?: IHostBridge;
  campaignId: string;
  frontendTesting?: FrontendTestingConfig;
};

export function PlayerView({ bridge, campaignId, frontendTesting }: PlayerViewProps): JSX.Element {
  const gameState = useCombatStore((state) => state.gameState);
  const isConnected = useCombatStore((state) => state.isConnected);
  const setActingAsUserId = useCombatStore((state) => state.setActingAsUserId);
  const latestCommandOutcome = useCombatStore((state) => state.latestCommandOutcome);
  const requestExecutableActions = useCombatStore((state) => state.requestExecutableActions);
  const requestMovePreview = useCombatStore((state) => state.requestMovePreview);
  const requestAttackPreview = useCombatStore((state) => state.requestAttackPreview);
  const moveToken = useCombatStore((state) => state.moveToken);
  const requestAction = useCombatStore((state) => state.requestAction);
  const latestDenied = useCombatStore((state) => state.latestDenied);

  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [selectedActorId, setSelectedActorId] = useState<string>("");
  const [draggingActorId, setDraggingActorId] = useState<string | null>(null);
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const [actionHint, setActionHint] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadUser = async (): Promise<void> => {
      if (!bridge?.auth) {
        if (!cancelled) {
          setCurrentUserId(null);
        }
        return;
      }

      try {
        const user = await bridge.auth.getUser();
        if (cancelled) {
          return;
        }
        setCurrentUserId(user?.id ?? null);
      } catch {
        if (!cancelled) {
          setCurrentUserId(null);
        }
      }
    };

    void loadUser();

    return () => {
      cancelled = true;
    };
  }, [bridge]);

  useEffect(() => {
    setActingAsUserId(currentUserId);
    return () => {
      setActingAsUserId(null);
    };
  }, [currentUserId, setActingAsUserId]);

  const ownedActors = useMemo(() => {
    if (!gameState || !currentUserId) {
      return [];
    }

    return gameState.combatants.filter((combatant) => (combatant.owner_user_id ?? "") === currentUserId);
  }, [gameState, currentUserId]);

  useEffect(() => {
    if (ownedActors.length === 0) {
      setSelectedActorId("");
      return;
    }

    const stillValid = ownedActors.some((actor) => actor.id === selectedActorId);
    if (stillValid) {
      return;
    }

    setSelectedActorId(ownedActors[0].id);
  }, [ownedActors, selectedActorId]);

  const playerActionLabEnabled = frontendTesting?.playerActionLab === true;
  const hasOwnedActors = ownedActors.length > 0;
  const activeActorId = hasOwnedActors ? selectedActorId || ownedActors[0].id : null;
  const activeActor = useMemo(() => {
    if (!activeActorId) {
      return null;
    }

    return gameState?.combatants.find((combatant) => combatant.id === activeActorId) ?? null;
  }, [activeActorId, gameState]);
  const executableActions = useCombatStore((state) => selectExecutableActionsForActor(state, activeActorId));
  const selectedAction = useMemo(() => executableActions.find((action) => action.action_id === selectedActionId) ?? null, [executableActions, selectedActionId]);
  const movementPreview = useCombatStore((state) => selectMovementPreviewForActor(state, activeActorId));
  const reachableCellSet = useCombatStore((state) => selectReachableCellSetForActor(state, activeActorId));
  const attackPreview = useCombatStore((state) => selectAttackPreviewForActorAction(state, activeActorId, selectedActionId));
  const attackEligibleTargetSet = useCombatStore((state) => selectAttackEligibleTargetSetForActorAction(state, activeActorId, selectedActionId));
  const attackEligibleCellSet = useCombatStore((state) => selectAttackEligibleCellSetForActorAction(state, activeActorId, selectedActionId));
  const attackAffectedCellSet = useCombatStore((state) => selectAttackAffectedCellSetForActorAction(state, activeActorId, selectedActionId));

  useEffect(() => {
    if (!isConnected || !activeActorId) {
      return;
    }

    requestExecutableActions(activeActorId);
  }, [activeActorId, isConnected, requestExecutableActions]);

  useEffect(() => {
    if (!isConnected || !activeActorId || !latestCommandOutcome?.ok) {
      return;
    }

    requestExecutableActions(activeActorId);
  }, [activeActorId, isConnected, latestCommandOutcome, requestExecutableActions]);

  useEffect(() => {
    if (!movementPreview) {
      setDraggingActorId(null);
    }
  }, [movementPreview]);

  useEffect(() => {
    setSelectedActionId(null);
  }, [activeActorId]);

  useEffect(() => {
    if (!latestDenied) {
      return;
    }

    if (latestDenied.type === "command_denied") {
      setDraggingActorId(null);
      if (latestDenied.reasonCode === "invalid_target") {
        setActionHint(latestDenied.message ?? "Target denied by backend validation.");
      }
    }
  }, [latestDenied]);

  const mapConfig = useMemo(() => {
    const xs: number[] = [];
    const ys: number[] = [];

    for (const combatant of gameState?.combatants ?? []) {
      xs.push(combatant.x);
      ys.push(combatant.y);
    }

    if (movementPreview) {
      xs.push(movementPreview.origin.x);
      ys.push(movementPreview.origin.y);
      for (const cell of movementPreview.reachable) {
        xs.push(cell.x);
        ys.push(cell.y);
      }
    }

    const maxX = xs.length > 0 ? Math.max(...xs) : 9;
    const maxY = ys.length > 0 ? Math.max(...ys) : 9;

    return {
      columns: Math.max(10, Math.min(24, maxX + 3)),
      rows: Math.max(10, Math.min(24, maxY + 3)),
    };
  }, [gameState, movementPreview]);

  const tokenByCell = useMemo(() => {
    type Combatant = NonNullable<typeof gameState>["combatants"][number];
    const map = new Map<string, Combatant>();
    for (const combatant of gameState?.combatants ?? []) {
      map.set(`${combatant.x},${combatant.y}`, combatant);
    }
    return map;
  }, [gameState]);

  const startMoveDrag = (actorId: string): void => {
    if (selectedAction) {
      setActionHint("Finish or cancel target selection before moving.");
      return;
    }

    if (!activeActorId || actorId !== activeActorId) {
      return;
    }

    setDraggingActorId(actorId);
    requestMovePreview(actorId);
  };

  const commitMove = (x: number, y: number): void => {
    if (!draggingActorId) {
      return;
    }

    const key = `${x},${y}`;
    if (!reachableCellSet.has(key)) {
      setDraggingActorId(null);
      return;
    }

    moveToken(draggingActorId, [[x, y]]);
    setDraggingActorId(null);
  };

  const runAction = (actionId: string, actionTypeCost: string, targetingMode: string): void => {
    if (!activeActorId) {
      return;
    }

    if (targetingMode !== "self") {
      setSelectedActionId(actionId);
      requestAttackPreview(activeActorId, actionId);
      setActionHint(`Select a highlighted target for ${actionId}.`);
      return;
    }

    requestAction(activeActorId, actionTypeCost, actionId, {});
    setSelectedActionId(null);
    setActionHint(`Sent ${actionId}.`);
  };

  const commitTargetedAction = (targetActorId: string): void => {
    if (!activeActorId || !selectedAction) {
      return;
    }

    if (!attackEligibleTargetSet.has(targetActorId)) {
      setActionHint("That target is not eligible for the selected action.");
      return;
    }

    requestAction(activeActorId, selectedAction.action_type_cost, selectedAction.action_id, {
      target_ids: [targetActorId],
    });
    setActionHint(`Submitted ${selectedAction.action_id} against ${targetActorId}.`);
    setSelectedActionId(null);
  };

  const commitAoeTemplateAction = (x: number, y: number): void => {
    if (!activeActorId || !selectedAction || selectedAction.targeting_mode !== "aoe") {
      return;
    }

    const selectedCellKey = `${x},${y}`;
    if (!attackEligibleCellSet.has(selectedCellKey)) {
      setActionHint("That cell is not eligible for this template.");
      return;
    }

    const projectedOrigin = attackPreview?.template_projection?.origin;
    const projectedOriginKey = projectedOrigin ? `${projectedOrigin.x},${projectedOrigin.y}` : null;
    if (!projectedOriginKey || projectedOriginKey !== selectedCellKey) {
      requestAttackPreview(activeActorId, selectedAction.action_id, { x, y });
      setActionHint("Template projection updated. Select the same cell again to confirm.");
      return;
    }

    const targetIds = (gameState?.combatants ?? [])
      .filter((combatant) => {
        if (combatant.id === activeActorId) {
          return false;
        }
        const key = `${combatant.x},${combatant.y}`;
        return attackAffectedCellSet.has(key);
      })
      .map((combatant) => combatant.id);

    requestAction(activeActorId, selectedAction.action_type_cost, selectedAction.action_id, {
      target_ids: targetIds,
      template_origin: { x, y },
      ...(attackPreview?.template_projection?.direction ? { template_direction: attackPreview.template_projection.direction } : {}),
    });

    setActionHint(`Submitted ${selectedAction.action_id} at ${x},${y}.`);
    setSelectedActionId(null);
  };

  if (!isConnected) {
    return <div className="flex h-full items-center justify-center bg-slate-950 text-sm text-slate-300">Waiting for combat feed for campaign {campaignId}...</div>;
  }

  return (
    <section className="h-full w-full overflow-y-auto bg-slate-950 p-4 text-slate-100">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
        <header className="rounded-lg border border-slate-700 bg-slate-900 p-4">
          <h2 className="text-lg font-semibold text-cyan-300">Player Console</h2>
          <p className="mt-1 text-xs text-slate-400">Campaign {campaignId}</p>
          <p className="mt-2 text-xs text-slate-300">Owned actors: {ownedActors.length}</p>
          <p className="text-xs text-slate-400">DM-only presets are hidden in this view.</p>
        </header>

        <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
          <div className="mb-3 flex flex-wrap items-end gap-3">
            <label className="text-xs text-slate-300" htmlFor="player-owned-actor-select">
              Owned actor
            </label>
            <select
              id="player-owned-actor-select"
              value={activeActorId ?? ""}
              onChange={(event) => setSelectedActorId(event.target.value)}
              className="min-w-48 rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-slate-100"
              disabled={!hasOwnedActors}
            >
              {!hasOwnedActors && <option value="">No owned actor available</option>}
              {ownedActors.map((actor) => (
                <option key={actor.id} value={actor.id}>
                  {actor.public_name} ({actor.id})
                </option>
              ))}
            </select>
            <button
              type="button"
              className="rounded border border-slate-500 bg-slate-800 px-2 py-1 text-xs text-slate-100 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!activeActorId}
              onClick={() => {
                if (activeActorId) {
                  requestExecutableActions(activeActorId);
                }
              }}
            >
              Refresh actions
            </button>
            <button
              type="button"
              className="rounded border border-cyan-700 bg-cyan-950/40 px-2 py-1 text-xs text-cyan-200 hover:bg-cyan-900/60 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!activeActorId}
              onClick={() => {
                if (activeActorId) {
                  requestMovePreview(activeActorId);
                }
              }}
            >
              Request move preview
            </button>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-300">Movement Surface</h3>
              <p className="mb-2 text-xs text-slate-400">Press and hold your active token to request preview, then release on a highlighted cell to commit move.</p>
              <div
                className="grid gap-px overflow-auto rounded border border-slate-700 bg-slate-800 p-1"
                style={{
                  gridTemplateColumns: `repeat(${mapConfig.columns}, minmax(24px, 1fr))`,
                }}
              >
                {Array.from({ length: mapConfig.rows }).map((_, y) =>
                  Array.from({ length: mapConfig.columns }).map((__, x) => {
                    const key = `${x},${y}`;
                    const token = tokenByCell.get(key);
                    const isReachable = reachableCellSet.has(key);
                    const isAttackCell = attackEligibleCellSet.has(key);
                    const isAttackAffectedCell = attackAffectedCellSet.has(key);
                    const isOrigin = movementPreview?.origin.x === x && movementPreview?.origin.y === y;
                    const isActiveToken = token?.id === activeActorId;
                    const isEligibleTarget = token ? attackEligibleTargetSet.has(token.id) : false;
                    const hasTargetingSelection = Boolean(selectedAction);

                    return (
                      <button
                        key={key}
                        type="button"
                        className={`relative h-7 min-w-7 rounded-sm border text-[10px] transition ${
                          isEligibleTarget
                            ? "border-rose-500 bg-rose-900/60 text-rose-100"
                            : isAttackAffectedCell
                              ? "border-amber-500 bg-amber-900/55 text-amber-100"
                              : isAttackCell
                                ? "border-violet-500 bg-violet-900/45 text-violet-100"
                                : isReachable
                                  ? "border-cyan-500 bg-cyan-900/60 text-cyan-100"
                                  : isOrigin
                                    ? "border-amber-500 bg-amber-900/40 text-amber-100"
                                    : "border-slate-700 bg-slate-900/80 text-slate-500"
                        }`}
                        onPointerUp={() => {
                          if (hasTargetingSelection && selectedAction) {
                            if (selectedAction.targeting_mode === "aoe") {
                              commitAoeTemplateAction(x, y);
                              return;
                            }

                            if (token) {
                              commitTargetedAction(token.id);
                              return;
                            }

                            setActionHint("Select a valid target token.");
                            return;
                          }

                          commitMove(x, y);
                        }}
                      >
                        {token ? (
                          <span
                            className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-[9px] font-semibold ${
                              isEligibleTarget ? "bg-rose-500 text-slate-950" : isActiveToken ? "bg-cyan-500 text-slate-950" : "bg-slate-500 text-slate-950"
                            }`}
                            onPointerDown={() => startMoveDrag(token.id)}
                          >
                            {token.public_name.slice(0, 1).toUpperCase()}
                          </span>
                        ) : null}
                      </button>
                    );
                  }),
                )}
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-400">
                <span>Drag state: {draggingActorId ? `active (${draggingActorId})` : "idle"}</span>
                <span>Target mode: {selectedAction ? selectedAction.action_id : "off"}</span>
                <span>Reachable cells: {movementPreview?.reachable.length ?? 0}</span>
                <span>Eligible targets: {attackPreview?.eligible_target_ids.length ?? 0}</span>
                <span>AoE affected cells: {attackPreview?.template_projection?.affected_cells.length ?? 0}</span>
                <span>AoE shape: {attackPreview?.template_projection?.shape ?? "n/a"}</span>
                <span>Movement remaining: {movementPreview?.movement_remaining ?? activeActor?.movement_remaining ?? 0}</span>
                {draggingActorId && (
                  <button type="button" className="rounded border border-slate-500 px-2 py-0.5 text-xs text-slate-200 hover:bg-slate-700" onClick={() => setDraggingActorId(null)}>
                    Cancel drag
                  </button>
                )}
                {selectedAction && (
                  <button
                    type="button"
                    className="rounded border border-slate-500 px-2 py-0.5 text-xs text-slate-200 hover:bg-slate-700"
                    onClick={() => {
                      setSelectedActionId(null);
                      setActionHint("Cancelled target selection.");
                    }}
                  >
                    Cancel targeting
                  </button>
                )}
              </div>
            </div>

            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-300">Executable Actions</h3>
              {activeActorId ? <p className="mb-2 text-xs text-slate-400">Actor {activeActorId}</p> : <p className="mb-2 text-xs text-amber-300">Select an owned actor to load actions.</p>}
              <div className="space-y-2">
                {executableActions.length === 0 && <div className="rounded border border-slate-700 bg-slate-950 p-3 text-xs text-slate-400">No action snapshot yet. Use Refresh actions.</div>}
                {executableActions.map((action) => {
                  const isAvailable = action.is_available;

                  return (
                    <div key={action.action_id} className="rounded border border-slate-700 bg-slate-950 p-3">
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
                          disabled={!isAvailable || !activeActorId}
                          onClick={() => runAction(action.action_id, action.action_type_cost, action.targeting_mode)}
                          title={
                            !isAvailable
                              ? (action.unavailable_reason ?? "Unavailable")
                              : action.targeting_mode === "self"
                                ? "Execute now"
                                : action.targeting_mode === "aoe"
                                  ? "Request AoE projection and choose a template origin"
                                  : "Request preview and select target"
                          }
                        >
                          {action.targeting_mode === "self" ? "Execute" : "Target"}
                        </button>
                      </div>
                      {!isAvailable && <p className="mt-2 text-[11px] text-amber-300">Unavailable: {action.unavailable_reason ?? "unknown_reason"}</p>}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {actionHint && <div className="mt-3 rounded border border-cyan-800/60 bg-cyan-900/20 p-2 text-xs text-cyan-200">{actionHint}</div>}
        </div>

        {playerActionLabEnabled ? (
          <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
            <ActionCommandLab role="player" actorId={activeActorId} title="Action Command Lab (Player)" allowRawMode={false} />
          </div>
        ) : (
          <div className="rounded-lg border border-amber-600/50 bg-amber-700/10 p-4 text-xs text-amber-100">
            Player action lab is disabled. Enable VITE_FRONTEND_TESTING_PLAYER_ACTION_LAB=true to turn on frontendTesting.playerActionLab.
          </div>
        )}
      </div>
    </section>
  );
}
