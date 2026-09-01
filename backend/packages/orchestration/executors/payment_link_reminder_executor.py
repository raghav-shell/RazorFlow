"""Payment Link Reminder Executor dispatching customer follow-ups via PaymentGatewayPort."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from packages.domain.commands import RecoveryCommand
from packages.domain.enums import RecoveryActionType, RecoveryAttemptStatus, RecoveryCaseStatus
from packages.orchestration.executors.base import BaseActionExecutor, ExecutionResult
from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.ports.payment_gateway import GatewayProviderConfig, PaymentGatewayPort

logger = logging.getLogger(__name__)


class PaymentLinkReminderExecutor(BaseActionExecutor):
    """
    Executes CUSTOMER_REMINDER commands by triggering an official notification on an active payment link.
    """

    @property
    def action_type(self) -> RecoveryActionType:
        return RecoveryActionType.CUSTOMER_REMINDER

    async def execute(
        self,
        session: AsyncSession,
        command: RecoveryCommand,
        case: RecoveryCaseModel,
        attempt: RecoveryAttemptModel,
        gateway: PaymentGatewayPort,
    ) -> ExecutionResult:
        settings = get_settings()

        # 1. Resolve active payment link ID from prior successful attempts
        stmt = (
            select(RecoveryAttemptModel)
            .where(
                RecoveryAttemptModel.case_id == case.id,
                RecoveryAttemptModel.action_type == RecoveryActionType.PAYMENT_LINK,
                RecoveryAttemptModel.gateway_reference_id.isnot(None),
                RecoveryAttemptModel.status.in_(
                    [RecoveryAttemptStatus.ACKNOWLEDGED, RecoveryAttemptStatus.SUCCEEDED]
                ),
            )
            .order_by(RecoveryAttemptModel.created_at.desc())
            .limit(1)
        )
        prior_link_attempt = (await session.execute(stmt)).scalar_one_or_none()

        if not prior_link_attempt or not prior_link_attempt.gateway_reference_id:
            logger.warning(
                f"Cannot send reminder for Case '{case.id}': No active payment link found."
            )
            return ExecutionResult(
                is_success=False,
                attempt_status=RecoveryAttemptStatus.FAILED,
                target_case_status=RecoveryCaseStatus.DIAGNOSING,
                error_message="No active payment link reference found on case to send reminder.",
            )

        gateway_link_id = prior_link_attempt.gateway_reference_id

        # 2. Build Gateway Provider Configuration
        merchant = await session.get(MerchantModel, case.merchant_id)
        if not merchant:
            return ExecutionResult(
                is_success=False,
                attempt_status=RecoveryAttemptStatus.FAILED,
                target_case_status=RecoveryCaseStatus.UNRECOVERABLE,
                error_message=f"Merchant {case.merchant_id} not found.",
            )

        prov_stmt = select(MerchantProviderConfigModel).where(
            MerchantProviderConfigModel.merchant_id == case.merchant_id,
            MerchantProviderConfigModel.provider == "RAZORPAY",
            MerchantProviderConfigModel.is_active.is_(True),
        )
        prov_cfg = (await session.execute(prov_stmt)).scalar_one_or_none()

        key_id = (
            prov_cfg.key_id if prov_cfg else (settings.RAZORPAY_KEY_ID or "rzp_test_placeholder")
        )
        key_secret = settings.RAZORPAY_KEY_SECRET or "rzp_test_secret"
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET or "rzp_webhook_secret"
        is_test_mode = prov_cfg.is_test_mode if prov_cfg else settings.RAZORPAY_MODE == "test"

        config = GatewayProviderConfig(
            key_id=key_id,
            key_secret=key_secret,
            webhook_secret=webhook_secret,
            is_test_mode=is_test_mode,
        )

        # 3. Send Notification via Port with exception safety
        try:
            notif_res = await gateway.send_payment_link_reminder(
                config=config,
                gateway_link_id=gateway_link_id,
                medium="sms",
            )
        except Exception as e:
            logger.error(f"Gateway send_payment_link_reminder raised exception: {e}")
            return ExecutionResult(
                is_success=False,
                attempt_status=RecoveryAttemptStatus.FAILED,
                target_case_status=RecoveryCaseStatus.WAITING_EXTERNAL,
                gateway_reference_id=gateway_link_id,
                error_message=f"GATEWAY_ERROR: {type(e).__name__} - {str(e)}",
                is_retryable=True,
            )

        if notif_res.is_success:
            logger.info(
                f"Payment link reminder sent for Link '{gateway_link_id}' on Case '{case.id}'."
            )
            return ExecutionResult(
                is_success=True,
                attempt_status=RecoveryAttemptStatus.ACKNOWLEDGED,
                target_case_status=RecoveryCaseStatus.WAITING_EXTERNAL,
                gateway_reference_id=gateway_link_id,
                execution_payload={
                    "gateway_link_id": gateway_link_id,
                    "medium": "sms",
                    "status": "sent",
                },
                gateway_response=notif_res.raw_response,
            )

        logger.warning(
            f"Failed to send reminder for Link '{gateway_link_id}' on Case '{case.id}': {notif_res.error_message}"
        )
        return ExecutionResult(
            is_success=False,
            attempt_status=RecoveryAttemptStatus.FAILED,
            target_case_status=RecoveryCaseStatus.WAITING_EXTERNAL,
            gateway_reference_id=gateway_link_id,
            error_message=notif_res.error_message,
            gateway_response=notif_res.raw_response,
            is_retryable=notif_res.is_retryable,
        )
