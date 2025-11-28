export interface Character {
  id: string;
  name: string;
  level: number;
  class: string;
  race: string;
  background: string;
  stats: {
    str: number;
    dex: number;
    con: number;
    int: number;
    wis: number;
    cha: number;
  };
  hp: {
    current: number;
    max: number;
    temp: number;
  };
  ac: number;
  speed: number;
  inventory: Item[];
  spells: Spell[];
  effects: Effect[];
}

export interface Item {
  id: string;
  name: string;
  type: string;
  quantity: number;
  equipped: boolean;
  description?: string;
}

export interface Spell {
  id: string;
  name: string;
  level: number;
  school: string;
  castingTime: string;
  range: string;
  components: string[];
  duration: string;
  description: string;
  prepared: boolean;
}

export interface Effect {
  id: string;
  name: string;
  description: string;
  duration: number; // rounds
  source: string;
}

export interface CampaignState {
  id: string;
  turnOrder: Turn[];
  currentTurnIndex: number;
  round: number;
  map: {
    id: string;
    imageUrl: string;
    width: number;
    height: number;
    tokens: Token[];
    fogOfWar: FogShape[];
  };
}

export interface Turn {
  entityId: string;
  initiative: number;
  isPlayer: boolean;
}

export interface Token {
  id: string;
  entityId: string; // Character or Monster ID
  x: number;
  y: number;
  size: number;
  imageUrl?: string;
  isHidden: boolean;
}

export interface FogShape {
  // TODO add id to each shape, so dm can easily remove it by /clear fog <id>
  type: 'rect' | 'circle' | 'poly';
  points?: number[]; // for poly
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  r?: number;
}

export interface ChatMessage {
  id: string;
  sender: string;
  content: string;
  timestamp: string;
  type: 'text' | 'roll' | 'system';
  roll?: {
    expression: string;
    total: number;
    breakdown: string;
    result: number[];
  };
}

export interface Campaign {
  id: string;
  name: string;
  role: 'DM' | 'PLAYER' | 'SPECTATOR';
  image?: string;
  nextSession?: string;
  members?: { userId: string; role: string }[];
}

export interface Monster {
    id: string;
    name: string;
    type: string;
    size: string;
    ac: number;
    hp: number;
    stats: {
        str: number;
        dex: number;
        con: number;
        int: number;
        wis: number;
        cha: number;
    };
    actions: {
        name: string;
        desc: string;
        attack_bonus?: number;
        damage_dice?: string;
    }[];
}
