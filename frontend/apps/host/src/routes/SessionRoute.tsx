import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { AppNavbar } from '../components/shell/AppNavbar';
import { ViewContainer } from '../components/shell/ViewContainer';
import { AuthService } from '../lib/auth';
import { WebSocketManager } from '../lib/websocket';
import { ReactHostBridge } from '../lib/bridge';
import { QueryClient } from '@tanstack/react-query';
import { IHostBridge } from '@rpg/bridge';
import { config } from '../config';

interface SessionRouteProps {
  auth: AuthService;
  ws: WebSocketManager;
  queryClient: QueryClient;
}

export const SessionRoute = ({ auth, ws, queryClient }: SessionRouteProps) => {
  const { id } = useParams();
  const [bridge, setBridge] = useState<IHostBridge | null>(null);
  const [user, setUser] = useState<any>(null); // Should be UserProfile
  const [connection, setConnection] = useState(ws.state);

  useEffect(() => {
    const initBridge = async () => {
      if (config.useMocks) {
        const { MockHostBridge } = await import('../../../player-view/src/mocks/MockHostBridge');
        const mockBridge = new MockHostBridge();
        setBridge(mockBridge);
        setConnection({ isConnected: true, latency: 0 });
        // Mock user
        setUser({ username: 'Mock User', id: 'mock-1', roles: ['DM'] });
      } else {
        // Initialize Real Bridge
        const newBridge = new ReactHostBridge(ws, queryClient, auth);
        setBridge(newBridge);

        // Connect WS
        const token = auth.getToken();
        if (id && token) {
          ws.connect(id, token);
        }
      }
    };

    initBridge();

    // Sync connection state (only for real WS)
    let interval: NodeJS.Timeout;
    if (!config.useMocks) {
        interval = setInterval(() => {
          setConnection({ ...ws.state });
        }, 1000);
    }

    // Load User (only for real auth)
    if (!config.useMocks) {
        auth.getUser().then(setUser);
    }

    return () => {
      if (!config.useMocks) {
          ws.disconnect();
          clearInterval(interval);
      }
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
        viewType={user?.roles?.includes('player') ? 'player' : 'dm'} 
        bridge={bridge} 
        campaignId={id || ''} 
      />
    </div>
  );
};
