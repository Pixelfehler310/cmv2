<!-- a504a064-0cac-4052-bc2f-317ddd5687e9 efa40393-c08a-46e0-a22c-2aa227c49cb3 -->

# Frontend Implementation Plan

This document outlines the step-by-step plan to build the Open RPG Engine frontend, following the Microfrontends (MFE) architecture with pnpm workspaces.

## Phase 1: Foundation & The "Digital Filing Cabinet" (MVP)

Focus: Basic UI structure, data display, and CRUD operations for characters, campaigns, and SRD content.

### Milestone 1.1: Project Setup & Infrastructure

- [x] Initialize pnpm workspace structure
- [x] Setup App Shell (`apps/host`) with Vite + React
- [x] Setup FlexLayout for docking windows
- [x] Create shared packages (`@rpg/types`, `@rpg/ui`)
- [ ] Configure TypeScript paths and workspace dependencies
- [ ] Setup Tailwind CSS with shadcn/ui integration
- [ ] Create development scripts for parallel MFE development
- [ ] Setup Vitest and React Testing Library for testing

### Milestone 1.2: Shared Contracts & API Client

- [ ] Define TypeScript interfaces in `@rpg/types` matching backend Pydantic models:
- [ ] `Item`, `Spell`, `Monster` (from Milestone 1.2)
- [ ] `Character`, `Campaign` (from Milestone 1.3)
- [ ] Request/Response types for all endpoints
- [ ] Create API client service in App Shell:
- [ ] HTTP client with base URL configuration
- [ ] Functions for Items API (`getItems`, `getItem`)
- [ ] Functions for Spells API (`getSpells`, `getSpell`)
- [ ] Functions for Monsters API (`getMonsters`, `getMonster`)
- [ ] Functions for Characters API (`getCharacters`, `getCharacter`, `createCharacter`, `updateCharacter`, `deleteCharacter`)
- [ ] Functions for Campaigns API (`getCampaigns`, `getCampaign`, `createCampaign`, `updateCampaign`, `deleteCampaign`)
- [ ] Create error handling and loading state utilities
- [ ] Create and run Tests for Milestone 1.2

### Milestone 1.3: App Shell - Core Infrastructure

- [ ] Implement routing system (React Router)
- [ ] Create authentication context/provider (JWT token management)
- [ ] Implement WebSocket connection manager (single connection in App Shell)
- [ ] Create Client-Side Event Bus for MFE communication
- [ ] Implement `dispatchAction(type, payload)` function for downward communication to views
- [ ] Create ViewContext for managing Player/DM view switching
- [ ] Implement AppNavbar component:
  - [ ] Logo/Branding (left)
  - [ ] Search bar (center) - Wiki search, future: command palette
  - [ ] Connection status indicator
  - [ ] User icon with dropdown menu
  - [ ] QR code icon (placeholder for friend management)
  - [ ] Settings icon (placeholder)
- [ ] Implement ViewContainer that switches between Player/DM views
- [ ] Add proper error boundaries around views
- [ ] Create and run Tests for Milestone 1.3

### Milestone 1.4: Shared UI Components (`@rpg/ui`)

- [ ] Install and configure shadcn/ui
- [ ] Create base UI components:
- [ ] Button, Input, Select, Textarea
- [ ] Card, Dialog, Sheet
- [ ] Table, Tabs
- [ ] Badge, Avatar
- [ ] Create RPG-specific components:
- [ ] StatBlock (for displaying ability scores)
- [ ] HPBar (health bar component)
- [ ] DiceRoller (visual dice component, non-functional initially)
- [ ] Create and run Tests for Milestone 1.4

### Milestone 1.5: MFE - Player View

- [ ] Create `apps/player-view` MFE package
- [ ] Implement FlexLayout system for Player View (manages its own windows)
- [ ] Create window components:
  - [ ] Character Sheet window (tabs: Stats, Inventory, Spells, Features)
  - [ ] Chat window (placeholder)
  - [ ] Lore/Notes window (Wiki access placeholder)
  - [ ] Inventory window (detailed view)
  - [ ] Actions/Combat window (placeholder for combat)
- [ ] Implement character data fetching (using API client from App Shell)
- [ ] Implement character selection/loading UI
- [ ] Add placeholder buttons for actions (not functional yet)
- [ ] Implement window layout persistence (Player View manages its own layout)
- [ ] Integrate Player View into App Shell ViewContainer
- [ ] Create and run Tests for Milestone 1.5

### Milestone 1.6: MFE - DM View

- [ ] Create `apps/dm-view` MFE package
- [ ] Implement FlexLayout system for DM View (manages its own windows)
- [ ] Create window components:
  - [ ] Monster window (active/planned monsters with properties)
  - [ ] Campaign Management window
  - [ ] Initiative Tracker window (basic list, no turn logic yet)
  - [ ] Additional windows as needed
