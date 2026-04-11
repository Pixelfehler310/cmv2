import React from "react";
import { DefinitionHeader } from "./DefinitionHeader";
import { Save, Loader2, MapPinned, AlertCircle } from "lucide-react";
import { useEntityForm } from "./useEntityForm";

/**
 * Editor for PlaceDefinitions (family="place").
 */

interface PlaceEditorProps {
  initialData?: any;
  packId: string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const PlaceEditor: React.FC<PlaceEditorProps> = ({ initialData, packId, onSave, onCancel }) => {
  const PLACE_TYPES = ["building", "town", "landmark", "dungeon", "room", "wilderness"];

  const { formData, setFormData, fieldErrors, handleSave, mutation } = useEntityForm<{
    name: string;
    slug: string;
    place_type: string;
    map_id: string | null;
  }>({
    initialData: initialData || { name: "", slug: "", place_type: "building", map_id: null },
    packId,
    family: "place",
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
        error={fieldErrors.name}
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-12">
        <div className="flex items-center gap-2 px-1">
          <MapPinned className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Place Details</h3>
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl border border-border bg-surface-50 shadow-sm">
          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase px-1">Place Type</label>
            <select
              value={formData.place_type}
              onChange={(e) => setFormData((prev) => ({ ...prev, place_type: e.target.value }))}
              className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-medium"
            >
              {PLACE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
            {fieldErrors.place_type && (
              <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                <AlertCircle className="h-3 w-3" /> {fieldErrors.place_type}
              </p>
            )}
          </div>
        </section>

        <div className="p-8 rounded-2xl border border-dashed border-border-muted bg-surface-50/30 text-center space-y-2">
          <h4 className="text-xs font-black uppercase tracking-tighter text-muted-foreground/40 italic">Scene & Map Linkage</h4>
          <p className="text-[10px] text-muted-foreground/30 font-medium tracking-tight">Direct Scene rendering and Map association will be enabled in Wave 6.</p>
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
          {!initialData?.id ? "Create Place" : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
