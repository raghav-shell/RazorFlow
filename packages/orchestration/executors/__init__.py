"""Executor Registry."""

from typing import Dict, Type

from packages.domain.enums import RecoveryActionType
from packages.orchestration.executors.base import BaseActionExecutor
from packages.orchestration.executors.human_escalation_executor import HumanEscalationExecutor
from packages.orchestration.executors.payment_link_executor import PaymentLinkExecutor
from packages.orchestration.executors.payment_link_reminder_executor import (
    PaymentLinkReminderExecutor,
)
from packages.orchestration.executors.wait_and_reassess_executor import WaitAndReassessExecutor

_EXECUTOR_REGISTRY: Dict[RecoveryActionType, Type[BaseActionExecutor]] = {
    RecoveryActionType.PAYMENT_LINK: PaymentLinkExecutor,
    RecoveryActionType.CUSTOMER_REMINDER: PaymentLinkReminderExecutor,
    RecoveryActionType.WAIT_AND_REASSESS: WaitAndReassessExecutor,
    RecoveryActionType.HUMAN_ESCALATION: HumanEscalationExecutor,
}


def get_executor_for_action(action_type: RecoveryActionType) -> BaseActionExecutor:
    """Returns an instance of the executor for the specified action type."""
    cls = _EXECUTOR_REGISTRY.get(action_type)
    if not cls:
        raise ValueError(f"No registered executor for action type: '{action_type}'")
    return cls()
