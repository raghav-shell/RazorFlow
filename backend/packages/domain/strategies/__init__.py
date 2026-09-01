"""Strategy Registry exporting all domain recovery strategies."""

from typing import Dict, List

from packages.domain.enums import RecoveryActionType
from packages.domain.strategies.base import BaseRecoveryStrategy, StrategyEvaluation
from packages.domain.strategies.customer_reminder import CustomerReminderStrategy
from packages.domain.strategies.do_nothing import DoNothingStrategy
from packages.domain.strategies.human_escalation import HumanEscalationStrategy
from packages.domain.strategies.payment_link import PaymentLinkStrategy
from packages.domain.strategies.wait_and_reassess import WaitAndReassessStrategy

_STRATEGY_REGISTRY: Dict[RecoveryActionType, BaseRecoveryStrategy] = {
    RecoveryActionType.PAYMENT_LINK: PaymentLinkStrategy(),
    RecoveryActionType.CUSTOMER_REMINDER: CustomerReminderStrategy(),
    RecoveryActionType.WAIT_AND_REASSESS: WaitAndReassessStrategy(),
    RecoveryActionType.HUMAN_ESCALATION: HumanEscalationStrategy(),
    RecoveryActionType.DO_NOTHING: DoNothingStrategy(),
}


def get_recovery_strategy(action_type: RecoveryActionType) -> BaseRecoveryStrategy:
    """Retrieves the pure domain strategy implementation for a specific action type."""
    strategy = _STRATEGY_REGISTRY.get(action_type)
    if strategy is None:
        raise KeyError(f"No registered recovery strategy found for action type '{action_type}'.")
    return strategy


def get_all_recovery_strategies() -> List[BaseRecoveryStrategy]:
    """Returns all registered domain recovery strategies in deterministic order."""
    return list(_STRATEGY_REGISTRY.values())


__all__ = [
    "BaseRecoveryStrategy",
    "StrategyEvaluation",
    "PaymentLinkStrategy",
    "CustomerReminderStrategy",
    "WaitAndReassessStrategy",
    "HumanEscalationStrategy",
    "DoNothingStrategy",
    "get_recovery_strategy",
    "get_all_recovery_strategies",
]
