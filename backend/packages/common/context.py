"""Context variable managers for asynchronous request tracing and tenant context."""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

# Context variable for tracing request IDs across async task chains
_request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Context variable for tenant isolation in current execution context
_merchant_id_ctx_var: ContextVar[Optional[UUID]] = ContextVar("merchant_id", default=None)


def set_request_id(request_id: str) -> None:
    """Sets the current request ID context."""
    _request_id_ctx_var.set(request_id)


def get_request_id() -> Optional[str]:
    """Returns the current request ID, if set."""
    return _request_id_ctx_var.get()


def set_current_merchant_id(merchant_id: UUID) -> None:
    """Sets the current active tenant (merchant) context."""
    _merchant_id_ctx_var.set(merchant_id)


def get_current_merchant_id() -> Optional[UUID]:
    """Returns the current active tenant (merchant) ID, if set."""
    return _merchant_id_ctx_var.get()
