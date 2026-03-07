# Management View: StoryGraph Editor

## 1. Overview

The StoryGraph is the signature feature of the Management View, transforming a linear campaign notebook into an interactive visual flowchart. Built on `reactflow`, it allows DMs to structure their narrative beats, scenes, and encounters as interconnected nodes.

## 2. Core Concepts / Layout

The view consists of a 100% width/height infinite canvas with a floating toolbar and a context-sensitive side-inspector.

### Infinite Canvas

DMs can pan and zoom across a large node graph. The graph is non-linear, allowing branching paths (e.g., "If players go left -> Encounter A; If right -> Village B").

### Node Types

- **Scene Node**: Represents a specific map. Clicking it sets the active background for an encounter.
- **Encounter Node**: Represents a combat beat. Connects to the `EncounterBuilder` where monsters are assigned.
- **Note Node**: A rich-text node for narrative descriptions, dialogue, or DC checks.

### Side Inspector

Whenever a node is clicked, a sidebar slides out from the right containing the detailed editor for that specific node type (e.g., swapping music for a scene, editing the monster list for an encounter).

## 3. Key Components / State

- **`ReactFlowInstance`**: The core graph rendering engine.
- **`StoryGraphStore` (Zustand)**: Manages the local state of `nodes` and `edges`, syncing with the backend on save or debounced auto-save.
- **Custom Nodes**: React components registered to the Flow instance, such as `SceneNode.tsx` which includes visual flair like imagery and difficulty badges.
- **`EncounterBuilder`**: A complex component housed in the Inspector that calculates total XP and Difficulty (Easy/Hard/Deadly) based on the assigned party level and chosen monsters.

## 4. Example Node Data Structure

Nodes must track their visual position and their linked database entity.

```json
{
  "id": "node_123",
  "type": "encounterNode",
  "position": { "x": 250, "y": 100 },
  "data": {
    "label": "Goblin Ambush",
    "encounterId": "enc_abc890",
    "difficultyBadge": "Hard"
  }
}
```

## 5. Dependencies

- `reactflow` (Core graph renderer)
- `@civic/design-system` (Toolbar, Inspector styling)
- Shared API types (to validate node data shapes when linking to actual encounters).
