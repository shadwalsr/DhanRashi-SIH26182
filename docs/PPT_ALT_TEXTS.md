# DhanRashi (VASP-Trace / SIH26182) — PowerPoint Alt Text & Image Description Guide

This document contains standardized, accessibility-compliant, and technical **Alt Text descriptions** for all slides, diagrams, graph visualizations, and UI mockups in your PowerPoint presentation.

---

## Slide 1: Title Slide & Platform Overview
* **Visual Content:** High-level DhanRashi platform banner featuring the automated graph tracing topology, VASP attribution engine, and FIU Sahyog compliance badge.
* **Short Alt Text:** 
  > *DhanRashi system overview banner showing automated multi-hop graph tracing, explainable VASP attribution, and FIU Sahyog compliance integration.*
* **Long Description (for presentation notes):** 
  > *System overview banner illustrating the DhanRashi (VASP-Trace) platform architecture. The left panel shows the input seed wallet address, the center highlights the multi-hop transaction graph, and the right badges display 100% deterministic attribution reproducibility and FIU-IND inter-agency integration.*

---

## Slide 2: Problem Statement — Laundering Obfuscation Tactics
* **Visual Content:** Diagram illustrating complex money laundering tactics including rapid peel chains, Tornado Cash mixer obfuscation, and cross-chain bridge hops.
* **Short Alt Text:** 
  > *Diagram of illicit crypto laundering tactics including peel chains, mixer privacy pools, and cross-chain bridge transfers.*
* **Long Description:** 
  > *Flowchart depicting illicit fund movements from a suspect wallet through a 6-hop peel chain, routing through a Tornado Cash mixer pool to obscure provenance, crossing a cross-chain bridge from Polygon to Ethereum, and attempting deposit at an exchange.*

---

## Slide 3: High-Level System Architecture
* **Visual Content:** Block diagram showing the Python 3.11 FastAPI backend, PostgreSQL + asyncpg database, Cytoscape.js graph engine, and Next.js 14 frontend.
* **Short Alt Text:** 
  > *DhanRashi system architecture diagram detailing FastAPI REST API, PostgreSQL database, graph engine, and Next.js frontend.*
* **Long Description:** 
  > *Architectural diagram of DhanRashi. The user interface connects via REST APIs and JWT auth to the FastAPI application layer. The application layer routes queries through the PostgreSQL graph engine, attribution module, risk assessment engine, and cryptographic audit logger.*

---

## Slide 4: Multi-Hop Graph Tracing Engine & BFS Topology
* **Visual Content:** Directed acyclic graph (DAG) showing transaction flows across wallet nodes, intermediate hops, and terminal VASP deposit addresses.
* **Short Alt Text:** 
  > *Interactive multi-hop transaction graph displaying wallet nodes, directed transaction edges, and destination exchange addresses.*
* **Long Description:** 
  > *Directed graph visualization representing a 3-hop transaction trace. Circular nodes represent wallet addresses, directed arrows indicate transfer paths labeled with USD values and transaction hashes, and hexagonal nodes represent identified VASP deposit endpoints.*

---

## Slide 5: Multi-Factor Explainable VASP Attribution Engine
* **Visual Content:** Mathematical formula breakdown and bar chart showing feature weight distribution (Flow %, Co-Deposits, Proximity, Subnet, Timing).
* **Short Alt Text:** 
  > *Explainable attribution feature weight chart illustrating flow percentage, co-deposit clustering, transfer proximity, and timing correlation.*
* **Long Description:** 
  > *Bar graph breaking down the multi-factor attribution algorithm weights: Direct Flow Volume (35%), Co-Deposit Clustering (25%), Direct Transfer Proximity (20%), Infrastructure Co-location (10%), and Behavioral Timing Correlation (10%). Includes the weight renormalization formula.*

---

## Slide 6: Deterministic Attribution Capping Rules (CAP-01..07)
* **Visual Content:** Decision tree flowchart showing raw correlation score evaluation against capping rules CAP-01 through CAP-07.
* **Short Alt Text:** 
  > *Attribution capping flowchart evaluating raw correlation scores against rules CAP-01 through CAP-07 to assign confidence tiers.*
* **Long Description:** 
  > *Flowchart demonstrating deterministic capping rules: CAP-01 caps low flow at 0.40, CAP-03 caps mixer path flow at 0.35, CAP-05 caps conflicting labels at 0.45, and CAP-07 caps stale unverified labels at 0.65. Ensures non-arbitrary and explainable attribution results.*

---

## Slide 7: Independent Transit Risk Scoring Engine
* **Visual Content:** Risk score gauge (0-100) highlighting triggered signals (Peel Chains, Mixers) alongside the VASP Neutrality Invariant.
* **Short Alt Text:** 
  > *Transit laundering risk gauge displaying risk score, triggered signals, and zero-risk rating for regulated VASP terminal nodes.*
