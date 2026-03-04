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

export interface CombatStore {
  // State
  gameState: GameState | null;
  isConnected: boolean;
  role: "dm" | "observer" | null;
  errorMessage: string | null;

  // Internal Socket ref (not perfectly pure Zustand, but functional for MVP)
  socket: WebSocket | null;

  // Actions
  connect: (campaignId: string, role: "dm" | "observer") => void;
  disconnect: () => void;

  // DM Intents
  dispatchIntent: (action: string, payload: any) => void;
  moveToken: (targetId: string, path: [number, number][]) => void;
  endTurn: () => void;
  applyDamage: (targetId: string, amount: number, damageType: string) => void;
  dispatchAction: (actionType: string, payload: any) => void;
}

export const useCombatStore = create<CombatStore>((set, get) => ({
  gameState: null,
  isConnected: false,
  role: null,
  errorMessage: null,
  socket: null,

  connect: (campaignId: string, role: "dm" | "observer") => {
    // Prevent double connections
    if (get().socket) return;

    const wsUrl = `ws://localhost:8020/campaigns/${campaignId}/ws?role=${role}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      set({ isConnected: true, role, errorMessage: null, socket: ws });
      console.log(`[WebSocket] Connected as ${role}`);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event_type === "STATE_UPDATE") {
          set({ gameState: payload.data });
        }
      } catch (e) {
        console.error("Failed to parse websocket message", e);
      }
    };

    ws.onerror = (error) => {
      console.error("[WebSocket] Error", error);
      set({ errorMessage: "WebSocket connection failed." });
    };

    ws.onclose = () => {
      set({ isConnected: false, socket: null, gameState: null });
      console.log("[WebSocket] Disconnected");
    };
  },

  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.close();
    }
  },

  // --- Intent Dispatchers (Only DM should call these ideally) ---

  dispatchIntent: (action: string, payload: any) => {
    const { socket, role } = get();
    if (!socket || role !== "dm") return;

    const intent = { action, payload };
    socket.send(JSON.stringify(intent));
  },

  moveToken: (targetId: string, path: [number, number][]) => {
    get().dispatchIntent("MOVE_TOKEN", { target_id: targetId, path });
  },

  endTurn: () => {
    get().dispatchIntent("END_TURN", {});
  },

  applyDamage: (targetId: string, amount: number, damageType: string) => {
    get().dispatchIntent("APPLY_DAMAGE", { target_id: targetId, amount, damage_type: damageType });
  },

  dispatchAction: (actionType: string, payload: any) => {
    get().dispatchIntent(actionType, payload);
  },
}));
