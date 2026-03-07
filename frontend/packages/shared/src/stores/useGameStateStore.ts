import { create } from "zustand";

export interface GameStateStore {
  state: any | null; // Represents the raw JSON state from backend for now
  patchState: (newState: any) => void;
  clearState: () => void;
}

export const useGameStateStore = create<GameStateStore>((set) => ({
  state: null,
  patchState: (newState: any) =>
    set((state) => ({
      state: { ...state.state, ...newState },
    })),
  clearState: () => set({ state: null }),
}));
