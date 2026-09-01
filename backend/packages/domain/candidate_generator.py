"""Candidate Generator for deterministic bounded action generation."""

import logging
from typing import Any, List

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import RecoveryActionType
from packages.domain.strategies import get_all_recovery_strategies

logger = logging.getLogger(__name__)


class CandidateGenerator:
    """
    Deterministically computes the bounded set of eligible RecoveryActionTypes.
    Ensures that structurally impossible or ineligible actions are never passed downstream.
    """

    @classmethod
    def generate_candidates(
        cls,
        case: RecoveryCaseSnapshot,
        context: CaseEnrichmentContext,
        policy: Any,
    ) -> List[RecoveryActionType]:
        """
        Evaluates all registered strategies and returns only those that are eligible.
        If no active intervention is eligible, returns [RecoveryActionType.DO_NOTHING].
        """
        eligible_actions: List[RecoveryActionType] = []

        for strategy in get_all_recovery_strategies():
            # Check if merchant policy explicitly disallows this action
            disallowed_actions = getattr(policy, "disallowed_actions", [])
            if strategy.action_type in disallowed_actions:
                logger.debug(
                    f"Action '{strategy.action_type.value}' excluded by merchant policy disallowed list."
                )
                continue

            try:
                evaluation = strategy.evaluate(case=case, context=context, policy=policy)
                if evaluation.is_eligible:
                    eligible_actions.append(strategy.action_type)
                else:
                    logger.debug(
                        f"Action '{strategy.action_type.value}' ineligible: {evaluation.ineligibility_reason}"
                    )
            except Exception as e:
                logger.warning(
                    f"Error evaluating strategy '{strategy.action_type.value}': {e}. Excluding from candidates."
                )

        # Fallback to DO_NOTHING if empty
        if not eligible_actions or eligible_actions == [RecoveryActionType.DO_NOTHING]:
            return [RecoveryActionType.DO_NOTHING]

        return eligible_actions
