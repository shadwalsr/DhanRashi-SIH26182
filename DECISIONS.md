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

---

## 5. Multi-Hop Graph Traversal & Explosion Controls (Phase 4)

### 5.1 Graph Relational Schema & Constraints (PRD §7.5)
- `graph_nodes`: Stores vertices with composite key `(investigation_id, node_key)` where `node_key = chain:address_lower`. Tracks classification (`node_type`, `address_type`), `vasp_id`, `is_terminal` flag, USD flow totals (`inflow_usd`, `outflow_usd`), and hop depth.
- `graph_edges`: Stores directed transfers with unique constraint on `(investigation_id, chain, transaction_hash, log_index, trace_id, source_key, destination_key, asset)` to prevent duplicate edges and double-counting during flow analysis (FR-DATA-07).
- Foreign key cascade on `investigation_id` ensures atomic cleanup on case/investigation deletion.

### 5.2 GraphEngine Protocol & Polyglot Database Abstraction (PRD §7.5, FR-GRAPH-06)
- Standardized `GraphEngine` async protocol in `app.graph.engine` defining `upsert_node`, `upsert_edge`, `get_node`, `get_neighbors`, `get_paths`, `get_subgraph`, and `get_stats`.
- `PostgresGraphEngine`: Production relational engine supporting bounded BFS pathfinding and SQL filtering across SQLite and PostgreSQL.
- `Neo4jGraphEngine`: Architecture stub raising `501 Not Implemented` for P2 graph database evaluation.

### 5.3 Best-First Graph Expansion & Explosion Controls (PRD §8.5, FR-GRAPH-01..05)
- **Best-First Frontier:** Priority queue prioritizes highest-USD transfers first (`-priority, hop, count, node`).
- **Terminal Node Stopping Rules:** Nodes classified as `VASP`, `BRIDGE`, `SERVICE` (e.g. mixers), or `CONTRACT` are marked terminal and are **never** expanded further.
- **Explosion Caps:**
  - `max_depth` (default 3, range 1-6)
  - `min_usd_value` (default $100)
  - `max_tx_per_node` (default 200)
  - `max_nodes_per_hop` (default 50)
  - `max_total_nodes` (1500)
  - `max_total_edges` (10000)
  - `high_degree_threshold` (1000 counterparties treated as service hub)
  - `provider_call_budget` (600 requests max)
- **Per-Hop Truncation Reporting:** Every pruned transfer/node records a `TruncationReport` detailing `hop`, `nodes_dropped`, `edges_dropped`, and `usd_dropped`. Any truncation marks the investigation as `PARTIAL` with reason `graph_truncated` (FR-GRAPH-05).

### 5.4 Chronologically Consistent Pro-Rata Flow Propagation (PRD §8.6, FR-GRAPH-04)
- **Haircut Model:** All edges are sorted chronologically. Transfers occurring before the first inflow to an intermediary carry strictly \$0 traced USD.
- **Pro-Rata Propagation:** Outflows are scaled by the running ratio of $\frac{\text{tainted\_balance}}{\text{running\_balance}}$.
- **Coverage Metrics:** Computes $\text{coverage} = \frac{\text{funds\_reached\_terminal}}{\text{total\_traced\_outflow}}$ and resolves per-VASP candidate fund shares for downstream attribution (Phase 5).

### 5.5 Investigation Lifecycle Orchestration (PRD §8.7, FR-INV-01..07)
- **State Machine Transitions:** `CREATED` → `VALIDATING` → `FETCHING_DATA` → `TRACING` → `ANALYZING` → `COMPLETED` / `PARTIAL` / `FAILED`.
- **Concurrent Execution Guard:** State machine enforces strict transitions; attempting to run an active investigation returns HTTP 409 conflict.
- **Snapshot Hashing (G5, FR-INV-07):** Computes canonical SHA-256 hash (`SNAP-...`) from chain, address, and transaction count for deterministic reruns.
- **User Cancellation:** `POST /{investigation_id}/cancel` transitions active runs to `FAILED` with audit trail.



---

## 6. Attribution Engine & Confidence Scoring (Phase 5)

