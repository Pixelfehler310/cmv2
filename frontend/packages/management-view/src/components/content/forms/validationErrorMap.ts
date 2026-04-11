import { ApiClientError } from "@rpg/bridge";

export type ValidationFieldErrorMap = Record<string, string[]>;

type ValidationFieldErrorEntry = {
  msg?: unknown;
};

type ValidationErrorDetail = {
  error?: unknown;
  message?: unknown;
};

type ValidationMessagePayload = {
  field_errors?: Record<string, ValidationFieldErrorEntry[] | string[] | unknown[]>;
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null;
};

const normalizeEntries = (entries: ValidationFieldErrorEntry[] | string[] | unknown[]): string[] => {
  return entries
    .map((entry) => {
      if (typeof entry === "string") {
        return entry;
      }
      if (isRecord(entry) && typeof entry.msg === "string") {
        return entry.msg;
      }
      return "Invalid value.";
    })
    .filter((msg) => msg.trim().length > 0);
};

export const extractValidationErrorMap = (error: unknown): ValidationFieldErrorMap => {
  if (!(error instanceof ApiClientError)) {
    return {};
  }

  if (!isRecord(error.detail)) {
    return {};
  }

  const detail = error.detail as ValidationErrorDetail;
  if (detail.error !== "VALIDATION_FAILED") {
    return {};
  }

  if (!isRecord(detail.message)) {
    if (typeof detail.message === "string" && detail.message.trim().length > 0) {
      return { __root__: [detail.message] };
    }
    return {};
  }

  const messagePayload = detail.message as ValidationMessagePayload;
  if (!isRecord(messagePayload.field_errors)) {
    return {};
  }

  const result: ValidationFieldErrorMap = {};
  for (const [fieldPath, entries] of Object.entries(messagePayload.field_errors)) {
    if (!Array.isArray(entries)) {
      continue;
    }
    const normalized = normalizeEntries(entries);
    if (normalized.length > 0) {
      result[fieldPath] = normalized;
    }
  }

  return result;
};

export const getFieldErrors = (errorMap: ValidationFieldErrorMap, fieldPath: string): string[] => {
  return errorMap[fieldPath] ?? [];
};
