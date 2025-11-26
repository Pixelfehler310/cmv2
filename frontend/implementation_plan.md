# Frontend Implementation Plan

This document outlines the step-by-step plan to build the Open RPG Engine frontend, following the Microfrontends (MFE) architecture with pnpm workspaces.

## Phase 1: Foundation & The "Digital Filing Cabinet" (MVP)

Focus: Basic UI structure, data display, and CRUD operations for characters, campaigns, and SRD content.

### Milestone 1.1: Project Setup & Infrastructure

- [x] Initialize pnpm workspace structure
- [x] Setup App Shell (`apps/host`) with Vite + React
- [x] Setup FlexLayout for docking windows
- [x] Create shared packages (`@rpg/types`, `@rpg/ui`)
- [x] Configure TypeScript paths and workspace dependencies
- [x] Setup Tailwind CSS with shadcn/ui integration
- [x] Create development scripts for parallel MFE development
- [x] Setup Vitest and React Testing Library for testing

### Milestone 1.2: Shared Contracts & API Client

- [x] Define TypeScript interfaces in `@rpg/types` matching backend Pydantic models:
- [x] `Item`, `Spell`, `Monster` (from Milestone 1.2)
- [x] `Character`, `Campaign` (from Milestone 1.3)
- [x] Request/Response types for all endpoints
- [x] Create API client service in App Shell:
- [x] HTTP client with base URL configuration
- [x] Functions for Items API (`getItems`, `getItem`)
- [x] Functions for Spells API (`getSpells`, `getSpell`)
- [x] Functions for Monsters API (`getMonsters`, `getMonster`)
- [x] Functions for Characters API (`getCharacters`, `getCharacter`, `createCharacter`, `updateCharacter`, `deleteCharacter`)
- [x] Functions for Campaigns API (`getCampaigns`, `getCampaign`, `createCampaign`, `updateCampaign`, `deleteCampaign`)
- [x] Create error handling and loading state utilities
- [x] Create and run Tests for Milestone 1.2

### Milestone 1.3: App Shell - Core Infrastructure

- [x] Implement routing system (React Router or similar)
- [x] Create authentication context/provider (JWT token management)
- [x] Implement WebSocket connection manager (single connection in App Shell)
- [x] Create Client-Side Event Bus for MFE communication
- [x] Implement `dispatchAction(type, payload)` function for downward communication to MFEs
- [x] Create layout persistence (save/restore FlexLayout configuration)
- [x] Add header with user info and navigation
- [x] Create and run Tests for Milestone 1.3

### Milestone 1.4: Shared UI Components (`@rpg/ui`)

- [x] Install and configure shadcn/ui
- [x] Create base UI components:
- [x] Button, Input, Select, Textarea
- [x] Card, Dialog, Sheet
- [x] Table, Tabs
- [x] Badge, Avatar
- [x] Create RPG-specific components:
- [x] StatBlock (for displaying ability scores)
- [x] HPBar (health bar component)
- [x] DiceRoller (visual dice component, non-functional initially)
- [x] Create and run Tests for Milestone 1.4

### Milestone 1.5: MFE - Player Sheet (View)

- [x] Create `apps/player-sheet` MFE package
- [x] Implement character data fetching (using API client from App Shell)
- [x] Create character display tabs:
- [x] Stats Tab: Display ability scores, modifiers, proficiency bonus
- [x] Inventory Tab: Display equipped items and inventory list
- [x] Spells Tab: Display known/prepared spells
- [x] Features Tab: Display character features and traits
- [x] Implement character selection/loading UI
- [x] Add placeholder buttons for actions (not functional yet)
- [x] Integrate Player Sheet into App Shell layout
- [x] Create and run Tests for Milestone 1.5

### Milestone 1.6: MFE - DM Tools (View)

- [x] Create `apps/dm-tools` MFE package
- [x] Implement Monster Library panel:
- [x] List monsters from API
- [x] Search/filter functionality
- [x] Monster detail view
- [x] Implement Campaign Management:
- [x] Campaign list and selection
- [x] Campaign detail view
- [x] Character list within campaign
- [x] Implement Initiative Tracker (basic list, no turn logic yet):
- [x] Add/remove combatants
- [x] Display initiative order
- [x] Implement HP Editor (direct value editing for monsters/characters)
- [x] Add drag-and-drop placeholder for spawning monsters (visual only)
- [x] Integrate DM Tools into App Shell layout
- [x] Create and run Tests for Milestone 1.6

### Milestone 1.7: Data Display & CRUD Operations

- [x] Implement Item Browser (in DM Tools or separate panel):
- [x] List all items
- [x] Item detail view
- [x] Search functionality
- [x] Implement Spell Browser:
- [x] List all spells
- [x] Spell detail view
- [x] Filter by level, school, class
- [x] Implement Character Creation Form:
- [x] Basic info (name, race, class, level)
- [x] Ability score assignment
- [x] Save to backend
- [x] Implement Campaign Creation Form:
- [x] Basic info (name, description)
- [x] Add characters to campaign
- [x] Save to backend
- [x] Create and run Tests for Milestone 1.7

## Phase 2: The "Calculator" (Automation)

Focus: Interactive features, dice rolling, real-time updates, and basic game mechanics.