- [ ] Implement Monster Library functionality:
  - [ ] List monsters from API
  - [ ] Search/filter functionality
  - [ ] Monster detail view
  - [ ] Drag-and-drop placeholder for spawning monsters
- [ ] Implement Campaign Management:
  - [ ] Campaign list and selection
  - [ ] Campaign detail view
  - [ ] Character list within campaign
- [ ] Implement HP Editor (direct value editing for monsters/characters)
- [ ] Implement window layout persistence (DM View manages its own layout)
- [ ] Integrate DM View into App Shell ViewContainer
- [ ] Create and run Tests for Milestone 1.6

### Milestone 1.7: Shared Components & Wiki Search

- [ ] Implement Item Browser component in `@rpg/ui`:
  - [ ] List all items
  - [ ] Item detail view
  - [ ] Search functionality
  - [ ] Reusable in both Player and DM views
- [ ] Implement Spell Browser component in `@rpg/ui`:
  - [ ] List all spells
  - [ ] Spell detail view
  - [ ] Filter by level, school, class
  - [ ] Reusable in both Player and DM views
- [ ] Implement Character Creation Form in `@rpg/ui`:
  - [ ] Basic info (name, race, class, level)
  - [ ] Ability score assignment
  - [ ] Save to backend
- [ ] Implement Campaign Creation Form in `@rpg/ui`:
  - [ ] Basic info (name, description)
  - [ ] Add characters to campaign
  - [ ] Save to backend
- [ ] Implement Wiki Search in App Shell navbar:
  - [ ] Search bar with dropdown results
  - [ ] Wiki content display (modal/dialog)
  - [ ] Basic wiki entry structure
- [ ] Create and run Tests for Milestone 1.7

## Phase 2: The "Calculator" (Automation)

Focus: Interactive features, dice rolling, real-time updates, and basic game mechanics.

### Milestone 2.1: Real-Time Communication & State Management

- [ ] Implement WebSocket message handling in App Shell
- [ ] Create state management (Zustand stores) for:
- [ ] Current campaign state
- [ ] Active characters/monsters
- [ ] Combat state (initiative, current turn)
- [ ] Implement WebSocket event listeners in MFEs
- [ ] Create event bus subscriptions for cross-MFE communication
- [ ] Create and run Tests for Milestone 2.1

### Milestone 2.2: Dice Rolling & Display

- [ ] Implement Dice Roller component (functional):
- [ ] Roll dice buttons (d4, d6, d8, d10, d12, d20, d100)
- [ ] Custom dice expression input (e.g., "2d6+3")
- [ ] Display roll results with breakdown
- [ ] Create Chat Log component:
- [ ] Display dice roll results
- [ ] Display action results from backend
- [ ] Timestamp and formatting
- [ ] Integrate dice rolling into Player Sheet (clickable ability scores)
- [ ] Create and run Tests for Milestone 2.2

### Milestone 2.3: Interactive Character Sheet

- [ ] Implement clickable attributes in Player Sheet:
- [ ] Ability score rolls (with modifiers)
- [ ] Skill checks
- [ ] Saving throws
- [ ] Implement action buttons:
- [ ] Attack actions (send command to backend)
- [ ] Spell casting (send command to backend)
- [ ] Item usage (send command to backend)
- [ ] Display calculated values from backend View Model:
- [ ] AC (Armor Class)
- [ ] HP (with max HP)
- [ ] Attack bonuses
- [ ] Damage bonuses
- [ ] Show calculation explanations (tooltips or expandable sections)
- [ ] Create and run Tests for Milestone 2.3

### Milestone 2.4: Combat System UI

- [ ] Implement Turn System UI:
- [ ] Current turn indicator
- [ ] Next/Previous turn buttons
- [ ] End turn button
- [ ] Implement Action Economy display:
- [ ] Action / Bonus Action / Reaction indicators
- [ ] Available actions counter
- [ ] Implement Initiative Tracker (functional):
- [ ] Roll initiative for all combatants
- [ ] Sort by initiative
- [ ] Highlight current turn
- [ ] Implement HP Bar updates (reactive to backend state changes)
- [ ] Create and run Tests for Milestone 2.4

### Milestone 2.5: DM Tools - Combat Management

- [ ] Implement Monster Spawning (functional):
- [ ] Drag-and-drop from library to combat
- [ ] Create monster instance
- [ ] Add to initiative tracker
- [ ] Implement Combat Controls:
- [ ] Start/End combat
- [ ] Add/Remove combatants
- [ ] Manual HP editing with validation
- [ ] Implement Monster Action UI:
- [ ] Display available actions
- [ ] Execute monster actions (send commands)
- [ ] Create and run Tests for Milestone 2.5

## Phase 3: The Platform (Modding & Advanced)

Focus: Map system, modding support, and advanced features.

