import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, Box, FileJson, RefreshCw, Send, ShieldCheck, Swords, Waypoints, Wifi, WifiOff } from "lucide-react";
import { config } from "../config";

type DebugTab = "characterWrite" | "characterSheet" | "compendium" | "wsStream";

type HttpCallResult = {
  method: string;
  url: string;
  requestId: string;
  status: number;
  ok: boolean;
  body: unknown;
  receivedAt: string;
};

type WsMessageEntry = {
  id: string;
  receivedAt: string;
  payload: unknown;
};

type CharacterWriteMode = "create" | "update";

const DEFAULT_CHARACTER_WRITE_PAYLOAD = {
  name: "Aelar",
  player_name: "Owner",
  player_id: "user-owner",
  status: "active",
  campaign_id: "camp-1",
  species_id: "species-1",
  class_id: "class-1",
  background_id: null,
  ability_ids: [],
  level: 1,
  xp: 0,
  alignment: "neutral",
  strength: 10,
  dexterity: 12,
  constitution: 13,
  intelligence: 10,
  wisdom: 10,
  charisma: 8,
  max_hp: 12,
  current_hp: 12,
  temp_hp: 0,
  hit_dice: "1d10",
  armor_class: 14,
  speed: 30,
  initiative: 1,
  inventory: [],
  spells: [],
  spell_slots: {},
  actions: [],
  effects: [],
};

const ACTIVE_TAB_STYLE = "border-primary text-primary bg-surface-100/60";
const INACTIVE_TAB_STYLE = "border-transparent text-muted-foreground hover:text-foreground hover:bg-surface-50";

function makeRequestId(prefix: string): string {
  const rand = Math.random().toString(36).slice(2, 10);
  return `${prefix}-${Date.now()}-${rand}`;
}

function readAuthToken(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem("civic_auth_token") ?? "";
}

