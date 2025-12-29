export const CombatPanel = () => {
  return (
    <div className="h-full p-4 bg-card text-card-foreground overflow-y-auto">
      <h2 className="font-bold mb-4 text-foreground">Combat Log</h2>
      <div className="space-y-2 text-sm">
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
          <div className="font-bold text-red-400">Attack Roll</div>
          <div className="text-muted-foreground">Result: 18 (Hit)</div>
          <div className="text-muted-foreground">Damage: 8 Slashing</div>
        </div>
      </div>
    </div>
  );
};
