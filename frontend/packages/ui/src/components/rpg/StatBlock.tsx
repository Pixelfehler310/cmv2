import { cn } from "../../lib/utils";

interface StatBlockProps {
  label: string;
  value: number;
  modifier?: number;
  className?: string;
  onClick?: () => void;
}

export function StatBlock({ label, value, modifier, className, onClick }: StatBlockProps) {
  const calculatedModifier = modifier !== undefined ? modifier : Math.floor((value - 10) / 2);

  const modifierDisplay = calculatedModifier >= 0 ? `+${calculatedModifier}` : `${calculatedModifier}`;

  return (
    <div className={cn("flex flex-col items-center p-2 rounded border bg-card", onClick && "cursor-pointer hover:bg-accent transition-colors", className)} onClick={onClick}>
      <div className="text-xs text-muted-foreground uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
      <div className={cn("text-sm font-semibold", calculatedModifier >= 0 ? "text-green-600" : "text-red-600")}>{modifierDisplay}</div>
    </div>
  );
}


