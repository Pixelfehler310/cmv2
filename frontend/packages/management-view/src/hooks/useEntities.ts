import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@rpg/bridge";

type EntityRecord = Record<string, unknown> & {
  id: string;
  family?: string;
  name?: string;
};

type CompendiumMutationContext = {
  family?: string;
  packId?: string;
  definitionId?: string;
};

type CreateCompendiumDefinitionInput = {
  payload: Record<string, unknown>;
  campaignId?: string;
};

type UpdateCompendiumDefinitionInput = {
  definitionId: string;
  expectedContentVersion: number;
  updates: Record<string, unknown>;
  campaignId?: string;
  family?: string;
  packId?: string;
};

type DeleteCompendiumDefinitionInput = {
  definitionId: string;
  expectedContentVersion: number;
  campaignId?: string;
  family?: string;
  packId?: string;
};

const normalizeEntities = (input: Record<string, unknown>[]): EntityRecord[] => {
  return input.filter((row): row is EntityRecord => typeof row.id === "string").map((row) => ({ ...row }));
};

const invalidateCompendiumQueries = async (queryClient: ReturnType<typeof useQueryClient>, context: CompendiumMutationContext) => {
  const invalidations: Promise<unknown>[] = [queryClient.invalidateQueries({ queryKey: ["compendium-packs"] })];

  if (context.definitionId) {
    invalidations.push(queryClient.invalidateQueries({ queryKey: ["compendium-definition", context.definitionId] }));
  }

  if (context.family && context.packId) {
    invalidations.push(queryClient.invalidateQueries({ queryKey: ["compendium-family", context.family, context.packId] }));
  }

  await Promise.all(invalidations);
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

export const useCompendiumDefinition = (id: string | null) => {
  return useQuery({
    queryKey: ["compendium-definition", id],
    queryFn: () => apiClient.compendium.getDefinition(id!),
    enabled: !!id,
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

export const useCreateCompendiumPack = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { id: string; title: string }) => {
      return apiClient.compendium.createPack({
        ...payload,
        is_homebrew: true,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["compendium-packs"] });
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
  return useCompendiumDefinition(id);
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

export const useLoreDefinitions = (packId?: string) => {
  return useCompendiumFamily("lore", packId);
};

export const useConditions = (packId?: string) => {
  return useCompendiumFamily("condition", packId);
};

export const useFactions = (packId?: string) => {
  return useCompendiumFamily("faction", packId);
};

export const useRegions = (packId?: string) => {
  return useCompendiumFamily("region", packId);
};

export const usePlaces = (packId?: string) => {
  return useCompendiumFamily("place", packId);
};

export const useCreateCompendiumDefinition = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ payload, campaignId }: CreateCompendiumDefinitionInput) => {
      return apiClient.compendium.createDefinition(payload, campaignId);
    },
    onSuccess: async (createdDefinition) => {
      await invalidateCompendiumQueries(queryClient, {
        definitionId: typeof createdDefinition.id === "string" ? createdDefinition.id : undefined,
        family: typeof createdDefinition.family === "string" ? createdDefinition.family : undefined,
        packId: typeof createdDefinition.pack_id === "string" ? createdDefinition.pack_id : undefined,
      });
    },
  });
};

export const useUpdateCompendiumDefinition = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ definitionId, expectedContentVersion, updates, campaignId }: UpdateCompendiumDefinitionInput) => {
      return apiClient.compendium.updateDefinition(definitionId, {
        expected_content_version: expectedContentVersion,
        updates,
        campaign_id: campaignId,
      });
    },
    onSuccess: async (updatedDefinition, variables) => {
      await invalidateCompendiumQueries(queryClient, {
        definitionId: variables.definitionId,
        family: typeof updatedDefinition.family === "string" ? updatedDefinition.family : variables.family,
        packId: typeof updatedDefinition.pack_id === "string" ? updatedDefinition.pack_id : variables.packId,
      });
    },
  });
};

export const useDeleteCompendiumDefinition = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ definitionId, expectedContentVersion, campaignId }: DeleteCompendiumDefinitionInput) => {
      return apiClient.compendium.deleteDefinition(definitionId, expectedContentVersion, campaignId);
    },
    onSuccess: async (_, variables) => {
      await invalidateCompendiumQueries(queryClient, {
        definitionId: variables.definitionId,
        family: variables.family,
        packId: variables.packId,
      });
    },
  });
};
