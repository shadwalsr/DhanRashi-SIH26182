"""add graph performance indexes

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-10-04 10:30:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_graph_edges_investigation_id", "graph_edges", ["investigation_id"], unique=False)
    op.create_index("ix_graph_edges_source_key", "graph_edges", ["source_key"], unique=False)
    op.create_index("ix_graph_edges_destination_key", "graph_edges", ["destination_key"], unique=False)
    op.create_index("ix_graph_nodes_investigation_id", "graph_nodes", ["investigation_id"], unique=False)
    op.create_index("ix_graph_nodes_node_key", "graph_nodes", ["node_key"], unique=False)
    op.create_index("ix_evidence_investigation_id", "evidence", ["investigation_id"], unique=False)
    op.create_index("ix_investigations_wallet_address", "investigations", ["wallet_address"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_investigations_wallet_address", table_name="investigations")
    op.drop_index("ix_evidence_investigation_id", table_name="evidence")
    op.drop_index("ix_graph_nodes_node_key", table_name="graph_nodes")
    op.drop_index("ix_graph_nodes_investigation_id", table_name="graph_nodes")
    op.drop_index("ix_graph_edges_destination_key", table_name="graph_edges")
    op.drop_index("ix_graph_edges_source_key", table_name="graph_edges")
    op.drop_index("ix_graph_edges_investigation_id", table_name="graph_edges")
