import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { AppNavbar } from '../components/shell/AppNavbar';
import { ViewContainer } from '../components/shell/ViewContainer';
import { AuthService } from '../lib/auth';
import { WebSocketManager } from '../lib/websocket';
import { ReactHostBridge } from '../lib/bridge';
import { QueryClient } from '@tanstack/react-query';

interface SessionRouteProps {
  auth: AuthService;
  ws: WebSocketManager;
  queryClient: QueryClient;
}

export const SessionRoute = ({ auth, ws, queryClient }: SessionRouteProps) => {
  const { id } = useParams();
  const [bridge, setBridge] = useState<ReactHostBridge | null>(null);
  const [user, setUser] = useState<any>(null); // Should be UserProfile
  const [connection, setConnection] = useState(ws.state);

  useEffect(() => {
    // Initialize Bridge
    const newBridge = new ReactHostBridge(ws, queryClient, auth);
    setBridge(newBridge);

    // Connect WS
    const token = auth.getToken();
    if (id && token) {
      ws.connect(id, token);
    }

    // Sync connection state
    const interval = setInterval(() => {
      setConnection({ ...ws.state });
    }, 1000);

    // Load User
    auth.getUser().then(setUser);

    return () => {
      ws.disconnect();
      clearInterval(interval);
    };
  }, [id, auth, ws, queryClient]);

  if (!bridge) return <div>Initializing...</div>;

  return (
    <div className="h-screen flex flex-col bg-background">
      <AppNavbar 
        user={user} 
        connection={connection} 
        onLogout={() => auth.logout()} 
      />
      <ViewContainer 
        viewType="dm" // Hardcoded for now, logic should determine this
        bridge={bridge} 
        campaignId={id || ''} 
      />
    </div>
  );
};
