import { create } from "zustand";

// --- Type Definitions based on Backend JSON Serialization ---
export interface CombatantState {
  id: string;
  public_name: string;
  x: number;
  y: number;
  size?: string;
  action_used?: boolean;
  bonus_action_used?: boolean;
  movement_remaining?: number;

  // DM Only
  hp_current?: number;
  hp_max?: number;

  // Stage View (Observer) Only
  hp_percent?: number;
}

export interface GameState {
  round: number;
  combatants: CombatantState[];
  activeIndex?: number;
}

export interface CombatLogEntry {
  timestamp: string;
  direction: "SEND" | "RECV" | "ERROR";
  type: string;
  payload: any;
  message?: string;
}

export type CombatActionDispatcher = (actionType: string, payload: any) => Promise<any>;

export interface CombatStore {
  // State
  gameState: GameState | null;
  isConnected: boolean;
  role: "dm" | "observer" | null;
  errorMessage: string | null;
  commandLog: CombatLogEntry[];
  actionDispatcher: CombatActionDispatcher | null;

  // Actions
  connect: (campaignId: string, role: "dm" | "observer") => void;
  disconnect: () => void;
  setConnectionStatus: (isConnected: boolean, role?: "dm" | "observer") => void;
  setActionDispatcher: (dispatcher: CombatActionDispatcher | null) => void;
  ingestEnvelope: (message: any) => void;
  clearCommandLog: () => void;
  dispatchRawEnvelope: (type: string, payload: any) => Promise<any>;

  // DM Intents
  dispatchIntent: (action: string, payload: any) => void;
  moveToken: (targetId: string, path: [number, number][]) => void;
  removeActor: (actorId: string) => void;
  endTurn: () => void;
  applyDamage: (targetId: string, amount: number, damageType: string) => void;
  dispatchAction: (actionType: string, payload: any) => void;
}

type BackendToken = {
  actor_id: string;
  position?: { x: number; y: number };
  size?: string;
};

type BackendActor = {
  id: string;
  name?: string;
  actor_type?: string;
  position?: { x: number; y: number };
  current_hp?: number;
  max_hp?: number;
  health_descriptor?: string;
};

type BackendEncounter = {
  round_number?: number;
  active_index?: number;
  combatants?: BackendActor[];
  map?: {
    tokens?: BackendToken[];
  };
};

const DEFAULT_HP_PERCENT_BY_DESCRIPTOR: Record<string, number> = {
  healthy: 1,
  "lightly wounded": 0.8,
  bloodied: 0.5,
  "badly wounded": 0.3,
  "near death": 0.1,
  dead: 0,
};

function toUiSize(rawSize?: string): string {
  if (!rawSize) {
    return "Medium";
  }
  const lowered = rawSize.toLowerCase();
  return lowered.charAt(0).toUpperCase() + lowered.slice(1);
}

function mapBackendEncounterToGameState(encounter: BackendEncounter): GameState {
  const tokenByActorId = new Map<string, BackendToken>();
  for (const token of encounter.map?.tokens ?? []) {
    if (token?.actor_id) {
      tokenByActorId.set(token.actor_id, token);
    }
  }

  const combatants: CombatantState[] = (encounter.combatants ?? []).map((actor) => {
    const token = tokenByActorId.get(actor.id);
    const pos = token?.position ?? actor.position ?? { x: 0, y: 0 };
    const hpDescriptor = actor.health_descriptor?.toLowerCase();
    const hpPercent = hpDescriptor ? DEFAULT_HP_PERCENT_BY_DESCRIPTOR[hpDescriptor] : undefined;

    return {
      id: actor.id,
      public_name: actor.name ?? actor.id,
      x: pos.x ?? 0,
      y: pos.y ?? 0,
      size: toUiSize(token?.size),
      hp_current: actor.current_hp,
      hp_max: actor.max_hp,
      hp_percent: hpPercent,
      action_used: false,
      bonus_action_used: false,
      movement_remaining: 30,
    };
  });

  return {
    round: encounter.round_number ?? 0,
    activeIndex: encounter.active_index ?? 0,
    combatants,
  };
}

function applyActorMove(state: GameState, payload: any): GameState {
  const movedTo = payload?.position;
  if (!payload?.actor_id || !movedTo) {
    return state;
  }

  return {
    ...state,
    combatants: state.combatants.map((c) =>
      c.id === payload.actor_id
        ? {
            ...c,
            x: movedTo.x ?? c.x,
            y: movedTo.y ?? c.y,
          }
        : c,
    ),
  };
}

