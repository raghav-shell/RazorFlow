"""Human Escalation Strategy implementation."""

from typing import Any

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import RecoveryActionType
from packages.domain.strategies.base import BaseRecoveryStrategy, StrategyEvaluation
from packages.domain.value_objects import MonetaryAmount


class HumanEscalationStrategy(BaseRecoveryStrategy):
    """
    Evaluates eligibility for routing high-value or high-risk cases to human operations.
    """

    @property
    def action_type(self) -> RecoveryActionType:
        return RecoveryActionType.HUMAN_ESCALATION

    def evaluate(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        policy: Any,
    ) -> StrategyEvaluation:
        # High value or repeated failures or high customer risk tier
        threshold = getattr(
            policy, "high_value_escalation_threshold_cents", 5000000
        )  # ₹50,000 default
        is_high_value = case.amount_at_risk_cents >= threshold
        is_chronic_failure = (
            case.current_attempt_count >= 1 and context.historical_failure_count >= 3
        )
        is_vip = (
            getattr(context, "customer_risk_tier", "") == "LOW_RISK_VIP"
            and case.amount_at_risk_cents >= 1000000
        )

        is_eligible = (
            is_high_value or is_chronic_failure or is_vip or case.amount_at_risk_cents >= 2000000
        )

        # Cost: human support operator manual review ~ ₹100.00 (10000 paise)
        intervention_cost = MonetaryAmount.from_paise(10000)
        risk_penalty = MonetaryAmount.from_paise(0)

        if is_eligible:
            rationale = (
                f"Route case (Amount: ₹{case.amount_at_risk_cents / 100:.2f}) to merchant human concierge/support "
                f"for high-touch manual handling."
            )
        else:
            rationale = "Order value and risk profile do not meet threshold for human escalation."

        return StrategyEvaluation(
            is_eligible=is_eligible,
            ineligibility_reason=None
            if is_eligible
            else "Does not meet high-value or concierge criteria",
            intervention_cost=intervention_cost,
            risk_penalty=risk_penalty,
            rationale=rationale,
            metadata={
                "escalation_queue": "priority_support" if is_high_value else "standard_support"
            },
        )
