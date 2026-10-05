"use client";

import React from "react";

interface LandingPageProps {
  onLaunchWorkbench: (caseRef?: string) => void;
  onOpenDashboard: () => void;
  onOpenSahyog: () => void;
  currentRole: "analyst" | "supervisor";
  onRoleChange: (role: "analyst" | "supervisor") => void;
}

export default function LandingPage({
  onLaunchWorkbench,
  onOpenDashboard,
  onOpenSahyog,
  currentRole,
  onRoleChange,
}: LandingPageProps) {
  return (
    <div className="w-full min-h-screen bg-surface font-body-md text-on-surface antialiased flex flex-col">
      {/* SIMULATION / SOVEREIGN AUDIT TOP BAR */}
      <aside
        aria-label="System Environment Banner"
        className="w-full bg-secondary text-on-primary py-1 px-space-md flex flex-wrap items-center justify-between font-label-mono text-label-mono border-b border-primary-container"
      >
        <div className="flex items-center gap-space-sm">
          <span className="inline-block w-2 h-2 bg-on-primary animate-pulse"></span>
          <span className="tracking-widest">SYSTEM SPECIFICATION // SIH26182</span>
          <span className="hidden md:inline text-secondary-fixed text-body-sm font-body-sm tracking-normal">
            |
          </span>
          <span className="hidden md:inline">FORENSIC TRANSACTION ATTRIBUTION SUITE</span>
        </div>
        <div className="flex items-center gap-space-md">
          <span className="text-body-sm font-label-mono tracking-widest hidden sm:inline">
            STATE: VERIFIABLE LEDGER TRACE
          </span>
          <span className="bg-primary-container text-on-primary px-1.5 py-0.5 text-label-caps font-label-caps tracking-widest">
            STRICT PROVENANCE
          </span>
        </div>
      </aside>

      {/* EDITORIAL MASTHEAD & PRIMARY NAVIGATION */}
      <header className="w-full bg-surface-container-lowest border-b border-primary/20 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-space-md lg:px-space-xl py-space-md flex flex-wrap items-center justify-between gap-space-md">
          {/* Brand lockup */}
          <div className="flex items-baseline gap-space-sm">
            <button
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              className="font-headline-md text-headline-md tracking-tight text-primary font-bold hover:text-secondary transition-colors font-serif"
            >
              DHANRASHI
            </button>
            <span className="hidden sm:inline-block font-label-mono text-label-caps tracking-widest text-outline uppercase">
              {"// VASP-TRACE • SIH26182"}
            </span>
          </div>

          {/* Navigation links */}
          <nav className="hidden lg:flex items-center gap-space-lg font-label-caps text-label-caps text-on-surface uppercase tracking-widest">
            <a className="hover:text-secondary border-b-2 border-transparent hover:border-secondary py-1 transition-colors" href="#manifesto">
              Manifesto
            </a>
            <a className="hover:text-secondary border-b-2 border-transparent hover:border-secondary py-1 transition-colors" href="#thesis">
              Core Thesis
            </a>
            <a className="hover:text-secondary border-b-2 border-transparent hover:border-secondary py-1 transition-colors" href="#factors">
              10-Factor Matrix
            </a>
            <a className="hover:text-secondary border-b-2 border-transparent hover:border-secondary py-1 transition-colors" href="#pipeline">
              Pipeline
            </a>
            <a className="hover:text-secondary border-b-2 border-transparent hover:border-secondary py-1 transition-colors" href="#cases">
              Dossier Archive
            </a>
            <button
              onClick={onOpenSahyog}
              className="hover:text-secondary border-b-2 border-transparent hover:border-secondary py-1 transition-colors cursor-pointer uppercase"
            >
              SAHYOG Portal
            </button>
          </nav>

          {/* Action Panel & Role Selector */}
          <div className="flex items-center gap-space-sm">
            <div className="flex items-center bg-surface-container border border-primary/20 font-label-mono text-label-caps p-0.5">
              <button
                className={`px-2 py-1 font-label-mono uppercase transition-all ${
                  currentRole === "analyst" ? "bg-primary text-on-primary" : "text-on-surface hover:text-secondary"
                }`}
                onClick={() => onRoleChange("analyst")}
              >
                ANALYST
              </button>
              <button
                className={`px-2 py-1 font-label-mono uppercase transition-all ${
                  currentRole === "supervisor" ? "bg-primary text-on-primary" : "text-on-surface hover:text-secondary"
                }`}
                onClick={() => onRoleChange("supervisor")}
              >
                SUPERVISOR
              </button>
            </div>
            <button
              onClick={() => onLaunchWorkbench("CASE-02")}
              className="px-4 py-2 bg-secondary text-on-primary font-label-caps text-label-caps tracking-widest hover:bg-primary transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
            >
              <span>LAUNCH WORKBENCH</span>
              <span className="material-symbols-outlined text-sm">arrow_outward</span>
            </button>
          </div>
        </div>
      </header>

      {/* HERO SECTION: ASYMMETRIC FORENSIC FOLIO */}
      <section className="w-full bg-primary text-on-primary relative overflow-hidden border-b border-primary/30" id="home">
        {/* Grid overlay texture */}
        <div className="absolute inset-0 opacity-10 pointer-events-none bg-[linear-gradient(to_right,#ffffff_1px,transparent_1px),linear-gradient(to_bottom,#ffffff_1px,transparent_1px)] bg-[size:4rem_4rem]"></div>
        <div className="max-w-7xl mx-auto px-space-md lg:px-space-xl py-space-xl lg:py-24 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl items-start">
            {/* Left Editorial Broadside (7 cols) */}
            <div className="lg:col-span-7 flex flex-col justify-between space-y-space-lg">
              <div className="space-y-space-sm">
                <div className="inline-flex items-center gap-space-xs font-label-mono text-label-caps tracking-widest text-primary-fixed uppercase border border-primary-fixed/30 px-2 py-1 bg-primary-container/40">
                  <span className="w-1.5 h-1.5 bg-secondary-container rounded-full"></span>
                  PROBLEM STATEMENT SIH26182 • COMPLIANCE & FORENSICS
                </div>
                <h1 className="font-display-hero text-display-hero lg:text-[76px] leading-[0.98] tracking-tight font-serif pt-2 text-surface-bright">
                  FOLLOW THE MONEY.<br />
                  <span className="italic font-normal text-secondary-fixed">FIND THE SERVICE.</span>
                </h1>
              </div>
              <p className="font-body-lg text-body-lg text-primary-fixed/90 max-w-2xl leading-relaxed">
                DHANRASHI reconstructs multi-hop cryptocurrency fund flows, disambiguates Virtual Asset Service Provider (VASP) destinations using explainable multi-factor attribution, independently assesses transit risk, and compiles cryptographic evidentiary dockets for sovereign judicial scrutiny.
              </p>

              {/* Interactive Action Block */}
              <div className="flex flex-wrap items-center gap-space-md pt-2">
                <button
                  onClick={() => onLaunchWorkbench("CASE-02")}
                  className="px-space-lg py-3.5 bg-secondary text-on-primary font-label-caps text-label-caps tracking-widest hover:bg-surface hover:text-primary transition-colors flex items-center gap-space-sm shadow-md cursor-pointer"
                >
                  <span className="material-symbols-outlined text-base">manage_search</span>
                  <span>START TRACE INVESTIGATION</span>
                </button>
                <button
                  onClick={onOpenDashboard}
                  className="px-space-lg py-3.5 border border-primary-fixed text-primary-fixed hover:bg-primary-fixed hover:text-primary transition-colors font-label-caps text-label-caps tracking-widest flex items-center gap-space-sm cursor-pointer"
                >
                  <span className="material-symbols-outlined text-base">folder_open</span>
                  <span>INSPECT DETERMINISTIC CASES</span>
                </button>
              </div>

              {/* Ledger Network Badges */}
              <div className="pt-space-md border-t border-primary-container">
                <span className="block font-label-mono text-label-caps text-on-primary-container uppercase tracking-widest mb-2">
                  MONITORED ON-CHAIN SETTLEMENT PROTOCOLS
                </span>
                <div className="flex flex-wrap items-center gap-space-sm">
                  {[
                    "ETHEREUM (MAINNET)",
                    "BNB SMART CHAIN",
                    "POLYGON PoS",
                    "TRON (TRC-20)",
                  ].map((network) => (
                    <span
                      key={network}
                      className="px-2.5 py-1 bg-primary-container border border-primary-fixed/20 font-label-mono text-label-mono text-surface-bright flex items-center gap-1.5"
                    >
                      <span className="w-1.5 h-1.5 bg-surface-tint"></span> {network}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Graph Hologram Preview (5 cols) */}
            <div className="lg:col-span-5 bg-surface text-on-surface border border-primary p-space-md lg:p-space-lg shadow-xl relative">
              <div className="flex items-center justify-between pb-space-sm border-b border-primary/20 mb-space-md font-label-mono text-label-mono">
                <span className="text-primary font-bold flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-sm text-secondary">hub</span>
                  FOLIO TRACE #084-ALPHA
                </span>
                <span className="px-2 py-0.5 bg-primary text-on-primary text-label-caps font-label-caps uppercase">
                  OBSERVED GRAPH
                </span>
              </div>

              {/* Synthetic Trace Graph Canvas Simulation */}
              <div className="bg-surface-container p-space-md border border-primary/20 space-y-space-md relative">
                <div className="flex items-center justify-between text-label-mono font-label-mono text-on-surface-variant">
                  <span>ROOT SEED: <strong className="text-on-surface">0x7a2...4f9</strong></span>
                  <span className="text-secondary font-semibold">120.00 ETH DISBURSED</span>
                </div>

                <div className="relative py-2 flex flex-col gap-space-sm font-label-mono text-label-mono">
                  {/* Hop 0 */}
                  <div className="flex items-center justify-between p-2 bg-surface-container-lowest border-l-2 border-primary">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 bg-primary text-on-primary text-center font-bold text-[10px] leading-5">00</span>
                      <div>
                        <div className="font-bold text-on-surface">EXPLOIT OUTLET</div>
                        <div className="text-[10px] text-outline">0x7a29bc...e4f9</div>
                      </div>
                    </div>
                    <span className="px-1.5 py-0.5 bg-primary/10 text-primary text-[10px] font-bold">TAINT: 100%</span>
                  </div>

                  <div className="flex items-center justify-between px-4 text-[10px] text-outline">
                    <span>↓ Hop 1 (Layering)</span>
                    <span className="text-secondary font-bold font-label-mono">112.5 ETH (93.7%)</span>
                  </div>

                  {/* Hop 1 */}
                  <div className="flex items-center justify-between p-2 bg-surface-container-lowest border-l-2 border-primary/40">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 bg-surface-variant text-on-surface text-center font-bold text-[10px] leading-5">01</span>
                      <div>
                        <div className="font-bold text-on-surface">INTERMEDIARY HOP A</div>
                        <div className="text-[10px] text-outline">0x4b18c1...99a2</div>
                      </div>
                    </div>
                    <span className="px-1.5 py-0.5 bg-surface-variant text-on-surface-variant text-[10px]">SPLIT HOP</span>
                  </div>

                  <div className="flex items-center justify-between px-4 text-[10px] text-outline">
                    <span>↓ Hop 2 (Cross-Chain Bridge)</span>
                    <span className="text-secondary font-bold font-label-mono">105.6 ETH (88.0%)</span>
                  </div>

                  {/* Hop 2 Bridge */}
                  <div className="flex items-center justify-between p-2 bg-surface-container-lowest border-l-2 border-secondary">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 bg-secondary text-on-primary text-center font-bold text-[10px] leading-5">02</span>
                      <div>
                        <div className="font-bold text-on-surface">SYNAPSE / HOP BRIDGE</div>
                        <div className="text-[10px] text-outline">0xdf921a...71ca • POLYGON TARGET</div>
                      </div>
                    </div>
                    <span className="px-1.5 py-0.5 bg-secondary-fixed text-on-secondary-fixed-variant text-[10px] font-bold">CROSS-CHAIN</span>
                  </div>

                  <div className="flex items-center justify-between px-4 text-[10px] text-secondary font-bold">
                    <span>↓ Final Deposit Sweep (Batch)</span>
                    <span className="font-label-mono">105.6 ETH (88.0% TOTAL FLOW)</span>
                  </div>

                  {/* Hop 3 Destination */}
                  <div className="p-3 bg-primary text-on-primary border border-secondary shadow-sm">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-[10px] uppercase tracking-widest text-primary-fixed block font-label-mono">
                          RESOLVED DESTINATION ENTITY
                        </span>
                        <h2 className="font-headline-sm text-headline-sm font-serif font-bold text-surface-bright">
                          VASP ALPHA (CUSTODIAL)
                        </h2>
                        <p className="text-label-mono text-label-mono text-primary-fixed-dim">
                          Cluster: 0x93f4e2...88cc • Hot Sweep #04
                        </p>
                      </div>
                      <span className="px-2 py-1 bg-secondary text-on-primary font-label-mono text-label-caps font-bold">
                        RANK #1 CANDIDATE
                      </span>
                    </div>
                    <div className="mt-2 pt-2 border-t border-primary-container flex items-center justify-between text-label-mono text-[11px]">
                      <span>10-FACTOR CONFIDENCE SCORE:</span>
                      <span className="text-secondary-fixed font-bold font-label-mono text-body-lg">87.4 / 100</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Telemetry Chips */}
              <div className="grid grid-cols-3 gap-space-xs mt-space-md text-center font-label-mono text-label-mono">
                <div className="p-2 bg-surface-container border border-primary/10">
                  <span className="text-[10px] text-outline block uppercase">Graph Distance</span>
                  <strong className="text-body-lg text-primary">3 HOPS</strong>
                </div>
                <div className="p-2 bg-surface-container border border-primary/10">
                  <span className="text-[10px] text-outline block uppercase">Flow Absorbed</span>
                  <strong className="text-body-lg text-secondary">88.0%</strong>
                </div>
                <div className="p-2 bg-surface-container border border-primary/10">
                  <span className="text-[10px] text-outline block uppercase">Resolution</span>
                  <strong className="text-body-lg text-primary">EXPLAINABLE</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MANIFESTO / ANALYTICAL SHORTCOMING SECTION */}
      <section className="w-full bg-surface-container-low py-space-xl lg:py-24 border-b border-primary/20" id="manifesto">
        <div className="max-w-7xl mx-auto px-space-md lg:px-space-xl">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl items-baseline">
            <div className="lg:col-span-5 space-y-space-sm">
              <span className="font-label-mono text-label-caps text-secondary uppercase tracking-widest block font-bold">
                ANALYTICAL SHORTCOMING
              </span>
              <h2 className="font-headline-lg text-headline-lg font-serif tracking-tight text-primary font-bold">
                THE BLOCKCHAIN REMEMBERS.<br />
                <em className="font-normal italic text-secondary">THE INVESTIGATOR NEEDS A MAP.</em>
              </h2>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                In financial cybercrime casework, raw block explorers offer only atomized ledger entries. Investigators drown in endless peel chains, deceptive intermediary wash addresses, and proprietary black-box scoring systems that fail the evidentiary standard in a sovereign court of law.
              </p>
            </div>

            <div className="lg:col-span-7">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
                {/* Without DHANRASHI */}
                <div className="bg-surface border border-outline-variant p-space-lg flex flex-col justify-between space-y-space-md">
                  <div className="space-y-space-sm">
                    <div className="flex items-center justify-between border-b border-outline-variant pb-2">
                      <span className="font-label-caps text-label-caps tracking-widest text-error uppercase font-bold">
                        WITHOUT DHANRASHI
                      </span>
                      <span className="material-symbols-outlined text-error text-lg">cancel</span>
                    </div>
                    <h3 className="font-headline-sm text-headline-sm font-serif text-primary font-bold">
                      The Manual Explorer Quagmire
                    </h3>
                    <ul className="space-y-2.5 font-body-sm text-body-sm text-on-surface-variant">
                      <li className="flex items-start gap-2">
                        <span className="text-error font-bold">×</span>
                        <span>Dozens of open browser tabs across Etherscan, Tronscan, and BscScan.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-error font-bold">×</span>
                        <span>Deceptive “nearest hop” heuristics point to 2-hop dusting dustbins.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-error font-bold">×</span>
                        <span>Conflicting intelligence labels with no mathematical explanation.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-error font-bold">×</span>
                        <span>Ad-hoc screenshots rejected by judicial bodies as unverified evidence.</span>
                      </li>
                    </ul>
                  </div>
                  <div className="p-2 bg-error/5 text-error font-label-mono text-label-mono border border-error/20 text-center">
                    ATTRITION RATE: ~84% LOSS OF PROVABLE CHAIN
                  </div>
                </div>

                {/* With DHANRASHI */}
                <div className="bg-surface-container-lowest border-2 border-primary p-space-lg flex flex-col justify-between space-y-space-md shadow-md">
                  <div className="space-y-space-sm">
                    <div className="flex items-center justify-between border-b border-primary/20 pb-2">
                      <span className="font-label-caps text-label-caps tracking-widest text-primary font-bold uppercase">
                        WITH DHANRASHI
                      </span>
                      <span className="material-symbols-outlined text-primary text-lg">verified</span>
                    </div>
                    <h3 className="font-headline-sm text-headline-sm font-serif text-primary font-bold">
                      Deterministic Sovereign Forensics
                    </h3>
                    <ul className="space-y-2.5 font-body-sm text-body-sm text-on-surface">
                      <li className="flex items-start gap-2">
                        <span className="text-primary font-bold">✓</span>
                        <span>Multi-hop fluid flow conservation algorithms tracking genuine bulk liquidity.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary font-bold">✓</span>
                        <span>10-Factor transparent polynomial attribution with full mathematical weights.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary font-bold">✓</span>
                        <span>Autonomous Section 91 CrPC lawful notice generation with Ed25519 signatures.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary font-bold">✓</span>
                        <span>Dual-state Merkle tree docket anchored to the immutable evidentiary ledger.</span>
                      </li>
                    </ul>
                  </div>
                  <div className="p-2 bg-primary/10 text-primary font-label-mono text-label-mono border border-primary/30 text-center font-bold">
                    RECOVERY VERIFICATION: 94.2% DETERMINISTIC
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CORE THESIS SECTION */}
      <section className="w-full bg-surface py-space-xl lg:py-24 border-b border-primary/20" id="thesis">
        <div className="max-w-7xl mx-auto px-space-md lg:px-space-xl space-y-space-xl">
          <div className="max-w-3xl space-y-space-xs">
            <span className="font-label-mono text-label-caps text-secondary uppercase tracking-widest font-bold">
              SCIENTIFIC FOUNDATION // HEURISTIC DEBUNKING
            </span>
            <h2 className="font-headline-lg text-headline-lg font-serif tracking-tight text-primary font-bold">
              THE MATHEMATICAL FAILURE OF SHORTEST-PATH HEURISTICS
            </h2>
            <p className="font-body-lg text-body-lg text-on-surface-variant leading-relaxed">
              When bad actors launder funds, they intentionally route a tiny fraction of dust to a nearby exchange within 1 or 2 hops to trigger naive early termination in commercial compliance engines, while quietly channeling 90%+ of bulk proceeds across a 3-hop or 4-hop wash network.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-space-lg">
            <div className="p-space-md bg-surface-container-low border border-primary/20 space-y-2">
              <span className="font-label-mono text-secondary text-data-metric font-bold block">01</span>
              <h3 className="font-title-editorial text-title-editorial font-bold text-primary font-serif">
                Volume-Preserving Fluidity
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Rather than treating all hops as equal, Dhanrashi calculates flow conservation: if a 2-hop entity receives $5k and a 3-hop entity receives $88k, the 3-hop entity is mathematically weighted at over 14x significance.
              </p>
            </div>

            <div className="p-space-md bg-surface-container-low border border-primary/20 space-y-2">
              <span className="font-label-mono text-secondary text-data-metric font-bold block">02</span>
              <h3 className="font-title-editorial text-title-editorial font-bold text-primary font-serif">
                Peel-Chain Graph Pruning
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Intermediary peel washers that retain or disperse small change are automatically collapsed and attributed as transit conduits rather than genuine endpoints.
              </p>
            </div>

            <div className="p-space-md bg-surface-container-low border border-primary/20 space-y-2">
              <span className="font-label-mono text-secondary text-data-metric font-bold block">03</span>
              <h3 className="font-title-editorial text-title-editorial font-bold text-primary font-serif">
                Temporal Velocity Decay
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Automated multi-hop hops executed in sub-20 minute intervals indicate rapid scripted layering, boosting attribution certainty to downstream custodial deposit sweeps.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 10-FACTOR ATTRIBUTION MATRIX SECTION */}
      <section className="w-full bg-surface-container-low py-space-xl lg:py-24 border-b border-primary/20" id="factors">
        <div className="max-w-7xl mx-auto px-space-md lg:px-space-xl space-y-space-lg">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md border-b border-primary/20 pb-space-md">
            <div>
              <span className="font-label-mono text-label-caps text-secondary uppercase tracking-widest font-bold">
                SCORING MATRIX // SPECIFICATION
              </span>
              <h2 className="font-headline-lg text-headline-lg font-serif tracking-tight text-primary font-bold">
                THE 10-FACTOR ATTRIBUTION MATRIX
              </h2>
            </div>
            <span className="font-label-mono text-body-sm bg-surface-container px-3 py-1 border border-primary/20 text-primary font-bold">
              POLYNOMIAL ATT-v1.0 (NORMALIZED 0-100)
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-space-sm font-label-mono text-body-sm">
            {[
              { id: "F01", name: "Flow Volume Share", weight: "35%", formula: "w1 · (V_vasp / V_total)", desc: "Proportion of total tainted funds absorbed." },
              { id: "F02", name: "Temporal Continuity", weight: "15%", formula: "w2 · exp(-λ·Δt)", desc: "Decay over elapsed time between hops." },
              { id: "F03", name: "Entity Cluster Confidence", weight: "15%", formula: "w3 · C_score", desc: "Corroborated hot/cold deposit cluster keys." },
              { id: "F04", name: "Direct Hop Proximity", weight: "10%", formula: "w4 / (H + 1)", desc: "Controlled inverse hop distance penalty." },
              { id: "F05", name: "Fee-Payer Clustering", weight: "5%", formula: "w5 · δ(fee_origin)", desc: "Shared gas funding address attribution." },
              { id: "F06", name: "Sweep Pattern Match", weight: "5%", formula: "w6 · δ(batch_sweep)", desc: "Hot-wallet batch aggregation signature." },
              { id: "F07", name: "Cross-Chain Bridge Link", weight: "5%", formula: "w7 · B_fidelity", desc: "Cross-ledger lock/mint or swap proof." },
              { id: "F08", name: "Transit Velocity Factor", weight: "5%", formula: "w8 · (1 - t_norm)", desc: "Automated wash scripting velocity metric." },
              { id: "F09", name: "Mixer / Tumbler Penalty", weight: "PENALTY", formula: "-P_mixer · M_flag", desc: "Subtractive penalty for unpeeled mixing." },
              { id: "F10", name: "Co-Spending Graph Heuristic", weight: "5%", formula: "w10 · CoSpend(U)", desc: "Common input ownership verification." },
            ].map((f) => (
              <div key={f.id} className="bg-surface p-space-sm border border-primary/20 flex flex-col justify-between hover:bg-surface-container transition-colors">
                <div>
                  <div className="flex items-center justify-between pb-1 mb-1 border-b border-primary/10">
                    <span className="font-bold text-secondary">{f.id}</span>
                    <span className="px-1.5 py-0.5 bg-primary text-on-primary text-[10px] font-bold">{f.weight}</span>
                  </div>
                  <div className="font-body-md font-bold text-primary mt-1">{f.name}</div>
                  <div className="text-[11px] text-outline mt-1 font-sans">{f.desc}</div>
                </div>
                <div className="mt-3 pt-1 border-t border-primary/10 text-[10px] text-on-surface-variant font-mono truncate">
                  {f.formula}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FORENSIC PIPELINE ARCHITECTURE SECTION */}
      <section className="w-full bg-surface py-space-xl lg:py-24 border-b border-primary/20" id="pipeline">
        <div className="max-w-7xl mx-auto px-space-md lg:px-space-xl space-y-space-lg">
          <div className="max-w-3xl space-y-space-xs">
            <span className="font-label-mono text-label-caps text-secondary uppercase tracking-widest font-bold">
              END-TO-END PIPELINE ARCHITECTURE
            </span>
            <h2 className="font-headline-lg text-headline-lg font-serif tracking-tight text-primary font-bold">
              SOVEREIGN EVIDENCE ACQUISITION & DISPATCH
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-space-md">
            <div className="bg-surface-container-low p-space-md border border-primary/20 relative">
              <span className="font-label-mono text-secondary font-bold text-sm block mb-1">STAGE 01</span>
              <h3 className="font-title-editorial font-bold text-primary font-serif">Multi-Chain RPC Ingestion</h3>
              <p className="font-body-sm text-on-surface-variant mt-2">
                Real-time extraction of raw blocks, transactions, contract logs, and internal traces across Ethereum, Polygon, BSC, and Tron.
              </p>
            </div>

            <div className="bg-surface-container-low p-space-md border border-primary/20 relative">
              <span className="font-label-mono text-secondary font-bold text-sm block mb-1">STAGE 02</span>
              <h3 className="font-title-editorial font-bold text-primary font-serif">Graph Topology & Pruning</h3>
              <p className="font-body-sm text-on-surface-variant mt-2">
                Construction of directed acyclic transaction graph with combinatorial peel-chain pruning and bridge identification.
              </p>
            </div>

            <div className="bg-surface-container-low p-space-md border border-primary/20 relative">
              <span className="font-label-mono text-secondary font-bold text-sm block mb-1">STAGE 03</span>
              <h3 className="font-title-editorial font-bold text-primary font-serif">Attribution & Risk Scoring</h3>
              <p className="font-body-sm text-on-surface-variant mt-2">
                Execution of the 10-Factor ATT-v1.0 polynomial algorithm to rank candidate VASPs with full factor decomposition.
              </p>
            </div>

            <div className="bg-surface-container-low p-space-md border border-primary/20 relative">
              <span className="font-label-mono text-secondary font-bold text-sm block mb-1">STAGE 04</span>
              <h3 className="font-title-editorial font-bold text-primary font-serif">SAHYOG Sovereign Dispatch</h3>
              <p className="font-body-sm text-on-surface-variant mt-2">
                Automated preparation of formal Section 91 CrPC notice, Merkle tree anchoring, and Ed25519 digital sign-off.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* DOSSIER ARCHIVE SECTION */}
      <section className="w-full bg-surface-container-low py-space-xl lg:py-24 border-b border-primary/20" id="cases">
        <div className="max-w-7xl mx-auto px-space-md lg:px-space-xl space-y-space-lg">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md border-b border-primary/20 pb-space-md">
            <div>
              <span className="font-label-mono text-label-caps text-secondary uppercase tracking-widest font-bold">
                BENCHMARK CASERUNS // SYNTHETIC
              </span>
              <h2 className="font-headline-lg text-headline-lg font-serif tracking-tight text-primary font-bold">
                DETERMINISTIC CASE DOSSIER ARCHIVE
              </h2>
            </div>
            <button
              onClick={onOpenDashboard}
              className="px-4 py-2 border border-primary text-primary hover:bg-primary hover:text-surface font-label-caps text-label-caps uppercase font-bold tracking-wider transition-colors cursor-pointer"
            >
              VIEW MASTER DASHBOARD →
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
            {/* Case 02 */}
            <div className="bg-surface border-2 border-secondary p-space-md flex flex-col justify-between shadow-md">
              <div>
                <div className="flex items-center justify-between pb-1 mb-2 bg-surface-container px-2 py-1">
                  <span className="font-label-mono text-body-sm font-bold text-primary">CASE-02</span>
                  <span className="px-1.5 py-0.5 bg-secondary text-on-secondary font-label-caps text-[9px] font-bold">FLAGSHIP</span>
                </div>
                <h3 className="font-headline-sm text-headline-sm font-serif font-bold text-primary">
                  Shorter Path vs. Larger Flow Discrepancy
                </h3>
                <p className="font-body-sm text-on-surface-variant mt-2">
                  Target splits 5% dust to Candidate A (2 hops) while routing 88% bulk flow to Candidate B (3 hops).
                </p>
                <div className="mt-3 p-2 bg-surface-container font-label-mono text-[11px] space-y-1">
                  <div>• Chain: ETH-MAINNET</div>
                  <div>• True Lead: VASP ALPHA (87.4 / 100)</div>
                  <div>• Trap Lead: VASP BETA (42.1 / 100)</div>
                </div>
              </div>
              <button
                onClick={() => onLaunchWorkbench("CASE-02")}
                className="mt-4 w-full py-2 bg-secondary text-on-secondary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-primary transition-colors cursor-pointer text-center"
              >
                LOAD IN WORKBENCH
              </button>
            </div>

            {/* Case 04 */}
            <div className="bg-surface border border-primary/20 p-space-md flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-center justify-between pb-1 mb-2 bg-surface-container px-2 py-1">
                  <span className="font-label-mono text-body-sm font-bold text-primary">CASE-04</span>
                  <span className="px-1.5 py-0.5 bg-surface-dim text-on-surface font-label-caps text-[9px] font-bold">4 HOPS</span>
                </div>
                <h3 className="font-headline-sm text-headline-sm font-serif font-bold text-primary">
                  Peel-Chain Mixer Wash & Bridge
                </h3>
                <p className="font-body-sm text-on-surface-variant mt-2">
                  Complex tumbler layering with peel change disbursement across multiple intermediate accounts.
                </p>
                <div className="mt-3 p-2 bg-surface-container font-label-mono text-[11px] space-y-1">
                  <div>• Chain: ETH-MAINNET</div>
                  <div>• True Lead: VASP DELTA (64.8 / 100)</div>
                  <div>• Transit Risk: 86 / 100 (HIGH)</div>
                </div>
              </div>
              <button
                onClick={() => onLaunchWorkbench("CASE-04")}
                className="mt-4 w-full py-2 bg-primary text-on-primary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-secondary transition-colors cursor-pointer text-center"
              >
                LOAD IN WORKBENCH
              </button>
            </div>

            {/* Case 05 */}
            <div className="bg-surface border border-primary/20 p-space-md flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-center justify-between pb-1 mb-2 bg-surface-container px-2 py-1">
                  <span className="font-label-mono text-body-sm font-bold text-primary">CASE-05</span>
                  <span className="px-1.5 py-0.5 bg-surface-dim text-on-surface font-label-caps text-[9px] font-bold">CROSS-CHAIN</span>
                </div>
                <h3 className="font-headline-sm text-headline-sm font-serif font-bold text-primary">
                  Cross-Chain Bridge Liquidity Jump
                </h3>
                <p className="font-body-sm text-on-surface-variant mt-2">
                  Funds routed across Ethereum-Polygon bridge pool into exchange deposit cluster.
                </p>
                <div className="mt-3 p-2 bg-surface-container font-label-mono text-[11px] space-y-1">
                  <div>• Chain: POLYGON PoS</div>
                  <div>• True Lead: VASP GAMMA (79.2 / 100)</div>
                  <div>• Bridge Verification: SYNAPSE PROOF</div>
                </div>
              </div>
              <button
                onClick={() => onLaunchWorkbench("CASE-05")}
                className="mt-4 w-full py-2 bg-primary text-on-primary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-secondary transition-colors cursor-pointer text-center"
              >
                LOAD IN WORKBENCH
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* INSTITUTIONAL FOOTER */}
      <footer className="w-full bg-primary text-on-primary py-space-xl border-t border-primary/40">
        <div className="max-w-7xl mx-auto px-space-md lg:px-space-xl flex flex-col md:flex-row items-center justify-between gap-space-md font-label-mono text-body-sm">
          <div>
            <span className="font-bold text-surface">DHANRASHI // VASP-TRACE</span>
            <span className="text-primary-fixed-dim block text-xs mt-1">
              Smart India Hackathon (SIH26182) • Sovereign Blockchain Intelligence Suite
            </span>
          </div>
          <div className="text-right text-xs text-primary-fixed-dim">
            Attribution leads are mathematical investigative indicators, not proof of culpability until corroborated.
          </div>
        </div>
      </footer>
    </div>
  );
}
