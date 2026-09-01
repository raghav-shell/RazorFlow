"""Recovery probability scoring protocol, explainable baseline heuristic, and trained ML scorer."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol

import pandas as pd

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import FailureCategory, RecoveryActionType
from packages.domain.value_objects import RecoveryProbability

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "models", "recovery_model_v1.joblib"
)

ACTION_COST_MAP = {
    RecoveryActionType.PAYMENT_LINK: 200,
    RecoveryActionType.CUSTOMER_REMINDER: 150,
    RecoveryActionType.WAIT_AND_REASSESS: 0,
    RecoveryActionType.HUMAN_ESCALATION: 10000,
    RecoveryActionType.DO_NOTHING: 0,
}


class RecoveryProbabilityScorerProtocol(Protocol):
    """Protocol for recovery probability estimation models (heuristics or ML)."""

    @property
    def model_version(self) -> str:
        """Identifier for the scoring model version."""
        ...

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
    Guarantees deterministic fallback when ML artifacts are unavailable.
    """

    @property
    def model_version(self) -> str:
        return "heuristic_baseline_v1"

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
        cat_val = case.failure_category.value if case.failure_category is not None else ""
        if cat_val == FailureCategory.FRAUD_RISK_BLOCK.value:
            return RecoveryProbability.from_float(0.0)

        # Base category probabilities mapped to candidate actions
        base_p = 0.35

        if cat_val == FailureCategory.USER_AUTHENTICATION_DROPOFF.value:
            if action in (RecoveryActionType.PAYMENT_LINK, RecoveryActionType.CUSTOMER_REMINDER):
                base_p = 0.65
            elif action == RecoveryActionType.HUMAN_ESCALATION:
                base_p = 0.70
            else:
                base_p = 0.30

        elif cat_val == FailureCategory.INSUFFICIENT_FUNDS.value:
            if action in (RecoveryActionType.PAYMENT_LINK, RecoveryActionType.CUSTOMER_REMINDER):
                base_p = 0.50
            elif action == RecoveryActionType.WAIT_AND_REASSESS:
                base_p = 0.40
            else:
                base_p = 0.25

        elif cat_val == FailureCategory.BANK_SYSTEM_OUTAGE.value:
            if action == RecoveryActionType.WAIT_AND_REASSESS:
                base_p = 0.75
            elif action == RecoveryActionType.PAYMENT_LINK:
                base_p = 0.45
            else:
                base_p = 0.20

        elif cat_val == FailureCategory.TECHNICAL_GATEWAY_TIMEOUT.value:
            if action == RecoveryActionType.WAIT_AND_REASSESS:
                base_p = 0.70
            elif action == RecoveryActionType.PAYMENT_LINK:
                base_p = 0.60
            else:
                base_p = 0.30

        elif cat_val == FailureCategory.PERMANENT_INSTRUMENT_DECLINE.value:
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


class MLProbabilityScorer:
    """
    Statistically calibrated Tabular ML Recovery Probability Scorer.
    Loads trained scikit-learn model artifact and scores P_ML(recovery | case, context, action).
    Gracefully falls back to BaselineHeuristicProbabilityScorer if model is unavailable.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self._model_path = model_path or DEFAULT_MODEL_PATH
        self._fallback_scorer = BaselineHeuristicProbabilityScorer()
        self._model = None
        self._version = "recovery_model_v1"
        self._load_model()

    def _load_model(self) -> None:
        """Attempts to load the serialized scikit-learn model pipeline."""
        p = Path(self._model_path).resolve()
        if p.exists() and p.is_file():
            try:
                import joblib

                self._model = joblib.load(p)
                logger.info(f"Loaded ML recovery scoring model from '{p}'.")
            except Exception as e:
                logger.warning(
                    f"Failed to load ML recovery model from '{p}': {e}. Falling back to baseline heuristic."
                )
                self._model = None
        else:
            logger.info(
                f"ML recovery model artifact '{p}' not found. Using baseline heuristic fallback."
            )
            self._model = None

    @property
    def model_version(self) -> str:
        return self._version if self._model is not None else self._fallback_scorer.model_version

    @property
    def is_ml_active(self) -> bool:
        return self._model is not None

    def _build_feature_row(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        action: RecoveryActionType,
    ) -> pd.DataFrame:
        """Extracts structured feature vector matching training dataset schema."""
        cat_val = case.failure_category.value if case.failure_category is not None else "UNKNOWN"
        action_val = action.value if hasattr(action, "value") else str(action)

        payment_method = "upi"
        error_source = "unknown"
        error_code = "UNKNOWN"
        error_step = "unknown"
        error_reason = "unknown"

        if context.initial_payment:
            payment_method = context.initial_payment.method or "upi"
            error_source = context.initial_payment.error_source or "unknown"
            error_code = context.initial_payment.error_code or "UNKNOWN"
            error_step = context.initial_payment.error_step or "unknown"
            error_reason = context.initial_payment.error_reason or "unknown"

        created_at = case.created_at or datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        time_since_failure_mins = max(1, int((now - created_at).total_seconds() / 60))

        cost_paise = ACTION_COST_MAP.get(action, 0)

        data = {
            "order_amount_paise": [case.amount_at_risk_cents],
            "is_transient": [1 if case.is_transient else 0],
            "customer_historical_success_count": [context.historical_success_count],
            "customer_historical_failure_count": [context.historical_failure_count],
            "customer_previous_recovery_success": [1 if context.previous_recovery_count > 0 else 0],
            "attempt_number": [case.current_attempt_count + 1],
            "hour_of_day": [now.hour],
            "day_of_week": [now.weekday()],
            "has_active_payment_link": [1 if context.has_active_payment_link else 0],
            "time_since_failure_minutes": [time_since_failure_mins],
            "previous_attempt_count": [case.current_attempt_count],
            "intervention_cost_paise": [cost_paise],
            "payment_method": [payment_method],
            "failure_category": [cat_val],
            "error_source": [error_source],
            "error_code": [error_code],
            "error_step": [error_step],
            "error_reason": [error_reason],
            "customer_risk_tier": [context.customer_risk_tier or "UNKNOWN"],
            "candidate_action": [action_val],
        }
        return pd.DataFrame(data)

    def score(
        self,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        action: RecoveryActionType,
    ) -> RecoveryProbability:
        """
        Estimates recovery probability P_ML in range [0.0, 1.0].
        Strictly enforces domain bounds and fallback on failure.
        """
        # Hard domain invariant: Fraud risk block has absolute 0.0 recovery probability
        cat_val = case.failure_category.value if case.failure_category is not None else ""
        if cat_val == FailureCategory.FRAUD_RISK_BLOCK.value:
            return RecoveryProbability.from_float(0.0)

        # Fallback to heuristic if model is not loaded
        if self._model is None:
            return self._fallback_scorer.score(case, context, action)

        try:
            feature_df = self._build_feature_row(case, context, action)
            probabilities = self._model.predict_proba(feature_df)
            prob_float = float(probabilities[0, 1])

            # Safety clamp [0.0, 1.0]
            clamped = max(0.0, min(1.0, prob_float))
            return RecoveryProbability.from_float(round(clamped, 4))
        except Exception as e:
            logger.warning(
                f"Error predicting probability with ML model: {e}. Falling back to baseline heuristic."
            )
            return self._fallback_scorer.score(case, context, action)


def get_default_probability_scorer() -> RecoveryProbabilityScorerProtocol:
    """Factory returning active ML scorer or fallback heuristic."""
    return MLProbabilityScorer()
