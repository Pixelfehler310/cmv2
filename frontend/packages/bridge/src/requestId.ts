import type { WsInboundEnvelope } from "@rpg/types";
import { COMMAND_LIKE_WS_INBOUND_TYPES } from "@rpg/types";

const COMMAND_LIKE_TYPE_SET = new Set<string>(COMMAND_LIKE_WS_INBOUND_TYPES);

function createRequestId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  const randomPart = Math.random().toString(36).slice(2, 10);
  return `req_${Date.now()}_${randomPart}`;
}

export function isCommandLikeInboundType(type: string): boolean {
  return COMMAND_LIKE_TYPE_SET.has(type);
}

// Ensures command-like envelopes carry a request_id before transport send.
export function ensureRequestId<TEnvelope extends WsInboundEnvelope>(envelope: TEnvelope): TEnvelope {
  if (!isCommandLikeInboundType(envelope.type)) {
    return envelope;
  }

  const requestId = typeof envelope.request_id === "string" ? envelope.request_id.trim() : "";
  if (requestId.length > 0) {
    return envelope;
  }

  return {
    ...envelope,
    request_id: createRequestId(),
  } as TEnvelope;
}
