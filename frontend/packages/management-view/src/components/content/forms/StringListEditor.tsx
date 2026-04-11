import React, { useState, KeyboardEvent } from "react";
import { Plus, X, GripVertical, AlertCircle } from "lucide-react";
import { cn } from "@rpg/ui";

/**
 * Shared String List Editor for proficiencies, languages, etc.
 * Supports add/remove/edit and keyboard-first entry workflow.
 */

interface StringListEditorProps {
  label?: string;
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
  emptyMessage?: string;
  isReadOnly?: boolean;
  className?: string;
  error?: string;
}

export const StringListEditor: React.FC<StringListEditorProps> = ({
  label,
  items,
  onChange,
  placeholder = "Add an item...",
  emptyMessage = "No items added yet.",
  isReadOnly = false,
  className,
  error,
}) => {
  const [inputValue, setInputValue] = useState("");

  const handleAddItem = () => {
    const trimmedValue = inputValue.trim();
    if (trimmedValue && !items.includes(trimmedValue)) {
      onChange([...items, trimmedValue]);
      setInputValue("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddItem();
    }
  };

  const handleRemoveItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index);
    onChange(newItems);
  };

  return (
    <div className={cn("space-y-3", className)}>
      {label && (
        <div className="flex items-center justify-between gap-4 px-1">
          <label className="text-xs font-black uppercase tracking-widest text-muted-foreground/80">{label}</label>
          <span className="text-[10px] font-bold text-muted-foreground/40 bg-surface-100 px-1.5 py-0.5 rounded border border-border">{items.length} total</span>
        </div>
      )}

      {/* List Area */}
      <div className="space-y-1">
        {items.length > 0 ? (
          items.map((item, index) => (
            <div
              key={`${item}-${index}`}
              className={cn(
                "group relative flex items-center gap-3 px-3 py-2 rounded-xl border border-border-muted bg-surface-50 hover:bg-surface-100 transition-all text-sm",
                isReadOnly ? "" : "hover:border-border",
              )}
            >
              {!isReadOnly && <GripVertical className="h-4 w-4 text-muted-foreground/30 group-hover:text-muted-foreground/60 shrink-0 cursor-grab active:cursor-grabbing" />}
              <span className="flex-1 font-medium">{item}</span>
              {!isReadOnly && (
                <button
                  type="button"
                  onClick={() => handleRemoveItem(index)}
                  className="p-1 text-muted-foreground/0 group-hover:text-muted-foreground/60 hover:text-destructive hover:bg-destructive/10 rounded-md transition-all"
                  aria-label={`Remove ${item}`}
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          ))
        ) : (
          <div className="px-3 py-6 rounded-xl border-2 border-dashed border-border-muted/50 text-center text-sm text-muted-foreground/60 italic font-medium">{emptyMessage}</div>
        )}
      </div>

      {/* Input Area */}
      {!isReadOnly && (
        <div className="relative group">
          <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
            <Plus className="h-4 w-4 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
          </div>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={cn(
              "w-full pl-10 pr-24 py-2.5 rounded-xl border border-border bg-surface-50 focus:bg-surface-100 focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all text-sm placeholder:opacity-50",
              error ? "border-destructive ring-destructive/10" : "border-border",
            )}
          />
          <div className="absolute inset-y-1 right-1 flex items-center">
            <button
              type="button"
              onClick={handleAddItem}
              disabled={!inputValue.trim() || items.includes(inputValue.trim())}
              className={cn(
                "h-full px-4 rounded-lg font-bold text-xs uppercase tracking-widest transition-all",
                inputValue.trim() && !items.includes(inputValue.trim())
                  ? "bg-primary text-white shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98]"
                  : "bg-muted text-muted-foreground/50 cursor-not-allowed",
              )}
            >
              Add
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 px-1 text-xs font-bold text-destructive animate-head-shake">
          <AlertCircle className="h-3.5 w-3.5" />
          {error}
        </div>
      )}
    </div>
  );
};
