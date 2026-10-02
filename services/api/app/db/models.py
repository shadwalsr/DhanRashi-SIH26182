import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin

# SQLite & Postgres JSON compatibility
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class Org(Base, TimestampMixin):
    __tablename__ = "orgs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="org")
    cases: Mapped[list["Case"]] = relationship(back_populates="org")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # INV, FIA, SUP, AUD, ADM, RO
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id"), nullable=False)

    role: Mapped["Role"] = relationship(back_populates="users")
    org: Mapped["Org"] = relationship(back_populates="users")
    created_cases: Mapped[list["Case"]] = relationship(back_populates="owner")


class Case(Base, TimestampMixin):
    __tablename__ = "cases"
    __table_args__ = (
        UniqueConstraint("org_id", "reference_number", name="uq_org_reference_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reference_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id"), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    org: Mapped["Org"] = relationship(back_populates="cases")
    owner: Mapped["User"] = relationship(back_populates="created_cases")
    members: Mapped[list["CaseMember"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    notes: Mapped[list["CaseNote"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    investigations: Mapped[list["Investigation"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class CaseMember(Base):
    __tablename__ = "case_members"
    __table_args__ = (
        UniqueConstraint("case_id", "user_id", name="uq_case_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    role_in_case: Mapped[str] = mapped_column(String(50), default="member", nullable=False)  # owner, collaborator, viewer
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    case: Mapped["Case"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()


class CaseNote(Base):
    __tablename__ = "case_notes"
    __table_args__ = (
        UniqueConstraint("case_id", "version", name="uq_case_note_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    case: Mapped["Case"] = relationship(back_populates="notes")
    author: Mapped["User"] = relationship()


class Investigation(Base, TimestampMixin):
    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    blockchain: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="CREATED", nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    min_usd_value: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    run_no: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    registry_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    warnings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    partial_reasons: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)

    case: Mapped["Case"] = relationship(back_populates="investigations")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)  # ALLOW, DENY
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    user: Mapped[Optional["User"]] = relationship()


class Vasp(Base, TimestampMixin):
    __tablename__ = "vasps"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vasp_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(2), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    addresses: Mapped[list["VaspAddress"]] = relationship(back_populates="vasp", cascade="all, delete-orphan")
    clusters: Mapped[list["VaspCluster"]] = relationship(back_populates="vasp", cascade="all, delete-orphan")


class VaspAddress(Base, TimestampMixin):
    __tablename__ = "vasp_addresses"
    __table_args__ = (
        UniqueConstraint("chain", "address", "vasp_id_fk", "valid_to", name="uq_chain_address_vasp_validity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    record_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    vasp_id_fk: Mapped[uuid.UUID] = mapped_column(ForeignKey("vasps.id"), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    chain: Mapped[str] = mapped_column(String(50), nullable=False)
    address_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cluster_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    first_seen: Mapped[date] = mapped_column(Date, nullable=False)
    last_verified: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    conflict: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    vasp: Mapped["Vasp"] = relationship(back_populates="addresses")


class VaspCluster(Base, TimestampMixin):
    __tablename__ = "vasp_clusters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    vasp_id_fk: Mapped[uuid.UUID] = mapped_column(ForeignKey("vasps.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    vasp: Mapped["Vasp"] = relationship(back_populates="clusters")


class RegistrySnapshot(Base):
    __tablename__ = "registry_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    investigation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("investigations.id"), nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class GraphNodeModel(Base, TimestampMixin):
    __tablename__ = "graph_nodes"
    __table_args__ = (
        UniqueConstraint("investigation_id", "node_key", name="uq_investigation_node_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("investigations.id"), nullable=False, index=True)
    node_key: Mapped[str] = mapped_column(String(255), nullable=False)  # Format: chain:address
    chain: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    node_type: Mapped[str] = mapped_column(String(50), default="wallet", nullable=False)
    address_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vasp_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    inflow_usd: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal(0), nullable=False)
    outflow_usd: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal(0), nullable=False)
    first_seen_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hop: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provenance_json: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE, nullable=True)

    investigation: Mapped["Investigation"] = relationship()


class GraphEdgeModel(Base, TimestampMixin):
    __tablename__ = "graph_edges"
    __table_args__ = (
        UniqueConstraint(
            "investigation_id",
            "chain",
            "transaction_hash",
            "log_index",
            "trace_id",
            "source_key",
            "destination_key",
            "asset",
            name="uq_investigation_edge_dedup",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("investigations.id"), nullable=False, index=True)
    source_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    destination_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    chain: Mapped[str] = mapped_column(String(50), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(50), default="native_transfer", nullable=False)
    transaction_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    log_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    asset: Mapped[str] = mapped_column(String(50), nullable=False)
    token_contract: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    amount_raw: Mapped[str] = mapped_column(String(255), nullable=False)
    usd_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    traced_usd: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal(0), nullable=False)
    hop: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_ids: Mapped[list[str] | None] = mapped_column(JSON_TYPE, nullable=True)

    investigation: Mapped["Investigation"] = relationship()


class AttributionResultModel(Base, TimestampMixin):
    __tablename__ = "attribution_results"
    __table_args__ = (
        UniqueConstraint(
            "investigation_id",
            "candidate_vasp_id",
            "version",
            name="uq_investigation_candidate_version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("investigations.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    candidate_vasp_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    candidate_vasp_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False)  # HIGH, MEDIUM, LOW, INSUFFICIENT
    competing_candidates: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evidence_gate_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    disposition: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, accepted, rejected, needs_review
    disposition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    disposition_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disposition_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    weights_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)
    registry_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    factors_json: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    caps_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=False)
    limitations_json: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False)
    supporting_addresses: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False)
    evidence_references: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False)

    investigation: Mapped["Investigation"] = relationship()
    disposition_user: Mapped[Optional["User"]] = relationship()


class EvidenceModel(Base, TimestampMixin):
    __tablename__ = "evidence"
    __table_args__ = (
        UniqueConstraint("investigation_id", "sequence_num", name="uq_evidence_investigation_seq"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    provenance_class: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    data_payload: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    derived_from: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    prev_evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    investigation: Mapped["Investigation"] = relationship()
    created_by: Mapped[Optional["User"]] = relationship()


class RiskAssessmentModel(Base, TimestampMixin):
    __tablename__ = "risk_assessments"
    __table_args__ = (
        UniqueConstraint("investigation_id", "version", name="uq_risk_investigation_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    target_address: Mapped[str] = mapped_column(String(255), nullable=False)
    chain: Mapped[str] = mapped_column(String(50), nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 to 100
    tier: Mapped[str] = mapped_column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, SEVERE
    signals_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_references: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)

    investigation: Mapped["Investigation"] = relationship()

