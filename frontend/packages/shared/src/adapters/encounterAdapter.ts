import type { ActorInstanceWire, CombatantViewModel, EncounterStateWire, GameStateViewModel, TurnBudgetWire } from "@rpg/types";

const DEFAULT_HP_PERCENT_BY_DESCRIPTOR: Record<string, number> = {
  healthy: 1,
  "lightly wounded": 0.8,
  bloodied: 0.5,
  "badly wounded": 0.3,
  "near death": 0.1,
  dead: 0,
};

const DEFAULT_TURN_BUDGET: TurnBudgetWire = {
  action_available: true,
  bonus_action_available: true,
  reaction_available: true,
  max_movement: 30,
  movement_used: 0,
  movement_remaining: 30,
};

function toUiSize(rawSize?: string): string {
  if (!rawSize) {
    return "Medium";
  }

  const lowered = rawSize.toLowerCase();
  return lowered.charAt(0).toUpperCase() + lowered.slice(1);
}

function resolveHpPercent(actor: ActorInstanceWire): number | undefined {
  if (typeof actor.current_hp === "number" && typeof actor.max_hp === "number" && actor.max_hp > 0) {
    return Math.max(0, Math.min(1, actor.current_hp / actor.max_hp));
  }

  const descriptor = (actor.health_status ?? actor.health_descriptor)?.toLowerCase();
  return descriptor ? DEFAULT_HP_PERCENT_BY_DESCRIPTOR[descriptor] : undefined;
}

function resolveTurnBudget(encounter: EncounterStateWire, actorId: string): TurnBudgetWire {
  const rawBudget = encounter.turn_budgets?.[actorId];
  if (!rawBudget) {
    return DEFAULT_TURN_BUDGET;
  }

  return {
    action_available: rawBudget.action_available,
    bonus_action_available: rawBudget.bonus_action_available,
    reaction_available: rawBudget.reaction_available,
    max_movement: rawBudget.max_movement,
    movement_used: rawBudget.movement_used,
    movement_remaining: rawBudget.movement_remaining,
  };
}

function mapActor(encounter: EncounterStateWire, actor: ActorInstanceWire): CombatantViewModel {
  const token = (encounter.map?.tokens ?? []).find((entry) => entry.actor_id === actor.id);
  const pos = token?.position ?? actor.position ?? { x: 0, y: 0 };
  const turnBudget = resolveTurnBudget(encounter, actor.id);

  return {
    id: actor.id,
    owner_user_id: actor.owner_user_id,
    public_name: actor.name ?? actor.id,
    x: pos.x ?? 0,
    y: pos.y ?? 0,
    size: toUiSize(token?.size),
    hp_current: actor.current_hp,
    hp_max: actor.max_hp,
    hp_percent: resolveHpPercent(actor),
    action_used: !turnBudget.action_available,
    bonus_action_used: !turnBudget.bonus_action_available,
    reaction_available: turnBudget.reaction_available,
    max_movement: turnBudget.max_movement,
    movement_used: turnBudget.movement_used,
    movement_remaining: turnBudget.movement_remaining,
  };
}

export function mapEncounterWireToGameState(encounter: EncounterStateWire): GameStateViewModel {
  return {
    round: encounter.round_number ?? 0,
    activeIndex: encounter.active_index ?? 0,
    combatants: (encounter.combatants ?? []).map((actor) => mapActor(encounter, actor)),
  };
}

export function mapActorWireToCombatant(encounter: EncounterStateWire, actor: ActorInstanceWire): CombatantViewModel {
  return mapActor(encounter, actor);
}