* **Long Description:** 
  > *Scorecard displaying an overall Transit Risk Score of 85/100 (HIGH). Highlights triggered laundering indicators including RS-01 (Mixer Pool Hop) and RS-02 (Rapid Peel Chain). Shows regulated destination VASP nodes receiving 0 risk score under the VASP Neutrality Invariant.*

---

## Slide 8: Cross-Chain Bridge Detection & Event Matching
* **Visual Content:** Diagram showing a cross-chain transfer from a Polygon source burn/lock smart contract to an Ethereum destination mint/release contract.
* **Short Alt Text:** 
  > *Cross-chain bridge detection diagram correlating source lock transactions on Polygon with destination release transactions on Ethereum.*
* **Long Description:** 
  > *Diagram detailing cross-chain bridge association logic. Shows source chain transaction (Polygon) matched against destination chain transaction (Ethereum) using value tolerance (+/-0.5%) and time window correlation (under 30 minutes), flagging ambiguous matches.*

---

## Slide 9: Immutable Cryptographic Audit Log & SHA-256 Hash Chain
* **Visual Content:** Diagram of append-only audit log entries linked cryptographically by sequential SHA-256 hash digests.
* **Short Alt Text:** 
  > *Cryptographic audit log diagram showing sequential SHA-256 hash chaining for tamper-evident activity tracking.*
* **Long Description:** 
  > *Diagram of the tamper-evident audit logging mechanism. Each log record stores the actor ID, action, resource ID, timestamp, and previous record hash, linked via SHA-256 digests to guarantee tamper detection.*

---

## Slide 10: FIU Sahyog Inter-Agency Collaboration Portal
* **Visual Content:** UI screenshot of the Sahyog FIU data exchange table showing incoming/outgoing LEA requests and VASP response statuses.
* **Short Alt Text:** 
  > *Sahyog portal interface showing inter-agency data sharing requests, VASP response statuses, and frozen asset tracking.*
* **Long Description:** 
  > *Interface mockup of the Sahyog FIU Inter-Agency Portal. Displays pending requests sent to VASPs for wallet owner KYC details, request reference numbers, submission timestamps, approval statuses, and encrypted data download buttons.*

---

## Slide 11: Demo Cases 1 & 2 — Direct Deposit & Peel Chain Ranking
* **Visual Content:** Graph visualization comparison between a direct 100% deposit to Binance vs a peel chain split between Kraken and Coinbase.
* **Short Alt Text:** 
  > *Graph view comparing Case 1 direct deposit to Case 2 peel chain flow percentage ranking.*
* **Long Description:** 
  > *Side-by-side graph comparison. Left side shows Case 1 with 100% direct transaction flow to Binance. Right side shows Case 2 with a peel chain routing 70% of funds to Kraken and 30% to Coinbase, verifying ranking logic.*

---

## Slide 12: Demo Cases 3 & 4 — Conflicting Labels & Mixer Laundering
* **Visual Content:** Visual graph showing Tornado Cash mixer node highlighted in red and conflicting VASP label badges.
* **Short Alt Text:** 
  > *Graph canvas highlighting Tornado Cash mixer node in red and conflicting vendor entity labels.*
* **Long Description:** 
  > *Graph visualization of Case 3 and Case 4. Shows suspect funds entering Tornado Cash mixer pool (highlighted in red), triggering high risk score, and resolving conflicting vendor entity labels via deterministic CAP-05 rule.*

---

## Slide 13: Demo Case 5 — Cross-Chain Bridge Laundering
* **Visual Content:** Multi-chain graph tracing funds from QuickSwap DEX on Polygon through a demo bridge to an Ethereum VASP deposit node.
* **Short Alt Text:** 
  > *Multi-chain transaction graph tracing funds from Polygon DEX through a cross-chain bridge to Ethereum VASP.*
* **Long Description:** 
  > *Graph visualization of Case 5. Traces seed wallet transfers through QuickSwap DEX on Polygon, across the Demo Cross-Chain Bridge contract, and onto an Ethereum deposit address at Binance.*

---

## Slide 14: Court-Admissible PDF Report & Separation of Duties
* **Visual Content:** Document preview of generated PDF report showing statutory disclaimers, SHA-256 hash stamp, and dual-signature approval block.
* **Short Alt Text:** 
  > *Court-admissible PDF investigation report preview with SHA-256 hash checksum and supervisor signature block.*
* **Long Description:** 
  > *Preview of generated formal investigation report. Features executive summary, VASP attribution breakdown, transit risk metrics, statutory disclaimer block, SHA-256 cryptographic checksum stamp, and dual-signature approval block enforcing Separation of Duties.*

---

## Slide 15: Automated Compliance Test Suite & Benchmark Results
* **Visual Content:** Terminal screenshot showing 115 passing Pytest unit/integration tests and sub-5 second performance benchmarks.
* **Short Alt Text:** 
  > *Terminal test execution results showing 115 out of 115 unit and integration tests passing with 100% success rate.*
* **Long Description:** 
  > *Screenshot of test suite execution output. Displays 115 passing tests across failure matrix, security, reproducibility, and performance suites, highlighting sub-5 second graph traversal over 5,000 nodes.*
