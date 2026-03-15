import type { WsOutboundEnvelope } from "@rpg/types";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function parseWsOutboundEnvelope(message: unknown): WsOutboundEnvelope | null {
  if (typeof message === "string") {
    try {
      return parseWsOutboundEnvelope(JSON.parse(message));
    } catch {
      return null;
    }
  }

  if (!isRecord(message)) {
    return null;
  }

  const type = message.type;
  if (typeof type !== "string") {
    return null;
  }

  const payload = isRecord(message.payload) ? message.payload : {};
  const requestId = typeof message.request_id === "string" ? message.request_id : undefined;

  return {
    type,
    payload,
    request_id: requestId,
  };
}
