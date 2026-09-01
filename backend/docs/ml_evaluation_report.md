# RazorFlow: ML Recovery Scoring Evaluation Report

- **Model Version**: `recovery_model_v1`
- **Algorithm**: `GradientBoostingClassifier` (with `ColumnTransformer` preprocessing)
- **Evaluation Date**: August 2026
- **Status**: Validated & Active

---

## 1. Executive Summary

This report documents the design, training, validation, and calibration of RazorFlow's Tabular Machine Learning Recovery Scoring model ($P_{ML}$).

The primary objective of $P_{ML}$ is to estimate the statistical probability of transaction recovery:
$$P_{ML}(\text{Recovery} \mid \text{Case Features}, \text{Customer Context}, \text{Candidate Action}) \in [0.0, 1.0]$$

$P_{ML}$ directly powers the downstream **Expected Recovery Value (ERV)** calculation:
$$\text{Gross ERV} = \text{round}(P_{ML} \times \text{Amount At Risk})$$
$$\text{Expected Net Recovery Value} = \text{Gross ERV} - \text{Intervention Cost} - \text{Risk Penalty}$$

---

## 2. Dataset Generation Methodology

The training data was generated via `backend/scripts/generate_synthetic_dataset.py`, producing **10,000 synthetic historical payment records** with fixed random seed (`--seed 42`) for reproducibility.

### Design Principles & Leakage Prevention:
1. **Candidate Action Decoupling**: Each record evaluates a prospective action against pre-intervention features. Post-intervention data (settlement timing, actual payment IDs) are strictly excluded.
2. **Realistic Non-Linear Domain Correlations**:
   - `USER_AUTHENTICATION_DROPOFF`: High recovery with `PAYMENT_LINK` and `CUSTOMER_REMINDER`.
   - `BANK_SYSTEM_OUTAGE`: Favors `WAIT_AND_REASSESS`.
   - `INSUFFICIENT_FUNDS`: Moderate recovery potential; responsive to reminders after delay.
   - `PERMANENT_INSTRUMENT_DECLINE`: Low overall recovery; requires `PAYMENT_LINK` for instrument update.
   - `FRAUD_RISK_BLOCK`: Hard-clamped to **0.00%** recovery across all actions (safety invariant).
3. **Behavioral Multipliers & Decay**: Customer historical payment success increases recovery odds, while attempt numbers ($1 \rightarrow 2 \rightarrow 3$) and elapsed time apply non-linear probability decay.
4. **Calibrated Stochastic Noise**: Gaussian perturbation ($\sigma = 0.35$) added to logit distributions to ensure the model learns generalized statistical signals rather than deterministic lookup rules.

---

## 3. Feature Dictionary

| Feature Name | Type | Description |
|---|---|---|
| `order_amount_paise` | Numeric (int) | Transaction value in integer minor units (paise) |
| `currency` | Categorical (str) | ISO-4217 Currency (`INR`) |
| `payment_method` | Categorical (str) | `upi`, `card`, `netbanking`, `wallet` |
| `failure_category` | Categorical (str) | Domain failure taxonomy (7 classes) |
| `error_source` | Categorical (str) | `customer`, `gateway`, `bank`, `internal`, `unknown` |
| `error_code` | Categorical (str) | Raw gateway error code identifier |
| `error_step` | Categorical (str) | Payment pipeline stage where failure occurred |
| `error_reason` | Categorical (str) | Specific root cause reason string |
| `is_transient` | Numeric (0/1) | Whether failure is transient/retryable |
| `customer_historical_success_count`| Numeric (int) | Number of lifetime successful payments |
| `customer_historical_failure_count`| Numeric (int) | Number of lifetime failed payments |
| `customer_previous_recovery_success`| Numeric (0/1) | Whether customer previously converted via recovery |
| `customer_risk_tier` | Categorical (str) | `LOW`, `MEDIUM`, `HIGH`, `UNKNOWN` |
| `attempt_number` | Numeric (int) | Current recovery attempt (1, 2, 3) |
| `hour_of_day` | Numeric (int) | UTC hour of attempt initiation (0–23) |
| `day_of_week` | Numeric (int) | Day of the week (0=Mon, 6=Sun) |
| `has_active_payment_link` | Numeric (0/1) | Whether an active link is already pending |
| `time_since_failure_minutes` | Numeric (int) | Elapsed time since payment failure |
| `previous_attempt_count` | Numeric (int) | Prior failed interventions |
| `candidate_action` | Categorical (str) | Action being evaluated (`PAYMENT_LINK`, etc.) |
| `intervention_cost_paise` | Numeric (int) | Direct modeled cost of executing the action |
| **`recovered`** (Target) | Binary (0/1) | Actual historical recovery outcome |

---

## 4. Dataset Statistics

- **Total Samples**: 10,000
- **Overall Base Recovery Rate**: 44.45%
- **Recovery Rate by Failure Category**:
  - `USER_AUTHENTICATION_DROPOFF`: 55.96% (3,542 samples)
  - `TECHNICAL_GATEWAY_TIMEOUT`: 51.37% (1,528 samples)
  - `BANK_SYSTEM_OUTAGE`: 45.89% (1,473 samples)
  - `UNKNOWN`: 42.52% (501 samples)
  - `INSUFFICIENT_FUNDS`: 41.52% (1,503 samples)
  - `PERMANENT_INSTRUMENT_DECLINE`: 17.03% (969 samples)
  - `FRAUD_RISK_BLOCK`: **0.00%** (484 samples)
- **Recovery Rate by Evaluated Action**:
  - `PAYMENT_LINK`: 57.38%
  - `HUMAN_ESCALATION`: 49.40%
  - `CUSTOMER_REMINDER`: 49.01%
  - `WAIT_AND_REASSESS`: 46.90%
  - `DO_NOTHING`: 19.73%

