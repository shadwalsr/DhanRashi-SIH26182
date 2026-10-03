from typing import Any

from app.db.base import Base, TimestampMixin
from app.db.models import (
    AuditLog,
    Case,
    CaseMember,
    CaseNote,
    Investigation,
    Org,
    Role,
    User,
)
from app.db.session import get_db

__all__ = [
    "AsyncSessionLocal",
    "AuditLog",
    "Base",
    "Case",
    "CaseMember",
    "CaseNote",
    "Investigation",
    "Org",
    "Role",
    "TimestampMixin",
    "User",
    "async_engine",
    "get_db",
    "sync_engine",
]


def __getattr__(name: str) -> Any:
    if name in ("AsyncSessionLocal", "async_engine", "sync_engine"):
        import app.db.session as session_mod
        return getattr(session_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
