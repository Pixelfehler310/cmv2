import React, { useState } from "react";
// Would typically use react-hook-form and zod here, but scaffolding pure React form for demonstration

export const MonsterForm = ({ initialData, onSave, onCancel }: { initialData?: any; onSave: (data: any) => void; onCancel: () => void }) => {
  const [formData, setFormData] = useState({
    name: initialData?.name || "",
    type: initialData?.type || "Humanoid",
    cr: initialData?.cr || "1/4",
    hp: initialData?.hp || 10,
    ac: initialData?.ac || 10,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
      <div className="bg-surface-100 rounded-3xl shadow-xl w-full max-w-2xl overflow-hidden border border-border animate-fade-in-up">
        {/* Header */}
        <div className="px-8 py-6 border-b border-border gradient-quest mb-1">
          <h2 className="text-2xl font-heading text-white font-bold drop-shadow-md">{initialData ? "Edit Monster" : "New Monster"}</h2>
          <p className="text-white/80 text-sm font-medium">Define the core statistics of the creature.</p>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="col-span-2">
              <label className="block text-sm font-bold text-muted-foreground mb-2">Name</label>
              <input required name="name" value={formData.name} onChange={handleChange} className="input w-full bg-surface-50 focus:bg-surface-100" placeholder="e.g. Goblin Boss" />
            </div>

            <div>
              <label className="block text-sm font-bold text-muted-foreground mb-2">Creature Type</label>
              <select name="type" value={formData.type} onChange={handleChange} className="input w-full bg-surface-50">
                <option>Humanoid</option>
                <option>Undead</option>
                <option>Monstrosity</option>
                <option>Dragon</option>
                <option>Ooze</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-muted-foreground mb-2">Challenge Rating (CR)</label>
              <input name="cr" value={formData.cr} onChange={handleChange} className="input w-full bg-surface-50" placeholder="1/4, 1, 2, 10..." />
            </div>

            <div>
              <label className="block text-sm font-bold text-muted-foreground mb-2">Hit Points (HP)</label>
              <input type="number" name="hp" value={formData.hp} onChange={handleChange} className="input w-full bg-surface-50" min="1" />
            </div>

            <div>
              <label className="block text-sm font-bold text-muted-foreground mb-2">Armor Class (AC)</label>
              <input type="number" name="ac" value={formData.ac} onChange={handleChange} className="input w-full bg-surface-50" min="1" />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="mt-8 pt-6 border-t border-border flex justify-end gap-4">
            <button type="button" onClick={onCancel} className="btn btn-secondary px-8">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary gradient-quest animate-boing-active px-8 font-bold text-lg">
              Save Monster
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
