import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { DataTable } from "./DataTable";
import { EntityDetailPanel } from "./EntityDetailPanel";
import { getEditorComponent } from "./config/editorRegistry";
import {
  useMonsters,
  useSpells,
  useItems,
  useSpecies,
  useClasses,
  useBackgrounds,
  useCompendiumPacks,
  useLoreDefinitions,
  useConditions,
  useFactions,
  useRegions,
  usePlaces,
} from "../../hooks/useEntities";
import { Search, Plus, Database, GraduationCap, Users, Shield, BookOpen, Sword, Package, ScrollText, Link2, Flag, Globe2, MapPinned } from "lucide-react";
import { CreatePackDialog } from "./dialogs/CreatePackDialog";

type FamilyTab = "monster" | "item" | "spell" | "species" | "class" | "background" | "lore" | "condition" | "faction" | "region" | "place";

const FAMILY_TABS: FamilyTab[] = ["monster", "spell", "item", "species", "class", "background", "lore", "condition", "faction", "region", "place"];

const toFamilyTab = (value?: string): FamilyTab | null => {
  if (!value) {
    return null;
  }

  if (FAMILY_TABS.includes(value as FamilyTab)) {
    return value as FamilyTab;
  }

  if (value === "bestiary") return "monster";
  if (value === "spells") return "spell";
  if (value === "items") return "item";
  if (value === "classes") return "class";
  if (value === "backgrounds") return "background";

  return null;
};

const getAddLabel = (family: FamilyTab): string => {
  switch (family) {
    case "monster":
      return "Monster";
    case "spell":
      return "Spell";
    case "item":
      return "Item";
    case "species":
      return "Species";
    case "class":
      return "Class";
    case "background":
      return "Background";
    case "lore":
      return "Lore";
    case "condition":
      return "Condition";
    case "faction":
      return "Faction";
    case "region":
      return "Region";
    case "place":
      return "Place";
    default:
      return "Entry";
  }
};

