# Project Open RPG: The Architecture Manifesto

## 1. The Product Vision

We are not developing a simple "character sheet app", but a **platform ecosystem for digital role-playing games (Virtual Tabletop / VTT)**.

### The Core Promise (USP)

*   **Familiarity for Beginners:** The base version ("Vanilla") feels immediately familiar to D&D 5e/D&D Beyond players, without needing to learn new rules.
*   **Power for Tinkers:** The system is designed from the ground up for modding. Everything from simple house rules to complete "Total Conversions" is possible by exchanging JSON files and/or microservices.
*   **Legal Safety:** The entire system is strictly based on the **Creative Commons (CC-BY 4.0)** license of the **SRD 5.1** and avoids closed licenses or trademark infringements.

## 2. The Technology Stack (Decisions & Rationale)

| Technology | Role | Rationale |
| :--- | :--- | :--- |
| **Monorepo (Git)** | Repository Structure | **Decision:** A single repo for Frontend & Backend.<br>**Reason:** Maximum AI productivity (Cursor/Copilot sees full context), atomic commits for fullstack features, simplified refactoring across system boundaries. |
| **Python 3.11+** | Backend Language | **Decision:** Python instead of C#.<br>**Reason:** Undisputed standard for AI/ML integration (Phase 3), fastest API development, powerful ecosystem for data processing (Pydantic). |
| **FastAPI** | Backend Framework | **Reason:** Highest performance (async/await), automatic OpenAPI (Swagger) for modder documentation, first-class Pydantic integration. |
| **Pydantic v2** | Data Validation | **Reason:** The "Truth" of the system. Defines strict data contracts. Extremely fast in v2. |
| **PostgreSQL** | Database | **Reason:** The robust standard for relational data. Operated via Docker. |
| **React + Vite** | Frontend Framework | **Reason:** Industry standard, mature ecosystem, best support for Microfrontends (Module Federation), fastest dev server (Vite). |
| **pnpm workspaces** | JS Package Manager | **Reason:** Most efficient management of monorepos. Enables sharing types (`@rpg/types`) as local packages without npm upload. |
| **FlexLayout / ShadcnUI** | UI & Layout | **Reason:** `flexlayout-react` for professional docking windows (VS Code style). `shadcn/ui` for copy-paste-able, modifiable components. |
| **PixiJS / Konva** | Map Engine | **Reason:** React is too slow for maps. WebGL-based 2D engines are the standard for performant games in the browser. |
| **Docker / Compose** | Infrastructure & Prod | **Reason:** Local development runs "on metal", but databases and the final product run isolated and portable in containers. |

## 3. The Roadmap (Phases)

### Phase 1: The MVP ("Digital Filing Cabinet")
*   **Focus:** Administration & DM Control. Moving away from paper.
*   **Backend:** Stores characters. Loads SRD data only as text (for display). No Effect Engine.
*   **Frontend:** DM can spawn monsters and edit values directly. Players see their sheet.
*   **Benefit:** Playable at the table as a replacement for papers and books.

### Phase 2: The Automation ("Calculator")
*   **Focus:** Speeding up the game.
*   **Backend:** Implementation of Effect Engine V1 (static bonuses). Dice logic.
*   **Frontend:** Clickable attributes ("Roll for Attack"). Chat log with results. HP bar that reacts to damage.
*   **Data:** Step-by-step conversion of the most important SRD items from text to JSON effects.

### Phase 3: The Ecosystem ("The Platform") (New Software that bundles the existing one, instead of Frontend backend it could be a full application)
*   **Focus:** Modding & Community.
*   **Backend:** Full Mod Loader (Layered Loading). Effect Engine V2 (Trigger/Conditions).
*   **Frontend:** Launcher UI for selecting mods. Support for loading external MFE bundles (Module Federation).
*   **Infrastructure:** Optional splitting into real Docker containers for "Architect" users.

## 4. Licensing & Legal

The entire project stands on a secure legal foundation.

*   **Basis:** System Reference Document 5.1 (SRD 5.1).
*   **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0).
*   **Strategy:**
    *   We use the game mechanics and texts of the SRD, which are released under CC-BY 4.0.
    *   We strictly avoid using protected trademarks ("Product Identity") of Wizards of the Coast (e.g., Beholder, D&D Logo).
    *   **Attribution:** The required license notice will be placed prominently in the software and documentation.
