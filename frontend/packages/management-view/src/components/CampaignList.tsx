import React, { useState, useEffect } from "react";

// Minimal component for walking skeleton CRUD
export const CampaignList = () => {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [newCampaignName, setNewCampaignName] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchCampaigns = async () => {
    try {
      const token = localStorage.getItem("civic_auth_token");
      const res = await fetch("/api/campaigns/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch campaigns");
      const data = await res.json();
      setCampaigns(data);
    } catch (err: any) {
      setError(err.message);
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
      const res = await fetch("/api/campaigns/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: newCampaignName, description: "Walking Skeleton Campaign" }),
      });

      if (!res.ok) throw new Error("Failed to create campaign");

      setNewCampaignName("");
      fetchCampaigns(); // Refresh list
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) return <div>Loading raw campaigns...</div>;

  return (
    <div style={{ padding: "20px", fontFamily: "monospace", background: "#eee", color: "#333" }}>
      <h2>Management View - Raw Campaign List</h2>

      {error && <div style={{ color: "red", marginBottom: "10px" }}>Error: {error}</div>}

      <form onSubmit={handleCreate} style={{ marginBottom: "20px", padding: "10px", border: "1px solid #ccc" }}>
        <h3>Create New Campaign</h3>
        <input type="text" value={newCampaignName} onChange={(e) => setNewCampaignName(e.target.value)} placeholder="Campaign Name..." style={{ marginRight: "10px", padding: "5px" }} />
        <button type="submit" style={{ padding: "5px 10px" }}>
          POST to /api/campaigns
        </button>
      </form>

      <ul style={{ listStyleType: "none", padding: 0 }}>
        {campaigns.map((c) => (
          <li key={c.id} style={{ margin: "10px 0", borderBottom: "1px solid #ccc", paddingBottom: "10px" }}>
            <strong>{c.name}</strong>
            <div style={{ fontSize: "0.8em", color: "#666" }}>ID: {c.id}</div>
            <pre style={{ margin: "5px 0", background: "#ddd", padding: "5px" }}>{JSON.stringify(c, null, 2)}</pre>
          </li>
        ))}
      </ul>
    </div>
  );
};
