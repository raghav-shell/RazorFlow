"""Deterministic Expected Recovery Value (ERV) Ranker."""

from typing import List

from packages.domain.enums import RecoveryActionType
from packages.domain.scoring.erv_calculator import ERVResult

# Deterministic priority ordering for tie-breaking
_ACTION_TIE_BREAKER_ORDER = {
    RecoveryActionType.PAYMENT_LINK: 1,
    RecoveryActionType.CUSTOMER_REMINDER: 2,
    RecoveryActionType.WAIT_AND_REASSESS: 3,
    RecoveryActionType.HUMAN_ESCALATION: 4,
    RecoveryActionType.DO_NOTHING: 5,
}


class ERVRanker:
    """
    Ranks candidate actions deterministically by Expected Net Recovery Value.
    Strictly free from LLM influence.
    """

    @classmethod
    def rank_candidates(cls, erv_results: List[ERVResult]) -> List[ERVResult]:
        """
        Sorts ERV results using deterministic multi-level criteria:
        1. Net ERV (Descending)
        2. Recovery Probability (Descending)
        3. Intervention Cost (Ascending)
        4. Action type static priority order (Ascending)
        """

        def sort_key(item: ERVResult):
            return (
                -item.expected_net_recovery_value_cents,
                -item.recovery_probability.value,
                item.intervention_cost_cents,
                _ACTION_TIE_BREAKER_ORDER.get(item.action, 99),
            )

        return sorted(erv_results, key=sort_key)