function safeParse(text: string): unknown {
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function performJsonRequest(params: { method: "GET" | "POST" | "PUT"; url: string; requestId: string; body?: unknown }): Promise<HttpCallResult> {
  const token = readAuthToken();
  const headers: Record<string, string> = {
    "x-request-id": params.requestId,
  };

  if (params.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (token.length > 0) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(params.url, {
    method: params.method,
    headers,
    body: params.body !== undefined ? JSON.stringify(params.body) : undefined,
  });

  const text = await response.text();

  return {
    method: params.method,
    url: params.url,
    requestId: params.requestId,
    status: response.status,
    ok: response.ok,
    body: safeParse(text),
    receivedAt: new Date().toISOString(),
  };
}

const TabButton = ({ active, onClick, label, icon }: { active: boolean; onClick: () => void; label: string; icon: React.ReactNode }) => (
  <button
    onClick={onClick}
    className={`px-5 py-3 font-semibold text-sm rounded-t-lg transition-colors border-b-2 flex items-center gap-2 whitespace-nowrap ${active ? ACTIVE_TAB_STYLE : INACTIVE_TAB_STYLE}`}
  >
    {icon}
    {label}
  </button>
);

const SectionCard = ({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) => (
  <section className="bg-surface-50 border border-border rounded-2xl p-5 h-full">
    <header className="mb-4">
      <h3 className="text-lg font-heading text-foreground">{title}</h3>
      <p className="text-sm text-muted-foreground">{subtitle}</p>
    </header>
    {children}
  </section>
);

const JsonPanel = ({ value }: { value: unknown }) => (
  <div className="bg-surface-100 border border-border rounded-xl p-4 overflow-auto max-h-104">
    <pre className="text-xs text-foreground whitespace-pre-wrap wrap-break-word">{JSON.stringify(value, null, 2)}</pre>
  </div>
);

export const DebugRoute = () => {
  const [activeTab, setActiveTab] = useState<DebugTab>("characterWrite");

  const [characterMode, setCharacterMode] = useState<CharacterWriteMode>("create");
  const [characterId, setCharacterId] = useState("");
  const [characterRequestId, setCharacterRequestId] = useState(makeRequestId("char-write"));
  const [characterPayloadText, setCharacterPayloadText] = useState(JSON.stringify(DEFAULT_CHARACTER_WRITE_PAYLOAD, null, 2));
  const [characterResult, setCharacterResult] = useState<HttpCallResult | null>(null);
  const [characterError, setCharacterError] = useState<string | null>(null);
  const [characterLoading, setCharacterLoading] = useState(false);

  const [sheetCharacterId, setSheetCharacterId] = useState("");
  const [sheetCatalogRevision, setSheetCatalogRevision] = useState("1");
  const [sheetRequestId, setSheetRequestId] = useState(makeRequestId("sheet"));
  const [sheetResult, setSheetResult] = useState<HttpCallResult | null>(null);
  const [sheetError, setSheetError] = useState<string | null>(null);
  const [sheetLoading, setSheetLoading] = useState(false);

  const [packId, setPackId] = useState("core-pack");
  const [definitionId, setDefinitionId] = useState("example-definition");
  const [compendiumResult, setCompendiumResult] = useState<HttpCallResult | null>(null);
  const [compendiumError, setCompendiumError] = useState<string | null>(null);
  const [compendiumLoading, setCompendiumLoading] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const defaultWsBase = config.wsUrl;
  const [wsBaseUrl, setWsBaseUrl] = useState(defaultWsBase);
  const [wsCampaignId, setWsCampaignId] = useState("camp-1");
  const [wsRole, setWsRole] = useState("dm");
  const [wsToken, setWsToken] = useState(readAuthToken());
  const [wsStatus, setWsStatus] = useState<"idle" | "connecting" | "connected" | "closed" | "error">("idle");
  const [wsError, setWsError] = useState<string | null>(null);
  const [wsMessages, setWsMessages] = useState<WsMessageEntry[]>([]);

  const wsStatusLabel = useMemo(() => {
    if (wsStatus === "connected") {
      return "Connected";
    }
    if (wsStatus === "connecting") {
      return "Connecting";
    }
    if (wsStatus === "error") {
      return "Error";
    }
    if (wsStatus === "closed") {
      return "Closed";
    }
    return "Idle";
  }, [wsStatus]);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const executeCharacterWrite = async () => {
    setCharacterLoading(true);
    setCharacterError(null);

    try {
      if (characterMode === "update" && characterId.trim().length === 0) {
        throw new Error("Character ID is required for update mode.");
      }

      const payload = JSON.parse(characterPayloadText);
      const url = characterMode === "create" ? "/api/characters" : `/api/characters/${encodeURIComponent(characterId.trim())}`;
      const method = characterMode === "create" ? "POST" : "PUT";

      const result = await performJsonRequest({
        method,
        url,
        requestId: characterRequestId,
        body: payload,
      });

      setCharacterResult(result);
      setCharacterRequestId(makeRequestId("char-write"));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected error during character write call.";
      setCharacterError(message);
    } finally {
      setCharacterLoading(false);
    }
  };

  const executeSheetProjection = async () => {
    setSheetLoading(true);
    setSheetError(null);

    try {
      if (sheetCharacterId.trim().length === 0) {
        throw new Error("Character ID is required for sheet projection.");
      }

      const revision = Number(sheetCatalogRevision);
      if (Number.isNaN(revision) || revision < 0) {
        throw new Error("Catalog revision must be a number >= 0.");
      }

      const result = await performJsonRequest({
        method: "GET",
        url: `/api/characters/${encodeURIComponent(sheetCharacterId.trim())}/sheet?catalog_revision=${revision}`,
        requestId: sheetRequestId,
      });

      setSheetResult(result);
      setSheetRequestId(makeRequestId("sheet"));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected error during sheet projection call.";
      setSheetError(message);
    } finally {
      setSheetLoading(false);
    }
  };

  const runCompendiumRequest = async (request: { method: "GET"; url: string; requestIdPrefix: string }) => {
    setCompendiumLoading(true);
    setCompendiumError(null);

    try {
      const requestId = makeRequestId(request.requestIdPrefix);
      const result = await performJsonRequest({
        method: request.method,
        url: request.url,
        requestId,
      });
      setCompendiumResult(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected error during compendium call.";
      setCompendiumError(message);
    } finally {
      setCompendiumLoading(false);
    }
  };

  const connectWs = () => {
    setWsError(null);

    if (wsCampaignId.trim().length === 0) {
      setWsError("Campaign ID is required.");
      return;
    }

    if (wsToken.trim().length === 0) {
      setWsError("Token is required for WebSocket connection.");
      return;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      const normalizedBase = wsBaseUrl.endsWith("/") ? wsBaseUrl.slice(0, -1) : wsBaseUrl;
      const connectionUrl = `${normalizedBase}/${encodeURIComponent(wsCampaignId.trim())}?token=${encodeURIComponent(wsToken.trim())}&role=${encodeURIComponent(wsRole)}`;
      const socket = new WebSocket(connectionUrl);

      wsRef.current = socket;
      setWsStatus("connecting");

      socket.onopen = () => {
        setWsStatus("connected");
      };

      socket.onmessage = (event) => {
        const parsed = safeParse(event.data);
        setWsMessages((prev) => {
          const nextEntry: WsMessageEntry = {
            id: makeRequestId("ws-msg"),
            receivedAt: new Date().toISOString(),
            payload: parsed,
          };
          const next = [nextEntry, ...prev];
          return next.slice(0, 150);
        });
      };

      socket.onerror = () => {
        setWsStatus("error");
        setWsError("WebSocket error occurred. Check token, campaign, and backend WS availability.");
      };

      socket.onclose = () => {
        setWsStatus("closed");
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to open WebSocket.";
      setWsStatus("error");
      setWsError(message);
    }
  };

  const disconnectWs = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setWsStatus("closed");
  };

  const clearWsMessages = () => {
    setWsMessages([]);
  };

  return (
    <div className="h-full bg-background flex flex-col p-8">
      <div className="max-w-7xl mx-auto w-full h-full flex flex-col gap-6">
        <header className="flex flex-col gap-2">
          <div className="flex items-center gap-2 text-primary">
            <Activity size={22} />
            <h1 className="text-3xl font-heading text-foreground">Implementation Debug Workspace</h1>
          </div>
          <p className="text-muted-foreground">Layered module debug workspace for CM-07 and CM-08 extension, plus compendium and stream verification.</p>
        </header>

        <div className="flex gap-2 border-b border-border overflow-x-auto pb-1 scrollbar-hide">
          <TabButton active={activeTab === "characterWrite"} onClick={() => setActiveTab("characterWrite")} label="Character Write (CM-07)" icon={<Swords size={16} />} />
          <TabButton active={activeTab === "characterSheet"} onClick={() => setActiveTab("characterSheet")} label="Character Sheet (CM-08)" icon={<ShieldCheck size={16} />} />
          <TabButton active={activeTab === "compendium"} onClick={() => setActiveTab("compendium")} label="Compendium (CM-01..CM-05)" icon={<Box size={16} />} />
          <TabButton active={activeTab === "wsStream"} onClick={() => setActiveTab("wsStream")} label="WebSocket Stream" icon={<Waypoints size={16} />} />
        </div>

        <div className="flex-1 overflow-auto">
          {activeTab === "characterWrite" ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              <SectionCard title="Request Composer" subtitle="Build and execute character create or update requests against the backend character router.">
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <label className="flex flex-col gap-1 text-sm">
                      <span className="text-muted-foreground">Mode</span>
                      <select
                        value={characterMode}
                        onChange={(event) => setCharacterMode(event.target.value as CharacterWriteMode)}
                        className="px-3 py-2 bg-background border border-border rounded-lg"
                      >
                        <option value="create">Create</option>
                        <option value="update">Update</option>
                      </select>
                    </label>
                    <label className="flex flex-col gap-1 text-sm">
                      <span className="text-muted-foreground">Character ID (update only)</span>
                      <input
                        value={characterId}
                        onChange={(event) => setCharacterId(event.target.value)}
                        placeholder="character-id"
                        className="px-3 py-2 bg-background border border-border rounded-lg"
                      />
                    </label>
                  </div>

                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">Request ID</span>
                    <input value={characterRequestId} onChange={(event) => setCharacterRequestId(event.target.value)} className="px-3 py-2 bg-background border border-border rounded-lg" />
                  </label>

                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">Payload JSON</span>
                    <textarea
                      value={characterPayloadText}
                      onChange={(event) => setCharacterPayloadText(event.target.value)}
                      className="min-h-64 px-3 py-2 bg-background border border-border rounded-lg font-mono text-xs"
                    />
                  </label>

                  <div className="flex gap-3">
                    <button onClick={executeCharacterWrite} disabled={characterLoading} className="btn btn-primary gradient-quest px-5 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50">
                      {characterLoading ? <RefreshCw size={16} className="animate-spin" /> : <Send size={16} />}
                      Send Request
                    </button>
                    <button
                      onClick={() => {
                        setCharacterPayloadText(JSON.stringify(DEFAULT_CHARACTER_WRITE_PAYLOAD, null, 2));
                        setCharacterError(null);
                      }}
                      className="btn btn-secondary px-5 py-2 rounded-lg"
                    >
                      Reset Payload
                    </button>
                  </div>

                  {characterError ? <p className="text-sm text-red-500">{characterError}</p> : null}
                </div>
              </SectionCard>

              <SectionCard title="Envelope Output" subtitle="Inspect resolved and denied envelopes with status, request correlation, and payload shape.">
                {characterResult ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="bg-surface-100 border border-border rounded-lg p-3">
                        <div className="text-muted-foreground">Status</div>
                        <div className={characterResult.ok ? "text-green-500 font-semibold" : "text-red-500 font-semibold"}>{characterResult.status}</div>
                      </div>
                      <div className="bg-surface-100 border border-border rounded-lg p-3">
                        <div className="text-muted-foreground">Request ID</div>
                        <div className="font-mono text-xs break-all">{characterResult.requestId}</div>
                      </div>
                    </div>
                    <JsonPanel value={characterResult} />
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm">No response yet. Execute a create or update request to inspect envelope behavior.</p>
                )}
              </SectionCard>
            </div>
          ) : null}

          {activeTab === "characterSheet" ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              <SectionCard title="Projection Request" subtitle="Fetch character sheet projections by revision to validate resolved, denied, and invalidated outcomes.">
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <label className="flex flex-col gap-1 text-sm">
                      <span className="text-muted-foreground">Character ID</span>
                      <input
                        value={sheetCharacterId}
                        onChange={(event) => setSheetCharacterId(event.target.value)}
                        placeholder="character-id"
                        className="px-3 py-2 bg-background border border-border rounded-lg"
                      />
                    </label>
                    <label className="flex flex-col gap-1 text-sm">
                      <span className="text-muted-foreground">Catalog Revision</span>
                      <input
                        value={sheetCatalogRevision}
                        onChange={(event) => setSheetCatalogRevision(event.target.value)}
                        placeholder="1"
                        className="px-3 py-2 bg-background border border-border rounded-lg"
                      />
                    </label>
                  </div>

                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">Request ID</span>
                    <input value={sheetRequestId} onChange={(event) => setSheetRequestId(event.target.value)} className="px-3 py-2 bg-background border border-border rounded-lg" />
                  </label>

                  <div className="flex gap-3">
                    <button onClick={executeSheetProjection} disabled={sheetLoading} className="btn btn-primary gradient-vtt px-5 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50">
                      {sheetLoading ? <RefreshCw size={16} className="animate-spin" /> : <FileJson size={16} />}
                      Fetch Projection
                    </button>
                  </div>

                  {sheetError ? <p className="text-sm text-red-500">{sheetError}</p> : null}
                </div>
              </SectionCard>

              <SectionCard title="Projection Output" subtitle="Validate revision metadata, resolution status, denial reason codes, and unresolved references.">
                {sheetResult ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="bg-surface-100 border border-border rounded-lg p-3">
                        <div className="text-muted-foreground">Status</div>
                        <div className={sheetResult.ok ? "text-green-500 font-semibold" : "text-red-500 font-semibold"}>{sheetResult.status}</div>
                      </div>
                      <div className="bg-surface-100 border border-border rounded-lg p-3">
                        <div className="text-muted-foreground">Request ID</div>
                        <div className="font-mono text-xs break-all">{sheetResult.requestId}</div>
                      </div>
                    </div>
                    <JsonPanel value={sheetResult} />
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm">No projection fetched yet. Call the sheet endpoint to inspect response branches.</p>
                )}
              </SectionCard>
            </div>
          ) : null}

          {activeTab === "compendium" ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              <SectionCard title="Compendium Quick Checks" subtitle="Run targeted reads for pack/query/link checks tied to CM-01 through CM-05 behavior.">
                <div className="space-y-4">
                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">Pack ID</span>
                    <input value={packId} onChange={(event) => setPackId(event.target.value)} className="px-3 py-2 bg-background border border-border rounded-lg" />
                  </label>

                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">Definition ID</span>
                    <input value={definitionId} onChange={(event) => setDefinitionId(event.target.value)} className="px-3 py-2 bg-background border border-border rounded-lg" />
                  </label>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <button
                      onClick={() => runCompendiumRequest({ method: "GET", url: "/api/compendium/packs", requestIdPrefix: "cmp-packs" })}
                      disabled={compendiumLoading}
                      className="btn btn-secondary px-4 py-2 rounded-lg disabled:opacity-50"
                    >
                      List Packs
                    </button>
                    <button
                      onClick={() =>
                        runCompendiumRequest({
                          method: "GET",
                          url: `/api/compendium/definitions?pack_id=${encodeURIComponent(packId.trim())}`,
                          requestIdPrefix: "cmp-defs",
                        })
                      }
                      disabled={compendiumLoading}
                      className="btn btn-secondary px-4 py-2 rounded-lg disabled:opacity-50"
                    >
                      List Definitions
                    </button>
                    <button
                      onClick={() =>
                        runCompendiumRequest({
                          method: "GET",
                          url: `/api/compendium/definitions/${encodeURIComponent(definitionId.trim())}/links`,
                          requestIdPrefix: "cmp-links",
                        })
                      }
                      disabled={compendiumLoading}
                      className="btn btn-secondary px-4 py-2 rounded-lg disabled:opacity-50"
                    >
                      Fetch Links
                    </button>
                    <button
                      onClick={() =>
                        runCompendiumRequest({
                          method: "GET",
                          url: `/api/compendium/definitions/${encodeURIComponent(definitionId.trim())}/replacement-chain`,
                          requestIdPrefix: "cmp-chain",
                        })
                      }
                      disabled={compendiumLoading}
                      className="btn btn-secondary px-4 py-2 rounded-lg disabled:opacity-50"
                    >
                      Replacement Chain
                    </button>
                  </div>

                  {compendiumError ? <p className="text-sm text-red-500">{compendiumError}</p> : null}
                </div>
              </SectionCard>

              <SectionCard title="Compendium Output" subtitle="Inspect revision-aware envelopes and linked-reference results from quick-check endpoints.">
                {compendiumResult ? <JsonPanel value={compendiumResult} /> : <p className="text-muted-foreground text-sm">Run one of the quick checks to inspect output.</p>}
              </SectionCard>
            </div>
          ) : null}

          {activeTab === "wsStream" ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              <SectionCard title="Connection Controls" subtitle="Connect directly to the campaign stream and observe envelope events in real time.">
                <div className="space-y-4">
                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">WS Base URL</span>
                    <input value={wsBaseUrl} onChange={(event) => setWsBaseUrl(event.target.value)} className="px-3 py-2 bg-background border border-border rounded-lg" />
                  </label>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <label className="flex flex-col gap-1 text-sm">
                      <span className="text-muted-foreground">Campaign ID</span>
                      <input value={wsCampaignId} onChange={(event) => setWsCampaignId(event.target.value)} className="px-3 py-2 bg-background border border-border rounded-lg" />
                    </label>
                    <label className="flex flex-col gap-1 text-sm">
                      <span className="text-muted-foreground">Role</span>
                      <select value={wsRole} onChange={(event) => setWsRole(event.target.value)} className="px-3 py-2 bg-background border border-border rounded-lg">
                        <option value="dm">dm</option>
                        <option value="player">player</option>
                        <option value="observer">observer</option>
                        <option value="spectator">spectator</option>
                      </select>
                    </label>
                  </div>

                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">Token</span>
                    <input value={wsToken} onChange={(event) => setWsToken(event.target.value)} className="px-3 py-2 bg-background border border-border rounded-lg font-mono text-xs" />
                  </label>

                  <div className="flex items-center gap-2 text-sm">
                    {wsStatus === "connected" ? <Wifi size={15} className="text-green-500" /> : <WifiOff size={15} className="text-muted-foreground" />}
                    <span className="text-muted-foreground">Status:</span>
                    <span className={wsStatus === "connected" ? "text-green-500 font-semibold" : "text-foreground font-semibold"}>{wsStatusLabel}</span>
                  </div>

                  <div className="flex gap-3">
                    <button onClick={connectWs} className="btn btn-primary gradient-vtt px-5 py-2 rounded-lg" disabled={wsStatus === "connecting"}>
                      Connect
                    </button>
                    <button onClick={disconnectWs} className="btn btn-secondary px-5 py-2 rounded-lg">
                      Disconnect
                    </button>
                    <button onClick={clearWsMessages} className="btn btn-secondary px-5 py-2 rounded-lg">
                      Clear Events
                    </button>
                  </div>

                  {wsError ? <p className="text-sm text-red-500">{wsError}</p> : null}
                </div>
              </SectionCard>

              <SectionCard title="Incoming Events" subtitle="Newest events are shown first. Use this stream to validate projection and invalidation envelopes.">
                <div className="space-y-3 max-h-128 overflow-auto pr-1">
                  {wsMessages.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No events received yet.</p>
                  ) : (
                    wsMessages.map((entry) => (
                      <div key={entry.id} className="bg-surface-100 border border-border rounded-xl p-3">
                        <div className="text-xs text-muted-foreground mb-2">{entry.receivedAt}</div>
                        <JsonPanel value={entry.payload} />
                      </div>
                    ))
                  )}
                </div>
              </SectionCard>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
