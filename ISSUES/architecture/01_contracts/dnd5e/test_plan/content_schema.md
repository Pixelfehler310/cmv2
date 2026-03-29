# Test Plan: DND5E-02 Content Schema

## Unit Targets
1. `DefinitionRecord` field validation.
2. Family-specific schema validation.
3. `ContentPackRecord` lifecycle field validation.

## Invariants
1. `content_version` is >= 1.
2. Family-specific fields are required when family matches.
3. `lifecycle_state` uses canonical enum values.

## Edge Cases
1. Wrong family discriminator for payload.
2. Negative `content_version`.
3. Missing required provenance fields.

## Expected Results
1. Schema violations return `VALIDATION_FAILED`.
2. Discriminator mismatches are denied deterministically.
