"""Recovery probability scoring protocol and explainable baseline heuristic scorer."""

from typing import Protocol

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import FailureCategory, RecoveryActionType
from packages.domain.value_objects import RecoveryProbability


class RecoveryProbabilityScorerProtocol(Protocol):
    """Protocol for recovery probability estimation models (heuristics or ML/XGBoost)."""

    def score(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        action: RecoveryActionType,
    ) -> RecoveryProbability:
        """Estimates P(recovery | case, context, action) in range [0.0, 1.0]."""
        ...


class BaselineHeuristicProbabilityScorer:
    """
    Transparent, deterministic, explainable baseline recovery probability calculator.
    NOTE: This is a BASELINE HEURISTIC and not a statistically calibrated ML model.
    A future XGBoost / LightGBM scorer can replace this by satisfying RecoveryProbabilityScorerProtocol.
    """

    def score(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        action: RecoveryActionType,
    ) -> RecoveryProbability:
        # DO_NOTHING has low organic recovery probability
        if action == RecoveryActionType.DO_NOTHING:
            return RecoveryProbability.from_float(0.05 if case.is_transient else 0.01)

        # FRAUD_RISK_BLOCK has zero recovery probability across all actions
        if case.failure_category == FailureCategory.FRAUD_RISK_BLOCK.value:
            return RecoveryProbability.from_float(0.0)

        # Base category probabilities mapped to candidate actions
        base_p = 0.35

        cat = case.failure_category
        if cat == FailureCategory.USER_AUTHENTICATION_DROPOFF.value:
            if action in (RecoveryActionType.PAYMENT_LINK, RecoveryActionType.CUSTOMER_REMINDER):
                base_p = 0.65
            elif action == RecoveryActionType.HUMAN_ESCALATION:
                base_p = 0.70
            else:
                base_p = 0.30

        elif cat == FailureCategory.INSUFFICIENT_FUNDS.value:
            if action in (RecoveryActionType.PAYMENT_LINK, RecoveryActionType.CUSTOMER_REMINDER):
                base_p = 0.50
            elif action == RecoveryActionType.WAIT_AND_REASSESS:
                base_p = 0.40
            else:
                base_p = 0.25

        elif cat == FailureCategory.BANK_SYSTEM_OUTAGE.value:
            if action == RecoveryActionType.WAIT_AND_REASSESS:
                base_p = 0.75
            elif action == RecoveryActionType.PAYMENT_LINK:
                base_p = 0.45
            else:
                base_p = 0.20

        elif cat == FailureCategory.TECHNICAL_GATEWAY_TIMEOUT.value:
            if action == RecoveryActionType.WAIT_AND_REASSESS:
                base_p = 0.70
            elif action == RecoveryActionType.PAYMENT_LINK:
                base_p = 0.60
            else:
                base_p = 0.30

        elif cat == FailureCategory.PERMANENT_INSTRUMENT_DECLINE.value:
            if action == RecoveryActionType.PAYMENT_LINK:
                base_p = 0.20
            elif action == RecoveryActionType.HUMAN_ESCALATION:
                base_p = 0.35
            else:
                base_p = 0.05

        # Customer Behavioral History Multipliers
        multiplier = 1.0

        if context.historical_success_count >= 3:
            multiplier += 0.15  # Reliable historical payer
        elif context.historical_failure_count >= 3 and context.historical_success_count == 0:
            multiplier -= 0.20  # Chronic failure history

        if context.previous_recovery_count > 0:
            multiplier += 0.10  # Has successfully responded to recovery in the past

        # Attempt Decay Multiplier
        # 1st attempt: 1.0x, 2nd attempt: 0.75x, 3rd attempt: 0.50x
        attempt_decay = max(0.2, 1.0 - (case.current_attempt_count * 0.25))
        multiplier *= attempt_decay

        final_score = base_p * multiplier
        # Clamp strictly between [0.0, 1.0]
        clamped = max(0.0, min(1.0, final_score))

        return RecoveryProbability.from_float(round(clamped, 4))
