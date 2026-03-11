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
      stageWs.connect(id, token);

      stageWs.onMessage((data) => {
        if (data.type === "state_sync" || data.type === "state_update") {
          logger.info("[StageRoute] Received state payload:", data.payload);
          // Only update local state, not the Zustand store, so it doesn't leak into DM view
          setLocalState((prev: any) => ({ ...prev, ...data.payload }));
        }
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
