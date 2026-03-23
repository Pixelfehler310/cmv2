# ISSUE: Database Integrity Constraints and Schema Drift Hardening

Status: Open  
Owner: Backend

## Summary

Material schema debt was identified while producing the database ERM specification. Several relationships are application-enforced only, key uniqueness guarantees are missing at DB level, and some type/default definitions are drift-prone.

## Affected Files and References

1. Additive startup backfill only (no full migration framework):

- backend/src/main.py:68
- backend/src/main.py:72
- backend/src/main.py:82

2. Social auth uniqueness and mutable JSON default:

- backend/src/identity/models.py:19
- backend/src/identity/models.py:24
- backend/src/identity/models.py:26

3. Campaign membership uniqueness missing:

- backend/src/campaigns/lib/campaign.py:14
- backend/src/campaigns/lib/campaign.py:17
- backend/src/campaigns/lib/campaign.py:18

4. Numeric type mismatch in SRD models:

- backend/src/data/lib/item.py:15
- backend/src/data/lib/monster.py:34
- backend/src/data/lib/monster.py:35

5. Faction model not part of active startup import graph:

- backend/src/campaigns/lib/faction.py:7
- backend/src/main.py:128

## Impact and Risk

1. Data integrity risks:

- Duplicate social auth identities and duplicate campaign memberships can be inserted under race conditions or out-of-band writes.

2. Referential drift risks:

- Catalog/session records and campaign context fields rely on soft references, allowing orphaned/mismatched rows if service-layer guards are bypassed.

3. Migration reliability risks:

- Current startup backfill handles only specific additive columns and does not provide a versioned, auditable migration path.

4. Type correctness risks:

- Fractional values for item weight/challenge rating may be truncated or represented inconsistently.

5. Environment consistency risks:

- Factions table creation depends on module import side effects and may be absent in fresh environments.

## In-Scope Fix List

1. Add DB constraints:

- Unique composite on user_social_auths(provider, provider_user_id).
- Unique composite on campaign_members(campaign_id, user_id).

2. Normalize JSON defaults:

- Replace literal mutable defaults with callable defaults where applicable.

3. Tighten numeric column types:

- Convert item.weight and monster.challenge_rating to explicit Float/Numeric as appropriate.

4. Ensure model registration consistency:

- Import/register faction model in startup metadata import path or establish explicit model package import bootstrap.

5. Define migration baseline:

- Introduce migration tooling and first migration set for constraints/type changes.

## Out-of-Scope Notes

1. Full redesign of all soft relationships to hard FK constraints across DnD5e context/catalog/session tables.
2. Historical data backfill strategy for all legacy environments.
3. Cross-service decomposition of persistence boundaries.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/campaigns -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -q
3. docker compose logs backend --tail=200
4. Optional DB checks:

- Verify unique constraints on social auth and campaign membership tables.
- Verify table existence for factions in fresh bootstrap.
- Verify numeric precision for item.weight and monster.challenge_rating writes/reads.
