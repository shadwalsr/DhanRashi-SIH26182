"""create vasp registry tables

Revision ID: b2c3d4e5f6g7
Revises: 
Create Date: 2026-10-02 09:15:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # vasps table
    op.create_table(
        'vasps',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('vasp_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('jurisdiction', sa.String(length=2), nullable=True),
        sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vasp_id')
    )

    # vasp_clusters table
    op.create_table(
        'vasp_clusters',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('cluster_id', sa.String(length=255), nullable=False),
        sa.Column('vasp_id_fk', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['vasp_id_fk'], ['vasps.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cluster_id')
    )

    # vasp_addresses table
    op.create_table(
        'vasp_addresses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('record_id', sa.String(length=255), nullable=False),
        sa.Column('vasp_id_fk', sa.Uuid(), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('chain', sa.String(length=50), nullable=False),
        sa.Column('address_type', sa.String(length=50), nullable=False),
        sa.Column('cluster_id', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=False),
        sa.Column('source_reference', sa.String(length=255), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('first_seen', sa.Date(), nullable=False),
        sa.Column('last_verified', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('conflict', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['vasp_id_fk'], ['vasps.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chain', 'address', 'vasp_id_fk', 'valid_to', name='uq_chain_address_vasp_validity'),
        sa.UniqueConstraint('record_id')
    )

    # registry_snapshots table
    op.create_table(
        'registry_snapshots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('snapshot_id', sa.String(length=255), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=True),
        sa.Column('record_count', sa.Integer(), nullable=False),
        sa.Column('snapshot_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snapshot_id')
    )


def downgrade() -> None:
    op.drop_table('registry_snapshots')
    op.drop_table('vasp_addresses')
    op.drop_table('vasp_clusters')
    op.drop_table('vasps')
