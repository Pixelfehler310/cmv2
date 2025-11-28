
export const PartyPanel = () => {
  return (
    <div className="h-full p-4 bg-white/90 overflow-y-auto">
      <h2 className="font-bold mb-4">Party</h2>
      <div className="space-y-2">
        {['Legolas', 'Gimli', 'Gandalf'].map(name => (
          <div key={name} className="flex items-center justify-between p-2 bg-slate-100 rounded">
            <span>{name}</span>
            <span className="text-xs font-mono bg-green-100 text-green-800 px-1 rounded">Healthy</span>
          </div>
        ))}
      </div>
    </div>
  );
};
