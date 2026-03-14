import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { WsClient } from "@rpg/bridge";
import { logger } from "../lib/logger";
import { config } from "../config";
import { AuthService } from "../lib/auth";
import { StageLayout, StageCartographer, PublicCombatLog, useStageFilter } from "@rpg/dm-view";

interface StageRouteProps {
  auth: AuthService;
}

function applyStageDelta(prev: any, data: any): any {
  if (!prev) {
    return prev;
  }

  if (data.type === "actor_moved") {
    const actorId = data.payload?.actor_id;
    const position = data.payload?.position;
    if (!actorId || !position) {
      return prev;
    }

    return {
      ...prev,
      combatants: (prev.combatants ?? []).map((c: any) =>
        c.id === actorId
          ? {
              ...c,
              position: { ...c.position, ...position },
              x: position.x ?? c.x,
              y: position.y ?? c.y,
            }
          : c,
      ),
      map: {
        ...prev.map,
        tokens: (() => {
          const tokens = prev.map?.tokens ?? [];
          const exists = tokens.some((t: any) => t.actor_id === actorId);
          if (exists) {
            return tokens.map((t: any) => (t.actor_id === actorId ? { ...t, position: { ...t.position, ...position } } : t));
          }
          return [...tokens, { actor_id: actorId, position }];
        })(),
      },
    };
  }

  if (data.type === "actor_added") {
    const actor = data.payload?.actor;
    const token = data.payload?.token;
    if (!actor?.id) {
      return prev;
    }

    return {
      ...prev,
      combatants: (prev.combatants ?? []).some((c: any) => c.id === actor.id) ? prev.combatants : [...(prev.combatants ?? []), actor],
      map: {
        ...prev.map,
        tokens: token ? ((prev.map?.tokens ?? []).some((t: any) => t.actor_id === token.actor_id) ? prev.map.tokens : [...(prev.map?.tokens ?? []), token]) : (prev.map?.tokens ?? []),
      },
    };
  }

  if (data.type === "actor_removed") {
    const actorId = data.payload?.actor_id;
    if (!actorId) {
      return prev;
    }

    return {
      ...prev,
      combatants: (prev.combatants ?? []).filter((c: any) => c.id !== actorId),
      map: {
        ...prev.map,
        tokens: (prev.map?.tokens ?? []).filter((t: any) => t.actor_id !== actorId),
      },
    };
  }

  if (data.type === "actor_damaged" || data.type === "actor_healed" || data.type === "actor_died") {
    const actorId = data.payload?.actor_id;
    if (!actorId) {
      return prev;
    }

    return {
      ...prev,
      combatants: (prev.combatants ?? []).map((c: any) =>
        c.id === actorId
          ? {
              ...c,
              current_hp: data.type === "actor_died" ? 0 : (data.payload?.new_hp ?? c.current_hp),
              hp_current: data.type === "actor_died" ? 0 : (data.payload?.new_hp ?? c.hp_current),
            }
          : c,
      ),
    };
  }

  if (data.type === "turn_advanced") {
    const activeActorId = data.payload?.active_actor_id;
    const combatants = prev.combatants ?? [];
    const nextActiveIndex = combatants.findIndex((c: any) => c.id === activeActorId);

    return {
      ...prev,
      round_number: data.payload?.round ?? prev.round_number,
      active_index: nextActiveIndex >= 0 ? nextActiveIndex : prev.active_index,
    };
  }

  return prev;
}

export const StageRoute = ({ auth }: StageRouteProps) => {
  const { id } = useParams();
  const [localState, setLocalState] = useState<any>(null);
  const [connection, setConnection] = useState({ isConnected: false, latency: 0 });

  useEffect(() => {
    // Create an entirely isolated WsClient for the Stage View
    const stageWs = new WsClient(config.wsUrl);

    // Connect WS using a simplified "Observer/Stage" perspective.
    // In a real scenario, this Token would be specifically vended for the stage display
    // or the URL query param would carry ?role=observer.
    // We append the role to the route locally just for backend WebSocket parsing if needed,
    // though our backend specifically identifies `stage_sync` stripping from the system.
    const token = auth.getToken();

    if (id && token) {
      stageWs.connect(id, token, "spectator");

      stageWs.onMessage((data) => {
        if (data.type === "state_sync" || data.type === "state_update") {
          logger.info("[StageRoute] Received state payload:", data.payload);
          // Only update local state, not the Zustand store, so it doesn't leak into DM view
          setLocalState((prev: any) => ({ ...prev, ...data.payload }));
          return;
        }

        setLocalState((prev: any) => applyStageDelta(prev, data));
      });
    }

    const interval = setInterval(() => {
      setConnection({ ...stageWs.state });
    }, 1000);

    return () => {
      stageWs.disconnect();
      clearInterval(interval);
    };
  }, [id, auth]);

  // Sanitize the raw state for player view
  const stageState = useStageFilter(localState);

  return (
    <StageLayout>
      <StageCartographer tokens={stageState.tokens} mapUrl={stageState.mapUrl} />
      <PublicCombatLog logs={stageState.logs} />

      <div className="absolute top-2 right-2 flex items-center space-x-2 z-50 opacity-50 hover:opacity-100 transition-opacity bg-black/50 p-1 rounded">
        <div className={`w-2 h-2 rounded-full ${connection.isConnected ? "bg-green-500" : "bg-red-500"}`} />
        <span className="text-gray-400 text-xs font-mono">{connection.isConnected ? "CONN" : "OFF"}</span>
      </div>
    </StageLayout>
  );
};
