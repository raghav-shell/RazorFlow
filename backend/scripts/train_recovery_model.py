"""Model Training & Evaluation Pipeline for RazorFlow ML Recovery Scoring.

Trains an explainable, calibrated tabular model on the synthetic dataset,
evaluates precision, recall, F1, ROC-AUC, Brier score, and saves
the serialized pipeline as recovery_model_v1.joblib.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

MODEL_VERSION = "recovery_model_v1"

NUMERIC_FEATURES = [
    "order_amount_paise",
    "is_transient",
    "customer_historical_success_count",
    "customer_historical_failure_count",
    "customer_previous_recovery_success",
    "attempt_number",
    "hour_of_day",
    "day_of_week",
    "has_active_payment_link",
    "time_since_failure_minutes",
    "previous_attempt_count",
    "intervention_cost_paise",
]

CATEGORICAL_FEATURES = [
    "payment_method",
    "failure_category",
    "error_source",
    "error_code",
    "error_step",
    "error_reason",
    "customer_risk_tier",
    "candidate_action",
]

ALL_FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "recovered"


def build_pipeline() -> Pipeline:
    """Builds an end-to-end scikit-learn preprocessing and estimator pipeline."""
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )

    estimator = GradientBoostingClassifier(
        n_estimators=120,
        learning_rate=0.08,
        max_depth=4,
        subsample=0.85,
        random_state=42,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", estimator),
        ]
    )
    return pipeline


def evaluate_model(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, Any]:
    """Computes comprehensive statistical and classification metrics."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # Verify probability bounds
    assert np.all((y_prob >= 0.0) & (y_prob <= 1.0)), "Probabilities out of bounds [0, 1]!"

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    brier = float(brier_score_loss(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "brier_score": round(brier, 4),
        "confusion_matrix": cm,
    }


def train_and_save_model(
    data_path: str,
    output_dir: str,
    random_seed: int = 42,
) -> Dict[str, Any]:
    """Main training workflow with train/val/test splits and artifact serialization."""
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records from {data_path}")

    # Validate target presence and uniqueness
    assert TARGET_COLUMN in df.columns, f"Target column '{TARGET_COLUMN}' missing!"
    assert set(df[TARGET_COLUMN].unique()).issubset({0, 1}), "Invalid target values!"

    X = df[ALL_FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Split 70% Train, 15% Validation, 15% Test (Stratified)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=random_seed, stratify=y
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=0.17647,  # 0.15 / 0.85 ≈ 0.17647
        random_state=random_seed,
        stratify=y_train_val,
    )

    print(f"Dataset split: Train={len(X_train)} | Val={len(X_val)} | Test={len(X_test)}")

    # Fit pipeline
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    # Evaluate on Validation and Test
    val_metrics = evaluate_model(pipeline, X_val, y_val)
    test_metrics = evaluate_model(pipeline, X_test, y_test)

    print("\n--- Model Validation Metrics ---")
    for k, v in val_metrics.items():
        print(f"  {k}: {v}")

    print("\n--- Model Test Metrics (Unseen Data) ---")
    for k, v in test_metrics.items():
        print(f"  {k}: {v}")

    # Artifact directory
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    model_file = out_dir / f"{MODEL_VERSION}.joblib"
    meta_file = out_dir / f"{MODEL_VERSION}_metadata.json"

    # Save trained pipeline
    joblib.dump(pipeline, model_file)
    print(f"\nSaved model artifact to: {model_file}")

    # Extract feature importances if available
    classifier = pipeline.named_steps["classifier"]
    preprocessor = pipeline.named_steps["preprocessor"]
    cat_feature_names = list(
        preprocessor.named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES)
    )
    all_transformed_features = NUMERIC_FEATURES + cat_feature_names

    feature_importances = {}
    if hasattr(classifier, "feature_importances_"):
        importances = classifier.feature_importances_
        sorted_indices = np.argsort(importances)[::-1]
        for idx in sorted_indices[:15]:
            feature_importances[all_transformed_features[idx]] = round(float(importances[idx]), 4)

    metadata = {
        "model_version": MODEL_VERSION,
        "algorithm": "GradientBoostingClassifier",
        "random_seed": random_seed,
        "training_samples": len(X_train),
        "validation_samples": len(X_val),
        "test_samples": len(X_test),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
        "top_feature_importances": feature_importances,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved model metadata to: {meta_file}")

    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Train RazorFlow ML Recovery Scoring Model.")
    parser.add_argument(
        "--data",
        type=str,
        default=os.path.join(
            os.path.dirname(__file__), "..", "data", "synthetic", "recovery_history.csv"
        ),
        help="Path to training CSV",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "..", "models"),
        help="Directory to save model artifacts",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for training split (default: 42)",
    )
    args = parser.parse_args()

    train_and_save_model(data_path=args.data, output_dir=args.outdir, random_seed=args.seed)


if __name__ == "__main__":
    main()
