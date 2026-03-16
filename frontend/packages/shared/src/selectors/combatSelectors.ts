import type { CombatStore, CommandOutcome, CommandSendMetadata } from "../stores/useCombatStore";

export function selectLatestCommandOutcome(state: CombatStore): CommandOutcome | null {
  return state.latestCommandOutcome;
}

export function selectCommandOutcomeByRequestId(state: CombatStore, requestId: string): CommandOutcome | null {
  return state.commandOutcomesByRequestId[requestId] ?? null;
}

export function selectPendingCommandByRequestId(state: CombatStore, requestId: string): CommandSendMetadata | null {
  return state.pendingCommandsByRequestId[requestId] ?? null;
}
