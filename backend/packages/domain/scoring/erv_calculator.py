"""Expected Recovery Value (ERV) Calculator with pure integer-cents precision."""

import logging
from dataclasses import dataclass
from typing import Any

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import RecoveryActionType
from packages.domain.strategies import get_recovery_strategy
from packages.domain.value_objects import RecoveryProbability

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ERVResult:
    """Structured calculation result of Expected Net Recovery Value for a candidate action."""

    action: RecoveryActionType
    recovery_probability: RecoveryProbability
    amount_at_risk_cents: int
    gross_expected_recovery_cents: int
    intervention_cost_cents: int
    risk_penalty_cents: int
    expected_net_recovery_value_cents: int
    rationale: str


class ERVCalculator:
    """
    Computes Expected Recovery Value (ERV) mathematically using integer minor units (paise).
    Formula:
        Gross = int(P(recovery) * amount_at_risk_cents)
        ERV   = Gross - intervention_cost_cents - risk_penalty_cents
    """

    @classmethod
    def calculate_erv(
        cls,
        action: RecoveryActionType,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        probability: RecoveryProbability,
        policy: Any,
    ) -> ERVResult:
        """Calculates exact integer ERV for an action."""
        strategy = get_recovery_strategy(action)
        evaluation = strategy.evaluate(case=case, context=context, policy=policy)

        p = probability.value
        amount_cents = case.amount_at_risk_cents

        # Gross Expected Recovery in integer paise
        gross_cents = int(p * amount_cents)

        cost_cents = evaluation.intervention_cost.amount_in_cents
        risk_cents = evaluation.risk_penalty.amount_in_cents

        # Expected Net Recovery Value
        net_erv_cents = gross_cents - cost_cents - risk_cents

        rationale = (
            f"Action '{action.value}': P={p:.2f}, Gross=₹{gross_cents / 100:.2f}, "
            f"Cost=₹{cost_cents / 100:.2f}, Risk=₹{risk_cents / 100:.2f} -> Net ERV=₹{net_erv_cents / 100:.2f}. "
            f"Strategy rationale: {evaluation.rationale}"
        )

        return ERVResult(
            action=action,
            recovery_probability=probability,
            amount_at_risk_cents=amount_cents,
            gross_expected_recovery_cents=gross_cents,
            intervention_cost_cents=cost_cents,
            risk_penalty_cents=risk_cents,
            expected_net_recovery_value_cents=net_erv_cents,
            rationale=rationale,
        )