function applyActorAdded(state: GameState, payload: any): GameState {
  const actor = payload?.actor;
  const token = payload?.token;
  if (!actor?.id) {
    return state;
  }

  const existing = state.combatants.some((c) => c.id === actor.id);
  if (existing) {
    return state;
  }

  const pos = token?.position ?? actor.position ?? { x: 0, y: 0 };

  return {
    ...state,
    combatants: [
      ...state.combatants,
      {
        id: actor.id,
        public_name: actor.name ?? actor.id,
        x: pos.x ?? 0,
        y: pos.y ?? 0,
        size: toUiSize(token?.size),
        hp_current: actor.current_hp,
        hp_max: actor.max_hp,
        hp_percent: undefined,
        action_used: false,
        bonus_action_used: false,
        movement_remaining: 30,
      },
    ],
  };
}

function applyActorRemoved(state: GameState, actorId: string): GameState {
  const nextCombatants = state.combatants.filter((c) => c.id !== actorId);
  let nextActiveIndex = state.activeIndex ?? 0;

  if (nextCombatants.length === 0) {
    nextActiveIndex = 0;
  } else if (nextActiveIndex >= nextCombatants.length) {
    nextActiveIndex = 0;
  }

  return {
    ...state,
    activeIndex: nextActiveIndex,
    combatants: nextCombatants,
  };
}

function applyHpUpdate(state: GameState, actorId: string, newHp: number): GameState {
  return {
    ...state,
    combatants: state.combatants.map((c) =>
      c.id === actorId
        ? {
            ...c,
            hp_current: newHp,
            hp_percent: typeof c.hp_max === "number" && c.hp_max > 0 ? Math.max(0, Math.min(1, newHp / c.hp_max)) : c.hp_percent,
          }
        : c,
    ),
  };
}

function applyActorDeath(state: GameState, actorId: string): GameState {
  return applyHpUpdate(state, actorId, 0);
}

function setCombatantPosition(state: GameState, actorId: string, x: number, y: number): GameState {
  return {
    ...state,
    combatants: state.combatants.map((c) =>
      c.id === actorId
        ? {
            ...c,
            x,
            y,
          }
        : c,
    ),
  };
}

const COMMAND_LOG_LIMIT = 200;

function createLogEntry(direction: "SEND" | "RECV" | "ERROR", type: string, payload: any, message?: string): CombatLogEntry {
  return {
    timestamp: new Date().toISOString(),
    direction,
    type,
    payload,
    message,
  };
}

function appendLogEntry(commandLog: CombatLogEntry[], entry: CombatLogEntry): CombatLogEntry[] {
  const next = [...commandLog, entry];
  if (next.length <= COMMAND_LOG_LIMIT) {
    return next;
  }
  return next.slice(next.length - COMMAND_LOG_LIMIT);
}

