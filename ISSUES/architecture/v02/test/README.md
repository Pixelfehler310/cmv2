# V02 Test Sequence Diagram Pack

Status: Draft test-design artifacts for backend implementation planning.

This folder contains five concrete DnD encounter sequence diagrams intended to drive deterministic and interrupt-aware test authoring for V02.
Each diagram includes explicit AC/DC checks, manual roll entry via pending_roll, and calculable damage and effect deltas.

Eventing policy in this test pack:

1. Public gameplay lane: pending_choice, pending_roll, attack and save outcomes, actor impact, turn budget updates, terminal action result.
2. Internal trace lane: graph build and target resolution stage lifecycle details are internal diagnostics, not default client events.

## Diagram Index

1. `V02_test_seq_01_deterministic_single_attack_baseline.mmd`
   - Baseline deterministic explicit-target attack (no interrupts).
2. `V02_test_seq_02_reaction_interrupt_window_on_hit.mmd`
   - On-hit reaction interrupt with taken/declined branches.
3. `V02_test_seq_03_pending_choice_pause_resume_smite.mmd`
   - Pending-choice pause/resume with automation bypass and manual continuation.
4. `V02_test_seq_04_unlock_mutation_and_followup_action.mmd`
   - Outcome-triggered unlock mutation (`unlocked_action_refs`) and optional follow-up action.
5. `V02_test_seq_05_deferred_zone_tick_and_cleanup_lifecycle.mmd`
   - Deferred zone creation, end-turn ticks, concentration break, and deterministic cleanup.

## Intended Test Family Mapping

1. Seq 01 -> Deterministic baseline action execution tests.
2. Seq 02 -> Reaction interrupt handling tests.
3. Seq 03 -> Pending-choice contract and continuation tests.
4. Seq 04 -> Unlock pattern and turn budget mutation tests.
5. Seq 05 -> Deferred/tick lifecycle and concentration cleanup tests.

## Shared Test Invariants

1. Every command has one terminal outcome (`resolved`, `denied`, `error`, `pending_choice`, or `pending_roll` then resumed to terminal state).
2. Every mutation is attributable to `request_id` and `operation_id` where applicable.
3. Event order is deterministic and replay-safe under identical input state.
4. `state_revision` increments exactly once per successful terminal command.