### Milestone 2.1: Real-Time Communication & State Management

- [x] Implement WebSocket message handling in App Shell
- [x] Create state management (Zustand stores) for:
- [x] Current campaign state
- [x] Active characters/monsters
- [x] Combat state (initiative, current turn)
- [x] Implement WebSocket event listeners in MFEs
- [x] Create event bus subscriptions for cross-MFE communication
- [x] Create and run Tests for Milestone 2.1

### Milestone 2.2: Dice Rolling & Display

- [x] Implement Dice Roller component (functional):
- [x] Roll dice buttons (d4, d6, d8, d10, d12, d20, d100)
- [x] Custom dice expression input (e.g., "2d6+3")
- [x] Display roll results with breakdown
- [x] Create Chat Log component:
- [x] Display dice roll results
- [x] Display action results from backend
- [x] Timestamp and formatting
- [x] Integrate dice rolling into Player Sheet (clickable ability scores)
- [x] Create and run Tests for Milestone 2.2

### Milestone 2.3: Interactive Character Sheet

- [x] Implement clickable attributes in Player Sheet:
- [x] Ability score rolls (with modifiers)
- [x] Skill checks
- [x] Saving throws
- [x] Implement action buttons:
- [x] Attack actions (send command to backend)
- [x] Spell casting (send command to backend)
- [x] Item usage (send command to backend)
- [x] Display calculated values from backend View Model:
- [x] AC (Armor Class)
- [x] HP (with max HP)
- [x] Attack bonuses
- [x] Damage bonuses
- [x] Show calculation explanations (tooltips or expandable sections)
- [x] Create and run Tests for Milestone 2.3

### Milestone 2.4: Combat System UI

- [x] Implement Turn System UI:
- [x] Current turn indicator
- [x] Next/Previous turn buttons
- [x] End turn button
- [x] Implement Action Economy display:
- [x] Action / Bonus Action / Reaction indicators
- [x] Available actions counter
- [x] Implement Initiative Tracker (functional):
- [x] Roll initiative for all combatants
- [x] Sort by initiative
- [x] Highlight current turn
- [x] Implement HP Bar updates (reactive to backend state changes)
- [x] Create and run Tests for Milestone 2.4

### Milestone 2.5: DM Tools - Combat Management

- [x] Implement Monster Spawning (functional):
- [x] Drag-and-drop from library to combat
- [x] Create monster instance
- [x] Add to initiative tracker
- [x] Implement Combat Controls:
- [x] Start/End combat
- [x] Add/Remove combatants
- [x] Manual HP editing with validation
- [x] Implement Monster Action UI:
- [x] Display available actions
- [x] Execute monster actions (send commands)
- [x] Create and run Tests for Milestone 2.5

## Phase 3: The Platform (Modding & Advanced)

Focus: Map system, modding support, and advanced features.

### Milestone 3.1: MFE - Cartographer (Map)

- [x] Create `apps/cartographer` MFE package
- [x] Setup PixiJS or Konva integration
- [x] Implement Grid System:
- [x] Display grid overlay
- [x] Grid size configuration
- [x] Snap-to-grid functionality
- [x] Implement Background Layer:
- [x] Load background images
- [x] Pan and zoom controls
- [x] Implement Token Layer:
- [x] Display character/monster tokens
- [x] Drag tokens on map
- [x] Send movement commands to backend
- [x] Integrate Cartographer into App Shell layout
- [x] Create and run Tests for Milestone 3.1

### Milestone 3.2: Advanced Map Features

- [x] Implement Fog of War:
- [x] DM-controlled visibility
- [x] Player view restrictions
- [x] Implement Measurement Tools:
- [x] Distance measurement
- [x] Area of effect visualization
- [x] Implement Map Layers:
- [x] Multiple map layers
- [x] Layer visibility toggles
- [x] Create and run Tests for Milestone 3.2

### Milestone 3.3: Modding Support - Frontend

- [x] Create Mod Launcher UI:
- [x] List available mods
- [x] Enable/disable mods
- [x] Mod load order management
- [x] Implement Style Mod Support:
- [x] CSS variable theming system
- [x] Theme selector
- [x] Custom theme loading
- [x] Implement Content Mod Display:
- [x] Show modded items/spells/monsters
- [x] Display mod attribution
- [x] Create and run Tests for Milestone 3.3

### Milestone 3.4: Module Federation & External MFEs

- [x] Setup Module Federation for MFEs:
- [x] Configure Vite Module Federation plugin
- [x] Expose MFE components
- [x] Remote MFE loading
- [x] Implement External MFE Loader:
- [x] Load MFEs from external URLs
- [x] Security validation
- [x] Error handling
- [x] Create MFE Registry/Discovery system
- [x] Create and run Tests for Milestone 3.4

### Milestone 3.5: Polish & Performance

- [x] Implement code splitting and lazy loading
- [x] Optimize bundle sizes
- [x] Implement virtual scrolling for large lists
- [x] Add loading skeletons and transitions
- [x] Implement error boundaries
- [x] Add accessibility features (ARIA labels, keyboard navigation)
- [x] Performance testing and optimization
- [x] Create and run Tests for Milestone 3.5

