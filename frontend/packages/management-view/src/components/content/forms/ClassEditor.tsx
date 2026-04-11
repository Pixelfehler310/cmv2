import React from "react";
import { DefinitionHeader } from "./DefinitionHeader";
import { StringListEditor } from "./StringListEditor";
import { AlertCircle, Save, Loader2, Shield } from "lucide-react";
import { useEntityForm } from "./useEntityForm";

/**
 * Editor for ClassDefinitions (family="class").
 */

interface ClassEditorProps {
  initialData?: any;
  packId: string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const ClassEditor: React.FC<ClassEditorProps> = ({ initialData, packId, onSave, onCancel }) => {
  const { formData, setFormData, fieldErrors, handleSave, mutation } = useEntityForm<{
    name: string;
    slug: string;
    hit_die: string;
    spellcasting_ability: string | null;
    saving_throw_proficiencies: string[];
    armor_proficiencies: string[];
    weapon_proficiencies: string[];
    tool_proficiencies: string[];
  }>({
    initialData: initialData || {
      name: "",
      slug: "",
      hit_die: "d8",
      spellcasting_ability: null,
      saving_throw_proficiencies: [],
      armor_proficiencies: [],
      weapon_proficiencies: [],
      tool_proficiencies: [],
    },
    packId,
    family: "class",
    onSave,
  });

  const HIT_DICE = ["d6", "d8", "d10", "d12"];
  const ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"];

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
        {/* Core Mechanics */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 px-1">
            <Shield className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Class Fundamentals</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl border border-border bg-surface-50 shadow-sm">
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Hit Die</label>
              <select
                value={formData.hit_die}
                onChange={(e) => setFormData((prev) => ({ ...prev, hit_die: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-mono"
              >
                {HIT_DICE.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
              {fieldErrors.hit_die && (
                <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {fieldErrors.hit_die}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Spellcasting Ability</label>
              <select
                value={formData.spellcasting_ability || ""}
                onChange={(e) => setFormData((prev) => ({ ...prev, spellcasting_ability: e.target.value || null }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-medium"
              >
                <option value="">None / Non-Caster</option>
                {ABILITIES.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {/* Proficiencies */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <section className="space-y-4">
            <StringListEditor
              label="Saving Throws"
              items={formData.saving_throw_proficiencies}
              onChange={(saving_throw_proficiencies) => setFormData((prev) => ({ ...prev, saving_throw_proficiencies }))}
              placeholder="e.g. STR, DEX..."
            />
          </section>

          <section className="space-y-4">
            <StringListEditor
              label="Armor Proficiencies"
              items={formData.armor_proficiencies}
              onChange={(armor_proficiencies) => setFormData((prev) => ({ ...prev, armor_proficiencies }))}
              placeholder="e.g. Light, Medium, Shield..."
            />
          </section>

          <section className="space-y-4">
            <StringListEditor
              label="Weapon Proficiencies"
              items={formData.weapon_proficiencies}
              onChange={(weapon_proficiencies) => setFormData((prev) => ({ ...prev, weapon_proficiencies }))}
              placeholder="e.g. Simple, Martial, Longbow..."
            />
          </section>

          <section className="space-y-4">
            <StringListEditor
              label="Tool Proficiencies"
              items={formData.tool_proficiencies}
              onChange={(tool_proficiencies) => setFormData((prev) => ({ ...prev, tool_proficiencies }))}
              placeholder="e.g. Flute, Thieves' Tools..."
            />
          </section>
        </div>

        <div className="p-8 rounded-2xl border border-dashed border-border-muted bg-surface-50/30 text-center space-y-2">
          <h4 className="text-xs font-black uppercase tracking-tighter text-muted-foreground/40 italic">Class Progression & Features</h4>
          <p className="text-[10px] text-muted-foreground/30 font-medium tracking-tight">Multi-level Ability Table mapping will be enabled in Wave 5.</p>
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
          {!initialData?.id ? "Create Class" : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
