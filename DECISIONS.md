# VASP-Trace Architecture & Schema Decisions

**Document Version:** 1.0  
**Phase:** Phase 1 (Domain model, auth, RBAC, audit)  
**Context:** Implements decisions for schemas and interfaces not fully elaborated in the preliminary PRD sections.

---

## 1. Domain Enums

### 1.1 Blockchain (`Chain`)
- Supported MVP: `ethereum`, `bnb_chain`, `polygon`, `tron`
- Architecture stubs: `bitcoin`, `solana`

### 1.2 Address Classification (`AddressType`)
- `deposit`: Unique deposit addresses created for users
- `hot_wallet`: Operational hot wallet used for withdrawals/inflows
- `cold_wallet`: High-security cold storage
- `custodial`: Custodial omnibus account
- `payment_processor`: Merchant payment processing contract/wallet
- `eoa`: Standard Externally Owned Account
- `contract`: Unclassified smart contract
- `mixer`: Obfuscation service (terminal node)
- `bridge`: Cross-chain bridge contract (terminal node → CrossChainEvent)

### 1.3 Epistemic Provenance Classes (`ProvenanceClass`)
- `OBSERVED`: Raw blockchain transactions and token logs
- `THIRD_PARTY_INTELLIGENCE`: Commercial/open-source labels and off-chain data
- `DERIVED`: Computed metrics (hop counts, flow percentages, scores)
- `INFERENCE`: Human analyst notes, dispositions, manual tags

### 1.4 State Machine States (`InvestigationState`)
`CREATED` → `VALIDATING` → `FETCHING_DATA` → `TRACING` → `ANALYZING` → `COMPLETED` / `PARTIAL` / `FAILED`

---

## 2. Core Relational Schema

### 2.1 Organizations & Users
- `orgs`: Multi-tenant organization boundaries (`id`, `name`, `code`, `created_at`, `updated_at`).
- `roles`: System RBAC roles (`INV`, `FIA`, `SUP`, `AUD`, `ADM`, `RO`).
- `users`: User profiles with bcrypt-hashed passwords, role, organization reference, and MFA flags.

### 2.2 Case Management
- `cases`: Tracked case files with unique `(org_id, reference_number)` constraint. Return 409 on duplicate.
- `case_members`: Explicit ACL access list linking users to cases with `role_in_case` (`owner`, `collaborator`, `viewer`).
- `case_notes`: Append-only, version-tracked investigative notes. Editing creates a new incremented version.

### 2.3 Investigations
- `investigations`: Investigation jobs linked to a case, wallet address, target chain, and execution parameters (`depth`, `min_usd_value`, `run_no`, `data_snapshot_id`, `registry_snapshot_id`).
- Unauthorized case/investigation access returns `404 NOT FOUND` (not 403) to prevent existence leakage.

### 2.4 Audit Logs & Hash Chain
- `audit_logs`: Immutable security log capturing every action, outcome (`ALLOW` / `DENY`), request parameters, timestamp, and a SHA-256 cryptographic chain:
  $$\text{hash}_n = \text{SHA256}(\text{hash}_{n-1} + \text{user\_id} + \text{action} + \text{outcome} + \text{timestamp})$$
- `verify_audit_chain()` verifies that the entire chain has not been altered.

---

## 3. VASP Registry & Intelligence Layer (Phase 2)

### 3.1 Registry Tables & Constraints
- `vasps`: Master VASP directory storing canonical `vasp_id` (e.g. `VASP-SYN-001`), display name, jurisdiction (ISO 3166-1 alpha-2), and `is_synthetic` indicator.
- `vasp_addresses`: Address labels with temporal validity (`valid_from`, `valid_to`), versioning, confidence score (0.0-1.0), and unique constraint `uq_chain_address_vasp_validity` on `(chain, address, vasp_id_fk, valid_to)`.
- `vasp_clusters`: Heuristic and known wallet clusters linked to a master VASP.
- `registry_snapshots`: Immutable frozen snapshots recording `snapshot_id`, `record_count`, and `snapshot_hash` for deterministic reproduction of historical investigation runs (G5).

### 3.2 Address Normalization
- EVM chains (`ethereum`, `bnb_chain`, `polygon`): Lowercased string matching `^0x[0-9a-f]{40}$`.
- Tron (`tron`): Case-sensitive Base58Check string matching `^T[a-zA-Z0-9]{33}$`.

