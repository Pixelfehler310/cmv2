import React from "react";
import { AlertCircle, Loader2, Save, Swords } from "lucide-react";
import { DefinitionHeader } from "./DefinitionHeader";
import { useEntityForm } from "./useEntityForm";

interface MonsterEditorProps {
  initialData?: any;
  packId: string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const MonsterEditor: React.FC<MonsterEditorProps> = ({ initialData, packId, onSave, onCancel }) => {
  const { formData, setFormData, fieldErrors, handleSave, mutation } = useEntityForm<{
    name: string;
    slug: string;
    type: string;
    challenge_rating: string;
    armor_class: number;
    hit_points: number;
  }>({
    initialData: initialData || {
      name: "",
      slug: "",
      type: "humanoid",
      challenge_rating: "1/4",
      armor_class: 10,
      hit_points: 10,
    },
    packId,
    family: "monster",
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

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        <section className="space-y-4">
          <div className="flex items-center gap-2 px-1">
            <Swords className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Monster Stats</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl border border-border bg-surface-50 shadow-sm">
            <div className="space-y-2 md:col-span-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Type</label>
              <input
                value={formData.type}
                onChange={(e) => setFormData((prev) => ({ ...prev, type: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm"
              />
              {fieldErrors.type && (
                <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {fieldErrors.type}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Challenge Rating</label>
              <input
                value={formData.challenge_rating}
                onChange={(e) => setFormData((prev) => ({ ...prev, challenge_rating: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm"
              />
              {fieldErrors.challenge_rating && (
                <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {fieldErrors.challenge_rating}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Armor Class</label>
              <input
                type="number"
                value={formData.armor_class}
                onChange={(e) => setFormData((prev) => ({ ...prev, armor_class: Number(e.target.value) }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-mono"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Hit Points</label>
              <input
                type="number"
                value={formData.hit_points}
                onChange={(e) => setFormData((prev) => ({ ...prev, hit_points: Number(e.target.value) }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-mono"
              />
            </div>
          </div>
        </section>
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
          {!initialData?.id ? "Create Monster" : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
