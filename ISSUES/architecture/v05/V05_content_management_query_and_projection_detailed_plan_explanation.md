# V05 Detailed Plan Explanation: Query, Linked-Entry Resolution, and Projection Contracts

This file explains the architecture in:

- V05_content_management_query_and_projection_detailed_plan.mmd

## 1. Runtime Structure Overview

This module is structured into four runtime planes:

1. Contract plane
- Validates input envelopes and produces terminal denied envelopes early.

2. Execution plane
- Runs query or mutation pipelines with deterministic stage order.

3. Projection plane
- Emits projection/invalidation events and applies them in frontend stores.

4. Recovery plane
- Handles revision/schema drift and deterministic resync.

Why this structure:

1. It separates "can this request run" from "how it runs" and "how clients converge".
2. It gives explicit places for denial, mutation, eventing, and recovery logic.

## 2. Structural Mapping Of Namespaces

## RequestContracts (contract plane)

Role:

1. Define all entry envelopes.
2. Reject malformed or ambiguous payloads.

Critical boundary:

1. Nothing enters QueryAndMutationPipeline without passing RequestValidationPolicy.

## QueryAndMutationPipeline (execution plane)

Role:

1. Orchestrate staged runtime behavior.

Stage order:

1. Validate
2. Authorize
3. Execute query or mutation
4. Resolve links (if requested)
5. Build projection
6. Finalize response and event set

Structural rule:

1. MutationStage is the only stage allowed to create a new revision.

## EventContracts (projection plane contract)

Role:

1. Define outbound event shapes for updates, invalidation, and denied outcomes.

Structural rule:

1. Stores consume events, but do not infer backend rules from missing fields.

## ProjectionConsumers (projection plane runtime)

Role:

1. Maintain UI-facing caches.
2. Apply event-driven updates.
3. Trigger targeted refetch on revision policy violations.

Structural rule:

1. ProjectionConsistencyPolicy is the only place deciding revision-gap response behavior.

## RecoveryAndObservability (recovery plane)

Role:

1. Detect drift.
2. Trigger invalidation/resync.
3. Record auditable request traces.

Structural rule:

1. Drift handling is explicit policy, never ad hoc in UI components.

## TestingAndGate (quality plane)

Role:

1. Enforce deterministic runtime behavior and convergence guarantees.

Structural rule:

1. V05ProjectionGate fails if any plane-specific test group fails.

## 3. Structural Boundaries And Allowed Calls

Allowed call graph:

1. RequestContracts -> QueryAndMutationPipeline
2. QueryAndMutationPipeline -> EventContracts
3. EventContracts -> ProjectionConsumers
4. ProjectionConsumers -> RecoveryAndObservability (through policy triggers)

Forbidden call graph:

1. ProjectionConsumers -> MutationStage direct mutation
2. RequestValidationPolicy -> store mutation
3. Recovery policy -> bypassing envelope contracts

Why this matters:

1. Prevents cache behavior from mutating source-of-truth state.
2. Prevents transport-layer shortcuts that skip validation.

## 4. Data Consistency Structure

Consistency model used here:

1. Revision snapshot consistency for reads.
2. Monotonic revision increments for writes.
3. Event-carried revision context for consumers.
4. Invalidation + targeted refetch on gaps.

Who owns each consistency decision:

1. QueryStage owns snapshot selection.
2. MutationStage owns revision creation.
3. ProjectionConsistencyPolicy owns gap detection.
4. DriftRecoveryPolicy owns resync strategy.

## 5. Concrete Runtime Flows As Structure

## Query flow structure

1. Envelope object created.
2. Validation gate.
3. QueryStage executes against fixed revision.
4. Optional LinkResolutionStage expansion.
5. ProjectionStage maps result for UI.
6. FinalResultEnvelope returns with revision metadata.

Guarantee:

1. Same input + same revision => same result ordering and equivalent payload semantics.

## Mutation flow structure

1. Envelope object created.
2. Validation gate.
3. MutationStage writes source state.
4. MutationStage creates new revision.
5. ProjectionStage emits update/invalidation events.
6. FinalResultEnvelope returns terminal status.

Guarantee:

1. One successful mutation corresponds to one coherent revision change.

## Character-sheet lookup structure

1. CharacterSheetLookupEnvelope enters contract plane.
2. LinkResolutionStage resolves refs and replacements.
3. CharacterSheetStore caches by revision.
4. Incoming higher revision triggers targeted invalidation.
5. Refetch restores convergence.

Guarantee:

1. Character sheet and content manager converge on same canonical reference targets.

## 6. Proposed Implementation Layout (Concrete Structure)

This is a suggested code layout for this runtime structure.

frontend/packages/content-runtime/
	contracts/
		envelopes.ts
		resultEnvelope.ts
		events.ts
	pipeline/
		contentPipeline.ts
		queryStage.ts
		linkResolutionStage.ts
		mutationStage.ts
		projectionStage.ts
	stores/
		contentManagerStore.ts
		characterSheetStore.ts
	consistency/
		projectionConsistencyPolicy.ts
		driftRecoveryPolicy.ts
	observability/
		auditLog.ts
		checkpoint.ts
	tests/
		queryContract.test.ts
		mutationContract.test.ts
		linkResolution.test.ts
		projectionConsistency.test.ts

Note:

1. This is structural guidance, not a required exact path.

## 7. Most Important Structural Rules To Keep

1. Envelopes are mandatory at every entrypoint.
2. Stage order is fixed and test-protected.
3. Revision creation only in mutation path.
4. Invalidation is explicit via event contracts.
5. Stores apply consistency policy, not business rules.
6. Recovery is policy-driven, not manual.

## 8. Why This Should Be Built This Way

1. It keeps content behavior deterministic under frequent edits.
2. It supports hybrid-play usage where fast trustworthy lookup is critical.
3. It avoids stale split-state between multiple open views.
4. It makes failures diagnosable by runtime plane.
5. It enables phased delivery: contracts first, then pipeline, then projection, then recovery.

## 9. If You Only Remember Five Things

1. Contract plane rejects bad input before logic runs.
2. Execution plane owns mutation and revision changes.
3. Projection plane owns cache convergence behavior.
4. Recovery plane owns resync and drift handling.
5. Gate tests are the architecture lock, not optional polish.