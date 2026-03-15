import React from "react";
import { IHostBridge } from "@rpg/bridge";
import { InitiativePanel } from "../components/InitiativePanel";
import { MapBoard } from "../components/MapBoard";
import { DmCommandDeck } from "../components/CommandDeck";
import { ActionDeck } from "../components/ActionDeck";
import { CommandLogPanel } from "../components/CommandLogPanel";

export type DmPanelId =
  | "initiative"
  | "map"
  | "command-deck"
  | "action-deck"
  | "command-log";

type PanelRenderContext = {
  bridge?: IHostBridge;
  campaignId: string;
  selectedCombatantId: string | null;
  onSelectCombatant: (id: string | null) => void;
  clearSelectedCombatant: () => void;
};

export type DmPanelDefinition = {
  id: DmPanelId;
  displayName: string;
  ariaLabel: string;
  render: (context: PanelRenderContext) => React.ReactElement;
};

const panelRegistry: Record<DmPanelId, DmPanelDefinition> = {
  initiative: {
    id: "initiative",
    displayName: "Initiative",
    ariaLabel: "Initiative panel",
    render: ({ selectedCombatantId, onSelectCombatant }) => (
      <InitiativePanel
        selectedCombatantId={selectedCombatantId}
        onSelectCombatant={(id) => onSelectCombatant(id)}
      />
    ),
  },
  map: {
    id: "map",
    displayName: "Battle Map",
    ariaLabel: "Battle map panel",
    render: ({ selectedCombatantId, onSelectCombatant }) => (
      <MapBoard
        selectedCombatantId={selectedCombatantId}
        onSelectCombatant={onSelectCombatant}
      />
    ),
  },
  "command-deck": {
    id: "command-deck",
    displayName: "Command Deck",
    ariaLabel: "Command deck panel",
    render: ({ selectedCombatantId, clearSelectedCombatant }) => (
      <DmCommandDeck
        selectedCombatantId={selectedCombatantId}
        onRemoveSelected={clearSelectedCombatant}
      />
    ),
  },
  "action-deck": {
    id: "action-deck",
    displayName: "Action Deck",
    ariaLabel: "Action deck panel",
    render: ({ bridge, campaignId, selectedCombatantId }) => (
      <ActionDeck
        bridge={bridge}
        selectedCombatantId={selectedCombatantId}
        campaignId={campaignId}
      />
    ),
  },
  "command-log": {
    id: "command-log",
    displayName: "Command Log",
    ariaLabel: "Command log panel",
    render: () => <CommandLogPanel />,
  },
};

export const getDmPanelDefinition = (
  panelId: string,
): DmPanelDefinition | undefined => panelRegistry[panelId as DmPanelId];

export const listDmPanels = (): DmPanelDefinition[] =>
  Object.values(panelRegistry);
