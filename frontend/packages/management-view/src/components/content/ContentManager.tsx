import React, { useState } from "react";
import { DataTable } from "./DataTable";
import { MonsterForm } from "./forms/MonsterForm";

// Mock data for initial development
const MOCK_MONSTERS = [
  { id: "m1", name: "Goblin", type: "Humanoid", cr: "1/4", hp: 7, ac: 15 },
  { id: "m2", name: "Orc", type: "Humanoid", cr: "1/2", hp: 15, ac: 13 },
  { id: "m3", name: "Adult Red Dragon", type: "Dragon", cr: "17", hp: 256, ac: 19 },
  { id: "m4", name: "Gelatinous Cube", type: "Ooze", cr: "2", hp: 84, ac: 6 },
  { id: "m5", name: "Lich", type: "Undead", cr: "21", hp: 135, ac: 17 },
  { id: "m6", name: "Skeleton", type: "Undead", cr: "1/4", hp: 13, ac: 13 },
  { id: "m7", name: "Zombie", type: "Undead", cr: "1/4", hp: 22, ac: 8 },
  { id: "m8", name: "Owlbear", type: "Monstrosity", cr: "3", hp: 59, ac: 13 },
];

const MOCK_ITEMS = [
  { id: "i1", name: "Longsword", type: "Weapon", rarity: "Common", value: "15 gp" },
  { id: "i2", name: "Potion of Healing", type: "Potion", rarity: "Uncommon", value: "50 gp" },
  { id: "i3", name: "Ring of Protection", type: "Ring", rarity: "Rare", value: "3500 gp" },
];

type TabType = "bestiary" | "items" | "spells";

export const ContentManager = () => {
  const [activeTab, setActiveTab] = useState<TabType>("bestiary");

  return (
    <div className="w-full h-full flex flex-col bg-background">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-heading text-foreground">Content Manager</h2>
          <p className="text-muted-foreground">Manage your homebrew compendium and rules elements.</p>
        </div>
        <button className="btn btn-primary gradient-quest px-6 shadow-sm hover:scale-105 active:scale-95 transition-all">
          + Add {activeTab === "bestiary" ? "Monster" : activeTab === "items" ? "Item" : "Spell"}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border mb-6">
        <TabButton active={activeTab === "bestiary"} onClick={() => setActiveTab("bestiary")} label="Bestiary" />
        <TabButton active={activeTab === "items"} onClick={() => setActiveTab("items")} label="Items" />
        <TabButton active={activeTab === "spells"} onClick={() => setActiveTab("spells")} label="Spells" />
      </div>

      {/* Content Area */}
      <div className="flex-1 bg-surface-50 rounded-2xl border border-border overflow-hidden p-1">
        {activeTab === "bestiary" && (
          <DataTable
            columns={[
              { key: "name", label: "Name" },
              { key: "type", label: "Type" },
              { key: "cr", label: "CR" },
              { key: "ac", label: "Armor Class" },
              { key: "hp", label: "Hit Points" },
            ]}
            data={MOCK_MONSTERS}
          />
        )}

        {activeTab === "items" && (
          <DataTable
            columns={[
              { key: "name", label: "Name" },
              { key: "type", label: "Type" },
              { key: "rarity", label: "Rarity" },
              { key: "value", label: "Value" },
            ]}
            data={MOCK_ITEMS}
          />
        )}

        {activeTab === "spells" && <div className="h-full flex items-center justify-center text-muted-foreground">Spells database coming soon...</div>}
      </div>
    </div>
  );
};

const TabButton = ({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) => (
  <button
    onClick={onClick}
    className={`px-6 py-3 font-semibold text-sm rounded-t-lg transition-colors border-b-2 ${
      active ? "border-primary text-primary bg-surface-100/50" : "border-transparent text-muted-foreground hover:text-foreground hover:bg-surface-50"
    }`}
  >
    {label}
  </button>
);
