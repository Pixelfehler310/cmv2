import { useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { LoginRoute } from "./routes/LoginRoute";
import { CampaignSelectorRoute } from "./routes/CampaignSelectorRoute";
import { SessionRoute } from "./routes/SessionRoute";
import { StageRoute } from "./routes/StageRoute";
import { ContentRoute } from "./routes/ContentRoute";
import { StoryGraphRoute } from "./routes/StoryGraphRoute";
import { WorkspaceLayout } from "./components/shell/WorkspaceLayout";
import { AuthService } from "./lib/auth";
import { WsClient } from "@rpg/bridge";

import { logger } from "./lib/logger";

import { config } from "./config";

// Initialize Core Services
const queryClient = new QueryClient();
const authService = new AuthService();
const wsManager = new WsClient(config.wsUrl);

const RouteLogger = () => {
  const location = useLocation();

  useEffect(() => {
    logger.info(`Route changed to: ${location.pathname}${location.search}`);
  }, [location]);

  return null;
};

function App() {
  useEffect(() => {
    if (!config.useMocks) {
      logger.info("VITE_USE_MOCKS is false; skipping seed import call.");
      return;
    }

    const normalizedApiUrl = config.apiUrl.replace(/\/$/, "");
    const seedPath = normalizedApiUrl === "/api"
      ? "/api/dev/load-seeds"
      : normalizedApiUrl.endsWith("/api")
        ? "/dev/load-seeds"
        : "/api/dev/load-seeds";
    const seedUrl = `${normalizedApiUrl}${seedPath}`;
    logger.info(`VITE_USE_MOCKS is true; calling seed import endpoint: ${seedUrl}`);

    void fetch(seedUrl, { method: "POST" })
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          logger.error(
            `Seed import failed: ${response.status} ${response.statusText}`,
            payload
          );
          return;
        }
        logger.info("Seed import response", payload);
      })
      .catch((error) => {
        logger.error("Seed import request failed", error);
      });
  }, []);

  logger.info("App starting...");
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <RouteLogger />
        <div className="theme-vtt min-h-screen bg-background text-foreground font-sans antialiased flex flex-col">
          <Routes>
            <Route path="/" element={<LoginRoute auth={authService} />} />
            <Route element={<WorkspaceLayout auth={authService} ws={wsManager} />}>
              <Route path="/campaigns" element={<CampaignSelectorRoute />} />
              <Route path="/content" element={<ContentRoute />} />
              <Route path="/campaigns/:id/story" element={<StoryGraphRoute />} />
              <Route path="/session/:id" element={<SessionRoute auth={authService} ws={wsManager} queryClient={queryClient} />} />
            </Route>
            <Route path="/stage/:id" element={<StageRoute auth={authService} />} />
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
