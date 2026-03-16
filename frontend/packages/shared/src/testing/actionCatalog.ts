import type { CommandLikeWsInboundEnvelope, CommandLikeWsInboundType, UtilityWsInboundType, WsInboundEnvelope } from "@rpg/types";
import { COMMAND_LIKE_WS_INBOUND_TYPES, UTILITY_WS_INBOUND_TYPES } from "@rpg/types";
import type { CommandOutcome, CommandSendMetadata } from "../stores/useCombatStore";

export type ActionFieldType = "string" | "number" | "boolean" | "actor-id" | "path" | "json";

export type ActionRolePolicy = "dm-only" | "player-or-dm" | "all";

export type ActionPresetFamily = "lifecycle" | "movement" | "action" | "effect" | "utility";

export type ActionPresetEditableField = {
  key: string;
  type: ActionFieldType;
  required?: boolean;
  helpText?: string;
};

export type ActionPreset = {
  id: string;
  label: string;
  envelopeType: string;
  family: ActionPresetFamily;
  rolePolicy: ActionRolePolicy;
  payloadTemplate: Record<string, unknown>;
  editableFields: ActionPresetEditableField[];
};

export type ActionLabRole = "dm" | "player" | "observer";

export type ActionLabDispatchResult = {
  ok: boolean;
  requestId?: string;
  error?: string;
};

const COMMAND_LIKE_SET = new Set<string>(COMMAND_LIKE_WS_INBOUND_TYPES);
const UTILITY_SET = new Set<string>(UTILITY_WS_INBOUND_TYPES);

