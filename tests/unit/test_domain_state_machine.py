"""Unit tests for CaseStateMachine and AttemptStateMachine."""

import pytest

from packages.domain.enums import RecoveryAttemptStatus, RecoveryCaseStatus
from packages.domain.state_machine import (
    AttemptStateMachine,
    CaseStateMachine,
    InvalidStateTransitionError,
)


def test_valid_case_lifecycle_progression():
    # DETECTED -> ENRICHING -> DIAGNOSING -> STRATEGY_GENERATED -> POLICY_CHECK_PENDING -> APPROVED -> EXECUTING -> WAITING_EXTERNAL -> VERIFYING -> RECOVERED
    assert CaseStateMachine.can_transition(
        RecoveryCaseStatus.DETECTED, RecoveryCaseStatus.ENRICHING
    )
    assert CaseStateMachine.can_transition(
        RecoveryCaseStatus.ENRICHING, RecoveryCaseStatus.DIAGNOSING
    )
    assert CaseStateMachine.can_transition(
        RecoveryCaseStatus.DIAGNOSING, RecoveryCaseStatus.STRATEGY_GENERATED
    )
    assert CaseStateMachine.can_transition(
        RecoveryCaseStatus.STRATEGY_GENERATED, RecoveryCaseStatus.POLICY_CHECK_PENDING
    )
    assert CaseStateMachine.can_transition(
        RecoveryCaseStatus.POLICY_CHECK_PENDING, RecoveryCaseStatus.APPROVED
    )
    assert CaseStateMachine.can_transition(
        RecoveryCaseStatus.APPROVED, RecoveryCaseStatus.EXECUTING
    )
    assert CaseStateMachine.can_transition(
        RecoveryCaseStatus.EXECUTING, RecoveryCaseStatus.WAITING_EXTERNAL
    )
    assert CaseStateMachine.can_transition(
        RecoveryCaseStatus.WAITING_EXTERNAL, RecoveryCaseStatus.VERIFYING
    )
    assert CaseStateMachine.can_transition(
        RecoveryCaseStatus.VERIFYING, RecoveryCaseStatus.RECOVERED
    )


def test_invalid_case_leap_raises_error():
    # Cannot jump directly from DETECTED to RECOVERED or EXECUTING
    assert not CaseStateMachine.can_transition(
        RecoveryCaseStatus.DETECTED, RecoveryCaseStatus.RECOVERED
    )
    assert not CaseStateMachine.can_transition(
        RecoveryCaseStatus.DETECTED, RecoveryCaseStatus.EXECUTING
    )

    with pytest.raises(InvalidStateTransitionError):
        CaseStateMachine.validate_transition(
            RecoveryCaseStatus.DETECTED, RecoveryCaseStatus.RECOVERED
        )


def test_terminal_case_states_have_zero_transitions():
    assert CaseStateMachine.ALLOWED_TRANSITIONS[RecoveryCaseStatus.RECOVERED] == set()
    assert CaseStateMachine.ALLOWED_TRANSITIONS[RecoveryCaseStatus.UNRECOVERABLE] == set()
    assert CaseStateMachine.ALLOWED_TRANSITIONS[RecoveryCaseStatus.EXPIRED] == set()
    assert CaseStateMachine.ALLOWED_TRANSITIONS[RecoveryCaseStatus.STOPPED] == set()

    with pytest.raises(InvalidStateTransitionError):
        CaseStateMachine.validate_transition(
            RecoveryCaseStatus.RECOVERED, RecoveryCaseStatus.DIAGNOSING
        )


def test_attempt_state_machine_transitions():
    assert AttemptStateMachine.can_transition(
        RecoveryAttemptStatus.DRAFT, RecoveryAttemptStatus.DISPATCHED
    )
    assert AttemptStateMachine.can_transition(
        RecoveryAttemptStatus.DISPATCHED, RecoveryAttemptStatus.SUCCEEDED
    )
    assert AttemptStateMachine.can_transition(
        RecoveryAttemptStatus.DISPATCHED, RecoveryAttemptStatus.FAILED
    )

    # Terminal attempt state
    assert not AttemptStateMachine.can_transition(
        RecoveryAttemptStatus.SUCCEEDED, RecoveryAttemptStatus.DISPATCHED
    )
    with pytest.raises(InvalidStateTransitionError):
        AttemptStateMachine.validate_transition(
            RecoveryAttemptStatus.SUCCEEDED, RecoveryAttemptStatus.DRAFT
        )
