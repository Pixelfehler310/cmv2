---
name: "dnd-business-logic-specialist"
description: "Manages the local-first Kanban board in ISSUES/FLOW/. Use this whenever you need to start, block, review, or complete a task."
---

## Purpose

This skill packages domain expertise for implementing, reviewing, and testing Dungeons & Dragons (5e) business logic in the backend of the CMV2 project. It focuses on correct rule interpretation, data-driven effect modelling, deterministic resolution pipelines, test strategies, and API/typing contracts that keep the backend as the single source of truth.

## Use when

- Designing or implementing damage, healing, saving-throw, and condition resolution logic.
- Creating an effect processor or extending the `effects` model on entities.
- Converting SRD or homebrew rules into data-driven JSON and `pydantic` models.
- Writing tests for rule correctness, edge cases, and deterministic simulations.
- Translating backend models into frontend types in `frontend/packages/types`.

## Scope & Responsibilities

- Provide canonical interpretations of ambiguous SRD rules relevant to engine behavior.
- Recommend data models and validation rules (must inherit from `pydantic.BaseModel`).
- Define action-resolution pipelines: targeting -> prechecks -> saves -> apply effects -> post-effects.
- Specify concurrency, transaction, and rollback behavior for multi-actor interactions.
- Create thorough test cases and property tests for probabilistic mechanics.
- Offer balancing heuristics and observability guidance (metrics, logs) for unexpected rule interactions.

## Constraints & Project Rules

- Backend is truth: never let frontend compute authoritative outcomes.
- Data-driven: prefer `effects: List[Effect]` rather than hard-coded branching logic.
- Microservice-ready: keep business logic decoupled from persistence; expose pure functions where possible.
- MVP Legacy Policy: do not preserve legacy behavior unless explicitly requested.
- All Python models should use `pydantic.BaseModel`.

## Implementation Guidance

1. Effect Processor Pattern
   - Represent abilities, spells, and attacks as declarative `Effect` objects.
   - Build a deterministic pipeline that accepts a `GameAction` and returns an `ActionResult`.
   - Steps: Resolve targeting -> Compute modifiers -> Roll/resolve saves -> Evaluate resistances/immunities -> Apply final state changes.

2. Determinism & Randomness
   - Provide an RNG abstraction that can be seeded for tests/simulations.
   - Expose pure functions for resolution that accept an RNG instance rather than calling `random` globally.

3. Stacking, Overwrites, and Precedence
   - Define explicit precedence rules (e.g., immunity > resistance > vulnerability).
   - Use versioned effect schemas to support future rule changes.

4. Transactions & Atomicity
   - Wrap multi-actor interactions in a single unit-of-work; on error, roll back state modifications.
   - Prefer in-memory simulation for conflict resolution, then persist final state.

5. Performance
   - Avoid eager expansion of large area-of-effect targeting; stream or paginate when evaluating many targets.
   - Cache derived stats (e.g., AC after temporary effects) for the duration of an action resolution.

## Data Model Suggestions (examples)

- `Effect` (base): type, source, duration, payload (damage, condition, buff), stacking rules.
- `GameAction`: actor_id, action_type, ability_used, targets, context (advantage/disadvantage, cover).
- `ActionResult`: changes (list of state diffs), logs (human-readable steps), resolved_rolls.

Example effect JSON

```json
{
  "id": "fireball-8d6",
  "type": "spell",
  "source": "fireball",
  "targeting": { "shape": "sphere", "radius_ft": 20 },
  "resolution": {
    "save": { "ability": "DEX", "on_fail": [{ "type": "damage", "dice": "8d6", "damage_type": "fire" }] }
  }
}
```

Pydantic snippet

```python
from pydantic import BaseModel
from typing import List, Optional

class DamagePayload(BaseModel):
    dice: str
    damage_type: str

class SaveSpec(BaseModel):
    ability: str
    dc_source: Optional[str]

class Effect(BaseModel):
    id: str
    type: str
    source: Optional[str]
    targeting: Optional[dict]
    resolution: Optional[dict]
    duration: Optional[str]
```

## Testing Guidance

- Unit tests: test each pipeline stage independently (targeting, save resolution, application).
- Integration tests: simulate full actions across multiple actors with deterministic RNG seeds.
- Property tests: verify invariants (e.g., hp never increases from damage application unless healed).
- Edge cases: concentration loss, simultaneous death, legendary reactions, reactions that interrupt other actions.

## Frontend Contract Notes

- Keep the frontend as a thin renderer: send human-readable `ActionResult.logs` for UI play-by-play.
- When models change, remember to update `frontend/packages/types` to match `backend/src/models`.

## Common Tasks (Use cases)

- Convert SRD spell entries to `Effect` JSON.
- Design a new `Effect` subtype for conditions that can stack with duration.
- Add comprehensive tests for a new mechanic (e.g., grapple/escape rules).
- Review existing code for rule drift or implicit assumptions.

## Do Not Use For

- General UX or CSS design tasks.
- Non-game domain business logic unrelated to combat/rules resolution.

## References

- SRD 5.1 rules as the canonical source for interpretations unless a campaign override exists.
- CMV2 architecture rules (backend truth, data-driven models).

## Contact pattern

When invoked, provide:

- A clear statement of the rule being implemented.
- A minimal `Effect` JSON example.
- Suggested `pydantic` model changes and test outlines.
- A brief note on frontend type changes required.
