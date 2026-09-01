"""Payment Link Executor creating hosted payment links via PaymentGatewayPort."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from packages.domain.commands import RecoveryCommand
from packages.domain.enums import RecoveryActionType, RecoveryAttemptStatus, RecoveryCaseStatus
from packages.orchestration.executors.base import BaseActionExecutor, ExecutionResult
from packages.persistence.models.customer import CustomerModel
from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.ports.payment_gateway import GatewayProviderConfig, PaymentGatewayPort

logger = logging.getLogger(__name__)


class PaymentLinkExecutor(BaseActionExecutor):
    """
    Executes PAYMENT_LINK recovery commands by requesting an idempotent Razorpay Payment Link.
    """

    @property
    def action_type(self) -> RecoveryActionType:
        return RecoveryActionType.PAYMENT_LINK

    async def execute(
        self,
        session: AsyncSession,
        command: RecoveryCommand,
        case: RecoveryCaseModel,
        attempt: RecoveryAttemptModel,
        gateway: PaymentGatewayPort,
    ) -> ExecutionResult:
        settings = get_settings()

        # 1. Fetch Order and Customer data
        order = await session.get(OrderModel, case.order_id)
        if not order:
            return ExecutionResult(
                is_success=False,
                attempt_status=RecoveryAttemptStatus.FAILED,
                target_case_status=RecoveryCaseStatus.UNRECOVERABLE,
                error_message=f"Order {case.order_id} not found in database.",
            )

        customer: Optional[CustomerModel] = None
        if case.customer_id:
            customer = await session.get(CustomerModel, case.customer_id)

        merchant = await session.get(MerchantModel, case.merchant_id)
        if not merchant:
            return ExecutionResult(
                is_success=False,
                attempt_status=RecoveryAttemptStatus.FAILED,
                target_case_status=RecoveryCaseStatus.UNRECOVERABLE,
                error_message=f"Merchant {case.merchant_id} not found in database.",
            )

        # 2. Build Gateway Provider Configuration
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

        expire_by_timestamp = int(command.deadline_at.timestamp())
        contact = customer.phone if customer else None
        email = customer.email if customer else None
        name = customer.name if customer else None

        # 3. Request Payment Link via Port with exception safety
        try:
            link_res = await gateway.create_payment_link(
                config=config,
                order_id=order.external_order_id,
                amount_cents=command.amount_at_risk_cents,
                currency=command.currency,
                customer_contact=contact,
                customer_email=email,
                customer_name=name,
                description=f"Recovery Link for Order {order.external_order_id}",
                expire_by_timestamp=expire_by_timestamp,
                idempotency_key=command.idempotency_key,
                reference_id=str(case.id),
            )
        except Exception as e:
            logger.error(f"Gateway create_payment_link raised exception: {e}")
            return ExecutionResult(
                is_success=False,
                attempt_status=RecoveryAttemptStatus.FAILED,
                target_case_status=RecoveryCaseStatus.DIAGNOSING,
                error_message=f"GATEWAY_ERROR: {type(e).__name__} - {str(e)}",
                is_retryable=True,
            )

        if link_res.is_success:
            logger.info(
                f"Payment Link '{link_res.gateway_link_id}' created for Case '{case.id}'. "
                f"URL: {link_res.short_url}"
            )
            return ExecutionResult(
                is_success=True,
                attempt_status=RecoveryAttemptStatus.ACKNOWLEDGED,
                target_case_status=RecoveryCaseStatus.WAITING_EXTERNAL,
                gateway_reference_id=link_res.gateway_link_id,
                execution_payload={
                    "order_id": str(order.id),
                    "external_order_id": order.external_order_id,
                    "short_url": link_res.short_url,
                    "amount_cents": command.amount_at_risk_cents,
                    "currency": command.currency,
                },
                gateway_response=link_res.raw_response,
            )

        logger.warning(
            f"Payment Link creation failed for Case '{case.id}': {link_res.error_code} - {link_res.error_message}"
        )
        return ExecutionResult(
            is_success=False,
            attempt_status=RecoveryAttemptStatus.FAILED,
            target_case_status=RecoveryCaseStatus.DIAGNOSING
            if link_res.is_retryable
            else RecoveryCaseStatus.WAITING_EXTERNAL,
            error_message=f"{link_res.error_code}: {link_res.error_message}",
            gateway_response=link_res.raw_response,
            is_retryable=link_res.is_retryable,
        )
