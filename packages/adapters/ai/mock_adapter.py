"""Mock Strategy AI Adapter for deterministic testing and scenario evaluation."""

import asyncio
from typing import Optional, Tuple

from packages.domain.ai.schemas import (
    AIDecisionContext,
    AIExecutionMetadata,
    AIStrategyRecommendation,
)
from packages.domain.enums import RecoveryActionType
from packages.ports.ai_strategy import RecoveryStrategyAIPort


class MockStrategyAIAdapter(RecoveryStrategyAIPort):
    """
    Configurable Mock AI Adapter allowing simulation of all failure modes and custom responses.
    """

    def __init__(
        self,
        force_action: Optional[RecoveryActionType] = None,
        force_confidence: float = 0.95,
        force_diagnosis: str = "Mock root cause diagnosis",
        force_rationale: str = "Mock strategy rationale",
        should_timeout: bool = False,
        should_fail_error: Optional[Exception] = None,
        invalid_action_name: Optional[str] = None,
    ) -> None:
        self.force_action = force_action
        self.force_confidence = force_confidence
        self.force_diagnosis = force_diagnosis
        self.force_rationale = force_rationale
        self.should_timeout = should_timeout
        self.should_fail_error = should_fail_error
        self.invalid_action_name = invalid_action_name

    async def recommend_strategy(
        self,
        context: AIDecisionContext,
    ) -> Tuple[AIStrategyRecommendation, AIExecutionMetadata]:
        if self.should_timeout:
            await asyncio.sleep(0.05)
            raise TimeoutError("Mock AI invocation timed out")

        if self.should_fail_error:
            raise self.should_fail_error

        if self.invalid_action_name:
            raise ValueError(f"Unknown recovery action: '{self.invalid_action_name}'")

        # Pick forced action, or first candidate, or DO_NOTHING
        chosen_action = self.force_action
        if chosen_action is None:
            chosen_action = (
                context.eligible_candidate_actions[0]
                if context.eligible_candidate_actions
                else RecoveryActionType.DO_NOTHING
            )

        # Check candidate membership
        if chosen_action not in context.eligible_candidate_actions:
            raise ValueError(
                f"Recommended action '{chosen_action.value}' not in bounded candidate list: "
                f"{[a.value for a in context.eligible_candidate_actions]}"
            )

        rec = AIStrategyRecommendation(
            recommended_action=chosen_action,
            confidence_score=self.force_confidence,
            root_cause_diagnosis=self.force_diagnosis,
            rationale=self.force_rationale,
            expected_recovery_latency_minutes=15,
        )

        meta = AIExecutionMetadata(
            provider="mock_ai",
            model="mock-gemini-v1",
            prompt_version=context.prompt_version,
            schema_version="v1.0.0",
            latency_ms=10,
            is_fallback=False,
        )

        return rec, meta