export const ACTION_PRESETS: ActionPreset[] = [
  {
    id: "start_combat",
    label: "Start Combat",
    envelopeType: "start_combat",
    family: "lifecycle",
    rolePolicy: "dm-only",
    payloadTemplate: {},
    editableFields: [],
  },
  {
    id: "end_turn",
    label: "End Turn",
    envelopeType: "end_turn",
    family: "lifecycle",
    rolePolicy: "player-or-dm",
    payloadTemplate: {
      actor_id: "",
    },
    editableFields: [{ key: "actor_id", type: "actor-id", required: true, helpText: "Turn actor" }],
  },
  {
    id: "end_combat",
    label: "End Combat",
    envelopeType: "end_combat",
    family: "lifecycle",
    rolePolicy: "dm-only",
    payloadTemplate: {},
    editableFields: [],
  },
  {
    id: "move_token",
    label: "Move Token",
    envelopeType: "move_token",
    family: "movement",
    rolePolicy: "player-or-dm",
    payloadTemplate: {
      actor_id: "",
      path: [{ x: 0, y: 0 }],
    },
    editableFields: [
      { key: "actor_id", type: "actor-id", required: true, helpText: "Actor to move" },
      { key: "path", type: "path", required: true, helpText: "JSON array [{x,y}, ...]" },
    ],
  },
  {
    id: "request_action_action",
    label: "Request Action (Action)",
    envelopeType: "request_action",
    family: "action",
    rolePolicy: "player-or-dm",
    payloadTemplate: {
      actor_id: "",
      action_type: "action",
      action_name: "attack",
      payload: {},
    },
    editableFields: [
      { key: "actor_id", type: "actor-id", required: true },
      { key: "action_name", type: "string", required: true },
      { key: "payload", type: "json", helpText: "Optional action payload object" },
    ],
  },
  {
    id: "request_action_bonus",
    label: "Request Action (Bonus)",
    envelopeType: "request_action",
    family: "action",
    rolePolicy: "player-or-dm",
    payloadTemplate: {
      actor_id: "",
      action_type: "bonus_action",
      action_name: "offhand_attack",
      payload: {},
    },
    editableFields: [
      { key: "actor_id", type: "actor-id", required: true },
      { key: "action_name", type: "string", required: true },
      { key: "payload", type: "json", helpText: "Optional action payload object" },
    ],
  },
  {
    id: "request_action_reaction",
    label: "Request Action (Reaction)",
    envelopeType: "request_action",
    family: "action",
    rolePolicy: "player-or-dm",
    payloadTemplate: {
      actor_id: "",
      action_type: "reaction",
      action_name: "opportunity_attack",
      payload: {},
    },
    editableFields: [
      { key: "actor_id", type: "actor-id", required: true },
      { key: "action_name", type: "string", required: true },
      { key: "payload", type: "json", helpText: "Optional action payload object" },
    ],
  },
  {
    id: "apply_damage",
    label: "Apply Damage",
    envelopeType: "apply_damage",
    family: "effect",
    rolePolicy: "dm-only",
    payloadTemplate: {
      actor_id: "",
      amount: 5,
      damage_type: "force",
    },
    editableFields: [
      { key: "actor_id", type: "actor-id", required: true },
      { key: "amount", type: "number", required: true },
      { key: "damage_type", type: "string", required: true },
    ],
  },
  {
    id: "apply_healing",
    label: "Apply Healing",
    envelopeType: "apply_healing",
    family: "effect",
    rolePolicy: "dm-only",
    payloadTemplate: {
      actor_id: "",
      amount: 5,
    },
    editableFields: [
      { key: "actor_id", type: "actor-id", required: true },
      { key: "amount", type: "number", required: true },
    ],
  },
  {
    id: "apply_condition",
    label: "Apply Condition",
    envelopeType: "apply_condition",
    family: "effect",
    rolePolicy: "dm-only",
    payloadTemplate: {
      actor_id: "",
      condition: "prone",
      source_id: "",
    },
    editableFields: [
      { key: "actor_id", type: "actor-id", required: true },
      { key: "condition", type: "string", required: true },
      { key: "source_id", type: "string", helpText: "Optional source id" },
    ],
  },
  {
    id: "remove_condition",
    label: "Remove Condition",
    envelopeType: "remove_condition",
    family: "effect",
    rolePolicy: "dm-only",
    payloadTemplate: {
      actor_id: "",
      condition: "prone",
    },
    editableFields: [
      { key: "actor_id", type: "actor-id", required: true },
      { key: "condition", type: "string", required: true },
    ],
  },
  {
    id: "add_actor",
    label: "Add Actor",
    envelopeType: "add_actor",
    family: "effect",
    rolePolicy: "dm-only",
    payloadTemplate: {
      definition_slug: "goblin",
      name: "",
      position: { x: 0, y: 0 },
      owner_user_id: "",
    },
    editableFields: [
      { key: "definition_slug", type: "string", required: true },
      { key: "name", type: "string", helpText: "Optional display name" },
      { key: "position", type: "json", helpText: "Optional position object" },
      { key: "owner_user_id", type: "string", helpText: "Optional owner user id" },
    ],
  },
  {
    id: "remove_actor",
    label: "Remove Actor",
    envelopeType: "remove_actor",
    family: "effect",
    rolePolicy: "dm-only",
    payloadTemplate: {
      actor_id: "",
    },
    editableFields: [{ key: "actor_id", type: "actor-id", required: true }],
  },
  {
    id: "request_sync",
    label: "Request Sync",
    envelopeType: "request_sync",
    family: "utility",
    rolePolicy: "all",
    payloadTemplate: {},
    editableFields: [],
  },
  {
    id: "ping",
    label: "Ping",
    envelopeType: "ping",
    family: "utility",
    rolePolicy: "all",
    payloadTemplate: {},
    editableFields: [],
  },
  {
    id: "roll_dice",
    label: "Roll Dice",
    envelopeType: "roll_dice",
    family: "utility",
    rolePolicy: "all",
    payloadTemplate: {
      expression: "1d20+5",
      purpose: "test",
    },
    editableFields: [
      { key: "expression", type: "string", required: true },
      { key: "purpose", type: "string", helpText: "Optional purpose label" },
    ],
  },
  {
    id: "chat_message",
    label: "Chat Message",
    envelopeType: "chat_message",
    family: "utility",
    rolePolicy: "all",
    payloadTemplate: {
      message: "hello from action lab",
    },
    editableFields: [{ key: "message", type: "string", required: true }],
  },
  {
    id: "raw_envelope",
    label: "Raw Envelope",
    envelopeType: "raw_envelope",
    family: "utility",
    rolePolicy: "dm-only",
    payloadTemplate: {
      type: "end_turn",
      payload: {},
    },
    editableFields: [
      { key: "type", type: "string", required: true },
      { key: "payload", type: "json", required: true },
    ],
  },
];

function copyTemplate(value: Record<string, unknown>): Record<string, unknown> {
  return JSON.parse(JSON.stringify(value)) as Record<string, unknown>;
}

