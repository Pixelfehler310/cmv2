import React from "react";
import { BadgeCheck, Lock, Globe, Database, Pencil, Trash2 } from "lucide-react";
import { cn } from "@rpg/ui";

/**
 * Shared Header for all Compendium Definition Editors.
 * Displays primary metadata: ID, Slug, Name, Lifecycle, Pack, Provenance.
 */

interface DefinitionHeaderProps {
  name: string;
  slug: string;
  id?: string;
  packName?: string;
  status?: "draft" | "published" | "archived";
  provenance?: "srd" | "homebrew" | "external";
  onNameChange: (newName: string) => void;
  onDelete?: () => void;
  isReadOnly?: boolean;
  className?: string;
  error?: string;
}

export const DefinitionHeader: React.FC<DefinitionHeaderProps> = ({
  name,
  slug,
  id,
  packName,
  status = "draft",
  provenance = "homebrew",
  onNameChange,
  onDelete,
  isReadOnly = false,
  className,
  error,
}) => {
  return (
    <div className={cn("px-6 py-4 border-b border-border bg-surface-50 sticky top-0 z-10", className)}>
      <div className="flex items-start justify-between gap-4">
        {/* Left Side: Title & Core Metadata */}
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={name}
              onChange={(e) => onNameChange(e.target.value)}
              placeholder="Unnamed Entity"
              readOnly={isReadOnly}
              className={cn(
                "text-2xl font-heading font-bold bg-transparent border-none outline-none focus:ring-0 p-0 text-foreground w-full placeholder:opacity-50 transition-colors",
                isReadOnly ? "cursor-default" : "hover:bg-surface-100/50 focus:bg-surface-100/50 rounded px-1 -mx-1",
                error && "text-destructive placeholder:text-destructive",
              )}
            />
            {isReadOnly && <Lock className="h-4 w-4 text-muted-foreground mr-1 shrink-0" />}
          </div>
          {error && <p className="text-xs text-destructive font-bold">{error}</p>}

          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs font-medium text-muted-foreground">
            {/* ID & Slug - Subtle */}
            <div className="flex items-center gap-1.5 opacity-60">
              <span className="font-mono">{slug}</span>
              {id && (
                <>
                  <span className="opacity-30">•</span>
                  <span className="font-mono text-[10px] uppercase">{id.split("-")[0]}...</span>
                </>
              )}
            </div>

            {/* Badges/Tags */}
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] uppercase font-bold tracking-wider",
                  status === "published"
                    ? "bg-green-500/10 text-green-600 border-green-500/20"
                    : status === "archived"
                      ? "bg-muted text-muted-foreground border-border"
                      : "bg-blue-500/10 text-blue-600 border-blue-500/20",
                )}
              >
                <div className={cn("h-1.5 w-1.5 rounded-full shrink-0", status === "published" ? "bg-green-500 animate-pulse" : status === "archived" ? "bg-muted-foreground" : "bg-blue-500")} />
                {status}
              </div>

              <div className="flex items-center gap-1 px-2 py-0.5 rounded-full border border-border bg-surface-100 text-[10px] uppercase">
                <Database className="h-2.5 w-2.5 shrink-0" />
                {packName || "Unknown Pack"}
              </div>

              {provenance === "srd" && (
                <div className="flex items-center gap-1 px-2 py-0.5 rounded-full border border-yellow-500/20 bg-yellow-500/10 text-yellow-700 text-[10px] uppercase font-bold">
                  <BadgeCheck className="h-2.5 w-2.5 shrink-0" />
                  SRD 5.1
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Primary Actions */}
        {!isReadOnly && onDelete && (
          <button onClick={onDelete} className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-all" title="Delete Definition">
            <Trash2 className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
};
