import React from "react";
import { DefinitionHeader } from "./DefinitionHeader";
import { StringListEditor } from "./StringListEditor";
import { AlertCircle, Save, Loader2, Users } from "lucide-react";
import { cn } from "@rpg/ui";
import { useEntityForm } from "./useEntityForm";

/**
 * Editor for SpeciesDefinitions (family="species").
 */

interface SpeciesEditorProps {
  initialData?: any;
  packId: string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const SpeciesEditor: React.FC<SpeciesEditorProps> = ({ initialData, packId, onSave, onCancel }) => {
  const { formData, setFormData, fieldErrors, handleSave, mutation } = useEntityForm<{
    name: string;
    slug: string;
    speed: number;
    size: string;
    languages: string[];
  }>({
    initialData: initialData || { name: "", slug: "", speed: 30, size: "medium", languages: [] },
    packId,
    family: "species",
    onSave,
  });

  const SIZES = ["tiny", "small", "medium", "large", "huge", "gargantuan"];

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
        {/* Core Stats Section */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 px-1">
            <Users className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Species Traits</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl border border-border bg-surface-50 shadow-sm">
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Walk Speed (ft)</label>
              <input
                type="number"
                value={formData.speed}
                onChange={(e) => setFormData((prev) => ({ ...prev, speed: Number(e.target.value) }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-mono"
              />
              {fieldErrors.speed && (
                <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {fieldErrors.speed}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Body Size</label>
              <select
                value={formData.size}
                onChange={(e) => setFormData((prev) => ({ ...prev, size: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-medium"
              >
                {SIZES.map((s) => (
                  <option key={s} value={s}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </option>
                ))}
              </select>
              {fieldErrors.size && (
                <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {fieldErrors.size}
                </p>
              )}
            </div>
          </div>
        </section>

        {/* Languages Section */}
        <section className="space-y-4">
          <StringListEditor
            label="Innate Languages"
            items={formData.languages}
            onChange={(languages) => setFormData((prev) => ({ ...prev, languages }))}
            placeholder="e.g. Common, Elvish..."
            error={fieldErrors.languages}
          />
        </section>

        {/* Placeholder for future Traits/Abilities */}
        <div className="p-8 rounded-2xl border border-dashed border-border-muted bg-surface-50/30 text-center space-y-2">
          <h4 className="text-xs font-black uppercase tracking-tighter text-muted-foreground/40 italic">Trait & Ability Management</h4>
          <p className="text-[10px] text-muted-foreground/30 font-medium tracking-tight">Linking to Abilities and Feats will be enabled in Wave 2.</p>
        </div>
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
          {!initialData?.id ? "Create Species" : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
