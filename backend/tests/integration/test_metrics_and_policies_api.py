"""Integration tests for Metrics, Policy Studio, Decisions Explorer, Audit Ledger, and Demo endpoints."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from packages.domain.enums import (
    FailureCategory,
    OrderStatus,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.persistence.models.recovery_outcome import RecoveryOutcomeModel


@pytest.mark.asyncio
async def test_metrics_api(async_client: AsyncClient, async_db_session: AsyncSession):
    merchant = MerchantModel(name="Metrics Store", slug="metrics-store", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id="ord_m1",
        amount_cents=1000000,
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=1000000,
        amount_recovered_cents=1000000,
        currency="INR",
        status=RecoveryCaseStatus.RECOVERED,
        failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    outcome = RecoveryOutcomeModel(
        case_id=case.id,
        merchant_id=merchant.id,
        is_successful=True,
        amount_recovered_cents=1000000,
        cost_incurred_cents=200,
        net_recovery_cents=999800,
        recovery_method=RecoveryActionType.PAYMENT_LINK,
        verification_source="TEST",
    )
    async_db_session.add(outcome)
    await async_db_session.commit()

    resp = await async_client.get("/api/v1/metrics?merchant_slug=metrics-store")
    assert resp.status_code == 200
    data = resp.json()
    assert data["revenue_at_risk_cents"] == 1000000
    assert data["verified_revenue_recovered_cents"] == 1000000
    assert data["net_recovered_revenue_cents"] == 999800
    assert data["recovery_rate_percentage"] == 100.0


@pytest.mark.asyncio
async def test_policies_api_crud_and_preview(
    async_client: AsyncClient, async_db_session: AsyncSession
):
    merchant = MerchantModel(name="Policy Store", slug="policy-store", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.commit()

    # 1. Get default policy
    get_res = await async_client.get("/api/v1/policies?merchant_slug=policy-store")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["active_policy"]["policy_version"] == 1
    assert data["active_policy"]["high_value_escalation_threshold_cents"] == 5000000

    # 2. Update policy
    update_res = await async_client.post(
        "/api/v1/policies?merchant_slug=policy-store",
        json={
            "max_allowed_attempts": 3,
            "recovery_window_hours": 48,
            "cooldown_period_minutes": 15,
            "high_value_escalation_threshold_cents": 1000000,  # ₹10,000
            "disallowed_actions": [],
            "require_human_escalation_for_high_risk": True,
            "auto_retry_transient_failures": True,
        },
    )
    assert update_res.status_code == 200
    up_data = update_res.json()
    assert up_data["policy_version"] == 2

    # 3. Preview Simulator
    prev_res = await async_client.post(
        "/api/v1/policies/preview?merchant_slug=policy-store",
        json={
            "candidate_action": "PAYMENT_LINK",
            "amount_at_risk_cents": 2000000,  # ₹20,000 > ₹10,000 threshold
            "current_attempt_count": 0,
            "failure_category": "INSUFFICIENT_FUNDS",
        },
    )
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["was_overridden"] is True
    assert prev_data["authorized_action"] == "HUMAN_ESCALATION"


@pytest.mark.asyncio
async def test_demo_scenario_launcher(async_client: AsyncClient, async_db_session: AsyncSession):
    # Launch Scenario 1
    res = await async_client.post(
        "/api/v1/demo/seed?merchant_slug=demo-eval",
        json={"scenario_id": "scenario_1"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "scenario_1"
    assert data["final_status"] == "RECOVERED"
    assert data["ai_action"] == "PAYMENT_LINK"

    # Launch Scenario 3 (High Value Override)
    res3 = await async_client.post(
        "/api/v1/demo/seed?merchant_slug=demo-eval",
        json={"scenario_id": "scenario_3"},
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["authorized_action"] == "HUMAN_ESCALATION"
    assert data3["final_status"] == "ESCALATED"

    # Launch Scenario 2 (Bank Outage)
    res2 = await async_client.post(
        "/api/v1/demo/seed?merchant_slug=demo-eval",
        json={"scenario_id": "scenario_2"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["ai_action"] == "WAIT_AND_REASSESS"
    assert data2["final_status"] == "WAITING_EXTERNAL"

    # Launch Scenario 4 (AI Fallback)
    res4 = await async_client.post(
        "/api/v1/demo/seed?merchant_slug=demo-eval",
        json={"scenario_id": "scenario_4"},
    )
    assert res4.status_code == 200
    data4 = res4.json()
    assert data4["final_status"] == "WAITING_EXTERNAL"


@pytest.mark.asyncio
async def test_demo_cohort_reset_and_seed(
    async_client: AsyncClient, async_db_session: AsyncSession
):
    # 1. Test Seed Cohort
    seed_res = await async_client.post("/api/v1/demo/seed-cohort?merchant_slug=cohort-store")
    assert seed_res.status_code == 200
    seed_data = seed_res.json()
    assert seed_data["status"] == "success"
    assert seed_data["total_seeded_cases"] == 22
    assert seed_data["cohort_breakdown"]["authentication_dropoffs"] == 5
    assert seed_data["cohort_breakdown"]["bank_outages"] == 5
    assert seed_data["cohort_breakdown"]["insufficient_funds"] == 5
    assert seed_data["cohort_breakdown"]["permanent_declines"] == 3
    assert seed_data["cohort_breakdown"]["fraud_risk_blocks"] == 2
    assert seed_data["cohort_breakdown"]["high_value_failures"] == 2

    # 2. Test Reset and Seed
    reset_res = await async_client.post("/api/v1/demo/reset-and-seed?merchant_slug=cohort-store")
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["status"] == "reset_and_seeded_successfully"
    assert reset_data["purged_demo_cases_count"] == 22
    assert reset_data["total_seeded_cases"] == 22
