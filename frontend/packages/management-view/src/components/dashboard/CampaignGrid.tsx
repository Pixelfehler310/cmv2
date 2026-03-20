import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

interface Campaign {
  id: string;
  name: string;
  description?: string;
  role?: string;
  members?: Array<{ user_id?: string; role?: string }>;
  characters?: Array<{ id?: string; player_name?: string | null; owner_user_id?: string | null }>;
}

const PLAYER_PICKER_RECENT_USERS_KEY = "campaign_player_picker_recent_users";

export const CampaignGrid = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [newCampaignName, setNewCampaignName] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [playerPickerCampaign, setPlayerPickerCampaign] = useState<Campaign | null>(null);
  const [playerPickerSelection, setPlayerPickerSelection] = useState<string>("");
  const [playerPickerCustomUserId, setPlayerPickerCustomUserId] = useState<string>("");
  const [recentPlayerUserIds, setRecentPlayerUserIds] = useState<string[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(PLAYER_PICKER_RECENT_USERS_KEY);
      if (!raw) {
        setRecentPlayerUserIds([]);
        return;
      }

      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) {
        setRecentPlayerUserIds([]);
        return;
      }

      const sanitized = parsed
        .filter((entry): entry is string => typeof entry === "string")
        .map((entry) => entry.trim())
        .filter((entry) => entry.length > 0)
        .slice(0, 12);
      setRecentPlayerUserIds(sanitized);
    } catch {
      setRecentPlayerUserIds([]);
    }
  }, []);

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

  const getPossiblePlayersForCampaign = (campaign: Campaign): string[] => {
    const fromMembers = (campaign.members ?? []).map((member) => (member.user_id ?? "").trim());
    const fromCharacterOwners = (campaign.characters ?? []).map((character) => (character.owner_user_id ?? "").trim());
    const fromCharacterPlayerNames = (campaign.characters ?? []).map((character) => (character.player_name ?? "").trim());

    return Array.from(new Set([...fromMembers, ...fromCharacterOwners, ...fromCharacterPlayerNames, ...recentPlayerUserIds].filter((userId) => userId.length > 0))).sort((a, b) => a.localeCompare(b));
  };

  const rememberRecentUserId = (userId: string): void => {
    const normalized = userId.trim();
    if (!normalized) {
      return;
    }

    const merged = Array.from(new Set([normalized, ...recentPlayerUserIds])).slice(0, 12);
    setRecentPlayerUserIds(merged);
    try {
      window.localStorage.setItem(PLAYER_PICKER_RECENT_USERS_KEY, JSON.stringify(merged));
    } catch {
      // Ignore localStorage failures and continue with runtime state only.
    }
  };

  const openPlayerPicker = (campaign: Campaign): void => {
    setPlayerPickerCampaign(campaign);
    setPlayerPickerSelection("");
    setPlayerPickerCustomUserId("");
  };

  const closePlayerPicker = (): void => {
    setPlayerPickerCampaign(null);
    setPlayerPickerSelection("");
    setPlayerPickerCustomUserId("");
  };

  const resolvePickedPlayerUserId = (): string => {
    const custom = playerPickerCustomUserId.trim();
    if (custom.length > 0) {
      return custom;
    }

    return playerPickerSelection.trim();
  };

  const launchPlayerView = (target: "new-tab" | "same-tab"): void => {
    if (!playerPickerCampaign) {
      return;
    }

    const selectedUserId = resolvePickedPlayerUserId();
    const query = new URLSearchParams({ view: "player" });
    if (selectedUserId.length > 0) {
      query.set("as_user_id", selectedUserId);
      rememberRecentUserId(selectedUserId);
    }

    const url = `/session/${encodeURIComponent(playerPickerCampaign.id)}?${query.toString()}`;
    if (target === "new-tab") {
      window.open(url, "_blank", "noopener,noreferrer");
      closePlayerPicker();
      return;
    }

    closePlayerPicker();
    navigate(url);
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
            <div key={c.id} className="card bg-surface-100 p-6 flex flex-col border-t-4 border-t-transparent hover:border-t-primary transition-colors">
              <div className="flex-1 mb-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-xl font-bold text-foreground">{c.name}</h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full gradient-vtt text-white font-bold">Active</span>
                </div>
                <p className="text-muted-foreground text-sm line-clamp-2">{c.description || "No description provided."}</p>
              </div>
              <div className="mt-auto pt-4 border-t border-border flex flex-col gap-3">
                <div className="flex gap-2">
                  <button
                    onClick={() => navigate(`/campaigns/${c.id}/story`)}
                    className="flex-1 py-2 px-3 rounded text-sm font-medium bg-surface-200 hover:bg-surface-300 text-foreground transition-colors border border-border"
                  >
                    Edit (StoryGraph)
                  </button>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => window.open(`/session/${c.id}`, "_blank")}
                    className="flex-1 py-2 px-3 rounded text-sm font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-[0_0_15px_rgba(var(--color-primary),0.3)]"
                    title="Launch DM Podium"
                  >
                    Play (DM)
                  </button>
                  <button
                    onClick={() => window.open(`/stage/${c.id}`, "_blank")}
                    className="flex-1 py-2 px-3 rounded text-sm font-bold bg-green-600 text-white hover:bg-green-500 transition-colors shadow-[0_0_15px_rgba(34,197,94,0.3)]"
                    title="Launch Stage View for Players"
                  >
                    Play (Stage)
                  </button>
                  <button
                    onClick={() => openPlayerPicker(c)}
                    className="flex-1 py-2 px-3 rounded text-sm font-bold bg-cyan-700 text-white hover:bg-cyan-600 transition-colors shadow-[0_0_15px_rgba(8,145,178,0.3)]"
                    title="Launch Player View with identity picker"
                  >
                    Play (Player)
                  </button>
                </div>
              </div>
            </div>
          ))}
          {campaigns.length === 0 && (
            <div className="col-span-full p-12 text-center rounded-2xl border-2 border-dashed border-border text-muted-foreground">No campaigns found. Create one to get started!</div>
          )}
        </div>
      )}

      {playerPickerCampaign && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={closePlayerPicker}>
          <div
            className="w-full max-w-md rounded-xl border border-border bg-surface-100 p-4 shadow-xl"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Player picker"
          >
            <h3 className="text-lg font-bold text-foreground">Open As Player</h3>
            <p className="mt-1 text-sm text-muted-foreground">Campaign: {playerPickerCampaign.name}</p>

            <div className="mt-4 space-y-2">
              <label htmlFor="campaign-player-picker-select" className="block text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Possible players
              </label>
              <select id="campaign-player-picker-select" value={playerPickerSelection} onChange={(event) => setPlayerPickerSelection(event.target.value)} className="input w-full">
                <option value="">Select player identity</option>
                {getPossiblePlayersForCampaign(playerPickerCampaign).map((userId) => (
                  <option key={userId} value={userId}>
                    {userId}
                  </option>
                ))}
              </select>
            </div>

            <div className="mt-3 space-y-2">
              <label htmlFor="campaign-player-picker-custom" className="block text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Or custom user id
              </label>
              <input
                id="campaign-player-picker-custom"
                type="text"
                value={playerPickerCustomUserId}
                onChange={(event) => setPlayerPickerCustomUserId(event.target.value)}
                placeholder="e.g. player_1"
                className="input w-full"
              />
            </div>

            <p className="mt-3 text-xs text-muted-foreground">Resolved identity: {resolvePickedPlayerUserId() || "none (opens player viewer without impersonation)"}</p>

            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={closePlayerPicker} className="btn btn-ghost">
                Cancel
              </button>
              <button type="button" onClick={() => launchPlayerView("same-tab")} className="btn btn-secondary">
                Open Here
              </button>
              <button type="button" onClick={() => launchPlayerView("new-tab")} className="btn btn-primary">
                Open New Tab
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
