# VASP-Trace: Phase-by-Phase Implementation Plan

**Source:** SIH26182 PRD v1.0 (Automated Attribution of Unknown Cryptocurrency Wallets to Nearest VASPs)
**Target:** Deterministic 5-case demo (under 5 minutes end to end) plus a live-mode path on Ethereum, BNB Chain, Polygon, Tron

---

## 0. Read this first

### 0.1 Gap in the PRD you uploaded
The uploaded file stops at section 10.5. Sections 11 to 26 are listed in the table of contents but are not present. These are the ones the plan depends on most:

| Missing section | What it holds | Impact on this plan |
|---|---|---|
| 11 Attribution Engine | The 10 factor formulas, weights, normalization, tiers, caps CAP-01 to CAP-08 | Phase 5 cannot start without it. Only CAP-04, CAP-05, CAP-06, CAP-07 and the 0.40 and 0.15 thresholds can be inferred from other sections |
| 12 Risk Engine | Signal list, weights, tier cut-offs | Phase 6. Only one data point exists: Case 4 must score 72 / HIGH |
| 13 Evidence Engine | Evidence schema 13.1 | Phase 6 |
| 14 to 15 | Cross-chain matching rules, SAHYOG field list and 7 operations | Phases 7 and 9 |
| 16 to 18 | API spec, UI screens (13 screens), DB schema | Phases 1, 4, 8 |
| 21 to 22 | Demo dataset and demo flow (5 cases, expected outputs) | Phase 10, and it is the acceptance oracle for Phase 5 |

**Action before Phase 5:** get the complete PRD, or write the missing specs yourselves as a short "Decisions" doc and freeze it. The plan below is written so that Phases 0 to 4 and Phase 8 (frontend shell) are unblocked either way.

### 0.2 Assumptions (change if wrong)
- Timeline is expressed in **working weeks** for a team of **4 to 5 people**. A compressed 6-week variant is in section 12.
- Demo mode comes first. Live public-chain mode is built after the demo path is green.
- Commercial intelligence adapters (Chainalysis, Elliptic, Merkle, Arkham) stay as stubs. SAHYOG stays mocked.

### 0.3 Suggested roles
| Role | Owns |
|---|---|
| R1 Backend lead | API, auth, orchestrator, DB, audit |
| R2 Data and chain engineer | Chain providers, resilience, caching, fixtures |
| R3 Analytics engineer | Graph, flow propagation, attribution, risk, evidence |
| R4 Frontend engineer | Next.js app, graph UI, comparison and explain screens |
| R5 (or shared) | Reports, SAHYOG mock, demo dataset, QA, docs |

---

## 1. Phase overview

| Phase | Name | Weeks | Core PRD refs | Exit gate |
|---|---|---|---|---|
| 0 | Foundation and tooling | 1 | 7.1, 7.6, 7.7, FR-OPS-01 | `docker compose up` shows web, api, worker healthy |
| 1 | Domain model, auth, RBAC, audit | 1 to 2 | 4, 6.1, FR-SEC-01 | Role x endpoint matrix passes; audit chain verifies |
| 2 | VASP registry and intelligence layer | 2 to 3 | 6.5, 10 | Registry import + conflict + staleness tests pass |
| 3 | Blockchain data layer | 2 to 4 | 6.3, 9 | Contract tests green for fixture + EVM + Tron providers |
| 4 | Graph engine, expansion, flow, orchestrator | 4 to 6 | 6.2, 6.4, 7.3 to 7.5, 8.5, 8.6 | Seed to graph with caps, state machine, snapshot |
| 5 | Attribution engine | 6 to 7 | 6.6, 11 | All 5 demo cases return expected top candidate and tier |
| 6 | Risk and evidence engines | 7 to 8 | 6.7, 6.8, 12, 13 | Case 4 risk = 72 / HIGH; AT-12 independence test |
| 7 | Cross-chain layer | 8 to 9 | 6.9, 14 | Case 5 yields one CrossChainEvent |
| 8 | Frontend | 4 to 9 (parallel) | 17 | All screens render from real API |
| 9 | Reports, SAHYOG mock, LLM (optional) | 9 to 10 | 6.10, 6.11, 15, 20 | PDF contains every section; mock lifecycle works |
| 10 | Demo dataset, testing, hardening, rehearsal | 10 to 11 | 21 to 23, G1 to G8 | Dry run under 5 min, 3 times in a row |

