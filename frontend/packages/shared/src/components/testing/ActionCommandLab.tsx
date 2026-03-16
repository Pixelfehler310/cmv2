import { useEffect, useMemo, useState } from "react";
import { useCombatStore } from "../../stores/useCombatStore";
import { selectCommandOutcomeByRequestId, selectPendingCommandByRequestId } from "../../selectors/combatSelectors";
import {
  ACTION_PRESETS,
  applyActorDefaults,
  createEnvelopeFromPreset,
  createInitialPayload,
  getActionPresetsForRole,
  type ActionLabRole,
  type ActionPreset,
  validatePresetPayload,
} from "../../testing/actionCatalog";
import { ActionPayloadEditor } from "./ActionPayloadEditor";
import { ActionResultBadge } from "./ActionResultBadge";
import { ActionSelectButton } from "./ActionSelectButton";

type ActionCommandLabProps = {
  role: ActionLabRole;
  actorId?: string | null;
  title?: string;
  presets?: ActionPreset[];
  allowRawMode?: boolean;
};

const RAW_ENVELOPE_PRESET_ID = "raw_envelope";

export function ActionCommandLab({ role, actorId = null, title = "Action Command Lab", presets = ACTION_PRESETS, allowRawMode }: ActionCommandLabProps): JSX.Element {
  const isConnected = useCombatStore((state) => state.isConnected);
  const dispatchCommand = useCombatStore((state) => state.dispatchCommand);
  const canUseRawMode = allowRawMode ?? role === "dm";

  const availablePresets = useMemo(() => {
    const filteredByRole = presets.filter((preset) => getActionPresetsForRole(role).some((allowed) => allowed.id === preset.id));
    if (canUseRawMode) {
      return filteredByRole;
    }

    return filteredByRole.filter((preset) => preset.id !== RAW_ENVELOPE_PRESET_ID);
  }, [canUseRawMode, presets, role]);

  const [selectedPresetId, setSelectedPresetId] = useState<string>(availablePresets[0]?.id ?? "");
  const [payload, setPayload] = useState<Record<string, unknown>>(() => {
    const initialPreset = availablePresets[0] ?? null;
    return initialPreset ? createInitialPayload(initialPreset) : {};
  });
  const [sendError, setSendError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [currentRequestId, setCurrentRequestId] = useState<string | undefined>(undefined);

  const selectedPreset = useMemo(() => availablePresets.find((preset) => preset.id === selectedPresetId) ?? null, [availablePresets, selectedPresetId]);

  useEffect(() => {
    if (availablePresets.length === 0) {
      setSelectedPresetId("");
      setPayload({});
      return;
    }

    const stillValid = availablePresets.some((preset) => preset.id === selectedPresetId);
    if (stillValid) {
      return;
    }

    setSelectedPresetId(availablePresets[0].id);
    setPayload(createInitialPayload(availablePresets[0]));
  }, [availablePresets, selectedPresetId]);

  useEffect(() => {
    if (!selectedPreset) {
      return;
    }

    setPayload(createInitialPayload(selectedPreset));
    setValidationErrors([]);
    setSendError(null);
  }, [selectedPresetId, selectedPreset]);

  const outcome = useCombatStore((state) => (currentRequestId ? selectCommandOutcomeByRequestId(state, currentRequestId) : null));
  const pending = useCombatStore((state) => (currentRequestId ? selectPendingCommandByRequestId(state, currentRequestId) : null));

  const commandReadyPayload = selectedPreset ? applyActorDefaults(payload, selectedPreset, actorId) : payload;

  const disabledReason = !isConnected ? "Transport disconnected" : availablePresets.length === 0 ? "No presets available for this role" : validationErrors.length > 0 ? validationErrors[0] : null;

  const handlePresetChange = (presetId: string): void => {
    setSelectedPresetId(presetId);
  };

  const handleSend = async (): Promise<void> => {
    if (!selectedPreset) {
      return;
    }

    setSendError(null);

    const errors = validatePresetPayload(selectedPreset, commandReadyPayload);
    setValidationErrors(errors);
    if (errors.length > 0) {
      return;
    }

    const envelope = createEnvelopeFromPreset(selectedPreset, commandReadyPayload);
    const requestId = typeof envelope.request_id === "string" ? envelope.request_id : undefined;
    setCurrentRequestId(requestId);

    try {
      await dispatchCommand(envelope);
    } catch (error) {
      setSendError(error instanceof Error ? error.message : "Failed to send command");
    }
  };

  return (
    <section className="m-4 rounded-md border border-slate-700 bg-slate-900/95 p-4 text-slate-100 shadow-lg">
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wide text-cyan-300">{title}</h3>
          <p className="text-[11px] text-slate-400">role: {role}</p>
        </div>
        {actorId && <p className="text-[11px] text-slate-400">default actor: {actorId}</p>}
      </header>

      <div className="space-y-4">
        <ActionSelectButton
          presets={availablePresets}
          selectedPresetId={selectedPresetId}
          onSelectedPresetIdChange={handlePresetChange}
          onSend={() => {
            void handleSend();
          }}
          disabled={Boolean(disabledReason)}
          disabledReason={disabledReason}
        />

        {selectedPreset && <ActionPayloadEditor preset={selectedPreset} payload={commandReadyPayload} onChange={setPayload} allowRawMode={canUseRawMode} />}

        <ActionResultBadge outcome={outcome} pending={pending} requestId={currentRequestId} />

        {validationErrors.length > 0 && (
          <div className="rounded border border-amber-600/60 bg-amber-700/20 px-3 py-2 text-xs text-amber-200">
            {validationErrors.map((error) => (
              <p key={error}>{error}</p>
            ))}
          </div>
        )}

        {sendError && (
          <div className="rounded border border-rose-600/60 bg-rose-700/20 px-3 py-2 text-xs text-rose-200">
            <p>{sendError}</p>
          </div>
        )}
      </div>
    </section>
  );
}
