# Conditional JSON type that works with both PostgreSQL (JSONB) and SQLite (JSON).

from sqlalchemy import JSON, TypeDecorator

try:
    # Attempt to import PostgreSQL JSONB type; fallback to generic JSON if unavailable.
    from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
except Exception:
    PG_JSONB = JSON


class ConditionalJSON(TypeDecorator):
    """Use PostgreSQL JSONB when on Postgres, otherwise fallback to generic JSON.
    This allows the same models to work with SQLite for local testing.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB)
        return dialect.type_descriptor(JSON)

# Conditional UUID type that works with both PostgreSQL and SQLite.
try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
except Exception:
    PG_UUID = None

from sqlalchemy import String
import uuid as _uuid

class ConditionalUUID(TypeDecorator):
    """Use PostgreSQL UUID when on Postgres, otherwise fallback to String.
    This allows models to define a UUID column compatible with SQLite.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PG_UUID:
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name == "postgresql":
                return value
            if isinstance(value, _uuid.UUID):
                return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and not isinstance(value, _uuid.UUID):
            return _uuid.UUID(value)
        return value


class ConditionalVector(TypeDecorator):
    """pgvector on PostgreSQL, JSON list elsewhere (SQLite tests)."""

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 768, *args, **kwargs):
        self.dim = dim
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except Exception:
                return dialect.type_descriptor(PG_JSONB)
        return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return list(value)

