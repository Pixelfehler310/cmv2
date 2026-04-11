import React, { useState } from "react";
import { Plus, X, GripVertical, AlertCircle, Settings2, Trash2, ArrowRight } from "lucide-react";
import { cn } from "@rpg/ui";

/**
 * Shared Modifier Spec List Editor.
 * Used for building mechanic rules like +2 Strength, Status: Grappled, etc.
 */

interface ModifierSpec {
  id?: string;
  type: string;
  target: string;
  value: any;
  priority?: number;
  tags?: string[];
}

interface ModifierSpecListEditorProps {
  modifiers: Record<string, any>[];
  onChange: (modifiers: Record<string, any>[]) => void;
  label?: string;
  className?: string;
  isReadOnly?: boolean;
}

export const ModifierSpecListEditor: React.FC<ModifierSpecListEditorProps> = ({ modifiers, onChange, label = "Modifier Specs", className, isReadOnly = false }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const handleAdd = () => {
    const fresh: ModifierSpec = {
      type: "bonus",
      target: "str",
      value: 1,
      priority: 0,
      tags: [],
    };
    onChange([...modifiers, fresh]);
    setExpandedIndex(modifiers.length);
  };

  const handleRemove = (index: number) => {
    const newItems = modifiers.filter((_, i) => i !== index);
    onChange(newItems);
    if (expandedIndex === index) setExpandedIndex(null);
    else if (expandedIndex !== null && expandedIndex > index) setExpandedIndex(expandedIndex - 1);
  };

  const handleUpdate = (index: number, updates: Partial<ModifierSpec>) => {
    const nextModifiers = [...modifiers];
    nextModifiers[index] = { ...nextModifiers[index], ...updates };
    onChange(nextModifiers);
  };

  const MODIFIER_TYPES = ["bonus", "status", "advantage", "disadvantage", "multiplier", "override"];
  const TARGET_STATS = ["str", "dex", "con", "int", "wis", "cha", "ac", "speed", "hp_max", "initiative", "saving_throw"];

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <Settings2 className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-black uppercase tracking-widest text-foreground/60">{label}</h3>
        </div>
        <span className="text-[10px] font-bold text-muted-foreground/40 bg-surface-100 px-1.5 py-0.5 rounded border border-border">{modifiers.length} active</span>
      </div>

      <div className="space-y-2">
        {modifiers.map((mod, index) => (
          <div
            key={mod.id || index}
            className={cn(
              "group rounded-2xl border bg-surface-50 transition-all",
              expandedIndex === index ? "border-primary ring-4 ring-primary/5 bg-surface-100 shadow-sm" : "border-border-muted hover:border-border hover:bg-surface-100/50",
            )}
          >
            {/* Row Trigger */}
            <div className="px-4 py-3 flex items-center gap-4 cursor-pointer" onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}>
              {!isReadOnly && <GripVertical className="h-4 w-4 text-muted-foreground/30 group-hover:text-muted-foreground/60 shrink-0 cursor-grab" />}

              <div className="flex-1 flex items-center gap-2 overflow-hidden">
                <div className="px-2 py-0.5 rounded-lg bg-primary/10 text-primary text-[10px] font-black uppercase tracking-wider shrink-0">{mod.type || "MISSING"}</div>
                <ArrowRight className="h-3 w-3 text-muted-foreground/40 shrink-0" />
                <div className="text-sm font-bold truncate">{mod.target || "Target"}</div>
                <div className="text-sm font-mono text-muted-foreground truncate">{typeof mod.value === "object" ? JSON.stringify(mod.value) : String(mod.value)}</div>
              </div>

              {!isReadOnly && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemove(index);
                  }}
                  className="p-1 px-2 text-muted-foreground/0 group-hover:text-muted-foreground/60 hover:text-destructive hover:bg-destructive/10 rounded-md transition-all text-[10px] font-black uppercase flex items-center gap-1"
                >
                  <Trash2 className="h-3 w-3" />
                  Remove
                </button>
              )}
            </div>

            {/* Expansion Panel */}
            {expandedIndex === index && !isReadOnly && (
              <div className="px-6 py-6 pt-2 border-t border-border-muted/50 grid grid-cols-2 gap-x-6 gap-y-4 animate-in slide-in-from-top-1">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-muted-foreground uppercase px-1">Source Type</label>
                  <select
                    value={mod.type}
                    onChange={(e) => handleUpdate(index, { type: e.target.value })}
                    className="w-full px-3 py-2 bg-surface-50 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none text-sm transition-all"
                  >
                    {MODIFIER_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-muted-foreground uppercase px-1">Stat Target</label>
                  <input
                    value={mod.target}
                    onChange={(e) => handleUpdate(index, { target: e.target.value })}
                    list="modifier-targets"
                    className="w-full px-3 py-2 bg-surface-50 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none text-sm transition-all font-mono"
                    placeholder="e.g. str, ac..."
                  />
                  <datalist id="modifier-targets">
                    {TARGET_STATS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </datalist>
                </div>

                <div className="space-y-2 col-span-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase px-1">Value (JSON/Num)</label>
                  <input
                    value={typeof mod.value === "string" ? mod.value : JSON.stringify(mod.value)}
                    onChange={(e) => {
                      const val = e.target.value;
                      // Attempt to parse as JSON or number
                      try {
                        const parsed = JSON.parse(val);
                        handleUpdate(index, { value: parsed });
                      } catch {
                        handleUpdate(index, { value: isNaN(Number(val)) ? val : Number(val) });
                      }
                    }}
                    className="w-full px-3 py-2 bg-surface-50 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none text-sm font-mono transition-all"
                    placeholder="e.g. 5, true, [1, 2]"
                  />
                </div>

                <div className="space-y-2 col-span-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase px-1">Priority (Layer Order)</label>
                  <input
                    type="number"
                    value={mod.priority || 0}
                    onChange={(e) => handleUpdate(index, { priority: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-surface-50 border border-border rounded-xl focus:ring-4 focus:ring-primary/5 focus:border-primary outline-none text-sm font-mono transition-all"
                  />
                </div>
              </div>
            )}
          </div>
        ))}

        {!isReadOnly && (
          <button
            type="button"
            onClick={handleAdd}
            className="w-full py-4 rounded-2xl border-2 border-dashed border-border-muted/50 hover:border-primary/50 hover:bg-primary/5 hover:text-primary transition-all text-sm font-black uppercase flex items-center justify-center gap-2 group tracking-widest"
          >
            <Plus className="h-4 w-4 group-hover:scale-125 transition-transform" />
            Add Mechanical Effect
          </button>
        )}
      </div>
    </div>
  );
};
