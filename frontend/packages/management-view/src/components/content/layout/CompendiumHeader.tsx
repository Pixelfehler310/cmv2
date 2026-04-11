import React from "react";
import { Database, Plus, Search } from "lucide-react";
import { FamilyTab, getAddLabel } from "../config/familyConfig";

interface CompendiumHeaderProps {
  activeFamily: FamilyTab;
  activePackId: string;
  packs?: any[];
  searchQuery: string;
  hasPackSelection: boolean;
  onPackChange: (packId: string) => void;
  onSearchQueryChange: (value: string) => void;
  onCreatePack: () => void;
  onAddEntity: () => void;
}

export const CompendiumHeader: React.FC<CompendiumHeaderProps> = ({
  activeFamily,
  activePackId,
  packs,
  searchQuery,
  hasPackSelection,
  onPackChange,
  onSearchQueryChange,
  onCreatePack,
  onAddEntity,
}) => {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
      <div>
        <h2 className="text-3xl font-heading text-foreground flex items-center gap-2">
          <Database className="text-primary" />
          Content Manager
        </h2>
        <p className="text-muted-foreground">Manage your homebrew compendium and rules elements.</p>
      </div>

      <div className="flex items-center gap-3">
        <div className="min-w-56 flex gap-2">
          <select
            value={activePackId}
            onChange={(event) => onPackChange(event.target.value)}
            className="flex-1 w-full px-3 py-2 bg-surface-100 border border-border rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
          >
            <option value="">Select pack...</option>
            {packs && packs.length > 0 ? (
              packs.map((pack: any) => (
                <option key={pack.id} value={pack.id}>
                  {pack.title || pack.id}
                </option>
              ))
            ) : (
              <option value="" disabled>
                No packs available
              </option>
            )}
          </select>
          <button onClick={onCreatePack} className="px-3 py-2 bg-surface-100 border border-border rounded-xl hover:bg-surface-200 transition-colors" title="Create New Pack">
            <Plus size={18} className="text-primary" />
          </button>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
          <input
            type="text"
            placeholder="Search entities..."
            value={searchQuery}
            onChange={(event) => onSearchQueryChange(event.target.value)}
            className="pl-10 pr-4 py-2 bg-surface-100 border border-border rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all w-64"
          />
        </div>

        <button
          disabled={!hasPackSelection}
          onClick={onAddEntity}
          className="btn btn-primary gradient-quest px-6 shadow-sm hover:scale-105 active:scale-95 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          <Plus size={18} />
          Add {getAddLabel(activeFamily)}
        </button>
      </div>
    </div>
  );
};
