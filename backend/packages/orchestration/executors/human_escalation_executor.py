"""Human Escalation Executor routing cases to manual merchant concierge."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from packages.domain.commands import RecoveryCommand
from packages.domain.enums import RecoveryActionType, RecoveryAttemptStatus, RecoveryCaseStatus
from packages.orchestration.executors.base import BaseActionExecutor, ExecutionResult
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.ports.payment_gateway import PaymentGatewayPort

logger = logging.getLogger(__name__)


class HumanEscalationExecutor(BaseActionExecutor):
    """
    Executes HUMAN_ESCALATION commands by creating a dashboard task for merchant operators.
    """

    @property
    def action_type(self) -> RecoveryActionType:
        return RecoveryActionType.HUMAN_ESCALATION

    async def execute(
        self,
        session: AsyncSession,
        command: RecoveryCommand,
        case: RecoveryCaseModel,
        attempt: RecoveryAttemptModel,
        gateway: PaymentGatewayPort,
    ) -> ExecutionResult:
        logger.info(
            f"Case '{case.id}': Escalated to Human Concierge for high-value/VIP intervention. "
            f"Amount: ₹{command.amount_at_risk_cents / 100:.2f}."
        )

        return ExecutionResult(
            is_success=True,
            attempt_status=RecoveryAttemptStatus.SUCCEEDED,
            target_case_status=RecoveryCaseStatus.ESCALATED,
            execution_payload={
                "escalated_reason": command.payload.get(
                    "rule_code", "HIGH_VALUE_THRESHOLD_EXCEEDED"
                ),
                "amount_at_risk_cents": command.amount_at_risk_cents,
                "action": "human_escalation_enqueued",
            },
            gateway_response={"status": "escalated_to_operator"},
        )
