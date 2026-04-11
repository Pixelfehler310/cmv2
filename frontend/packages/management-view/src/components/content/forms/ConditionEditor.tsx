import React from "react";
import { DefinitionHeader } from "./DefinitionHeader";
import { ModifierSpecListEditor } from "./ModifierSpecListEditor";
import { AlertCircle, Save, Loader2, Zap } from "lucide-react";
import { cn } from "@rpg/ui";
import { useEntityForm } from "./useEntityForm";

/**
 * Editor for ConditionDefinitions (family="condition").
 */

interface ConditionEditorProps {
  initialData?: any;
  packId: string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const ConditionEditor: React.FC<ConditionEditorProps> = ({ initialData, packId, onSave, onCancel }) => {
  const { formData, setFormData, fieldErrors, handleSave, mutation } = useEntityForm<{
    name: string;
    slug: string;
    condition_type: string;
    has_levels: boolean;
    modifier_specs: any[];
  }>({
    initialData: initialData || { name: "", slug: "", condition_type: "status", has_levels: false, modifier_specs: [] },
    packId,
    family: "condition",
    onSave,
  });

  const CONDITION_TYPES = ["status", "affliction", "temporary", "passive_mechanical", "rule_hook"];

  return (
    <div className="flex flex-col h-full bg-background animate-in fade-in slide-in-from-right-4 duration-300">
      <DefinitionHeader
        name={formData.name}
        slug={formData.slug}
        id={initialData?.id}
        packName={initialData?.pack_title || "Current Pack"}
        status={initialData?.status || "draft"}
        onNameChange={(name) => setFormData((prev) => ({ ...prev, name }))}
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* Core Metadata Section */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 px-1">
            <Zap className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Condition Configuration</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl border border-border bg-surface-50 shadow-sm">
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Condition Type</label>
              <select
                value={formData.condition_type}
                onChange={(e) => setFormData((prev) => ({ ...prev, condition_type: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-medium"
              >
                {CONDITION_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                  </option>
                ))}
              </select>
              {fieldErrors.condition_type && (
                <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {fieldErrors.condition_type}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1 flex items-center justify-between">
                Leveled Condition
                <span
                  className={cn(
                    "px-1.5 py-0.5 rounded text-[10px] font-black tracking-widest uppercase transition-colors",
                    formData.has_levels ? "bg-primary text-white" : "bg-muted text-muted-foreground/50",
                  )}
                >
                  {formData.has_levels ? "ON" : "OFF"}
                </span>
              </label>
              <div
                onClick={() => setFormData((p) => ({ ...p, has_levels: !p.has_levels }))}
                className={cn(
                  "relative h-10 w-full rounded-xl border cursor-pointer transition-all flex items-center px-4 gap-2",
                  formData.has_levels ? "bg-primary/5 border-primary/50 text-foreground" : "bg-surface-100 border-border text-muted-foreground",
                )}
              >
                <div
                  className={cn(
                    "h-5 w-5 rounded-full border border-border shadow-sm flex items-center justify-center transition-all",
                    formData.has_levels ? "translate-x-0 bg-primary border-primary" : "translate-x-0 bg-white",
                  )}
                >
                  {formData.has_levels && <div className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />}
                </div>
                <span className="text-xs font-bold font-mono tracking-tight select-none">{formData.has_levels ? "Supports incremental levels (1..N)" : "Binary status effect (ON/OFF)"}</span>
                {fieldErrors.has_levels && (
                  <p className="text-xs text-destructive font-bold px-1 ml-auto shrink-0 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                  </p>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Effects Section */}
        <section className="space-y-4">
          <ModifierSpecListEditor modifiers={formData.modifier_specs} onChange={(modifier_specs) => setFormData((p) => ({ ...p, modifier_specs }))} />
          {fieldErrors.modifier_specs && (
            <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
              <AlertCircle className="h-3.5 w-3.5" />
              {fieldErrors.modifier_specs}
            </p>
          )}
        </section>
      </div>

      {/* Footer Actions */}
      <div className="p-6 border-t border-border bg-surface-50/50 flex items-center justify-between">
        <button onClick={onCancel} className="px-6 py-2.5 rounded-xl font-bold text-sm text-muted-foreground hover:bg-surface-200 transition-all">
          Discard Changes
        </button>

        <button
          onClick={() => handleSave()}
          disabled={mutation.isPending}
          className="group relative flex items-center gap-2 px-8 py-2.5 bg-primary text-white rounded-xl font-bold text-sm shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:hover:scale-100 transition-all"
        >
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {!initialData?.id ? "Create Condition" : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
