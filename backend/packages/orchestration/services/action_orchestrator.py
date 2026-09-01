"""Action Orchestrator coordinating idempotent execution of authorized RecoveryCommands."""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.adapters.razorpay.gateway_adapter import RazorpayGatewayAdapter
from packages.domain.commands import RecoveryCommand
from packages.domain.enums import RecoveryActionType, RecoveryAttemptStatus, RecoveryCaseStatus
from packages.domain.state_machine import AttemptStateMachine, CaseStateMachine
from packages.orchestration.executors import get_executor_for_action
from packages.persistence.audit_ledger import AuditLedgerService
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.ports.payment_gateway import PaymentGatewayPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrchestrationResult:
    """Auditable result of command execution orchestration."""

    case_id: uuid.UUID
    attempt_id: uuid.UUID
    idempotency_key: str
    action_type: RecoveryActionType
    attempt_status: RecoveryAttemptStatus
    case_status: RecoveryCaseStatus
    gateway_reference_id: Optional[str]
    is_duplicate_execution: bool = False
    error_message: Optional[str] = None


class ActionOrchestrator:
    """
    Authoritative service for executing RecoveryCommands.
    Enforces PostgreSQL row-level locks, idempotency keys, state machines, and audit logging.
    """

    @classmethod
    async def execute_command(
        cls,
        session: AsyncSession,
        command: RecoveryCommand,
        decision_id: Optional[uuid.UUID] = None,
        gateway: Optional[PaymentGatewayPort] = None,
    ) -> OrchestrationResult:
        now = datetime.now(timezone.utc)
        gateway_port = gateway or RazorpayGatewayAdapter()

        # 1. Acquire row-level lock on RecoveryCaseModel
        stmt = (
            select(RecoveryCaseModel)
            .where(RecoveryCaseModel.id == command.case_id)
            .with_for_update()
        )
        case = (await session.execute(stmt)).scalar_one_or_none()

        if not case:
            raise ValueError(f"RecoveryCase '{command.case_id}' not found.")

        # 2. Check if an attempt with this exact idempotency key already exists
        existing_attempt_stmt = select(RecoveryAttemptModel).where(
            RecoveryAttemptModel.idempotency_key == command.idempotency_key
        )
        existing_attempt = (await session.execute(existing_attempt_stmt)).scalar_one_or_none()

        if existing_attempt:
            logger.info(
                f"Idempotency hit: Attempt with key '{command.idempotency_key}' already executed "
                f"(Status: {existing_attempt.status.value}). Returning existing record."
            )
            return OrchestrationResult(
                case_id=case.id,
                attempt_id=existing_attempt.id,
                idempotency_key=existing_attempt.idempotency_key,
                action_type=existing_attempt.action_type,
                attempt_status=existing_attempt.status,
                case_status=case.status,
                gateway_reference_id=existing_attempt.gateway_reference_id,
                is_duplicate_execution=True,
            )

        # 3. Check that case is not already in a terminal state
        terminal_statuses = {
            RecoveryCaseStatus.RECOVERED,
            RecoveryCaseStatus.UNRECOVERABLE,
            RecoveryCaseStatus.EXPIRED,
            RecoveryCaseStatus.STOPPED,
        }
        if case.status in terminal_statuses:
            logger.warning(
                f"Cannot execute command on case '{case.id}' in terminal status '{case.status.value}'."
            )
            raise ValueError(f"Case '{case.id}' is in terminal status '{case.status.value}'.")

        # 4. Advance Case State Machine: APPROVED -> EXECUTING (or ESCALATED -> EXECUTING)
        if case.status in (RecoveryCaseStatus.APPROVED, RecoveryCaseStatus.ESCALATED):
            CaseStateMachine.validate_transition(case.status, RecoveryCaseStatus.EXECUTING)
            case.status = RecoveryCaseStatus.EXECUTING
            await session.flush()

        # 5. Create RecoveryAttemptModel in DRAFT status
        attempt = RecoveryAttemptModel(
            case_id=case.id,
            merchant_id=case.merchant_id,
            decision_id=decision_id,
            action_type=command.action_type,
            idempotency_key=command.idempotency_key,
            status=RecoveryAttemptStatus.DRAFT,
            execution_payload=command.payload,
            gateway_response={},
        )
        session.add(attempt)
        await session.flush()

        # 6. Record Audit Event: ATTEMPT_CREATED
        await AuditLedgerService.record_event(
            session=session,
            merchant_id=case.merchant_id,
            entity_type="RECOVERY_ATTEMPT",
            entity_id=attempt.id,
            action="ATTEMPT_CREATED",
            actor_type="SYSTEM",
            actor_id="action-orchestrator",
            payload={
                "case_id": str(case.id),
                "action_type": command.action_type.value,
                "idempotency_key": command.idempotency_key,
            },
        )

        # 7. Advance Attempt State Machine: DRAFT -> DISPATCHED
        AttemptStateMachine.validate_transition(attempt.status, RecoveryAttemptStatus.DISPATCHED)
        attempt.status = RecoveryAttemptStatus.DISPATCHED
        attempt.dispatched_at = now
        await session.flush()

        # 8. Dispatch to Action Executor
        executor = get_executor_for_action(command.action_type)
        exec_res = await executor.execute(
            session=session,
            command=command,
            case=case,
            attempt=attempt,
            gateway=gateway_port,
        )

        # 9. Update Attempt Record with Execution Result
        if AttemptStateMachine.can_transition(attempt.status, exec_res.attempt_status):
            AttemptStateMachine.validate_transition(attempt.status, exec_res.attempt_status)
            attempt.status = exec_res.attempt_status

        attempt.gateway_reference_id = exec_res.gateway_reference_id
        attempt.gateway_response = exec_res.gateway_response
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.error_message = exec_res.error_message
        if exec_res.execution_payload:
            attempt.execution_payload = {**attempt.execution_payload, **exec_res.execution_payload}

        # 10. Advance Case State Machine: EXECUTING -> Target Status
        if CaseStateMachine.can_transition(case.status, exec_res.target_case_status):
            CaseStateMachine.validate_transition(case.status, exec_res.target_case_status)
            case.status = exec_res.target_case_status

        case.current_attempt_count += 1
        case.last_attempt_at = now
        await session.flush()

        # 11. Record Audit Event: EXECUTION_COMPLETED / GATEWAY_ACCEPTED / FAILED
        audit_action = "GATEWAY_ACCEPTED" if exec_res.is_success else "EXECUTION_FAILED"
        await AuditLedgerService.record_event(
            session=session,
            merchant_id=case.merchant_id,
            entity_type="RECOVERY_ATTEMPT",
            entity_id=attempt.id,
            action=audit_action,
            actor_type="SYSTEM",
            actor_id="action-orchestrator",
            payload={
                "case_id": str(case.id),
                "attempt_id": str(attempt.id),
                "action_type": command.action_type.value,
                "is_success": exec_res.is_success,
                "gateway_reference_id": exec_res.gateway_reference_id,
                "target_case_status": case.status.value,
                "error_message": exec_res.error_message,
            },
        )

        logger.info(
            f"ActionOrchestrator: Executed '{command.action_type.value}' on Case '{case.id}'. "
            f"Attempt Status: '{attempt.status.value}', Case Status: '{case.status.value}', Ref: '{exec_res.gateway_reference_id}'."
        )

        return OrchestrationResult(
            case_id=case.id,
            attempt_id=attempt.id,
            idempotency_key=attempt.idempotency_key,
            action_type=attempt.action_type,
            attempt_status=attempt.status,
            case_status=case.status,
            gateway_reference_id=attempt.gateway_reference_id,
            is_duplicate_execution=False,
            error_message=exec_res.error_message,
        )
