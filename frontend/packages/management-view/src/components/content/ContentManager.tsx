import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FamilyTab, isLeafFamily, toFamilyTab } from "./config/familyConfig";
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
import { CompendiumContentPane } from "./layout/CompendiumContentPane";
import { CompendiumFamilyTabs } from "./layout/CompendiumFamilyTabs";
import { CompendiumHeader } from "./layout/CompendiumHeader";
import { CompendiumOverlayHost } from "./layout/CompendiumOverlayHost";

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

  const closeEditor = () => {
    setIsAdding(false);
    setEditingEntity(null);
  };

  return (
    <div className="w-full h-full flex flex-col bg-background">
      <CompendiumHeader
        activeFamily={activeFamily}
        activePackId={activePackId}
        packs={packs}
        searchQuery={searchQuery}
        hasPackSelection={hasPackSelection}
        onPackChange={setSelectedPackId}
        onSearchQueryChange={setSearchQuery}
        onCreatePack={() => setIsCreatePackDialogOpen(true)}
        onAddEntity={() => setIsAdding(true)}
      />

      <CompendiumFamilyTabs activeFamily={activeFamily} onSelectFamily={selectFamily} />

      <CompendiumContentPane
        activeFamily={activeFamily}
        hasPackSelection={hasPackSelection}
        isLoading={isLoading}
        data={currentData}
        onCreatePack={() => setIsCreatePackDialogOpen(true)}
        onRowClick={(item: any) => {
          if (isLeafFamily(activeFamily)) {
            setEditingEntity(item);
          } else {
            setSelectedEntity(item);
          }
        }}
      />

      <CompendiumOverlayHost
        activeFamily={activeFamily}
        activePackId={activePackId}
        selectedEntity={selectedEntity}
        isAdding={isAdding}
        editingEntity={editingEntity}
        isCreatePackDialogOpen={isCreatePackDialogOpen}
        onCloseDetail={() => setSelectedEntity(null)}
        onCloseEditor={closeEditor}
        onCloseCreatePack={() => setIsCreatePackDialogOpen(false)}
        onCreatePackSuccess={(newPackId) => {
          setSelectedPackId(newPackId);
          setIsCreatePackDialogOpen(false);
        }}
      />
    </div>
  );
};
