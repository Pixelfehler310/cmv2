# User & Identity Management: Campaigns & Sessions

This document defines the architecture for managing User Identities within the context of Campaigns, specifically addressing the "DM vs. Player" role distinction and how Sessions are managed.

## 1. The Core Concept: Contextual Identity

A User's identity is **global**, but their Role is **contextual**.
-   **Global Identity**: "Simon" (User ID: 123). Authenticated via `src.identity`.
-   **Contextual Role**: In "Campaign A", Simon is the **DM**. In "Campaign B", Simon is a **Player** (playing "Gandalf").

### Data Model: The Association

We need a many-to-many relationship between `Users` and `Campaigns`, storing the specific role and potentially the active character.

```python
# backend/src/campaigns/models.py (Conceptual)

class CampaignMember(Base):
    __tablename__ = "campaign_members"
    
    campaign_id = ForeignKey("campaigns.id")
    user_id = ForeignKey("users.id")
    
    role = Enum("DM", "PLAYER", "SPECTATOR")
    
    # If Player, which character are they currently controlling?
    # Can be null if DM, or if Player hasn't selected a character yet.
    active_character_id = ForeignKey("characters.id", nullable=True) 
```

## 2. Campaign Access & Discovery

### API: `GET /campaigns`
Returns a list of campaigns the current user is associated with.
**Response:**
```json
[
  {
    "id": "uuid-1",
    "name": "The Dark Tower",
    "role": "DM",
    "next_session": "2023-10-27T19:00:00Z"
  },
  {
    "id": "uuid-2",
    "name": "Lost Mines",
    "role": "PLAYER",
    "character_name": "Gandalf"
  }
]
```
*Frontend Logic:* When rendering the dashboard, the frontend uses the `role` field to decide whether to show "Edit Campaign" buttons (DM) or just "Join Session" (Player).

### API: `POST /campaigns` (Create)
Creates a new campaign. The creator is automatically assigned the **DM** role.

### API: `POST /campaigns/{id}/join` (Invite/Join)
-   **Invite Link**: Campaigns generate a unique invite code.
-   **Logic**: When a user uses an invite code, a `CampaignMember` record is created with `role=PLAYER`.

## 3. Session Management (The "Lobby")

When a user "Enters" a campaign, they are effectively joining a **Session**.

### The Handshake (WebSocket)
1.  **Connect**: Frontend connects to `ws://api/campaigns/{id}/ws?token={jwt}`.
2.  **Authenticate**: Backend validates JWT -> Gets `User`.
3.  **Authorize**: Backend checks `CampaignMember` table:
    -   Is `User` a member of `Campaign {id}`?
    -   What is their `role`?
4.  **Register**: Backend adds the connection to the `SessionManager` for that campaign.
    -   `SessionManager` stores: `ConnectionID -> { UserID, Role, ActiveCharacterID }`.

### State Synchronization
-   **Initial State**: Server sends the full `GameState` (or relevant subset).
    -   **DM** receives everything (hidden monsters, GM notes).
    -   **Player** receives only what they can see (Fog of War filtered).
-   **Role-Based Actions**:
    -   **DM**: Can move any token, reveal maps, change HP of monsters.
    -   **Player**: Can only move their own token (`active_character_id`), roll for their character.

## 4. Frontend Architecture

### The `CampaignRoute`
This route acts as the "Lobby" or "Bootstrapper".

1.  **Load**: Fetches `GET /campaigns/{id}` to get metadata and **User's Role**.
2.  **Switch**:
    -   If `role === 'DM'`: Render `<DMView />`.
    -   If `role === 'PLAYER'`: Render `<PlayerView />`.

### `SessionProvider` (Context)
Wraps the view. Manages the WebSocket connection.
-   **`useSession()` hook**: Exposes `isConnected`, `latency`, `onlineUsers`.
-   **`useGameState()` hook**: Exposes the synced state (Entities, Map).

## 5. Implementation Plan

### Backend
1.  **Models**: Create `Campaign` and `CampaignMember` models in `src/campaigns`.
2.  **API**: Implement CRUD for campaigns and membership management.
3.  **WebSocket**: Implement `ConnectionManager` that is aware of `CampaignMember` roles.

### Frontend
1.  **Dashboard**: Update to fetch and display campaigns with roles.
2.  **Routing**: `CampaignRoute` determines Role and renders appropriate View.
3.  **Context**: Enhance `WebSocketManager` to handle role-specific state.