### 6.1 Multi-Feature Scoring Model & Weights (PRD §10.3, FR-ATT-01..02)
- Implemented 10 explainable scoring features as pure functions in `app.attribution.features`:
  - `graph_distance` (weight 0.15): Non-linear penalty for hop distance ($1 \to 1.0, 2 \to 0.8, 3 \to 0.5, 4 \to 0.25, 5+ \to 0.1$).
  - `known_deposit_match` (weight 0.20): Strong positive signal when target directly matches a verified deposit address.
  - `cluster_association` (weight 0.15): Co-spend heuristics and multi-input clustering confidence.
  - `funds_reached` (weight 0.15): Logarithmic volume scoring up to \$100,000+.
  - `percentage_of_traced_funds` (weight 0.10): Pro-rata flow share captured by candidate. Core regression test confirms hop 3 capturing 88% outranks hop 2 capturing 5%.
  - `transaction_frequency` (weight 0.05): Recurrent counterparty interaction scoring.
  - `recency_of_interaction` (weight 0.05): Exponential time-decay over 365 days.
  - `continuity_of_flow` (weight 0.05): Time delta penalty between successive hops.
  - `intelligence_provider_confidence` (weight 0.05): Registry provider confidence score.
  - `cross_chain_evidence` (weight 0.05): Bridge and cross-chain tracking confidence.
- Default weights sum to exactly 1.000.
- Dynamic weight renormalization via `renormalize_weights()` when features are inapplicable (e.g. single-chain investigations omit cross-chain evidence). Ensures invariant G2: $\sum \text{contributions} == \text{raw\_score} \pm 0.001$.

### 6.2 Attribution Caps & Tier Assignment (PRD §10.3.3, FR-ATT-03..05)
- Evaluates 8 deterministic caps (CAP-01 through CAP-08) in descending order of severity:
  - **CAP-01 (Minimum Evidence Gate):** No direct hop 1/2 connection or cluster score < 0.2 caps score at 0.35 (`LOW`).
  - **CAP-02 (High-Degree Intermediary):** Path traversed intermediary with degree $\ge 1000$ without deposit match caps score at 0.40 (`LOW`).
  - **CAP-03 (Unresolved Flow):** $>50\%$ of path outflow absorbed by contract or unparsed transaction caps score at 0.50 (`MEDIUM`).
  - **CAP-04 (Conflicting / Disputed Labels):** VASP label contradicted or disputed caps score at 0.45 (`MEDIUM`).
  - **CAP-05 (Ambiguous Cross-Chain):** Bridge exit identified only by timing correlation caps score at 0.55 (`MEDIUM`).
  - **CAP-06 (Incomplete Data):** Partial pagination or rate limit hit on path caps score at 0.60 (`MEDIUM`).
  - **CAP-07 (Stale Label):** Attribution relies on label $>180$ days unconfirmed caps score at 0.65 (`MEDIUM`).
  - **CAP-08 (Low Flow Proportion):** $<5\%$ of total traced funds reached candidate caps score at 0.40 (`LOW`).
- Final confidence score is strictly bounded: $\text{final\_score} = \min(\text{raw\_score}, \min(\text{applied\_caps}))$.
- Qualitative confidence tiers:
  - `HIGH`: Score $\ge 0.70$
  - `MEDIUM`: $0.40 \le \text{Score} < 0.70$
  - `LOW`: Score $< 0.40$

### 6.3 Explainability Payload & Dispositions (PRD §10.4, FR-ATT-06..09)
- Structured `ExplainAttributionResponse` provides complete feature breakdown: raw values, normalized scores, dynamic weights, contributions, applied caps, and limitations.
- Competing candidates flag (`competing_candidates = true`, `margin_to_next`) triggers whenever top two candidates differ by score $< 0.10$.
- Human-in-the-loop investigator disposition (`accepted`, `rejected`, `under_review`, `unreviewed`) allows investigators to record review outcomes and subpoena notes.
- **Score Invariance (FR-ATT-09):** Investigator disposition updates strictly update review metadata without mutating mathematical score, tier, rank, or factors.

### 6.4 Independence of Attribution and Risk Engines (PRD §11.1, FR-RISK-03, AT-12)
- Attribution Engine (`app.attribution`) has zero import or functional dependencies on risk scoring or risk models, ensuring objective, bias-free entity attribution.


