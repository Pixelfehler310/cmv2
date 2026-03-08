import { create } from "zustand";
import { Connection, Edge, EdgeChange, Node, NodeChange, addEdge, OnNodesChange, OnEdgesChange, OnConnect, applyNodeChanges, applyEdgeChanges } from "@xyflow/react";

export type StoryNodeData = {
  label: string;
  encounterId?: string;
  difficultyBadge?: "Easy" | "Medium" | "Hard" | "Deadly";
  sceneId?: string;
  noteContent?: string;
  [key: string]: unknown;
};

export type StoryNode = Node<StoryNodeData>;

interface StoryGraphState {
  nodes: StoryNode[];
  edges: Edge[];
  selectedNodeId: string | null;
  onNodesChange: OnNodesChange<StoryNode>;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  setNodes: (nodes: StoryNode[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (node: StoryNode) => void;
  setSelectedNodeId: (id: string | null) => void;
}

const initialNodes: StoryNode[] = [
  {
    id: "1",
    type: "sceneNode",
    position: { x: 250, y: 100 },
    data: { label: "Tavern Start", sceneId: "scene_1" },
  },
  {
    id: "2",
    type: "encounterNode",
    position: { x: 250, y: 300 },
    data: { label: "Goblin Ambush", encounterId: "enc_1", difficultyBadge: "Medium" },
  },
];

const initialEdges: Edge[] = [{ id: "e1-2", source: "1", target: "2" }];

export const useStoryGraphStore = create<StoryGraphState>((set, get) => ({
  nodes: initialNodes,
  edges: initialEdges,
  selectedNodeId: null,
  onNodesChange: (changes: NodeChange<StoryNode>[]) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },
  onEdgesChange: (changes: EdgeChange[]) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },
  onConnect: (connection: Connection) => {
    set({
      edges: addEdge(connection, get().edges),
    });
  },
  setNodes: (nodes: StoryNode[]) => set({ nodes }),
  setEdges: (edges: Edge[]) => set({ edges }),
  addNode: (node: StoryNode) => set({ nodes: [...get().nodes, node] }),
  setSelectedNodeId: (id: string | null) => set({ selectedNodeId: id }),
}));
