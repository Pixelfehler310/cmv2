export const PartyPanel = () => {
  return (
    <div className="h-full p-4 bg-card text-card-foreground overflow-y-auto">
      <h2 className="font-bold mb-4 text-foreground">Party</h2>
      <div className="space-y-2">
        {["Legolas", "Gimli", "Gandalf"].map((name) => (
          <div key={name} className="flex items-center justify-between p-2 bg-secondary rounded-lg">
            <span>{name}</span>
            <span className="text-xs font-mono bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">Healthy</span>
          </div>
        ))}
      </div>
    </div>
  );
};
