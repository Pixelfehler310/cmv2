import { CampaignState } from './types';

export const campaignState: CampaignState = {
  id: 'campaign-1',
  round: 3,
  currentTurnIndex: 1,
  turnOrder: [
    { entityId: 'char-1', initiative: 18, isPlayer: true }, // Gandalf
    { entityId: 'monster-1', initiative: 15, isPlayer: false }, // Goblin
    { entityId: 'monster-2', initiative: 12, isPlayer: false }, // Goblin
  ],
  map: {
    id: 'map-1',
    imageUrl: 'https://images.unsplash.com/photo-1626265774643-f1943311a86b?q=80&w=2669&auto=format&fit=crop', // Generic dungeon map
    width: 20, // Grid cells
    height: 15,
    tokens: [
      { id: 'token-1', entityId: 'char-1', x: 5, y: 5, size: 1, isHidden: false, imageUrl: 'https://ui-avatars.com/api/?name=G&background=random' },
      { id: 'token-2', entityId: 'monster-1', x: 8, y: 6, size: 1, isHidden: false, imageUrl: 'https://ui-avatars.com/api/?name=Gob&background=red' },
      { id: 'token-3', entityId: 'monster-2', x: 9, y: 4, size: 1, isHidden: true, imageUrl: 'https://ui-avatars.com/api/?name=Gob&background=red' }, // Hidden goblin
    ],
    fogOfWar: [
      { id: 'fog-1', type: 'rect', x: 0, y: 0, w: 20, h: 15 }, // Cover everything
      { id: 'fog-2', type: 'circle', x: 5, y: 5, r: 6 }, // Reveal around player (subtractive logic needed in renderer, or this is revealed area?)
      // Assuming these are REVEALED areas for simplicity in this mock, or standard FoW is "shapes that are hidden"?
      // Let's assume these are UNREVEALED areas (Fog).
      // Actually, usually it's easier to define what is VISIBLE.
      // Let's assume the renderer handles it.
    ]
  }
};