### Milestone 3.1: Cartographer Integration (Map Window in DM View)

- [ ] Create `apps/cartographer` package (component, not standalone MFE)
- [ ] Setup PixiJS or Konva integration
- [ ] Implement Grid System:
  - [ ] Display grid overlay
  - [ ] Grid size configuration
  - [ ] Snap-to-grid functionality
- [ ] Implement Background Layer:
  - [ ] Load background images
  - [ ] Pan and zoom controls
- [ ] Implement Token Layer:
  - [ ] Display character/monster tokens
  - [ ] Drag tokens on map
  - [ ] Send movement commands to backend
- [ ] Integrate Cartographer as window in DM View's FlexLayout:
  - [ ] Default: Fullscreen, focused, background layer
  - [ ] Window controls (minimize, maximize, close)
  - [ ] Proper integration with DM View's layout system
- [ ] Create and run Tests for Milestone 3.1

### Milestone 3.2: Advanced Map Features

- [ ] Implement Fog of War:
- [ ] DM-controlled visibility
- [ ] Player view restrictions
- [ ] Implement Measurement Tools:
- [ ] Distance measurement
- [ ] Area of effect visualization
- [ ] Implement Map Layers:
- [ ] Multiple map layers
- [ ] Layer visibility toggles
- [ ] Create and run Tests for Milestone 3.2

### Milestone 3.3: Modding Support - Frontend

- [ ] Create Mod Launcher UI:
- [ ] List available mods
- [ ] Enable/disable mods
- [ ] Mod load order management
- [ ] Implement Style Mod Support:
- [ ] CSS variable theming system
- [ ] Theme selector
- [ ] Custom theme loading
- [ ] Implement Content Mod Display:
- [ ] Show modded items/spells/monsters
- [ ] Display mod attribution
- [ ] Create and run Tests for Milestone 3.3

### Milestone 3.4: Module Federation & External MFEs

- [ ] Setup Module Federation for MFEs:
- [ ] Configure Vite Module Federation plugin
- [ ] Expose MFE components
- [ ] Remote MFE loading
- [ ] Implement External MFE Loader:
- [ ] Load MFEs from external URLs
- [ ] Security validation
- [ ] Error handling
- [ ] Create MFE Registry/Discovery system
- [ ] Create and run Tests for Milestone 3.4

### Milestone 3.5: Polish & Performance

- [ ] Implement code splitting and lazy loading
- [ ] Optimize bundle sizes
- [ ] Implement virtual scrolling for large lists
- [ ] Add loading skeletons and transitions
- [ ] Implement error boundaries
- [ ] Add accessibility features (ARIA labels, keyboard navigation)
- [ ] Performance testing and optimization
- [ ] Create and run Tests for Milestone 3.5

Phase 4: Enhancement

- [ ] Prettier UI and stronger use of shadcn, currently css is pretty plain and basic.
- [ ] Add more detailed and informative error messages to the UI.
- [ ] Set titles of tabs in the Player Sheet and DM Tools to be more descriptive.
- [ ] Make Player view and DM Tools more logic and based on DND rules. Currently Layout is problematic and incomplete.

### To-dos

- [ ] Complete Milestone 1.1: Configure TypeScript, Tailwind, shadcn/ui, testing setup, and development scripts
- [ ] Complete Milestone 1.2: Define TypeScript interfaces matching backend models and create API client service
- [ ] Complete Milestone 1.3: Implement routing, authentication, WebSocket, event bus, and action dispatch in App Shell
- [ ] Complete Milestone 1.4: Create base UI components and RPG-specific components in @rpg/ui package
- [ ] Complete Milestone 1.5: Create Player Sheet MFE with character display tabs and data fetching
- [ ] Complete Milestone 1.6: Create DM Tools MFE with monster library, campaign management, and initiative tracker
- [ ] Complete Milestone 1.7: Implement item/spell browsers and character/campaign creation forms
- [ ] Complete Milestone 2.1: Implement WebSocket handling, state management, and event bus subscriptions
- [ ] Complete Milestone 2.2: Implement functional dice roller and chat log components
- [ ] Complete Milestone 2.3: Add clickable attributes, action buttons, and calculated value display in Player Sheet
- [ ] Complete Milestone 2.4: Implement turn system, action economy, and functional initiative tracker
- [ ] Complete Milestone 2.5: Implement functional monster spawning, combat controls, and monster actions
- [ ] Complete Milestone 3.1: Create Cartographer MFE with PixiJS/Konva, grid system, and token layer
- [ ] Complete Milestone 3.2: Implement fog of war, measurement tools, and map layers
- [ ] Complete Milestone 3.3: Create mod launcher UI, style mod support, and content mod display
- [ ] Complete Milestone 3.4: Setup Module Federation and implement external MFE loading
- [ ] Complete Milestone 3.5: Optimize performance, add accessibility, and implement error boundaries
