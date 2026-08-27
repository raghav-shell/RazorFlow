"""Do Nothing Recovery Strategy implementation."""

from typing import Any

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import RecoveryActionType
from packages.domain.strategies.base import BaseRecoveryStrategy, StrategyEvaluation
from packages.domain.value_objects import MonetaryAmount


class DoNothingStrategy(BaseRecoveryStrategy):
    """
    Evaluates fallback when no active intervention is appropriate, safe, or cost-effective.
    """

    @property
    def action_type(self) -> RecoveryActionType:
        return RecoveryActionType.DO_NOTHING

    def evaluate(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        policy: Any,
    ) -> StrategyEvaluation:
        return StrategyEvaluation(
            is_eligible=True,
            ineligibility_reason=None,
            intervention_cost=MonetaryAmount.from_paise(0),
            risk_penalty=MonetaryAmount.from_paise(0),
            rationale="No active recovery intervention authorized or necessary.",
            metadata={},
        )
