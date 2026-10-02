"""create evidence and risk tables

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-10-02 22:15:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'e5f6g7h8i9j0'
down_revision = 'd4e5f6g7h8i9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Evidence Ledger Table (FR-EVD-01, FR-EVD-02, FR-EVD-03)
    op.create_table(
        'evidence',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('sequence_num', sa.Integer(), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('provenance_class', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('source_ref', sa.String(length=255), nullable=False),
        sa.Column('raw_hash', sa.String(length=64), nullable=False),
        sa.Column('data_payload', sa.JSON(), nullable=False),
        sa.Column('derived_from', sa.JSON(), nullable=False),
        sa.Column('prev_evidence_hash', sa.String(length=64), nullable=False),
        sa.Column('evidence_hash', sa.String(length=64), nullable=False),
        sa.Column('created_by_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('investigation_id', 'sequence_num', name='uq_evidence_investigation_seq'),
    )
    op.create_index(op.f('ix_evidence_investigation_id'), 'evidence', ['investigation_id'], unique=False)
    op.create_index(op.f('ix_evidence_provenance_class'), 'evidence', ['provenance_class'], unique=False)
    op.create_index(op.f('ix_evidence_evidence_hash'), 'evidence', ['evidence_hash'], unique=False)

    # 2. Risk Assessments Table (FR-RISK-01, FR-RISK-02, FR-RISK-04)
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('target_address', sa.String(length=255), nullable=False),
        sa.Column('chain', sa.String(length=50), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('signals_json', sa.JSON(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('evidence_references', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('investigation_id', 'version', name='uq_risk_investigation_version'),
    )
    op.create_index(op.f('ix_risk_assessments_investigation_id'), 'risk_assessments', ['investigation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_risk_assessments_investigation_id'), table_name='risk_assessments')
    op.drop_table('risk_assessments')
    op.drop_index(op.f('ix_evidence_evidence_hash'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_provenance_class'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_investigation_id'), table_name='evidence')
    op.drop_table('evidence')
