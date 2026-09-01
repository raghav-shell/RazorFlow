"""Synthetic Dataset Generator for RazorFlow ML Recovery Scoring.

Generates realistic historical payment failure and recovery records
incorporating domain-specific correlations, behavioral indicators,
attempt decay, and calibrated noise.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

FAILURE_CATEGORIES = [
    "USER_AUTHENTICATION_DROPOFF",
    "BANK_SYSTEM_OUTAGE",
    "TECHNICAL_GATEWAY_TIMEOUT",
    "INSUFFICIENT_FUNDS",
    "PERMANENT_INSTRUMENT_DECLINE",
    "FRAUD_RISK_BLOCK",
    "UNKNOWN",
]

PAYMENT_METHODS = ["upi", "card", "netbanking", "wallet"]

CANDIDATE_ACTIONS = [
    "PAYMENT_LINK",
    "CUSTOMER_REMINDER",
    "WAIT_AND_REASSESS",
    "HUMAN_ESCALATION",
    "DO_NOTHING",
]

RISK_TIERS = ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]

ERROR_CODES = {
    "USER_AUTHENTICATION_DROPOFF": (
        "BAD_REQUEST_ERROR",
        "customer",
        "payment_authentication",
        "authentication_failed",
    ),
    "BANK_SYSTEM_OUTAGE": ("GATEWAY_ERROR", "bank", "payment_authorization", "issuer_down"),
    "TECHNICAL_GATEWAY_TIMEOUT": (
        "SERVER_ERROR",
        "gateway",
        "payment_authorization",
        "gateway_timeout",
    ),
    "INSUFFICIENT_FUNDS": (
        "BAD_REQUEST_ERROR",
        "customer",
        "payment_authorization",
        "insufficient_funds",
    ),
    "PERMANENT_INSTRUMENT_DECLINE": (
        "BAD_REQUEST_ERROR",
        "bank",
        "payment_authorization",
        "card_expired",
    ),
    "FRAUD_RISK_BLOCK": ("RISK_BLOCK", "internal", "payment_initiation", "fraud_suspected"),
    "UNKNOWN": ("UNKNOWN_ERROR", "unknown", "unknown", "unknown"),
}


def sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    """Standard numerically stable logistic sigmoid."""
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20.0, 20.0)))


def generate_synthetic_recovery_dataset(
    num_rows: int = 10000,
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Generates a synthetic historical payment dataset with realistic domain correlations.

    Guarantees:
    1. Reproducibility via fixed random seed.
    2. Strict feature isolation (no target/action outcome leakage).
    3. Non-deterministic probabilistic outcomes with domain-calibrated distributions.
    """
    rng = np.random.default_rng(random_seed)

    # 1. Failure Categories distribution
    cat_weights = [0.35, 0.15, 0.15, 0.15, 0.10, 0.05, 0.05]
    failure_cats = rng.choice(FAILURE_CATEGORIES, size=num_rows, p=cat_weights)

    # 2. Payment Methods distribution
    method_weights = [0.55, 0.30, 0.10, 0.05]  # India UPI heavy
    payment_methods = rng.choice(PAYMENT_METHODS, size=num_rows, p=method_weights)

    # 3. Actions evaluated (balanced candidate selection)
    actions = rng.choice(CANDIDATE_ACTIONS, size=num_rows)

    # 4. Customer features
    cust_ids = [f"cust_{rng.integers(1000, 9999)}" for _ in range(num_rows)]
    hist_success = rng.poisson(lam=2.5, size=num_rows)
    hist_failure = rng.poisson(lam=1.0, size=num_rows)
    prev_recovery = (rng.uniform(size=num_rows) < 0.25).astype(int)
    risk_tiers = rng.choice(RISK_TIERS, size=num_rows, p=[0.50, 0.30, 0.15, 0.05])

    # 5. Case transaction features
    # Order amount in paise: lognormal centered around ₹1,500 (150,000 paise)
    order_amounts = np.clip(
        np.exp(rng.normal(loc=11.9, scale=0.9, size=num_rows)).astype(int),
        10000,  # ₹100 min
        10000000,  # ₹100,000 max
    )

    attempt_numbers = rng.choice([1, 2, 3], size=num_rows, p=[0.70, 0.20, 0.10])
    previous_attempt_counts = attempt_numbers - 1
    hours = rng.integers(0, 24, size=num_rows)
    days = rng.integers(0, 7, size=num_rows)
    time_since_failure_mins = rng.integers(1, 720, size=num_rows)
    has_active_plink = (rng.uniform(size=num_rows) < 0.15).astype(int)

    # 6. Error details mapped from failure category with small perturbation
    error_codes = []
    error_sources = []
    error_steps = []
    error_reasons = []
    is_transients = []

    for cat in failure_cats:
        code, source, step, reason = ERROR_CODES[cat]
        error_codes.append(code)
        error_sources.append(source)
        error_steps.append(step)
        error_reasons.append(reason)
        # Transient flag: high for gateway/bank/auth dropoff
        if cat in ("BANK_SYSTEM_OUTAGE", "TECHNICAL_GATEWAY_TIMEOUT"):
            is_transients.append(1 if rng.uniform() < 0.90 else 0)
        elif cat == "USER_AUTHENTICATION_DROPOFF":
            is_transients.append(1 if rng.uniform() < 0.75 else 0)
        else:
            is_transients.append(1 if rng.uniform() < 0.15 else 0)

    # 7. Intervention cost based on candidate action (in paise)
    action_cost_map = {
        "PAYMENT_LINK": 200,  # ₹2.00
        "CUSTOMER_REMINDER": 150,  # ₹1.50
        "WAIT_AND_REASSESS": 0,
        "HUMAN_ESCALATION": 10000,  # ₹100.00
        "DO_NOTHING": 0,
    }
    intervention_costs = [action_cost_map[a] for a in actions]

    # =========================================================================
    # 8. COMPUTE RECOVERY GROUND TRUTH PROBABILITY & REALIZED OUTCOME
    # =========================================================================
    logits = np.zeros(num_rows, dtype=float)

    for i in range(num_rows):
        cat = failure_cats[i]
        act = actions[i]
        transient = is_transients[i]

        # Base category-action affinity logit
        if cat == "USER_AUTHENTICATION_DROPOFF":
            if act in ("PAYMENT_LINK", "CUSTOMER_REMINDER"):
                logits[i] += 0.85
            elif act == "HUMAN_ESCALATION":
                logits[i] += 1.10
            elif act == "DO_NOTHING":
                logits[i] -= 1.80
            else:  # WAIT_AND_REASSESS
                logits[i] -= 0.60

        elif cat == "BANK_SYSTEM_OUTAGE":
            if act == "WAIT_AND_REASSESS":
                logits[i] += 1.20
            elif act == "PAYMENT_LINK":
                logits[i] += 0.20
            elif act == "DO_NOTHING":
                logits[i] -= 1.50
            else:
                logits[i] -= 0.80

        elif cat == "TECHNICAL_GATEWAY_TIMEOUT":
            if act == "WAIT_AND_REASSESS":
                logits[i] += 1.05
            elif act == "PAYMENT_LINK":
                logits[i] += 0.65
            elif act == "DO_NOTHING":
                logits[i] -= 1.40
            else:
                logits[i] -= 0.50

        elif cat == "INSUFFICIENT_FUNDS":
            if act in ("PAYMENT_LINK", "CUSTOMER_REMINDER"):
                logits[i] += 0.25
            elif act == "WAIT_AND_REASSESS":
                logits[i] -= 0.20
            else:
                logits[i] -= 1.20

        elif cat == "PERMANENT_INSTRUMENT_DECLINE":
            if act == "PAYMENT_LINK":
                logits[i] -= 0.90  # Still possible with new payment method
            elif act == "HUMAN_ESCALATION":
                logits[i] -= 0.50
            else:
                logits[i] -= 3.20  # Reassessing same dead card has near zero recovery

        elif cat == "FRAUD_RISK_BLOCK":
            # Safety invariant: Fraud blocks must have essentially zero recovery
            logits[i] -= 12.0

        elif cat == "UNKNOWN":
            logits[i] -= 0.40

        # Customer historical behavior impact
        logits[i] += min(0.60, hist_success[i] * 0.12)
        logits[i] -= min(0.60, hist_failure[i] * 0.15)
        if prev_recovery[i]:
            logits[i] += 0.35

        # Risk tier impact
        if risk_tiers[i] == "LOW":
            logits[i] += 0.30
        elif risk_tiers[i] == "HIGH":
            logits[i] -= 0.75

        # Attempt decay
        if attempt_numbers[i] == 2:
            logits[i] -= 0.40
        elif attempt_numbers[i] == 3:
            logits[i] -= 0.95

        # Latency decay
        logits[i] -= (time_since_failure_mins[i] / 720.0) * 0.30

        # Transient failure boost
        if transient:
            logits[i] += 0.25

    # Add realistic stochastic noise
    noise = rng.normal(loc=0.0, scale=0.35, size=num_rows)
    # Ensure fraud remains strictly unrecovered even with noise
    fraud_mask = failure_cats == "FRAUD_RISK_BLOCK"
    noise[fraud_mask] = 0.0

    true_probabilities = sigmoid(logits + noise)
    # Strict clamp
    true_probabilities = np.clip(true_probabilities, 0.0, 1.0)
    true_probabilities[fraud_mask] = 0.0

    # Realize binary recovery outcome
    recovered = (rng.uniform(size=num_rows) < true_probabilities).astype(int)
    recovered[fraud_mask] = 0

    df = pd.DataFrame(
        {
            "customer_id": cust_ids,
            "order_amount_paise": order_amounts,
            "currency": "INR",
            "payment_method": payment_methods,
            "failure_category": failure_cats,
            "error_source": error_sources,
            "error_code": error_codes,
            "error_step": error_steps,
            "error_reason": error_reasons,
            "is_transient": is_transients,
            "customer_historical_success_count": hist_success,
            "customer_historical_failure_count": hist_failure,
            "customer_previous_recovery_success": prev_recovery,
            "customer_risk_tier": risk_tiers,
            "attempt_number": attempt_numbers,
            "hour_of_day": hours,
            "day_of_week": days,
            "has_active_payment_link": has_active_plink,
            "time_since_failure_minutes": time_since_failure_mins,
            "previous_attempt_count": previous_attempt_counts,
            "candidate_action": actions,
            "intervention_cost_paise": intervention_costs,
            "recovered": recovered,
        }
    )

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic payment recovery dataset.")
    parser.add_argument(
        "--rows", type=int, default=10000, help="Number of records to generate (default: 10000)"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for exact reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(
            os.path.dirname(__file__), "..", "data", "synthetic", "recovery_history.csv"
        ),
        help="Target output CSV file path",
    )
    args = parser.parse_args()

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.rows} synthetic historical payment records (seed={args.seed})...")
    df = generate_synthetic_recovery_dataset(num_rows=args.rows, random_seed=args.seed)

    df.to_csv(out_path, index=False)
    print(f"Successfully wrote dataset to {out_path}")
    print(f"  - Total records: {len(df)}")
    print(f"  - Overall recovery rate: {df['recovered'].mean():.2%}")
    print("\nRecovery rate by Failure Category:")
    print(df.groupby("failure_category")["recovered"].agg(["count", "mean"]).to_string())
    print("\nRecovery rate by Candidate Action:")
    print(df.groupby("candidate_action")["recovered"].agg(["count", "mean"]).to_string())


if __name__ == "__main__":
    main()
