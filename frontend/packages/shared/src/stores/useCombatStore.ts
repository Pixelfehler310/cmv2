import { create } from "zustand";
import type {
  ActionDeniedPayload,
  ActionFeedbackViewModel,
  ActorAddedPayload,
  ActorDiedPayload,
  ActorMovedPayload,
  ActorRemovedPayload,
  AttackResultPayload,
  ChatMessagePayload,
  CommandLikeWsInboundType,
  CommandDeniedPayload,
  CombatantViewModel,
  CombatStartedPayload,
  DiceRolledPayload,
  EncounterStateWire,
  ErrorPayload,
  EffectAppliedPayload,
  GameStateViewModel,
  HpChangedPayload,
  KnownWsOutboundEnvelope,
  SaveResultPayload,
  TurnBudgetSnapshotPayload,
  TurnAdvancedPayload,
  WsInboundEnvelope,
} from "@rpg/types";
import { COMMAND_LIKE_WS_INBOUND_TYPES, KNOWN_WS_OUTBOUND_TYPES } from "@rpg/types";
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

export interface CombatTimelineEntry {
  id: string;
  at: string;
  type: string;
  requestId?: string;
  actorId?: string;
  summary: string;
  rawPayload: Record<string, unknown>;
}

export interface DeniedFeedback {
  requestId?: string;
  type: "action_denied" | "command_denied";
  reasonCode: string;
  message?: string;
  at: string;
}

export interface CommandSendMetadata {
  requestId: string;
  sentType: string;
  payload: Record<string, unknown>;
  sentAt: string;
}

export interface CommandOutcome {
  requestId: string;
  sentType: string;
  terminalType: string;
  ok: boolean;
  reasonCode?: string;
  message?: string;
  at: string;
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
  eventTimeline: CombatTimelineEntry[];
  latestDenied: DeniedFeedback | null;
  unknownEventCount: number;
  lastRequestSyncAt: string | null;
  pendingCommandsByRequestId: Record<string, CommandSendMetadata>;
  commandOutcomesByRequestId: Record<string, CommandOutcome>;
  latestCommandOutcome: CommandOutcome | null;
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
const EVENT_TIMELINE_LIMIT = 300;
const KNOWN_WS_OUTBOUND_TYPE_SET = new Set<string>(KNOWN_WS_OUTBOUND_TYPES);
const COMMAND_LIKE_INBOUND_TYPE_SET = new Set<string>(COMMAND_LIKE_WS_INBOUND_TYPES);

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

function appendTimelineEntry(timeline: CombatTimelineEntry[], entry: CombatTimelineEntry): CombatTimelineEntry[] {
  const next = [...timeline, entry];
  if (next.length <= EVENT_TIMELINE_LIMIT) {
    return next;
  }

  return next.slice(next.length - EVENT_TIMELINE_LIMIT);
}

function toRecord(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return {};
  }
  return value as Record<string, unknown>;
}

function parseOptionalBoolean(value: unknown): boolean | undefined {
  return typeof value === "boolean" ? value : undefined;
}

function parseOptionalNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function applyTurnBudgetSnapshot(state: GameState, snapshot: TurnBudgetSnapshotPayload | undefined): { nextState: GameState; hasMismatch: boolean } {
  if (!snapshot) {
    return { nextState: state, hasMismatch: false };
  }

  const nextCombatants = state.combatants.map((combatant) => {
    const rawBudget = toRecord(snapshot.budgets?.[combatant.id]);
    const actionAvailable = parseOptionalBoolean(rawBudget.action_available);
    const bonusActionAvailable = parseOptionalBoolean(rawBudget.bonus_action_available);
    const reactionAvailable = parseOptionalBoolean(rawBudget.reaction_available);
    const maxMovement = parseOptionalNumber(rawBudget.max_movement);
    const movementUsed = parseOptionalNumber(rawBudget.movement_used);
    const movementRemaining = parseOptionalNumber(rawBudget.movement_remaining);

    return {
      ...combatant,
      action_used: typeof actionAvailable === "boolean" ? !actionAvailable : combatant.action_used,
      bonus_action_used: typeof bonusActionAvailable === "boolean" ? !bonusActionAvailable : combatant.bonus_action_used,
      reaction_available: reactionAvailable ?? combatant.reaction_available,
      max_movement: maxMovement ?? combatant.max_movement,
      movement_used: movementUsed ?? combatant.movement_used,
      movement_remaining: movementRemaining ?? combatant.movement_remaining,
    };
  });

  let hasMismatch = false;
  let nextActiveIndex = state.activeIndex;
  if (typeof snapshot.active_actor_id === "string" && snapshot.active_actor_id.length > 0) {
    const actorIndex = nextCombatants.findIndex((combatant) => combatant.id === snapshot.active_actor_id);
    if (actorIndex >= 0) {
      nextActiveIndex = actorIndex;
    } else {
      hasMismatch = true;
    }
  }

  const round = typeof snapshot.round === "number" ? snapshot.round : state.round;
  return {
    hasMismatch,
    nextState: {
      ...state,
      round,
      activeIndex: nextActiveIndex,
      combatants: nextCombatants,
    },
  };
}

