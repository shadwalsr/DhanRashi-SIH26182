"""create cross chain tables

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-10-02 23:05:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'f6g7h8i9j0k1'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add via_cross_chain_event_id column to graph_edges
    op.add_column('graph_edges', sa.Column('via_cross_chain_event_id', sa.String(length=255), nullable=True))

    # 2. Bridge Registry Table (FR-XCH-01)
    op.create_table(
        'bridge_registry',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('bridge_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_chain', sa.String(length=50), nullable=False),
        sa.Column('destination_chain', sa.String(length=50), nullable=False),
        sa.Column('source_contract_address', sa.String(length=255), nullable=False),
        sa.Column('destination_contract_address', sa.String(length=255), nullable=False),
        sa.Column('event_abi_signature', sa.Text(), nullable=True),
        sa.Column('fee_percentage', sa.Float(), nullable=False, server_default='0.002'),
        sa.Column('max_time_window_seconds', sa.Integer(), nullable=False, server_default='7200'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bridge_id', name='uq_bridge_registry_bridge_id'),
    )
    op.create_index(op.f('ix_bridge_registry_source_contract_address'), 'bridge_registry', ['source_contract_address'], unique=False)

    # 3. Cross-Chain Events Table (FR-XCH-02, FR-XCH-03)
    op.create_table(
        'cross_chain_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('bridge_id', sa.String(length=100), nullable=False),
        sa.Column('source_chain', sa.String(length=50), nullable=False),
        sa.Column('source_tx_hash', sa.String(length=255), nullable=False),
        sa.Column('source_address', sa.String(length=255), nullable=False),
        sa.Column('destination_chain', sa.String(length=50), nullable=False),
        sa.Column('destination_tx_hash', sa.String(length=255), nullable=True),
        sa.Column('destination_address', sa.String(length=255), nullable=True),
        sa.Column('asset', sa.String(length=50), nullable=False),
        sa.Column('source_amount', sa.Numeric(precision=38, scale=18), nullable=False),
        sa.Column('destination_amount', sa.Numeric(precision=38, scale=18), nullable=True),
        sa.Column('source_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('destination_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('bridge_tx_id', sa.String(length=255), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('is_ambiguous', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('alternatives_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='MATCHED'),
        sa.Column('evidence_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cross_chain_events_investigation_id'), 'cross_chain_events', ['investigation_id'], unique=False)
    op.create_index(op.f('ix_cross_chain_events_source_tx_hash'), 'cross_chain_events', ['source_tx_hash'], unique=False)
    op.create_index(op.f('ix_cross_chain_events_bridge_tx_id'), 'cross_chain_events', ['bridge_tx_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_cross_chain_events_bridge_tx_id'), table_name='cross_chain_events')
    op.drop_index(op.f('ix_cross_chain_events_source_tx_hash'), table_name='cross_chain_events')
    op.drop_index(op.f('ix_cross_chain_events_investigation_id'), table_name='cross_chain_events')
    op.drop_table('cross_chain_events')
    op.drop_index(op.f('ix_bridge_registry_source_contract_address'), table_name='bridge_registry')
    op.drop_table('bridge_registry')
    op.drop_column('graph_edges', 'via_cross_chain_event_id')
