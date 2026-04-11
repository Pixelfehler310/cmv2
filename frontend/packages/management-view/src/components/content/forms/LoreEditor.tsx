import React, { useState, useEffect } from "react";
import { DefinitionHeader } from "./DefinitionHeader";
import { AlertCircle, Save, Loader2, BookOpenText } from "lucide-react";
import { cn } from "@rpg/ui";
import { useEntityForm } from "./useEntityForm";

/**
 * Editor for LoreDefinitions (family="lore").
 * Focuses on rich text content and semantic type labels.
 */

interface LoreEditorProps {
  initialData?: any;
  packId: string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const LoreEditor: React.FC<LoreEditorProps> = ({ initialData, packId, onSave, onCancel }) => {
  const { formData, setFormData, fieldErrors, handleSave, mutation } = useEntityForm<{
    name: string;
    slug: string;
    lore_type: string;
    rich_text_content: string;
  }>({
    initialData: initialData || { name: "", slug: "", lore_type: "description", rich_text_content: "" },
    packId,
    family: "lore",
    onSave,
  });

  const LORE_TYPES = ["description", "history", "myth", "deity", "journal", "location_summary", "factions"];

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
        {/* Lore Metadata Section */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 px-1">
            <BookOpenText className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Lore Configuration</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl border border-border bg-surface-50">
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase px-1">Lore Type</label>
              <select
                value={formData.lore_type}
                onChange={(e) => setFormData((prev) => ({ ...prev, lore_type: e.target.value }))}
                className="w-full px-3 py-2.5 bg-surface-100 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-sm font-medium"
              >
                {LORE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                  </option>
                ))}
              </select>
              {fieldErrors.lore_type && (
                <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {fieldErrors.lore_type}
                </p>
              )}
            </div>
          </div>
        </section>

        {/* Content Section */}
        <section className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">Content</h3>
            </div>
          </div>

          <div className="space-y-2">
            <textarea
              value={formData.rich_text_content}
              onChange={(e) => setFormData((prev) => ({ ...prev, rich_text_content: e.target.value }))}
              placeholder="Start writing lore, history, or descriptions here..."
              className={cn(
                "w-full min-h-[400px] p-6 rounded-2xl border bg-surface-50 focus:bg-surface-100 focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none transition-all text-base leading-relaxed font-serif",
                fieldErrors.rich_text_content ? "border-destructive" : "border-border",
              )}
            />
            {fieldErrors.rich_text_content && (
              <p className="text-xs text-destructive font-bold px-1 flex items-center gap-1">
                <AlertCircle className="h-3 w-3" /> {fieldErrors.rich_text_content}
              </p>
            )}
          </div>
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
          {!initialData?.id ? "Create Lore" : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
