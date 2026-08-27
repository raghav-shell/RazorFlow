"""Unit tests for domain value objects."""

from decimal import Decimal

import pytest

from packages.domain.value_objects import (
    ModelConfidence,
    MonetaryAmount,
    RecoveryProbability,
    RiskScore,
)


def test_monetary_amount_arithmetic():
    amt1 = MonetaryAmount(cents=1000, currency="INR")
    amt2 = MonetaryAmount(cents=550, currency="INR")

    added = amt1.add(amt2)
    assert added.cents == 1550
    assert added.decimal_value == Decimal("15.50")

    subtracted = amt1.subtract(amt2)
    assert subtracted.cents == 450
    assert subtracted.decimal_value == Decimal("4.50")


def test_monetary_amount_negative_rejection():
    with pytest.raises(ValueError):
        MonetaryAmount(cents=-100)


def test_monetary_amount_currency_mismatch():
    inr = MonetaryAmount(cents=1000, currency="INR")
    usd = MonetaryAmount(cents=1000, currency="USD")
    with pytest.raises(ValueError):
        inr.add(usd)


def test_risk_score_bounds():
    valid = RiskScore(score=0.45)
    assert valid.score == 0.45

    with pytest.raises(ValueError):
        RiskScore(score=-0.1)

    with pytest.raises(ValueError):
        RiskScore(score=1.1)


def test_recovery_probability_bounds():
    prob = RecoveryProbability(probability=0.88)
    assert prob.probability == 0.88

    with pytest.raises(ValueError):
        RecoveryProbability(probability=1.5)


def test_model_confidence_separation():
    conf = ModelConfidence(confidence=0.92, reasoning="Clear gateway timeout signal")
    assert conf.confidence == 0.92
    assert "timeout" in conf.reasoning

    with pytest.raises(ValueError):
        ModelConfidence(confidence=-0.5, reasoning="invalid")
