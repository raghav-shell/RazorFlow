"""Wait and Reassess Executor scheduling delay for transient outages."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from packages.domain.commands import RecoveryCommand
from packages.domain.enums import RecoveryActionType, RecoveryAttemptStatus, RecoveryCaseStatus
from packages.orchestration.executors.base import BaseActionExecutor, ExecutionResult
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.ports.payment_gateway import PaymentGatewayPort

logger = logging.getLogger(__name__)


class WaitAndReassessExecutor(BaseActionExecutor):
    """
    Executes WAIT_AND_REASSESS commands by scheduling future reassessment without calling payment APIs.
    """

    @property
    def action_type(self) -> RecoveryActionType:
        return RecoveryActionType.WAIT_AND_REASSESS

    async def execute(
        self,
        session: AsyncSession,
        command: RecoveryCommand,
        case: RecoveryCaseModel,
        attempt: RecoveryAttemptModel,
        gateway: PaymentGatewayPort,
    ) -> ExecutionResult:
        delay_seconds = command.payload.get("reassessment_delay_seconds") or 1800  # Default 30 min
        scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

        case.next_action_scheduled_at = scheduled_time
        logger.info(
            f"Case '{case.id}': Scheduled future reassessment at {scheduled_time.isoformat()} "
            f"(in {delay_seconds}s)."
        )

        return ExecutionResult(
            is_success=True,
            attempt_status=RecoveryAttemptStatus.SUCCEEDED,
            target_case_status=RecoveryCaseStatus.WAITING_EXTERNAL,
            execution_payload={
                "delay_seconds": delay_seconds,
                "scheduled_at": scheduled_time.isoformat(),
                "action": "reassessment_scheduled",
            },
            gateway_response={"status": "scheduled", "scheduled_at": scheduled_time.isoformat()},
        )
