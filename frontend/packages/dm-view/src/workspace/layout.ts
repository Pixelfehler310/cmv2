import { IJsonModel } from "flexlayout-react";

const LAYOUT_VERSION = "v1";

const baseGlobalConfig: IJsonModel["global"] = {
  tabEnableClose: false,
  tabSetEnableMaximize: true,
  tabSetEnableTabStrip: true,
  borderBarSize: 32,
};

const desktopLayout: IJsonModel = {
  global: baseGlobalConfig,
  borders: [
    {
      type: "border",
      location: "left",
      size: 320,
      children: [{ type: "tab", name: "Initiative", component: "initiative" }],
    },
    {
      type: "border",
      location: "right",
      size: 420,
      children: [{ type: "tab", name: "Action Deck", component: "action-deck" }],
    },
    {
      type: "border",
      location: "bottom",
      size: 280,
      children: [{ type: "tab", name: "Command Deck", component: "command-deck" }],
    },
  ],
  layout: {
    type: "row",
    weight: 100,
    children: [
      {
        type: "tabset",
        weight: 100,
        children: [{ type: "tab", name: "Battle Map", component: "map", enableClose: false }],
      },
    ],
  },
};

const tabletLayout: IJsonModel = {
  ...desktopLayout,
  borders: [
    {
      type: "border",
      location: "left",
      size: 260,
      children: [{ type: "tab", name: "Initiative", component: "initiative" }],
    },
    {
      type: "border",
      location: "right",
      size: 300,
      children: [{ type: "tab", name: "Action Deck", component: "action-deck" }],
    },
    {
      type: "border",
      location: "bottom",
      size: 260,
      children: [{ type: "tab", name: "Command Deck", component: "command-deck" }],
    },
  ],
};

const mobileLayout: IJsonModel = {
  global: baseGlobalConfig,
  borders: [
    {
      type: "border",
      location: "bottom",
      size: 300,
      children: [
        { type: "tab", name: "Command Deck", component: "command-deck" },
        { type: "tab", name: "Action Deck", component: "action-deck" },
        { type: "tab", name: "Initiative", component: "initiative" },
      ],
    },
  ],
  layout: {
    type: "row",
    weight: 100,
    children: [
      {
        type: "tabset",
        weight: 100,
        children: [{ type: "tab", name: "Battle Map", component: "map", enableClose: false }],
      },
    ],
  },
};

const getLayoutStorageKey = (campaignId: string): string => `dm-workspace-layout:${LAYOUT_VERSION}:${campaignId}`;

export const getDefaultDmLayout = (viewportWidth: number): IJsonModel => {
  if (viewportWidth < 768) {
    return mobileLayout;
  }
  if (viewportWidth < 1200) {
    return tabletLayout;
  }
  return desktopLayout;
};

export const loadDmLayout = (campaignId: string, fallbackLayout: IJsonModel): IJsonModel => {
  if (typeof window === "undefined") {
    return fallbackLayout;
  }

  try {
    const raw = window.localStorage.getItem(getLayoutStorageKey(campaignId));
    if (!raw) {
      return fallbackLayout;
    }

    const parsed = JSON.parse(raw) as IJsonModel;
    if (!parsed || typeof parsed !== "object") {
      return fallbackLayout;
    }

    return parsed;
  } catch {
    return fallbackLayout;
  }
};

export const saveDmLayout = (campaignId: string, layout: IJsonModel): void => {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(getLayoutStorageKey(campaignId), JSON.stringify(layout));
  } catch {
    // Ignore storage errors to keep runtime resilient.
  }
};

export const clearDmLayout = (campaignId: string): void => {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.removeItem(getLayoutStorageKey(campaignId));
  } catch {
    // Ignore storage errors to keep runtime resilient.
  }
};
