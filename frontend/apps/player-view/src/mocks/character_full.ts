import { Character } from './types';

export const characterFull: Character = {
  id: 'char-1',
  name: 'Gandalf the Grey',
  level: 5,
  class: 'Wizard',
  race: 'Human',
  background: 'Sage',
  stats: {
    str: 10,
    dex: 14,
    con: 14,
    int: 18,
    wis: 12,
    cha: 10,
  },
  hp: {
    current: 32,
    max: 32,
    temp: 0,
  },
  ac: 12, // 10 + Dex (2)
  speed: 30,
  inventory: [
    { id: 'item-1', name: 'Quarterstaff', type: 'Weapon', quantity: 1, equipped: true, description: '1d6 bludgeoning' },
    { id: 'item-2', name: 'Arcane Focus (Staff)', type: 'Adventuring Gear', quantity: 1, equipped: true },
    { id: 'item-3', name: 'Spellbook', type: 'Adventuring Gear', quantity: 1, equipped: false },
    { id: 'item-4', name: 'Potion of Healing', type: 'Potion', quantity: 2, equipped: false, description: '2d4+2' },
  ],
  spells: [
    { id: 'spell-1', name: 'Fireball', level: 3, school: 'Evocation', castingTime: '1 Action', range: '150 ft', components: ['V', 'S', 'M'], duration: 'Instantaneous', description: '8d6 fire damage', prepared: true },
    { id: 'spell-2', name: 'Mage Armor', level: 1, school: 'Abjuration', castingTime: '1 Action', range: 'Touch', components: ['V', 'S', 'M'], duration: '8 Hours', description: 'AC becomes 13 + Dex', prepared: true },
    { id: 'spell-3', name: 'Magic Missile', level: 1, school: 'Evocation', castingTime: '1 Action', range: '120 ft', components: ['V', 'S'], duration: 'Instantaneous', description: '3 darts, 1d4+1 force each', prepared: true },
    { id: 'spell-4', name: 'Shield', level: 1, school: 'Abjuration', castingTime: '1 Reaction', range: 'Self', components: ['V', 'S'], duration: '1 Round', description: '+5 AC', prepared: true },
    { id: 'spell-5', name: 'Detect Magic', level: 1, school: 'Divination', castingTime: '1 Action', range: 'Self', components: ['V', 'S'], duration: 'Concentration, up to 10 min', description: 'Sense magic', prepared: false },
  ],
  effects: [
    { id: 'effect-1', name: 'Mage Armor', description: 'AC is 15', duration: 480, source: 'Spell' }
  ]
};
