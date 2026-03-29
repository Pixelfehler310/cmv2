# ISSUE [VERT][V05-09]: Campaign Content Policy & Multitenancy Lookups

Status: Planned
Owner: Content Systems
Parent: ISSUE [VERT][V05]
Depends on: ISSUE [VERT][V05-06]

## Why This Exists

Currently, the V05 search and resolution APIs return all `PUBLISHED` content globally. In a real-world VTT scenario, a Dungeon Master (DM) needs the ability to control which "Source Books" (Content Packs) are allowed in their specifically scoped campaign.

Without a `CampaignContentPolicy`, players might select homebrew monsters or optional rules that the DM has explicitly banned for that session. This also forms the foundation for digital entitlement (ensuring users only see content they own or have been granted access to).

## Implementation Steps (Actionable)

1. **Database Schema:**
   * Create a `CampaignContentPolicy` table: `campaign_id (FK)`, `pack_id (FK)`, `is_enabled (bool)`.
2. **Update Compendium APIs:**
   * Modify `list_definitions` and `search_definitions` endpoints to accept an optional `campaign_id` header or parameter.
   * If `campaign_id` is provided, the query MUST filter results to only include definitions from packs where `is_enabled = True` for that campaign.
3. **Integrity Policy Update:**
   * Update the `LinkedEntryResolutionService` to prevent resolving links to "Disabled" content during a campaign session.
4. **Policy Management UI/API:**
   * Create an endpoint for DMs to toggle packs on/off within their campaign.

## Scope

In Scope:
- Filtering the Read Path (Search/Query) by Campaign context.
- Storage for Campaign -> Pack enablement states.

Out of Scope:
- Payment/Stripe integration for entitlements (SaaS billing).
- Filtering the Write Path (an author can always see their own content in the creator tool).

## Acceptance Criteria

1. A DM can disable "Content Pack A" for "Campaign 1".
2. A search for a monster belonging to "Content Pack A" within the context of "Campaign 1" returns zero results.
3. The same search performed globally (or for another campaign where the pack is enabled) returns the monster.
4. Integration tests verify that `campaign_id` scoping is strictly enforced at the repository level.

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/content -k policy_scoping`
