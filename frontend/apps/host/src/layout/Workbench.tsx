import React, { useState, useEffect } from "react";
import { Layout, Model, TabNode, IJsonModel } from "flexlayout-react";
import "flexlayout-react/style/light.css";
import { defaultLayout } from "./defaultLayout";
import { loadLayout, saveLayout } from "../lib/layout/LayoutPersistence";
import { PlayerSheet } from "@rpg/player-sheet";
import { CharacterSelector } from "../components/CharacterSelector";
import { useCharacter, useMonsters, useCampaigns } from "../lib/api";
import { dispatchAction } from "../lib/actions";
import { DMToolsWithCRUD } from "../components/DMToolsWithCRUD";

const factory = (node: TabNode) => {
  const component = node.getComponent();
  if (component === "dm-view") {
    return <DMToolsWrapper />;
  }
  if (component === "player-sheet") {
    return <PlayerSheetWrapper />;
  }
  return <div className="p-4">Unknown Component</div>;
};

function PlayerSheetWrapper() {
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null);
  const { data: character } = useCharacter(selectedCharacterId);

  const handleAction = (type: string, payload: any) => {
    dispatchAction(type as any, payload);
  };

  return (
    <div className="h-full flex flex-col">
      <CharacterSelector
        selectedCharacterId={selectedCharacterId}
        onCharacterSelect={setSelectedCharacterId}
      />
      <div className="flex-1 overflow-hidden">
        <PlayerSheet character={character || null} onAction={handleAction} />
      </div>
    </div>
  );
}

function DMToolsWrapper() {
  const { data: monsters = [] } = useMonsters();
  const { data: campaigns = [] } = useCampaigns();

  const handleSpawnMonster = (monsterId: string) => {
    dispatchAction('SPAWN_MONSTER', { monsterId });
  };

  const handleUpdateHP = (entityId: string, hp: number) => {
    dispatchAction('UPDATE_HP', { entityId, hp });
  };

  return (
    <DMToolsWithCRUD
      monsters={monsters}
      campaigns={campaigns}
      onSpawnMonster={handleSpawnMonster}
      onUpdateHP={handleUpdateHP}
    />
  );
}

export const Workbench = () => {
  const [model, setModel] = useState<Model>(() => {
    // Try to load saved layout, fallback to default
    const savedLayout = loadLayout();
    return Model.fromJson(savedLayout || defaultLayout);
  });

  const handleModelChange = (newModel: Model) => {
    setModel(newModel);
    saveLayout(newModel.toJson());
  };

  return (
    <div className="relative flex-1 h-full w-full">
      <Layout 
        model={model} 
        factory={factory}
        onModelChange={handleModelChange}
      />
    </div>
  );
};
