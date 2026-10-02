from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
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

