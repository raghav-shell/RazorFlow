"""Wait and Reassess Strategy implementation."""

from typing import Any

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import FailureCategory, RecoveryActionType
from packages.domain.strategies.base import BaseRecoveryStrategy, StrategyEvaluation
from packages.domain.value_objects import MonetaryAmount


class WaitAndReassessStrategy(BaseRecoveryStrategy):
    """
    Evaluates eligibility for postponing recovery actions to allow bank/gateway outages to clear.
    """

    @property
    def action_type(self) -> RecoveryActionType:
        return RecoveryActionType.WAIT_AND_REASSESS

    def evaluate(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        policy: Any,
    ) -> StrategyEvaluation:
        # Ineligible for fraud or permanent decline
        cat = case.failure_category
        cat_val = cat.value if isinstance(cat, FailureCategory) else cat
        if cat_val in (
            FailureCategory.FRAUD_RISK_BLOCK.value,
            FailureCategory.PERMANENT_INSTRUMENT_DECLINE.value,
        ):
            return StrategyEvaluation(
                is_eligible=False,
                ineligibility_reason="Permanent failures or fraud blocks cannot be postponed or reassessed",
                intervention_cost=MonetaryAmount.from_paise(0),
                risk_penalty=MonetaryAmount.from_paise(0),
                rationale="Ineligible for delay.",
                metadata={},
            )

        # Eligible primarily for transient infrastructure / bank downtime
        is_transient = case.is_transient or cat_val in (
            FailureCategory.BANK_SYSTEM_OUTAGE.value,
            FailureCategory.TECHNICAL_GATEWAY_TIMEOUT.value,
        )

        if not is_transient and case.current_attempt_count >= case.max_allowed_attempts:
            return StrategyEvaluation(
                is_eligible=False,
                ineligibility_reason="Non-transient failure with exhausted attempts",
                intervention_cost=MonetaryAmount.from_paise(0),
                risk_penalty=MonetaryAmount.from_paise(0),
                rationale="Ineligible for delay.",
                metadata={},
            )

        # Zero cost, zero risk
        intervention_cost = MonetaryAmount.from_paise(0)
        risk_penalty = MonetaryAmount.from_paise(0)

        rationale = (
            f"Postpone action and schedule reassessment for transient failure '{cat_val}' "
            f"to allow bank/gateway systems to stabilize."
        )

        return StrategyEvaluation(
            is_eligible=True,
            ineligibility_reason=None,
            intervention_cost=intervention_cost,
            risk_penalty=risk_penalty,
            rationale=rationale,
            metadata={"recommended_delay_minutes": 30},
        )
