"""Abstract port interface for AI Recovery Strategy Agent."""

from typing import Protocol, Tuple

from packages.domain.ai.schemas import (
    AIDecisionContext,
    AIExecutionMetadata,
    AIStrategyRecommendation,
)


class RecoveryStrategyAIPort(Protocol):
    """
    Provider-agnostic interface for AI strategy recommendation agents.
    Implementations (Gemini, Mock, etc.) must fulfill this protocol.
    """

    async def recommend_strategy(
        self,
        context: AIDecisionContext,
    ) -> Tuple[AIStrategyRecommendation, AIExecutionMetadata]:
        """
        Takes structured decision context and returns verified AI recommendation along with telemetry metadata.
        """
        ...
