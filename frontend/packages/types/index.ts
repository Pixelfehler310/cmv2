// This file will be auto-generated from Pydantic models in the future.
// For now, it serves as a placeholder.

export interface EffectConfig {
  trigger: string;
  action: string;
  value: any;
  target?: string;
}

export interface GameEntity {
  id: string;
  name: string;
  description: string;
  effects: EffectConfig[];
}
