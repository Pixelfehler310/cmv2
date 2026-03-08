import { useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { LoginRoute } from "./routes/LoginRoute";
import { CampaignSelectorRoute } from "./routes/CampaignSelectorRoute";
import { SessionRoute } from "./routes/SessionRoute";
import { StageRoute } from "./routes/StageRoute";
import { ContentRoute } from "./routes/ContentRoute";
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
