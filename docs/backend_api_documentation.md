# Backend API Documentation

## Overview
The backend is built using **FastAPI** (Python) and follows a **Modular Monolith** architecture. It serves as the source of truth for game data, rules processing, and campaign state.

## WebSocket Combat Contract (Current)

The D&D 5e websocket combat flow is authoritative and server-validated.

1. Command events require `request_id`.
2. Terminal outcomes are explicit: success event, `action_denied` / `command_denied`, or `error`.
3. Payload-based impersonation (`acting_as_user_id`) is no longer authoritative for command authorization.
4. Delegation is server-side lifecycle state managed through explicit commands:
	- `delegate_start` (DM only)
	- `delegate_stop` (DM only)
	- `delegate_status`
5. Delegated authorization uses effective identity, and audit context tracks both identities:
	- `authenticated_user_id` (socket owner)
	- `effective_user_id` (delegated player when active)

### Denial Reason Additions

- `encounter_session_required`: returned when mutating combat commands are attempted without a valid encounter session.

## 1. File Structure
The backend code is located in `backend/src/` and is organized into the following modules:

```
backend/src/
├── common/                 # Shared utilities
│   ├── database.py         # Database connection & Base model
│   ├── config.py           # Environment configuration
│   └── mixins.py           # Shared model mixins (UUID, Timestamp)
├── data/                   # "The Librarian" (Static Content)
│   ├── lib/                # Models & Logic
│   │   ├── item.py, spell.py, monster.py ...
│   │   └── loader.py       # Data ingestion logic
│   └── routers/            # API Endpoints
│       ├── items.py        # /items
│       ├── spells.py       # /spells
│       ├── monsters.py     # /monsters
│       └── definitions.py  # /definitions (Species, Classes, etc.)
├── engine/                 # "The Core" (Rules & Math)
│   └── lib/
│       ├── dice.py         # Dice rolling logic
│       ├── rules.py        # D&D 5e Rules (modifiers, proficiency)
│       └── effect_engine.py# Static effect processing
├── campaigns/              # "The State Manager" (Game State)
│   ├── lib/
│   │   ├── campaign.py     # Campaign model
│   │   ├── character.py    # Character model
│   │   ├── inventory.py    # Inventory management logic
│   │   └── instance_factory.py # Factory for creating instances
│   └── routers/
│       ├── campaigns.py    # /campaigns
│       └── characters.py   # /characters
└── main.py                 # Application Entrypoint
```

## 2. API Endpoints

### Base URL
`http://localhost:8000` (Local Development)

### Data Module (Static Content)
These endpoints provide read-only access to game definitions (SRD content).

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/items/` | List all item definitions (pagination: `skip`, `limit`). |
| `GET` | `/items/{id}` | Get a specific item definition. |
| `GET` | `/spells/` | List all spell definitions. |
| `GET` | `/spells/{id}` | Get a specific spell definition. |
| `GET` | `/monsters/` | List all monster definitions. |
| `GET` | `/monsters/{id}` | Get a specific monster definition. |
| `GET` | `/definitions/species` | List all Species (Races). |
| `GET` | `/definitions/classes` | List all Classes. |
| `GET` | `/definitions/backgrounds` | List all Backgrounds. |

### Campaigns Module (Game State)
These endpoints manage the dynamic state of games and characters.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/campaigns/` | List all campaigns. |
| `POST` | `/campaigns/` | Create a new campaign. |
| `GET` | `/campaigns/{id}` | Get campaign details (includes list of characters). |
| `DELETE` | `/campaigns/{id}` | Delete a campaign. |
| `GET` | `/characters/` | List all characters. |
| `POST` | `/characters/` | Create a new character. |
| `GET` | `/characters/{id}` | Get character details (includes full stats, inventory, spells). |
| `PUT` | `/characters/{id}` | Update character details. |
| `DELETE` | `/characters/{id}` | Delete a character. |

## 3. Key Logic & Concepts

### Character Creation
Creating a character involves linking it to specific Definitions:
1.  **Species (`species_id`)**: Determines base speed, size, and racial traits.
2.  **Class (`class_id`)**: Determines hit dice, proficiencies, and class features.
3.  **Background (`background_id`)**: Determines starting equipment and skills.

The backend does **not** automatically populate stats or inventory upon creation yet (planned for future). The frontend should send the selected IDs.

### Inventory Management
Inventory is stored as a JSON list of **Item Instances** on the Character or Monster model.
- **Structure:** `[{ "id": "uuid", "item_id": "def_id", "quantity": 1, "equipped": boolean }]`
- **Equipping:** When an item is `equipped=True`, the **Effect Engine** will automatically apply its effects (e.g., +2 AC from a Shield) to the character's stats when the View Model is generated.

### The Effect Engine
The backend calculates the final "View Model" of a character dynamically.
- **Base Stats:** Stored in the DB (Strength=16, Dex=14).
- **Effects:** Derived from Species, Class, and Equipped Items.
- **Calculation:** The engine iterates through all active effects and modifies the base stats to produce the final values (e.g., AC 10 + 2 (Shield) = 12).
- **Frontend Usage:** The API returns the *calculated* values in the response, so the frontend mostly just renders what it receives.

### Dice Rolling
(Future Endpoint) The backend has a `DiceService` capable of parsing expressions like `1d20+5`. This will be exposed via a `/command/roll` endpoint in the future.

## 4. Development Workflow
- **Docs:** Auto-generated Swagger UI is available at `http://localhost:8000/docs`.
- **Database:** Uses PostgreSQL. Models are defined in `src/*/lib/*.py`.
- **Migrations:** Currently using `alembic` (if configured) or direct table creation in tests.
