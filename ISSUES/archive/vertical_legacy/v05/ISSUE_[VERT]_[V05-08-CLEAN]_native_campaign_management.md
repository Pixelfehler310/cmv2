# ISSUE [VERT][V05-08-CLEAN]: Native D&D Campaign Management & Content Policy

Status: Planned
Owner: Campaign Systems
Parent: ISSUE [VERT][V05]
Depends on: ISSUE [VERT][V05-06]

## Why This Exists

The prototype campaign logic (`legacy/campaigns`) relied on flat SQL models and was not built for a multi-tenant SaaS environment. To finish V05, we must implement a **High-Integrity Campaign Domain** that natively understands the new V05 Compendium.

Most importantly, we need the **CampaignContentPolicy**. Currently, any published content is visible in all campaigns. DMs need to be able to "Activate" or "Deactivate" entire Content Packs (e.g., "Exclude Tasha's Cauldron" or "Allow Only My Homebrew") for a specific game session.

## Implementation Steps (Actionable)

1. **Domain Models (`src/systems/dnd5e/campaigns/domain/models.py`):**
   * **`Campaign`**: Move from legacy to a new V05 entity. includes `owner_user_id`, `name`, `active_scene_id`.
   * **`CampaignMember`**: Defines `role` (DM, Player) and links to the user.
   * **`CampaignContentPolicy`**: A junction model linking `Campaign` to allowed `ContentPackRecord`s.
2. **Infrastructure (`src/systems/dnd5e/campaigns/infrastructure/`):**
   * Implement SQLAlchemy models and a `CampaignRepository`.
3. **Application Service:**
   * Implement `CampaignApplicationService` to manage session life-cycles and content policy toggles.
4. **Read-Path Filtering:**
   * Update the Compendium's `search` and `resolution` logic to accept a `campaign_id` and filter results based on the **Content Policy** of that campaign.

## Scope

In Scope:
- Native campaign persistence in the `dnd5e` namespace.
- Content Policy enforcement for all Compendium lookups.

Out of Scope:
- Real-time combat state (V02).
- Final UI for the campaign dashboard.

## Acceptance Criteria

1. A `Campaign` can be created natively in the `dnd5e` system.
2. The `CampaignContentPolicy` successfully restricts search results in the compendium when a `campaign_id` context is provided.
3. Unit tests confirm that unauthorized players cannot see "GM-Only" campaign notes or restricted content packs.

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/campaigns`
