import React from "react";
import { Database } from "lucide-react";
import { DataTable } from "../DataTable";
import { FamilyTab, getColumnsForFamily } from "../config/familyConfig";

interface CompendiumContentPaneProps {
  activeFamily: FamilyTab;
  hasPackSelection: boolean;
  isLoading: boolean;
  data: any[];
  onCreatePack: () => void;
  onRowClick: (item: any) => void;
}

export const CompendiumContentPane: React.FC<CompendiumContentPaneProps> = ({ activeFamily, hasPackSelection, isLoading, data, onCreatePack, onRowClick }) => {
  return (
    <div className="flex-1 bg-surface-50 rounded-2xl border border-border overflow-hidden p-1 relative">
      {!hasPackSelection ? (
        <div className="h-full flex flex-col items-center justify-center gap-4 text-muted-foreground">
          <Database className="opacity-60" />
          <p>Select or create a pack to load and manage definitions.</p>
          <button onClick={onCreatePack} className="btn btn-secondary mt-2">
            Create Pack
          </button>
        </div>
      ) : isLoading ? (
        <div className="h-full flex flex-col items-center justify-center gap-4 text-muted-foreground">
          <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p>Loading compendium data...</p>
        </div>
      ) : (
        <DataTable columns={getColumnsForFamily(activeFamily)} data={data} onRowClick={onRowClick} />
      )}
    </div>
  );
};
