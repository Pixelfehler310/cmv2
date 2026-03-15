export type ActionDeniedReasonCode = "not_your_turn" | "not_owner" | "budget_exhausted" | "invalid_action" | "invalid_actor" | "invalid_target" | "invalid_message" | "forbidden" | "unknown";

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
      return normalized;
    default:
      return "unknown";
  }
}