**Critical path:** 0 → 1 → 3 (fixture provider) → 4 → 5 → 6 → 9 → 10. Phases 2, 7 and 8 run alongside it.

---

## Phase 0: Foundation and tooling (Week 1)

**Goal:** Everyone can run the stack locally and merge code safely.

**Tasks**
1. Create monorepo per 7.6: `apps/web`, `services/api`, `data/demo`, `docker-compose.yml`, `Makefile`.
2. FastAPI skeleton (`app/main.py`, routers folder, `core/config.py`) with Pydantic v2 settings loaded from `.env`; `.env.example` committed, `.env` ignored.
3. Postgres 15 and Redis containers; SQLAlchemy 2 base and Alembic initialised with a first empty migration.
4. Celery app with the four queues (`fetch`, `trace`, `analyze`, `report`) and a `beat` service; one no-op task proving the round trip.
5. Next.js (App Router, TypeScript, Tailwind) hello page that calls `/health/live`.
6. Compose services per 7.7: `web:3000`, `api:8000`, `worker`, `beat`, `postgres`, `redis`, optional `keycloak`.
7. `DEMO_MODE` and `LIVE` mode flag in config (7.7); persistent "SYNTHETIC DATA" ribbon stub in the web layout.
8. CI: lint (ruff, eslint), type check (mypy, tsc), pytest, one smoke job that builds the compose stack.
9. Secret hygiene from day one: log redaction middleware placeholder (9.6), pre-commit hook blocking `.env`.
10. `make` targets: `up`, `down`, `migrate`, `seed-demo` (stub), `test`, `import-registry`.

**Deliverables:** running stack, CI green, README with setup steps.
**Exit criteria:** fresh clone to running app in under 10 minutes using only README steps.
**Risks:** Keycloak adds setup weight. Mitigation: start with a local JWT issuer, keep Keycloak optional.

---

## Phase 1: Domain model, auth, RBAC, audit (Weeks 1 to 2)

**Goal:** Secure skeleton that every later feature plugs into.

**Tasks**
1. Domain enums and Pydantic models: `Chain`, `AddressType`, `EvidenceType`, provenance classes (`OBSERVED`, `THIRD-PARTY INTELLIGENCE`, `DERIVED`, `INFERENCE`), node and edge types, state machine states.
2. Core tables (Alembic): `users`, `roles`, `orgs`, `cases`, `case_members`, `case_notes` (versioned), `investigations`, `audit_logs`. Schema 18 is missing, so define columns from 6.1 and 7.4 and record them in the Decisions doc.
3. Auth (FR-AUTH-01): local IdP or Keycloak, JWT with `sub`, `roles`, `org_id`; refresh rotation and revocation.
4. RBAC (FR-AUTH-02): permission map from the 4.2 matrix as data, a `require(permission, scope)` dependency used on every route.
5. Case-level authorization (rule 1): role AND assignment/ACL/supervisor. Unauthorized case access returns 404, not 403 (FR-CASE-03).
6. Separation of duties hooks (rule 2) as reusable guards, used later by report approval and SAHYOG submit.
7. Case CRUD (FR-CASE-01 to 04): unique `reference_number` per org (409 on duplicate), creator becomes `owner`, list filters, pagination capped at 100, append-only notes with history.
8. Audit writer (FR-SEC-01): every state change and every data view; hash chain (`prev_hash`, `hash`); DB trigger blocking UPDATE and DELETE; `verify_audit_chain` function; allow and deny outcomes both logged (rule 5).
9. Input validation, rate limiting middleware, error envelope with stable error codes (`INVALID_ADDRESS`, `UNSUPPORTED_CHAIN`, and so on).
10. Seed script creating one user per role.

