import { useMemo } from "react";

// Types we expect in the raw state
export interface RawTokenState {
  id: string;
  name?: string;
  public_name?: string;
  hp_current?: number;
  hp_max?: number;
  hp_percent?: number;
  x?: number;
  y?: number;
  hidden?: boolean;
  [key: string]: any;
}

export interface RawLogEvent {
  id: string;
  message: string;
  visibility?: "PUBLIC" | "DM_ONLY" | "PRIVATE";
  timestamp: string;
}

export interface StageState {
  tokens: any[];
  logs: any[];
  [key: string]: any;
}

export function useStageFilter(rawState: any): StageState {
  return useMemo(() => {
    if (!rawState) return { tokens: [], logs: [] };

    // 1. Filter and map tokens (support both old flat tokens list and new combatants list)
    const rawTokens = rawState.tokens || rawState.combatants || [];
    const mapTokens = rawState.map?.tokens || [];

    const sanitizedTokens = rawTokens
      .filter((t: any) => !t.hidden)
      .map((t: any) => {
        let healthStatus = "Healthy";
        
        // Handle both old mock field names and new Dnd5e engine field names
        const hpCurrent = t.hp_current !== undefined ? t.hp_current : t.current_hp;
        const hpMax = t.hp_max !== undefined ? t.hp_max : t.max_hp;
        
        const percent = t.hp_percent !== undefined 
          ? t.hp_percent 
          : (hpMax && hpCurrent !== undefined ? hpCurrent / hpMax : 1);

        if (percent <= 0) healthStatus = "Dead";
        else if (percent <= 0.25) healthStatus = "Critical";
        else if (percent <= 0.5) healthStatus = "Bloodied";

        let color = "border-green-500";
        if (healthStatus === "Bloodied") color = "border-yellow-500";
        if (healthStatus === "Critical") color = "border-red-500";
        if (healthStatus === "Dead") color = "border-gray-900";

        // Extract position from map.tokens if available, fallback to actor.position, then actor.x/y
        const mapToken = mapTokens.find((mt: any) => mt.actor_id === t.id);
        const posX = mapToken?.position?.x ?? t.position?.x ?? t.x ?? 0;
        const posY = mapToken?.position?.y ?? t.position?.y ?? t.y ?? 0;

        // Create sanitized token
        const sanitized = {
          ...t,
          name: t.public_name || t.name || "Unknown Entity",
          healthStatus,
          healthRingColor: color,
          x: posX,
          y: posY
        };

        // Remove exact HP metrics to prevent leaking them to players
        delete sanitized.hp_current;
        delete sanitized.hp_max;
        delete sanitized.hp_percent;
        delete sanitized.current_hp;
        delete sanitized.max_hp;
        delete sanitized.temp_hp;

        return sanitized;
      });

    // 2. Filter logs
    const rawLogs = rawState.logs || [];
    const publicLogs = rawLogs.filter((log: RawLogEvent) => log.visibility === "PUBLIC" || !log.visibility);

    return {
      ...rawState,
      tokens: sanitizedTokens,
      logs: publicLogs,
    };
  }, [rawState]);
}
