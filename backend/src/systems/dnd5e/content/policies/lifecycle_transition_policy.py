from typing import Tuple

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
            LifecycleState.ARCHIVED,
        },
        LifecycleState.PUBLISHED: {
            LifecycleState.ARCHIVED,
            LifecycleState.SUPERSEDED,
            LifecycleState.DRAFT,  # E.g. unpublishing back to draft
        },
        LifecycleState.ARCHIVED: {
            LifecycleState.DRAFT,  # Restore back to draft
            LifecycleState.PUBLISHED, # Restore directly to active
        },
        LifecycleState.SUPERSEDED: set(), # Terminal state
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
        return current_state == LifecycleState.ARCHIVED

    @classmethod
    def can_supersede(cls, current_state: LifecycleState) -> bool:
        """Only published items can be formally superseded by a replacement chain"""
        return LifecycleState.SUPERSEDED in cls._VALID_TRANSITIONS[current_state]

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
