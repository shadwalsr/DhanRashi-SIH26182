from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import (
    AddressType,
    AuditOutcome,
    Chain,
    EdgeType,
    InvestigationState,
    NodeType,
    ProvenanceClass,
    UserRole,
)


class ProvenanceRecord(BaseModel):
    provenance_class: ProvenanceClass
    source: str
    source_ref: str
    retrieved_at: datetime
    raw_hash: str
    derived_from: list[str] = Field(default_factory=list)


class Transfer(BaseModel):
    chain: Chain
    transaction_hash: str
    log_index: int | None = None
    trace_id: str | None = None
    block_number: int
    timestamp: datetime
    source: str
    destination: str
    asset: str
    token_contract: str | None = None
    amount: Decimal
    amount_raw: str
    usd_value: Decimal | None = None
    transaction_type: Literal["native", "token", "contract_call", "bridge", "swap"] = "native"
    provider: str
    status: Literal["success", "failed"] = "success"


Direction = Literal["in", "out", "both"]
T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    truncated: bool = False
    provider_meta: dict[str, Any] = Field(default_factory=dict)


class AddressValidation(BaseModel):
    valid: bool
    normalized: str
    reason: str | None = None
    kind: Literal["eoa", "contract", "unknown"] = "unknown"


class TransactionDetail(BaseModel):
    chain: Chain
    tx_hash: str
    block_number: int
    timestamp: datetime
    status: Literal["success", "failed"]
    confirmations: int
    transfers: list[Transfer] = Field(default_factory=list)
    raw_logs: list[dict[str, Any]] = Field(default_factory=list)


class Balance(BaseModel):
    chain: Chain
    address: str
    asset: str
    amount: Decimal
    usd_value: Decimal | None = None


class NeighborSet(BaseModel):
    address: str
    chain: Chain
    direction: Direction
    counterparties: list[dict[str, Any]] = Field(default_factory=list)


class ProviderHealth(BaseModel):
    name: str
    status: Literal["healthy", "degraded", "down", "disabled"]
    latency_ms: float | None = None
    quota_remaining: int | None = None


class GraphNode(BaseModel):
    id: str  # Format: chain:address
    address: str
    chain: Chain
    node_type: NodeType
    address_type: AddressType | None = None
    vasp_id: str | None = None
    label: str | None = None
    is_terminal: bool = False
    inflow_usd: Decimal = Decimal(0)
    outflow_usd: Decimal = Decimal(0)
    first_seen_ts: datetime | None = None
    last_seen_ts: datetime | None = None
    hop: int = 0
    provenance: ProvenanceRecord | None = None


class GraphEdge(BaseModel):
    id: str
    investigation_id: UUID
    source: str
    destination: str
    chain: Chain
    edge_type: EdgeType
    transaction_hash: str
    log_index: int | None = None
    trace_id: str | None = None
    timestamp: datetime
    asset: str
    amount: Decimal
    usd_value: Decimal | None = None
    traced_usd: Decimal = Decimal(0)  # Taint amount carried
    hop: int
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: ProvenanceRecord | None = None


class TruncationReport(BaseModel):
    hop: int
    nodes_dropped: int = 0
    edges_dropped: int = 0
    usd_dropped: Decimal = Decimal(0)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str  # user_id
    email: str
    role: UserRole
    org_id: str
    exp: int


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str
    org_id: UUID
    is_active: bool
    created_at: datetime

    @field_validator("role", mode="before")
    @classmethod
    def extract_role(cls, v: Any) -> str:
        if hasattr(v, "name"):
            return str(v.name)
        return str(v)



class CaseBase(BaseModel):
    reference_number: str
    title: str
    description: str | None = None


class CaseCreate(CaseBase):
    pass


