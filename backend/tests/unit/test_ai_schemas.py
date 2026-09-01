"""Unit tests for AI Schemas and Output Validation."""

import pytest
from pydantic import ValidationError

from packages.domain.ai.schemas import AIStrategyRecommendation
from packages.domain.enums import RecoveryActionType


def test_ai_strategy_recommendation_valid_schema():
    rec = AIStrategyRecommendation(
        recommended_action=RecoveryActionType.PAYMENT_LINK,
        confidence_score=0.88,
        root_cause_diagnosis="Customer dropped off during 3DS OTP verification.",
        rationale="Sending an interactive payment link gives the user an immediate second chance.",
        alternative_action=RecoveryActionType.WAIT_AND_REASSESS,
        expected_recovery_latency_minutes=20,
    )
    assert rec.recommended_action == RecoveryActionType.PAYMENT_LINK
    assert rec.confidence_score == 0.88
    assert rec.expected_recovery_latency_minutes == 20


def test_ai_strategy_recommendation_invalid_confidence_bounds():
    # Confidence score > 1.0 -> ValidationError
    with pytest.raises(ValidationError):
        AIStrategyRecommendation(
            recommended_action=RecoveryActionType.PAYMENT_LINK,
            confidence_score=1.5,
            root_cause_diagnosis="Diagnosis",
            rationale="Rationale",
            expected_recovery_latency_minutes=10,
        )

    # Confidence score < 0.0 -> ValidationError
    with pytest.raises(ValidationError):
        AIStrategyRecommendation(
            recommended_action=RecoveryActionType.PAYMENT_LINK,
            confidence_score=-0.1,
            root_cause_diagnosis="Diagnosis",
            rationale="Rationale",
            expected_recovery_latency_minutes=10,
        )
