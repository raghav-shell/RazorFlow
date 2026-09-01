"""Unit tests for Synthetic Dataset Generator, ML Probability Scorer, Model Versioning, and ERV Integration."""

import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from packages.domain.entities import (
    CaseEnrichmentContext,
    CustomerSnapshot,
    OrderSnapshot,
    PaymentSnapshot,
    RecoveryCaseSnapshot,
)
from packages.domain.enums import (
    FailureCategory,
    OrderStatus,
    PaymentStatus,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.scoring.erv_calculator import ERVCalculator
from packages.domain.scoring.probability_scorer import (
    MLProbabilityScorer,
    get_default_probability_scorer,
)
from packages.domain.value_objects import MonetaryAmount, RiskScore
from scripts.generate_synthetic_dataset import generate_synthetic_recovery_dataset
from scripts.train_recovery_model import (
    ALL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    build_pipeline,
    evaluate_model,
)


def create_sample_case_and_context(
    failure_category: FailureCategory = FailureCategory.USER_AUTHENTICATION_DROPOFF,
    amount_cents: int = 500000,
    hist_success: int = 2,
    hist_failure: int = 0,
    risk_score: float = 0.20,
    attempt_count: int = 0,
) -> tuple[RecoveryCaseSnapshot, CaseEnrichmentContext]:
    """Helper creating domain snapshot and context for ML testing."""
    merchant_id = uuid.uuid4()
    case_id = uuid.uuid4()
    order_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    cust_id = uuid.uuid4()

    case = RecoveryCaseSnapshot(
        id=case_id,
        merchant_id=merchant_id,
        order_id=order_id,
        initial_payment_id=payment_id,
        customer_id=cust_id,
        amount_at_risk=MonetaryAmount.from_paise(amount_cents, "INR"),
        amount_recovered=MonetaryAmount.from_paise(0, "INR"),
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category=failure_category,
        is_transient=failure_category
        in (FailureCategory.BANK_SYSTEM_OUTAGE, FailureCategory.TECHNICAL_GATEWAY_TIMEOUT),
        current_attempt_count=attempt_count,
        max_allowed_attempts=3,
        deadline_at=datetime.now(timezone.utc),
    )

    context = CaseEnrichmentContext(
        customer=CustomerSnapshot(
            id=cust_id,
            merchant_id=merchant_id,
            external_customer_id="cust_test_1",
            email="cust@test.com",
            phone="+919876543210",
            name="Test Customer",
            risk_score=RiskScore(score=risk_score),
            recovery_success_count=hist_success,
            total_failure_count=hist_failure,
        ),
        order=OrderSnapshot(
            id=order_id,
            merchant_id=merchant_id,
            external_order_id="order_test_1",
            amount=MonetaryAmount.from_paise(amount_cents, "INR"),
            status=OrderStatus.ATTEMPTED,
            customer_id=cust_id,
        ),
        initial_payment=PaymentSnapshot(
            id=payment_id,
            merchant_id=merchant_id,
            order_id=order_id,
            external_payment_id="pay_test_1",
            amount=MonetaryAmount.from_paise(amount_cents, "INR"),
            status=PaymentStatus.FAILED,
            customer_id=cust_id,
            method="card",
            error_code="BAD_REQUEST_ERROR",
            error_source="customer",
            error_step="payment_authentication",
            error_reason="authentication_failed",
        ),
        historical_success_count=hist_success,
        historical_failure_count=hist_failure,
        previous_recovery_count=1 if hist_success > 0 else 0,
        customer_risk_tier="LOW" if risk_score < 0.3 else "HIGH",
    )
    return case, context


def test_synthetic_dataset_reproducibility():
    """Verifies that the dataset generator produces identical outputs with fixed seed."""
    df1 = generate_synthetic_recovery_dataset(num_rows=200, random_seed=42)
    df2 = generate_synthetic_recovery_dataset(num_rows=200, random_seed=42)
    pd.testing.assert_frame_equal(df1, df2)


def test_synthetic_dataset_schema_and_target_bounds():
    """Validates column presence, no missing values, and target bounds in {0, 1}."""
    df = generate_synthetic_recovery_dataset(num_rows=500, random_seed=99)
    for col in ALL_FEATURE_COLUMNS:
        assert col in df.columns, f"Missing feature column: {col}"
    assert TARGET_COLUMN in df.columns
    assert set(df[TARGET_COLUMN].unique()).issubset({0, 1})

    # Fraud cases must strictly have zero recovery
    fraud_rows = df[df["failure_category"] == "FRAUD_RISK_BLOCK"]
    assert len(fraud_rows) > 0
    assert fraud_rows["recovered"].sum() == 0


def test_ml_pipeline_training_and_metric_evaluation():
    """Verifies that the scikit-learn pipeline fits and produces calibrated probabilities."""
    df = generate_synthetic_recovery_dataset(num_rows=1000, random_seed=123)
    X = df[ALL_FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    pipeline = build_pipeline()
    pipeline.fit(X[:800], y[:800])

    metrics = evaluate_model(pipeline, X[800:], y[800:])
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert 0.0 <= metrics["brier_score"] <= 1.0

    probs = pipeline.predict_proba(X[800:])[:, 1]
    assert np.all((probs >= 0.0) & (probs <= 1.0))


def test_ml_probability_scorer_active_prediction():
    """Tests MLProbabilityScorer prediction, safety clamping, and probability bounds."""
    scorer = MLProbabilityScorer()
    assert scorer.model_version in ("recovery_model_v1", "heuristic_baseline_v1")

    case, context = create_sample_case_and_context(
        failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
        amount_cents=250000,
    )

    prob = scorer.score(case, context, RecoveryActionType.PAYMENT_LINK)
    assert 0.0 <= prob.value <= 1.0
    assert isinstance(prob.value, float)


def test_ml_probability_scorer_fraud_risk_boundary_invariant():
    """Ensures that FRAUD_RISK_BLOCK always outputs 0.0 probability."""
    scorer = MLProbabilityScorer()
    case, context = create_sample_case_and_context(
        failure_category=FailureCategory.FRAUD_RISK_BLOCK,
        amount_cents=1000000,
        risk_score=0.99,
    )

    for action in RecoveryActionType:
        prob = scorer.score(case, context, action)
        assert prob.value == 0.0, f"Fraud block produced non-zero probability for {action}"


def test_ml_probability_scorer_customer_history_impact():
    """Verifies that customers with high historical success score higher than chronic failure customers."""
    scorer = MLProbabilityScorer()

    # Good customer
    case_good, ctx_good = create_sample_case_and_context(
        failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
        hist_success=5,
        hist_failure=0,
        risk_score=0.10,
    )
    # Poor customer
    case_poor, ctx_poor = create_sample_case_and_context(
        failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
        hist_success=0,
        hist_failure=6,
        risk_score=0.90,
    )

    prob_good = scorer.score(case_good, ctx_good, RecoveryActionType.PAYMENT_LINK)
    prob_poor = scorer.score(case_poor, ctx_poor, RecoveryActionType.PAYMENT_LINK)

    assert prob_good.value > prob_poor.value


def test_ml_probability_scorer_fallback_behavior():
    """Verifies graceful fallback to BaselineHeuristicProbabilityScorer when model file is missing."""
    scorer = MLProbabilityScorer(model_path="/tmp/non_existent_model_xyz.joblib")
    assert not scorer.is_ml_active
    assert scorer.model_version == "heuristic_baseline_v1"

    case, context = create_sample_case_and_context()
    prob = scorer.score(case, context, RecoveryActionType.PAYMENT_LINK)
    assert 0.0 <= prob.value <= 1.0


def test_erv_integration_with_ml_probability():
    """Verifies exact integer paise ERV calculations driven by ML probabilities."""
    scorer = get_default_probability_scorer()
    case, context = create_sample_case_and_context(
        failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
        amount_cents=450000,  # ₹4,500.00
    )
    policy = MerchantPolicySnapshot()

    prob = scorer.score(case, context, RecoveryActionType.PAYMENT_LINK)
    erv = ERVCalculator.calculate_erv(
        action=RecoveryActionType.PAYMENT_LINK,
        case=case,
        context=context,
        probability=prob,
        policy=policy,
    )

    # Invariant: Gross ERV == int(P_ML * Amount)
    expected_gross = int(prob.value * 450000)
    assert erv.gross_expected_recovery_cents == expected_gross

    # Invariant: Net ERV == Gross ERV - Cost - Risk Penalty
    expected_net = expected_gross - erv.intervention_cost_cents - erv.risk_penalty_cents
    assert erv.expected_net_recovery_value_cents == expected_net
    assert erv.amount_at_risk_cents == 450000
    assert isinstance(erv.expected_net_recovery_value_cents, int)