**Deliverables:** auth working in Swagger, role x endpoint test matrix, audit verification command.
**Exit criteria:** every endpoint has a documented allow/deny row and a test; tampering with one audit row makes verification fail.
**Risks:** RBAC retrofitted later is painful. Mitigation: no route merges without a `require()` call, enforced by a test that walks the router table.

---

## Phase 2: VASP registry and intelligence layer (Weeks 2 to 3, parallel with Phase 3)

**Goal:** Labeling works end to end against synthetic data.

**Tasks**
1. Tables `vasp_addresses`, `vasp_clusters`, `registry_snapshots` per 10.2, including `record_id`, `version`, `valid_from`, `valid_to`, `is_synthetic`. Constraints: enum checks, no duplicate active `(chain, address, vasp_id)` (FR-REG-01).
2. Address normalization per chain (lowercase EVM keys, Tron Base58).
3. `IntelligenceAdapter` protocol and `IntelLabel` model (10.1); `LocalRegistryAdapter` implemented; four commercial adapters as disabled stubs that raise a clear "not configured" error. Rule: with all commercial adapters off, the full P0 suite passes.
4. Lookup API returning **all** active records including conflicts, never silently merged (FR-REG-03).
5. Cluster resolution (FR-REG-04): an address in a cluster inherits the cluster VASP with `cluster_match` evidence.
6. Conflict detection (10.4): same `(chain, address)` with different `VASP_ID` sets `conflict=true`; address-level override only for `law_enforcement_confirmed`, `public_proof_of_reserves`, `self_attested`.
7. Staleness (FR-REG-06): under 180 d = 1.0; 180 to 365 d = 0.7; over 365 d = 0.4 and triggers CAP-07; `disputed` triggers CAP-04.
8. Registry snapshot freeze: each investigation stores a `registry_snapshot_id` so reruns reproduce (G5).
9. Import (FR-REG-02): `make import-registry FILE=...` with schema validation, row-level error report, transactional commit, audit event with file hash.
10. Synthetic registry file with at least: 8 VASPs, all address types, one conflict pair, one stale record, one disputed record, one bridge, one mixer, one payment processor.

**Deliverables:** `data/demo/registry/*.csv`, import CLI, adapter tests.
**Exit criteria:** import of a deliberately broken file reports each bad row and commits nothing; conflict and staleness fixtures behave per 10.4.
**Risks:** Weak synthetic data makes Phase 5 look better than it is. Mitigation: deliberately include tricky registry rows (tiny-flow exchange, stale label, community label).

---

## Phase 3: Blockchain data layer (Weeks 2 to 4)

**Goal:** One `ChainProvider` interface, deterministic in demo mode, resilient in live mode.

**Order matters:** build the fixture provider first. It unblocks Phases 4 and 5 and makes the demo offline-safe.

**Tasks**
1. `ChainProvider` protocol and exception hierarchy exactly as 9.2 (`InvalidAddress`, `RateLimited`, `ProviderTimeout`, and others). `Page[T]` with `truncated` flag.
2. Canonical `Transfer` model (8.3): `Decimal` amounts, `amount_raw` as string, UTC timestamps, failed txs stored but excluded from flow.
3. Address validation (FR-DATA-02): EVM regex plus EIP-55 for mixed case, zero address rejected, Tron Base58Check with `0x41` version byte. Test vectors from 9.3.
4. `FixtureChainProvider` reading `data/demo/chain/*.json`; accepts `SYN-TX-` ids only when `DEMO_MODE=true`.
5. `EvmProvider` base class parameterised by chain id, explorer base URL and RPC URL; subclasses for Ethereum, BNB, Polygon (9.1 notes this is one engineering effort).
6. `TronProvider` (TronGrid / TronScan): TRC-20 handling, 19-confirmation finality.
7. Resilience (FR-DATA-04, 9.4): Redis token bucket per `(provider, api_key_id)`, retries with full jitter and `Retry-After`, timeouts (3 s connect, 15 s read, 20 s total), circuit breaker (5 consecutive or 50% of 20), ordered fallback with `provider` recorded on every record, page cap 20, finality filter.
8. Caching (9.5): key formats and TTLs from the table; finalized ranges 24 h, open ranges 60 s.
9. Dedup (FR-DATA-07): unique key `(chain, tx_hash, log_index/trace_id, from, to, asset)`; duplicates counted in diagnostics.
10. `PriceProvider` (9.7): historical daily close, stablecoin peg only for allowlisted contracts and flagged `DERIVED:peg_assumed`; missing price gives `usd_value=null` (failure row 16).
11. Secrets (9.6): `secret_ref` plus fingerprint in DB, header-based keys, URL sanitising before evidence storage, unit test that logs contain no key material.
12. Bitcoin and Solana stubs raising `UnsupportedChain`, listed as `architecture_only` (FR-DATA-08, P2).

