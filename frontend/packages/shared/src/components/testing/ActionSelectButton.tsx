import { useMemo } from "react";
import type { KeyboardEvent } from "react";
import type { ActionPreset } from "../../testing/actionCatalog";

type ActionSelectButtonProps = {
  presets: ActionPreset[];
  selectedPresetId: string;
  onSelectedPresetIdChange: (presetId: string) => void;
  onSend: () => void;
  disabled?: boolean;
  disabledReason?: string | null;
};

export function ActionSelectButton({ presets, selectedPresetId, onSelectedPresetIdChange, onSend, disabled = false, disabledReason = null }: ActionSelectButtonProps): JSX.Element {
  const selectedIndex = useMemo(() => presets.findIndex((preset) => preset.id === selectedPresetId), [presets, selectedPresetId]);

  const cyclePreset = (step: number): void => {
    if (presets.length === 0) {
      return;
    }

    const baseIndex = selectedIndex >= 0 ? selectedIndex : 0;
    const nextIndex = (baseIndex + step + presets.length) % presets.length;
    onSelectedPresetIdChange(presets[nextIndex].id);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>): void => {
    if (event.key === "[") {
      event.preventDefault();
      cyclePreset(-1);
    }

    if (event.key === "]") {
      event.preventDefault();
      cyclePreset(1);
    }
  };

  const selectedPreset = selectedIndex >= 0 ? presets[selectedIndex] : presets[0];

  return (
    <div className="space-y-2" onKeyDown={handleKeyDown}>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onSend}
          disabled={disabled || presets.length === 0}
          className="rounded bg-sky-700 px-3 py-2 text-xs font-semibold text-white hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Send {selectedPreset ? selectedPreset.label : "Command"}
        </button>

        <button
          type="button"
          onClick={() => cyclePreset(-1)}
          disabled={presets.length < 2}
          className="rounded border border-slate-600 px-2 py-2 text-xs text-slate-100 hover:bg-slate-800 disabled:opacity-40"
          aria-label="Select previous preset"
        >
          [
        </button>

        <button
          type="button"
          onClick={() => cyclePreset(1)}
          disabled={presets.length < 2}
          className="rounded border border-slate-600 px-2 py-2 text-xs text-slate-100 hover:bg-slate-800 disabled:opacity-40"
          aria-label="Select next preset"
        >
          ]
        </button>
      </div>

      <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-300">
        Preset
        <select
          value={selectedPresetId}
          onChange={(event) => onSelectedPresetIdChange(event.target.value)}
          className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-slate-100"
        >
          {presets.map((preset) => (
            <option key={preset.id} value={preset.id}>
              {preset.label} ({preset.envelopeType})
            </option>
          ))}
        </select>
      </label>

      {disabledReason && <p className="text-xs text-amber-300">{disabledReason}</p>}
    </div>
  );
}
