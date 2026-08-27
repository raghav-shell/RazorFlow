"""Non-blocking AI Observability and Telemetry Service."""

import logging
from typing import Any, Dict, Optional

from packages.domain.ai.schemas import AIExecutionMetadata, AIStrategyRecommendation

logger = logging.getLogger(__name__)


class AITelemetryService:
    """
    Non-blocking telemetry tracker for AI strategy invocations.
    Guarantees that telemetry failure will NEVER block or fail the financial decision pipeline.
    """

    @classmethod
    def record_ai_decision_trace(
        cls,
        case_id: str,
        recommendation: Optional[AIStrategyRecommendation],
        metadata: AIExecutionMetadata,
        context_summary: Dict[str, Any],
    ) -> None:
        """
        Records structured telemetry log and non-blocking trace event.
        """
        try:
            logger.info(
                f"[AI Trace] Case '{case_id}': Provider={metadata.provider}, Model={metadata.model}, "
                f"Action={recommendation.recommended_action.value if recommendation else 'FALLBACK'}, "
                f"Confidence={recommendation.confidence_score if recommendation else 0.0}, "
                f"Latency={metadata.latency_ms}ms, Fallback={metadata.is_fallback}"
            )
        except Exception as e:
            # Telemetry errors must never propagate to financial callers
            logger.debug(f"Non-blocking telemetry record failed: {e}")
