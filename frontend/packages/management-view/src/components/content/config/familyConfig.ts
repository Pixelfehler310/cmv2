export type FamilyTab = "monster" | "item" | "spell" | "species" | "class" | "background" | "lore" | "condition" | "faction" | "region" | "place";

const LEGACY_FAMILY_ALIASES: Record<string, FamilyTab> = {
  bestiary: "monster",
  spells: "spell",
  items: "item",
  classes: "class",
  backgrounds: "background",
};

const ADD_LABELS: Record<FamilyTab, string> = {
  monster: "Monster",
  spell: "Spell",
  item: "Item",
  species: "Species",
  class: "Class",
  background: "Background",
  lore: "Lore",
  condition: "Condition",
  faction: "Faction",
  region: "Region",
  place: "Place",
};

const LEAF_FAMILIES: FamilyTab[] = ["lore", "condition", "species", "class", "background", "faction", "region", "place"];

const COLUMNS_BY_FAMILY: Record<FamilyTab, Array<{ key: string; label: string }>> = {
  monster: [
    { key: "name", label: "Name" },
    { key: "type", label: "Type" },
    { key: "challenge_rating", label: "CR" },
    { key: "armor_class", label: "AC" },
    { key: "hit_points", label: "HP" },
  ],
  item: [
    { key: "name", label: "Name" },
    { key: "type", label: "Type" },
    { key: "rarity", label: "Rarity" },
    { key: "price", label: "Price (gp)" },
  ],
  spell: [
    { key: "name", label: "Name" },
    { key: "level", label: "Level" },
    { key: "school", label: "School" },
    { key: "casting_time", label: "Time" },
  ],
  species: [
    { key: "name", label: "Name" },
    { key: "size", label: "Size" },
    { key: "speed", label: "Speed" },
  ],
  class: [
    { key: "name", label: "Name" },
    { key: "hit_die", label: "Hit Die" },
  ],
  background: [{ key: "name", label: "Name" }],
  lore: [
    { key: "name", label: "Name" },
    { key: "lore_type", label: "Type" },
  ],
  condition: [
    { key: "name", label: "Name" },
    { key: "condition_type", label: "Type" },
    { key: "has_levels", label: "Levels" },
  ],
  faction: [
    { key: "name", label: "Name" },
    { key: "alignment", label: "Alignment" },
    { key: "influence_tier", label: "Influence" },
  ],
  region: [
    { key: "name", label: "Name" },
    { key: "climate", label: "Climate" },
  ],
  place: [
    { key: "name", label: "Name" },
    { key: "place_type", label: "Place Type" },
  ],
};

export const FAMILY_TABS: FamilyTab[] = ["monster", "spell", "item", "species", "class", "background", "lore", "condition", "faction", "region", "place"];

export const toFamilyTab = (value?: string): FamilyTab | null => {
  if (!value) {
    return null;
  }

  if (FAMILY_TABS.includes(value as FamilyTab)) {
    return value as FamilyTab;
  }

  return LEGACY_FAMILY_ALIASES[value] ?? null;
};

export const getAddLabel = (family: FamilyTab): string => {
  return ADD_LABELS[family] ?? "Entry";
};

export const isLeafFamily = (family: FamilyTab): boolean => {
  return LEAF_FAMILIES.includes(family);
};

export const getColumnsForFamily = (family: FamilyTab): Array<{ key: string; label: string }> => {
  return COLUMNS_BY_FAMILY[family] ?? [{ key: "name", label: "Name" }];
};