export const useCombatStore = create<CombatStore>((set, get) => ({
  gameState: null,
  isConnected: false,
  role: null,
  errorMessage: null,
  commandLog: [],
  actionDispatcher: null,

  connect: (_campaignId: string, role: "dm" | "observer") => {
    set((current) => ({
      role,
      errorMessage: null,
      commandLog: appendLogEntry(current.commandLog, createLogEntry("RECV", "connection_role_set", { role })),
    }));
  },

  disconnect: () => {
    set({
      isConnected: false,
      role: null,
      gameState: null,
      actionDispatcher: null,
    });
  },

  setConnectionStatus: (isConnected: boolean, role?: "dm" | "observer") => {
    set((current) => ({
      isConnected,
      role: role ?? current.role,
    }));
  },

  setActionDispatcher: (dispatcher: CombatActionDispatcher | null) => {
    set({ actionDispatcher: dispatcher });
  },

  ingestEnvelope: (message: any) => {
    let envelope = message;
    if (typeof message === "string") {
      try {
        envelope = JSON.parse(message);
      } catch (error) {
        const parseMessage = error instanceof Error ? error.message : "Failed to parse envelope";
        set((current) => ({
          errorMessage: parseMessage,
          commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", "invalid_envelope", message, parseMessage)),
        }));
        return;
      }
    }

    if (!envelope?.type) {
      return;
    }

    set((current) => ({
      commandLog: appendLogEntry(current.commandLog, createLogEntry("RECV", envelope.type, envelope.payload)),
    }));

    if (envelope.type === "error") {
      const nextErrorMessage = envelope.payload?.message ?? "WebSocket error";
      const errorCode = envelope.payload?.code ?? "unknown";
      set({ errorMessage: `${nextErrorMessage} (${errorCode})` });
      return;
    }

    if (envelope.type === "state_sync") {
      set({ gameState: mapBackendEncounterToGameState(envelope.payload) });
      return;
    }

    if (envelope.type === "actor_moved") {
      set((current) => ({
        gameState: current.gameState ? applyActorMove(current.gameState, envelope.payload) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "actor_added") {
      set((current) => ({
        gameState: current.gameState ? applyActorAdded(current.gameState, envelope.payload) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "actor_removed") {
      set((current) => ({
        gameState: current.gameState && envelope.payload?.actor_id ? applyActorRemoved(current.gameState, envelope.payload.actor_id) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "actor_damaged" || envelope.type === "actor_healed") {
      set((current) => ({
        gameState: current.gameState && envelope.payload?.actor_id ? applyHpUpdate(current.gameState, envelope.payload.actor_id, envelope.payload.new_hp) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "actor_died") {
      set((current) => ({
        gameState: current.gameState && envelope.payload?.actor_id ? applyActorDeath(current.gameState, envelope.payload.actor_id) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "turn_advanced") {
      set((current) => {
        if (!current.gameState) {
          return { gameState: current.gameState };
        }

        const nextActiveIndex = current.gameState.combatants.findIndex((c) => c.id === envelope.payload?.active_actor_id);

        return {
          gameState: {
            ...current.gameState,
            round: envelope.payload?.round ?? current.gameState.round,
            activeIndex: nextActiveIndex >= 0 ? nextActiveIndex : current.gameState.activeIndex,
          },
        };
      });
    }
  },

  clearCommandLog: () => {
    set({ commandLog: [] });
  },

  dispatchRawEnvelope: async (type: string, payload: any) => {
    const { actionDispatcher } = get();

    set((current) => ({
      commandLog: appendLogEntry(current.commandLog, createLogEntry("SEND", type, payload)),
    }));

    if (!actionDispatcher) {
      const message = "No action dispatcher configured.";
      set((current) => ({
        errorMessage: message,
        commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", type, payload, message)),
      }));
      throw new Error(message);
    }

    try {
      const result = await actionDispatcher(type, payload);

      if (result && typeof result === "object" && "success" in result && result.success === false) {
        const message = typeof result.error === "string" ? result.error : "Command dispatch failed";
        set((current) => ({
          errorMessage: message,
          commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", type, payload, message)),
        }));

        const handledError = new Error(message) as Error & { alreadyLogged?: boolean };
        handledError.alreadyLogged = true;
        throw handledError;
      }

      return result;
    } catch (error) {
      if (error instanceof Error && (error as Error & { alreadyLogged?: boolean }).alreadyLogged) {
        throw error;
      }

      const message = error instanceof Error ? error.message : "Failed to dispatch action";
      set((current) => ({
        errorMessage: message,
        commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", type, payload, message)),
      }));
      throw error;
    }
  },

  // --- Intent Dispatchers (Only DM should call these ideally) ---

  dispatchIntent: (action: string, payload: any) => {
    const { role } = get();
    if (role !== "dm") {
      const message = "Only the DM can dispatch command actions.";
      set((current) => ({
        errorMessage: message,
        commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", action, payload, message)),
      }));
      return;
    }

    void get().dispatchRawEnvelope(action, payload);
  },

  moveToken: (targetId: string, path: [number, number][]) => {
    const normalizedPath = path.map(([x, y]) => ({ x, y }));

    if (normalizedPath.length > 0) {
      const finalStep = normalizedPath[normalizedPath.length - 1];
      set((current) => ({
        gameState: current.gameState ? setCombatantPosition(current.gameState, targetId, finalStep.x, finalStep.y) : current.gameState,
      }));
    }

    get().dispatchIntent("move_token", { actor_id: targetId, path: normalizedPath });
  },

  removeActor: (actorId: string) => {
    set((current) => ({
      gameState: current.gameState ? applyActorRemoved(current.gameState, actorId) : current.gameState,
    }));

    get().dispatchIntent("remove_actor", { actor_id: actorId });
  },

  endTurn: () => {
    const state = get().gameState;
    const activeActor = state && typeof state.activeIndex === "number" ? state.combatants[state.activeIndex] : undefined;

    get().dispatchIntent("end_turn", { actor_id: activeActor?.id ?? "" });
  },

  applyDamage: (targetId: string, amount: number, damageType: string) => {
    get().dispatchIntent("apply_damage", { actor_id: targetId, amount, damage_type: damageType });
  },

  dispatchAction: (actionType: string, payload: any) => {
    get().dispatchIntent(actionType, payload);
  },
}));
