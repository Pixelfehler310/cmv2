"""Canonical denial reason codes for combat command/event contracts.

These constants are a shared taxonomy foundation for contract evolution.
Runtime paths can adopt these incrementally without behavior change in this PR.
"""

from __future__ import annotations


ACTION_DENIED_REASON_CODES: set[str] = {
    "not_your_turn",
    "not_owner",
    "budget_exhausted",
    "invalid_action",
    "invalid_actor",
    "invalid_target",
    "invalid_message",
    "forbidden",
    "invalid_turn_phase",
    "no_active_actor",
    "movement_exhausted",
    "action_exhausted",
    "bonus_action_exhausted",
    "reaction_exhausted",
    "unsupported_action",
    "effect_not_found",
    "target_immune",
    "target_invalid",
    "concentration_conflict",
    "stacking_limit_reached",
    "invalid_duration",
    "unsupported_effect_operation",
    "invalid_template_origin",
    "invalid_template_direction",
    "template_out_of_range",
    "no_resolved_targets",
    "target_not_in_template",
    "target_no_longer_eligible",
    "line_of_effect_blocked",
}


COMMAND_DENIED_REASON_CODES: set[str] = {
    "forbidden",
    "invalid_message",
    "invalid_turn_phase",
    "no_active_actor",
    "not_your_turn",
    "not_owner",
    "movement_exhausted",
    "invalid_actor",
}
