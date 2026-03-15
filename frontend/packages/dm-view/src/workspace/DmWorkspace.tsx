import React, { useEffect, useState } from "react";
import { IHostBridge } from "@rpg/bridge";
import { Layout, Model, TabNode } from "flexlayout-react";
import "flexlayout-react/style/dark.css";
import { useCombatStore } from "@rpg/shared";
import { clearDmLayout, getDefaultDmLayout, loadDmLayout, saveDmLayout } from "./layout";
import { getDmPanelDefinition } from "./panelRegistry";

interface DmWorkspaceProps {
  bridge?: IHostBridge;
  campaignId: string;
}

const getViewportWidth = (): number => {
  if (typeof window === "undefined") {
    return 1280;
  }
  return window.innerWidth;
};

export const DmWorkspace: React.FC<DmWorkspaceProps> = ({ bridge, campaignId }) => {
  const { isConnected } = useCombatStore();
  const [selectedCombatantId, setSelectedCombatantId] = useState<string | null>(null);
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
  }, [campaignId]);

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
      <section className="h-full w-full overflow-hidden" role="region" aria-label={panel.ariaLabel}>
        {panel.render({
          bridge,
          campaignId,
          selectedCombatantId,
          onSelectCombatant: setSelectedCombatantId,
          clearSelectedCombatant: () => setSelectedCombatantId(null),
        })}
      </section>
    );
  };

  if (!isConnected) {
    return <div className="p-5 text-white">Waiting for Host connection for campaign {campaignId}...</div>;
  }

  return (
    <div className="relative h-full w-full bg-black text-white" aria-label="DM docked workspace">
      <div className="absolute right-3 top-3 z-50">
        <button
          type="button"
          onClick={resetLayout}
          className="rounded border border-slate-600 bg-slate-900/90 px-3 py-1 text-xs font-medium text-slate-100 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-400"
        >
          Reset Layout
        </button>
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
