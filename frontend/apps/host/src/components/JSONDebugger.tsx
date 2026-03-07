import { useGameStateStore, GameStateStore } from "@rpg/shared";

export const JSONDebugger = () => {
  const state = useGameStateStore((s: GameStateStore) => s.state);

  return (
    <div className="p-4 bg-gray-900 border border-gray-700 rounded-md overflow-auto font-mono text-xs text-green-400 m-4 max-h-[80vh]">
      <div className="text-gray-400 mb-2 font-bold uppercase tracking-wider">Raw VTT State</div>
      {state ? <pre>{JSON.stringify(state, null, 2)}</pre> : <div className="text-gray-500 italic">Waiting for state hydration...</div>}
    </div>
  );
};
