import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AppNavbar } from '../components/shell/AppNavbar';
import { ViewContainer } from '../components/shell/ViewContainer';
import { AuthService } from '../lib/auth';
import { WebSocketManager } from '../lib/websocket';
import { ReactHostBridge } from '../lib/bridge';
import { QueryClient } from '@tanstack/react-query';
import { IHostBridge } from '@rpg/bridge';
import { config } from '../config';
import { logger } from '../lib/logger';

interface SessionRouteProps {
  auth: AuthService;
  ws: WebSocketManager;
  queryClient: QueryClient;
}

export const SessionRoute = ({ auth, ws, queryClient }: SessionRouteProps) => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [bridge, setBridge] = useState<IHostBridge | null>(null);
  const [user, setUser] = useState<any>(null); // Should be UserProfile
  const [role, setRole] = useState<string>('PLAYER');
  const [connection, setConnection] = useState(ws.state);

  useEffect(() => {
    const initBridge = async () => {
      logger.info('SessionRoute: initBridge called');
      try {
        if (config.useMocks) {
          logger.info('SessionRoute: Loading MockHostBridge');
          const { MockHostBridge } = await import('../../../player-view/src/mocks/MockHostBridge');
          const mockBridge = new MockHostBridge();
          setBridge(mockBridge);
          setConnection({ isConnected: true, latency: 0 });
          logger.info('SessionRoute: MockHostBridge initialized');
        } else {
          // Initialize Real Bridge
          logger.info('SessionRoute: Initializing Real Bridge');
          const newBridge = new ReactHostBridge(ws, queryClient, auth);
          setBridge(newBridge);

          // Connect WS
          const token = auth.getToken();
          if (id && token) {
            ws.connect(id, token);
          }
        }
      } catch (error) {
        logger.error('SessionRoute: Failed to initialize bridge', error);
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

    // Load User and determine role
    const loadUserAndRole = async () => {
      const u = await auth.getUser();
      if (u) {
        let currentRole = 'PLAYER'; // Default
        
        if (config.useMocks && id) {
           try {
             const { campaigns: mockCampaigns } = await import('../../../player-view/src/mocks/campaigns');
             const campaign = mockCampaigns.find((c: any) => c.id === id);
             if (campaign) {
               const member = campaign.members?.find((m: any) => m.userId === u.id);
               if (member) {
                 currentRole = member.role;
               }
             }
           } catch (e) {
             logger.error('SessionRoute: Failed to load mock campaigns', e);
           }
        }
        
        logger.info(`SessionRoute: User loaded: ${JSON.stringify(u)}`); 
        logger.info(`SessionRoute: Role determined: ${currentRole}`); 
        setUser(u);
        setRole(currentRole);
      } else {
        logger.warn('SessionRoute: No user found, redirecting to login');
        // If no user, we should probably redirect to login?
        // But let's check if we are just waiting for auth check?
        // auth.getUser() should resolve quickly.
        // If it returns null, we are not logged in.
        navigate('/');
      }
    };

    loadUserAndRole();
    
    return () => {
      if (!config.useMocks) {
          ws.disconnect();
          clearInterval(interval);
      }
    };
  }, [id, auth, ws, queryClient, navigate]);

  if (!bridge) return <div>Initializing...</div>;

  return (
    <div className="h-screen flex flex-col bg-background">
      <AppNavbar 
        user={user} 
        connection={connection} 
        onLogout={async () => {
            await auth.logout();
            navigate('/');
        }} 
      />
      <ViewContainer 
        viewType={role.toLowerCase() === 'dm' ? 'dm' : 'player'} 
        bridge={bridge} 
        campaignId={id || ''} 
      />
    </div>
  );
};
