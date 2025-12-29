export interface Character {
  id: string;
  name: string;
  player_name?: string;
  campaign_id?: string;
  
  // Core Identity
  species_id: string;
  class_id: string;
  background_id?: string;
  
  level: number;
  xp: number;
  alignment?: string;
  
  // Stats
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  
  // Vitals
  max_hp: number;
  current_hp: number;
  temp_hp: number;
  hit_dice: string;
  armor_class: number;
  speed: number;
  initiative: number;
  
  // State
  inventory: any[]; // Define stricter types later
  spells: any[];
  spell_slots: Record<string, number>;
  actions: any[];
  effects: any[];
}
