"""Pure deterministic state machine enforcing allowed lifecycle transitions."""

from typing import Dict, Set

from packages.domain.enums import RecoveryAttemptStatus, RecoveryCaseStatus


class InvalidStateTransitionError(ValueError):
    """Raised when an invalid state transition is requested."""

    pass


class CaseStateMachine:
    """
    Formal state machine for RecoveryCase aggregates.
    Guarantees strict financial state transitions and prevents invalid leaps.
    """

    ALLOWED_TRANSITIONS: Dict[RecoveryCaseStatus, Set[RecoveryCaseStatus]] = {
        RecoveryCaseStatus.DETECTED: {
            RecoveryCaseStatus.ENRICHING,
            RecoveryCaseStatus.UNRECOVERABLE,
            RecoveryCaseStatus.STOPPED,
        },
        RecoveryCaseStatus.ENRICHING: {
            RecoveryCaseStatus.DIAGNOSING,
            RecoveryCaseStatus.UNRECOVERABLE,
            RecoveryCaseStatus.STOPPED,
        },
        RecoveryCaseStatus.DIAGNOSING: {
            RecoveryCaseStatus.STRATEGY_GENERATED,
            RecoveryCaseStatus.UNRECOVERABLE,
            RecoveryCaseStatus.STOPPED,
        },
        RecoveryCaseStatus.STRATEGY_GENERATED: {
            RecoveryCaseStatus.POLICY_CHECK_PENDING,
            RecoveryCaseStatus.STOPPED,
        },
        RecoveryCaseStatus.POLICY_CHECK_PENDING: {
            RecoveryCaseStatus.APPROVED,
            RecoveryCaseStatus.REJECTED,
            RecoveryCaseStatus.ESCALATED,
        },
        RecoveryCaseStatus.APPROVED: {
            RecoveryCaseStatus.EXECUTING,
            RecoveryCaseStatus.WAITING_EXTERNAL,
            RecoveryCaseStatus.STOPPED,
        },
        RecoveryCaseStatus.REJECTED: {
            RecoveryCaseStatus.STOPPED,
            RecoveryCaseStatus.UNRECOVERABLE,
        },
        RecoveryCaseStatus.ESCALATED: {
            RecoveryCaseStatus.APPROVED,  # Manual human approval
            RecoveryCaseStatus.STOPPED,  # Manual human rejection
            RecoveryCaseStatus.UNRECOVERABLE,
        },
        RecoveryCaseStatus.EXECUTING: {
            RecoveryCaseStatus.WAITING_EXTERNAL,
            RecoveryCaseStatus.VERIFYING,
            RecoveryCaseStatus.UNRECOVERABLE,
            RecoveryCaseStatus.STOPPED,
        },
        RecoveryCaseStatus.WAITING_EXTERNAL: {
            RecoveryCaseStatus.VERIFYING,
            RecoveryCaseStatus.DIAGNOSING,  # Reassessment loop after failure or cooldown
            RecoveryCaseStatus.EXPIRED,
            RecoveryCaseStatus.STOPPED,
        },
        RecoveryCaseStatus.VERIFYING: {
            RecoveryCaseStatus.RECOVERED,
            RecoveryCaseStatus.DIAGNOSING,  # Verification failed -> reassess if retries left
            RecoveryCaseStatus.UNRECOVERABLE,
            RecoveryCaseStatus.STOPPED,
        },
        # Terminal states
        RecoveryCaseStatus.RECOVERED: set(),
        RecoveryCaseStatus.UNRECOVERABLE: set(),
        RecoveryCaseStatus.EXPIRED: set(),
        RecoveryCaseStatus.STOPPED: set(),
    }

    @classmethod
    def can_transition(cls, current: RecoveryCaseStatus, target: RecoveryCaseStatus) -> bool:
        """Returns True if transition is legally allowed, False otherwise."""
        return target in cls.ALLOWED_TRANSITIONS.get(current, set())

    @classmethod
    def validate_transition(cls, current: RecoveryCaseStatus, target: RecoveryCaseStatus) -> None:
        """Raises InvalidStateTransitionError if transition is disallowed."""
        if not cls.can_transition(current, target):
            raise InvalidStateTransitionError(
                f"Cannot transition RecoveryCase from {current.value} to {target.value}"
            )


class AttemptStateMachine:
    """
    Formal state machine for individual physical RecoveryAttempts.
    """

    ALLOWED_TRANSITIONS: Dict[RecoveryAttemptStatus, Set[RecoveryAttemptStatus]] = {
        RecoveryAttemptStatus.DRAFT: {
            RecoveryAttemptStatus.DISPATCHED,
            RecoveryAttemptStatus.FAILED,
        },
        RecoveryAttemptStatus.DISPATCHED: {
            RecoveryAttemptStatus.ACKNOWLEDGED,
            RecoveryAttemptStatus.SUCCEEDED,
            RecoveryAttemptStatus.FAILED,
            RecoveryAttemptStatus.TIMED_OUT,
        },
        RecoveryAttemptStatus.ACKNOWLEDGED: {
            RecoveryAttemptStatus.SUCCEEDED,
            RecoveryAttemptStatus.FAILED,
            RecoveryAttemptStatus.TIMED_OUT,
        },
        RecoveryAttemptStatus.SUCCEEDED: set(),
        RecoveryAttemptStatus.FAILED: set(),
        RecoveryAttemptStatus.TIMED_OUT: set(),
    }

    @classmethod
    def can_transition(cls, current: RecoveryAttemptStatus, target: RecoveryAttemptStatus) -> bool:
        return target in cls.ALLOWED_TRANSITIONS.get(current, set())

    @classmethod
    def validate_transition(
        cls, current: RecoveryAttemptStatus, target: RecoveryAttemptStatus
    ) -> None:
        if not cls.can_transition(current, target):
            raise InvalidStateTransitionError(
                f"Cannot transition RecoveryAttempt from {current.value} to {target.value}"
            )
