export type UserRole = "INV" | "FIA" | "SUP" | "AUD" | "ADM" | "RO";

export interface UserSession {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  orgId: string;
  token: string;
}

export type Blockchain = "ethereum" | "polygon" | "tron" | "bnb_chain" | "bitcoin" | "solana";

export type InvestigationState =
  | "CREATED"
  | "VALIDATING"
  | "FETCHING_DATA"
  | "TRACING"
  | "ANALYZING"
  | "COMPLETED"
  | "PARTIAL"
  | "FAILED"
  | "CANCELLED";

export type AttributionTier = "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT";
export type RiskTier = "LOW" | "MEDIUM" | "HIGH" | "SEVERE";
export type ProvenanceClass = "OBSERVED" | "THIRD-PARTY INTELLIGENCE" | "DERIVED" | "INFERENCE";

export interface Case {
  id: string;
  reference_number: string;
  title: string;
  description?: string;
  org_id: string;
  owner_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  investigations_count?: number;
  evidence_count?: number;
}

export interface Investigation {
  id: string;
  case_id: string;
  wallet_address: string;
  blockchain: Blockchain;
  start_time?: string;
  end_time?: string;
  depth: number;
  min_usd_threshold?: number;
  state: InvestigationState;
  state_detail?: string;
  created_at: string;
  completed_at?: string;
  node_count?: number;
  edge_count?: number;
  partial_reason?: string;
}

export interface GraphNode {
  node_key: string;
  chain: string;
  address: string;
  node_type: "seed" | "wallet" | "vasp" | "cluster" | "bridge" | "mixer" | "service";
  address_type?: string;
  vasp_id?: string;
  label?: string;
  is_terminal: boolean;
  hop: number;
  balance_usd?: number;
  is_high_risk?: boolean;
}

export interface GraphEdge {
  id: string;
  source_key: string;
  destination_key: string;
  chain: string;
  edge_type: string;
  transaction_hash: string;
  timestamp: string;
  asset: string;
  amount: number;
  usd_value?: number;
  traced_usd?: number;
  hop: number;
  via_cross_chain_event_id?: string;
  evidence_ids?: string[];
  is_high_risk?: boolean;
}

export interface GraphResponse {
  investigation_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  is_partial: boolean;
  partial_reason?: string;
  max_hop: number;
}

export interface AttributionFactor {
  name: string;
  raw_value: any;
  normalized_score: number;
  weight: number;
  contribution: number;
  applicable: boolean;
  description: string;
}

export interface AppliedCap {
  cap_code: string;
  max_score: number;
  reason: string;
}

export interface CandidateAttribution {
  vasp_id: string;
  vasp_name: string;
  rank: number;
  raw_score: number;
  final_score: number;
  tier: AttributionTier;
  competing: boolean;
  evidence_gate_passed: boolean;
  factors: AttributionFactor[];
  caps_applied: AppliedCap[];
  limitations: string[];
  supporting_addresses: string[];
  evidence_references: string[];
  disposition?: "pending" | "accepted" | "rejected" | "needs_review";
  disposition_notes?: string;
}

export interface AttributionResponse {
  investigation_id: string;
  version: number;
  top_candidate?: CandidateAttribution;
  competing_candidates: boolean;
  margin?: number;
  candidates: CandidateAttribution[];
  evidence_gate_passed: boolean;
  weights_version: string;
  registry_snapshot_id?: string;
  calculated_at: string;
}

export interface RiskSignal {
  signal_code: string;
  signal_name: string;
  points: number;
  triggered: boolean;
  description: string;
  details: Record<string, any>;
}

export interface RiskAssessment {
  investigation_id: string;
  risk_score: number;
  risk_tier: RiskTier;
  target_wallet: string;
  signals: RiskSignal[];
  evaluated_at: string;
  is_independent: boolean;
}

export interface Evidence {
  id: string;
  investigation_id: string;
  sequence_num: number;
  evidence_type: string;
  provenance_class: ProvenanceClass;
  source: string;
  source_ref?: string;
  raw_hash: string;
  evidence_hash: string;
  prev_evidence_hash?: string;
  data_payload: Record<string, any>;
  derived_from?: string[];
  created_at: string;
}

export interface VaspRecord {
  vasp_id: string;
  name: string;
  jurisdiction?: string;
  addresses_count?: number;
  status: string;
  is_synthetic: boolean;
}

export interface VaspAddressRecord {
  id: string;
  chain: string;
  address: string;
  vasp_id: string;
  vasp_name?: string;
  address_type: string;
  cluster_id?: string;
  confidence: number;
  status: "active" | "stale" | "disputed" | "superseded" | "retired";
  source: string;
  source_reference?: string;
  evidence_type: string;
  last_verified?: string;
}

export interface CrossChainEvent {
  id: string;
  investigation_id: string;
  bridge_id: string;
  source_chain: string;
  source_tx_hash: string;
  source_address: string;
  source_amount: number;
  destination_chain: string;
  destination_tx_hash?: string;
  destination_address?: string;
  destination_amount?: number;
  confidence: number;
  status: string;
  is_ambiguous: boolean;
  alternatives?: any[];
  detected_at: string;
}

export interface AuditLog {
  id: string;
  sequence_num: number;
  timestamp: string;
  actor_id?: string;
  actor_email?: string;
  actor_role?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  outcome: "ALLOW" | "DENY" | "ERROR";
  reason?: string;
  prev_hash?: string;
  entry_hash: string;
  details?: Record<string, any>;
}

export interface Report {
  id: string;
  case_id: string;
  investigation_id: string;
  title: string;
  pdf_hash?: string;
  status: "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "REJECTED";
  created_by: string;
  created_by_email?: string;
  approved_by?: string;
  approved_by_email?: string;
  approval_comment?: string;
  created_at: string;
  approved_at?: string;
}

export interface SahyogRequest {
  id: string;
  case_id: string;
  investigation_id: string;
  report_id: string;
  reference_number: string;
  target_vasp_id: string;
  target_vasp_name: string;
  status: "DRAFT" | "SUBMITTED" | "ACKNOWLEDGED" | "COMPLETED" | "REJECTED";
  is_mock: boolean;
  created_by: string;
  created_at: string;
  submitted_at?: string;
}
