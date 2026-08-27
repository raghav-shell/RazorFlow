"""Deterministic Decision Orchestration Service coordinating Candidate Generation, ERV, and Policy Engine."""

import logging
import uuid
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from packages.domain.candidate_generator import CandidateGenerator
from packages.domain.commands import RecoveryCommand
from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import (
    FailureCategory,
    PolicyVerdict,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.policy.engine import PolicyEngine
from packages.domain.policy.result import PolicyEvaluationResult
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.scoring.erv_calculator import ERVCalculator, ERVResult
from packages.domain.scoring.erv_ranker import ERVRanker
from packages.domain.scoring.probability_scorer import BaselineHeuristicProbabilityScorer
from packages.domain.state_machine import CaseStateMachine
from packages.domain.value_objects import MonetaryAmount, RecoveryProbability
from packages.persistence.audit_ledger import AuditLedgerService
from packages.persistence.models.recovery_attempt import RecoveryDecisionModel
from packages.persistence.models.recovery_case import RecoveryCaseModel

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DecisionPipelineResult:
    """Full auditable output of the deterministic decision pipeline."""

    case_id: uuid.UUID
    eligible_candidates: List[RecoveryActionType]
    erv_rankings: List[ERVResult]
    top_recommended_action: RecoveryActionType
    policy_evaluation: PolicyEvaluationResult
    authorized_command: Optional[RecoveryCommand]
    decision_record_id: uuid.UUID


class DecisionService:
    """
    Coordinates the deterministic decision pipeline for a RecoveryCase:
    Candidate Generation -> Probability Scoring -> ERV Ranking -> Policy Engine -> Command Authorization.
    Operates 100% independently of Gemini / external LLMs.
    """

    @classmethod
    async def evaluate_case_decision(
        cls,
        session: AsyncSession,
        case: RecoveryCaseModel,
        context: CaseEnrichmentContext,
        policy: MerchantPolicySnapshot,
    ) -> DecisionPipelineResult:
        """
        Executes end-to-end deterministic evaluation and persists decision record and state transition.
        """
        merchant_id = case.merchant_id
        case_id = case.id
        attempt_number = case.current_attempt_count + 1

        # Parse failure category enum safely
        failure_cat_enum: Optional[FailureCategory] = None
        if case.failure_category:
            try:
                failure_cat_enum = FailureCategory(case.failure_category)
            except ValueError:
                failure_cat_enum = None

        prob_vo = (
            RecoveryProbability.from_float(case.recovery_probability)
            if case.recovery_probability is not None
            else None
        )
        erv_vo = (
            MonetaryAmount.from_paise(case.expected_recovery_value_cents, case.currency)
            if case.expected_recovery_value_cents is not None
            else None
        )

        # Build pure domain snapshot
        case_snapshot = RecoveryCaseSnapshot(
            id=case.id,
            merchant_id=case.merchant_id,
            order_id=case.order_id,
            initial_payment_id=case.initial_payment_id,
            customer_id=case.customer_id,
            amount_at_risk=MonetaryAmount.from_paise(case.amount_at_risk_cents, case.currency),
            amount_recovered=MonetaryAmount.from_paise(case.amount_recovered_cents, case.currency),
            status=case.status,
            failure_category=failure_cat_enum,
            is_transient=case.is_transient,
            diagnosis_reasoning=case.diagnosis_reasoning,
            recovery_probability=prob_vo,
            expected_recovery_value=erv_vo,
            last_ai_confidence=case.last_ai_confidence,
            current_attempt_count=case.current_attempt_count,
            max_allowed_attempts=case.max_allowed_attempts,
            deadline_at=case.deadline_at,
            next_action_scheduled_at=case.next_action_scheduled_at,
            last_attempt_at=case.last_attempt_at,
            metadata=case.metadata_json or {},
        )

        # 1. Candidate Generation
        candidates = CandidateGenerator.generate_candidates(
            case=case_snapshot,
            context=context,
            policy=policy,
        )

        # 2. Probability Scoring & ERV Calculation
        scorer = BaselineHeuristicProbabilityScorer()
        erv_results: List[ERVResult] = []

        for cand in candidates:
            prob = scorer.score(case=case_snapshot, context=context, action=cand)
            erv = ERVCalculator.calculate_erv(
                action=cand,
                case=case_snapshot,
                context=context,
                probability=prob,
                policy=policy,
            )
            erv_results.append(erv)

        # 3. ERV Ranking
        ranked_ervs = ERVRanker.rank_candidates(erv_results)
        top_erv = ranked_ervs[0]
        proposed_action = top_erv.action

        # 4. Advance State Machine: DIAGNOSING -> STRATEGY_GENERATED
        if case.status == RecoveryCaseStatus.DIAGNOSING:
            CaseStateMachine.validate_transition(case.status, RecoveryCaseStatus.STRATEGY_GENERATED)
            case.status = RecoveryCaseStatus.STRATEGY_GENERATED
            await session.flush()

        # 5. Advance State Machine: STRATEGY_GENERATED -> POLICY_CHECK_PENDING
        if case.status == RecoveryCaseStatus.STRATEGY_GENERATED:
            CaseStateMachine.validate_transition(
                case.status, RecoveryCaseStatus.POLICY_CHECK_PENDING
            )
            case.status = RecoveryCaseStatus.POLICY_CHECK_PENDING
            await session.flush()

        # 6. Policy Engine Evaluation
        policy_eval = PolicyEngine.evaluate(
            proposed_action=proposed_action,
            case=case_snapshot,
            context=context,
            policy=policy,
            erv_rankings=ranked_ervs,
        )

        # 7. Update Case Status based on Policy Verdict
        if policy_eval.verdict == PolicyVerdict.APPROVED:
            target_status = RecoveryCaseStatus.APPROVED
        elif policy_eval.verdict == PolicyVerdict.MODIFIED:
            target_status = (
                RecoveryCaseStatus.APPROVED
                if policy_eval.authorized_action != RecoveryActionType.DO_NOTHING
                else RecoveryCaseStatus.REJECTED
            )
        elif policy_eval.verdict == PolicyVerdict.ESCALATED:
            target_status = RecoveryCaseStatus.ESCALATED
        else:
            target_status = RecoveryCaseStatus.REJECTED

        CaseStateMachine.validate_transition(case.status, target_status)
        case.status = target_status
        case.recovery_probability = top_erv.recovery_probability.value
        case.expected_recovery_value_cents = top_erv.expected_net_recovery_value_cents

        # 8. Create Authorized Command if an actionable intervention is authorized
        authorized_cmd: Optional[RecoveryCommand] = None
        if (
            policy_eval.authorized_action != RecoveryActionType.DO_NOTHING
            and policy_eval.verdict != PolicyVerdict.REJECTED
        ):
            authorized_cmd = RecoveryCommand.create(
                case_id=case_id,
                merchant_id=merchant_id,
                order_id=case.order_id,
                action_type=policy_eval.authorized_action,
                attempt_number=attempt_number,
                amount_cents=case.amount_at_risk_cents,
                currency=case.currency,
                deadline_at=case.deadline_at,
                payload={
                    "rule_code": policy_eval.rule_code,
                    "reassessment_delay_seconds": policy_eval.reassessment_delay_seconds,
                },
            )

        # 9. Persist RecoveryDecisionModel
        erv_summary = [
            {
                "action": r.action.value,
                "p_recovery": r.recovery_probability.value,
                "gross_expected_cents": r.gross_expected_recovery_cents,
                "cost_cents": r.intervention_cost_cents,
                "risk_cents": r.risk_penalty_cents,
                "net_erv_cents": r.expected_net_recovery_value_cents,
            }
            for r in ranked_ervs
        ]

        decision_record = RecoveryDecisionModel(
            case_id=case_id,
            merchant_id=merchant_id,
            attempt_number=attempt_number,
            eligible_candidate_actions=[c.value for c in candidates],
            ai_recommended_action=proposed_action,  # In Phase 2: Highest deterministic ERV candidate
            ai_confidence=1.0,  # Pure deterministic confidence
            ai_reasoning=top_erv.rationale,
            ai_raw_response={"erv_table": erv_summary, "scorer": "baseline_heuristic_v1"},
            policy_verdict=policy_eval.verdict,
            authorized_action=policy_eval.authorized_action,
            policy_rule_triggered=policy_eval.rule_code,
            policy_details={
                "rule_code": policy_eval.rule_code,
                "reason": policy_eval.reason,
                "policy_version": policy.policy_version,
                "reassessment_delay_seconds": policy_eval.reassessment_delay_seconds,
            },
        )
        session.add(decision_record)
        await session.flush()

        # 10. Record Cryptographic Hash Chain Audit Event
        await AuditLedgerService.record_event(
            session=session,
            merchant_id=merchant_id,
            entity_type="RECOVERY_DECISION",
            entity_id=decision_record.id,
            action="RECOVERY_DECISION_EVALUATED",
            actor_type="SYSTEM",
            actor_id="deterministic-policy-engine",
            payload={
                "case_id": str(case_id),
                "proposed_action": proposed_action.value,
                "authorized_action": policy_eval.authorized_action.value,
                "verdict": policy_eval.verdict.value,
                "rule_code": policy_eval.rule_code,
                "net_erv_cents": top_erv.expected_net_recovery_value_cents,
                "attempt_number": attempt_number,
            },
        )

        logger.info(
            f"Decision for Case '{case_id}': Proposed '{proposed_action.value}' (ERV ₹{top_erv.expected_net_recovery_value_cents / 100:.2f}) "
            f"-> Policy Verdict '{policy_eval.verdict.value}' -> Authorized '{policy_eval.authorized_action.value}' [{policy_eval.rule_code}]."
        )

        return DecisionPipelineResult(
            case_id=case_id,
            eligible_candidates=candidates,
            erv_rankings=ranked_ervs,
            top_recommended_action=proposed_action,
            policy_evaluation=policy_eval,
            authorized_command=authorized_cmd,
            decision_record_id=decision_record.id,
        )
