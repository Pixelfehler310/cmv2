import { create } from 'zustand';
import type { Character, Campaign, Monster } from '@rpg/types';

interface CombatState {
  isActive: boolean;
  currentTurn: number;
  initiativeOrder: Array<{
    id: string;
    name: string;
    initiative: number;
    type: 'character' | 'monster';
  }>;
}

interface GameState {
  // Campaign state
  currentCampaign: Campaign | null;
  setCurrentCampaign: (campaign: Campaign | null) => void;

  // Active entities
  activeCharacters: Character[];
  activeMonsters: Monster[];
  addCharacter: (character: Character) => void;
  removeCharacter: (characterId: string) => void;
  addMonster: (monster: Monster) => void;
  removeMonster: (monsterId: string) => void;
  updateCharacter: (characterId: string, updates: Partial<Character>) => void;
  updateMonster: (monsterId: string, updates: Partial<Monster>) => void;

  // Combat state
  combat: CombatState;
  startCombat: () => void;
  endCombat: () => void;
  setInitiativeOrder: (order: CombatState['initiativeOrder']) => void;
  nextTurn: () => void;
  previousTurn: () => void;
  setCurrentTurn: (turn: number) => void;
}

export const useGameStore = create<GameState>((set) => ({
  // Campaign state
  currentCampaign: null,
  setCurrentCampaign: (campaign) => set({ currentCampaign: campaign }),

  // Active entities
  activeCharacters: [],
  activeMonsters: [],
  addCharacter: (character) =>
    set((state) => ({
      activeCharacters: [...state.activeCharacters, character],
    })),
  removeCharacter: (characterId) =>
    set((state) => ({
      activeCharacters: state.activeCharacters.filter((c) => c.id !== characterId),
    })),
  addMonster: (monster) =>
    set((state) => ({
      activeMonsters: [...state.activeMonsters, monster],
    })),
  removeMonster: (monsterId) =>
    set((state) => ({
      activeMonsters: state.activeMonsters.filter((m) => m.id !== monsterId),
    })),
  updateCharacter: (characterId, updates) =>
    set((state) => ({
      activeCharacters: state.activeCharacters.map((c) =>
        c.id === characterId ? { ...c, ...updates } : c
      ),
    })),
  updateMonster: (monsterId, updates) =>
    set((state) => ({
      activeMonsters: state.activeMonsters.map((m) =>
        m.id === monsterId ? { ...m, ...updates } : m
      ),
    })),

  // Combat state
  combat: {
    isActive: false,
    currentTurn: 0,
    initiativeOrder: [],
  },
  startCombat: () =>
    set((state) => ({
      combat: { ...state.combat, isActive: true, currentTurn: 0 },
    })),
  endCombat: () =>
    set((state) => ({
      combat: { ...state.combat, isActive: false, currentTurn: 0, initiativeOrder: [] },
    })),
  setInitiativeOrder: (order) =>
    set((state) => ({
      combat: { ...state.combat, initiativeOrder: order },
    })),
  nextTurn: () =>
    set((state) => {
      const nextTurn = (state.combat.currentTurn + 1) % state.combat.initiativeOrder.length;
      return {
        combat: { ...state.combat, currentTurn: nextTurn },
      };
    }),
  previousTurn: () =>
    set((state) => {
      const prevTurn =
        state.combat.currentTurn === 0
          ? state.combat.initiativeOrder.length - 1
          : state.combat.currentTurn - 1;
      return {
        combat: { ...state.combat, currentTurn: prevTurn },
      };
    }),
  setCurrentTurn: (turn) =>
    set((state) => ({
      combat: { ...state.combat, currentTurn: turn },
    })),
}));

