
export const CombatPanel = () => {
  return (
    <div className="h-full p-4 bg-white/90 overflow-y-auto">
      <h2 className="font-bold mb-4">Combat Log</h2>
      <div className="space-y-2 text-sm">
        <div className="p-2 bg-red-50 border border-red-100 rounded">
          <div className="font-bold text-red-800">Attack Roll</div>
          <div>Result: 18 (Hit)</div>
          <div>Damage: 8 Slashing</div>
        </div>
      </div>
    </div>
  );
};