**Deliverables:** provider contract test suite run against recorded fixtures for every provider.
**Exit criteria:** simulated 429 storm retries within limits and opens the breaker; malformed payload above 5% of a page fails the call; no provider failure ever produces invented edges (FR-DATA-06).
**Risks:** Explorer quotas and endpoint details are marked UNVERIFIED-EXTERNAL. Mitigation: record real responses once into fixtures, develop against those, and confirm quotas from official docs before live mode.

---

## Phase 4: Graph engine, expansion, flow, orchestrator (Weeks 4 to 6)

**Goal:** From a seed wallet to a persisted, bounded, chronologically consistent graph.

**Tasks**
1. Tables `graph_nodes`, `graph_edges` with enum constraints (FR-GRAPH-01) and the unique key from 8.5 (`COALESCE(log_index,-1)`, `COALESCE(trace_id,'')`).
2. `GraphEngine` protocol and `PostgresGraphEngine` (7.5): `upsert_*`, `neighbors`, `paths` via depth-bounded recursive CTE, `subgraph`, `stats`. Neo4j placeholder file only. Lint rule: attribution, risk and API import only the interface (FR-GRAPH-06).
3. Expansion (8.5 pseudocode): best-first by traced USD, `visited` map with min hop, edges always stored even to visited nodes, cycle handling by non-re-expansion.
4. Explosion controls (FR-GRAPH-03) with the default and max table: depth 3/5, min USD 100, 200 tx per node, 50 nodes per hop, 1,500 and 10,000 global caps, high-degree threshold 1,000, call budget 600. Truncation report per hop `{nodes_dropped, edges_dropped, usd_dropped}`.
5. Terminal rules (FR-GRAPH-04): VASP, mixer, bridge, contract, high-degree service never expand past.
6. Node labeling during expansion using the Phase 2 adapter with a per-run cache.
7. Flow propagation (8.6): pro-rata haircut with chronological processing; `traced_usd` per edge; outputs `funds_reached`, `fund_percentage`, `coverage`, `unresolved_percentage`. Seed's prior inflows are not tainted. Edge earlier than any inflow carries zero (FR-GRAPH-05).
8. Orchestrator and state machine (FR-INV-01 to 04): `CREATED → VALIDATING → FETCHING_DATA → TRACING → ANALYZING → COMPLETED/PARTIAL/FAILED`, illegal transitions rejected, each transition audited, run idempotent per `(investigation_id, run_no)`, second run returns 409, job id returned in 500 ms or less.
9. Progress endpoint (FR-INV-04) with monotonic counters and 2 s update latency.
10. Snapshot (FR-INV-07): hash every provider response, create `data_snapshot_id`; re-analysis on the same snapshot must reproduce identical output.
11. Failure matrix rows 1 to 17 (7.8) implemented as tests, each writing a `warnings[]` entry.
12. Graph retrieval API with filters (FR-GRAPH-07). P1: cancel, resume failed segments, JSON/GraphML export.

