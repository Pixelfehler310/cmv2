import type { CombatStore, CommandOutcome, CommandSendMetadata } from "../stores/useCombatStore";
import type { AttackPreviewPayload, ExecutableActionPayload, MovementPreviewPayload } from "@rpg/types";

export function selectLatestCommandOutcome(state: CombatStore): CommandOutcome | null {
  return state.latestCommandOutcome;
}

export function selectCommandOutcomeByRequestId(state: CombatStore, requestId: string): CommandOutcome | null {
  return state.commandOutcomesByRequestId[requestId] ?? null;
}

export function selectPendingCommandByRequestId(state: CombatStore, requestId: string): CommandSendMetadata | null {
  return state.pendingCommandsByRequestId[requestId] ?? null;
}

export function selectExecutableActionsForActor(state: CombatStore, actorId: string | null | undefined): ExecutableActionPayload[] {
  if (!actorId) {
    return [];
  }

  const snapshot = state.executableActionsSnapshot;
  if (!snapshot || snapshot.actor_id !== actorId) {
    return [];
  }

  return snapshot.actions;
}

export function selectMovementPreviewForActor(state: CombatStore, actorId: string | null | undefined): MovementPreviewPayload | null {
  if (!actorId) {
    return null;
  }

  const preview = state.movementPreview;
  if (!preview || preview.actor_id !== actorId) {
    return null;
  }

  return preview;
}

export function selectReachableCellSetForActor(state: CombatStore, actorId: string | null | undefined): Set<string> {
  const preview = selectMovementPreviewForActor(state, actorId);
  if (!preview) {
    return new Set<string>();
  }

  return new Set(preview.reachable.map((cell) => `${cell.x},${cell.y}`));
}

export function selectAttackPreviewForActorAction(state: CombatStore, actorId: string | null | undefined, actionId: string | null | undefined): AttackPreviewPayload | null {
  if (!actorId || !actionId) {
    return null;
  }

  const preview = state.attackPreview;
  if (!preview || preview.actor_id !== actorId || preview.action_id !== actionId) {
    return null;
  }

  return preview;
}

export function selectAttackEligibleTargetSetForActorAction(state: CombatStore, actorId: string | null | undefined, actionId: string | null | undefined): Set<string> {
  const preview = selectAttackPreviewForActorAction(state, actorId, actionId);
  if (!preview) {
    return new Set<string>();
  }

  return new Set(preview.eligible_target_ids);
}

export function selectAttackEligibleCellSetForActorAction(state: CombatStore, actorId: string | null | undefined, actionId: string | null | undefined): Set<string> {
  const preview = selectAttackPreviewForActorAction(state, actorId, actionId);
  if (!preview || !preview.eligible_cells) {
    return new Set<string>();
  }

  return new Set(preview.eligible_cells.map((cell) => `${cell.x},${cell.y}`));
}

export function selectAttackAffectedCellSetForActorAction(state: CombatStore, actorId: string | null | undefined, actionId: string | null | undefined): Set<string> {
  const preview = selectAttackPreviewForActorAction(state, actorId, actionId);
  if (!preview?.template_projection?.affected_cells) {
    return new Set<string>();
  }

  return new Set(preview.template_projection.affected_cells.map((cell) => `${cell.x},${cell.y}`));
}
