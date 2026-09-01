"""Customer Reminder Recovery Strategy implementation."""

from typing import Any

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import RecoveryActionType
from packages.domain.strategies.base import BaseRecoveryStrategy, StrategyEvaluation
from packages.domain.value_objects import MonetaryAmount


class CustomerReminderStrategy(BaseRecoveryStrategy):
    """
    Evaluates eligibility for dispatching a follow-up reminder for an existing active payment link.
    """

    @property
    def action_type(self) -> RecoveryActionType:
        return RecoveryActionType.CUSTOMER_REMINDER

    def evaluate(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        policy: Any,
    ) -> StrategyEvaluation:
        # Crucial Invariant: Reminder is structurally impossible without an active payment link!
        has_active_link = getattr(context, "has_active_payment_link", False) or (
            case.metadata_json.get("active_payment_link_id") is not None
        )
        if not has_active_link:
            return StrategyEvaluation(
                is_eligible=False,
                ineligibility_reason="No active payment link exists to send a reminder for",
                intervention_cost=MonetaryAmount.from_paise(150),
                risk_penalty=MonetaryAmount.from_paise(0),
                rationale="Ineligible because no active payment link is currently open.",
                metadata={},
            )

        if case.current_attempt_count >= case.max_allowed_attempts:
            return StrategyEvaluation(
                is_eligible=False,
                ineligibility_reason="Max recovery attempts exceeded for case",
                intervention_cost=MonetaryAmount.from_paise(150),
                risk_penalty=MonetaryAmount.from_paise(0),
                rationale="Ineligible due to attempt quota exhaustion.",
                metadata={},
            )

        # Cost: SMS / WhatsApp notification fee ~ ₹1.50 (150 paise)
        intervention_cost = MonetaryAmount.from_paise(150)
        # Risk penalty: customer notification friction ~ ₹1.00 (100 paise)
        risk_penalty = MonetaryAmount.from_paise(100)

        rationale = "Dispatch notification reminder to customer for pending open payment link."

        return StrategyEvaluation(
            is_eligible=True,
            ineligibility_reason=None,
            intervention_cost=intervention_cost,
            risk_penalty=risk_penalty,
            rationale=rationale,
            metadata={"medium": "sms"},
        )
