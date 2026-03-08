import { useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { AppNavbar } from "./AppNavbar";
import { AuthService } from "../../lib/auth";
import { WsClient } from "@rpg/bridge";
import { UserProfile } from "@rpg/bridge";
import { config } from "../../config";

export const WorkspaceLayout = ({ auth, ws }: { auth: AuthService; ws?: WsClient }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [connection, setConnection] = useState(ws ? ws.state : { isConnected: false, latency: 0 });

  useEffect(() => {
    auth.getUser().then(setUser);

    let interval: NodeJS.Timeout;
    if (ws && !config.useMocks) {
      interval = setInterval(() => {
        setConnection({ ...ws.state });
      }, 1000);
    } else if (config.useMocks) {
      setConnection({ isConnected: true, latency: 0 });
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [auth, ws]);

  const handleLogout = async () => {
    await auth.logout();
    navigate("/");
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <AppNavbar user={user} connection={connection} onLogout={handleLogout} />
      <div className="flex-1 overflow-auto">
        <Outlet />
      </div>
    </div>
  );
};
