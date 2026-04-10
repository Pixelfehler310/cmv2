# Feature: Spatial Map System (VTT Core)

Status: Backlog
Category: Interaction / VTT
Parent Module: 07_assets, 04_campaigns

## Mission

Implement the spatial and visual representation of the game world, allowing for tactical token placement, grid management, and scene orchestration.

## Core Requirements

1. **Grid Management:** Support for Square and Hexagonal grids with configurable scale (ft/m).
2. **Token Orchestration:** Position, rotate, and scale character and monster tokens on the active scene.
3. **Layered Assets:** Support for background maps, tiles, and weather/effect overlays.
4. **Fog of War:** Basic visibility management for players (DM-controlled or automated LOS).
5. **Scene State Synchronization:** Real-time movement and state updates via Module 08 (Events).

## Backend Integration

- **Module 07 (Assets):** Storage and retrieval of map images and token sprites.
- **Module 04 (Campaigns):** Persisting the "Active Scene" state and token positions.
- **Module 11 (Transport):** WebSocket delivery of spatial updates.

## Frontend Components

- **Canvas/WebGL Renderer:** High-performance rendering of maps and tokens.
- **Interaction Layer:** Drag-and-drop movement, measurement tools, and pinging.
- **Scene Switcher:** DM interface for managing multiple tactical environments.

## Done Criteria

- [ ] Users can upload a map and configure a grid.
- [ ] Drag-and-drop tokens onto the map.
- [ ] Position updates synchronized across all connected players.
- [ ] Basic measurement tool for tactical distance.

## Traceability

- Legacy Feature 7 (Spatial Map System)
- Module Specification 07 (Assets)
- Module Specification 04 (Campaigns)
