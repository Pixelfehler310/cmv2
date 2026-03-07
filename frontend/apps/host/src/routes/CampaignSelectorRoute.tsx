import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AuthService } from "../lib/auth";
import { config } from "../config";
import { AppNavbar } from "../components/shell/AppNavbar";
import { CampaignList } from "@rpg/management-view";

interface Campaign {
  id: string;
  name: string;
  role: string;
  image?: string;
}

import { logger } from "../lib/logger";

interface Campaign {
  id: string;
  name: string;
  role: string;
  image?: string;
}

export const CampaignSelectorRoute = ({ auth }: { auth: AuthService }) => {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    auth.getUser().then(setUser);
    fetchCampaigns();
  }, []);

  const handleLogout = async () => {
    await auth.logout();
    navigate("/");
  };

  const fetchCampaigns = async () => {
    logger.info("CampaignSelectorRoute: fetchCampaigns called");
    try {
      if (config.useMocks) {
        logger.info("CampaignSelectorRoute: Using mocks");
        const { campaigns: mockCampaigns } = await import("../../../player-view/src/mocks/campaigns");

        // Get current user to determine roles
        const user = await auth.getUser();

        setCampaigns(
          mockCampaigns.map((c: any) => {
            // Find user in members list
            const member = c.members?.find((m: any) => m.userId === user?.id);
            const role = member ? member.role : "PLAYER"; // Default to PLAYER if not found

            return {
              ...c,
              role: role,
              image: c.image || "https://images.unsplash.com/photo-1599058945522-28d584b6f0ff?q=80&w=2669&auto=format&fit=crop",
            };
          }),
        );
        setLoading(false);
        return;
      }

      const token = auth.getToken();
      if (!token) {
        logger.warn("CampaignSelectorRoute: No token found");
        return;
      }

      const res = await fetch("/api/campaigns/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCampaigns(
          data.map((c: any) => ({
            ...c,
            image: "https://images.unsplash.com/photo-1599058945522-28d584b6f0ff?q=80&w=2669&auto=format&fit=crop", // Placeholder
          })),
        );
      } else {
        logger.warn(`CampaignSelectorRoute: Failed to fetch campaigns, status: ${res.status}`);
      }
    } catch (e) {
      logger.error("Failed to fetch campaigns", e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    const name = prompt("Campaign Name:");
    if (!name) return;

    logger.info(`CampaignSelectorRoute: Creating campaign "${name}"`);
    try {
      const token = auth.getToken();
      const res = await fetch("/api/campaigns/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name }),
      });

      if (res.ok) {
        logger.info("CampaignSelectorRoute: Campaign created successfully");
        fetchCampaigns();
      } else {
        logger.warn(`CampaignSelectorRoute: Failed to create campaign, status: ${res.status}`);
      }
    } catch (e) {
      logger.error("Failed to create campaign", e);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading realms...</div>;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <AppNavbar user={user} connection={{ isConnected: true, latency: 0 }} onLogout={handleLogout} />
      <div className="p-8 flex-1 flex flex-col items-center">
        {/* Render the ugly walking skeleton CRUD list temporarily */}
        <div className="w-full max-w-4xl bg-white rounded shadow text-black mb-8 p-4">
          <h2 className="text-red-500 font-bold mb-4 uppercase">Walking Skeleton Phase 1.5</h2>
          <CampaignList />
        </div>

        <div className="max-w-5xl mx-auto w-full">
          <h1 className="text-3xl font-heading text-primary mb-8">Select Campaign</h1>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map((c) => (
              <div
                key={c.id}
                onClick={() => navigate(`/session/${c.id}`)}
                className="group relative aspect-video card card-interactive card-gradient-accent gradient-combo-twilight overflow-hidden cursor-pointer"
              >
                <img src={c.image} alt={c.name} className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 to-transparent" />

                <div className="absolute bottom-0 left-0 p-4">
                  <h3 className="text-xl font-bold text-white">{c.name}</h3>
                  <span className="text-xs uppercase tracking-wider text-primary font-medium">{c.role}</span>
                </div>
              </div>
            ))}

            {/* Create New */}
            <div onClick={handleCreate} className="aspect-video card hover-lift border-2 border-dashed border-muted flex flex-col items-center justify-center cursor-pointer">
              <span className="text-4xl mb-2 text-muted-foreground">+</span>
              <span className="text-muted-foreground font-medium">Create New</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
