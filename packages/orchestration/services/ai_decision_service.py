"""AI Decision Service coordinating LLM reasoning, deterministic fallback, and Policy Engine authorization."""

import logging
import uuid
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from packages.adapters.ai.gemini_adapter import GeminiStrategyAIAdapter
from packages.adapters.ai.observability import AITelemetryService
from packages.domain.ai.context_builder import AIContextBuilder
from packages.domain.ai.schemas import (
    AIExecutionMetadata,
    AIStrategyRecommendation,
)
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
from packages.ports.ai_strategy import RecoveryStrategyAIPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIDecisionPipelineResult:
    """Complete auditable result of the AI decision pipeline."""

    case_id: uuid.UUID
    eligible_candidates: List[RecoveryActionType]
    deterministic_recommendation: RecoveryActionType
    ai_recommendation: AIStrategyRecommendation
    ai_metadata: AIExecutionMetadata
    erv_rankings: List[ERVResult]
    policy_evaluation: PolicyEvaluationResult
    authorized_command: Optional[RecoveryCommand]
    decision_record_id: uuid.UUID


class AIDecisionService:
    """
    Coordinates the AI Recovery Strategy workflow:
    Candidates -> Probability -> ERV -> AI Reasoner -> Fallback -> Policy Engine -> Authorization.
    Gemini is a STRATEGIST, NOT an AUTHORITY.
    """

    @classmethod
    async def evaluate_with_ai(
        cls,
        session: AsyncSession,
        case: RecoveryCaseModel,
        context: CaseEnrichmentContext,
        policy: MerchantPolicySnapshot,
        ai_client: Optional[RecoveryStrategyAIPort] = None,
    ) -> AIDecisionPipelineResult:
        """
        Executes end-to-end AI strategy reasoning with automatic deterministic fallback.
        """
        settings = get_settings()
        merchant_id = case.merchant_id
        case_id = case.id
        attempt_number = case.current_attempt_count + 1

        # Resolve AI client if not injected
        if ai_client is None:
            ai_client = GeminiStrategyAIAdapter(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_MODEL,
                timeout_seconds=settings.AI_TIMEOUT_SECONDS,
            )

        # 1. Build pure domain snapshot
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

        # 2. Deterministic Candidate Generation
        candidates = CandidateGenerator.generate_candidates(
            case=case_snapshot,
            context=context,
            policy=policy,
        )

        # 3. Deterministic Probability Scoring & ERV Calculation
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

        # 4. Deterministic ERV Ranking (The Baseline / Fallback Recommendation)
        ranked_ervs = ERVRanker.rank_candidates(erv_results)
        top_erv = ranked_ervs[0]
        deterministic_proposed_action = top_erv.action

        # 5. Build Sanitized, PII-Minimised Decision Context for Gemini
        ai_context = AIContextBuilder.build_context(
            case=case_snapshot,
            context=context,
            eligible_candidates=candidates,
            erv_rankings=ranked_ervs,
            policy=policy,
            prompt_version=settings.AI_PROMPT_VERSION,
        )

        # 6. Invoke AI Strategy Agent with Automatic Fallback Protection
        ai_recommendation: AIStrategyRecommendation
        ai_metadata: AIExecutionMetadata

        if not settings.AI_ENABLED:
            logger.info("AI is disabled in configuration. Using deterministic ERV fallback.")
            ai_recommendation = AIStrategyRecommendation(
                recommended_action=deterministic_proposed_action,
                confidence_score=1.0,
                root_cause_diagnosis=f"Deterministic analysis: {case.diagnosis_reasoning or case.failure_category}",
                rationale=top_erv.rationale,
                expected_recovery_latency_minutes=15,
            )
            ai_metadata = AIExecutionMetadata(
                provider="deterministic_engine",
                model="erv_baseline_v1",
                prompt_version=settings.AI_PROMPT_VERSION,
                latency_ms=0,
                is_fallback=True,
                fallback_reason="AI_DISABLED_IN_CONFIG",
            )
        else:
            try:
                ai_rec, ai_meta = await ai_client.recommend_strategy(ai_context)

                # Check Candidate Membership
                if ai_rec.recommended_action not in candidates:
                    logger.warning(
                        f"AI recommended action '{ai_rec.recommended_action.value}' not in eligible set. Falling back."
                    )
                    ai_recommendation = AIStrategyRecommendation(
                        recommended_action=deterministic_proposed_action,
                        confidence_score=0.5,
                        root_cause_diagnosis=ai_rec.root_cause_diagnosis,
                        rationale=f"[FALLBACK from invalid AI action '{ai_rec.recommended_action.value}'] {top_erv.rationale}",
                        expected_recovery_latency_minutes=15,
                    )
                    ai_metadata = AIExecutionMetadata(
                        provider=ai_meta.provider,
                        model=ai_meta.model,
                        prompt_version=ai_meta.prompt_version,
                        latency_ms=ai_meta.latency_ms,
                        is_fallback=True,
                        fallback_reason=f"INVALID_CANDIDATE_ACTION_{ai_rec.recommended_action.value}",
                    )
                else:
                    ai_recommendation = ai_rec
                    ai_metadata = ai_meta

            except Exception as e:
                logger.warning(f"AI invocation failed: {e}. Executing deterministic ERV fallback.")
                ai_recommendation = AIStrategyRecommendation(
                    recommended_action=deterministic_proposed_action,
                    confidence_score=0.5,
                    root_cause_diagnosis=f"Deterministic fallback diagnosis for '{case.failure_category}'",
                    rationale=f"[FALLBACK: {type(e).__name__}] {top_erv.rationale}",
                    expected_recovery_latency_minutes=15,
                )
                ai_metadata = AIExecutionMetadata(
                    provider="deterministic_fallback",
                    model="fallback_erv_v1",
                    prompt_version=settings.AI_PROMPT_VERSION,
                    latency_ms=0,
                    is_fallback=True,
                    fallback_reason=f"{type(e).__name__}: {str(e)}",
                )

        # 7. Record Non-Blocking Telemetry
        AITelemetryService.record_ai_decision_trace(
            case_id=str(case_id),
            recommendation=ai_recommendation,
            metadata=ai_metadata,
            context_summary={
                "amount_cents": case.amount_at_risk_cents,
                "failure": case.failure_category,
            },
        )

        # 8. Advance State Machine: DIAGNOSING -> STRATEGY_GENERATED
        if case.status == RecoveryCaseStatus.DIAGNOSING:
            CaseStateMachine.validate_transition(case.status, RecoveryCaseStatus.STRATEGY_GENERATED)
            case.status = RecoveryCaseStatus.STRATEGY_GENERATED
            await session.flush()

        # 9. Advance State Machine: STRATEGY_GENERATED -> POLICY_CHECK_PENDING
        if case.status == RecoveryCaseStatus.STRATEGY_GENERATED:
            CaseStateMachine.validate_transition(
                case.status, RecoveryCaseStatus.POLICY_CHECK_PENDING
            )
            case.status = RecoveryCaseStatus.POLICY_CHECK_PENDING
            await session.flush()

        # 10. Policy Engine Evaluation over AI Proposal (Policy ALWAYS wins!)
        policy_eval = PolicyEngine.evaluate(
            proposed_action=ai_recommendation.recommended_action,
            case=case_snapshot,
            context=context,
            policy=policy,
            erv_rankings=ranked_ervs,
        )

        # 11. Update Case Status based on Policy Verdict
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
        case.last_ai_confidence = ai_recommendation.confidence_score
        case.diagnosis_reasoning = ai_recommendation.root_cause_diagnosis

        # 12. Create Authorized Command if an actionable intervention is authorized
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
                    "ai_recommended_action": ai_recommendation.recommended_action.value,
                    "is_fallback": ai_metadata.is_fallback,
                },
            )

        # 13. Persist RecoveryDecisionModel (preserving both AI & Deterministic proposals)
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
            ai_recommended_action=ai_recommendation.recommended_action,
            ai_confidence=ai_recommendation.confidence_score,
            ai_reasoning=ai_recommendation.rationale,
            ai_raw_response={
                "root_cause_diagnosis": ai_recommendation.root_cause_diagnosis,
                "alternative_action": ai_recommendation.alternative_action.value
                if ai_recommendation.alternative_action
                else None,
                "expected_recovery_latency_minutes": ai_recommendation.expected_recovery_latency_minutes,
                "deterministic_recommended_action": deterministic_proposed_action.value,
                "erv_table": erv_summary,
                "ai_metadata": ai_metadata.model_dump(),
            },
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

        # 14. Record Cryptographic Hash Chain Audit Event
        await AuditLedgerService.record_event(
            session=session,
            merchant_id=merchant_id,
            entity_type="RECOVERY_DECISION",
            entity_id=decision_record.id,
            action="AI_RECOVERY_DECISION_EVALUATED",
            actor_type="AI_AGENT",
            actor_id=ai_metadata.model,
            payload={
                "case_id": str(case_id),
                "ai_proposed_action": ai_recommendation.recommended_action.value,
                "deterministic_proposed_action": deterministic_proposed_action.value,
                "authorized_action": policy_eval.authorized_action.value,
                "verdict": policy_eval.verdict.value,
                "rule_code": policy_eval.rule_code,
                "confidence_score": ai_recommendation.confidence_score,
                "is_fallback": ai_metadata.is_fallback,
                "fallback_reason": ai_metadata.fallback_reason,
            },
        )

        logger.info(
            f"AI Decision for Case '{case_id}': AI Proposed '{ai_recommendation.recommended_action.value}' "
            f"(Conf={ai_recommendation.confidence_score:.2f}, Fallback={ai_metadata.is_fallback}) "
            f"-> Policy Verdict '{policy_eval.verdict.value}' -> Authorized '{policy_eval.authorized_action.value}' [{policy_eval.rule_code}]."
        )

        return AIDecisionPipelineResult(
            case_id=case_id,
            eligible_candidates=candidates,
            deterministic_recommendation=deterministic_proposed_action,
            ai_recommendation=ai_recommendation,
            ai_metadata=ai_metadata,
            erv_rankings=ranked_ervs,
            policy_evaluation=policy_eval,
            authorized_command=authorized_cmd,
            decision_record_id=decision_record.id,
        )
