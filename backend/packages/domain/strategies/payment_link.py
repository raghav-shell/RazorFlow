"""Payment Link Recovery Strategy implementation."""

from typing import Any

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import FailureCategory, RecoveryActionType
from packages.domain.strategies.base import BaseRecoveryStrategy, StrategyEvaluation
from packages.domain.value_objects import MonetaryAmount


class PaymentLinkStrategy(BaseRecoveryStrategy):
    """
    Evaluates eligibility for generating and dispatching a new Hosted Payment Link.
    """

    @property
    def action_type(self) -> RecoveryActionType:
        return RecoveryActionType.PAYMENT_LINK

    def evaluate(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        policy: Any,
    ) -> StrategyEvaluation:
        # Ineligibility checks
        if case.current_attempt_count >= case.max_allowed_attempts:
            return StrategyEvaluation(
                is_eligible=False,
                ineligibility_reason="Max recovery attempts already reached for case",
                intervention_cost=MonetaryAmount.from_paise(200),  # ₹2.00
                risk_penalty=MonetaryAmount.from_paise(0),
                rationale="Ineligible due to attempt quota exhaustion.",
                metadata={},
            )

        if case.failure_category == FailureCategory.FRAUD_RISK_BLOCK.value:
            return StrategyEvaluation(
                is_eligible=False,
                ineligibility_reason="Cannot issue payment links for fraud/risk blocked transactions",
                intervention_cost=MonetaryAmount.from_paise(200),
                risk_penalty=MonetaryAmount.from_paise(10000),  # ₹100.00 risk penalty
                rationale="Blocked by fraud and risk protection policy.",
                metadata={},
            )

        if case.amount_at_risk_cents <= 0:
            return StrategyEvaluation(
                is_eligible=False,
                ineligibility_reason="Amount at risk must be greater than zero",
                intervention_cost=MonetaryAmount.from_paise(200),
                risk_penalty=MonetaryAmount.from_paise(0),
                rationale="Zero or negative amount at risk.",
                metadata={},
            )

        # Cost: standard SMS / Gateway API fee overhead ₹2.00 (200 paise)
        intervention_cost = MonetaryAmount.from_paise(200)

        # Risk penalty: higher if customer has chronic failure rate
        if context.historical_failure_count >= 5 and context.historical_success_count == 0:
            risk_penalty = MonetaryAmount.from_paise(500)  # ₹5.00
        else:
            risk_penalty = MonetaryAmount.from_paise(50)  # ₹0.50

        rationale = (
            f"Generate hosted Razorpay payment link for ₹{case.amount_at_risk_cents / 100:.2f} "
            f"addressing failure category '{case.failure_category}'."
        )

        return StrategyEvaluation(
            is_eligible=True,
            ineligibility_reason=None,
            intervention_cost=intervention_cost,
            risk_penalty=risk_penalty,
            rationale=rationale,
            metadata={"link_validity_hours": 24},
        )
