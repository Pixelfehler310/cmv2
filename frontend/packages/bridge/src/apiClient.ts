import type { BackgroundResponse, ClassResponse, ItemResponse, MonsterResponse, SpeciesResponse, SpellResponse } from "@rpg/types";

export interface PaginationParams {
  skip?: number;
  limit?: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = this.resolveDefaultBaseUrl()) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  private resolveDefaultBaseUrl(): string {
    const meta = import.meta as unknown as {
      env?: {
        VITE_API_BASE_URL?: string;
      };
    };
    return meta.env?.VITE_API_BASE_URL ?? "/api";
  }

  private async fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, options);
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  public monsters = {
    list: (params: PaginationParams = {}) => {
      const query = new URLSearchParams(params as any).toString();
      return this.fetchJson<MonsterResponse[]>(`/monsters?${query}`);
    },
    get: (id: string) => this.fetchJson<MonsterResponse>(`/monsters/${id}`),
  };

  public spells = {
    list: (params: PaginationParams = {}) => {
      const query = new URLSearchParams(params as any).toString();
      return this.fetchJson<SpellResponse[]>(`/spells?${query}`);
    },
    get: (id: string) => this.fetchJson<SpellResponse>(`/spells/${id}`),
  };

  public items = {
    list: (params: PaginationParams = {}) => {
      const query = new URLSearchParams(params as any).toString();
      return this.fetchJson<ItemResponse[]>(`/items?${query}`);
    },
    get: (id: string) => this.fetchJson<ItemResponse>(`/items/${id}`),
  };

  public definitions = {
    species: () => this.fetchJson<SpeciesResponse[]>("/definitions/species"),
    classes: () => this.fetchJson<ClassResponse[]>("/definitions/classes"),
    backgrounds: () => this.fetchJson<BackgroundResponse[]>("/definitions/backgrounds"),
  };
}

export const apiClient = new ApiClient();