**Deliverables:** `POST /investigations`, `/run`, `/status`, `/graph`; branching test graph; 100k-edge stress fixture.
**Exit criteria:** stress fixture stops at caps and returns `PARTIAL` with a truncation report; hop counts correct on a branching graph; chronological test passes; second run on the same snapshot is byte-identical.
**Risks:** Flow propagation is the subtlest code in the project. Mitigation: hand-compute three tiny graphs on paper and use them as unit tests before writing the algorithm.

---

## Phase 5: Attribution engine (Weeks 6 to 7)

**Blocked on PRD section 11.** If unavailable, freeze your own spec first (see 0.1).

**Goal:** Rank candidate VASPs by explainable weighted score, never by shortest path.

**Tasks**
1. Candidate discovery (FR-ATT-01): traced nodes or clusters with VASP-class labels. Mixers and bridges never appear.
2. Ten features (FR-ATT-02): graph distance, known/deposit address match, cluster association, funds reached, percentage of traced funds, transaction frequency, recency, temporal continuity, intelligence-provider confidence, cross-chain evidence. Each has a pure function and boundary-value tests.
3. Weighted score (FR-ATT-03): weights from a versioned config file; renormalise over applicable features; contributions sum to the score within 0.001 (G2).
4. Tiers and caps (FR-ATT-04): CAP-01 to CAP-08 as separate small functions, each with a test, applied caps listed in the output. Known caps from the PRD: CAP-04 conflicting or disputed labels, CAP-05 ambiguous cross-chain, CAP-06 incomplete data, CAP-07 stale label over 365 d.
5. Evidence gate (FR-ATT-05): no qualifying evidence means `INSUFFICIENT EVIDENCE` with a reason; scores under 0.40 flagged "do not use for disclosure request".
6. Competing candidates (FR-ATT-06): flag when top-2 margin is under 0.15.
7. Explain payload (FR-ATT-07): factors, raw values, weights, contributions, caps, evidence refs, limitations; the client does no extra computation.
8. Versioning (FR-ATT-08): `version`, `weights_version`, `registry_snapshot`; rerun creates a new row.
9. Disposition (FR-ATT-09): accept, reject, needs-review stored as `INFERENCE`, never changes the score.
10. **Regression test for the core principle:** a VASP at hop 2 with 5% of funds must rank below a VASP at hop 3 with 88%.
11. Payment-processor limitation text and deposit vs hot wallet handling per the 10.3 table.

**Deliverables:** `/attribution` endpoint, golden JSON for each demo case.
**Exit criteria:** G1 and G2 met on all five cases; AT-12 stub in place for Phase 6.
**Risks:** Weight tuning to fit the demo can look like overfitting. Mitigation: freeze weights before building the demo cases, change them only through a new `weights_version`.

---

## Phase 6: Risk and evidence engines (Weeks 7 to 8)

**Goal:** Independent risk score, plus an immutable evidence ledger behind every result.

**Tasks (risk, section 12 missing)**
1. P0 signals (FR-RISK-01): mixer interaction, rapid movement, peel chain, high-value transfers, high-risk counterparty from the local list. Each with fixture-based detection tests.
2. Score and tier (FR-RISK-02): Case 4 must produce 72 / HIGH. P1: sanctions, ransomware, darknet via adapters.
3. Independence (FR-RISK-03): no import from `risk/` into `attribution/`; test AT-12 flips risk data and asserts identical attribution output.
4. VASP nodes never carry a risk score (FR-RISK-04); UI wording test later.

**Tasks (evidence, section 13 missing)**
5. `evidence` table per 13.1: type, provenance class, source, `source_ref`, `raw_hash`, `derived_from[]`, hash chain link.
6. Immutability (FR-EVD-02): DB trigger blocks UPDATE and DELETE; analyst notes append-only; verification function.
7. Every attribution result links at least one evidence row (FR-EVD-01), enforced by FK plus an application invariant test.
8. Edge-to-evidence links so clicking an edge lists its evidence (FR-EVD-04).
9. Evidence list API with filters by provenance class (FR-EVD-03).

**Exit criteria:** invariants hold: no attribution without evidence, no unlabeled fact, no mutation possible through SQL.

