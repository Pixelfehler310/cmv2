# Content Pack Fixtures

Drop JSON content pack files in this directory to load them through:

- startup mock-data import (`LOAD_MOCK_DATA=true`), or
- `POST /api/dev/load-seeds`.

Each file must contain one content-pack object compatible with
`src.systems.dnd5e.schemas.contracts.ContentPack`.

Conflict policy defaults to `reject_conflict` during seed loading.