---

## 7. Risk and Evidence Engines (Phase 6)

### 7.1 Immutable Evidence Ledger & Hash Chain (PRD §8.1, §8.2, §13.1, FR-EVD-01..04)
- **Schema & Ledger (`evidence`):** Stores discrete factual assertions with monotonic `sequence_num` per investigation, strict epistemic labeling (`provenance_class` ∈ {`OBSERVED`, `THIRD-PARTY INTELLIGENCE`, `DERIVED`, `INFERENCE`}), `raw_hash` of payload, `derived_from[]` references, and cryptographic hash chaining (`prev_evidence_hash` → `evidence_hash`).
- **Genesis & Hash Chain (FR-EVD-02):** Sequence 1 uses genesis hash (`0` * 64). Subsequent records chain $H_{i} = \text{SHA256}(H_{i-1} : \text{inv\_id} : \text{seq} : \text{raw\_hash} : \text{created\_at\_utc})$.
- **Tamper Detection (`verify_chain`):** System walks the ledger verifying contiguous sequence numbers, pointer continuity, and canonical SHA-256 payload integrity.
- **FR-EVD-01 Invariant:** Every attribution candidate links to at least 1 verified evidence record in `evidence_references`.
- **FR-EVD-04 Edge-to-Evidence Links:** Graph edges store associated `evidence_ids` allowing investigators to query all raw transfers and proof records backing any graph hop.
- **Append-Only Analyst Notes:** Investigator notes are recorded as immutable evidence rows with `provenance_class = INFERENCE`.

### 7.2 Independent Risk Scoring Engine (PRD §12, FR-RISK-01..04)
- **P0 Signals (FR-RISK-01):**
  - `mixer_interaction` (30 points): Detects 1-2 hop interactions with mixer contracts/services (Tornado Cash, Blender, ChipMixer).
  - `peel_chain` (24 points): Identifies structured peeling behavior across asymmetric intermediate splitting nodes.
  - `rapid_movement` (18 points): Flags transfers occurring in $< 15$ minutes between consecutive hops.
  - `high_value_transfers` (10 points): Flags single transfers $\ge \$10,000$ or cumulative traced volume $\ge \$50,000$.
  - `high_risk_counterparty` (25 points): Direct or transitive association with flagged illicit entities (sanctioned, darknet, exploit).
- **Case 4 Acceptance Oracle (FR-RISK-02):**
  - Case 4 combines mixer interaction (30) + peel chain (24) + rapid movement (18) = exactly **72 / HIGH**.
  - Risk Tiers: `LOW` (0–29), `MEDIUM` (30–59), `HIGH` (60–84), `SEVERE` (85–100).
- **FR-RISK-03 / AT-12 Strict Independence:**
  - Attribution Engine (`app.attribution`) has zero import or operational dependency on `app.risk`.
  - Toggling or modifying risk data results in mathematically invariant attribution outputs.
- **FR-RISK-04 VASP Neutrality:**
  - Regulated VASP nodes are terminal destinations and never carry a risk score or illicit label. Risk assessment strictly evaluates the source wallet and transit laundering trail.

---

## 8. Cross-Chain Layer (Phase 7)

### 8.1 Bridge Registry & Pluggable Architecture (PRD §7.3, §14, FR-XCH-01, FR-XCH-05)
- **Pluggable Bridge Adapter Interface (`BridgeAdapter`):**
  - Standard protocol defining `bridge_id`, `bridge_name`, `supported_chains`, `supports_contract()`, `detect_bridge_interaction()`, and `match()`.
  - Concrete `DemoBridgeAdapter` handles cross-chain liquidity pool and lock-and-mint bridge protocols.
  - Extensibility verified via `StubBridgeAdapter` (FR-XCH-05): new cross-chain bridges register without altering the core pipeline or attribution engine.
- **Bridge Registry (`bridge_registry` table & `BridgeRegistry` class):**
  - Maintains source/destination contract addresses, deposit/payout event signatures, slippage/fee tolerances (default 2%), and time windows (default 120 min).
  - Synced to persistent database and accessible via REST API (`GET /api/v1/investigations/bridges/registry`).

