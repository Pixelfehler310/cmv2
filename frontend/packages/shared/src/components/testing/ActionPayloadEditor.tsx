import { useMemo, useState } from "react";
import type { ActionPreset, ActionPresetEditableField } from "../../testing/actionCatalog";

type ActionPayloadEditorProps = {
  preset: ActionPreset;
  payload: Record<string, unknown>;
  onChange: (nextPayload: Record<string, unknown>) => void;
  allowRawMode?: boolean;
};

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalizeTextFieldValue(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return "";
}

function normalizeJsonFieldValue(value: unknown): string {
  if (value === undefined) {
    return "";
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return "";
  }
}

function renderHelpText(field: ActionPresetEditableField): JSX.Element | null {
  if (!field.helpText) {
    return null;
  }

  return <p className="mt-1 text-[11px] text-slate-400">{field.helpText}</p>;
}

export function ActionPayloadEditor({ preset, payload, onChange, allowRawMode = false }: ActionPayloadEditorProps): JSX.Element {
  const [isRawMode, setIsRawMode] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const rawPayload = useMemo(() => normalizeJsonFieldValue(payload), [payload]);

  const setPayloadField = (fieldKey: string, value: unknown): void => {
    onChange({
      ...payload,
      [fieldKey]: value,
    });
  };

  const setFieldError = (fieldKey: string, message: string | null): void => {
    setFieldErrors((current) => {
      if (!message) {
        const next = { ...current };
        delete next[fieldKey];
        return next;
      }

      return {
        ...current,
        [fieldKey]: message,
      };
    });
  };

  const handleRawPayloadChange = (rawValue: string): void => {
    if (!rawValue.trim()) {
      onChange({});
      setFieldError("$raw", null);
      return;
    }

    try {
      const parsed = JSON.parse(rawValue) as unknown;
      if (!isObject(parsed)) {
        setFieldError("$raw", "Raw payload must be a JSON object.");
        return;
      }

      setFieldError("$raw", null);
      onChange(parsed);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Invalid JSON";
      setFieldError("$raw", message);
    }
  };

  const renderStructuredField = (field: ActionPresetEditableField): JSX.Element => {
    const key = field.key;
    const value = payload[key];
    const error = fieldErrors[key] ?? null;

    if (field.type === "boolean") {
      return (
        <label key={key} className="flex items-center justify-between rounded border border-slate-700 bg-slate-950/40 px-2 py-2 text-xs text-slate-200">
          <span>{key}</span>
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(event) => {
              setPayloadField(key, event.target.checked);
            }}
          />
        </label>
      );
    }

    if (field.type === "number") {
      return (
        <label key={key} className="block text-[11px] text-slate-300">
          {key}
          <input
            type="number"
            value={typeof value === "number" ? value : 0}
            onChange={(event) => setPayloadField(key, Number(event.target.value))}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
          />
          {renderHelpText(field)}
          {error && <p className="mt-1 text-[11px] text-rose-300">{error}</p>}
        </label>
      );
    }

    if (field.type === "path" || field.type === "json") {
      return (
        <label key={key} className="block text-[11px] text-slate-300">
          {key}
          <textarea
            rows={4}
            value={normalizeJsonFieldValue(value)}
            onChange={(event) => {
              const rawValue = event.target.value;
              if (!rawValue.trim()) {
                setFieldError(key, field.required ? `${key} is required` : null);
                setPayloadField(key, field.type === "path" ? [] : {});
                return;
              }

              try {
                const parsed = JSON.parse(rawValue) as unknown;
                if (field.type === "path" && !Array.isArray(parsed)) {
                  setFieldError(key, "Path must be a JSON array.");
                  return;
                }

                setFieldError(key, null);
                setPayloadField(key, parsed);
              } catch (errorValue) {
                const message = errorValue instanceof Error ? errorValue.message : "Invalid JSON";
                setFieldError(key, message);
              }
            }}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 font-mono text-xs"
          />
          {renderHelpText(field)}
          {error && <p className="mt-1 text-[11px] text-rose-300">{error}</p>}
        </label>
      );
    }

    return (
      <label key={key} className="block text-[11px] text-slate-300">
        {key}
        <input
          type="text"
          value={normalizeTextFieldValue(value)}
          onChange={(event) => setPayloadField(key, event.target.value)}
          className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
        />
        {renderHelpText(field)}
        {error && <p className="mt-1 text-[11px] text-rose-300">{error}</p>}
      </label>
    );
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-300">Payload Editor</p>
        {allowRawMode && (
          <button type="button" onClick={() => setIsRawMode((current) => !current)} className="rounded border border-slate-600 px-2 py-1 text-[11px] text-slate-200 hover:bg-slate-800">
            {isRawMode ? "Structured" : "Raw JSON"}
          </button>
        )}
      </div>

      {isRawMode && allowRawMode ? (
        <label className="block text-[11px] text-slate-300">
          payload
          <textarea
            rows={8}
            value={rawPayload}
            onChange={(event) => handleRawPayloadChange(event.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 font-mono text-xs"
          />
          {fieldErrors.$raw && <p className="mt-1 text-[11px] text-rose-300">{fieldErrors.$raw}</p>}
        </label>
      ) : (
        <div className="grid grid-cols-1 gap-2">{preset.editableFields.map((field) => renderStructuredField(field))}</div>
      )}
    </div>
  );
}