export const ContentManager = ({ initialFamily }: { initialFamily?: string }) => {
  const navigate = useNavigate();
  const [activeFamily, setActiveFamily] = useState<FamilyTab>(toFamilyTab(initialFamily) ?? "monster");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEntity, setSelectedEntity] = useState<any | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [editingEntity, setEditingEntity] = useState<any | null>(null);
  const [selectedPackId, setSelectedPackId] = useState("");
  const [isCreatePackDialogOpen, setIsCreatePackDialogOpen] = useState(false);

  const { data: packs, isLoading: packsLoading } = useCompendiumPacks();

  useEffect(() => {
    const routeFamily = toFamilyTab(initialFamily);
    if (routeFamily && routeFamily !== activeFamily) {
      setActiveFamily(routeFamily);
      setSelectedEntity(null);
    }
  }, [activeFamily, initialFamily]);

  const activePackId = useMemo(() => selectedPackId, [selectedPackId]);

  const { data: monsters, isLoading: monstersLoading } = useMonsters(activePackId || undefined);
  const { data: spells, isLoading: spellsLoading } = useSpells(activePackId || undefined);
  const { data: items, isLoading: itemsLoading } = useItems(activePackId || undefined);
  const { data: species, isLoading: speciesLoading } = useSpecies(activePackId || undefined);
  const { data: classes, isLoading: classesLoading } = useClasses(activePackId || undefined);
  const { data: backgrounds, isLoading: backgroundsLoading } = useBackgrounds(activePackId || undefined);
  const { data: lore, isLoading: loreLoading } = useLoreDefinitions(activePackId || undefined);
  const { data: conditions, isLoading: conditionsLoading } = useConditions(activePackId || undefined);
  const { data: factions, isLoading: factionsLoading } = useFactions(activePackId || undefined);
  const { data: regions, isLoading: regionsLoading } = useRegions(activePackId || undefined);
  const { data: places, isLoading: placesLoading } = usePlaces(activePackId || undefined);

  const currentData = useMemo<any[]>(() => {
    let data: any[] = [];
    if (activeFamily === "monster") data = monsters || [];
    if (activeFamily === "spell") data = spells || [];
    if (activeFamily === "item") data = items || [];
    if (activeFamily === "species") data = species || [];
    if (activeFamily === "class") data = classes || [];
    if (activeFamily === "background") data = backgrounds || [];
    if (activeFamily === "lore") data = lore || [];
    if (activeFamily === "condition") data = conditions || [];
    if (activeFamily === "faction") data = factions || [];
    if (activeFamily === "region") data = regions || [];
    if (activeFamily === "place") data = places || [];

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
  }, [activeFamily, monsters, spells, items, species, classes, backgrounds, lore, conditions, factions, regions, places, searchQuery]);

  const isLoading =
    packsLoading ||
    monstersLoading ||
    spellsLoading ||
    itemsLoading ||
    speciesLoading ||
    classesLoading ||
    backgroundsLoading ||
    loreLoading ||
    conditionsLoading ||
    factionsLoading ||
    regionsLoading ||
    placesLoading;

  const hasPackSelection = !!activePackId;

  const selectFamily = (family: FamilyTab) => {
    setActiveFamily(family);
    setSelectedEntity(null);
    navigate(`/content/${family}`);
  };

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
          <div className="min-w-56 flex gap-2">
            <select
              value={activePackId}
              onChange={(event) => setSelectedPackId(event.target.value)}
              className="flex-1 w-full px-3 py-2 bg-surface-100 border border-border rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
            >
              <option value="">Select pack...</option>
              {packs && packs.length > 0 ? (
                packs.map((pack: any) => (
                  <option key={pack.id} value={pack.id}>
                    {pack.title || pack.id}
                  </option>
                ))
              ) : (
                <option value="" disabled>
                  No packs available
                </option>
              )}
            </select>
            <button onClick={() => setIsCreatePackDialogOpen(true)} className="px-3 py-2 bg-surface-100 border border-border rounded-xl hover:bg-surface-200 transition-colors" title="Create New Pack">
              <Plus size={18} className="text-primary" />
            </button>
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
          <button
            disabled={!hasPackSelection}
            onClick={() => setIsAdding(true)}
            className="btn btn-primary gradient-quest px-6 shadow-sm hover:scale-105 active:scale-95 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            <Plus size={18} />
            Add {getAddLabel(activeFamily)}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border mb-6 overflow-x-auto pb-1 scrollbar-hide">
        <TabButton active={activeFamily === "monster"} onClick={() => selectFamily("monster")} label="Bestiary" icon={<Sword size={16} />} />
        <TabButton active={activeFamily === "spell"} onClick={() => selectFamily("spell")} label="Spells" icon={<BookOpen size={16} />} />
        <TabButton active={activeFamily === "item"} onClick={() => selectFamily("item")} label="Items" icon={<Package size={16} />} />
        <TabButton active={activeFamily === "species"} onClick={() => selectFamily("species")} label="Species" icon={<Users size={16} />} />
        <TabButton active={activeFamily === "class"} onClick={() => selectFamily("class")} label="Classes" icon={<Shield size={16} />} />
        <TabButton active={activeFamily === "background"} onClick={() => selectFamily("background")} label="Backgrounds" icon={<GraduationCap size={16} />} />
        <TabButton active={activeFamily === "lore"} onClick={() => selectFamily("lore")} label="Lore" icon={<ScrollText size={16} />} />
        <TabButton active={activeFamily === "condition"} onClick={() => selectFamily("condition")} label="Conditions" icon={<Link2 size={16} />} />
        <TabButton active={activeFamily === "faction"} onClick={() => selectFamily("faction")} label="Factions" icon={<Flag size={16} />} />
        <TabButton active={activeFamily === "region"} onClick={() => selectFamily("region")} label="Regions" icon={<Globe2 size={16} />} />
        <TabButton active={activeFamily === "place"} onClick={() => selectFamily("place")} label="Places" icon={<MapPinned size={16} />} />
      </div>

      {/* Content Area */}
      <div className="flex-1 bg-surface-50 rounded-2xl border border-border overflow-hidden p-1 relative">
        {!hasPackSelection ? (
          <div className="h-full flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <Database className="opacity-60" />
            <p>Select or create a pack to load and manage definitions.</p>
            <button onClick={() => setIsCreatePackDialogOpen(true)} className="btn btn-secondary mt-2">
              Create Pack
            </button>
          </div>
        ) : isLoading ? (
          <div className="h-full flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
            <p>Loading compendium data...</p>
          </div>
        ) : (
          <DataTable
            columns={getColumnsForFamily(activeFamily)}
            data={currentData}
            onRowClick={(item: any) => {
              // For Leaf Bundle, go straight to Edit.
              const leafFamilies = ["lore", "condition", "species", "class", "background", "faction", "region", "place"];
              if (leafFamilies.includes(activeFamily)) {
                setEditingEntity(item);
              } else {
                setSelectedEntity(item);
              }
            }}
          />
        )}
      </div>

      {/* Detail Slide-over */}
      <EntityDetailPanel entity={selectedEntity} isOpen={!!selectedEntity} onClose={() => setSelectedEntity(null)} />

      {/* Editor Drawer (Simplified for Leaf Bundle) */}
      {(isAdding || editingEntity) && (
        <div className="fixed inset-0 z-50 flex items-center justify-end">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => {
              setIsAdding(false);
              setEditingEntity(null);
            }}
          />
          <div className="relative h-full w-full max-w-4xl bg-background border-l border-border shadow-2xl animate-in slide-in-from-right-full">
            {getEditorComponent(activeFamily, {
              initialData: editingEntity,
              packId: activePackId,
              onSave: () => {
                setIsAdding(false);
                setEditingEntity(null);
              },
              onCancel: () => {
                setIsAdding(false);
                setEditingEntity(null);
              },
            })}
          </div>
        </div>
      )}

      <CreatePackDialog
        isOpen={isCreatePackDialogOpen}
        onClose={() => setIsCreatePackDialogOpen(false)}
        onSuccess={(newPackId) => {
          setSelectedPackId(newPackId);
          setIsCreatePackDialogOpen(false);
        }}
      />
    </div>
  );
};

