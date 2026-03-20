export type CombatInteractionMode = "idle" | "action_selected" | "target_pick_entity" | "target_pick_cell" | "target_pick_direction" | "confirm" | "executing" | "error_recover";

export type CombatClickResolution =
  | { kind: "pass_to_selection" }
  | { kind: "select_target"; targetId: string }
  | { kind: "select_cell"; cellKey: string }
  | { kind: "noop"; reason: "executing" | "missing_context" | "invalid_click" | "not_eligible" };

export type ResolveCombatClickInput = {
  mode: CombatInteractionMode;
  tokenId: string | null;
  cellKey: string | null;
  hasContract: boolean;
  eligibleTargetSet: ReadonlySet<string>;
  eligibleCellSet: ReadonlySet<string>;
};

export function normalizeTargetingMode(targetingMode: string | null | undefined): "self" | "single_target" | "aoe" | "unknown" {
  if (!targetingMode) {
    return "unknown";
  }

  if (targetingMode === "self") {
    return "self";
  }

  if (targetingMode === "single_target" || targetingMode === "single") {
    return "single_target";
  }

  if (targetingMode === "aoe") {
    return "aoe";
  }

  return "unknown";
}

export function targetingModeToInteractionMode(targetingMode: string | null | undefined): CombatInteractionMode {
  const normalized = normalizeTargetingMode(targetingMode);
  if (normalized === "single_target") {
    return "target_pick_entity";
  }

  if (normalized === "aoe") {
    return "target_pick_cell";
  }

  return "idle";
}

export function resolveCombatClick(input: ResolveCombatClickInput): CombatClickResolution {
  const { mode, tokenId, cellKey, hasContract, eligibleCellSet, eligibleTargetSet } = input;

  if (mode === "idle") {
    return { kind: "pass_to_selection" };
  }

  if (mode === "executing") {
    return { kind: "noop", reason: "executing" };
  }

  if (!hasContract) {
    return { kind: "noop", reason: "missing_context" };
  }

  if (mode === "target_pick_entity") {
    if (!tokenId) {
      return { kind: "noop", reason: "invalid_click" };
    }

    if (!eligibleTargetSet.has(tokenId)) {
      return { kind: "noop", reason: "not_eligible" };
    }

    return { kind: "select_target", targetId: tokenId };
  }

  if (mode === "target_pick_cell" || mode === "target_pick_direction") {
    if (!cellKey) {
      return { kind: "noop", reason: "invalid_click" };
    }

    if (!eligibleCellSet.has(cellKey)) {
      return { kind: "noop", reason: "not_eligible" };
    }

    return { kind: "select_cell", cellKey };
  }

  return { kind: "noop", reason: "invalid_click" };
}

export function cellKeyFromCoordinates(x: number, y: number): string {
  return `${x},${y}`;
}

export function parseCellKey(cellKey: string): { x: number; y: number } | null {
  const [xRaw, yRaw] = cellKey.split(",");
  const x = Number.parseInt(xRaw ?? "", 10);
  const y = Number.parseInt(yRaw ?? "", 10);
  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    return null;
  }

  return { x, y };
}
