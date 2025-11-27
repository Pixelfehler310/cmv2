# General View Overview

This document provides a high-level overview of the Microfrontends (MFEs), their Views, and the Windows/Components contained within them. It serves as the map for our frontend implementation.

## 1. App Shell (The Host)
**Responsibility:** Infrastructure, Authentication, Global Navigation, View Switching.
**Tech:** React, Vite, WebSocket Client.

### Components
- **AppNavbar:**
  - **Global Search:** The primary entry point for the Wiki/Library. accessible via `Ctrl+K`. (later on points for other features like commands and macros)
  - **User Menu:** Profile, Settings, Logout.
  - **Connection Status:** WebSocket health indicator.
  - **Friend/Social:** (Future) Friend list and invites. (with qr-code)
- **ViewContainer:** The mount point where the active MFE (Player, DM, or Campaign Editor) is rendered.
- **Global Overlays:**
  - **Login Window:** A simple overlay or page for unauthenticated users. Currently just requires a username.
  - **Wiki Modal:** A floating, resizeable dialog to browse Items, Spells, Monsters, and Rules without leaving the game.
  - **Settings Dialog:** Global application settings (Theme, Audio, Keybinds).

---

## 2. Player View MFE (`@rpg/player-view`)
**Responsibility:** The interface for a player controlling a character.
**Layout Engine:** `flexlayout-react` (User persists their own layout).

### Windows
- **Cartographer (The Map):**
  - **Summary:** The visual representation of the world.
  - **Features:** Fog of War (Player view), Token movement (Own tokens), Pings.
  - **Note:** Reuses the same "Cartographer" component as the DM view but in `PlayerMode`.
- **Character Sheet:**
  - **Summary:** The core identity. HP, AC, Ability Scores, Skills, Saving Throws.
  - **Features:** Visual representation of health, clickable skills for rolling.
- **Combat & Actions:**
  - **Summary:** What can I do *now*?
  - **Features:** List of available Actions, Bonus Actions, Reactions (filtered by current state). Attack buttons, Spell casting buttons.
- **Inventory:**
  - **Summary:** Management of equipment and loot.
  - **Features:** Drag-and-drop equipment slots (Head, Body, Hands), Backpack list, Currency tracker.
- **Spellbook:**
  - **Summary:** Magic management.
  - **Features:** Known spells, Prepared spells, Spell Slots tracker.
- **Chat & Log:**
  - **Summary:** Communication and history.
  - **Features:** Dice roll results, In-character chat, Out-of-character chat, Whispers.
- **Lore & Notes:**
  - **Summary:** Personal journal and handouts.
  - **Features:** Rich text editor for notes, list of received handouts/images from DM.

---

## 3. DM View MFE (`@rpg/dm-view`)
**Responsibility:** The interface for the Dungeon Master running the game.
**Layout Engine:** `flexlayout-react` (Optimized for multi-monitor or dense information).

### Windows
- **Cartographer (The Map):**
  - **Summary:** The shared visual space.
  - **Features:** Fog of War control, Token movement, Layer management (Map, Objects, Tokens, GM Only), Drawings/Pings.
- **Combat Tracker (Initiative):**
  - **Summary:** Time management.
  - **Features:** Initiative list, Turn order, Active Conditions/Effects duration tracking.
- **Bestiary / Monster Manual:**
  - **Summary:** Monster source.
  - **Features:** Searchable list of monsters. Drag-and-drop onto the Map to spawn instances. (Advanced Feature)
- **Campaign Manager:**
  - **Summary:** Session control.
  - **Features:** Scene selection, Music/Audio control, Handout sharing.
- **Chat & Log:**
  - **Summary:** Global communication.
  - **Features:** See all rolls (including hidden GM rolls), send private messages.
- **Quick Reference:**
  - **Summary:** DM Screen.
  - **Features:** Customizable tables (Conditions, DC guides) for quick lookup.

---

## 4. Campaign Creator MFE (New)
**Responsibility:** A dedicated workspace for the DM to plan and structure the campaign before or between sessions.
**Layout:** Full-screen Node Editor.

### Components
- **Node-Based Story Editor:**
  - **Summary:** Visual flow of the campaign.
  - **Features:** Nodes representing Scenes, Encounters, or Narrative Beats. Lines representing transitions.
- **Encounter Builder:**
  - **Summary:** Setup for fights.
  - **Features:** Select monsters, define starting positions, calculate difficulty (XP/CR).
- **NPC Designer:**
  - **Summary:** Quick NPC generation.
  - **Features:** Create NPCs with stats and roleplay notes.


---

## 5. Shared / System Views

### Login / Auth System
- **View:** **Login Page** (Standalone Route).
- **Components:** Login Form, Registration Form, Password Recovery.

### Wiki / Library System
- **View:** **Wiki Modal** (Overlay) or **Wiki Page** (Standalone Route).
- **Components:**
  - **Definition Viewer:** Renders `ItemDefinition`, `SpellDefinition`, `MonsterDefinition` in a standardized, beautiful format.
  - **Search Results:** Fast filtering and categorization.
