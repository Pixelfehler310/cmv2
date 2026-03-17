import { useEffect, useMemo, useState } from "react";
import type { IHostBridge } from "@rpg/bridge";
import { ActionCommandLab, ContractActionSurface, selectMovementPreviewForActor, selectReachableCellSetForActor, useCombatStore } from "@rpg/shared";

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
  const requestMovePreview = useCombatStore((state) => state.requestMovePreview);
  const moveToken = useCombatStore((state) => state.moveToken);
  const latestDenied = useCombatStore((state) => state.latestDenied);

  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [selectedActorId, setSelectedActorId] = useState<string>("");
  const [draggingActorId, setDraggingActorId] = useState<string | null>(null);
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

  const movementPreview = useCombatStore((state) => selectMovementPreviewForActor(state, activeActorId));
  const reachableCellSet = useCombatStore((state) => selectReachableCellSetForActor(state, activeActorId));

  useEffect(() => {
    if (!movementPreview) {
      setDraggingActorId(null);
    }
  }, [movementPreview]);

  useEffect(() => {
    if (!latestDenied) {
      return;
    }

    if (latestDenied.type === "command_denied") {
      setDraggingActorId(null);
    }

    setActionHint(latestDenied.message ?? `Denied (${latestDenied.reasonCode}).`);
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
                    const isOrigin = movementPreview?.origin.x === x && movementPreview?.origin.y === y;
                    const isActiveToken = token?.id === activeActorId;

                    return (
                      <button
                        key={key}
                        type="button"
                        className={`relative h-7 min-w-7 rounded-sm border text-[10px] transition ${
                          isReachable
                            ? "border-cyan-500 bg-cyan-900/60 text-cyan-100"
                            : isOrigin
                              ? "border-amber-500 bg-amber-900/40 text-amber-100"
                              : "border-slate-700 bg-slate-900/80 text-slate-500"
                        }`}
                        onPointerUp={() => {
                          commitMove(x, y);
                        }}
                      >
                        {token ? (
                          <span
                            className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-[9px] font-semibold ${
                              isActiveToken ? "bg-cyan-500 text-slate-950" : "bg-slate-500 text-slate-950"
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
                <span>Reachable cells: {movementPreview?.reachable.length ?? 0}</span>
                <span>Movement remaining: {movementPreview?.movement_remaining ?? activeActor?.movement_remaining ?? 0}</span>
                {draggingActorId && (
                  <button type="button" className="rounded border border-slate-500 px-2 py-0.5 text-xs text-slate-200 hover:bg-slate-700" onClick={() => setDraggingActorId(null)}>
                    Cancel drag
                  </button>
                )}
              </div>
            </div>

            <ContractActionSurface
              actorId={activeActorId}
              actorName={activeActor?.public_name ?? null}
              actorOwnerUserId={currentUserId}
              identityBadgeLabel={currentUserId ? `player:${currentUserId}` : "player"}
              emptyActorMessage="Select an owned actor to load actions."
            />
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
