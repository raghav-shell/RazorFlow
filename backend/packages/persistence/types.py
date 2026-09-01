"""Portable SQLAlchemy types supporting PostgreSQL natively and SQLite for in-memory testing."""

import json
from typing import Any, List

from sqlalchemy import JSON, String, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

# Portable JSONB type: Uses native JSONB on PostgreSQL and JSON on SQLite
PortableJSON = JSON().with_variant(JSONB(), "postgresql")

# Portable UUID type: Uses native UUID on PostgreSQL and CHAR(36) on SQLite
PortableUUID = String(36).with_variant(UUID(as_uuid=True), "postgresql")


class PortableArray(TypeDecorator):
    """
    Type that renders as native PostgreSQL ARRAY(String) on PostgreSQL,
    and JSON-serialized list of strings on SQLite.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String(50)))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return []
        return value

    def process_result_value(self, value: Any, dialect) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [value]
            except Exception:
                return [value]
        return list(value)
