import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { WebSocketProvider } from "./contexts/WebSocketContext";
import { EventBusProvider } from "./contexts/EventBusContext";
import { ActionDispatchProvider } from "./contexts/ActionDispatchContext";
import { ViewProvider } from "./contexts/ViewContext";
import { AppNavbar } from "./components/AppNavbar";
import { ViewContainer } from "./components/ViewContainer";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { useWebSocketEvents } from "./hooks/useWebSocketEvents";

function AppContent() {
  const { token, isAuthenticated } = useAuth();
  useWebSocketEvents();

  if (!isAuthenticated) {
    return (
      <div className="h-screen w-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold">Open RPG Engine</h1>
          <p className="text-muted-foreground">Please log in to continue</p>
          {/* TODO: Add login form */}
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col">
      <AppNavbar />
      <main className="flex-1 relative overflow-hidden">
        <ErrorBoundary>
          <ViewContainer />
        </ErrorBoundary>
      </main>
    </div>
  );
}

function AppWithProviders() {
  const { token } = useAuth();

  return (
    <EventBusProvider>
      <WebSocketProvider token={token}>
        <ActionDispatchProvider>
          <ViewProvider>
            <Routes>
              <Route path="/" element={<AppContent />} />
              <Route path="/campaigns" element={<AppContent />} />
              <Route path="/campaigns/:id" element={<AppContent />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ViewProvider>
        </ActionDispatchProvider>
      </WebSocketProvider>
    </EventBusProvider>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <AuthProvider>
          <AppWithProviders />
        </AuthProvider>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