---

## Phase 7: Cross-chain layer (Weeks 8 to 9, parallel)

**Goal:** Detect and match bridge hops for the demo bridge, with an extension point for others.

**Tasks**
1. Bridge registry (FR-XCH-01): contract addresses, event ABI, supported chain pairs; one demo bridge.
2. Detector (FR-XCH-02): flag traced edges touching registered bridges, create `CrossChainEvent`.
3. Matcher (FR-XCH-03): source to destination matching by amount within fee, time window and bridge-provided id, confidence score; ambiguous matches store all `alternatives` and confidence under 0.80 applies CAP-05.
4. Continue trace on destination chain when confidence is at least 0.50 (FR-XCH-04, P1); edges tagged `via_cross_chain_event_id`.
5. Stub bridge adapter proving that adding a bridge needs no engine change (FR-XCH-05).
6. Wire `cross_chain_evidence` into the attribution factor set.

**Exit criteria:** Case 5 produces exactly one `CrossChainEvent` and the downstream VASP gets the cross-chain factor.

---

## Phase 8: Frontend (Weeks 4 to 9, parallel from Phase 4)

**Goal:** Investigator-grade UI, built against real API responses as they appear. Screen list (17) is missing, so the list below follows the journeys in section 5.

**Tasks**
1. Auth, session handling, role-aware navigation, dashboard with assigned cases and pending approvals.
2. Case list and detail (wallets, investigations, notes, evidence count, reports).
3. New Investigation form with instant validation and depth warnings.
4. Live progress view (polling or SSE) showing stage, counts, warnings.
5. Overview: top candidate, attribution tier and risk tier as **separate cards**, coverage %, warnings.
6. Graph view (Cytoscape.js): node types, VASP highlighting, risk overlay toggle, edge click showing evidence, filters by chain, date, asset, min value, depth.
7. Candidate comparison and "Explain Attribution" screen rendering the explain payload only.
8. Evidence ledger with provenance filters and label badges beside every fact.
9. Registry screens (P1: CRUD with history), conflict resolution flow (J2).
10. Report and SAHYOG screens with the "MOCK, not transmitted to any authority" banner.
11. Audit viewer with hash-chain verify button (J4); admin provider health (J6).
12. Persistent SYNTHETIC DATA ribbon in demo mode; PARTIAL state shows incomplete sub-trees.
13. UX rules: epistemic label on every datum; wording tests so no VASP is called illicit.

**Exit criteria:** journeys J1, J2, J3 and J5 clickable end to end without console errors.
**Risks:** Graph rendering at 1,500 nodes. Mitigation: default to a filtered subgraph, load more on demand.

---

## Phase 9: Reports, SAHYOG mock, LLM (Weeks 9 to 10)

**Tasks**
1. PDF generator (FR-RPT-01): all sections from the missing 17 screen-13 list; sha256 stored on the `reports` row.
2. Labels and limitations (FR-RPT-02/03): every fact row labelled, mandatory limitations and disclaimer that cannot be disabled; automated check for unlabeled rows.
3. Approval workflow (FR-RPT-04): different user must approve; same-user approval rejected.
4. `SahyogProvider` interface and `MockSahyogProvider` implementing all 7 operations (FR-SAH-01); request builder with completeness validation, missing fields keep status `DRAFT` with an error list (FR-SAH-02).
5. Time-based mock status transitions `SUBMITTED → ACKNOWLEDGED`, history persisted (FR-SAH-04); submit requires an approved report and a different user.
6. Deterministic template narrative (FR-AI-02): report must generate fully with the LLM off.
7. Optional LLM layer (P1): grounded only on structured JSON; output validator rejects any address, hash or VASP name not in the input (test LLM-03); LLM text visibly marked as narrative, never as data.

**Exit criteria:** end-to-end report generated, approved by a second user, mock submission tracked.

---

## Phase 10: Demo dataset, testing, hardening, rehearsal (Weeks 10 to 11)

