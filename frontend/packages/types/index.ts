// Base types matching backend Pydantic models

export interface EffectConfig {
  trigger: string;
  action: string;
  value: any;
  target?: string;
}

export interface GameEntity {
  id: string;
  name: string;
  description: string;
  effects: EffectConfig[];
}

// Item types
export interface Item extends GameEntity {
  type: string;
  rarity: string;
  weight: number;
  price: number;
  properties: Record<string, any>;
}

export interface ItemCreate {
  name: string;
  description: string;
  type: string;
  rarity: string;
  weight?: number;
  price?: number;
  properties?: Record<string, any>;
  effects?: EffectConfig[];
}

export interface ItemResponse extends Item {}

// Spell types
export interface Spell extends GameEntity {
  level: number;
  school: string;
  casting_time: string;
  range: string;
  components: Record<string, any>;
  duration: string;
}

export interface SpellCreate {
  name: string;
  description: string;
  level: number;
  school: string;
  casting_time: string;
  range: string;
  components?: Record<string, any>;
  duration: string;
  effects?: EffectConfig[];
}

export interface SpellResponse extends Spell {}

// Monster types
export interface Monster extends GameEntity {
  size: string;
  type: string;
  alignment: string;
  armor_class: number;
  hit_points: number;
  hit_dice: string;
  speed: Record<string, number>;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

export interface MonsterCreate {
  name: string;
  description: string;
  size: string;
  type: string;
  alignment: string;
  armor_class: number;
  hit_points: number;
  hit_dice: string;
  speed: Record<string, number>;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  effects?: EffectConfig[];
}

export interface MonsterResponse extends Monster {}

// Character types
export interface Character {
  id: string;
  name: string;
  player_name?: string;
  campaign_id?: string;
  race: string;
  class_name: string;
  level: number;
  xp: number;
  alignment?: string;
  background?: string;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  max_hp: number;
  current_hp: number;
  temp_hp: number;
  hit_dice: string;
  armor_class: number;
  speed: number;
  initiative: number;
  inventory: Array<Record<string, any>>;
  spells: Array<Record<string, any>>;
  spell_slots: Record<string, number>;
  actions: Array<Record<string, any>>;
  effects: Array<Record<string, any>>;
}

export interface CharacterCreate {
  name: string;
  player_name?: string;
  campaign_id?: string;
  race: string;
  class_name: string;
  level?: number;
  xp?: number;
  alignment?: string;
  background?: string;
  strength?: number;
  dexterity?: number;
  constitution?: number;
  intelligence?: number;
  wisdom?: number;
  charisma?: number;
  max_hp: number;
  current_hp: number;
  temp_hp?: number;
  hit_dice: string;
  armor_class?: number;
  speed?: number;
  initiative?: number;
  inventory?: Array<Record<string, any>>;
  spells?: Array<Record<string, any>>;
  spell_slots?: Record<string, number>;
  actions?: Array<Record<string, any>>;
  effects?: Array<Record<string, any>>;
}

export interface CharacterResponse extends Character {}

// Campaign types
export interface Campaign {
  id: string;
  name: string;
  description?: string;
  dm_id?: string;
  characters: CharacterResponse[];
}

export interface CampaignCreate {
  name: string;
  description?: string;
  dm_id?: string;
}

export interface CampaignResponse extends Campaign {}

// API Response types
export interface ApiListResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface ApiError {
  detail: string;
}

// Pagination params
export interface PaginationParams {
  skip?: number;
  limit?: number;
}
