import React from "react";
import { DefinitionHeader } from "./DefinitionHeader";
import { StringListEditor } from "./StringListEditor";
import { Save, Loader2, GraduationCap } from "lucide-react";
import { useEntityForm } from "./useEntityForm";

/**
 * Editor for BackgroundDefinitions (family="background").
 */

interface BackgroundEditorProps {
  initialData?: any;
  packId: string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const BackgroundEditor: React.FC<BackgroundEditorProps> = ({ initialData, packId, onSave, onCancel }) => {
  const { formData, setFormData, fieldErrors, handleSave, mutation } = useEntityForm<{
    name: string;
    slug: string;
    skill_proficiencies: string[];
    tool_proficiencies: string[];
    languages: string[];
  }>({
    initialData: initialData || {
      name: "",
      slug: "",
      skill_proficiencies: [],
      tool_proficiencies: [],
      languages: [],
    },
    packId,
    family: "background",
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
          <GraduationCap className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Background Proficiencies</h3>
        </div>

        <section className="space-y-4">
          <StringListEditor
            label="Skill Proficiencies"
            items={formData.skill_proficiencies}
            onChange={(skill_proficiencies) => setFormData((prev) => ({ ...prev, skill_proficiencies }))}
            placeholder="e.g. Athletics, Deception..."
            error={fieldErrors.skill_proficiencies}
          />
        </section>

        <section className="space-y-4">
          <StringListEditor
            label="Tool Proficiencies"
            items={formData.tool_proficiencies}
            onChange={(tool_proficiencies) => setFormData((prev) => ({ ...prev, tool_proficiencies }))}
            placeholder="e.g. Thieves' Tools, Flute..."
            error={fieldErrors.tool_proficiencies}
          />
        </section>

        <section className="space-y-4">
          <StringListEditor
            label="Bonus Languages"
            items={formData.languages}
            onChange={(languages) => setFormData((prev) => ({ ...prev, languages }))}
            placeholder="e.g. Draconic, Celestial..."
            error={fieldErrors.languages}
          />
        </section>

        <div className="p-8 rounded-2xl border border-dashed border-border-muted bg-surface-50/30 text-center space-y-2">
          <h4 className="text-xs font-black uppercase tracking-tighter text-muted-foreground/40 italic">Starting Equipment & Features</h4>
          <p className="text-[10px] text-muted-foreground/30 font-medium tracking-tight">Linking to Wealth and Equipment Tables will be enabled in Wave 3.</p>
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
          {!initialData?.id ? "Create Background" : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
