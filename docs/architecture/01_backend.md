# Backend Architecture: The Modular Monolith

## 1. Services & Communication

### Design Pattern: Interface-First

We define strict **Interfaces (Contracts)** for all services.

- **Phase 1 (Monolith):** Implementation uses **direct library calls** (in-process) for performance and simplicity.
- **Phase 3 (Microservices):** We swap the implementation to use **HTTP/gRPC clients**, without changing the consuming code.

### Data Service ("The Librarian")

- **Responsibility:** Static Definitions (Items, Spells, Monsters).
- **Storage:** Database (PostgreSQL). Stores Core Content + Community Content (distinguished by `source` flag).
- **API:** Exposes a REST API (FastAPI) for external consumers/tools.
- **Validation:** Validates the _structure_ of Effects (via Pydantic) before serving them.

### Logic Service ("The Game Master")

- **Responsibility:** Campaign State, Rule Execution, Dice Rolling.
- **Storage:** Database (PostgreSQL). Stores Campaign/Character State.
- **API:** Exposes a REST API + WebSocket for the Frontend.
- **Dependency:** Consumes the Data Service via the defined Interface.

## 2. Database Strategy

- **Configurable Access:** Both services access PostgreSQL.
- **Separation:**
  - Tables are logically separated (e.g., `definitions_*` vs `state_*`).
  - Configuration allows pointing them to different DB instances in the future.

## 3. The Effect Engine (Library)

- **Nature:** A standalone **Library** with a concrete Interface.
- **Role:** Processes Rules and Effects.
- **Swappability:** Can be replaced by a different engine (or an external API-based engine) by implementing the Interface.
- **Extensibility:** Effect Data Types are extensible to allow Modders to define new Effect structures.

## 4. Data Flow

1.  **Frontend** requests static data from **Data Service API**.
2.  **Frontend** sends Commands (Actions) to **Logic Service API**.
3.  **Logic Service** fetches necessary definitions from **Data Service Interface**.
4.  **Logic Service** uses **Effect Engine Library** to process rules.
5.  **Logic Service** updates State in DB and notifies **Frontend** (via WebSocket).
