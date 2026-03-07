import { create } from "zustand";

export interface SelectionStore {
  selectedTokenId: string | null;
  setSelectedTokenId: (id: string | null) => void;
  clearSelection: () => void;
}

export const useSelectionStore = create<SelectionStore>((set) => ({
  selectedTokenId: null,
  setSelectedTokenId: (id: string | null) => set({ selectedTokenId: id }),
  clearSelection: () => set({ selectedTokenId: null }),
}));
