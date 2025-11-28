import type {
  ItemResponse,
  SpellResponse,
  MonsterResponse,
  CharacterResponse,
  CampaignResponse,
} from '@rpg/types';

export type PaginationParams = { skip?: number; limit?: number };
export type CharacterCreate = any;
export type CampaignCreate = any;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // If response is not JSON, use default message
    }
    throw new ApiError(errorMessage, response.status);
  }

  // Handle empty responses
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  
  return {} as T;
}

// Items API
export const itemsApi = {
  getItems: async (params?: PaginationParams): Promise<ItemResponse[]> => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    const query = queryParams.toString();
    return fetchApi<ItemResponse[]>(`/items/${query ? `?${query}` : ''}`);
  },

  getItem: async (itemId: string): Promise<ItemResponse> => {
    return fetchApi<ItemResponse>(`/items/${itemId}`);
  },
};

// Spells API
export const spellsApi = {
  getSpells: async (params?: PaginationParams): Promise<SpellResponse[]> => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    const query = queryParams.toString();
    return fetchApi<SpellResponse[]>(`/spells/${query ? `?${query}` : ''}`);
  },

  getSpell: async (spellId: string): Promise<SpellResponse> => {
    return fetchApi<SpellResponse>(`/spells/${spellId}`);
  },
};

// Monsters API
export const monstersApi = {
  getMonsters: async (params?: PaginationParams): Promise<MonsterResponse[]> => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    const query = queryParams.toString();
    return fetchApi<MonsterResponse[]>(`/monsters/${query ? `?${query}` : ''}`);
  },

  getMonster: async (monsterId: string): Promise<MonsterResponse> => {
    return fetchApi<MonsterResponse>(`/monsters/${monsterId}`);
  },
};

// Characters API
export const charactersApi = {
  getCharacters: async (params?: PaginationParams): Promise<CharacterResponse[]> => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    const query = queryParams.toString();
    return fetchApi<CharacterResponse[]>(`/characters/${query ? `?${query}` : ''}`);
  },

  getCharacter: async (characterId: string): Promise<CharacterResponse> => {
    return fetchApi<CharacterResponse>(`/characters/${characterId}`);
  },

  createCharacter: async (character: CharacterCreate): Promise<CharacterResponse> => {
    return fetchApi<CharacterResponse>('/characters', {
      method: 'POST',
      body: JSON.stringify(character),
    });
  },

  updateCharacter: async (characterId: string, character: Partial<CharacterCreate>): Promise<CharacterResponse> => {
    return fetchApi<CharacterResponse>(`/characters/${characterId}`, {
      method: 'PUT',
      body: JSON.stringify(character),
    });
  },

  deleteCharacter: async (characterId: string): Promise<void> => {
    return fetchApi<void>(`/characters/${characterId}`, {
      method: 'DELETE',
    });
  },
};

// Campaigns API
export const campaignsApi = {
  getCampaigns: async (params?: PaginationParams): Promise<CampaignResponse[]> => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    const query = queryParams.toString();
    return fetchApi<CampaignResponse[]>(`/campaigns/${query ? `?${query}` : ''}`);
  },

  getCampaign: async (campaignId: string): Promise<CampaignResponse> => {
    return fetchApi<CampaignResponse>(`/campaigns/${campaignId}`);
  },

  createCampaign: async (campaign: CampaignCreate): Promise<CampaignResponse> => {
    return fetchApi<CampaignResponse>('/campaigns', {
      method: 'POST',
      body: JSON.stringify(campaign),
    });
  },

  updateCampaign: async (campaignId: string, campaign: Partial<CampaignCreate>): Promise<CampaignResponse> => {
    return fetchApi<CampaignResponse>(`/campaigns/${campaignId}`, {
      method: 'PUT',
      body: JSON.stringify(campaign),
    });
  },

  deleteCampaign: async (campaignId: string): Promise<void> => {
    return fetchApi<void>(`/campaigns/${campaignId}`, {
      method: 'DELETE',
    });
  },
};

// Export all APIs
export const api = {
  items: itemsApi,
  spells: spellsApi,
  monsters: monstersApi,
  characters: charactersApi,
  campaigns: campaignsApi,
};

export { ApiError };



