import React from "react";
import { useSelectionStore, useGameStateStore, GameStateStore } from "@rpg/shared";
import { IHostBridge } from "@rpg/bridge";

interface ActionDeckProps {
  bridge?: IHostBridge;
}

export const ActionDeck = ({ bridge }: ActionDeckProps) => {
  const { selectedTokenId, setSelectedTokenId } = useSelectionStore();
  const gameState = useGameStateStore((s: GameStateStore) => s.state);

  const handleAction = (actionType: string) => {
    if (!bridge || !selectedTokenId) return;

    // Send a generic action payload
    bridge.actions
      .dispatch("ACTION", {
        actor_id: selectedTokenId,
        action_type: actionType,
        target_id: "dummy_target", // Hardcoded for walking skeleton
        payload: { amount: 5 },
      })
      .catch((err) => {
        console.error("Failed to dispatch action:", err);
      });
  };

  return (
    <div className="p-4 bg-gray-800 border border-red-900 rounded-md m-4">
      <h3 className="text-xl font-bold mb-4 text-red-500 uppercase tracking-wider">Ugly DM Podium</h3>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Manually Select Token ID:</label>
        <input
          type="text"
          value={selectedTokenId || ""}
          onChange={(e) => setSelectedTokenId(e.target.value)}
          placeholder="e.g. char_123"
          className="w-full bg-black border border-gray-600 rounded px-3 py-2 text-white"
        />
        {selectedTokenId && <p className="text-xs text-gray-400 mt-1">Currently Selected: {selectedTokenId}</p>}
      </div>

      {selectedTokenId && (
        <div className="grid grid-cols-2 gap-2 mt-4">
          <button onClick={() => handleAction("ATTACK")} className="bg-red-700 hover:bg-red-600 text-white font-bold py-2 px-4 rounded">
            ATTACK (5 DMG)
          </button>
          <button onClick={() => handleAction("HEAL")} className="bg-green-700 hover:bg-green-600 text-white font-bold py-2 px-4 rounded">
            HEAL (5 HP)
          </button>
        </div>
      )}
    </div>
  );
};
