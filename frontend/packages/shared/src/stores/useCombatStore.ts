import { create } from "zustand";
import type {
  ActionDeniedPayload,
  ActionFeedbackViewModel,
  ActorAddedPayload,
  ActorMovedPayload,
  CombatantViewModel,
  EncounterStateWire,
  GameStateViewModel,
  HpChangedPayload,
  TurnAdvancedPayload,
  WsInboundEnvelope,
} from "@rpg/types";
import { normalizeActionDeniedReasonCode } from "@rpg/types";
import { mapActorWireToCombatant, mapEncounterWireToGameState } from "../adapters/encounterAdapter";
import { parseWsOutboundEnvelope } from "../adapters/wsEnvelopeAdapter";

export type CombatantState = CombatantViewModel;
export type GameState = GameStateViewModel;

export interface CombatLogEntry {
  timestamp: string;
  direction: "SEND" | "RECV" | "ERROR";
  type: string;
  payload: unknown;
  message?: string;
}

export type CombatActionDispatcher = (commandOrType: WsInboundEnvelope | string, payload?: Record<string, unknown>) => Promise<unknown>;

export interface CombatStore {
  gameState: GameState | null;
  isConnected: boolean;
  role: "dm" | "observer" | null;
  actingAsUserId: string | null;
  errorMessage: string | null;
  actionFeedback: ActionFeedbackViewModel | null;
  commandLog: CombatLogEntry[];
  actionDispatcher: CombatActionDispatcher | null;

  connect: (campaignId: string, role: "dm" | "observer") => void;
  disconnect: () => void;
  setConnectionStatus: (isConnected: boolean, role?: "dm" | "observer") => void;
  setActingAsUserId: (userId: string | null) => void;
  setActionDispatcher: (dispatcher: CombatActionDispatcher | null) => void;
  ingestEnvelope: (message: unknown) => void;
  clearCommandLog: () => void;
  clearActionFeedback: () => void;
  dispatchRawEnvelope: (type: string, payload: Record<string, unknown>) => Promise<unknown>;
  dispatchCommand: (command: WsInboundEnvelope) => Promise<unknown>;

  dispatchIntent: (action: string, payload: Record<string, unknown>) => void;
  requestAction: (actorId: string, actionType: string, actionName: string, payload?: Record<string, unknown>) => void;
  moveToken: (targetId: string, path: [number, number][]) => void;
  removeActor: (actorId: string) => void;
  endTurn: () => void;
  applyDamage: (targetId: string, amount: number, damageType: string) => void;
  dispatchAction: (actionType: string, payload: Record<string, unknown>) => void;
}

function applyActorMove(state: GameState, payload: ActorMovedPayload): GameState {
  const movedTo = payload.position;
  if (!payload.actor_id || !movedTo) {
    return state;
  }

  return {
    ...state,
    combatants: state.combatants.map((combatant) =>
      combatant.id === payload.actor_id
        ? {
            ...combatant,
            x: movedTo.x ?? combatant.x,
            y: movedTo.y ?? combatant.y,
          }
        : combatant,
    ),
  };
}

function applyActorAdded(state: GameState, payload: ActorAddedPayload): GameState {
  const actor = payload.actor;
  if (!actor?.id) {
    return state;
  }

  const exists = state.combatants.some((combatant) => combatant.id === actor.id);
  if (exists) {
    return state;
  }

  const combatant = mapActorWireToCombatant(
    {
      map: { tokens: payload.token ? [payload.token] : [] },
      turn_budgets: {},
    },
    actor,
  );

  return {
    ...state,
    combatants: [...state.combatants, combatant],
  };
}

function applyActorRemoved(state: GameState, actorId: string): GameState {
  const nextCombatants = state.combatants.filter((combatant) => combatant.id !== actorId);
  let nextActiveIndex = state.activeIndex;

  if (nextCombatants.length === 0 || nextActiveIndex >= nextCombatants.length) {
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
    combatants: state.combatants.map((combatant) =>
      combatant.id === actorId
        ? {
            ...combatant,
            hp_current: newHp,
            hp_percent: typeof combatant.hp_max === "number" && combatant.hp_max > 0 ? Math.max(0, Math.min(1, newHp / combatant.hp_max)) : combatant.hp_percent,
          }
        : combatant,
    ),
  };
}

