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
  | "effect_not_found"
  | "target_immune"
  | "target_invalid"
  | "concentration_conflict"
  | "stacking_limit_reached"
  | "invalid_duration"
  | "unsupported_effect_operation"
  | "invalid_template_origin"
  | "invalid_template_direction"
  | "template_out_of_range"
  | "no_resolved_targets"
  | "target_not_in_template"
  | "target_no_longer_eligible"
  | "line_of_effect_blocked"
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
    case "effect_not_found":
    case "target_immune":
    case "target_invalid":
    case "concentration_conflict":
    case "stacking_limit_reached":
    case "invalid_duration":
    case "unsupported_effect_operation":
    case "invalid_template_origin":
    case "invalid_template_direction":
    case "template_out_of_range":
    case "no_resolved_targets":
    case "target_not_in_template":
    case "target_no_longer_eligible":
    case "line_of_effect_blocked":
      return normalized;
    default:
      return "unknown";
  }
}
