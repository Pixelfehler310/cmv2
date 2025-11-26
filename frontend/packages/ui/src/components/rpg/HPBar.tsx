import * as React from "react";
import { cn } from "../../lib/utils";

export interface HPBarProps {
  current: number;
  max: number;
  temp?: number;
  className?: string;
  showNumbers?: boolean;
}

export function HPBar({ 
  current, 
  max, 
  temp = 0, 
  className,
  showNumbers = true 
}: HPBarProps) {
  const percentage = Math.max(0, Math.min(100, (current / max) * 100));
  const tempPercentage = temp > 0 ? (temp / max) * 100 : 0;
  const totalPercentage = Math.min(100, percentage + tempPercentage);

  const getColorClass = () => {
    if (percentage > 75) return "bg-green-500";
    if (percentage > 50) return "bg-yellow-500";
    if (percentage > 25) return "bg-orange-500";
    return "bg-red-500";
  };

  return (
    <div className={cn("w-full", className)}>
      {showNumbers && (
        <div className="flex justify-between text-sm mb-1">
          <span>
            {current} / {max}
            {temp > 0 && <span className="text-blue-500"> (+{temp} temp)</span>}
          </span>
          <span className="text-muted-foreground">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div className="w-full h-4 bg-muted rounded-full overflow-hidden relative">
        {/* Main HP bar */}
        <div
          className={cn("h-full transition-all duration-300", getColorClass())}
          style={{ width: `${percentage}%` }}
        />
        {/* Temporary HP bar */}
        {temp > 0 && (
          <div
            className="absolute top-0 h-full bg-blue-400 opacity-70 transition-all duration-300"
            style={{ 
              left: `${percentage}%`,
              width: `${tempPercentage}%` 
            }}
          />
        )}
      </div>
    </div>
  );
}

