"""Unit tests for cryptographic utilities and hash-chain audit ledger calculation."""

from packages.common.crypto import (
    compute_audit_event_hash,
    compute_sha256,
    verify_hmac_sha256,
)


def test_compute_sha256():
    digest = compute_sha256("test-input")
    assert len(digest) == 64
    assert digest == compute_sha256("test-input")


def test_hmac_sha256_verification():
    secret = "rzp_webhook_secret_key_123"
    body = b'{"event":"payment.failed","payload":{"payment":{"id":"pay_123"}}}'

    # Compute expected signature
    import hashlib
    import hmac

    valid_sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    assert verify_hmac_sha256(body, secret, valid_sig) is True
    assert verify_hmac_sha256(body, secret, "invalid_signature_hex") is False
    assert verify_hmac_sha256(b"different body", secret, valid_sig) is False


def test_audit_event_hash_chaining():
    # Genesis event (seq=1, prev_hash='0'*64)
    genesis_prev = "0" * 64
    payload_1 = {"case_id": "case-001", "action": "DETECTED"}

    hash_1 = compute_audit_event_hash(
        sequence_number=1,
        prev_event_hash=genesis_prev,
        entity_type="RECOVERY_CASE",
        entity_id="case-001",
        action="DETECTED",
        actor_type="SYSTEM",
        actor_id="webhook-ingest",
        payload=payload_1,
        timestamp_iso="2026-08-27T15:00:00Z",
    )
    assert len(hash_1) == 64

    # Second event chained from hash_1
    payload_2 = {"case_id": "case-001", "action": "APPROVED"}
    hash_2 = compute_audit_event_hash(
        sequence_number=2,
        prev_event_hash=hash_1,
        entity_type="RECOVERY_CASE",
        entity_id="case-001",
        action="APPROVED",
        actor_type="POLICY_ENGINE",
        actor_id="policy-engine-v1",
        payload=payload_2,
        timestamp_iso="2026-08-27T15:01:00Z",
    )
    assert len(hash_2) == 64
    assert hash_2 != hash_1

    # Tampering with payload_1 must change hash_1 and invalidate the chain
    tampered_payload_1 = {"case_id": "case-001", "action": "TAMPERED"}
    tampered_hash_1 = compute_audit_event_hash(
        sequence_number=1,
        prev_event_hash=genesis_prev,
        entity_type="RECOVERY_CASE",
        entity_id="case-001",
        action="DETECTED",
        actor_type="SYSTEM",
        actor_id="webhook-ingest",
        payload=tampered_payload_1,
        timestamp_iso="2026-08-27T15:00:00Z",
    )
    assert tampered_hash_1 != hash_1
