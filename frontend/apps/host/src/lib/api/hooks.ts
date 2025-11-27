import { useState, useEffect } from 'react';
import { api, ApiError } from './client';
import type { PaginationParams } from '@rpg/types';

export interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => Promise<void>;
}

export function useApi<T>(
  fetchFn: () => Promise<T>,
  deps: any[] = []
): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError('Unknown error', 0));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, deps);

  return { data, loading, error, refetch: fetchData };
}

// Specific hooks for each resource
export function useItems(params?: PaginationParams) {
  return useApi(() => api.items.getItems(params), [params?.skip, params?.limit]);
}

export function useItem(itemId: string | null) {
  return useApi(() => {
    if (!itemId) throw new Error('Item ID is required');
    return api.items.getItem(itemId);
  }, [itemId]);
}

export function useSpells(params?: PaginationParams) {
  return useApi(() => api.spells.getSpells(params), [params?.skip, params?.limit]);
}

export function useSpell(spellId: string | null) {
  return useApi(() => {
    if (!spellId) throw new Error('Spell ID is required');
    return api.spells.getSpell(spellId);
  }, [spellId]);
}

export function useMonsters(params?: PaginationParams) {
  return useApi(() => api.monsters.getMonsters(params), [params?.skip, params?.limit]);
}

export function useMonster(monsterId: string | null) {
  return useApi(() => {
    if (!monsterId) throw new Error('Monster ID is required');
    return api.monsters.getMonster(monsterId);
  }, [monsterId]);
}

export function useCharacters(params?: PaginationParams) {
  return useApi(() => api.characters.getCharacters(params), [params?.skip, params?.limit]);
}

export function useCharacter(characterId: string | null) {
  return useApi(() => {
    if (!characterId) throw new Error('Character ID is required');
    return api.characters.getCharacter(characterId);
  }, [characterId]);
}

export function useCampaigns(params?: PaginationParams) {
  return useApi(() => api.campaigns.getCampaigns(params), [params?.skip, params?.limit]);
}

export function useCampaign(campaignId: string | null) {
  return useApi(() => {
    if (!campaignId) throw new Error('Campaign ID is required');
    return api.campaigns.getCampaign(campaignId);
  }, [campaignId]);
}



