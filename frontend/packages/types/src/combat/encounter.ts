export interface PositionWire {
  x: number;
  y: number;
}

export interface MapTokenWire {
  actor_id: string;
  position?: PositionWire;
  size?: string;
}

export interface MapStateWire {
  width?: number;
  height?: number;
  grid_type?: string;
  tokens?: MapTokenWire[];
}

export interface TurnBudgetWire {
  action_available: boolean;
  bonus_action_available: boolean;
  reaction_available: boolean;
  max_movement: number;
  movement_used: number;
  movement_remaining: number;
}

export interface ActorInstanceWire {
  id: string;
  owner_user_id?: string | null;
  definition_slug?: string;
  name?: string;
  actor_type?: string;
  position?: PositionWire;
  current_hp?: number;
  max_hp?: number;
  health_status?: string;
  health_descriptor?: string;
}

export interface EncounterStateWire {
  id?: string;
  campaign_id?: string;
  round_number?: number;
  turn_phase?: string;
  active_index?: number;
  combatants?: ActorInstanceWire[];
  turn_budgets?: Record<string, TurnBudgetWire>;
  map?: MapStateWire;
}

export interface CombatantViewModel {
  id: string;
  owner_user_id?: string | null;
  public_name: string;
  x: number;
  y: number;
  size?: string;
  hp_current?: number;
  hp_max?: number;
  hp_percent?: number;
  action_used: boolean;
  bonus_action_used: boolean;
  reaction_available: boolean;
  movement_remaining: number;
  max_movement: number;
  movement_used: number;
}

export interface GameStateViewModel {
  round: number;
  combatants: CombatantViewModel[];
  activeIndex: number;
}

export interface ActionFeedbackViewModel {
  actorId: string;
  actionType: string;
  reasonCode: string;
  message: string;
  at: string;
}
