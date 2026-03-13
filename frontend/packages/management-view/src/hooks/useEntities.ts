import { useQuery } from "@tanstack/react-query";
import { apiClient, MonsterResponse, SpellResponse, ItemResponse } from "@rpg/bridge";

export const useMonsters = (params = {}) => {
  return useQuery({
    queryKey: ["monsters", params],
    queryFn: () => apiClient.monsters.list(params),
  });
};

export const useSpells = (params = {}) => {
  return useQuery({
    queryKey: ["spells", params],
    queryFn: () => apiClient.spells.list(params),
  });
};

export const useItems = (params = {}) => {
  return useQuery({
    queryKey: ["items", params],
    queryFn: () => apiClient.items.list(params),
  });
};

export const useMonster = (id: string | null) => {
  return useQuery({
    queryKey: ["monster", id],
    queryFn: () => apiClient.monsters.get(id!),
    enabled: !!id,
  });
};

export const useSpecies = () => {
  return useQuery({
    queryKey: ["species"],
    queryFn: () => apiClient.definitions.species(),
  });
};

export const useClasses = () => {
  return useQuery({
    queryKey: ["classes"],
    queryFn: () => apiClient.definitions.classes(),
  });
};

export const useBackgrounds = () => {
  return useQuery({
    queryKey: ["backgrounds"],
    queryFn: () => apiClient.definitions.backgrounds(),
  });
};
