"""Base Recovery Strategy interface and metadata dataclasses."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import RecoveryActionType
from packages.domain.value_objects import MonetaryAmount


@dataclass(frozen=True)
class StrategyEvaluation:
    """Outcome of a pure strategy eligibility and cost assessment."""

    is_eligible: bool
    ineligibility_reason: str | None
    intervention_cost: MonetaryAmount
    risk_penalty: MonetaryAmount
    rationale: str
    metadata: Dict[str, Any]


class BaseRecoveryStrategy(ABC):
    """
    Pure domain strategy definition.
    Zero DB, zero Razorpay, zero Redis, zero network I/O.
    """

    @property
    @abstractmethod
    def action_type(self) -> RecoveryActionType:
        """The specific RecoveryActionType this strategy governs."""
        pass

    @abstractmethod
    def evaluate(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        policy: Any,
    ) -> StrategyEvaluation:
        """
        Pure deterministic evaluation of eligibility, cost, risk penalty, and rationale.
        """
        pass