### 8.2 Cross-Chain Detection & Source-to-Destination Matching (FR-XCH-02, FR-XCH-03)
- **Detection (`FR-XCH-02`):**
  - Flags graph edges interacting with registered bridge contracts and generates persistent `cross_chain_events` records.
- **Matcher Logic (`FR-XCH-03`):**
  - **Tier 1 (Exact ID Match):** Bridge-provided deposit/sequence ID matches destination transfer $\to$ `confidence = 0.98`, `is_ambiguous = False`.
  - **Tier 2 (Heuristic Match):** Transfer amount matches within 2% fee tolerance and destination timestamp falls within $[t_{\text{src}}, t_{\text{src}} + 120\text{ min}]$.
    - If unique: `confidence = 0.85`, `is_ambiguous = False`.
  - **Tier 3 (Ambiguity & PRD Failure Matrix Row 15):**
    - If multiple plausible destination transfers match amount and time criteria: records all candidates in `alternatives_json`, flags `is_ambiguous = True`, and caps confidence at $0.65$ ($< 0.80$).
    - This deterministic confidence threshold directly activates **CAP-05**, capping the downstream attribution score at $0.65$ (`MEDIUM` tier).

### 8.3 Destination Trace Continuation & Evidence Chaining (FR-XCH-04, FR-EVD-01)
- **Trace Continuation (FR-XCH-04):**
  - If match confidence $\ge 0.50$, destination graph edges are tagged with `via_cross_chain_event_id = str(event.id)`.
  - Graph visualization and export engines utilize `via_cross_chain_event_id` to render seamless cross-chain edge connections.
- **Cryptographic Evidence Record:**
  - Every detected match emits an immutable evidence record (`evidence_type = "cross_chain_match"`, `provenance_class = "DERIVED"`), linked into the investigation's hash chain.

### 8.4 Attribution Engine Integration & Case 5 Acceptance Oracle
- **Attribution Feature Wiring:**
  - Attribution Engine incorporates `cross_chain_evidence` factor when candidate paths traverse bridge hops.
  - Rebalances dynamic weights across active features, ensuring G2 invariant ($\sum \text{contributions} == \text{raw\_score} \pm 0.001$).
- **Case 5 Acceptance Oracle:**
  - Scenario: Ethereum seed wallet deposits $5,000 USDC into Demo Bridge $\to$ bridge pays out $4,990 USDC on Polygon to intermediary $\to$ intermediary deposits funds into Kraken.
  - Verified: Produces exactly **1** `CrossChainEvent` (`BRIDGE-DEMO-001`), tags downstream edge, and ranks Kraken as top candidate with active `cross_chain_evidence` factor.

---

## 9. Frontend Architecture & User Journeys (Phase 8)

### 9.1 Multi-Persona Role Switcher & Role-Aware Navigation (PRD §4.1, §4.2, Task 1)
- **Role-Aware Navigation & Quick Switcher (`AuthBar`):**
  - Instant persona switcher supporting all 6 PRD roles (`INV`, `FIA`, `SUP`, `AUD`, `ADM`, `RO`).
  - Pre-seeded credential profiles (`DEMO_USERS`) allow zero-friction testing of RBAC restrictions and supervisor reviews.
  - Scoped UI permissions disable or hide unauthorized tabs (e.g., registry curation restricted to `FIA`/`ADM`, report approvals restricted to `SUP`, audit ledger prioritized for `AUD`).

### 9.2 Interactive Graph Visualization with Cytoscape.js (PRD §5 J1, Task 6)
- **Visual Encoding:**
  - Distinct node colorings and shapes: Seed wallet (`#1d4ed8`), VASP terminal node (`#7c3aed` with halo), Bridge contract (`#0891b2` round rectangle), Mixer (`#e11d48` octagon), Cluster (`#0d9488` diamond), and transit Wallets (`#64748b`).
  - Cross-chain bridge edges rendered with dashed cyan lines and tagged with `via_cross_chain_event_id`.
  - Edge stroke thickness dynamically scaled to transfer USD amount.
