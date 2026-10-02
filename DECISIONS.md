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