### 3.3 Intelligence Adapter Architecture
- `IntelligenceAdapter` Protocol: Async protocol defining `lookup_address(chain, address)`, `lookup_batch(chain, addresses)`, and `health()`.
- `LocalRegistryAdapter`: Native SQL implementation querying `vasp_addresses` and resolving cluster memberships.
- Commercial Adapters: `ChainalysisAdapter`, `EllipticAdapter`, `MerkleScienceAdapter`, `ArkhamAdapter` are registered as disabled stubs (`enabled=False`) raising `AdapterNotConfiguredException` (HTTP 503) unless explicitly configured by administrators. The full core test suite runs offline without commercial APIs.

### 3.4 Conflict Resolution & Override Policy (PRD §10.4)
- **Direct Label Conflict:** If multiple active records exist for `(chain, address)` with different `VASP_ID`s, both records are retained with `conflict=True` and returned together in lookup responses; conflicting labels are **never** silently merged.
- **Cluster vs Address Conflict:** Direct address-level records outrank cluster inference if and only if `evidence_type` is one of `law_enforcement_confirmed`, `public_proof_of_reserves`, or `self_attested`. Otherwise, cluster inference is retained and flags a conflict.

### 3.5 Staleness Degradation Factor (FR-REG-06)
- $\text{age} < 180\text{ days}$: Factor 1.0 (fresh match).
- $180 \le \text{age} \le 365\text{ days}$: Factor 0.7 (moderately stale).
- $\text{age} > 365\text{ days}$: Factor 0.4 (stale, triggers CAP-07 downstream limitation).

---

## 4. Blockchain Data Layer (Phase 3)

### 4.1 ChainProvider Protocol & Provider Abstraction
- Standardized `ChainProvider` async protocol in `app.chain.interface` unifying EVM and Tron networks.
- `FixtureChainProvider`: Loads recorded JSON fixtures from `data/demo/chain/*.json`. Accepts synthetic IDs (`SYN-TX-`) only when `DEMO_MODE=true` is set.
- `EvmProvider`: Shared base class parameterized by chain ID, explorer API, and JSON-RPC URL; subclasses `EthereumProvider`, `BnbProvider`, and `PolygonProvider`.
- `TronProvider`: Specialized TronGrid/TronScan provider handling TRC-20 token parsing and 19-block finality requirements.
- Architecture-Only Stubs: `BitcoinProvider` and `SolanaProvider` raise `ProviderUnsupportedChain` (FR-DATA-08, P2).

### 4.2 Address Checksum Verification (PRD §9.3)
- EVM: Strict regex validation `^0x[0-9a-fA-F]{40}$`, zero-address rejection (`0x000...000`), and pure-Python EIP-55 mixed-case checksum verification. All-lower or all-upper addresses are accepted and normalized to lowercase.
- Tron: Base58Check decoding with strict `0x41` version byte check, 25-byte length verification, and double-SHA256 checksum validation.

### 4.3 Resilience & Reliability Architecture (PRD §9.4)
- **Token Bucket Rate Limiting:** Per-(provider, key) rate limiting preventing 429 request storms.
- **Circuit Breaker:** Opens after 5 consecutive failures or $\ge 50\%$ failure rate in a 20-call sliding window; transitions to half-open after 30 seconds.
- **Exponential Backoff with Full Jitter:** Retries transient failures (timeouts, 429, 5xx) up to 3 times with full jitter and honors `Retry-After` headers.
- **Deduplication:** Deduplicates transfers using canonical key `(chain, tx_hash, log_index/trace_id, source, destination, asset)` per FR-DATA-07.

### 4.4 USD Pricing & Stablecoin Allowlist (PRD §9.7)
- Historical daily close pricing via `PriceProvider`.
- Stablecoin \$1.00 peg is applied only if the contract address is on the verified allowlist, tagged with provenance flag `DERIVED:peg_assumed`.
- Missing prices yield `usd_value = null`.

### 4.5 Secrets Protection & URL Sanitization (PRD §9.6)
- API keys are redacted from logs and exception messages.
- Stored credentials store a `secret_ref` and a 4-character SHA-256 fingerprint, never the plaintext key.
- Provider request URLs are sanitized by stripping API key and authentication query parameters before persistence.
