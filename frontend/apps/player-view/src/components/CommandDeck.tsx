import React, { useState, useRef } from "react";
import { useMyCharacter } from "../hooks/useMyCharacter";
import { useContainerSize } from "../hooks/useContainerSize";
import { Sword, Backpack, Scroll, User, Book, Shield, Zap, LayoutGrid, PanelTop } from "lucide-react";
import { clsx } from "clsx";

import { IHostBridge } from "@rpg/bridge";

type LayoutMode = "dock" | "sheet";

interface CommandDeckProps {
  bridge: IHostBridge;
  campaignId?: string;
}

export const CommandDeck: React.FC<CommandDeckProps> = ({ bridge, campaignId }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const containerSize = useContainerSize(containerRef);

  // Manual layout mode toggle (Option C - user control)
  const [layoutMode, setLayoutMode] = useState<LayoutMode>("dock");

  const activeCampaignId = campaignId || "campaign-1";
  const { data: character, isLoading, error } = useMyCharacter(bridge, activeCampaignId);
  const [activeTab, setActiveTab] = useState<"actions" | "inventory" | "spells" | "attributes" | "lore">("actions");

  if (isLoading) return <div className="p-4 text-muted">Loading character...</div>;
  if (error) return <div className="p-4 text-gaming-500">Error loading character</div>;
  if (!character) return <div className="p-4 text-muted">No character found for this campaign.</div>;

  const hpPercent = Math.min(100, Math.max(0, (character.current_hp / character.max_hp) * 100));
  const isSheetMode = layoutMode === "sheet";

  const toggleLayout = () => {
    setLayoutMode((prev) => (prev === "dock" ? "sheet" : "dock"));
  };

  return (
    <div ref={containerRef} className={clsx("w-full h-full bg-surface text-primary overflow-hidden transition-all", isSheetMode ? "flex flex-col" : "flex flex-row border-t border-default")}>
      {/* Layout Toggle Button */}
      <button
        onClick={toggleLayout}
        className="btn btn-ghost btn-sm absolute z-10 transition-all top-2 right-2"
        data-tooltip={isSheetMode ? "Switch to Dock Mode" : "Switch to Sheet Mode"}
        aria-label={isSheetMode ? "Switch to Dock Mode" : "Switch to Sheet Mode"}
      >
        {isSheetMode ? <LayoutGrid size={18} /> : <PanelTop size={18} />}
      </button>

      {/* Vitals Section */}
      <div className={clsx("bg-muted shrink-0 transition-all", isSheetMode ? "w-full p-4 border-b border-default" : "w-64 p-4 flex flex-col gap-4 border-r border-default")}>
        <div className={clsx("flex gap-3", isSheetMode ? "items-center justify-between" : "items-center")}>
          {/* Profile */}
          <div className="flex items-center gap-3">
            <div className="avatar avatar-lg gradient-vtt flex items-center justify-center shrink-0">
              <User className="w-6 h-6 text-white" />
            </div>
            <div className="min-w-0">
              <h2 className="font-bold text-lg truncate">{character.name}</h2>
              <div className="text-label-s text-secondary">
                Level {character.level} {character.class_id}
              </div>
            </div>
          </div>

          {/* Stats Row (Sheet mode: inline with profile) */}
          {isSheetMode && (
            <div className="flex gap-4 items-center">
              <StatBox icon={Shield} label="AC" value={character.armor_class} />
              <StatBox icon={Zap} label="Init" value={character.initiative >= 0 ? `+${character.initiative}` : character.initiative} iconClassName="text-spark-500" />
              <HPBar current={character.current_hp} max={character.max_hp} percent={hpPercent} compact />
            </div>
          )}
        </div>

        {/* HP & Stats (Dock mode: vertical layout) */}
        {!isSheetMode && (
          <>
            <HPBar current={character.current_hp} max={character.max_hp} percent={hpPercent} />
            <div className="grid grid-cols-2 gap-2 text-center">
              <StatBox icon={Shield} label="AC" value={character.armor_class} />
              <StatBox icon={Zap} label="Init" value={character.initiative >= 0 ? `+${character.initiative}` : character.initiative} iconClassName="text-spark-500" />
            </div>
          </>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0 relative">
        {/* Tabs Header */}
        <div className={clsx("flex border-b border-default bg-muted/50", isSheetMode && "justify-center")}>
          <TabButton active={activeTab === "actions"} onClick={() => setActiveTab("actions")} icon={<Sword size={16} />} label="Actions" compact={isSheetMode} />
          <TabButton active={activeTab === "inventory"} onClick={() => setActiveTab("inventory")} icon={<Backpack size={16} />} label="Inventory" compact={isSheetMode} />
          <TabButton active={activeTab === "spells"} onClick={() => setActiveTab("spells")} icon={<Scroll size={16} />} label="Spells" compact={isSheetMode} />
          <TabButton active={activeTab === "attributes"} onClick={() => setActiveTab("attributes")} icon={<User size={16} />} label="Attributes" compact={isSheetMode} />
          <TabButton active={activeTab === "lore"} onClick={() => setActiveTab("lore")} icon={<Book size={16} />} label="Lore" compact={isSheetMode} />
        </div>

        {/* Tab Content */}
        <div className={clsx("flex-1 p-4 overflow-y-auto bg-surface/50", isSheetMode && "pb-8")}>
          {activeTab === "actions" && <ActionsTab character={character} isSheetMode={isSheetMode} />}
          {activeTab === "inventory" && <InventoryTab character={character} isSheetMode={isSheetMode} />}
          {activeTab === "spells" && <SpellsTab character={character} isSheetMode={isSheetMode} />}
          {activeTab === "attributes" && <AttributesTab character={character} isSheetMode={isSheetMode} />}
          {activeTab === "lore" && <LoreTab character={character} isSheetMode={isSheetMode} />}
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

interface StatBoxProps {
  icon: React.FC<{ className?: string }>;
  label: string;
  value: string | number;
  iconClassName?: string;
}

const StatBox: React.FC<StatBoxProps> = ({ icon: Icon, label, value, iconClassName }) => (
  <div className="card card-flat p-2 text-center min-w-[60px]">
    <div className="text-label-s text-muted uppercase">{label}</div>
    <div className="font-bold text-xl flex items-center justify-center gap-1">
      <Icon className={clsx("w-4 h-4", iconClassName || "text-secondary")} />
      {value}
    </div>
  </div>
);

interface HPBarProps {
  current: number;
  max: number;
  percent: number;
  compact?: boolean;
}

const HPBar: React.FC<HPBarProps> = ({ current, max, percent, compact }) => (
  <div className={clsx("space-y-1", compact && "min-w-[120px]")}>
    <div className="flex justify-between text-label-s font-mono text-secondary">
      <span>HP</span>
      <span>
        {current} / {max}
      </span>
    </div>
    <div className="h-3 bg-muted rounded-full overflow-hidden border border-default">
      <div className="h-full bg-gaming-500 transition-all duration-500 ease-out" style={{ width: `${percent}%` }} />
    </div>
  </div>
);

// Tab Button Component

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  compact?: boolean;
}

const TabButton: React.FC<TabButtonProps> = ({ active, onClick, icon, label, compact }) => (
  <button
    onClick={onClick}
    className={clsx(
      "flex items-center gap-2 text-sm font-medium transition-all border-r border-default",
      compact ? "px-4 py-2" : "px-6 py-3",
      active ? "bg-vtt-900/30 text-vtt-300 border-b-2 border-b-vtt-500" : "text-secondary hover:bg-muted hover:text-primary",
    )}
  >
    {icon}
    {!compact && label}
  </button>
);

interface TabContentProps {
  character: any;
  isSheetMode?: boolean;
}

const ActionsTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => (
  <div className={clsx("grid gap-3", isSheetMode ? "grid-cols-2 sm:grid-cols-3 md:grid-cols-4" : "grid-cols-2 md:grid-cols-4 lg:grid-cols-6")}>
    {/* Default Actions */}
    <ActionButton name="Attack" type="physical" />
    <ActionButton name="Dash" type="utility" />
    <ActionButton name="Disengage" type="utility" />
    <ActionButton name="Dodge" type="utility" />

    {/* Character Specific Actions */}
    {character.actions?.map((action: any, i: number) => (
      <ActionButton key={i} name={action.name} type="class" />
    ))}
  </div>
);

const ActionButton = ({ name, type }: { name: string; type: "physical" | "utility" | "class" }) => {
  const colors = {
    physical: "bg-gaming-900/20 border-gaming-800 hover:bg-gaming-900/40 text-gaming-300",
    utility: "card card-flat hover:bg-muted text-secondary",
    class: "bg-vtt-900/20 border-vtt-800 hover:bg-vtt-900/40 text-vtt-300",
  };

  return (
    <button className={clsx("p-3 rounded-xl border text-left transition-all hover-lift flex flex-col gap-1", colors[type])}>
      <span className="font-bold text-sm">{name}</span>
      <span className="text-label-s opacity-70 uppercase tracking-wider">{type}</span>
    </button>
  );
};

const InventoryTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => (
  <div className={clsx("space-y-2", isSheetMode && "max-w-2xl mx-auto")}>
    {character.inventory?.length === 0 && <div className="text-muted italic">Inventory is empty.</div>}
    {character.inventory?.map((item: any, i: number) => (
      <div key={i} className="card card-flat flex items-center justify-between p-3">
        <span>{item.name}</span>
        <span className="badge badge-neutral">Qty: {item.quantity || 1}</span>
      </div>
    ))}
  </div>
);

const SpellsTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => (
  <div className={clsx("grid gap-4", isSheetMode ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2")}>
    {/* Group by level logic would go here */}
    <div className="space-y-2">
      <h3 className="text-label-s font-bold uppercase text-muted mb-2">Cantrips</h3>
      {character.spells
        ?.filter((s: any) => s.level === 0)
        .map((spell: any, i: number) => (
          <div key={i} className="card card-flat p-3 text-sm">
            {spell.name}
          </div>
        ))}
      {(!character.spells || character.spells.length === 0) && <div className="text-muted italic">No spells known.</div>}
    </div>
  </div>
);

const AttributesTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => {
  const attrs = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"];
  return (
    <div className={clsx("grid gap-4", isSheetMode ? "grid-cols-2 sm:grid-cols-3 max-w-xl mx-auto" : "grid-cols-3 md:grid-cols-6")}>
      {attrs.map((attr) => {
        const val = character[attr];
        const mod = Math.floor((val - 10) / 2);
        return (
          <div key={attr} className="card card-flat p-4 text-center hover-lift">
            <div className="text-label-s uppercase text-muted mb-1">{attr.substring(0, 3)}</div>
            <div className="text-2xl font-bold">{mod >= 0 ? `+${mod}` : mod}</div>
            <div className="text-label-s text-secondary font-mono">{val}</div>
          </div>
        );
      })}
    </div>
  );
};

const LoreTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => (
  <div className={clsx("prose prose-invert prose-sm", isSheetMode ? "max-w-2xl mx-auto" : "max-w-none")}>
    <h3 className="text-vtt-400">Background</h3>
    <p className="text-secondary">{character.background_id ? `Character has the ${character.background_id} background.` : "No background details available."}</p>
    {/* Future: Render full markdown lore here */}
  </div>
);
