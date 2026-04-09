import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@rpg/bridge";

type EntityRecord = Record<string, unknown> & {
  id: string;
  family?: string;
  name?: string;
};

const normalizeEntities = (input: Record<string, unknown>[]): EntityRecord[] => {
  return input.filter((row): row is EntityRecord => typeof row.id === "string").map((row) => ({ ...row }));
};

const useCompendiumFamily = (family: string, packId?: string) => {
  return useQuery({
    queryKey: ["compendium-family", family, packId],
    queryFn: async () => {
      if (!packId) {
        return [] as EntityRecord[];
      }
      const rows = await apiClient.compendium.listDefinitions(packId, family);
      return normalizeEntities(rows);
    },
    enabled: !!packId,
  });
};

export const useCompendiumPacks = () => {
  return useQuery({
    queryKey: ["compendium-packs"],
    queryFn: async () => {
      const rows = await apiClient.compendium.listPacks();
      return rows.filter((row): row is EntityRecord => typeof row.id === "string");
    },
  });
};

export const useMonsters = (packId?: string) => {
  return useCompendiumFamily("monster", packId);
};

export const useSpells = (packId?: string) => {
  return useCompendiumFamily("spell", packId);
};

export const useItems = (packId?: string) => {
  return useCompendiumFamily("item", packId);
};

export const useMonster = (id: string | null) => {
  return useQuery({
    queryKey: ["monster", id],
    queryFn: () => apiClient.compendium.getDefinition(id!),
    enabled: !!id,
  });
};

export const useSpecies = (packId?: string) => {
  return useCompendiumFamily("species", packId);
};

export const useClasses = (packId?: string) => {
  return useCompendiumFamily("class", packId);
};

export const useBackgrounds = (packId?: string) => {
  return useCompendiumFamily("background", packId);
};
