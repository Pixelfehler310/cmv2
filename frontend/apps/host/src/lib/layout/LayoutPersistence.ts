import { IJsonModel } from 'flexlayout-react';

const LAYOUT_KEY = 'rpg_layout_config';

export function saveLayout(model: IJsonModel) {
  try {
    localStorage.setItem(LAYOUT_KEY, JSON.stringify(model));
  } catch (error) {
    console.error('Failed to save layout:', error);
  }
}

export function loadLayout(): IJsonModel | null {
  try {
    const saved = localStorage.getItem(LAYOUT_KEY);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (error) {
    console.error('Failed to load layout:', error);
  }
  return null;
}

export function clearLayout() {
  localStorage.removeItem(LAYOUT_KEY);
}

