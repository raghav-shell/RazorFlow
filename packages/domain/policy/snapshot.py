"""Merchant Policy Snapshot definition for deterministic rule evaluation and audit versioning."""

from dataclasses import dataclass, field
from typing import List

from packages.domain.enums import RecoveryActionType


@dataclass(frozen=True)
class MerchantPolicySnapshot:
    """
    Immutable snapshot of merchant financial and operational recovery policies.
    Enables reproducible policy audits.
    """

    policy_version: int = 1
    max_allowed_attempts: int = 2
    recovery_window_hours: int = 72
    cooldown_period_minutes: int = 30
    high_value_escalation_threshold_cents: int = 5000000  # ₹50,000.00
    disallowed_actions: List[RecoveryActionType] = field(default_factory=list)
    require_human_escalation_for_high_risk: bool = True
    auto_retry_transient_failures: bool = True
