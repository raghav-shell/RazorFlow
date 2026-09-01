"""Unit tests for domain enums."""

from packages.domain.enums import (
    OrderStatus,
    PaymentStatus,
    RecoveryActionType,
    RecoveryCaseStatus,
)


def test_order_status_values():
    assert OrderStatus.CREATED.value == "CREATED"
    assert OrderStatus.PAID.value == "PAID"
    assert OrderStatus.CANCELLED.value == "CANCELLED"


def test_payment_status_values():
    assert PaymentStatus.CAPTURED.value == "CAPTURED"
    assert PaymentStatus.FAILED.value == "FAILED"


def test_recovery_case_status_terminal_states():
    terminal_statuses = {
        RecoveryCaseStatus.RECOVERED,
        RecoveryCaseStatus.UNRECOVERABLE,
        RecoveryCaseStatus.EXPIRED,
        RecoveryCaseStatus.STOPPED,
    }
    assert len(terminal_statuses) == 4


def test_recovery_action_types():
    actions = {
        RecoveryActionType.PAYMENT_LINK,
        RecoveryActionType.CUSTOMER_REMINDER,
        RecoveryActionType.WAIT_AND_REASSESS,
        RecoveryActionType.HUMAN_ESCALATION,
        RecoveryActionType.DO_NOTHING,
    }
    assert len(actions) == 5
