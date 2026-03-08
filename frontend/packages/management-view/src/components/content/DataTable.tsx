import React from "react";
import { cn } from "@rpg/ui";

export interface Column<T> {
  key: Extract<keyof T, string>;
  label: string;
  render?: (item: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (item: T) => void;
}

export function DataTable<T extends { id: string | number }>({ columns, data, onRowClick }: DataTableProps<T>) {
  return (
    <div className="w-full h-full overflow-auto bg-surface-100 rounded-xl">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-surface-50 sticky top-0 z-10 border-b border-border shadow-sm">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className="px-6 py-4 font-bold text-muted-foreground uppercase tracking-wider">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {data.map((row) => (
            <tr key={row.id} onClick={() => onRowClick?.(row)} className={cn("group transition-colors", onRowClick ? "cursor-pointer hover:bg-surface-200" : "")}>
              {columns.map((col) => (
                <td key={`${row.id}-${col.key}`} className="px-6 py-4 text-foreground group-hover:text-primary transition-colors">
                  {col.render ? col.render(row) : (row[col.key] as any)}
                </td>
              ))}
            </tr>
          ))}
          {data.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-6 py-12 text-center text-muted-foreground italic bg-surface-50/50">
                No records found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
