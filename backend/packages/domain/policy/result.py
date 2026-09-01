"""Structured Policy Evaluation Result."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from packages.domain.enums import PolicyVerdict, RecoveryActionType


@dataclass(frozen=True)
class PolicyEvaluationResult:
    """Immutable verdict and authorization metadata produced by the Policy Engine."""

    verdict: PolicyVerdict
    proposed_action: RecoveryActionType
    authorized_action: RecoveryActionType
    rule_code: str
    reason: str
    policy_version: int
    reassessment_delay_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