function summarizeTimelineEvent(type: CombatTimelineEntry["type"], payload: Record<string, unknown>): string {
  switch (type) {
    case "attack_result": {
      const typed = payload as unknown as AttackResultPayload;
      const outcome = typed.hit ? "hit" : "miss";
      return `${typed.action_name ?? "Attack"}: ${outcome}`;
    }
    case "save_result": {
      const typed = payload as unknown as SaveResultPayload;
      return `${typed.action_name ?? "Save effect"} resolved`;
    }
    case "effect_applied": {
      const typed = payload as unknown as EffectAppliedPayload;
      return `${typed.effect_type ?? "effect"} applied`;
    }
    case "dice_rolled": {
      const typed = payload as unknown as DiceRolledPayload;
      return `${typed.expression ?? "roll"} = ${typed.result ?? "?"}`;
    }
    case "chat_message": {
      const typed = payload as unknown as ChatMessagePayload;
      return `${typed.sender_name ?? "Unknown"}: ${typed.message ?? ""}`;
    }
    case "pong":
      return "Pong received";
    default:
      return type;
  }
}

function buildTimelineEntry(type: CombatTimelineEntry["type"], payload: Record<string, unknown>, requestId: string | undefined): CombatTimelineEntry {
  const at = new Date().toISOString();
  const actorId = typeof payload.actor_id === "string" ? payload.actor_id : undefined;

  return {
    id: `${type}:${requestId ?? "n/a"}:${at}`,
    at,
    type,
    requestId,
    actorId,
    summary: summarizeTimelineEvent(type, payload),
    rawPayload: payload,
  };
}

function buildDeniedFeedback(type: DeniedFeedback["type"], payload: ActionDeniedPayload | CommandDeniedPayload, requestId: string | undefined): DeniedFeedback {
  return {
    at: new Date().toISOString(),
    requestId,
    type,
    reasonCode: normalizeActionDeniedReasonCode(payload.reason_code),
    message: payload.message,
  };
}

function isKnownWsOutboundEnvelope(envelope: { type: string }): envelope is KnownWsOutboundEnvelope {
  return KNOWN_WS_OUTBOUND_TYPE_SET.has(envelope.type);
}

function isCommandLikeInboundType(type: string): type is CommandLikeWsInboundType {
  return COMMAND_LIKE_INBOUND_TYPE_SET.has(type);
}

function createRequestId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  const randomPart = Math.random().toString(36).slice(2, 10);
  return `req_${Date.now()}_${randomPart}`;
}

function ensureRequestId<TEnvelope extends WsInboundEnvelope>(envelope: TEnvelope): TEnvelope {
  if (!isCommandLikeInboundType(envelope.type)) {
    return envelope;
  }

  const requestId = typeof envelope.request_id === "string" ? envelope.request_id.trim() : "";
  if (requestId.length > 0) {
    return envelope;
  }

  return {
    ...envelope,
    request_id: createRequestId(),
  } as TEnvelope;
}

