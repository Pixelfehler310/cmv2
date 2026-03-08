import React, { useCallback, useMemo } from "react";
import { ReactFlow, Controls, Background, MiniMap, Panel, useReactFlow, ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useStoryGraphStore, StoryNode } from "../../store/StoryGraphStore";
import { SceneNode } from "./nodes/SceneNode";
import { EncounterNode } from "./nodes/EncounterNode";
import { NoteNode } from "./nodes/NoteNode";
import { InspectorPanel } from "./inspector/InspectorPanel";

const nodeTypes = {
  sceneNode: SceneNode,
  encounterNode: EncounterNode,
  noteNode: NoteNode,
};

const StoryGraphCanvas = () => {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, setSelectedNodeId, addNode } = useStoryGraphStore();
  const { screenToFlowPosition } = useReactFlow();

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: StoryNode) => {
      setSelectedNodeId(node.id);
    },
    [setSelectedNodeId],
  );

  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, [setSelectedNodeId]);

  const handleAddNode = useCallback(
    (type: string) => {
      const position = screenToFlowPosition({
        x: window.innerWidth / 2,
        y: window.innerHeight / 2,
      });

      const newNode: StoryNode = {
        id: `node_${Date.now()}`,
        type,
        position: { x: position.x + (Math.random() * 50 - 25), y: position.y + (Math.random() * 50 - 25) },
        data: { label: `New ${type.replace("Node", "")}` },
      };

      if (type === "encounterNode") {
        newNode.data.difficultyBadge = "Easy";
      }

      addNode(newNode);
    },
    [screenToFlowPosition, addNode],
  );

  return (
    <div style={{ position: "relative", width: "100%", height: "100vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        selectNodesOnDrag={false}
      >
        <Background />
        <Controls />
        <MiniMap />
        <Panel position="top-left" style={{ background: "white", padding: "8px", borderRadius: "8px", boxShadow: "0 2px 4px rgba(0,0,0,0.1)", display: "flex", gap: "8px" }}>
          <button onClick={() => handleAddNode("sceneNode")} style={buttonStyle}>
            + Scene
          </button>
          <button onClick={() => handleAddNode("encounterNode")} style={buttonStyle}>
            + Encounter
          </button>
          <button onClick={() => handleAddNode("noteNode")} style={buttonStyle}>
            + Note
          </button>
        </Panel>
      </ReactFlow>
      <InspectorPanel />
    </div>
  );
};

const buttonStyle = {
  padding: "6px 12px",
  background: "#f1f2f6",
  border: "1px solid #dfe4ea",
  borderRadius: "4px",
  cursor: "pointer",
  fontWeight: "bold" as const,
  color: "#2f3542",
};

export const StoryGraph = () => {
  return (
    <ReactFlowProvider>
      <StoryGraphCanvas />
    </ReactFlowProvider>
  );
};
