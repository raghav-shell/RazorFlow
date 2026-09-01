"""Gemini Strategy AI Adapter implementing structured recovery strategy generation."""

import asyncio
import json
import logging
import time
from typing import Any, Optional, Tuple

from google import genai
from google.genai import types

from packages.domain.ai.context_builder import AIContextBuilder
from packages.domain.ai.schemas import (
    AIDecisionContext,
    AIExecutionMetadata,
    AIStrategyRecommendation,
)
from packages.ports.ai_strategy import RecoveryStrategyAIPort

logger = logging.getLogger(__name__)


class GeminiStrategyAIAdapter(RecoveryStrategyAIPort):
    """
    Concrete adapter connecting to Google Gemini API using structured Pydantic schema generation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3.6-flash",
        timeout_seconds: float = 8.0,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key:
                raise ValueError("Gemini API key is not configured in settings.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def recommend_strategy(
        self,
        context: AIDecisionContext,
    ) -> Tuple[AIStrategyRecommendation, AIExecutionMetadata]:
        start_time = time.perf_counter()
        prompt_text = AIContextBuilder.render_prompt(context)

        try:
            client = self._get_client()

            # Execute Gemini API call with timeout protection
            def _call_gemini() -> Any:
                return client.models.generate_content(
                    model=self.model_name,
                    contents=prompt_text,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=AIStrategyRecommendation,
                        temperature=0.1,  # Low temperature for deterministic adherence
                    ),
                )

            response = await asyncio.wait_for(
                asyncio.to_thread(_call_gemini),
                timeout=self.timeout_seconds,
            )

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Parse and validate structured output
            raw_text = response.text or "{}"
            parsed_dict = json.loads(raw_text)
            recommendation = AIStrategyRecommendation.model_validate(parsed_dict)

            # Candidate Membership Validation: Must belong to eligible candidate list!
            if recommendation.recommended_action not in context.eligible_candidate_actions:
                logger.warning(
                    f"Gemini recommended action '{recommendation.recommended_action.value}' "
                    f"which is NOT in eligible candidate set: {[a.value for a in context.eligible_candidate_actions]}."
                )
                raise ValueError(
                    f"Recommended action '{recommendation.recommended_action.value}' not in bounded candidate list."
                )

            metadata = AIExecutionMetadata(
                provider="gemini",
                model=self.model_name,
                prompt_version=context.prompt_version,
                schema_version="v1.0.0",
                latency_ms=latency_ms,
                is_fallback=False,
            )

            return recommendation, metadata

        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(f"Gemini AI recommendation failed: {e}. Raising for fallback handling.")
            raise
