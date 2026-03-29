# ISSUE [VERT][V05-10-CLEAN]: Identity & Content Entitlement Persistence

Status: Planned
Owner: Identity + Content Systems
Parent: ISSUE [VERT][V05]
Depends on: ISSUE [VERT][V05-01]

## Why This Exists

V05 defines the system as a multi-tenant SaaS. Currently, authentication exists, but there is no mechanism to track **Library Permissions** for game data. 

To complete V05, we must implement the **ContentEntitlement** model. This provides the permission layer that grants a specific `UserAccount` access to a `ContentPackRecord` (e.g., "User A purchased the PHB and Tasha's"). This is the final bridge between the generic identity system and the specialized D&D game data.

## Implementation Steps (Actionable)

1. **Domain Models (`src/systems/dnd5e/identity/domain/models.py`):**
   * **`ContentEntitlement`**: Link `user_id` to `pack_id`. Includes `granted_at` and `source` (purchase, subscription).
   * **`UserSubscription`**: (Mocked or Minimal) To track overall storage limits as defined in the V05 SaaS map.
2. **Infrastructure:**
   * Implement SQLAlchemy models and a `ContentEntitlementRepository`.
3. **Application Service:**
   * Implement an `EntitlementService` that provides a fast "Identity Context" (a list of all PackIDs the user can access).
4. **Policy Enforcement:**
   * Update the Compendium Query service to intersect its results with the user's **Entitlement Context** to ensure users only see content they "own" or have been granted access to.

## Scope

In Scope:
- Digital content ownership mapping.
- Filtering the compendium search results by user entitlement.

Out of Scope:
- Credit Card processing or a Marketplace UI.
- OAuth provider implementation (already exists in `src/identity`).

## Acceptance Criteria

1. A user can be "Granted" an entitlement to a specific `ContentPackRecord`.
2. A search in the compendium successfully hides all results from Packs that the user does not own.
3. Unit tests verify that "System SRD" packs are accessible to all users by default.

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/identity -k entitlement_scoping`
