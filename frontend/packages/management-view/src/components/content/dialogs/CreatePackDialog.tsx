import React, { useState } from "react";
import { X, Loader2, AlertCircle } from "lucide-react";
import { useCreateCompendiumPack } from "../../../hooks/useEntities";
import { cn } from "@rpg/ui";

interface CreatePackDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (packId: string) => void;
}

export const CreatePackDialog: React.FC<CreatePackDialogProps> = ({ isOpen, onClose, onSuccess }) => {
  const createMutation = useCreateCompendiumPack();
  const [formData, setFormData] = useState({ id: "", title: "" });
  const [error, setError] = useState<string>("");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!formData.id.trim() || !formData.title.trim()) {
      setError("Please provide both an ID and a Title.");
      return;
    }

    try {
      const result: any = await createMutation.mutateAsync({
        id: formData.id.trim(),
        title: formData.title.trim(),
      });
      if (onSuccess) onSuccess(result?.id || formData.id);
      setFormData({ id: "", title: "" });
    } catch (err: any) {
      setError(err?.message || "Failed to create pack.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md bg-background rounded-2xl border border-border shadow-2xl p-6 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-heading font-bold text-foreground">Create New Pack</h2>
          <button onClick={onClose} className="p-2 hover:bg-surface-100 rounded-lg transition-colors">
            <X size={20} className="text-muted-foreground" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="flex items-start gap-2 bg-destructive/10 border border-destructive/20 text-destructive p-3 rounded-lg text-sm font-bold">
              <AlertCircle size={16} className="mt-0.5 shrink-0" />
              <p>{error}</p>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase px-1">Pack Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => {
                const title = e.target.value;
                setFormData((prev) => ({
                  ...prev,
                  title,
                  id:
                    prev.id ||
                    title
                      .toLowerCase()
                      .replace(/[^a-z0-9]+/g, "-")
                      .replace(/(^-|-$)+/g, ""),
                }));
              }}
              placeholder="e.g. My Custom Content"
              className="w-full px-3 py-2 bg-surface-100 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase px-1">Pack ID</label>
            <input
              type="text"
              value={formData.id}
              onChange={(e) => setFormData((prev) => ({ ...prev, id: e.target.value }))}
              placeholder="e.g. my-custom-content"
              className="w-full px-3 py-2 bg-surface-100 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-mono text-sm"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button type="button" onClick={onClose} className="w-1/3 px-4 py-2 bg-surface-100 text-foreground font-medium rounded-lg hover:bg-surface-200 transition-colors">
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1 px-4 py-2 bg-primary text-white font-bold rounded-lg hover:bg-primary/90 flex items-center justify-center gap-2"
            >
              {createMutation.isPending && <Loader2 size={16} className="animate-spin" />}
              {createMutation.isPending ? "Creating..." : "Create Pack"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
