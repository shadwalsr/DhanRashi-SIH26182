from enum import Enum


class Chain(str, Enum):
    ETHEREUM = "ethereum"
    BNB_CHAIN = "bnb_chain"
    POLYGON = "polygon"
    TRON = "tron"
    BITCOIN = "bitcoin"  # Architecture stub
    SOLANA = "solana"    # Architecture stub


class AddressType(str, Enum):
    DEPOSIT = "deposit"
    HOT_WALLET = "hot_wallet"
    COLD_WALLET = "cold_wallet"
    CUSTODIAL = "custodial"
    PAYMENT_PROCESSOR = "payment_processor"
    EOA = "eoa"
    CONTRACT = "contract"
    MIXER = "mixer"
    BRIDGE = "bridge"


class ProvenanceClass(str, Enum):
    OBSERVED = "OBSERVED"
    THIRD_PARTY_INTELLIGENCE = "THIRD-PARTY INTELLIGENCE"
    DERIVED = "DERIVED"
    INFERENCE = "INFERENCE"


class NodeType(str, Enum):
    WALLET = "wallet"
    CONTRACT = "contract"
    VASP = "vasp"
    CLUSTER = "cluster"
    BRIDGE = "bridge"
    SERVICE = "service"


class EdgeType(str, Enum):
    NATIVE_TRANSFER = "native_transfer"
    TOKEN_TRANSFER = "token_transfer"
    CONTRACT_INTERACTION = "contract_interaction"
    BRIDGE_EVENT = "bridge_event"
    SWAP = "swap"


class InvestigationState(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    FETCHING_DATA = "FETCHING_DATA"
    TRACING = "TRACING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class EvidenceType(str, Enum):
    DIRECT_TRANSFER = "direct_transfer"
    CLUSTER_MATCH = "cluster_match"
    DEPOSIT_ADDRESS_REUSE = "deposit_address_reuse"
    REGISTRY_ENTRY = "registry_entry"
    INTELLIGENCE_LABEL = "intelligence_label"
    CROSS_CHAIN_MATCH = "cross_chain_match"
    HEURISTIC = "heuristic"
    ANALYST_NOTE = "analyst_note"


class UserRole(str, Enum):
    INV = "INV"  # Investigator
    FIA = "FIA"  # Financial Intelligence Analyst
    SUP = "SUP"  # Supervisor
    AUD = "AUD"  # Auditor
    ADM = "ADM"  # Administrator
    RO = "RO"    # Read-only Officer


class AuditOutcome(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class RegistryAddressType(str, Enum):
    DEPOSIT_WALLET = "deposit_wallet"
    HOT_WALLET = "hot_wallet"
    COLD_WALLET = "cold_wallet"
    EXCHANGE_CLUSTER = "exchange_cluster"
    CUSTODIAL_WALLET = "custodial_wallet"
    BRIDGE = "bridge"
    MIXER = "mixer"
    PAYMENT_PROCESSOR = "payment_processor"
    OTHER_SERVICE = "other_service"


class RegistryEvidenceType(str, Enum):
    SELF_ATTESTED = "self_attested"
    PUBLIC_PROOF_OF_RESERVES = "public_proof_of_reserves"
    LAW_ENFORCEMENT_CONFIRMED = "law_enforcement_confirmed"
    VENDOR_LABEL = "vendor_label"
    HEURISTIC_CLUSTER = "heuristic_cluster"
    COMMUNITY_LABEL = "community_label"
    SYNTHETIC_DEMO = "synthetic_demo"


class RegistryStatus(str, Enum):
    ACTIVE = "active"
    STALE = "stale"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


class AttributionTier(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class AttributionDisposition(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"

