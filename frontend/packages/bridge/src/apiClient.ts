export interface GameEntity {
  id: string;
  name: string;
  description?: string;
  effects: any[];
}

export interface MonsterResponse extends GameEntity {
  size: string;
  type: string;
  alignment: string;
  armor_class: number;
  hit_points: number;
  challenge_rating: number;
}

export interface SpellResponse extends GameEntity {
  level: number;
  school: string;
  casting_time: string;
  range: string;
  duration: string;
}

export interface ItemResponse extends GameEntity {
  type: string;
  rarity: string;
  weight: number;
  price: number;
}

export interface SpeciesResponse extends GameEntity {
  size: string;
  speed: number;
}

export interface ClassResponse extends GameEntity {
  hit_die: string;
}

export interface BackgroundResponse extends GameEntity {}

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
