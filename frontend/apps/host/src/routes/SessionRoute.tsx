import { useEffect, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { ViewContainer } from "../components/shell/ViewContainer";
import { AuthService } from "../lib/auth";
import { WsClient } from "@rpg/bridge";
import { ReactHostBridge } from "../lib/bridge";
import { QueryClient } from "@tanstack/react-query";
import { IHostBridge } from "@rpg/bridge";
import { useCombatStore } from "@rpg/shared";
import { config } from "../config";
import { logger } from "../lib/logger";

interface SessionRouteProps {
  auth: AuthService;
  ws: WsClient;
  queryClient: QueryClient;
}

export const SessionRoute = ({ auth, ws, queryClient }: SessionRouteProps) => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const [bridge, setBridge] = useState<IHostBridge | null>(null);
  const [user, setUser] = useState<any>(null); // Should be UserProfile
  const [role, setRole] = useState<string>(config.useMocks ? "PLAYER" : "DM");
  const [connection, setConnection] = useState(ws.state);

  const requestedView = (searchParams.get("view") ?? "").trim().toLowerCase();
  const requestedImpersonationUserId = (searchParams.get("as_user_id") ?? "").trim();
  const requestedSceneId = (searchParams.get("scene_id") ?? "").trim();
  const requestedEncounterId = (searchParams.get("encounter_id") ?? "").trim();

  useEffect(() => {
    let currentStoreRole: "dm" | "observer" = config.useMocks ? "observer" : "dm";
    let unsubscribeBridgeRecv: (() => void) | null = null;

    const initBridge = async () => {
      logger.info("SessionRoute: initBridge called");
      try {
        if (config.useMocks) {
          logger.info("SessionRoute: Loading MockHostBridge");
          const { MockHostBridge } = await import("../../../player-view/src/mocks/MockHostBridge");
          const mockBridge = new MockHostBridge();
          setBridge(mockBridge);
          setConnection({ isConnected: true, latency: 0 });
          useCombatStore.getState().setConnectionStatus(true, "observer");
          logger.info("SessionRoute: MockHostBridge initialized");
        } else {
          // Initialize Real Bridge
          logger.info("SessionRoute: Initializing Real Bridge");
          const newBridge = new ReactHostBridge(ws, queryClient, auth);
          setBridge(newBridge);

          useCombatStore
            .getState()
            .setActionDispatcher((commandOrType, payload) =>
              typeof commandOrType === "string" ? newBridge.actions.dispatch(commandOrType, payload ?? {}) : newBridge.actions.dispatch(commandOrType),
            );
          unsubscribeBridgeRecv = newBridge.events.on("ws:recv", (data) => {
            useCombatStore.getState().ingestEnvelope(data);
          });

          // Connect WS
          const token = auth.getToken();
          if (id && token) {
            useCombatStore.getState().setSelectedContext(id, requestedSceneId || null, requestedEncounterId || null);
            ws.connect(id, token, "dm");
          }
        }
      } catch (error) {
        logger.error("SessionRoute: Failed to initialize bridge", error);
      }
    };

    initBridge();

    // Sync connection state (only for real WS)
    let interval: NodeJS.Timeout;
    if (!config.useMocks) {
      interval = setInterval(() => {
        const nextConnection = { ...ws.state };
        setConnection(nextConnection);
        useCombatStore.getState().setConnectionStatus(nextConnection.isConnected, currentStoreRole);
      }, 1000);
    }

    // Load User and determine role
    const loadUserAndRole = async () => {
      const u = await auth.getUser();
      if (u) {
        let currentRole = config.useMocks ? "PLAYER" : "DM";

        if (config.useMocks && id) {
          try {
            const { campaigns: mockCampaigns } = await import("../../../player-view/src/mocks/campaigns");
            const campaign = mockCampaigns.find((c: any) => c.id === id);
            if (campaign) {
              const member = campaign.members?.find((m: any) => m.userId === u.id);
              if (member) {
                currentRole = member.role;
              }
            }
          } catch (e) {
            logger.error("SessionRoute: Failed to load mock campaigns", e);
          }
        }

        logger.info(`SessionRoute: User loaded: ${JSON.stringify(u)}`);
        logger.info(`SessionRoute: Role determined: ${currentRole}`);

        const canForcePlayerView = currentRole.toLowerCase() === "dm" && requestedView === "player";
        const effectiveRole = canForcePlayerView ? "PLAYER" : currentRole;

        currentStoreRole = effectiveRole.toLowerCase() === "dm" ? "dm" : "observer";
        setUser(u);
        setRole(effectiveRole);
      } else {
        logger.warn("SessionRoute: No user found, redirecting to login");
        // If no user, we should probably redirect to login?
        // But let's check if we are just waiting for auth check?
        // auth.getUser() should resolve quickly.
        // If it returns null, we are not logged in.
        navigate("/");
      }
    };

    loadUserAndRole();

    return () => {
      if (unsubscribeBridgeRecv) {
        unsubscribeBridgeRecv();
      }
      if (!config.useMocks) {
        clearInterval(interval);
      }
      useCombatStore.getState().setActionDispatcher(null);
      useCombatStore.getState().setConnectionStatus(false);
      ws.disconnect();
    };
  }, [id, auth, ws, queryClient, navigate, requestedView, requestedSceneId, requestedEncounterId]);

  if (!bridge) return <div>Initializing...</div>;

  return (
    <div className="h-full flex flex-col bg-background">
      <ViewContainer
        viewType={role.toLowerCase() === "dm" ? "dm" : "player"}
        bridge={bridge}
        campaignId={id || ""}
        playerImpersonationUserId={role.toLowerCase() === "player" && requestedImpersonationUserId.length > 0 ? requestedImpersonationUserId : null}
      />
    </div>
  );
};
