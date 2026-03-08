import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

interface Campaign {
  id: string;
  name: string;
  description?: string;
  role?: string;
}

export const CampaignGrid = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [newCampaignName, setNewCampaignName] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("civic_auth_token");
      const res = await fetch("/api/campaigns", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch campaigns");
      const data = await res.json();
      setCampaigns(data);
    } catch (err: any) {
      setError(err.message);
      // Fallback for visual testing if api is down
      setCampaigns([
        { id: "1", name: "Curse of Strahd", description: "Vampire hunting in Barovia." },
        { id: "2", name: "Lost Mine of Phandelver", description: "Starter adventure." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCampaignName.trim()) return;

    try {
      const token = localStorage.getItem("civic_auth_token");
      const res = await fetch("/api/campaigns", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: newCampaignName, description: "A new adventure begins..." }),
      });

      if (!res.ok) throw new Error("Failed to create campaign");

      setNewCampaignName("");
      fetchCampaigns();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-heading text-foreground">Your Campaigns</h2>
          <p className="text-muted-foreground text-sm">Manage your active adventures and worlds.</p>
        </div>
        <form onSubmit={handleCreate} className="flex gap-2">
          <input type="text" value={newCampaignName} onChange={(e) => setNewCampaignName(e.target.value)} placeholder="New Campaign Name" className="input w-64" />
          <button type="submit" className="btn btn-primary gradient-quest animate-boing-active">
            Create
          </button>
        </form>
      </div>

      {error && <div className="p-4 mb-6 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm">{error}</div>}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card h-48 animate-pulse bg-surface-100"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campaigns.map((c) => (
            <div
              key={c.id}
              onClick={() => navigate(`/campaigns/${c.id}/story`)}
              className="card card-interactive bg-surface-100 hover:scale-[1.02] transition-transform p-6 flex flex-col cursor-pointer border-t-4 border-t-transparent hover:border-t-primary"
            >
              <div className="flex-1">
                <h3 className="text-xl font-bold text-foreground mb-2">{c.name}</h3>
                <p className="text-muted-foreground text-sm line-clamp-2">{c.description || "No description provided."}</p>
              </div>
              <div className="mt-4 pt-4 border-t border-border flex justify-between items-center">
                <span className="text-xs font-medium text-muted-foreground truncate flex-1">ID: {c.id}</span>
                <span className="text-xs px-2 py-1 rounded-full gradient-vtt text-white font-bold ml-2">Active</span>
              </div>
            </div>
          ))}
          {campaigns.length === 0 && (
            <div className="col-span-full p-12 text-center rounded-2xl border-2 border-dashed border-border text-muted-foreground">No campaigns found. Create one to get started!</div>
          )}
        </div>
      )}
    </div>
  );
};
