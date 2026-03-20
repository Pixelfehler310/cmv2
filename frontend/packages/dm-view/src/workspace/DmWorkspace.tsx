import React, { useEffect, useMemo, useState } from "react";
import { IHostBridge } from "@rpg/bridge";
import { Layout, Model, TabNode } from "flexlayout-react";
import "flexlayout-react/style/dark.css";
import { useCombatStore } from "@rpg/shared";
import { clearDmLayout, getDefaultDmLayout, loadDmLayout, saveDmLayout } from "./layout";
import { getDmPanelDefinition } from "./panelRegistry";

interface DmWorkspaceProps {
  bridge?: IHostBridge;
  campaignId: string;
  frontendTesting?: {
    dmProxyDock?: boolean;
  };
}

const getViewportWidth = (): number => {
  if (typeof window === "undefined") {
    return 1280;
  }
  return window.innerWidth;
};

export const DmWorkspace: React.FC<DmWorkspaceProps> = ({ bridge, campaignId, frontendTesting }) => {
  const { isConnected, gameState, setActingAsUserId } = useCombatStore();
  const [selectedCombatantId, setSelectedCombatantId] = useState<string | null>(null);
  const [playAsSelection, setPlayAsSelection] = useState<string>("auto");
  const [isPlayerViewLauncherOpen, setIsPlayerViewLauncherOpen] = useState<boolean>(false);
  const [playerViewLaunchUserId, setPlayerViewLaunchUserId] = useState<string>("");
  const [model, setModel] = useState<Model>(() => {
    const defaultLayout = getDefaultDmLayout(getViewportWidth());
    const initialLayout = loadDmLayout(campaignId, defaultLayout);
    return Model.fromJson(initialLayout);
  });

  useEffect(() => {
    const defaultLayout = getDefaultDmLayout(getViewportWidth());
    const nextLayout = loadDmLayout(campaignId, defaultLayout);
    setModel(Model.fromJson(nextLayout));
    setSelectedCombatantId(null);
    setPlayAsSelection("auto");
    setIsPlayerViewLauncherOpen(false);
    setPlayerViewLaunchUserId("");
    setActingAsUserId(null);
  }, [campaignId, setActingAsUserId]);

  const selectedCombatant = useMemo(() => {
    if (!selectedCombatantId) {
      return null;
    }

    return gameState?.combatants.find((combatant) => combatant.id === selectedCombatantId) ?? null;
  }, [gameState, selectedCombatantId]);

  const autoProxyUserId = useMemo(() => {
    const owner = (selectedCombatant?.owner_user_id ?? "").trim();
    return owner.length > 0 ? owner : null;
  }, [selectedCombatant]);

  const effectiveActingAsUserId = useMemo(() => {
    if (playAsSelection === "auto") {
      return autoProxyUserId;
    }

    return playAsSelection.trim().length > 0 ? playAsSelection.trim() : null;
  }, [autoProxyUserId, playAsSelection]);

  useEffect(() => {
    setActingAsUserId(effectiveActingAsUserId);
  }, [effectiveActingAsUserId, setActingAsUserId]);

  const playableUserIds = useMemo(() => {
    if (!gameState) {
      return [];
    }

    return Array.from(new Set(gameState.combatants.map((combatant) => (combatant.owner_user_id ?? "").trim()).filter((ownerId) => ownerId.length > 0))).sort((a, b) => a.localeCompare(b));
  }, [gameState]);

  const resolvedPlayerViewLaunchUserId = useMemo(() => {
    const trimmed = playerViewLaunchUserId.trim();
    if (trimmed.length > 0) {
      return trimmed;
    }

    if (playAsSelection === "auto") {
      return autoProxyUserId;
    }

    return playAsSelection.trim().length > 0 ? playAsSelection.trim() : null;
  }, [autoProxyUserId, playAsSelection, playerViewLaunchUserId]);

  const buildPlayerViewRoute = (): string => {
    const encodedCampaignId = encodeURIComponent(campaignId);
    const query = new URLSearchParams({ view: "player" });
    if (resolvedPlayerViewLaunchUserId) {
      query.set("as_user_id", resolvedPlayerViewLaunchUserId);
    }

    return `/session/${encodedCampaignId}?${query.toString()}`;
  };

  const launchPlayerViewAsUserInNewTab = (): void => {
    const url = buildPlayerViewRoute();
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const launchPlayerViewAsUserInCurrentTab = (): void => {
    const url = buildPlayerViewRoute();
    window.location.assign(url);
  };

  const resetLayout = () => {
    clearDmLayout(campaignId);
    const defaultLayout = getDefaultDmLayout(getViewportWidth());
    setModel(Model.fromJson(defaultLayout));
  };

  const factory = (node: TabNode) => {
    const componentId = node.getComponent() ?? "";
    const panel = getDmPanelDefinition(componentId);

    if (!panel) {
      return <div className="p-3 text-sm text-slate-300">Unknown DM panel: {componentId}</div>;
    }

    return (
      <section className="h-full w-full min-h-0 overflow-hidden bg-surface-1" role="region" aria-label={panel.ariaLabel}>
        {panel.render({
          bridge,
          campaignId,
          frontendTesting,
          selectedCombatantId,
          onSelectCombatant: setSelectedCombatantId,
          clearSelectedCombatant: () => setSelectedCombatantId(null),
        })}
      </section>
    );
  };

  if (!isConnected) {
    return <div className="p-5 text-on-canvas">Waiting for Host connection for campaign {campaignId}...</div>;
  }

  const flexLayoutThemeVars = {
    "--color-text": "var(--on-canvas)",
    "--color-background": "var(--bg-surface-1)",
    "--color-base": "var(--bg-canvas)",
    "--color-1": "var(--bg-surface-1)",
    "--color-2": "var(--bg-surface-2)",
    "--color-3": "var(--bg-surface-2)",
    "--color-4": "var(--bg-surface-3)",
    "--color-5": "var(--bg-muted)",
    "--color-6": "var(--bg-subtle)",
    "--font-family": "var(--font-sans)",
    "--color-overflow": "var(--on-muted)",
    "--color-icon": "var(--on-muted)",
    "--color-tabset-background": "var(--bg-surface-1)",
    "--color-tabset-background-selected": "var(--bg-surface-1)",
    "--color-tabset-background-maximized": "var(--bg-surface-2)",
    "--color-tabset-divider-line": "var(--border-subtle)",
    "--color-tabset-header-background": "var(--bg-surface-2)",
    "--color-tabset-header": "var(--on-surface)",
    "--color-border-background": "var(--bg-surface-1)",
    "--color-border-divider-line": "var(--border-subtle)",
    "--color-tab-selected": "var(--on-surface)",
    "--color-tab-selected-background": "var(--bg-surface-3)",
    "--color-tab-unselected": "var(--on-muted)",
    "--color-tab-unselected-background": "transparent",
    "--color-tab-textbox": "var(--on-surface)",
    "--color-tab-textbox-background": "var(--bg-inset)",
    "--color-border-tab-selected": "var(--on-surface)",
    "--color-border-tab-selected-background": "var(--bg-surface-3)",
    "--color-border-tab-unselected": "var(--on-muted)",
    "--color-border-tab-unselected-background": "var(--bg-surface-2)",
    "--color-splitter": "var(--bg-surface-2)",
    "--color-splitter-hover": "var(--bg-surface-3)",
    "--color-splitter-drag": "var(--color-primary)",
    "--color-drag-rect-border": "var(--border-default)",
    "--color-drag-rect-background": "var(--bg-surface-1)",
    "--color-drag-rect": "var(--on-surface)",
    "--color-popup-border": "var(--border-default)",
    "--color-popup-unselected": "var(--on-surface)",
    "--color-popup-unselected-background": "var(--bg-surface-1)",
    "--color-popup-selected": "var(--on-surface)",
    "--color-popup-selected-background": "var(--bg-surface-3)",
    "--color-edge-marker": "var(--color-primary)",
    "--color-edge-icon": "var(--on-primary)",
  } as React.CSSProperties;

  return (
    <div className="dm-workspace relative h-full w-full bg-canvas text-on-canvas" style={flexLayoutThemeVars} aria-label="DM docked workspace">
      <div className="absolute right-3 top-3 z-20 flex items-center gap-2 rounded-lg border border-(--border-default) bg-surface-2/95 px-3 py-2 text-xs shadow-sm backdrop-blur">
        <label htmlFor="dm-play-as-select" className="font-semibold text-on-muted">
          Play as
        </label>
        <select
          id="dm-play-as-select"
          value={playAsSelection}
          onChange={(event) => {
            setPlayAsSelection(event.target.value);
          }}
          className="rounded border border-(--border-subtle) bg-surface-1 px-2 py-1 text-xs text-on-surface"
        >
          <option value="auto">Auto (selected actor owner, else DM)</option>
          <option value="">DM (no impersonation)</option>
          {playableUserIds.map((userId) => (
            <option key={userId} value={userId}>
              {userId}
            </option>
          ))}
        </select>
        <span className="rounded border border-(--border-subtle) bg-surface-1 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-on-muted">
          Effective: {effectiveActingAsUserId ? `player:${effectiveActingAsUserId}` : "DM"}
        </span>
        <button
          type="button"
          onClick={() => setIsPlayerViewLauncherOpen(true)}
          className="rounded border border-cyan-700 bg-cyan-900/30 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-cyan-100 hover:bg-cyan-800/40"
        >
          Open Player View Launcher
        </button>
      </div>

      {isPlayerViewLauncherOpen && (
        <div className="absolute inset-0 z-40 flex items-center justify-center bg-slate-950/60 p-4" onClick={() => setIsPlayerViewLauncherOpen(false)}>
          <div
            className="w-full max-w-md rounded-xl border border-(--border-default) bg-surface-1 p-4 shadow-xl"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Player view launcher"
          >
            <h3 className="text-sm font-bold uppercase tracking-wide text-(--primary-text)">Open Player View</h3>
            <p className="mt-2 text-xs text-on-muted">Choose a player identity and open the player route with the correct query parameters.</p>

            <div className="mt-4 space-y-2">
              <label htmlFor="dm-player-view-as-select-modal" className="block text-xs font-semibold text-on-muted">
                Player identity
              </label>
              <select
                id="dm-player-view-as-select-modal"
                value={playerViewLaunchUserId}
                onChange={(event) => {
                  setPlayerViewLaunchUserId(event.target.value);
                }}
                className="w-full rounded border border-(--border-subtle) bg-surface-2 px-2 py-1 text-xs text-on-surface"
              >
                <option value="">Auto (Play as selection)</option>
                {playableUserIds.map((userId) => (
                  <option key={`player-view-modal-${userId}`} value={userId}>
                    {userId}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-on-muted">Resolved user: {resolvedPlayerViewLaunchUserId ?? "none (viewer mode)"}</p>
              <p className="rounded border border-(--border-subtle) bg-surface-2 px-2 py-1 text-[11px] text-on-muted">Route: {buildPlayerViewRoute()}</p>
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setIsPlayerViewLauncherOpen(false)}
                className="rounded border border-(--border-subtle) px-2 py-1 text-xs font-semibold text-on-muted hover:bg-surface-2"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={launchPlayerViewAsUserInCurrentTab}
                className="rounded border border-cyan-700 bg-cyan-900/30 px-2 py-1 text-xs font-semibold text-cyan-100 hover:bg-cyan-800/40"
              >
                Open Here
              </button>
              <button
                type="button"
                onClick={launchPlayerViewAsUserInNewTab}
                className="rounded border border-cyan-700 bg-cyan-900/30 px-2 py-1 text-xs font-semibold text-cyan-100 hover:bg-cyan-800/40"
              >
                Open New Tab
              </button>
            </div>
          </div>
        </div>
      )}

      <Layout
        model={model}
        factory={factory}
        onModelChange={(nextModel: Model) => {
          saveDmLayout(campaignId, nextModel.toJson());
          setModel(nextModel);
        }}
      />
    </div>
  );
};
