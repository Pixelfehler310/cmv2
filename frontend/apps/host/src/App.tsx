import React, { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { wsManager } from "./lib/websocket/WebSocketManager";
import { Header } from "./components/Header";
import { Workbench } from "./layout/Workbench";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { useWebSocketEvents } from "./hooks/useWebSocketEvents";

function AppContent() {
  const { token, isAuthenticated } = useAuth();
  useWebSocketEvents();

  useEffect(() => {
    // Connect WebSocket when authenticated
    if (isAuthenticated && token) {
      wsManager.connect(token).catch((error) => {
        console.error('Failed to connect WebSocket:', error);
      });
    }

    return () => {
      // Disconnect on unmount
      wsManager.disconnect();
    };
  }, [isAuthenticated, token]);

  return (
    <div className="h-screen w-screen flex flex-col">
      <Header />
      <main className="flex-1 relative overflow-hidden">
        <ErrorBoundary>
          <Workbench />
        </ErrorBoundary>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ErrorBoundary>
          <AppContent />
        </ErrorBoundary>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
