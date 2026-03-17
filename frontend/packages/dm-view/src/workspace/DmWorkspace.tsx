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
      </div>
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
