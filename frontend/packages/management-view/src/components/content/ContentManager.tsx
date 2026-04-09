import React, { useState, useMemo } from "react";
import { DataTable } from "./DataTable";
import { EntityDetailPanel } from "./EntityDetailPanel";
import { useMonsters, useSpells, useItems, useSpecies, useClasses, useBackgrounds, useCompendiumPacks } from "../../hooks/useEntities";
import { Search, Plus, Database, GraduationCap, Users, Shield, BookOpen, Sword, Package } from "lucide-react";

type TabType = "bestiary" | "items" | "spells" | "species" | "classes" | "backgrounds";

export const ContentManager = () => {
  const [activeTab, setActiveTab] = useState<TabType>("bestiary");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEntity, setSelectedEntity] = useState<any | null>(null);
  const [selectedPackId, setSelectedPackId] = useState("");

  const { data: packs, isLoading: packsLoading } = useCompendiumPacks();

  const activePackId = useMemo(() => {
    if (selectedPackId) {
      return selectedPackId;
    }
    if (packs && packs.length > 0) {
      return String(packs[0].id);
    }
    return "";
  }, [packs, selectedPackId]);

  const { data: monsters, isLoading: monstersLoading } = useMonsters(activePackId || undefined);
  const { data: spells, isLoading: spellsLoading } = useSpells(activePackId || undefined);
  const { data: items, isLoading: itemsLoading } = useItems(activePackId || undefined);
  const { data: species, isLoading: speciesLoading } = useSpecies(activePackId || undefined);
  const { data: classes, isLoading: classesLoading } = useClasses(activePackId || undefined);
  const { data: backgrounds, isLoading: backgroundsLoading } = useBackgrounds(activePackId || undefined);

  const currentData = useMemo<any[]>(() => {
    let data: any[] = [];
    if (activeTab === "bestiary") data = monsters || [];
    if (activeTab === "spells") data = spells || [];
    if (activeTab === "items") data = items || [];
    if (activeTab === "species") data = species || [];
    if (activeTab === "classes") data = classes || [];
    if (activeTab === "backgrounds") data = backgrounds || [];

    if (!searchQuery) return data;

    const query = searchQuery.toLowerCase();
    return data.filter(
      (item: any) =>
        String(item.name || "")
          .toLowerCase()
          .includes(query) ||
        String(item.type || item.family || "")
          .toLowerCase()
          .includes(query),
    );
  }, [activeTab, monsters, spells, items, species, classes, backgrounds, searchQuery]);

  const isLoading = packsLoading || monstersLoading || spellsLoading || itemsLoading || speciesLoading || classesLoading || backgroundsLoading;

  return (
    <div className="w-full h-full flex flex-col bg-background">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-3xl font-heading text-foreground flex items-center gap-2">
            <Database className="text-primary" />
            Content Manager
          </h2>
          <p className="text-muted-foreground">Manage your homebrew compendium and rules elements.</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="min-w-56">
            <select
              value={activePackId}
              onChange={(event) => setSelectedPackId(event.target.value)}
              className="w-full px-3 py-2 bg-surface-100 border border-border rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
            >
              {packs && packs.length > 0 ? (
                packs.map((pack: any) => (
                  <option key={pack.id} value={pack.id}>
                    {pack.title || pack.id}
                  </option>
                ))
              ) : (
                <option value="">No packs available</option>
              )}
            </select>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
            <input
              type="text"
              placeholder="Search entities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 bg-surface-100 border border-border rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all w-64"
            />
          </div>
          <button className="btn btn-primary gradient-quest px-6 shadow-sm hover:scale-105 active:scale-95 transition-all flex items-center gap-2">
            <Plus size={18} />
            Add {activeTab === "bestiary" ? "Monster" : activeTab === "items" ? "Item" : "Spell"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border mb-6 overflow-x-auto pb-1 scrollbar-hide">
        <TabButton active={activeTab === "bestiary"} onClick={() => setActiveTab("bestiary")} label="Bestiary" icon={<Sword size={16} />} />
        <TabButton active={activeTab === "spells"} onClick={() => setActiveTab("spells")} label="Spells" icon={<BookOpen size={16} />} />
        <TabButton active={activeTab === "items"} onClick={() => setActiveTab("items")} label="Items" icon={<Package size={16} />} />
        <TabButton active={activeTab === "species"} onClick={() => setActiveTab("species")} label="Species" icon={<Users size={16} />} />
        <TabButton active={activeTab === "classes"} onClick={() => setActiveTab("classes")} label="Classes" icon={<Shield size={16} />} />
        <TabButton active={activeTab === "backgrounds"} onClick={() => setActiveTab("backgrounds")} label="Backgrounds" icon={<GraduationCap size={16} />} />
      </div>

      {/* Content Area */}
      <div className="flex-1 bg-surface-50 rounded-2xl border border-border overflow-hidden p-1 relative">
        {isLoading ? (
          <div className="h-full flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
            <p>Loading compendium data...</p>
          </div>
        ) : (
          <DataTable columns={getColumnsForTab(activeTab)} data={currentData} onRowClick={(item: any) => setSelectedEntity(item)} />
        )}
      </div>

      {/* Detail Slide-over */}
      <EntityDetailPanel entity={selectedEntity} isOpen={!!selectedEntity} onClose={() => setSelectedEntity(null)} />
    </div>
  );
};

const getColumnsForTab = (tab: TabType) => {
  switch (tab) {
    case "bestiary":
      return [
        { key: "name", label: "Name" },
        { key: "type", label: "Type" },
        { key: "challenge_rating", label: "CR" },
        { key: "armor_class", label: "AC" },
        { key: "hit_points", label: "HP" },
      ];
    case "items":
      return [
        { key: "name", label: "Name" },
        { key: "type", label: "Type" },
        { key: "rarity", label: "Rarity" },
        { key: "price", label: "Price (gp)" },
      ];
    case "spells":
      return [
        { key: "name", label: "Name" },
        { key: "level", label: "Level" },
        { key: "school", label: "School" },
        { key: "casting_time", label: "Time" },
      ];
    case "species":
      return [
        { key: "name", label: "Name" },
        { key: "size", label: "Size" },
        { key: "speed", label: "Speed" },
      ];
    case "classes":
      return [
        { key: "name", label: "Name" },
        { key: "hit_die", label: "Hit Die" },
      ];
    case "backgrounds":
      return [{ key: "name", label: "Name" }];
    default:
      return [{ key: "name", label: "Name" }];
  }
};

const TabButton = ({ active, onClick, label, icon }: { active: boolean; onClick: () => void; label: string; icon: React.ReactNode }) => (
  <button
    onClick={onClick}
    className={`px-6 py-3 font-semibold text-sm rounded-t-lg transition-colors border-b-2 flex items-center gap-2 whitespace-nowrap ${
      active ? "border-primary text-primary bg-surface-100/50" : "border-transparent text-muted-foreground hover:text-foreground hover:bg-surface-50"
    }`}
  >
    {icon}
    {label}
  </button>
);
