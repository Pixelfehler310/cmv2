import { useEffect, useMemo, useState } from "react";
import type { IHostBridge } from "@rpg/bridge";
import { ActionCommandLab, useCombatStore } from "@rpg/shared";

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

  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [selectedActorId, setSelectedActorId] = useState<string>("");

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

        {playerActionLabEnabled ? (
          <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
            <div className="mb-3 flex flex-wrap items-end gap-3">
              <label className="text-xs text-slate-300" htmlFor="player-owned-actor-select">
                Owned actor default
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
            </div>

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