---

## 5. Model Architecture & Training Methodology

### Dataset Splits
- **Training Set**: 7,000 samples (70%)
- **Validation Set**: 1,500 samples (15%)
- **Test Set (Held-out)**: 1,500 samples (15%)
- *Stratified by target `recovered` to preserve class distributions across splits.*

### Scikit-Learn Pipeline Architecture
```
Raw Features (Dataframe)
         ↓
ColumnTransformer:
  ├── StandardScaler (Numeric Features: amount, history, time, cost)
  └── OneHotEncoder(handle_unknown='ignore') (Categorical Features)
         ↓
GradientBoostingClassifier:
  ├── n_estimators = 120
  ├── learning_rate = 0.08
  ├── max_depth = 4
  ├── subsample = 0.85
  └── random_state = 42
         ↓
Calibrated Probabilities P_ML ∈ [0.0, 1.0]
```

---

## 6. Evaluation Metrics

| Metric | Validation Set (1,500 rows) | Test Set (Held-Out, 1,500 rows) |
|---|---|---|
| **Accuracy** | 71.27% | **70.00%** |
| **Precision** | 67.61% | **67.09%** |
| **Recall** | 67.92% | **63.87%** |
| **F1-Score** | 67.76% | **65.44%** |
| **ROC-AUC** | **0.7829** | **0.7690** |
| **Brier Score** | **0.1883** | **0.1941** |

### Confusion Matrix (Test Set, N=1,500)
| | Predicted: Not Recovered (0) | Predicted: Recovered (1) |
|---|---|---|
| **Actual: Not Recovered (0)** | 624 (TN) | 209 (FP) |
| **Actual: Recovered (1)** | 241 (FN) | 426 (TP) |

---

## 7. Calibration & Top Feature Importances

The low Brier score (0.1941) confirms that predicted probabilities are smooth, calibrated, and reflect empirical recovery frequencies.

### Top 10 Influential Features:
1. `candidate_action == DO_NOTHING` (17.65%): Strong negative discriminator against passive inaction.
2. `order_amount_paise` (8.26%): Ticket size influences customer payment commitment.
3. `intervention_cost_paise` (6.06%): Cost signature correlation with high-touch actions.
4. `time_since_failure_minutes` (5.79%): Rapid recovery windows show higher probability.
5. `error_reason == card_expired` (5.45%): Strong indicator for instrument decline.
6. `customer_risk_tier == HIGH` (4.14%): High-risk flag reduces recovery likelihood.
7. `failure_category == PERMANENT_INSTRUMENT_DECLINE` (3.95%): Drives necessity for alternate payment links.
8. `customer_historical_success_count` (3.48%): Established payer credibility.
9. `error_reason == authentication_failed` (3.29%): Positive signal for SMS/WhatsApp payment link recovery.
10. `candidate_action == WAIT_AND_REASSESS` (2.97%): Favorable indicator during bank/gateway outages.

---

## 8. Example Model Predictions & ERV Calculations

### Example 1: 3DS Authentication Dropoff (Order: ₹4,500.00 / 450,000 paise)
- Customer History: 4 successes, 0 failures, Low risk
- Candidate Action: `PAYMENT_LINK` (Cost: ₹2.00 / 200 paise, Risk Penalty: ₹0.00)
- **$P_{ML}$ Prediction**: **0.6842 (68.42%)**
- $\text{Gross ERV} = \text{round}(0.6842 \times 450,000) = 307,890\text{ paise (₹3,078.90)}$
- $\text{Net ERV} = 307,890 - 200 - 0 = \mathbf{307,690\text{ paise (₹3,076.90)}}$

### Example 2: Bank Outage (Order: ₹3,500.00 / 350,000 paise)
- Candidate Action: `WAIT_AND_REASSESS` (Cost: ₹0.00, Risk Penalty: ₹0.00)
- **$P_{ML}$ Prediction**: **0.7215 (72.15%)**
- $\text{Gross ERV} = \text{round}(0.7215 \times 350,000) = 252,525\text{ paise (₹2,525.25)}$
- $\text{Net ERV} = 252,525 - 0 - 0 = \mathbf{252,525\text{ paise (₹2,525.25)}}$

### Example 3: Fraud Risk Block (Order: ₹12,000.00 / 1,200,000 paise)
- Candidate Action: `PAYMENT_LINK`
- **$P_{ML}$ Prediction**: **0.0000 (0.00% - Safety Invariant)**
- $\text{Gross ERV} = 0\text{ paise}$
- $\text{Net ERV} = 0 - 200 - 0 = \mathbf{-200\text{ paise}}$ (Filtered out by PolicyEngine)

---

## 9. Model Limitations & Safeguards

1. **Synthetic Training Distribution**: Trained on synthetic historical payment dynamics calibrated to Indian payment rail patterns (UPI/Card 3DS). Requires online shadow validation when live production dataset reaches sufficient scale.
2. **Deterministic Fallback**: If the model file is missing or corrupted, `BaselineHeuristicProbabilityScorer` automatically takes over without interrupting recovery operations.
3. **Hard Invariant Clamping**: Fraud blocks and negative net-value proposals are strictly prevented by the deterministic Policy Engine regardless of model output.

---

## 10. Reproduction Steps

```bash
# 1. Generate 10,000-row reproducible synthetic dataset
python backend/scripts/generate_synthetic_dataset.py --rows 10000 --seed 42

# 2. Train model, evaluate metrics, and save recovery_model_v1.joblib
python backend/scripts/train_recovery_model.py --seed 42
```
