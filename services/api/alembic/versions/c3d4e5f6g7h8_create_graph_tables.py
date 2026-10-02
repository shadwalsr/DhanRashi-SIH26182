"""create graph tables

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-10-02 11:30:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # graph_nodes table
    op.create_table(
        'graph_nodes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('node_key', sa.String(length=255), nullable=False),
        sa.Column('chain', sa.String(length=50), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('node_type', sa.String(length=50), server_default='wallet', nullable=False),
        sa.Column('address_type', sa.String(length=50), nullable=True),
        sa.Column('vasp_id', sa.String(length=255), nullable=True),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('is_terminal', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('inflow_usd', sa.Numeric(precision=20, scale=2), server_default=sa.text('0'), nullable=False),
        sa.Column('outflow_usd', sa.Numeric(precision=20, scale=2), server_default=sa.text('0'), nullable=False),
        sa.Column('first_seen_ts', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_seen_ts', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hop', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('provenance_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('investigation_id', 'node_key', name='uq_investigation_node_key')
    )
    op.create_index(op.f('ix_graph_nodes_investigation_id'), 'graph_nodes', ['investigation_id'], unique=False)

    # graph_edges table
    op.create_table(
        'graph_edges',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('source_key', sa.String(length=255), nullable=False),
        sa.Column('destination_key', sa.String(length=255), nullable=False),
        sa.Column('chain', sa.String(length=50), nullable=False),
        sa.Column('edge_type', sa.String(length=50), server_default='native_transfer', nullable=False),
        sa.Column('transaction_hash', sa.String(length=255), nullable=False),
        sa.Column('log_index', sa.Integer(), nullable=True),
        sa.Column('trace_id', sa.String(length=255), nullable=True),
        sa.Column('block_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('asset', sa.String(length=50), nullable=False),
        sa.Column('token_contract', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Numeric(precision=38, scale=18), nullable=False),
        sa.Column('amount_raw', sa.String(length=255), nullable=False),
        sa.Column('usd_value', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('traced_usd', sa.Numeric(precision=20, scale=2), server_default=sa.text('0'), nullable=False),
        sa.Column('hop', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='success', nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('evidence_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'investigation_id', 'chain', 'transaction_hash', 'log_index', 'trace_id',
            'source_key', 'destination_key', 'asset',
            name='uq_investigation_edge_dedup'
        )
    )
    op.create_index(op.f('ix_graph_edges_investigation_id'), 'graph_edges', ['investigation_id'], unique=False)
    op.create_index(op.f('ix_graph_edges_source_key'), 'graph_edges', ['source_key'], unique=False)
    op.create_index(op.f('ix_graph_edges_destination_key'), 'graph_edges', ['destination_key'], unique=False)
    op.create_index(op.f('ix_graph_edges_transaction_hash'), 'graph_edges', ['transaction_hash'], unique=False)


def downgrade() -> None:
    op.drop_table('graph_edges')
    op.drop_table('graph_nodes')
