import React from "react";
import { DefinitionHeader } from "./DefinitionHeader";
import { Save, Loader2, Flag } from "lucide-react";
import { useEntityForm } from "./useEntityForm";

/**
 * Editor for FactionDefinitions (family="faction").
 */

interface FactionEditorProps {
  initialData?: any;
  packId: string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const FactionEditor: React.FC<FactionEditorProps> = ({ initialData, packId, onSave, onCancel }) => {
  const { formData, setFormData, fieldErrors, handleSave, mutation } = useEntityForm<{
    name: string;
    slug: string;
    alignment: string;
    influence_tier: number;
  }>({
    initialData: initialData || { name: "", slug: "", alignment: "True Neutral", influence_tier: 1 },
    packId,
    family: "faction",
    onSave,
  });

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

      <div className="flex-1 overflow-y-auto p-6 space-y-12">
        <div className="flex items-center gap-2 px-1">
          <Flag className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Faction Alignment & Influence</h3>
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl border border-border bg-surface-50 shadow-sm">
          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase px-1">Alignment</label>
            <input
              type="text"
              value={formData.alignment}
              onChange={(e) => setFormData((prev) => ({ ...prev, alignment: e.target.value }))}
              placeholder="e.g. Lawful Good"
              className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-medium"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase px-1">Influence Tier (1-5)</label>
            <input
              type="number"
              min="1"
              max="5"
              value={formData.influence_tier}
              onChange={(e) => setFormData((prev) => ({ ...prev, influence_tier: Number(e.target.value) }))}
              className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-mono"
            />
          </div>
        </section>

        <div className="p-8 rounded-2xl border border-dashed border-border-muted bg-surface-50/30 text-center space-y-2">
          <h4 className="text-xs font-black uppercase tracking-tighter text-muted-foreground/40 italic">Lore & Members</h4>
          <p className="text-[10px] text-muted-foreground/30 font-medium tracking-tight">Linking to Lore documents and Member Lists will be enabled in Wave 2.</p>
        </div>
      </div>

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
          {!initialData?.id ? "Create Faction" : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
