import React, { useState } from "react";
import { useCombatStore } from "@rpg/shared";

interface MapBoardProps {
  selectedCombatantId: string | null;
  onSelectCombatant: (id: string | null) => void;
}

export const MapBoard: React.FC<MapBoardProps> = ({ selectedCombatantId, onSelectCombatant }) => {
  const { gameState, moveToken, actingAsUserId } = useCombatStore();
  const [draggedTokenId, setDraggedTokenId] = useState<string | null>(null);
  const GRID_SIZE = 50;

  if (!gameState) {
    return <div className="h-full w-full p-4 text-sm text-on-muted">Waiting for map data...</div>;
  }

  const handleDragStart = (e: React.DragEvent, tokenId: string) => {
    setDraggedTokenId(tokenId);
    e.dataTransfer.setData("text/plain", tokenId);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedTokenId) return;

    // Snap drops to grid coordinates for deterministic server payloads.
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.max(0, Math.floor((e.clientX - rect.left) / GRID_SIZE));
    const y = Math.max(0, Math.floor((e.clientY - rect.top) / GRID_SIZE));

    // The store applies optimistic position and reconciles against server updates.
    moveToken(draggedTokenId, [[x, y]]);
    setDraggedTokenId(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div
      className="relative h-full w-full overflow-hidden rounded-xl border border-(--border-default) bg-surface-2"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onClick={() => onSelectCombatant(null)}
    >
      {/* Grid Background */}
      <div
        className="absolute inset-0 opacity-60"
        style={{
          backgroundImage: "linear-gradient(var(--border-subtle) 1px, transparent 1px), linear-gradient(90deg, var(--border-subtle) 1px, transparent 1px)",
          backgroundSize: `${GRID_SIZE}px ${GRID_SIZE}px`,
        }}
      />

      {/* Fog Reveal Tools Header */}
      <div className="absolute left-3 top-3 z-10 flex gap-2 rounded-xl border border-(--border-subtle) bg-surface-1/90 p-2 shadow-sm backdrop-blur-sm">
        <button className="btn btn-ghost btn-sm px-3! py-1! text-xs">Reveal Fog</button>
        <button className="btn btn-ghost btn-sm px-3! py-1! text-xs">Hide Fog</button>
        <button className="btn btn-ghost btn-sm px-3! py-1! text-xs">Measure</button>
      </div>

      <div className="absolute right-3 top-3 z-10 rounded-md border border-(--border-subtle) bg-surface-1/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-on-muted shadow-sm backdrop-blur-sm">
        {actingAsUserId ? `Play as ${actingAsUserId}` : "Play as DM"}
      </div>

      {/* Tokens */}
      {gameState.combatants.map((token: any) => (
        <div
          key={token.id}
          draggable
          onDragStart={(e) => handleDragStart(e, token.id)}
          onClick={(e) => {
            e.stopPropagation();
            onSelectCombatant(token.id);
          }}
          className={[
            "absolute z-5 flex h-10 w-10 select-none items-center justify-center rounded-full border-2",
            "cursor-grab bg-surface-1 text-sm font-semibold text-on-surface",
            selectedCombatantId === token.id ? "border-(--color-primary)" : "border-(--border-default)",
          ].join(" ")}
          style={{
            left: `${token.x * GRID_SIZE}px`,
            top: `${token.y * GRID_SIZE}px`,
            transition: "left 0.2s, top 0.2s",
          }}
        >
          {token.public_name[0]}
        </div>
      ))}
    </div>
  );
};