- **Risk Signals Overlay Toggle:**
  - One-click toggle overlays high-risk red halos on nodes and edges flagged by the independent risk engine (mixer hops, peel chains, rapid hops).
- **Element Inspector & Filters (FR-EVD-04):**
  - Clicking any node or edge opens an inspector drawer displaying exact transaction hashes, block numbers, amounts, and direct links to associated evidence IDs.
  - Interactive toolbar supports filtering by blockchain, minimum USD value, hop depth, and layouts (`breadthfirst`, `concentric`, `cose`), with full-canvas PNG export.

### 9.3 Four-Card Overview & Epistemic Limitations (PRD §10.3, §10.4, Task 5)
- **Four Distinct Metric Cards:**
  1. **Top Candidate VASP:** Entity name, VASP ID, jurisdiction, score, and competing candidates warning badge.
  2. **Attribution Tier:** Multi-factor confidence tier (`HIGH`, `MEDIUM`, `LOW`, `INSUFFICIENT`).
  3. **Independent Risk Tier:** Numerical laundering score (0–100) and risk tier (`LOW`, `MEDIUM`, `HIGH`, `SEVERE`) evaluating the transit trail, strictly neutral towards regulated VASPs (FR-RISK-04).
  4. **Graph Coverage:** Depth traversed, node/edge counts, and execution status (`COMPLETED` vs `PARTIAL`).
- **Investigative Lead Disclaimer:**
  - Persistent amber warning emphasizing that attribution scores are mathematical correlations over public graph topologies and not legal proof of guilt. Scores under 0.40 are flagged as inadmissible for sole statutory disclosure.

### 9.4 "Explain Attribution" Drawer with G2 Proof (PRD §11, FR-ATT-07, Task 7)
- **Feature Decomposition Table:**
  - Detailed breakdown of all 10 features: raw values, normalized scores (0.00–1.00), dynamic weights, and individual feature contributions.
  - Mathematical G2 verification badge confirming $\sum \text{contributions} == \text{raw\_score} \pm 0.001$.
- **Attribution Caps (CAP-01..08):**
  - Highlights all active cap rules, maximum allowed score ceiling, and contextual reason.
  - Epistemic limitations list explaining payment processors and hot wallet caveats.
- **Human-in-the-Loop Disposition (FR-ATT-09):**
  - Allows investigators to record review decisions (`accepted`, `rejected`, `needs_review`) and subpoena justification notes. Stored immutably as `INFERENCE` in the evidence ledger without modifying the raw mathematical score.

### 9.5 Evidence Ledger & Hash Chain Verification (PRD §13, FR-EVD-01..04, Task 8)
- **Epistemic Provenance Badging:**
  - Every fact displays an explicit provenance badge: `OBSERVED` (green), `THIRD-PARTY INTELLIGENCE` (blue), `DERIVED` (purple), `INFERENCE` (amber).
- **Cryptographic Tamper Verification:**
  - "Verify Hash Chain" button executes verification over the hash-chained sequence ($H_i = \text{SHA256}(H_{i-1} \mathbin{\Vert} \text{payload})$).
- **Append-Only Analyst Notes:**
  - In-app modal allows investigators to append signed notes chained into the ledger.

### 9.6 End-to-End User Journeys (Journeys J1 through J6)
- **J1 (Investigator Primary Flow):** New investigation with instant client-side format checks $\to$ live progress stepper $\to$ Cytoscape graph exploration $\to$ explain attribution $\to$ disposition recording.
- **J2 (Analyst Label Conflict Resolution):** Dedicated tab for conflicting or stale VASP records with formal supersede/dispute workflow.
- **J3 (Supervisor Oversight & SAHYOG Pipeline):** Mandatory "MOCK" banner, separation of duties validation (report creator cannot approve own report), and mock SAHYOG request tracking (`SUBMITTED` $\to$ `ACKNOWLEDGED`).
- **J4 (Auditor Process Integrity):** Filterable audit log with one-click hash-chain integrity verification and CSV export.
- **J5 (Partial Graph Handling):** Live stepper and cards handle `PARTIAL` state with explicit truncation warnings and CAP-06 flagging.
- **J6 (System & Provider Telemetry):** Live status of blockchain providers, token bucket rate limits, and circuit breaker states.
