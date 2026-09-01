"""Cryptographic helpers for tamper-evident hash chaining and HMAC validation."""

import hashlib
import hmac
import json
from typing import Any, Dict


def compute_sha256(data: str) -> str:
    """Computes standard hex SHA-256 digest of input UTF-8 string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_audit_event_hash(
    sequence_number: int,
    prev_event_hash: str,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_type: str,
    actor_id: str,
    payload: Dict[str, Any],
    timestamp_iso: str,
) -> str:
    """
    Computes a cryptographic hash for an audit ledger entry in an append-only hash chain.
    Ensures sequential tamper evidence across the entire tenant history.
    """
    # Deterministic JSON canonical representation of payload
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    preimage = (
        f"{sequence_number}|{prev_event_hash}|{entity_type}|{entity_id}|"
        f"{action}|{actor_type}|{actor_id}|{canonical_payload}|{timestamp_iso}"
    )
    return compute_sha256(preimage)


def generate_hmac_sha256(payload_bytes: bytes, secret: str) -> str:
    """Computes hex HMAC-SHA256 signature of input payload bytes."""
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()


def verify_hmac_sha256(payload_bytes: bytes, secret: str, received_signature: str) -> bool:
    """
    Verifies HMAC-SHA256 signature using constant-time comparison to prevent timing attacks.
    """
    expected_signature = generate_hmac_sha256(payload_bytes, secret)
    return hmac.compare_digest(expected_signature, received_signature)
