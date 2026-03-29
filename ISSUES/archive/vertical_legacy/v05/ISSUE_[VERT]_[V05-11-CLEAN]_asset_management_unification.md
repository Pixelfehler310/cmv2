# ISSUE [VERT][V05-11-CLEAN]: Asset Management & Media-to-Definition Convergence

Status: Planned
Owner: Assets + Content Systems
Parent: ISSUE [VERT][V05]
Depends on: ISSUE [VERT][V05-01]

## Why This Exists

Currently, asset management (images, PDFs) is decoupled from the Compendium rule-graph. We need to unify these two domains so that media assets are treated as legitimate nodes in the `LinkedEntryReference` system. This allows for:
1. **Referential Integrity**: Warning the user if they try to delete an image that is currently used by 5 monsters.
2. **Simplified Clients**: Allowing the UI to resolve the "Token URL" automatically when loading a monster, instead of making separate API calls.

## Implementation Steps (Actionable)

1. **Asset Identity Integration:**
   * Ensure `AssetRecord` (from the Asset Domain) uses a compatible ID format (UUID) with `DefinitionRecord`.
2. **Linking Mechanics:**
   * Add `media_links` field to the polymorphic `DefinitionRecord` payload.
   * Use the existing `LinkedEntryReference` system with a new `RelationKind.MEDIA` to point from definitions to assets.
3. **Write Path Enforcement:**
   * Update `CompendiumApplicationService` to validate that linked asset IDs actually exist during the creation/update of a definition.
4. **Read Path Enrichment:**
   * Modify `LinkedEntryResolutionService` to include asset metadata (signed URLs, dimensions) in the resolved definition tree projection.

## Scope

In Scope:
- Linking definitions to uploaded images/tokens.
- Validation of media existence on the Write Path.
- Projection of media URLs on the Read Path.

Out of Scope:
- The actual binary storage/upload logic (S3/Cloudinary).
- Image processing or thumbnail generation.

## Acceptance Criteria

1. A `MonsterDefinition` can be saved with a `token_asset_id`.
2. Deleting the image asset is blocked (or triggers a warning) if it is actively linked to a definition.
3. The Resolved ReadModel for a monster includes the direct URL to its token.
4. The system supports `required: True` for media links (e.g., a "Map" entry MUST have an image).

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/content -k media_resolution`
