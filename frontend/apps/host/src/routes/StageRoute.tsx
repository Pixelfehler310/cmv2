import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { WsClient } from "@rpg/bridge";
import { logger } from "../lib/logger";
import { config } from "../config";
import { AuthService } from "../lib/auth";

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

  return (
    <div className="h-screen w-screen bg-black flex flex-col p-4">
      <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
        <h1 className="text-2xl text-white font-bold tracking-widest uppercase">Stage View (Player)</h1>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${connection.isConnected ? "bg-green-500" : "bg-red-500"}`} />
          <span className="text-gray-400 text-sm font-mono">{connection.isConnected ? "CONNECTED" : "OFFLINE"}</span>
        </div>
      </div>

      <div className="flex-1 bg-gray-900 border border-gray-700 rounded-lg overflow-auto p-4 text-green-400 font-mono text-sm max-h-full">
        {localState ? <pre>{JSON.stringify(localState, null, 2)}</pre> : <div className="text-gray-500 italic animate-pulse">Awaiting stage hydration...</div>}
      </div>
    </div>
  );
};
