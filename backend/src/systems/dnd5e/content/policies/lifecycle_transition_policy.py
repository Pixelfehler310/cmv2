__production_status__ = "gold"

from ..domain.primitives import LifecycleState
from ..domain.invariants import CompendiumErrorCode


class ContentLifecycleError(ValueError):
    def __init__(self, message: str):
        super().__init__(f"{CompendiumErrorCode.INVALID_LIFECYCLE_TRANSITION.value}: {message}")


class LifecycleTransitionPolicy:
    """Enforces correctness of transitions between content lifecycle states."""

    _VALID_TRANSITIONS = {
        LifecycleState.DRAFT: {
            LifecycleState.PUBLISHED,
        },
        LifecycleState.PUBLISHED: {
            LifecycleState.ARCHIVED,
            LifecycleState.SUPERSEDED,
        },
        LifecycleState.ARCHIVED: {
            LifecycleState.PUBLISHED,
        },
        LifecycleState.SUPERSEDED: set(),
    }

    @classmethod
    def can_publish(cls, current_state: LifecycleState) -> bool:
        return LifecycleState.PUBLISHED in cls._VALID_TRANSITIONS[current_state]

    @classmethod
    def can_archive(cls, current_state: LifecycleState) -> bool:
        return LifecycleState.ARCHIVED in cls._VALID_TRANSITIONS[current_state]

    @classmethod
    def can_restore(cls, current_state: LifecycleState) -> bool:
        """Archived items can be restored"""
        return LifecycleState.PUBLISHED in cls._VALID_TRANSITIONS[current_state]

    @classmethod
    def can_supersede(cls, current_state: LifecycleState) -> bool:
        """Only published items can be formally superseded by a replacement chain"""
        return LifecycleState.SUPERSEDED in cls._VALID_TRANSITIONS[current_state]

    @classmethod
    def validate_transition(
        cls,
        *,
        current_state: LifecycleState,
        target_state: LifecycleState,
    ) -> None:
        cls.deny_on_invalid_transition(current_state, target_state)

    @classmethod
    def validate_supersedence(
        cls,
        *,
        source_state: LifecycleState,
        replacement_state: LifecycleState,
    ) -> None:
        cls.deny_on_invalid_transition(source_state, LifecycleState.SUPERSEDED)
        if replacement_state == LifecycleState.DRAFT:
            raise ContentLifecycleError(
                "Supersedence replacement target cannot be in draft state."
            )

    @classmethod
    def validate_delete_permission(cls, *, state: LifecycleState) -> None:
        if state != LifecycleState.DRAFT:
            raise ContentLifecycleError(
                f"Delete denied for lifecycle_state={state.value}; only draft definitions may be deleted."
            )

    @classmethod
    def deny_on_invalid_transition(
        cls, current_state: LifecycleState, target_state: LifecycleState
    ) -> None:
        """Raises ContentLifecycleError if the transition is illegal."""
        if current_state == target_state:
            return  # No-op

        valid_targets = cls._VALID_TRANSITIONS.get(current_state, set())
        if target_state not in valid_targets:
            raise ContentLifecycleError(
                f"Cannot transition from {current_state.value} to {target_state.value}."
            )
