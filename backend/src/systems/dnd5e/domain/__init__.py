from .authorization import (
    AuthorizationResult,
    check_actor_exists,
    check_actor_alive,
    check_user_role_allowed,
    check_actor_ownership,
    check_turn_ownership,
    combine_authorization_checks,
)
from .action_economy import (
    ActionBudgetCheckResult,
    normalize_action_type,
    can_spend_action_budget,
    apply_action_budget_consumption,
    get_or_create_in_memory_budget,
)
from .action_resolution_pipeline import (
    ActionResolutionRequest,
    ActionResolutionContext,
    ActionResolutionDenial,
    ActionResolutionSuccess,
)

__all__ = [
    "AuthorizationResult",
    "check_actor_exists",
    "check_actor_alive",
    "check_user_role_allowed",
    "check_actor_ownership",
    "check_turn_ownership",
    "combine_authorization_checks",
    "ActionBudgetCheckResult",
    "normalize_action_type",
    "can_spend_action_budget",
    "apply_action_budget_consumption",
    "get_or_create_in_memory_budget",
    "ActionResolutionRequest",
    "ActionResolutionContext",
    "ActionResolutionDenial",
    "ActionResolutionSuccess",
]
