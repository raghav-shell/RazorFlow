"""Base Action Executor interface and result dataclass."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from packages.domain.commands import RecoveryCommand
from packages.domain.enums import RecoveryActionType, RecoveryAttemptStatus, RecoveryCaseStatus
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.ports.payment_gateway import PaymentGatewayPort


@dataclass(frozen=True)
class ExecutionResult:
    """Result of an action execution dispatched by ActionOrchestrator."""

    is_success: bool
    attempt_status: RecoveryAttemptStatus
    target_case_status: RecoveryCaseStatus
    gateway_reference_id: Optional[str] = None
    execution_payload: Dict[str, Any] = field(default_factory=dict)
    gateway_response: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    is_retryable: bool = False


class BaseActionExecutor(ABC):
    """
    Abstract Action Executor handling a specific RecoveryActionType.
    Executors MUST be called ONLY via ActionOrchestrator with an authorized RecoveryCommand.
    """

    @property
    @abstractmethod
    def action_type(self) -> RecoveryActionType:
        """The action type handled by this executor."""
        pass

    @abstractmethod
    async def execute(
        self,
        session: AsyncSession,
        command: RecoveryCommand,
        case: RecoveryCaseModel,
        attempt: RecoveryAttemptModel,
        gateway: PaymentGatewayPort,
    ) -> ExecutionResult:
        """Executes the authorized recovery action."""
        pass
