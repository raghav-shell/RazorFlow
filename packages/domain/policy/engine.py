"""Deterministic Policy Engine enforcing financial and operational guardrails."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import (
    FailureCategory,
    PolicyVerdict,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.policy.result import PolicyEvaluationResult
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.scoring.erv_calculator import ERVResult

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Pure side-effect-free Policy Engine.
    Enforces deterministic hard stopping rules, merchant guardrails, and compliance bounds.
    Policy ALWAYS wins over ML/ERV optimization.
    """

    @classmethod
    def evaluate(
        cls,
        proposed_action: RecoveryActionType,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        policy: MerchantPolicySnapshot,
        erv_rankings: Optional[List[ERVResult]] = None,
        now: Optional[datetime] = None,
    ) -> PolicyEvaluationResult:
        """
        Evaluates proposed action against policy rules in strict order of precedence.
        """
        current_time = now or datetime.now(timezone.utc)
        policy_ver = policy.policy_version

        # 1. Terminal State Guard
        terminal_statuses = (
            RecoveryCaseStatus.RECOVERED,
            RecoveryCaseStatus.UNRECOVERABLE,
            RecoveryCaseStatus.EXPIRED,
            RecoveryCaseStatus.STOPPED,
        )
        if case.status in terminal_statuses:
            return PolicyEvaluationResult(
                verdict=PolicyVerdict.REJECTED,
                proposed_action=proposed_action,
                authorized_action=RecoveryActionType.DO_NOTHING,
                rule_code="CASE_ALREADY_TERMINAL",
                reason=f"RecoveryCase is in terminal state '{case.status.value}'. No further actions permitted.",
                policy_version=policy_ver,
            )

        # 2. Recovery Deadline Guard
        if case.deadline_at and current_time >= case.deadline_at:
            return PolicyEvaluationResult(
                verdict=PolicyVerdict.MODIFIED,
                proposed_action=proposed_action,
                authorized_action=RecoveryActionType.DO_NOTHING,
                rule_code="DEADLINE_EXPIRED",
                reason=f"Recovery deadline {case.deadline_at.isoformat()} has expired.",
                policy_version=policy_ver,
            )

        # 3. Maximum Attempts Guard
        if case.current_attempt_count >= policy.max_allowed_attempts:
            return PolicyEvaluationResult(
                verdict=PolicyVerdict.MODIFIED,
                proposed_action=proposed_action,
                authorized_action=RecoveryActionType.DO_NOTHING,
                rule_code="MAX_ATTEMPTS_EXCEEDED",
                reason=(
                    f"Current attempt count ({case.current_attempt_count}) has reached or exceeded "
                    f"merchant max allowed attempts ({policy.max_allowed_attempts})."
                ),
                policy_version=policy_ver,
            )

        # 4. Active Cooldown Guard
        if case.last_attempt_at is not None:
            elapsed_seconds = (current_time - case.last_attempt_at).total_seconds()
            cooldown_seconds = policy.cooldown_period_minutes * 60
            if elapsed_seconds < cooldown_seconds and proposed_action not in (
                RecoveryActionType.WAIT_AND_REASSESS,
                RecoveryActionType.DO_NOTHING,
            ):
                remaining_delay = int(cooldown_seconds - elapsed_seconds)
                return PolicyEvaluationResult(
                    verdict=PolicyVerdict.MODIFIED,
                    proposed_action=proposed_action,
                    authorized_action=RecoveryActionType.WAIT_AND_REASSESS,
                    rule_code="COOLDOWN_ACTIVE",
                    reason=(
                        f"Active cooldown in effect. {remaining_delay}s remaining of "
                        f"{policy.cooldown_period_minutes}m cooldown window."
                    ),
                    reassessment_delay_seconds=remaining_delay,
                    policy_version=policy_ver,
                )

        # 5. Fraud / Risk Block Guard
        if case.failure_category == FailureCategory.FRAUD_RISK_BLOCK.value:
            if proposed_action != RecoveryActionType.DO_NOTHING:
                return PolicyEvaluationResult(
                    verdict=PolicyVerdict.REJECTED,
                    proposed_action=proposed_action,
                    authorized_action=RecoveryActionType.DO_NOTHING,
                    rule_code="FRAUD_RISK_GUARD",
                    reason="Automated recovery prohibited for transactions flagged as FRAUD_RISK_BLOCK.",
                    policy_version=policy_ver,
                )

        # 6. Customer Reminder without Active Link Guard
        if proposed_action == RecoveryActionType.CUSTOMER_REMINDER:
            has_active_link = getattr(context, "has_active_payment_link", False) or (
                case.metadata_json.get("active_payment_link_id") is not None
            )
            if not has_active_link:
                # Modify to PAYMENT_LINK if eligible, otherwise DO_NOTHING
                return PolicyEvaluationResult(
                    verdict=PolicyVerdict.MODIFIED,
                    proposed_action=proposed_action,
                    authorized_action=RecoveryActionType.PAYMENT_LINK,
                    rule_code="NO_ACTIVE_PAYMENT_LINK",
                    reason="Cannot send reminder without an active payment link. Modified to PAYMENT_LINK.",
                    policy_version=policy_ver,
                )

        # 7. High-Value Escalation Guard
        if case.amount_at_risk_cents >= policy.high_value_escalation_threshold_cents:
            if proposed_action != RecoveryActionType.HUMAN_ESCALATION:
                return PolicyEvaluationResult(
                    verdict=PolicyVerdict.ESCALATED,
                    proposed_action=proposed_action,
                    authorized_action=RecoveryActionType.HUMAN_ESCALATION,
                    rule_code="HIGH_VALUE_THRESHOLD_EXCEEDED",
                    reason=(
                        f"Amount at risk (₹{case.amount_at_risk_cents / 100:.2f}) meets or exceeds "
                        f"high-value threshold (₹{policy.high_value_escalation_threshold_cents / 100:.2f}). "
                        f"Escalated to human concierge."
                    ),
                    policy_version=policy_ver,
                )

        # 8. Merchant Disallowed Actions Guard
        if proposed_action in policy.disallowed_actions:
            # Fallback to next best eligible action from ERV ranking if available
            fallback_action = RecoveryActionType.DO_NOTHING
            if erv_rankings:
                for r in erv_rankings:
                    if r.action not in policy.disallowed_actions and r.action != proposed_action:
                        fallback_action = r.action
                        break

            return PolicyEvaluationResult(
                verdict=PolicyVerdict.MODIFIED,
                proposed_action=proposed_action,
                authorized_action=fallback_action,
                rule_code="ACTION_DISALLOWED_BY_MERCHANT",
                reason=(
                    f"Proposed action '{proposed_action.value}' is disabled in merchant configuration. "
                    f"Modified to '{fallback_action.value}'."
                ),
                policy_version=policy_ver,
            )

        # 9. DO_NOTHING Safety Handling
        if proposed_action == RecoveryActionType.DO_NOTHING:
            return PolicyEvaluationResult(
                verdict=PolicyVerdict.APPROVED,
                proposed_action=proposed_action,
                authorized_action=RecoveryActionType.DO_NOTHING,
                rule_code="NO_INTERVENTION_AUTHORIZED",
                reason="No active recovery intervention authorized.",
                policy_version=policy_ver,
            )

        # 10. Policy Default Approval
        return PolicyEvaluationResult(
            verdict=PolicyVerdict.APPROVED,
            proposed_action=proposed_action,
            authorized_action=proposed_action,
            rule_code="POLICY_APPROVAL_CLEARED",
            reason=f"Proposed action '{proposed_action.value}' cleared all deterministic policy guardrails.",
            policy_version=policy_ver,
        )