const getColumnsForFamily = (family: FamilyTab) => {
  switch (family) {
    case "monster":
      return [
        { key: "name", label: "Name" },
        { key: "type", label: "Type" },
        { key: "challenge_rating", label: "CR" },
        { key: "armor_class", label: "AC" },
        { key: "hit_points", label: "HP" },
      ];
    case "item":
      return [
        { key: "name", label: "Name" },
        { key: "type", label: "Type" },
        { key: "rarity", label: "Rarity" },
        { key: "price", label: "Price (gp)" },
      ];
    case "spell":
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
    case "class":
      return [
        { key: "name", label: "Name" },
        { key: "hit_die", label: "Hit Die" },
      ];
    case "background":
      return [{ key: "name", label: "Name" }];
    case "lore":
      return [
        { key: "name", label: "Name" },
        { key: "lore_type", label: "Type" },
      ];
    case "condition":
      return [
        { key: "name", label: "Name" },
        { key: "condition_type", label: "Type" },
        { key: "has_levels", label: "Levels" },
      ];
    case "faction":
      return [
        { key: "name", label: "Name" },
        { key: "alignment", label: "Alignment" },
        { key: "influence_tier", label: "Influence" },
      ];
    case "region":
      return [
        { key: "name", label: "Name" },
        { key: "climate", label: "Climate" },
      ];
    case "place":
      return [
        { key: "name", label: "Name" },
        { key: "place_type", label: "Place Type" },
      ];
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
