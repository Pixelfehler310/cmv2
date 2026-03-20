import React, { useState } from "react";
import {
  cellKeyFromCoordinates,
  parseCellKey,
  resolveCombatClick,
  selectAttackAffectedCellSetForActorAction,
  selectAttackEligibleCellSetForActorAction,
  selectAttackEligibleTargetSetForActorAction,
  useCombatStore,
} from "@rpg/shared";

interface MapBoardProps {
  selectedCombatantId: string | null;
  onSelectCombatant: (id: string | null) => void;
}

export const MapBoard: React.FC<MapBoardProps> = ({ selectedCombatantId, onSelectCombatant }) => {
  const gameState = useCombatStore((state) => state.gameState);
  const moveToken = useCombatStore((state) => state.moveToken);
  const actingAsUserId = useCombatStore((state) => state.actingAsUserId);
  const requestAttackPreview = useCombatStore((state) => state.requestAttackPreview);
  const setSelectedTargetId = useCombatStore((state) => state.setSelectedTargetId);
  const setSelectedTemplateCell = useCombatStore((state) => state.setSelectedTemplateCell);

  const interactionMode = useCombatStore((state) => state.interactionMode);
  const interactionActorId = useCombatStore((state) => state.interactionActorId);
  const interactionActionId = useCombatStore((state) => state.interactionActionId);
  const selectedTargetId = useCombatStore((state) => state.selectedTargetId);
  const selectedTemplateCell = useCombatStore((state) => state.selectedTemplateCell);

  const eligibleTargetSet = useCombatStore((state) => selectAttackEligibleTargetSetForActorAction(state, interactionActorId, interactionActionId));
  const eligibleCellSet = useCombatStore((state) => selectAttackEligibleCellSetForActorAction(state, interactionActorId, interactionActionId));
  const affectedCellSet = useCombatStore((state) => selectAttackAffectedCellSetForActorAction(state, interactionActorId, interactionActionId));

  const [draggedTokenId, setDraggedTokenId] = useState<string | null>(null);
  const GRID_SIZE = 50;

  if (!gameState) {
    return <div className="h-full w-full p-4 text-sm text-on-muted">Waiting for map data...</div>;
  }

  const handleDragStart = (e: React.DragEvent, tokenId: string) => {
    if (interactionMode !== "idle") {
      e.preventDefault();
      return;
    }

    setDraggedTokenId(tokenId);
    e.dataTransfer.setData("text/plain", tokenId);
  };

  const handleDrop = (e: React.DragEvent) => {
    if (interactionMode !== "idle") {
      return;
    }

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

  const clickToCellKey = (clientX: number, clientY: number, container: HTMLDivElement): string => {
    const rect = container.getBoundingClientRect();
    const x = Math.max(0, Math.floor((clientX - rect.left) / GRID_SIZE));
    const y = Math.max(0, Math.floor((clientY - rect.top) / GRID_SIZE));
    return cellKeyFromCoordinates(x, y);
  };

  const hasTargetingContract = Boolean(interactionActorId && interactionActionId);

  const handleResolvedClick = (tokenId: string | null, cellKey: string | null): boolean => {
    const resolution = resolveCombatClick({
      mode: interactionMode,
      tokenId,
      cellKey,
      hasContract: hasTargetingContract,
      eligibleTargetSet,
      eligibleCellSet,
    });

    if (resolution.kind === "pass_to_selection") {
      return false;
    }

    if (resolution.kind === "select_target") {
      setSelectedTargetId(resolution.targetId);
      return true;
    }

    if (resolution.kind === "select_cell") {
      setSelectedTemplateCell(resolution.cellKey);
      if (interactionActorId && interactionActionId) {
        const parsed = parseCellKey(resolution.cellKey);
        if (parsed) {
          requestAttackPreview(interactionActorId, interactionActionId, parsed);
        }
      }
      return true;
    }

    return true;
  };

  const showEntityTargeting = interactionMode === "target_pick_entity";
  const showCellTargeting = interactionMode === "target_pick_cell" || interactionMode === "target_pick_direction" || interactionMode === "confirm";

  const eligibleCellOverlays = showCellTargeting ? Array.from(eligibleCellSet.values()) : [];
  const affectedCellOverlays = showCellTargeting ? Array.from(affectedCellSet.values()) : [];

  return (
    <div
      className="relative h-full w-full overflow-hidden rounded-xl border border-(--border-default) bg-surface-2"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onClick={(event) => {
        const currentTarget = event.currentTarget;
        const clickedCellKey = clickToCellKey(event.clientX, event.clientY, currentTarget);
        const consumed = handleResolvedClick(null, clickedCellKey);
        if (!consumed) {
          onSelectCombatant(null);
        }
      }}
    >
      {/* Grid Background */}
      <div
        className="absolute inset-0 opacity-60"
        style={{
          backgroundImage: "linear-gradient(var(--border-subtle) 1px, transparent 1px), linear-gradient(90deg, var(--border-subtle) 1px, transparent 1px)",
          backgroundSize: `${GRID_SIZE}px ${GRID_SIZE}px`,
        }}
      />

      {eligibleCellOverlays.map((cellKey) => {
        const cell = parseCellKey(cellKey);
        if (!cell) {
          return null;
        }

        const isSelected = selectedTemplateCell === cellKey;
        return (
          <div
            key={`eligible-${cellKey}`}
            className={`pointer-events-none absolute border ${isSelected ? "border-cyan-300 bg-cyan-500/35" : "border-cyan-700 bg-cyan-500/20"}`}
            style={{
              left: `${cell.x * GRID_SIZE}px`,
              top: `${cell.y * GRID_SIZE}px`,
              width: `${GRID_SIZE}px`,
              height: `${GRID_SIZE}px`,
            }}
          />
        );
      })}

      {affectedCellOverlays.map((cellKey) => {
        const cell = parseCellKey(cellKey);
        if (!cell) {
          return null;
        }

        return (
          <div
            key={`affected-${cellKey}`}
            className="pointer-events-none absolute border border-amber-700 bg-amber-500/15"
            style={{
              left: `${cell.x * GRID_SIZE}px`,
              top: `${cell.y * GRID_SIZE}px`,
              width: `${GRID_SIZE}px`,
              height: `${GRID_SIZE}px`,
            }}
          />
        );
      })}

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
            const tokenCellKey = cellKeyFromCoordinates(token.x, token.y);
            const consumed = handleResolvedClick(token.id, tokenCellKey);
            if (!consumed) {
              onSelectCombatant(token.id);
            }
          }}
          className={[
            "absolute z-5 flex h-10 w-10 select-none items-center justify-center rounded-full border-2",
            interactionMode === "idle" ? "cursor-grab" : "cursor-pointer",
            "bg-surface-1 text-sm font-semibold text-on-surface",
            showEntityTargeting && eligibleTargetSet.has(token.id) ? "ring-2 ring-cyan-500" : "",
            selectedTargetId === token.id ? "border-cyan-300" : selectedCombatantId === token.id ? "border-(--color-primary)" : "border-(--border-default)",
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