class CaseRead(CaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    owner_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class CaseNoteCreate(BaseModel):
    content: str


class CaseNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    author_id: UUID
    version: int
    content: str
    created_at: datetime


class InvestigationCreate(BaseModel):
    wallet_address: str
    blockchain: Chain
    depth: int = 3
    min_usd_value: float = 100.0


class InvestigationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    wallet_address: str
    blockchain: Chain
    status: InvestigationState
    depth: int
    min_usd_value: float
    run_no: int
    warnings: list[str] = Field(default_factory=list)
    partial_reasons: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    outcome: AuditOutcome
    details: dict[str, Any] | None = None
    timestamp: datetime
    prev_hash: str
    hash: str


class IntelLabel(BaseModel):
    chain: Chain
    address: str
    vasp_id: str | None = None
    vasp_name: str | None = None
    address_type: str  # RegistryAddressType value
    cluster_id: str | None = None
    confidence: float
    source: str
    source_reference: str
    evidence_type: str  # RegistryEvidenceType value
    last_verified: date | None = None
    provenance_class: str = "THIRD-PARTY INTELLIGENCE"
    conflict: bool = False
    staleness_factor: float = 1.0


class VaspRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    vasp_id: str
    name: str
    jurisdiction: str | None = None
    is_synthetic: bool
    created_at: datetime


class VaspAddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    record_id: str
    address: str
    chain: str
    address_type: str
    cluster_id: str | None = None
    source: str
    source_reference: str
    evidence_type: str
    confidence: float
    first_seen: date
    last_verified: date
    status: str
    conflict: bool
    staleness_factor: float = 1.0
    vasp_id: str  # The VASP display vasp_id, not FK UUID
    vasp_name: str  # VASP display name


class VaspAddressCreate(BaseModel):
    record_id: str
    address: str
    chain: Chain
    vasp_id: str  # refers to Vasp.vasp_id
    address_type: str
    cluster_id: str | None = None
    source: str
    source_reference: str
    evidence_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    first_seen: date
    last_verified: date
    status: str = "active"
    is_synthetic: bool = True


class RegistryLookupResponse(BaseModel):
    chain: str
    address: str
    labels: list[IntelLabel]
    has_conflict: bool = False
    cluster_labels: list[IntelLabel] = Field(default_factory=list)


class RegistryImportResult(BaseModel):
    total_rows: int
    imported: int
    errors: list[dict[str, Any]]
    file_hash: str


class RegistrySnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    snapshot_id: str
    record_count: int
    snapshot_hash: str
    created_at: datetime


class RegistryImportRequest(BaseModel):
    csv_content: str


class InvestigationStatusResponse(BaseModel):
    investigation_id: UUID
    status: str
    run_no: int
    data_snapshot_id: str | None = None
    registry_snapshot_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_reasons: list[str] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    investigation_id: UUID
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


class AttributionFactor(BaseModel):
    name: str
    raw_value: Any = None
    normalized_score: float
    weight: float
    contribution: float
    applicable: bool = True
    description: str | None = None


class AppliedCap(BaseModel):
    cap_code: str
    max_score: float
    reason: str


class CandidateAttribution(BaseModel):
    vasp_id: str
    vasp_name: str
    rank: int
    raw_score: float
    final_score: float
    tier: str
    competing: bool = False
    evidence_gate_passed: bool = True
    factors: list[AttributionFactor] = Field(default_factory=list)
    caps_applied: list[AppliedCap] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    supporting_addresses: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    disposition: str = "pending"
    disposition_notes: str | None = None


class AttributionResponse(BaseModel):
    investigation_id: UUID
    version: int = 1
    top_candidate: CandidateAttribution | None = None
    competing_candidates: bool = False
    margin: float | None = None
    candidates: list[CandidateAttribution] = Field(default_factory=list)
    evidence_gate_passed: bool = True
    weights_version: str = "v1.0.0"
    registry_snapshot_id: str | None = None
    calculated_at: datetime | None = None


class AttributionDispositionRequest(BaseModel):
    disposition: Literal["accepted", "rejected", "needs_review"]
    notes: str | None = None


class ExplainAttributionResponse(BaseModel):
    investigation_id: UUID
    candidate: CandidateAttribution
    formula_breakdown: str
    weights_version: str = "v1.0.0"
    reproducibility_hash: str | None = None


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investigation_id: UUID
    sequence_num: int
    evidence_type: str
    provenance_class: str
    source: str
    source_ref: str
    raw_hash: str
    data_payload: dict[str, Any]
    derived_from: list[str] = Field(default_factory=list)
    prev_evidence_hash: str
    evidence_hash: str
    created_by_id: UUID | None = None
    created_at: datetime


class EvidenceFilterParams(BaseModel):
    provenance_class: str | None = None
    evidence_type: str | None = None
    limit: int = 100
    offset: int = 0


class EvidenceChainVerificationResult(BaseModel):
    investigation_id: UUID
    is_valid: bool
    total_records: int
    latest_evidence_hash: str | None = None
    error_message: str | None = None
    verified_at: datetime


class AnalystNoteCreate(BaseModel):
    note: str
    derived_from: list[str] = Field(default_factory=list)
    source_ref: str | None = None


class RiskSignal(BaseModel):
    signal_code: str
    name: str
    score: int
    weight: float
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)


class RiskAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investigation_id: UUID
    version: int = 1
    target_address: str
    chain: str
    overall_score: int
    tier: str
    signals: list[RiskSignal] = Field(default_factory=list)
    summary: str
    evidence_references: list[str] = Field(default_factory=list)
    created_at: datetime


class RiskAssessmentRunResponse(BaseModel):
    investigation_id: UUID
    target_address: str
    chain: str
    overall_score: int
    tier: str
    signals: list[RiskSignal]
    summary: str
    evidence_references: list[str]
    calculated_at: datetime


class BridgeDefinition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bridge_id: str
    name: str
    source_chain: str
    destination_chain: str
    source_contract_address: str
    destination_contract_address: str
    event_abi_signature: str | None = None
    fee_percentage: float = 0.002
    max_time_window_seconds: int = 7200
    is_active: bool = True


class CrossChainEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investigation_id: UUID
    bridge_id: str
    source_chain: str
    source_tx_hash: str
    source_address: str
    destination_chain: str
    destination_tx_hash: str | None = None
    destination_address: str | None = None
    asset: str
    source_amount: Decimal
    destination_amount: Decimal | None = None
    source_timestamp: datetime
    destination_timestamp: datetime | None = None
    bridge_tx_id: str | None = None
    confidence: float
    is_ambiguous: bool = False
    alternatives_json: list[dict[str, Any]] = Field(default_factory=list)
    status: str
    evidence_id: UUID | None = None
    created_at: datetime


class CrossChainDetectionResponse(BaseModel):
    investigation_id: UUID
    events_detected: int
    events: list[CrossChainEventRead] = Field(default_factory=list)
    summary: str




