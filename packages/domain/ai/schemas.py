"""Pydantic schemas and output contracts for AI Strategy Agent."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from packages.domain.enums import RecoveryActionType


class AIStrategyRecommendation(BaseModel):
    """
    Strict structured output contract for AI Recovery Strategy recommendations.
    """

    recommended_action: RecoveryActionType = Field(
        ...,
        description="The primary recovery action recommended from the eligible candidate set.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="LLM qualitative epistemic certainty (NOT statistical recovery probability).",
    )
    root_cause_diagnosis: str = Field(
        ...,
        description="Qualitative root-cause analysis explaining why the payment failed and why this strategy was chosen.",
    )
    rationale: str = Field(
        ...,
        description="Detailed strategic explanation for merchant operators.",
    )
    alternative_action: Optional[RecoveryActionType] = Field(
        default=None,
        description="Secondary fallback action if the primary action fails or is rejected by policy.",
    )
    expected_recovery_latency_minutes: int = Field(
        default=30,
        ge=0,
        description="Estimated time in minutes until expected recovery resolution.",
    )


class AIDecisionContext(BaseModel):
    """
    Structured, sanitized, PII-minimized decision context passed to the LLM.
    """

    case_id: str
    amount_cents: int
    amount_formatted: str
    currency: str
    failure_category: str
    is_transient: bool
    current_attempt_count: int
    max_allowed_attempts: int
    minutes_since_failure: int
    customer_profile: Dict[str, Any]
    eligible_candidate_actions: List[RecoveryActionType]
    erv_rankings: List[Dict[str, Any]]
    policy_constraints: Dict[str, Any]
    untrusted_gateway_diagnostics: str
    prompt_version: str = "v1.0.0"


class AIExecutionMetadata(BaseModel):
    """
    Observability and audit metadata for the AI invocation.
    """

    provider: str
    model: str
    prompt_version: str
    schema_version: str = "v1.0.0"
    latency_ms: int
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