function createRequestId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  const randomPart = Math.random().toString(36).slice(2, 10);
  return `req_${Date.now()}_${randomPart}`;
}

export function isCommandLikeEnvelopeType(type: string): type is CommandLikeWsInboundType {
  return COMMAND_LIKE_SET.has(type);
}

export function isUtilityEnvelopeType(type: string): type is UtilityWsInboundType {
  return UTILITY_SET.has(type);
}

export function isAllowedForRole(policy: ActionRolePolicy, role: ActionLabRole): boolean {
  if (policy === "all") {
    return true;
  }

  if (policy === "dm-only") {
    return role === "dm";
  }

  return role === "dm" || role === "player";
}

export function getActionPresetsForRole(role: ActionLabRole): ActionPreset[] {
  return ACTION_PRESETS.filter((preset) => isAllowedForRole(preset.rolePolicy, role));
}

export function getActionPresetById(presetId: string): ActionPreset | null {
  return ACTION_PRESETS.find((preset) => preset.id === presetId) ?? null;
}

export function createInitialPayload(preset: ActionPreset): Record<string, unknown> {
  return copyTemplate(preset.payloadTemplate);
}

export function applyActorDefaults(payload: Record<string, unknown>, preset: ActionPreset, actorId: string | null | undefined): Record<string, unknown> {
  const actorField = preset.editableFields.find((field) => field.type === "actor-id");
  if (!actorField || typeof actorId !== "string" || actorId.trim().length === 0) {
    return payload;
  }

  const currentValue = payload[actorField.key];
  if (typeof currentValue === "string" && currentValue.trim().length > 0) {
    return payload;
  }

  return {
    ...payload,
    [actorField.key]: actorId.trim(),
  };
}

export function validatePresetPayload(preset: ActionPreset, payload: Record<string, unknown>): string[] {
  const errors: string[] = [];

  for (const field of preset.editableFields) {
    if (!field.required) {
      continue;
    }

    const value = payload[field.key];
    if (value === undefined || value === null) {
      errors.push(`${field.key} is required`);
      continue;
    }

    if ((field.type === "string" || field.type === "actor-id") && (typeof value !== "string" || value.trim().length === 0)) {
      errors.push(`${field.key} must be a non-empty string`);
      continue;
    }

    if (field.type === "number" && (typeof value !== "number" || Number.isNaN(value))) {
      errors.push(`${field.key} must be a number`);
      continue;
    }

    if (field.type === "path") {
      if (!Array.isArray(value)) {
        errors.push(`${field.key} must be an array`);
        continue;
      }

      const isPathValid = value.every((step) => {
        if (typeof step !== "object" || step === null) {
          return false;
        }

        const record = step as Record<string, unknown>;
        return typeof record.x === "number" && typeof record.y === "number";
      });

      if (!isPathValid) {
        errors.push(`${field.key} must be an array of {x:number, y:number}`);
      }
    }
  }

  return errors;
}

export function createEnvelopeFromPreset(preset: ActionPreset, payload: Record<string, unknown>): WsInboundEnvelope {
  if (preset.id === "raw_envelope") {
    const rawType = typeof payload.type === "string" ? payload.type.trim() : "";
    const rawPayload = payload.payload;

    return {
      type: rawType || "unknown",
      payload: typeof rawPayload === "object" && rawPayload !== null ? (rawPayload as Record<string, unknown>) : {},
      request_id: undefined,
    };
  }

  const envelope: WsInboundEnvelope = {
    type: preset.envelopeType,
    payload,
    request_id: undefined,
  };

  if (!isCommandLikeEnvelopeType(envelope.type)) {
    return envelope;
  }

  return {
    ...(envelope as CommandLikeWsInboundEnvelope),
    request_id: createRequestId(),
  };
}

export function classifyOutcome(outcome: CommandOutcome | null): "success" | "denied" | "error" | "pending" | "idle" {
  if (!outcome) {
    return "idle";
  }

  if (outcome.terminalType === "action_denied" || outcome.terminalType === "command_denied") {
    return "denied";
  }

  if (outcome.terminalType === "error" || outcome.terminalType === "dispatch_error" || !outcome.ok) {
    return "error";
  }

  return "success";
}

export function isPendingRequest(pending: CommandSendMetadata | null): boolean {
  return pending !== null;
}