**Tasks**
1. Build the five synthetic cases (section 21 missing). Suggested scenarios derived from the PRD: (1) clean single exchange deposit, (2) tiny hop-1 exchange vs large hop-3 exchange to prove the ranking principle, (3) conflicting labels, (4) high-risk with mixer and peel chain (risk 72 / HIGH), (5) bridge then deposit.
2. Expected-output JSON per case; `make seed-demo` loads registry, fixtures, users, cases in one command.
3. Test suite: unit per feature and cap, contract per provider, failure-matrix 17 rows, RBAC matrix, SSRF vectors (FR-SEC-02), log scan for secrets (FR-SEC-03), audit tamper test, G5 byte-identical rerun, G8 timing (depth 3 under 30 s p95 on demo data).
4. Live-mode smoke on a few real public addresses with `PARTIAL` handling verified, plus UNVERIFIED-EXTERNAL checks of explorer quotas.
5. Performance and cap tuning, DB indexes on `graph_edges`.
6. Demo script (5 minutes): case 2 first to show ranking, then explain screen, then evidence, then report, then mock SAHYOG.
7. Failure drills: kill a provider mid-run to show `PARTIAL`, then resume (P1).
8. Backup plan: recorded screen capture plus a pre-seeded database dump.
9. Documentation: architecture diagram, limitations slide (attribution is a lead, not proof), how to add a chain or adapter in one file.

**Exit criteria:** three consecutive clean dry runs under 5 minutes; every G1 to G8 target ticked.

---

## 2. Dependency map

```
P0 ──► P1 ──► P3(fixture) ──► P4 ──► P5 ──► P6 ──► P9 ──► P10
        │        │             │      ▲       ▲
        └► P2 ───┘             │      │       │
                               └► P7 ─┘       │
P8 (frontend) starts at P4 and consumes each phase's API as it lands
```

## 3. Definition of done (applies to every phase)
- Code merged with tests; CI green.
- Every new endpoint has a `require()` permission and an audit event.
- Every new datum carries a `provenance_class`.
- No secret appears in logs, evidence or responses.
- Failure paths return `PARTIAL` or an explicit error, never fabricated data.

## 4. Scope cut-line (if time runs short)

| Keep (P0) | Drop first (P1) | Drop if desperate (P2) |
|---|---|---|
| Demo mode, fixture provider, registry, graph, attribution, risk, evidence, PDF, mock SAHYOG, RBAC, audit | Live Tron, cancel/resume, graph export, registry UI, LLM, MFA, depth 7 | Commercial adapters, generic bridge matching, Bitcoin, Solana, Neo4j |

Never cut: evidence gate, attribution/risk independence, audit chain, limitations text, SYNTHETIC ribbon.

## 5. Top risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Missing PRD sections 11 to 26 | Certain | Obtain them, or freeze a Decisions doc before Phase 5 |
| Flow propagation bugs | Medium | Hand-computed unit graphs first |
| Live explorer rate limits | High | Fixture-first, cache everything, live mode is a bonus |
| Demo weights look overfit | Medium | Freeze weights early, version any change |
| Frontend graph performance | Medium | Filtered default subgraph |
| Scope creep into LLM or commercial adapters | High | Cut-line above, enforced in standups |

## 6. Open questions to resolve this week
1. Final SIH submission date and demo format (live vs recorded)?
2. Who supplies the full PRD sections 11 to 26?
3. Keycloak or local JWT only for the demo?
4. Which explorer providers and keys are actually available for live mode?
5. Is a PDF-only report acceptable, or is a Word export also expected?

## 7. Compressed 6-week variant
| Week | Work |
|---|---|
| 1 | Phases 0, 1 (auth, audit) and fixture provider |
| 2 | Registry, expansion, flow propagation |
| 3 | Orchestrator, snapshot, attribution core |
| 4 | Caps, risk, evidence; frontend graph and overview |
| 5 | Cross-chain demo bridge, report, SAHYOG mock, demo cases |
| 6 | Testing, live-mode smoke on EVM only, rehearsal |

In this variant, drop Tron live, LLM, registry UI and cancel/resume.
