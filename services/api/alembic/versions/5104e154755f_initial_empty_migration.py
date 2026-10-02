"""initial_empty_migration

Revision ID: 5104e154755f
Revises: 
Create Date: 2026-10-02 13:54:05.110137

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '5104e154755f'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
