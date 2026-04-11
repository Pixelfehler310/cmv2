import type { BackgroundResponse, ClassResponse, ItemResponse, MonsterResponse, SpeciesResponse, SpellResponse } from "@rpg/types";

export interface PaginationParams {
  skip?: number;
  limit?: number;
}

export interface CompendiumPackCreateRequest {
  id: string;
  title: string;
  author_user_id?: string | null;
  is_homebrew?: boolean;
  pack_key?: string | null;
  compatibility_target?: string | null;
}

export interface CompendiumUpdateRequest {
  expected_content_version: number;
  updates: Record<string, unknown>;
  campaign_id?: string | null;
}

export interface CompendiumSupersedeRequest {
  new_definition_id: string;
  campaign_id?: string | null;
}

export interface CompendiumSearchParams {
  q?: string;
  family?: string;
  lifecycle_state?: string;
  pack_id?: string;
  payload_filters?: Record<string, string | number | boolean>;
  limit?: number;
  offset?: number;
  include_contract?: boolean;
}

export interface CharacterSheetParams {
  catalog_revision: number;
}

export interface CharacterListParams {
  campaign_id: string;
  player_id: string;
}

export interface CharacterCommandEnvelope<TPayload = unknown> {
  request_id: string;
  status: string;
  reason_code?: string | null;
  catalog_revision?: number | null;
  payload: TPayload;
}

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly statusText: string;
  public readonly detail: unknown;

  constructor(status: number, statusText: string, detail: unknown) {
    const fallbackMessage = `API Error: ${status} ${statusText}`;
    const detailMessage = ApiClientError.extractDetailMessage(detail);
    super(detailMessage ?? fallbackMessage);
    this.name = "ApiClientError";
    this.status = status;
    this.statusText = statusText;
    this.detail = detail;
  }

  private static extractDetailMessage(detail: unknown): string | null {
    if (!detail || typeof detail !== "object") {
      return null;
    }

    const detailObject = detail as { message?: unknown };
    if (typeof detailObject.message === "string" && detailObject.message.trim().length > 0) {
      return detailObject.message;
    }

    if (detailObject.message && typeof detailObject.message === "object") {
      const nested = detailObject.message as { summary?: unknown };
      if (typeof nested.summary === "string" && nested.summary.trim().length > 0) {
        return nested.summary;
      }
    }

    return null;
  }
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

    const text = await response.text();
    if (!response.ok) {
      let parsedError: unknown = undefined;
      if (text) {
        try {
          const parsedBody = JSON.parse(text) as { detail?: unknown };
          parsedError = parsedBody.detail ?? parsedBody;
        } catch {
          parsedError = text;
        }
      }
      throw new ApiClientError(response.status, response.statusText, parsedError);
    }

    if (response.status === 204 || !text) {
      return undefined as T;
    }

    if (!text) {
      return undefined as T;
    }
    return JSON.parse(text) as T;
  }

  private buildQuery(params: Record<string, unknown>): string {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") {
        return;
      }
      query.append(key, String(value));
    });
    return query.toString();
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

  public compendium = {
    createPack: (payload: CompendiumPackCreateRequest) =>
      this.fetchJson<Record<string, unknown>>("/compendium/packs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),

    listPacks: (lifecycle_state?: string) => {
      const query = this.buildQuery({ lifecycle_state });
      return this.fetchJson<Record<string, unknown>[]>(`/compendium/packs${query ? `?${query}` : ""}`);
    },

    getPack: (packId: string) => this.fetchJson<Record<string, unknown>>(`/compendium/packs/${encodeURIComponent(packId)}`),

    createDefinition: (payload: Record<string, unknown>, campaign_id?: string) => {
      const query = this.buildQuery({ campaign_id });
      return this.fetchJson<Record<string, unknown>>(`/compendium/definitions${query ? `?${query}` : ""}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },

    listDefinitions: (packId: string, family?: string) => {
      const query = this.buildQuery({ pack_id: packId, family });
      return this.fetchJson<Record<string, unknown>[]>(`/compendium/definitions?${query}`);
    },

    getDefinition: (definitionId: string) => this.fetchJson<Record<string, unknown>>(`/compendium/definitions/${encodeURIComponent(definitionId)}`),

    updateDefinition: (definitionId: string, payload: CompendiumUpdateRequest) =>
      this.fetchJson<Record<string, unknown>>(`/compendium/definitions/${encodeURIComponent(definitionId)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),

    deleteDefinition: (definitionId: string, expected_content_version: number, campaign_id?: string) => {
      const query = this.buildQuery({ expected_content_version, campaign_id });
      return this.fetchJson<void>(`/compendium/definitions/${encodeURIComponent(definitionId)}?${query}`, {
        method: "DELETE",
      });
    },

    publishDefinition: (definitionId: string, campaign_id?: string) =>
      this.fetchJson<Record<string, unknown>>(`/compendium/definitions/${encodeURIComponent(definitionId)}/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ campaign_id: campaign_id ?? null }),
      }),

    supersedeDefinition: (definitionId: string, payload: CompendiumSupersedeRequest) =>
      this.fetchJson<Record<string, unknown>>(`/compendium/definitions/${encodeURIComponent(definitionId)}/supersede`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),

    search: (params: CompendiumSearchParams = {}) => {
      const { payload_filters, ...rest } = params;
      const queryParams: Record<string, unknown> = { ...rest };

      if (payload_filters) {
        Object.entries(payload_filters).forEach(([key, value]) => {
          if (value === undefined || value === null || value === "") {
            return;
          }
          queryParams[`pf_${key}`] = value;
        });
      }

      const query = this.buildQuery(queryParams);
      return this.fetchJson<Record<string, unknown> | Record<string, unknown>[]>(`/compendium/search${query ? `?${query}` : ""}`);
    },

    getLinks: (definitionId: string, include_contract: boolean = false) => {
      const query = this.buildQuery({ include_contract });
      return this.fetchJson<Record<string, unknown>>(`/compendium/definitions/${encodeURIComponent(definitionId)}/links${query ? `?${query}` : ""}`);
    },

    getReplacementChain: (definitionId: string, include_contract: boolean = false) => {
      const query = this.buildQuery({ include_contract });
      return this.fetchJson<Record<string, unknown>>(`/compendium/definitions/${encodeURIComponent(definitionId)}/replacement-chain${query ? `?${query}` : ""}`);
    },
  };

  public characters = {
    list: (params: CharacterListParams) => {
      const query = this.buildQuery({
        campaign_id: params.campaign_id,
        player_id: params.player_id,
      });
      return this.fetchJson<CharacterCommandEnvelope<Record<string, unknown>[]>>(`/characters?${query}`);
    },

    create: (payload: Record<string, unknown>) =>
      this.fetchJson<CharacterCommandEnvelope>("/characters", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),

    update: (characterId: string, payload: Record<string, unknown>) =>
      this.fetchJson<CharacterCommandEnvelope>(`/characters/${encodeURIComponent(characterId)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),

    getSheet: (characterId: string, params: CharacterSheetParams) => {
      const query = this.buildQuery({ catalog_revision: params.catalog_revision });
      return this.fetchJson<CharacterCommandEnvelope>(`/characters/${encodeURIComponent(characterId)}/sheet?${query}`);
    },
  };
}

export const apiClient = new ApiClient();
