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
export declare function DiceRoller({ onRoll, className }: DiceRollerProps): import("react/jsx-runtime").JSX.Element;
//# sourceMappingURL=DiceRoller.d.ts.map