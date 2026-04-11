import React from "react";
import { AlertCircle, BookOpen, Loader2, Save } from "lucide-react";
import { DefinitionHeader } from "./DefinitionHeader";
import { useEntityForm } from "./useEntityForm";

interface SpellEditorProps {
  initialData?: any;
  packId: string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const SpellEditor: React.FC<SpellEditorProps> = ({ initialData, packId, onSave, onCancel }) => {
  const { formData, setFormData, fieldErrors, handleSave, mutation } = useEntityForm<{
    name: string;
    slug: string;
    level: number;
    school: string;
    casting_time: string;
    range: string;
    duration: string;
  }>({
    initialData: initialData || {
      name: "",
      slug: "",
      level: 0,
      school: "evocation",
      casting_time: "1 action",
      range: "Self",
      duration: "Instantaneous",
    },
    packId,
    family: "spell",
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
            <BookOpen className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Spell Metadata</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl border border-border bg-surface-50 shadow-sm">
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Level</label>
              <input
                type="number"
                min={0}
                max={9}
                value={formData.level}
                onChange={(e) => setFormData((prev) => ({ ...prev, level: Number(e.target.value) }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-mono"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">School</label>
              <input
                value={formData.school}
                onChange={(e) => setFormData((prev) => ({ ...prev, school: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm"
              />
              {fieldErrors.school && (
                <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {fieldErrors.school}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Casting Time</label>
              <input
                value={formData.casting_time}
                onChange={(e) => setFormData((prev) => ({ ...prev, casting_time: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Range</label>
              <input
                value={formData.range}
                onChange={(e) => setFormData((prev) => ({ ...prev, range: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm"
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Duration</label>
              <input
                value={formData.duration}
                onChange={(e) => setFormData((prev) => ({ ...prev, duration: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm"
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
          {!initialData?.id ? "Create Spell" : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