function applyActorDeath(state: GameState, actorId: string): GameState {
  return applyHpUpdate(state, actorId, 0);
}

function setCombatantPosition(state: GameState, actorId: string, x: number, y: number): GameState {
  return {
    ...state,
    combatants: state.combatants.map((combatant) =>
      combatant.id === actorId
        ? {
            ...combatant,
            x,
            y,
          }
        : combatant,
    ),
  };
}

const COMMAND_LOG_LIMIT = 200;

function createLogEntry(direction: "SEND" | "RECV" | "ERROR", type: string, payload: unknown, message?: string): CombatLogEntry {
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
  actingAsUserId: null,
  errorMessage: null,
  actionFeedback: null,
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
      actingAsUserId: null,
      gameState: null,
      actionDispatcher: null,
      actionFeedback: null,
    });
  },

  setConnectionStatus: (isConnected: boolean, role?: "dm" | "observer") => {
    set((current) => ({
      isConnected,
      role: role ?? current.role,
    }));
  },

  setActingAsUserId: (userId: string | null) => {
    set({ actingAsUserId: userId && userId.trim() ? userId.trim() : null });
  },

  setActionDispatcher: (dispatcher: CombatActionDispatcher | null) => {
    set({ actionDispatcher: dispatcher });
  },

  ingestEnvelope: (message: unknown) => {
    const envelope = parseWsOutboundEnvelope(message);

    if (!envelope?.type) {
      const parseMessage = "Failed to parse envelope";
      set((current) => ({
        errorMessage: parseMessage,
        commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", "invalid_envelope", message, parseMessage)),
      }));
      return;
    }

    set((current) => ({
      commandLog: appendLogEntry(current.commandLog, createLogEntry("RECV", envelope.type, envelope.payload)),
    }));

    if (envelope.type === "error") {
      const payload = envelope.payload as { message?: string; code?: string };
      const nextErrorMessage = payload.message ?? "WebSocket error";
      const errorCode = payload.code ?? "unknown";
      set({ errorMessage: `${nextErrorMessage} (${errorCode})` });
      return;
    }

    if (envelope.type === "state_sync") {
      const payload = envelope.payload as EncounterStateWire;
      set({ gameState: mapEncounterWireToGameState(payload) });
      return;
    }

    if (envelope.type === "actor_moved") {
      const payload = envelope.payload as ActorMovedPayload;
      set((current) => ({
        gameState: current.gameState ? applyActorMove(current.gameState, payload) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "actor_added") {
      const payload = envelope.payload as ActorAddedPayload;
      set((current) => ({
        gameState: current.gameState ? applyActorAdded(current.gameState, payload) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "actor_removed") {
      const payload = envelope.payload as { actor_id?: string };
      set((current) => ({
        gameState: current.gameState && payload.actor_id ? applyActorRemoved(current.gameState, payload.actor_id) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "actor_damaged" || envelope.type === "actor_healed") {
      const payload = envelope.payload as HpChangedPayload;
      set((current) => ({
        gameState: current.gameState && payload.actor_id && typeof payload.new_hp === "number" ? applyHpUpdate(current.gameState, payload.actor_id, payload.new_hp) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "actor_died") {
      const payload = envelope.payload as { actor_id?: string };
      set((current) => ({
        gameState: current.gameState && payload.actor_id ? applyActorDeath(current.gameState, payload.actor_id) : current.gameState,
      }));
      return;
    }

    if (envelope.type === "action_authorized") {
      set({ actionFeedback: null });
      return;
    }

    if (envelope.type === "action_denied") {
      const payload = envelope.payload as ActionDeniedPayload;
      set({
        actionFeedback: {
          actorId: payload.actor_id,
          actionType: payload.action_type,
          reasonCode: normalizeActionDeniedReasonCode(payload.reason_code),
          message: payload.message,
          at: new Date().toISOString(),
        },
      });
      return;
    }

    if (envelope.type === "turn_advanced") {
      const payload = envelope.payload as TurnAdvancedPayload;
      set((current) => {
        if (!current.gameState) {
          return { gameState: current.gameState };
        }

        const nextActiveIndex = current.gameState.combatants.findIndex((combatant) => combatant.id === payload.active_actor_id);

        return {
          gameState: {
            ...current.gameState,
            round: payload.round ?? current.gameState.round,
            activeIndex: nextActiveIndex >= 0 ? nextActiveIndex : current.gameState.activeIndex,
          },
        };
      });
    }
  },

  clearCommandLog: () => {
    set({ commandLog: [] });
  },

  clearActionFeedback: () => {
    set({ actionFeedback: null });
  },

  dispatchRawEnvelope: async (type: string, payload: Record<string, unknown>) => {
    return get().dispatchCommand({ type, payload });
  },

  dispatchCommand: async (command: WsInboundEnvelope) => {
    const { actionDispatcher } = get();

    set((current) => ({
      commandLog: appendLogEntry(current.commandLog, createLogEntry("SEND", command.type, command.payload)),
    }));

    if (!actionDispatcher) {
      const message = "No action dispatcher configured.";
      set((current) => ({
        errorMessage: message,
        commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", command.type, command.payload, message)),
      }));
      throw new Error(message);
    }

    try {
      const result = await actionDispatcher(command);
      const isFailureResult = typeof result === "object" && result !== null && "success" in result && (result as { success?: unknown }).success === false;

      if (isFailureResult) {
        const errorFromResult = (result as { error?: unknown }).error;
        const message = typeof errorFromResult === "string" ? errorFromResult : "Command dispatch failed";
        set((current) => ({
          errorMessage: message,
          commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", command.type, command.payload, message)),
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
        commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", command.type, command.payload, message)),
      }));
      throw error;
    }
  },

  dispatchIntent: (action: string, payload: Record<string, unknown>) => {
    const { role } = get();
    if (role !== "dm") {
      const message = "Only the DM can dispatch command actions.";
      set((current) => ({
        errorMessage: message,
        commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", action, payload, message)),
      }));
      return;
    }

    void get().dispatchCommand({ type: action, payload });
  },

  requestAction: (actorId: string, actionType: string, actionName: string, payload: Record<string, unknown> = {}) => {
    const { actingAsUserId } = get();
    void get().dispatchCommand({
      type: "request_action",
      payload: {
        actor_id: actorId,
        action_type: actionType,
        action_name: actionName,
        payload,
        ...(actingAsUserId ? { acting_as_user_id: actingAsUserId } : {}),
      },
    });
  },

  moveToken: (targetId: string, path: [number, number][]) => {
    const { actingAsUserId } = get();
    const normalizedPath = path.map(([x, y]) => ({ x, y }));

    if (normalizedPath.length > 0) {
      const finalStep = normalizedPath[normalizedPath.length - 1];
      set((current) => ({
        gameState: current.gameState ? setCombatantPosition(current.gameState, targetId, finalStep.x, finalStep.y) : current.gameState,
      }));
    }

    if (actingAsUserId) {
      void get().dispatchCommand({
        type: "move_token",
        payload: {
          actor_id: targetId,
          path: normalizedPath,
          acting_as_user_id: actingAsUserId,
        },
      });
      return;
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
    const activeActor = state ? state.combatants[state.activeIndex] : undefined;
    get().dispatchIntent("end_turn", { actor_id: activeActor?.id ?? "" });
  },

  applyDamage: (targetId: string, amount: number, damageType: string) => {
    get().dispatchIntent("apply_damage", { actor_id: targetId, amount, damage_type: damageType });
  },

  dispatchAction: (actionType: string, payload: Record<string, unknown>) => {
    get().dispatchIntent(actionType, payload);
  },
}));
