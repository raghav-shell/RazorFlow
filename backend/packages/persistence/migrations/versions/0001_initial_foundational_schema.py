"""0001_initial_foundational_schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-08-27 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Merchants Table
    op.create_table(
        "merchants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("currency", sa.String(3), server_default="INR", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_merchants_slug"),
    )
    op.create_index("ix_merchants_slug", "merchants", ["slug"])

    # 2. Merchant Provider Configs Table
    op.create_table(
        "merchant_provider_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), server_default="RAZORPAY", nullable=False),
        sa.Column("key_id", sa.String(255), nullable=False),
        sa.Column("key_secret_enc", sa.String(), nullable=False),
        sa.Column("webhook_secret_enc", sa.String(), nullable=False),
        sa.Column("is_test_mode", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("config_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "provider", name="uq_merchant_provider"),
    )
    op.create_index("ix_merchant_provider_configs_merchant_id", "merchant_provider_configs", ["merchant_id"])

    # 3. Customers Table
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_customer_id", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("risk_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("recovery_success_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_failure_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "external_customer_id", name="uq_merchant_customer"),
    )
    op.create_index("ix_customers_merchant_id", "customers", ["merchant_id"])
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_phone", "customers", ["phone"])

    # 4. Orders Table
    order_status_enum = postgresql.ENUM("CREATED", "ATTEMPTED", "PAID", "EXPIRED", "CANCELLED", name="order_status", create_type=False)
    order_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_order_id", sa.String(255), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="INR", nullable=False),
        sa.Column("status", order_status_enum, server_default="CREATED", nullable=False),
        sa.Column("receipt", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "external_order_id", name="uq_merchant_external_order"),
    )
    op.create_index("ix_orders_merchant_id", "orders", ["merchant_id"])
    op.create_index("ix_orders_external_order_id", "orders", ["external_order_id"])

    # 5. Payments Table
    payment_status_enum = postgresql.ENUM("CREATED", "AUTHORIZED", "CAPTURED", "FAILED", "REFUNDED", name="payment_status", create_type=False)
    payment_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_payment_id", sa.String(255), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="INR", nullable=False),
        sa.Column("status", payment_status_enum, nullable=False),
        sa.Column("method", sa.String(50), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_description", sa.Text(), nullable=True),
        sa.Column("error_source", sa.String(50), nullable=True),
        sa.Column("error_step", sa.String(50), nullable=True),
        sa.Column("error_reason", sa.String(100), nullable=True),
        sa.Column("rzp_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "external_payment_id", name="uq_merchant_external_payment"),
    )
    op.create_index("ix_payments_merchant_id", "payments", ["merchant_id"])
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index("ix_payments_external_payment_id", "payments", ["external_payment_id"])

    # 6. Raw Webhook Events Table
    op.create_table(
        "raw_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), server_default="RAZORPAY", nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("signature", sa.String(255), nullable=False),
        sa.Column("headers", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("processed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "event_id", name="uq_merchant_event"),
    )
    op.create_index("ix_raw_webhook_events_merchant_id", "raw_webhook_events", ["merchant_id"])
    op.create_index("ix_raw_webhook_events_processed", "raw_webhook_events", ["processed"])

    # 7. Recovery Cases Table
    recovery_case_status_enum = postgresql.ENUM(
        "DETECTED", "ENRICHING", "DIAGNOSING", "STRATEGY_GENERATED",
        "POLICY_CHECK_PENDING", "APPROVED", "REJECTED", "ESCALATED",
        "EXECUTING", "WAITING_EXTERNAL", "VERIFYING",
        "RECOVERED", "UNRECOVERABLE", "EXPIRED", "STOPPED",
        name="recovery_case_status",
        create_type=False,
    )
    recovery_case_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "recovery_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("initial_payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount_at_risk_cents", sa.BigInteger(), nullable=False),
        sa.Column("amount_recovered_cents", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("currency", sa.String(3), server_default="INR", nullable=False),
        sa.Column("status", recovery_case_status_enum, server_default="DETECTED", nullable=False),
        sa.Column("failure_category", sa.String(100), nullable=True),
        sa.Column("is_transient", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("diagnosis_reasoning", sa.Text(), nullable=True),
        sa.Column("recovery_probability", sa.Float(), nullable=True),
        sa.Column("expected_recovery_value_cents", sa.BigInteger(), nullable=True),
        sa.Column("last_ai_confidence", sa.Float(), nullable=True),
        sa.Column("current_attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_allowed_attempts", sa.Integer(), server_default="2", nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_action_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recovery_cases_merchant_id", "recovery_cases", ["merchant_id"])
    op.create_index("ix_recovery_cases_status", "recovery_cases", ["status"])
    op.create_index(
        "uq_active_order_recovery_case",
        "recovery_cases",
        ["merchant_id", "order_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('RECOVERED', 'UNRECOVERABLE', 'EXPIRED', 'STOPPED')"),
    )

    # 8. Recovery Decisions Table
    recovery_action_type_enum = postgresql.ENUM(
        "PAYMENT_LINK", "CUSTOMER_REMINDER", "WAIT_AND_REASSESS", "HUMAN_ESCALATION", "DO_NOTHING",
        name="recovery_action_type",
        create_type=False,
    )
    recovery_action_type_enum.create(op.get_bind(), checkfirst=True)

    policy_verdict_type_enum = postgresql.ENUM(
        "APPROVED", "REJECTED", "ESCALATED", "MODIFIED",
        name="policy_verdict_type",
        create_type=False,
    )
    policy_verdict_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "recovery_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("eligible_candidate_actions", sa.ARRAY(sa.String(50)), nullable=False),
        sa.Column("ai_recommended_action", recovery_action_type_enum, nullable=False),
        sa.Column("ai_confidence", sa.Float(), nullable=False),
        sa.Column("ai_reasoning", sa.Text(), nullable=False),
        sa.Column("ai_raw_response", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("policy_verdict", policy_verdict_type_enum, nullable=False),
        sa.Column("authorized_action", recovery_action_type_enum, nullable=False),
        sa.Column("policy_rule_triggered", sa.String(255), nullable=True),
        sa.Column("policy_details", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recovery_decisions_case_id", "recovery_decisions", ["case_id"])
    op.create_index("ix_recovery_decisions_merchant_id", "recovery_decisions", ["merchant_id"])

    # 9. Recovery Attempts Table
    recovery_attempt_status_enum = postgresql.ENUM(
        "DRAFT", "DISPATCHED", "ACKNOWLEDGED", "SUCCEEDED", "FAILED", "TIMED_OUT",
        name="recovery_attempt_status",
        create_type=False,
    )
    recovery_attempt_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "recovery_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recovery_decisions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", recovery_action_type_enum, nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("status", recovery_attempt_status_enum, server_default="DRAFT", nullable=False),
        sa.Column("execution_payload", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("gateway_reference_id", sa.String(255), nullable=True),
        sa.Column("gateway_response", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_recovery_attempts_idempotency"),
    )
    op.create_index("ix_recovery_attempts_case_id", "recovery_attempts", ["case_id"])
    op.create_index("ix_recovery_attempts_merchant_id", "recovery_attempts", ["merchant_id"])
    op.create_index("ix_recovery_attempts_idempotency_key", "recovery_attempts", ["idempotency_key"])

    # 10. Recovery Outcomes Table
    op.create_table(
        "recovery_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recovery_cases.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("settling_payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("successful_attempt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recovery_attempts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_successful", sa.Boolean(), nullable=False),
        sa.Column("amount_recovered_cents", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("cost_incurred_cents", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("net_recovery_cents", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("recovery_method", recovery_action_type_enum, nullable=True),
        sa.Column("verification_source", sa.String(100), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recovery_outcomes_case_id", "recovery_outcomes", ["case_id"])
    op.create_index("ix_recovery_outcomes_merchant_id", "recovery_outcomes", ["merchant_id"])

    # 11. Hash-Chain Audit Events Table
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence_number", sa.BigInteger(), nullable=False),
        sa.Column("prev_event_hash", sa.String(64), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("actor_type", sa.String(50), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("state_before", postgresql.JSONB(), nullable=True),
        sa.Column("state_after", postgresql.JSONB(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "sequence_number", name="uq_merchant_audit_seq"),
    )
    op.create_index("ix_audit_events_merchant_id", "audit_events", ["merchant_id"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.create_index("ix_audit_events_event_hash", "audit_events", ["event_hash"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("recovery_outcomes")
    op.drop_table("recovery_attempts")
    op.drop_table("recovery_decisions")
    op.drop_table("recovery_cases")
    op.drop_table("raw_webhook_events")
    op.drop_table("payments")
    op.drop_table("orders")
    op.drop_table("customers")
    op.drop_table("merchant_provider_configs")
    op.drop_table("merchants")
