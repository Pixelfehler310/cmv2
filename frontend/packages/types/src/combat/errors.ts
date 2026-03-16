export type ActionDeniedReasonCode =
  | "not_your_turn"
  | "not_owner"
  | "budget_exhausted"
  | "invalid_action"
  | "invalid_actor"
  | "invalid_target"
  | "invalid_message"
  | "forbidden"
  | "invalid_turn_phase"
  | "no_active_actor"
  | "movement_exhausted"
  | "action_exhausted"
  | "bonus_action_exhausted"
  | "reaction_exhausted"
  | "unsupported_action"
  | "unknown";

export function normalizeActionDeniedReasonCode(code: string | undefined): ActionDeniedReasonCode {
  const normalized = (code ?? "unknown").toLowerCase();

  switch (normalized) {
    case "not_your_turn":
    case "not_owner":
    case "budget_exhausted":
    case "invalid_action":
    case "invalid_actor":
    case "invalid_target":
    case "invalid_message":
    case "forbidden":
    case "invalid_turn_phase":
    case "no_active_actor":
    case "movement_exhausted":
    case "action_exhausted":
    case "bonus_action_exhausted":
    case "reaction_exhausted":
    case "unsupported_action":
      return normalized;
    default:
      return "unknown";
  }
}
