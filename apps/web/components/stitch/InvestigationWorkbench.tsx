"use client";

import React, { useState } from "react";

interface InvestigationWorkbenchProps {
  initialCaseRef?: string;
  initialAddress?: string;
  initialChain?: string;
  initialHopDepth?: number;
  onOpenFileSahyog?: (caseRef: string) => void;
  onVerifyEvidenceChain?: () => void;
}

export default function InvestigationWorkbench({
  initialCaseRef = "CASE-02",
  initialAddress = "0x71C94828b8E85B438B0F2A389A2",
  initialChain = "ETH-MAINNET",
  initialHopDepth = 3,
  onOpenFileSahyog,
  onVerifyEvidenceChain,
}: InvestigationWorkbenchProps) {
  // Traversal Engine Controls
  const [hopDepth, setHopDepth] = useState<number>(initialHopDepth);
  const [fluidityCutoff, setFluidityCutoff] = useState<number>(5000);
  const [activeLedger, setActiveLedger] = useState<string>("ETHEREUM");
  const [activeViewTab, setActiveViewTab] = useState<"canvas" | "waterfall" | "timeline">("canvas");
  const [activeInspectorTab, setActiveInspectorTab] = useState<"attribution" | "risk" | "evidence">("attribution");
  const [analystDisposition, setAnalystDisposition] = useState<"ACCEPT" | "REJECT" | "REVIEW" | null>("ACCEPT");
  const [showExplainModal, setShowExplainModal] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [isReRunning, setIsReRunning] = useState<boolean>(false);

  // Filters
  const [filterVaspOnly, setFilterVaspOnly] = useState(true);
  const [filterVelocity, setFilterVelocity] = useState(true);
  const [filterBridge, setFilterBridge] = useState(true);
  const [filterTerminal, setFilterTerminal] = useState(true);
  const [filterBadges, setFilterBadges] = useState(true);

  const handleReRun = () => {
    setIsReRunning(true);
    setTimeout(() => {
      setIsReRunning(false);
    }, 600);
  };

  return (
    <div className="flex flex-col w-full">
      {/* TOP TOOLBAR & FORENSIC DOSSIER BANNER */}
      <section className="bg-surface-container-low p-space-md mb-space-lg border border-primary/20 shadow-sm">
        <div className="flex flex-col 2xl:flex-row items-start 2xl:items-center justify-between gap-space-md">
          {/* Case Meta Title & Context */}
          <div className="flex flex-col gap-space-xs">
            <div className="flex flex-wrap items-center gap-space-sm">
              <span className="px-2 py-0.5 bg-primary text-on-primary font-label-mono text-body-sm font-semibold tracking-wider">
                {`${initialCaseRef} // FORENSIC WORKBENCH`}
              </span>
              <span className="font-headline-sm text-headline-sm font-bold tracking-tight text-primary">
                Shorter Path vs. Larger Flow Discrepancy
              </span>
              <span className="px-2 py-0.5 bg-primary-container text-surface font-label-caps text-label-caps uppercase tracking-widest font-semibold">
                STATUS: COMPLETED
              </span>
              <span className="px-2 py-0.5 bg-secondary-container text-on-secondary-container font-label-mono text-body-sm uppercase tracking-wider font-semibold">
                SYNTHETIC DEMO
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-x-space-md gap-y-1 font-label-mono text-body-sm text-on-surface-variant">
              <span className="flex items-center gap-1">
                <span className="text-secondary font-bold">TARGET:</span>
                <span className="bg-surface-container px-1 text-on-surface select-all font-bold">
                  {initialAddress}
                </span>
                <span className="text-outline text-[10px]">[{initialChain.toUpperCase()}]</span>
              </span>
              <span className="text-outline">/</span>
              <span>
                EXECUTION: <strong className="text-on-surface">RUN #03</strong>
              </span>
              <span className="text-outline">/</span>
              <span>
                SNAPSHOT: <strong className="text-on-surface font-label-mono">SNAP-00182</strong>
              </span>
              <span className="text-outline">/</span>
              <span>
                VASP REGISTRY: <strong className="text-on-surface">REG-004</strong>
              </span>
              <span className="text-outline">/</span>
              <span>
                SCORING WEIGHTS: <strong className="text-secondary font-bold font-label-mono">ATT-v1.0 (FLOW BIAS: 0.72)</strong>
              </span>
            </div>
          </div>

          {/* Institutional Action Group */}
          <div className="flex flex-wrap items-center gap-space-sm self-stretch 2xl:self-auto justify-end">
            <button
              onClick={() => onOpenFileSahyog && onOpenFileSahyog(initialCaseRef)}
              className="flex items-center gap-space-xs px-space-md py-2 bg-secondary text-on-secondary font-label-caps text-label-caps tracking-widest hover:bg-primary transition-colors cursor-pointer shadow-md"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">account_balance</span>
              <span>FILE SAHYOG REQUEST</span>
              <span className="px-1 bg-surface text-secondary text-[9px] font-label-mono font-bold ml-1">MOCK</span>
            </button>
            <button
              onClick={() => alert("Cryptographic PDF Dossier generated with SHA-256 Merkle root anchor.")}
              className="flex items-center gap-space-xs px-space-md py-2 bg-primary-container text-surface hover:bg-primary font-label-caps text-label-caps tracking-widest transition-colors cursor-pointer shadow-sm"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">picture_as_pdf</span>
              <span>GENERATE PDF DOSSIER</span>
            </button>
            <button
              onClick={onVerifyEvidenceChain || (() => alert("Evidence chain validated: Merkle root 0x93FA...CE88 matches distributed registry."))}
              className="flex items-center gap-space-xs px-space-md py-2 bg-surface text-primary hover:bg-surface-variant font-label-caps text-label-caps tracking-widest transition-colors cursor-pointer border border-primary/20 shadow-sm"
              type="button"
            >
              <span className="material-symbols-outlined text-secondary text-[16px]">verified</span>
              <span>VERIFY EVIDENCE CHAIN</span>
            </button>
          </div>
        </div>
      </section>

      {/* 12-COLUMN MAIN INVESTIGATION ENGINE GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-start">
        {/* COLUMNS 1-3: FILTER & ATTRIBUTION TUNING CONTROLS */}
        <aside className="lg:col-span-3 flex flex-col gap-space-md">
          {/* Traversal Parameters Card */}
          <div className="bg-surface-container-low p-space-md border border-primary/20 shadow-sm">
            <div className="flex items-center justify-between mb-space-md pb-space-xs bg-surface-container px-space-sm py-1">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-secondary text-[18px]">tune</span>
                <span className="font-label-caps text-label-caps font-bold uppercase tracking-wider text-primary">
                  TRAVERSAL ENGINE PARAMETERS
                </span>
              </div>
              <span className="font-label-mono text-body-sm text-outline">CFG.02</span>
            </div>

            {/* Hop Depth Control */}
            <div className="mb-space-md">
              <div className="flex justify-between items-center mb-space-xs">
                <label className="font-label-caps text-label-caps text-primary uppercase font-bold tracking-wider">
                  GRAPH EXPLORATION DEPTH
                </label>
                <span className="font-label-mono text-body-md font-bold text-secondary bg-surface px-2 py-0.5 border border-primary/10">
                  {hopDepth} HOPS
                </span>
              </div>
              <div className="relative w-full flex items-center gap-2">
                <input
                  className="w-full h-1.5 bg-surface-dim accent-secondary cursor-pointer"
                  max="5"
                  min="1"
                  type="range"
                  value={hopDepth}
                  onChange={(e) => setHopDepth(Number(e.target.value))}
                />
                <span className="font-label-mono text-body-sm text-outline">MAX 5</span>
              </div>
              <div className="mt-1 flex items-center gap-1 font-label-mono text-[10px] text-on-surface-variant">
                <span className="material-symbols-outlined text-[12px] text-secondary">info</span>
                <span>Depths &gt;3 activate iterative peel-chain combinatorial pruning.</span>
              </div>
            </div>

            {/* Minimum Flow Threshold */}
            <div className="mb-space-md">
              <div className="flex justify-between items-center mb-space-xs">
                <label className="font-label-caps text-label-caps text-primary uppercase font-bold tracking-wider">
                  MIN FLUIDITY CUTOFF
                </label>
                <span className="font-label-mono text-body-sm text-on-surface-variant font-medium">
                  ${fluidityCutoff.toLocaleString()} USD ({((fluidityCutoff / 100000) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="grid grid-cols-3 gap-1 text-center font-label-mono text-body-sm">
                {[1000, 5000, 25000].map((amt) => (
                  <button
                    key={amt}
                    type="button"
                    onClick={() => setFluidityCutoff(amt)}
                    className={`py-1 font-bold transition-colors cursor-pointer ${
                      fluidityCutoff === amt
                        ? "bg-primary text-on-primary shadow-sm"
                        : "bg-surface hover:bg-surface-variant text-on-surface"
                    }`}
                  >
                    ${amt >= 1000 ? `${amt / 1000}k` : amt}
                  </button>
                ))}
              </div>
            </div>

            {/* Chain Matrix */}
            <div className="mb-space-md">
              <label className="block font-label-caps text-label-caps text-primary uppercase font-bold tracking-wider mb-space-xs">
                TARGET DISTRIBUTED LEDGER
              </label>
              <div className="grid grid-cols-2 gap-1 font-label-mono text-body-sm">
                {[
                  { id: "ETHEREUM", label: "ETHEREUM" },
                  { id: "POLYGON", label: "POLYGON" },
                  { id: "BNB CHAIN", label: "BNB CHAIN" },
                  { id: "TRON", label: "TRON" },
                ].map((c) => (
                  <div
                    key={c.id}
                    onClick={() => setActiveLedger(c.id)}
                    className={`p-2 flex items-center justify-between cursor-pointer transition-colors ${
                      activeLedger === c.id
                        ? "bg-primary text-on-primary font-semibold"
                        : "bg-surface text-on-surface-variant hover:text-on-surface"
                    }`}
                  >
                    <span>{c.label}</span>
                    <span
                      className={`w-2 h-2 rounded-full ${
                        activeLedger === c.id ? "bg-secondary-container" : "bg-outline/50"
                      }`}
                    ></span>
                  </div>
                ))}
              </div>
            </div>

            {/* Rectilinear Forensic Toggles */}
            <div className="flex flex-col gap-2 mb-space-md pt-space-xs border-t border-primary/10">
              <label className="font-label-caps text-label-caps text-primary uppercase font-bold tracking-wider mb-1">
                PROVENANCE FILTERS
              </label>
              {[
                { label: "VASP Clusters Only", val: filterVaspOnly, setVal: setFilterVaspOnly },
                { label: "Transit Velocity Stress", val: filterVelocity, setVal: setFilterVelocity },
                { label: "Cross-Chain Bridge Telemetry", val: filterBridge, setVal: setFilterBridge },
                { label: "Terminal Sweep Attribution", val: filterTerminal, setVal: setFilterTerminal },
                { label: "Evidentiary Provenance Badges", val: filterBadges, setVal: setFilterBadges },
              ].map((item, idx) => (
                <label
                  key={idx}
                  className="flex items-center justify-between p-2 bg-surface cursor-pointer hover:bg-surface-container transition-colors"
                >
                  <span className="font-label-mono text-body-sm text-on-surface">{item.label}</span>
                  <input
                    type="checkbox"
                    checked={item.val}
                    onChange={(e) => item.setVal(e.target.checked)}
                    className="w-4 h-4 accent-secondary rounded-none"
                  />
                </label>
              ))}
            </div>

            {/* Re-run Attribution Trigger */}
            <button
              onClick={handleReRun}
              disabled={isReRunning}
              className="w-full py-2.5 bg-secondary hover:bg-primary text-on-secondary font-label-caps text-label-caps uppercase tracking-widest font-bold transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-md disabled:opacity-70"
              type="button"
            >
              <span className={`material-symbols-outlined text-[18px] ${isReRunning ? "animate-spin" : ""}`}>
                rotate_right
              </span>
              <span>{isReRunning ? "RE-CALCULATING FLOWS..." : "RE-RUN ATTRIBUTION ENGINE"}</span>
            </button>
          </div>

          {/* Engine Mathematical Premise Callout */}
          <div className="bg-surface-container p-space-md border border-primary/20">
            <div className="flex items-center gap-space-xs text-secondary font-label-caps text-label-caps font-bold tracking-wider mb-space-xs uppercase">
              <span className="material-symbols-outlined text-[16px]">balance</span>
              <span>HEURISTIC DISCREPANCY RULE</span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed mb-space-xs">
              Naïve graph heuristics privilege the closest entity in hop distance (Candidate A @ 2 hops). Dhanrashi ATT-v1.0 models <em>fluid volume preservation</em>: Candidate B receives <strong>88.0% of stolen liquidity</strong> across an elongated 3-hop mixing structure.
            </p>
            <div className="p-2 bg-surface-container-high font-label-mono text-[10px] text-on-surface border border-outline/20">
              WEIGHT MATRIX: Flow(0.70) + Temporal(0.15) + EntityCluster(0.10) - HopDecay(0.05)
            </div>
          </div>
        </aside>

        {/* COLUMNS 4-9: CENTRAL INTERACTIVE FLOW & GRAPH CANVAS */}
        <main className="lg:col-span-6 flex flex-col gap-space-md">
          {/* View State Tabs */}
          <div className="flex items-center justify-between bg-surface-container-low p-1 border border-primary/20">
            <div className="flex items-center">
              <button
                type="button"
                onClick={() => setActiveViewTab("canvas")}
                className={`px-space-md py-2 font-label-caps text-label-caps tracking-widest font-bold uppercase transition-colors ${
                  activeViewTab === "canvas"
                    ? "bg-primary text-on-primary shadow-sm"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                TRANSACTION GRAPH CANVAS
              </button>
              <button
                type="button"
                onClick={() => setActiveViewTab("waterfall")}
                className={`px-space-md py-2 font-label-caps text-label-caps tracking-widest uppercase transition-colors ${
                  activeViewTab === "waterfall"
                    ? "bg-primary text-on-primary font-bold shadow-sm"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                FLOW WATERFALL DIVERGENCE
              </button>
              <button
                type="button"
                onClick={() => setActiveViewTab("timeline")}
                className={`px-space-md py-2 font-label-caps text-label-caps tracking-widest uppercase transition-colors ${
                  activeViewTab === "timeline"
                    ? "bg-primary text-on-primary font-bold shadow-sm"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                CROSS-CHAIN TIMELINE
              </button>
            </div>
            <div className="flex items-center gap-2 pr-2 text-on-surface-variant font-label-mono text-body-sm">
              <span className="inline-block w-2 h-2 rounded-full bg-secondary-container animate-pulse"></span>
              <span>CANVAS: ACTIVE DUAL-PATH SIMULATION</span>
            </div>
          </div>

          {/* Graph Viewport Container */}
          <div className="relative bg-primary-container text-on-primary p-space-md min-h-[580px] overflow-hidden flex flex-col justify-between border border-primary">
            {/* Watermark */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none">
              <span className="font-headline-lg text-[64px] text-surface/5 font-bold uppercase tracking-widest transform -rotate-12">
                SYNTHETIC FORENSIC TRACE
              </span>
            </div>

            {/* Canvas HUD Overlay Header */}
            <div className="relative z-10 flex items-center justify-between pb-space-xs bg-primary/80 px-space-sm py-1.5 backdrop-blur-sm border-b border-primary-fixed/20">
              <div className="flex items-center gap-space-md">
                <span className="font-label-mono text-body-sm text-surface font-semibold tracking-tight">
                  CANVAS VIEW // DISCOVERY MESH ({zoomLevel}%)
                </span>
                <span className="px-2 py-0.5 bg-surface/10 font-label-mono text-[10px] text-surface-variant">
                  5 VERTICES / 4 DIRECTED EDGES
                </span>
              </div>
              <div className="flex items-center gap-space-sm">
                <button
                  onClick={() => setZoomLevel((z) => Math.min(150, z + 15))}
                  className="p-1 text-surface hover:text-secondary-fixed transition-colors cursor-pointer"
                  title="Zoom In"
                  type="button"
                >
                  <span className="material-symbols-outlined text-[18px]">zoom_in</span>
                </button>
                <button
                  onClick={() => setZoomLevel((z) => Math.max(70, z - 15))}
                  className="p-1 text-surface hover:text-secondary-fixed transition-colors cursor-pointer"
                  title="Zoom Out"
                  type="button"
                >
                  <span className="material-symbols-outlined text-[18px]">zoom_out</span>
                </button>
                <button
                  onClick={() => setZoomLevel(100)}
                  className="p-1 text-surface hover:text-secondary-fixed transition-colors cursor-pointer"
                  title="Fit to Screen"
                  type="button"
                >
                  <span className="material-symbols-outlined text-[18px]">fit_screen</span>
                </button>
              </div>
            </div>

            {/* Vector Forensics Node Layout Simulation */}
            <div
              className="relative z-10 my-auto py-space-md transition-transform duration-200"
              style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: "center center" }}
            >
              <div className="w-full flex flex-col gap-space-xl">
                {/* HOP 0: Origin Root Wallet */}
                <div className="flex items-center">
                  <div className="w-64 bg-surface p-space-sm shadow-xl border border-primary">
                    <div className="flex items-center justify-between mb-1 pb-1 bg-surface-container px-1">
                      <span className="font-label-caps text-[9px] text-secondary font-bold uppercase tracking-widest">
                        ORIGIN TARGET NODE
                      </span>
                      <span className="px-1 bg-primary text-on-primary font-label-mono text-[9px]">
                        OBSERVED
                      </span>
                    </div>
                    <div className="font-label-mono text-body-sm font-bold text-primary truncate select-all">
                      0x71C9...89A2
                    </div>
                    <div className="flex justify-between items-center text-[10px] font-label-mono text-on-surface-variant mt-1">
                      <span>UNIDENTIFIED WALLET</span>
                      <span className="font-bold text-primary">$100,000.00</span>
                    </div>
                  </div>

                  <div className="flex-1 px-4 flex flex-col items-center">
                    <div className="w-full h-0.5 bg-secondary-container relative flex items-center justify-center">
                      <span className="material-symbols-outlined text-secondary text-[16px] absolute right-0">
                        arrow_right
                      </span>
                    </div>
                    <span className="font-label-mono text-[10px] text-surface-variant mt-1 tracking-tight">
                      100% DISPATCH ($100k)
                    </span>
                  </div>

                  {/* INTERMEDIARY HOP 1 */}
                  <div className="w-60 bg-surface-container p-space-sm border border-outline/30">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-label-caps text-[9px] text-primary uppercase font-bold tracking-wider">
                        HOP 1: INTERMEDIARY
                      </span>
                      <span className="px-1 bg-outline text-surface font-label-mono text-[9px]">
                        TRANSIT
                      </span>
                    </div>
                    <div className="font-label-mono text-body-sm font-semibold text-primary truncate">
                      0x94bF...48E1
                    </div>
                    <div className="text-[10px] font-label-mono text-on-surface-variant">
                      TRANSIT VELOCITY: 12 MIN
                    </div>
                  </div>
                </div>

                {/* PATH FORKING: DIVERGENCE (Candidate A vs Candidate B) */}
                <div className="grid grid-cols-2 gap-space-lg pt-space-xs relative">
                  {/* CANDIDATE A (Top Branch: 2 Hops, Short Path Trap) */}
                  <div className="flex flex-col gap-2 relative">
                    <div className="flex items-center">
                      <div className="w-12 h-0.5 bg-outline/60 relative flex items-center justify-end">
                        <span className="material-symbols-outlined text-outline text-[16px]">arrow_right</span>
                      </div>
                      <div className="bg-surface-container-high p-space-sm flex-1 border border-outline/30">
                        <div className="flex items-center justify-between">
                          <span className="font-label-caps text-[9px] text-outline font-bold tracking-widest uppercase">
                            HOP 2 TERMINUS (SHORTEST)
                          </span>
                          <span className="px-1.5 py-0.5 bg-surface-dim text-on-surface font-label-mono text-[9px] font-bold">
                            5% FLOW
                          </span>
                        </div>
                        <div className="font-title-editorial text-title-editorial text-primary font-bold mt-1">
                          CANDIDATE A: VASP BETA
                        </div>
                        <div className="font-label-mono text-body-sm text-on-surface-variant">
                          0x3e17...B5a8
                        </div>
                        <div className="mt-2 p-1.5 bg-surface flex items-center justify-between text-body-sm font-label-mono">
                          <span className="text-outline">DEPOSITED:</span>
                          <span className="text-on-surface font-bold">$5,000.00 USD</span>
                        </div>
                        <div className="mt-1 text-[10px] font-label-mono text-error font-medium">
                          [!] ATTRIBUTION RATING: 42.1 (LOW CONFIDENCE)
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* CANDIDATE B (Bottom Branch: 3 Hops, Stolen Liquidity Destination) */}
                  <div className="flex flex-col gap-2 relative">
                    {/* Peel Intermediary */}
                    <div className="flex items-center">
                      <div className="w-12 h-0.5 bg-secondary relative flex items-center justify-end">
                        <span className="material-symbols-outlined text-secondary text-[16px]">arrow_right</span>
                      </div>
                      <div className="bg-surface-container p-2 w-48 border border-secondary/40">
                        <div className="font-label-caps text-[8px] text-secondary font-bold uppercase tracking-widest">
                          HOP 2: PEEL WASHER
                        </div>
                        <div className="font-label-mono text-[11px] font-medium text-primary truncate">
                          0x48cF...119A
                        </div>
                        <div className="font-label-mono text-[9px] text-outline">RETAINED: 88.0%</div>
                      </div>
                      <div className="w-8 h-0.5 bg-secondary relative flex items-center justify-end">
                        <span className="material-symbols-outlined text-secondary text-[16px]">arrow_right</span>
                      </div>

                      {/* The True Target */}
                      <div className="bg-surface p-space-sm flex-1 shadow-2xl border-2 border-secondary">
                        <div className="flex items-center justify-between mb-1 pb-1 bg-surface-container px-1">
                          <span className="px-1.5 py-0.5 bg-secondary text-on-secondary font-label-caps text-[9px] font-bold uppercase tracking-widest">
                            PRIMARY RECIPIENT
                          </span>
                          <span className="px-1.5 py-0.5 bg-secondary-container text-on-secondary-container font-label-mono text-[9px] font-bold">
                            88% FLOW SHARE
                          </span>
                        </div>
                        <div className="font-title-editorial text-title-editorial text-primary font-bold">
                          CANDIDATE B: VASP ALPHA
                        </div>
                        <div className="font-label-mono text-body-sm text-secondary font-bold select-all">
                          0x11a3...77Ec
                        </div>
                        <div className="mt-2 p-1.5 bg-primary text-on-primary flex items-center justify-between text-body-sm font-label-mono">
                          <span>FLOW ABSORBED:</span>
                          <span className="font-bold text-secondary-container">$88,000.00 USD</span>
                        </div>
                        <div className="mt-1.5 flex items-center justify-between text-[10px] font-label-mono">
                          <span className="text-on-surface-variant">TEMPORAL: 1.4 HOURS</span>
                          <span className="text-secondary font-bold">SCORE: 87.4 / 100</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Canvas Flow Summary Ledger Bar */}
            <div className="relative z-10 bg-surface text-primary p-space-sm border-t border-primary/20">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-space-sm font-label-mono text-body-sm">
                <div className="flex flex-col">
                  <span className="text-outline text-[10px] uppercase tracking-wider font-semibold">
                    TOTAL TRACED ORIGIN
                  </span>
                  <span className="font-bold text-primary text-body-lg">$100,000.00</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-secondary text-[10px] uppercase tracking-wider font-semibold">
                    VASP ALPHA (HOP 3)
                  </span>
                  <span className="font-bold text-secondary text-body-lg">$88,000.00 (88.0%)</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-outline text-[10px] uppercase tracking-wider font-semibold">
                    VASP BETA (HOP 2)
                  </span>
                  <span className="font-bold text-on-surface text-body-lg">$5,000.00 (5.0%)</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-outline text-[10px] uppercase tracking-wider font-semibold">
                    UNRESOLVED PEELS
                  </span>
                  <span className="font-bold text-on-surface-variant text-body-lg">$7,000.00 (7.0%)</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-outline text-[10px] uppercase tracking-wider font-semibold">
                    COVERAGE RATIO
                  </span>
                  <span className="font-bold text-primary text-body-lg">93.0% RECOVERED</span>
                </div>
              </div>
              {/* Multi-Segment Flow Progress Bar */}
              <div className="w-full h-2 bg-surface-dim mt-2 flex border border-primary/10">
                <div className="bg-secondary h-full" style={{ width: "88%" }} title="VASP Alpha (88%)"></div>
                <div className="bg-outline h-full" style={{ width: "5%" }} title="VASP Beta (5%)"></div>
                <div className="bg-surface-variant h-full" style={{ width: "7%" }} title="Peels (7%)"></div>
              </div>
            </div>
          </div>

          {/* Forensics Dossier Note */}
          <div className="bg-surface-container-low p-space-md border border-primary/20 shadow-sm">
            <div className="flex items-start gap-space-sm">
              <span className="material-symbols-outlined text-secondary text-[24px]">troubleshoot</span>
              <div className="flex flex-col gap-1">
                <span className="font-label-caps text-label-caps font-bold text-primary uppercase tracking-widest">
                  INVESTIGATOR INTELLIGENCE NOTE // CASE-02 AUDIT
                </span>
                <p className="font-body-md text-body-md text-on-surface leading-relaxed">
                  Target address deployed an intentional obfuscation pattern: small split diversion to Candidate A (VASP Beta) within 2 hops to trigger early termination in legacy shortest-path heuristics, while routing 88% of liquidity via wallet{" "}
                  <code className="font-label-mono bg-surface-variant px-1 text-on-surface">
                    0x48cF...119A
                  </code>{" "}
                  directly to hot deposit accounts belonging to Candidate B (VASP Alpha).
                </p>
              </div>
            </div>
          </div>
        </main>

        {/* COLUMNS 10-12: ATTRIBUTION INSPECTOR & EVIDENCE PROVENANCE */}
        <aside className="lg:col-span-3 flex flex-col gap-space-md">
          {/* Tab Switcher for Inspector */}
          <div className="grid grid-cols-3 bg-surface-container font-label-caps text-label-caps font-bold uppercase tracking-wider text-center border border-primary/20">
            <button
              onClick={() => setActiveInspectorTab("attribution")}
              className={`py-2.5 transition-colors cursor-pointer ${
                activeInspectorTab === "attribution"
                  ? "bg-primary text-on-primary shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
              type="button"
            >
              ATTRIBUTION
            </button>
            <button
              onClick={() => setActiveInspectorTab("risk")}
              className={`py-2.5 transition-colors cursor-pointer ${
                activeInspectorTab === "risk"
                  ? "bg-primary text-on-primary shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
              type="button"
            >
              RISK (72)
            </button>
            <button
              onClick={() => setActiveInspectorTab("evidence")}
              className={`py-2.5 transition-colors cursor-pointer ${
                activeInspectorTab === "evidence"
                  ? "bg-primary text-on-primary shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
              type="button"
            >
              EVIDENCE (6)
            </button>
          </div>

          {/* PRIMARY CANDIDATE #1: VASP ALPHA CARD */}
          <div className="bg-surface-container-low p-space-md shadow-md border border-primary/20">
            <div className="flex items-center justify-between pb-space-xs mb-space-sm bg-surface px-space-sm py-1 border border-primary/10">
              <div className="flex items-center gap-1 font-label-caps text-label-caps font-bold text-secondary uppercase tracking-widest">
                <span className="material-symbols-outlined text-[16px]">stars</span>
                <span>#1 RANKED CANDIDATE</span>
              </div>
              <span className="px-1.5 py-0.5 bg-primary text-on-primary font-label-mono text-[9px] uppercase font-semibold">
                LEAD ENTITY
              </span>
            </div>

            <div className="flex items-baseline justify-between mb-space-xs">
              <h3 className="font-headline-sm text-headline-sm font-bold text-primary">VASP ALPHA</h3>
              <span className="font-data-metric text-data-metric font-bold text-secondary leading-none">
                87.4<span className="text-body-sm font-normal text-outline">/100</span>
              </span>
            </div>

            <div className="inline-block px-2 py-0.5 bg-surface-container font-label-mono text-body-sm text-secondary font-bold mb-space-sm border border-secondary/20">
              STRONG INVESTIGATIVE LEAD
            </div>

            {/* Factor Decomposition Breakdown */}
            <div className="flex flex-col gap-2 pt-space-xs mb-space-md border-t border-primary/10">
              <div className="flex items-center justify-between text-body-sm font-label-mono">
                <span className="text-on-surface-variant">Flow Volume Share</span>
                <span className="font-bold text-primary">88.0% (+61.6 pts)</span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-label-mono">
                <span className="text-on-surface-variant">Cluster Confidence</span>
                <span className="font-bold text-primary">HIGH (FinTrace DB)</span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-label-mono">
                <span className="text-on-surface-variant">Temporal Continuity</span>
                <span className="font-bold text-primary">1.4h (+14.2 pts)</span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-label-mono">
                <span className="text-on-surface-variant">Hop Distance Decay</span>
                <span className="font-bold text-on-surface-variant">3 Hops (-3.4 pts)</span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-label-mono">
                <span className="text-on-surface-variant">Applied Penalty Caps</span>
                <span className="font-bold text-primary font-label-caps">NONE (PASSED GATE)</span>
              </div>
            </div>

            <button
              onClick={() => setShowExplainModal(true)}
              className="w-full py-2 bg-surface hover:bg-surface-variant text-primary font-label-caps text-label-caps uppercase tracking-wider font-bold transition-colors cursor-pointer mb-space-md border border-primary/20 shadow-sm"
              type="button"
            >
              EXPLAIN MATHEMATICAL WEIGHTS
            </button>

            {/* Analyst Disposition Block */}
            <div className="p-space-sm bg-surface-container border border-primary/20">
              <div className="font-label-caps text-[9px] uppercase tracking-widest font-bold text-primary mb-2">
                ANALYST ADJUDICATION DISPOSITION
              </div>
              <div className="grid grid-cols-3 gap-1 text-center font-label-caps text-[9px]">
                <button
                  type="button"
                  onClick={() => setAnalystDisposition("ACCEPT")}
                  className={`py-1.5 font-bold uppercase transition-colors cursor-pointer shadow-sm ${
                    analystDisposition === "ACCEPT"
                      ? "bg-secondary text-on-secondary"
                      : "bg-surface text-on-surface hover:bg-surface-dim"
                  }`}
                >
                  ACCEPT LEAD
                </button>
                <button
                  type="button"
                  onClick={() => setAnalystDisposition("REJECT")}
                  className={`py-1.5 font-bold uppercase transition-colors cursor-pointer ${
                    analystDisposition === "REJECT"
                      ? "bg-error text-on-error"
                      : "bg-surface text-on-surface hover:bg-surface-dim"
                  }`}
                >
                  REJECT
                </button>
                <button
                  type="button"
                  onClick={() => setAnalystDisposition("REVIEW")}
                  className={`py-1.5 font-bold uppercase transition-colors cursor-pointer ${
                    analystDisposition === "REVIEW"
                      ? "bg-primary text-on-primary"
                      : "bg-surface text-on-surface hover:bg-surface-dim"
                  }`}
                >
                  REVIEW
                </button>
              </div>
              <div className="mt-2 text-[9px] font-label-mono text-outline leading-tight">
                * INFERENCE: Disposition logged to immutable audit ledger; does not modify algorithmic engine score.
              </div>
            </div>
          </div>

          {/* SECONDARY CANDIDATE #2: VASP BETA (SHORTEST PATH TRAP) */}
          <div className="bg-surface-container p-space-md border border-primary/20">
            <div className="flex items-center justify-between mb-1 pb-1 bg-surface px-space-sm py-1 border border-primary/10">
              <span className="font-label-caps text-label-caps text-outline font-bold uppercase tracking-wider">
                #2 RANKED (WEAK CANDIDATE)
              </span>
              <span className="px-1.5 py-0.5 bg-surface-dim text-on-surface font-label-mono text-[9px] uppercase">
                TRAP LEAD
              </span>
            </div>
            <div className="flex items-baseline justify-between">
              <h4 className="font-title-editorial text-title-editorial font-bold text-primary">VASP BETA</h4>
              <span className="font-headline-sm text-headline-sm font-bold text-outline">
                42.1<span className="text-body-sm font-normal text-outline">/100</span>
              </span>
            </div>
            <div className="text-[10px] font-label-mono text-error font-medium mt-1">
              SHORTEST PATH HEURISTIC FAILURE: Only 5.0% funds absorbed despite 2-hop proximity.
            </div>
          </div>

          {/* TRANSIT RISK SNAPSHOT ACCORDION MINI */}
          <div className="bg-surface-container-low p-space-md border border-primary/20">
            <div className="flex items-center justify-between mb-space-sm pb-space-xs bg-surface px-space-sm py-1 border border-primary/10">
              <div className="flex items-center gap-1 font-label-caps text-label-caps font-bold text-primary uppercase tracking-widest">
                <span className="material-symbols-outlined text-[16px] text-secondary">warning</span>
                <span>TRANSIT VELOCITY RISK</span>
              </div>
              <span className="font-label-mono text-body-sm font-bold text-secondary bg-surface px-1.5 py-0.5">
                72 / 100 HIGH
              </span>
            </div>
            <ul className="flex flex-col gap-1.5 font-label-mono text-body-sm">
              <li className="flex items-start gap-2 text-on-surface">
                <span className="text-secondary font-bold">!</span>
                <span>Rapid Layering (&lt; 20 min hop delta)</span>
              </li>
              <li className="flex items-start gap-2 text-on-surface">
                <span className="text-secondary font-bold">!</span>
                <span>Asymmetric Split Wash Detected</span>
              </li>
              <li className="flex items-start gap-2 text-on-surface">
                <span className="text-primary font-bold">✓</span>
                <span>No Known Tumbler or Darknet Contract</span>
              </li>
            </ul>
          </div>
        </aside>
      </div>

      {/* EXPLAIN MATHEMATICAL WEIGHTS MODAL */}
      {showExplainModal && (
        <div className="fixed inset-0 z-50 bg-primary/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border-2 border-primary max-w-2xl w-full p-space-lg shadow-2xl space-y-space-md">
            <div className="flex items-center justify-between border-b border-primary/20 pb-2">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-[24px]">functions</span>
                <h3 className="font-headline-sm text-headline-sm font-bold text-primary">
                  MATHEMATICAL EXPLANATION // ATT-v1.0 SCORING
                </h3>
              </div>
              <button
                onClick={() => setShowExplainModal(false)}
                className="text-on-surface-variant hover:text-primary p-1 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="font-label-mono text-body-sm bg-surface-container p-3 space-y-2 border border-primary/10">
              <div className="text-primary font-bold">ATTRIBUTION POLYNOMIAL FORMULATION:</div>
              <div className="bg-surface p-2 border border-primary/20 font-bold text-secondary">
                S = w_flow · (V_vasp / V_total) + w_temp · exp(-λ·Δt) + w_clus · C_score - w_hop · (H - 1)
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 text-on-surface-variant">
                <div>• Flow Weight (w_flow): 0.70</div>
                <div>• Temporal Decay (w_temp): 0.15</div>
                <div>• Cluster Confidence (w_clus): 0.10</div>
                <div>• Hop Decay Penalty (w_hop): 0.05</div>
              </div>
            </div>

            <p className="font-body-md text-body-md text-on-surface leading-relaxed">
              In this case, <strong>Candidate B (VASP Alpha)</strong> absorbed $88,000 (88.0%) of stolen funds across 3 hops, yielding 61.6 volume points and 14.2 temporal points. Hop penalty was only -3.4 points. Total score <strong>87.4/100</strong> definitively outranks Candidate A (42.1/100) whose 2-hop proximity was mere dust dusting.
            </p>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowExplainModal(false)}
                className="px-space-md py-2 bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider font-bold hover:bg-secondary transition-colors cursor-pointer"
              >
                CLOSE EXPLANATION
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
