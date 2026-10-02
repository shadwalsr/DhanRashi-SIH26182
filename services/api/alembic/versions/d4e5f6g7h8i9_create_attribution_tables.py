"""create attribution tables

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-10-02 18:30:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'attribution_results',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('candidate_vasp_id', sa.String(length=255), nullable=False),
        sa.Column('candidate_vasp_name', sa.String(length=255), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('competing_candidates', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('evidence_gate_passed', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('disposition', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('disposition_notes', sa.Text(), nullable=True),
        sa.Column('disposition_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disposition_user_id', sa.Uuid(), nullable=True),
        sa.Column('weights_version', sa.String(length=50), nullable=False, server_default='v1.0.0'),
        sa.Column('registry_snapshot_id', sa.String(length=64), nullable=True),
        sa.Column('factors_json', sa.JSON(), nullable=False),
        sa.Column('caps_json', sa.JSON(), nullable=False),
        sa.Column('limitations_json', sa.JSON(), nullable=False),
        sa.Column('supporting_addresses', sa.JSON(), nullable=False),
        sa.Column('evidence_references', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['disposition_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('investigation_id', 'candidate_vasp_id', 'version', name='uq_investigation_candidate_version'),
    )
    op.create_index(op.f('ix_attribution_results_investigation_id'), 'attribution_results', ['investigation_id'], unique=False)
    op.create_index(op.f('ix_attribution_results_candidate_vasp_id'), 'attribution_results', ['candidate_vasp_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_attribution_results_candidate_vasp_id'), table_name='attribution_results')
    op.drop_index(op.f('ix_attribution_results_investigation_id'), table_name='attribution_results')
    op.drop_table('attribution_results')
