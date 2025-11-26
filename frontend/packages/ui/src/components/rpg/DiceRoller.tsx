import * as React from "react";
import { Button } from "../button";
import { cn } from "../../lib/utils";

export interface DiceRollerProps {
  onRoll?: (expression: string, result: DiceRollResult) => void;
  className?: string;
}

export interface DiceRollResult {
  expression: string;
  rolls: number[];
  modifier: number;
  total: number;
  breakdown: string;
}

const DICE_TYPES = [
  { label: "d4", value: "d4" },
  { label: "d6", value: "d6" },
  { label: "d8", value: "d8" },
  { label: "d10", value: "d10" },
  { label: "d12", value: "d12" },
  { label: "d20", value: "d20" },
  { label: "d100", value: "d100" },
];

// Parse dice expression like "2d6+3" or "1d20"
function parseDiceExpression(expression: string): { count: number; sides: number; modifier: number } | null {
  const trimmed = expression.trim();
  const match = trimmed.match(/^(\d*)d(\d+)([+-]\d+)?$/i);
  
  if (!match) return null;
  
  const count = match[1] ? parseInt(match[1]) : 1;
  const sides = parseInt(match[2]);
  const modifier = match[3] ? parseInt(match[3]) : 0;
  
  return { count, sides, modifier };
}

// Roll dice based on expression
function rollDice(expression: string): DiceRollResult | null {
  const parsed = parseDiceExpression(expression);
  if (!parsed) return null;

  const { count, sides, modifier } = parsed;
  const rolls: number[] = [];
  
  for (let i = 0; i < count; i++) {
    rolls.push(Math.floor(Math.random() * sides) + 1);
  }
  
  const sum = rolls.reduce((a, b) => a + b, 0);
  const total = sum + modifier;
  
  const breakdown = rolls.length > 1
    ? `${rolls.join(' + ')}${modifier !== 0 ? ` ${modifier >= 0 ? '+' : ''}${modifier}` : ''} = ${total}`
    : `${rolls[0]}${modifier !== 0 ? ` ${modifier >= 0 ? '+' : ''}${modifier}` : ''} = ${total}`;

  return {
    expression,
    rolls,
    modifier,
    total,
    breakdown,
  };
}

export function DiceRoller({ onRoll, className }: DiceRollerProps) {
  const [expression, setExpression] = React.useState("");

  const handleDiceClick = (dice: string) => {
    const newExpression = expression ? `${expression} + ${dice}` : dice;
    setExpression(newExpression);
  };

  const handleRoll = () => {
    if (!expression) return;
    
    const result = rollDice(expression);
    if (result && onRoll) {
      onRoll(expression, result);
      setExpression("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRoll();
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-wrap gap-2">
        {DICE_TYPES.map((dice) => (
          <Button
            key={dice.value}
            variant="outline"
            size="sm"
            onClick={() => handleDiceClick(dice.value)}
          >
            {dice.label}
          </Button>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={expression}
          onChange={(e) => setExpression(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="e.g., 2d6+3 or 1d20"
          className="flex-1 px-3 py-2 border rounded-md bg-background text-sm"
        />
        <Button onClick={handleRoll} disabled={!expression}>
          Roll
        </Button>
      </div>
    </div>
  );
}
