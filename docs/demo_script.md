# VASP-Trace 5-Minute SIH Presentation & Demonstration Script

## Overview
This document provides the step-by-step 5-minute rehearsal script for presenting `VASP-Trace` to SIH evaluators.

---

## 5-Minute Demonstration Agenda

| Minute | Focus Area | Action & Narrative |
|---|---|---|
| **0:00 - 0:45** | **Introduction & Persona Switcher** | Log in as `inv@vasptrace.internal` (Inspector Roy). Highlight the **SYNTHETIC DATA** ribbon indicating demo isolation. Demonstrate the role switcher (`INV`, `FIA`, `SUP`, `AUD`). |
| **0:45 - 1:45** | **Case 2: Pro-Rata Flow Ranking Proof** | Open Case 2 (`CASE-DEMO-002`) with seed wallet `0x0000000000000000000000000000000000aa0002`. Click **Run Investigation**. Show graph traversal capturing $500 to Coinbase at Hop-1 vs $8,800 to Kraken at Hop-3. Explain why Kraken ranks #1 (pro-rata flow captured = 88% vs 5%). |
| **1:45 - 2:30** | **"Explain Attribution" & G2 Proof** | Open the **Explain Attribution** drawer. Show the 10-feature scoring matrix, dynamic weight renormalization, and the **G2 Verification Badge** ($\sum \text{contributions} == \text{raw\_score} \pm 0.001$). Highlight applied caps (CAP-01 through CAP-08) and investigative lead disclaimers. |
| **2:30 - 3:15** | **Case 4: Risk Engine & Mixer Overlay** | Open Case 4 (`CASE-DEMO-004`). Toggle the **Risk Signals Overlay**. Point out the Tornado Cash mixer hop glowing red, the rapid movement (<15 min), and the peel chain. Show the **Risk Score 72 / HIGH** card. Reiterate AT-12 independence: regulated VASPs carry zero risk score (FR-RISK-04). |
| **3:15 - 4:00** | **Evidence Ledger & Provenance Badges** | Open the **Evidence Ledger** tab. Highlight color-coded provenance badges (`OBSERVED`, `THIRD-PARTY INTELLIGENCE`, `DERIVED`, `INFERENCE`). Click **Verify Hash Chain** to execute real-time SHA-256 integrity verification over the append-only ledger. |
| **4:00 - 4:45** | **PDF Report & Supervisory Approval** | Generate the multi-page PDF report. Point out the `X-Report-SHA256` checksum header and mandatory disclaimers. Switch persona to `sup@vasptrace.internal` (Superintendent Verma). Show separation of duties: author cannot approve own report. Approve report, draft SAHYOG statutory request, and show transition (`DRAFT` → `SUBMITTED` → `ACKNOWLEDGED`). |
| **4:45 - 5:00** | **Conclusion & Key Takeaways** | Summarize core innovations: 100% explainable AI attribution, independent risk scoring, cryptographic evidence ledger, statutory SAHYOG readiness, and sub-30s graph traversal. |

---

## 5 Synthetic Demo Scenarios Summary

| Case | Reference | Target Wallet | Key Highlight | Expected Attribution |
|---|---|---|---|---|
| **Case 1** | `CASE-DEMO-001` | `0x0000...aa0001` | Clean single-hop deposit | `VASP-BINANCE` (HIGH) |
| **Case 2** | `CASE-DEMO-002` | `0x0000...aa0002` | Flow % ranking proof (Hop-3 outranks Hop-1) | `VASP-KRAKEN` (MEDIUM) |
| **Case 3** | `CASE-DEMO-003` | `0x0000...aa0003` | Conflicting VASP labels (CAP-04 capping) | `VASP-OKEX` (MEDIUM) |
| **Case 4** | `CASE-DEMO-004` | `0x0000...aa0004` | Mixer + peel chain + rapid movement | `VASP-HUOBI` (Risk 72 / HIGH) |
| **Case 5** | `CASE-DEMO-005` | `0x0000...aa0005` | Cross-chain bridge (ETH -> Polygon) | `VASP-POLYGON-DEX` (HIGH) |

---

## Technical Emergency Backup Plan
If live network or web execution is interrupted during the live demo:
1. **Local Docker Fallback:** Run `make up && make seed-demo` to execute against local SQLite/PostgreSQL.
2. **Pre-Seeded Output Verification:** All expected JSON files are stored in `data/demo/expected/case[1-5].json` for offline verification.