function isTerminalOutboundTypeForSentType(sentType: string, outboundType: string): boolean {
  if (outboundType === "error" || outboundType === "action_denied" || outboundType === "command_denied") {
    return true;
  }

  if (sentType === "ping") {
    return outboundType === "pong";
  }

  if (sentType === "request_sync") {
    return outboundType === "state_sync";
  }

  if (sentType === "roll_dice") {
    return outboundType === "dice_rolled";
  }

  if (sentType === "chat_message") {
    return outboundType === "chat_message";
  }

  return (
    outboundType === "action_authorized" ||
    outboundType === "combat_started" ||
    outboundType === "combat_ended" ||
    outboundType === "turn_advanced" ||
    outboundType === "actor_moved" ||
    outboundType === "actor_added" ||
    outboundType === "actor_removed" ||
    outboundType === "attack_result" ||
    outboundType === "save_result" ||
    outboundType === "effect_applied" ||
    outboundType === "actor_damaged" ||
    outboundType === "actor_healed" ||
    outboundType === "actor_died" ||
    outboundType === "condition_added" ||
    outboundType === "condition_removed"
  );
}

export const useCombatStore = create<CombatStore>((set, get) => ({
  gameState: null,
  isConnected: false,
  role: null,
  actingAsUserId: null,
  errorMessage: null,
  actionFeedback: null,
  commandLog: [],
  eventTimeline: [],
  latestDenied: null,
  unknownEventCount: 0,
  lastRequestSyncAt: null,
  pendingCommandsByRequestId: {},
  commandOutcomesByRequestId: {},
  latestCommandOutcome: null,
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
      latestDenied: null,
      eventTimeline: [],
      unknownEventCount: 0,
      lastRequestSyncAt: null,
      pendingCommandsByRequestId: {},
      commandOutcomesByRequestId: {},
      latestCommandOutcome: null,
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

    if (!isKnownWsOutboundEnvelope(envelope)) {
      set((current) => ({
        unknownEventCount: current.unknownEventCount + 1,
      }));
      return;
    }

    const maybeRecordTerminalOutcome = (): void => {
      const requestId = typeof envelope.request_id === "string" ? envelope.request_id : undefined;
      if (!requestId) {
        return;
      }

      const state = get();
      const pending = state.pendingCommandsByRequestId[requestId];
      if (!pending) {
        return;
      }

      if (!isTerminalOutboundTypeForSentType(pending.sentType, envelope.type)) {
        return;
      }

      const payload = toRecord(envelope.payload);
      const outcome: CommandOutcome = {
        requestId,
        sentType: pending.sentType,
        terminalType: envelope.type,
        ok: envelope.type !== "error" && envelope.type !== "action_denied" && envelope.type !== "command_denied",
        reasonCode: typeof payload.reason_code === "string" ? normalizeActionDeniedReasonCode(payload.reason_code) : undefined,
        message: typeof payload.message === "string" ? payload.message : undefined,
        at: new Date().toISOString(),
      };

      set((current) => {
        const nextPending = { ...current.pendingCommandsByRequestId };
        delete nextPending[requestId];

        return {
          pendingCommandsByRequestId: nextPending,
          commandOutcomesByRequestId: {
            ...current.commandOutcomesByRequestId,
            [requestId]: outcome,
          },
          latestCommandOutcome: outcome,
        };
      });
    };

    maybeRecordTerminalOutcome();

    const maybeRequestSyncOnMismatch = (hasMismatch: boolean): void => {
      if (!hasMismatch) {
        return;
      }

      const at = new Date().toISOString();
      set({ lastRequestSyncAt: at });

      const { actionDispatcher } = get();
      if (!actionDispatcher) {
        return;
      }

      void get()
        .dispatchCommand({ type: "request_sync", payload: {} })
        .catch(() => {
          // request_sync is best-effort fallback; normal error logging already happens in dispatchCommand.
        });
    };

    const pushTimelineEvent = (type: CombatTimelineEntry["type"], payload: Record<string, unknown>, requestId: string | undefined): void => {
      set((current) => ({
        eventTimeline: appendTimelineEntry(current.eventTimeline, buildTimelineEntry(type, payload, requestId)),
      }));
    };

    switch (envelope.type) {
      case "error": {
        const payload = envelope.payload as ErrorPayload;
        const nextErrorMessage = payload.message ?? "WebSocket error";
        const errorCode = payload.code ?? "unknown";
        set({ errorMessage: `${nextErrorMessage} (${errorCode})` });
        return;
      }

      case "state_sync": {
        const payload = envelope.payload as EncounterStateWire;
        set({ gameState: mapEncounterWireToGameState(payload) });
        return;
      }

      case "actor_moved": {
        const payload = envelope.payload as ActorMovedPayload;
        let mismatch = false;
        set((current) => {
          if (!current.gameState) {
            return { gameState: current.gameState };
          }

          const movedState = applyActorMove(current.gameState, payload);
          const applied = applyTurnBudgetSnapshot(movedState, payload.turn_budget);
          mismatch = applied.hasMismatch;
          return { gameState: applied.nextState };
        });
        maybeRequestSyncOnMismatch(mismatch);
        return;
      }

      case "actor_added": {
        const payload = envelope.payload as ActorAddedPayload;
        set((current) => ({
          gameState: current.gameState ? applyActorAdded(current.gameState, payload) : current.gameState,
        }));
        return;
      }

      case "actor_removed": {
        const payload = envelope.payload as ActorRemovedPayload;
        set((current) => ({
          gameState: current.gameState && payload.actor_id ? applyActorRemoved(current.gameState, payload.actor_id) : current.gameState,
        }));
        return;
      }

      case "actor_damaged":
      case "actor_healed": {
        const payload = envelope.payload as HpChangedPayload;
        set((current) => ({
          gameState: current.gameState && payload.actor_id && typeof payload.new_hp === "number" ? applyHpUpdate(current.gameState, payload.actor_id, payload.new_hp) : current.gameState,
        }));
        return;
      }

      case "actor_died": {
        const payload = envelope.payload as ActorDiedPayload;
        set((current) => ({
          gameState: current.gameState && payload.actor_id ? applyActorDeath(current.gameState, payload.actor_id) : current.gameState,
        }));
        return;
      }

      case "action_authorized": {
        const payload = envelope.payload as { turn_budget?: TurnBudgetSnapshotPayload };
        let mismatch = false;
        set((current) => {
          if (!current.gameState) {
            return { actionFeedback: null, gameState: current.gameState };
          }

          const applied = applyTurnBudgetSnapshot(current.gameState, payload.turn_budget);
          mismatch = applied.hasMismatch;

          return {
            actionFeedback: null,
            gameState: applied.nextState,
          };
        });
        maybeRequestSyncOnMismatch(mismatch);
        return;
      }

      case "action_denied": {
        const payload = envelope.payload as ActionDeniedPayload;
        const denied = buildDeniedFeedback("action_denied", payload, envelope.request_id);
        set({
          latestDenied: denied,
          actionFeedback: {
            actorId: payload.actor_id,
            actionType: payload.action_type,
            reasonCode: denied.reasonCode,
            message: payload.message,
            at: denied.at,
          },
        });
        return;
      }

      case "command_denied": {
        const payload = envelope.payload as CommandDeniedPayload;
        const denied = buildDeniedFeedback("command_denied", payload, envelope.request_id);
        set({
          latestDenied: denied,
          actionFeedback: {
            actorId: payload.actor_id ?? "",
            actionType: payload.action_type ?? payload.event_type,
            reasonCode: denied.reasonCode,
            message: payload.message,
            at: denied.at,
          },
        });
        return;
      }

      case "combat_started": {
        const payload = envelope.payload as CombatStartedPayload;
        let mismatch = false;
        set((current) => {
          if (!current.gameState) {
            return { gameState: current.gameState };
          }

          const applied = applyTurnBudgetSnapshot(current.gameState, payload.turn_budget);
          mismatch = applied.hasMismatch;
          return { gameState: applied.nextState };
        });
        maybeRequestSyncOnMismatch(mismatch);
        return;
      }

      case "combat_ended": {
        return;
      }

      case "turn_advanced": {
        const payload = envelope.payload as TurnAdvancedPayload;
        let mismatch = false;
        set((current) => {
          if (!current.gameState) {
            return { gameState: current.gameState };
          }

          const nextActiveIndex = current.gameState.combatants.findIndex((combatant) => combatant.id === payload.active_actor_id);
          const advancedState = {
            ...current.gameState,
            round: payload.round ?? current.gameState.round,
            activeIndex: nextActiveIndex >= 0 ? nextActiveIndex : current.gameState.activeIndex,
          };
          const applied = applyTurnBudgetSnapshot(advancedState, payload.turn_budget);
          mismatch = applied.hasMismatch;

          return {
            gameState: applied.nextState,
          };
        });
        maybeRequestSyncOnMismatch(mismatch);
        return;
      }

      case "condition_added": {
        return;
      }

      case "condition_removed": {
        return;
      }

      case "attack_result":
      case "save_result":
      case "effect_applied":
      case "dice_rolled":
      case "chat_message":
      case "pong": {
        pushTimelineEvent(envelope.type, toRecord(envelope.payload), envelope.request_id);
        return;
      }

      default: {
        const _exhaustive: never = envelope;
        return _exhaustive;
      }
    }
  },

  clearCommandLog: () => {
    set({ commandLog: [] });
  },

  clearActionFeedback: () => {
    set({ actionFeedback: null, latestDenied: null });
  },

  dispatchRawEnvelope: async (type: string, payload: Record<string, unknown>) => {
    return get().dispatchCommand({ type, payload });
  },

  dispatchCommand: async (command: WsInboundEnvelope) => {
    const { actionDispatcher } = get();
    const commandWithRequestId = ensureRequestId(command);
    const requestId = typeof commandWithRequestId.request_id === "string" ? commandWithRequestId.request_id : undefined;
    const sendAt = new Date().toISOString();

    set((current) => ({
      commandLog: appendLogEntry(current.commandLog, createLogEntry("SEND", commandWithRequestId.type, commandWithRequestId.payload)),
      pendingCommandsByRequestId: requestId
        ? {
            ...current.pendingCommandsByRequestId,
            [requestId]: {
              requestId,
              sentType: commandWithRequestId.type,
              payload: toRecord(commandWithRequestId.payload),
              sentAt: sendAt,
            },
          }
        : current.pendingCommandsByRequestId,
    }));

    if (!actionDispatcher) {
      const message = "No action dispatcher configured.";
      set((current) => ({
        errorMessage: message,
        commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", commandWithRequestId.type, commandWithRequestId.payload, message)),
        pendingCommandsByRequestId: requestId
          ? (() => {
              const nextPending = { ...current.pendingCommandsByRequestId };
              delete nextPending[requestId];
              return nextPending;
            })()
          : current.pendingCommandsByRequestId,
      }));
      throw new Error(message);
    }

    try {
      const result = await actionDispatcher(commandWithRequestId);
      const isFailureResult = typeof result === "object" && result !== null && "success" in result && (result as { success?: unknown }).success === false;

      if (isFailureResult) {
        const errorFromResult = (result as { error?: unknown }).error;
        const message = typeof errorFromResult === "string" ? errorFromResult : "Command dispatch failed";
        set((current) => ({
          errorMessage: message,
          commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", commandWithRequestId.type, commandWithRequestId.payload, message)),
          pendingCommandsByRequestId: requestId
            ? (() => {
                const nextPending = { ...current.pendingCommandsByRequestId };
                delete nextPending[requestId];
                return nextPending;
              })()
            : current.pendingCommandsByRequestId,
          commandOutcomesByRequestId: requestId
            ? {
                ...current.commandOutcomesByRequestId,
                [requestId]: {
                  requestId,
                  sentType: commandWithRequestId.type,
                  terminalType: "dispatch_error",
                  ok: false,
                  message,
                  at: new Date().toISOString(),
                },
              }
            : current.commandOutcomesByRequestId,
          latestCommandOutcome: requestId
            ? {
                requestId,
                sentType: commandWithRequestId.type,
                terminalType: "dispatch_error",
                ok: false,
                message,
                at: new Date().toISOString(),
              }
            : current.latestCommandOutcome,
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
        commandLog: appendLogEntry(current.commandLog, createLogEntry("ERROR", commandWithRequestId.type, commandWithRequestId.payload, message)),
        pendingCommandsByRequestId: requestId
          ? (() => {
              const nextPending = { ...current.pendingCommandsByRequestId };
              delete nextPending[requestId];
              return nextPending;
            })()
          : current.pendingCommandsByRequestId,
        commandOutcomesByRequestId: requestId
          ? {
              ...current.commandOutcomesByRequestId,
              [requestId]: {
                requestId,
                sentType: commandWithRequestId.type,
                terminalType: "dispatch_error",
                ok: false,
                message,
                at: new Date().toISOString(),
              },
            }
          : current.commandOutcomesByRequestId,
        latestCommandOutcome: requestId
          ? {
              requestId,
              sentType: commandWithRequestId.type,
              terminalType: "dispatch_error",
              ok: false,
              message,
              at: new Date().toISOString(),
            }
          : current.latestCommandOutcome,
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
