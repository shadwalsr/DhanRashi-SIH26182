"use client";

import React, { useState } from "react";

interface CaseItem {
  ref: string;
  targetAddress: string;
  fullAddress: string;
  chain: string;
  status: "COMPLETED" | "RUNNING" | "QUEUED";
  topVasp: string;
  vaspSub: string;
  score: number;
  scoreGrade: string;
  transitRisk: number;
  riskLevel: "HIGH" | "MEDIUM" | "LOW";
  updated: string;
  hopDepth: number;
}

interface InvestigatorDashboardProps {
  onOpenWorkbench: (caseData?: { address: string; chain: string; hopDepth: number; caseRef?: string }) => void;
  onOpenSahyog: (caseRef?: string) => void;
  onNewInvestigation?: () => void;
}

export default function InvestigatorDashboard({
  onOpenWorkbench,
  onOpenSahyog,
  onNewInvestigation,
}: InvestigatorDashboardProps) {
  const [walletInput, setWalletInput] = useState("0x71C836e1471d497672288079633eA940026e89A2");
  const [selectedChain, setSelectedChain] = useState("eth");
  const [selectedHopDepth, setSelectedHopDepth] = useState(3);
  const [statusFilter, setStatusFilter] = useState<"ALL" | "COMPLETED" | "HIGH_RISK">("ALL");

  const benchmarkCases: CaseItem[] = [
    {
      ref: "CASE-02",
      targetAddress: "0x71C8...89A2",
      fullAddress: "0x71C836e1471d497672288079633eA940026e89A2",
      chain: "ETH",
      status: "COMPLETED",
      topVasp: "VASP ALPHA",
      vaspSub: "(Binance Custody)",
      score: 87.4,
      scoreGrade: "STRONG",
      transitRisk: 72,
      riskLevel: "HIGH",
      updated: "12 mins ago",
      hopDepth: 3,
    },
    {
      ref: "CASE-01",
      targetAddress: "0x3d91...b841",
      fullAddress: "0x3d9129aa48bfe028198f480018b84102919323c1",
      chain: "BNB",
      status: "COMPLETED",
      topVasp: "VASP KAPPA",
      vaspSub: "(Coinbase)",
      score: 94.1,
      scoreGrade: "DEFINITIVE",
      transitRisk: 18,
      riskLevel: "LOW",
      updated: "34 mins ago",
      hopDepth: 2,
    },
    {
      ref: "CASE-04",
      targetAddress: "0x88f2...91c0",
      fullAddress: "0x88f21922c019d44e54880921bbfe4889c01991c0",
      chain: "ETH",
      status: "COMPLETED",
      topVasp: "VASP DELTA",
      vaspSub: "(Kraken Stash)",
      score: 64.8,
      scoreGrade: "MODERATE",
      transitRisk: 86,
      riskLevel: "HIGH",
      updated: "1 hour ago",
      hopDepth: 4,
    },
    {
      ref: "CASE-05",
      targetAddress: "0x90e4...2281",
      fullAddress: "0x90e44b91010b99182334ccfe771891bcaaff2281",
      chain: "POLYGON",
      status: "COMPLETED",
      topVasp: "VASP GAMMA",
      vaspSub: "(OKX Hot Cluster)",
      score: 79.2,
      scoreGrade: "STRONG",
      transitRisk: 68,
      riskLevel: "MEDIUM",
      updated: "3 hours ago",
      hopDepth: 3,
    },
    {
      ref: "CASE-03",
      targetAddress: "TX79w...kL29",
      fullAddress: "TX79wb19K382Laop8912Jkzq991kL29",
      chain: "TRON",
      status: "COMPLETED",
      topVasp: "VASP ZETA",
      vaspSub: "(HTX Sweeper)",
      score: 82.5,
      scoreGrade: "STRONG",
      transitRisk: 75,
      riskLevel: "HIGH",
      updated: "5 hours ago",
      hopDepth: 3,
    },
  ];

  const filteredCases = benchmarkCases.filter((c) => {
    if (statusFilter === "HIGH_RISK") return c.transitRisk >= 70;
    if (statusFilter === "COMPLETED") return c.status === "COMPLETED";
    return true;
  });

  const loadPreset = (address: string, chain: string, depth: number) => {
    setWalletInput(address);
    setSelectedChain(chain);
    setSelectedHopDepth(depth);
  };

  const handleRunTrace = () => {
    onOpenWorkbench({
      address: walletInput,
      chain: selectedChain,
      hopDepth: selectedHopDepth,
      caseRef: "CASE-QUICK",
    });
  };

  return (
    <div className="relative w-full overflow-hidden">
      {/* Background Watermark */}
      <div className="pointer-events-none absolute inset-0 select-none flex items-center justify-center opacity-[0.03] z-0">
        <span className="font-headline-lg text-[130px] font-bold tracking-widest text-primary uppercase rotate-[-18deg] whitespace-nowrap">
          SYNTHETIC EVIDENCE // ARCHIVAL
        </span>
      </div>

      {/* Editorial Header Block */}
      <div className="relative z-10 w-full bg-surface pb-space-lg">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md border-b border-primary/20 pb-space-md">
          <div className="space-y-1">
            <div className="flex items-center gap-space-sm">
              <span className="px-2 py-0.5 bg-primary text-surface font-label-caps text-label-caps uppercase tracking-widest font-semibold">
                DOSSIER REPO // SIH26182
              </span>
              <span className="font-label-mono text-body-sm text-outline uppercase tracking-wider">
                FOLIO REF: FIU-IND-2026-Q1
              </span>
            </div>
            <h1 className="font-headline-lg text-headline-lg font-semibold text-primary tracking-tight">
              INVESTIGATOR DASHBOARD
            </h1>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
              Active cryptocurrency fund tracing, VASP candidate attributions, and pending sovereign intelligence actions.
            </p>
          </div>
          <div className="flex items-center gap-space-sm shrink-0">
            <button
              onClick={onNewInvestigation || (() => onOpenWorkbench())}
              className="group flex items-center gap-2 bg-secondary text-surface px-space-md py-2.5 hover:bg-primary transition-colors cursor-pointer shadow-sm"
              type="button"
            >
              <span className="material-symbols-outlined text-[18px]">add_circle</span>
              <span className="font-label-caps text-label-caps tracking-widest uppercase font-semibold">
                + NEW INVESTIGATION
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Synthetic Notice Sub-Banner */}
      <div className="relative z-10 w-full mb-space-lg bg-surface-container border-l-4 border-secondary p-space-sm flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-secondary">
          <span className="material-symbols-outlined text-[16px]">gavel</span>
          <span className="font-label-mono text-body-sm font-semibold tracking-wide uppercase">
            DEMONSTRATION DIRECTIVE:
          </span>
          <span className="font-label-mono text-body-sm text-on-surface uppercase">
            SYNTHETIC DATA PIPELINE — NO RECORDED ADDRESS, TXID, OR ENTITY MAPS TO REAL CITIZEN/CORPORATE RESERVES.
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0 font-label-mono text-[10px] text-outline uppercase">
          <span>SECURITY ENCLAVE // LEVEL 4</span>
        </div>
      </div>

      {/* Metrics Ledger Overview (5 Rectilinear Columns) */}
      <div className="relative z-10 w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-px bg-primary/20 mb-space-xl">
        {/* Stat 1 */}
        <div className="bg-surface p-space-md flex flex-col justify-between hover:bg-surface-container-lowest transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="font-label-caps text-label-caps text-outline uppercase tracking-widest">
              ACTIVE CASES
            </span>
            <span className="px-1.5 py-0.5 bg-secondary text-surface font-label-mono text-[9px] uppercase font-bold">
              3 CRITICAL
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-data-metric text-data-metric text-primary">14</span>
            <span className="font-label-mono text-body-sm text-outline">/ 20 FIU CAP</span>
          </div>
          <div className="mt-space-sm pt-2 border-t border-outline-variant flex items-center justify-between text-on-surface-variant font-body-sm">
            <span>Priority Load</span>
            <span className="font-label-mono font-medium text-secondary">High Velocity</span>
          </div>
        </div>

        {/* Stat 2 */}
        <div className="bg-surface p-space-md flex flex-col justify-between hover:bg-surface-container-lowest transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="font-label-caps text-label-caps text-outline uppercase tracking-widest">
              ACTIVE TRACES
            </span>
            <span className="px-1.5 py-0.5 bg-primary-container text-surface font-label-mono text-[9px] uppercase">
              12 RUNNING
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-data-metric text-data-metric text-primary">28</span>
            <span className="font-label-mono text-body-sm text-outline">16 TERMINATED</span>
          </div>
          <div className="mt-space-sm pt-2 border-t border-outline-variant flex items-center justify-between text-on-surface-variant font-body-sm">
            <span>Algorithmic Hop Rate</span>
            <span className="font-label-mono font-medium">9.4 hops/sec</span>
          </div>
        </div>

        {/* Stat 3 */}
        <div className="bg-surface p-space-md flex flex-col justify-between hover:bg-surface-container-lowest transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="font-label-caps text-label-caps text-outline uppercase tracking-widest">
              ATTRIBUTED VASPs
            </span>
            <span className="px-1.5 py-0.5 bg-surface-container text-primary font-label-mono text-[9px] uppercase font-semibold">
              94.2% ACC
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-data-metric text-data-metric text-primary">42</span>
            <span className="font-label-mono text-body-sm text-outline">CLUSTER KEYS</span>
          </div>
          <div className="mt-space-sm pt-2 border-t border-outline-variant flex items-center justify-between text-on-surface-variant font-body-sm">
            <span>High Confidence Class</span>
            <span className="font-label-mono font-medium text-primary">Grade A1</span>
          </div>
        </div>

        {/* Stat 4 */}
        <div className="bg-surface p-space-md flex flex-col justify-between hover:bg-surface-container-lowest transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="font-label-caps text-label-caps text-secondary uppercase tracking-widest font-semibold">
              HIGH-RISK ALERTS
            </span>
            <span className="w-2 h-2 rounded-none bg-secondary"></span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-data-metric text-data-metric text-secondary">06</span>
            <span className="font-label-mono text-body-sm text-outline">TRANSIT &gt; 70</span>
          </div>
          <div className="mt-space-sm pt-2 border-t border-outline-variant flex items-center justify-between text-on-surface-variant font-body-sm">
            <span>Peel / Tumbler Detection</span>
            <span className="font-label-mono font-medium text-secondary">Active Warning</span>
          </div>
        </div>

        {/* Stat 5 */}
        <div className="bg-surface p-space-md flex flex-col justify-between hover:bg-surface-container-lowest transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="font-label-caps text-label-caps text-outline uppercase tracking-widest">
              SAHYOG REQUESTS
            </span>
            <span className="px-1.5 py-0.5 bg-tertiary-container text-surface font-label-mono text-[9px] uppercase">
              1 PENDING SUP
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-data-metric text-data-metric text-primary">03</span>
            <span className="font-label-mono text-body-sm text-outline">LEGAL DISPATCH</span>
          </div>
          <div className="mt-space-sm pt-2 border-t border-outline-variant flex items-center justify-between text-on-surface-variant font-body-sm">
            <span>Inter-Agency Gateway</span>
            <button
              onClick={() => onOpenSahyog()}
              className="font-label-mono font-medium text-secondary hover:underline cursor-pointer"
            >
              Secured Sync →
            </button>
          </div>
        </div>
      </div>

      {/* Quick Trace Execution Workbench Launcher */}
      <div className="relative z-10 w-full mb-space-xl bg-surface border border-primary/20 shadow-sm">
        {/* Section Header Band */}
        <div className="bg-surface-container px-space-md py-space-sm border-b border-primary/20 flex flex-col md:flex-row md:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[20px] text-primary">terminal</span>
            <h2 className="font-headline-sm text-headline-sm font-semibold text-primary uppercase tracking-wider">
              EXECUTE QUICK TRACE // WORKBENCH LAUNCHER
            </h2>
          </div>
          <div className="flex items-center gap-2 font-label-mono text-body-sm text-outline">
            <span className="w-2 h-2 rounded-full bg-secondary-container animate-pulse"></span>
            <span>ENGINE STATUS: READY (RPC MESH v4)</span>
          </div>
        </div>

        <div className="p-space-md md:p-space-lg">
          {/* Input Form Layout (4 Columns) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md items-end">
            {/* Input 1: Target Wallet Address */}
            <div className="lg:col-span-5 flex flex-col gap-1.5">
              <div className="flex justify-between items-center">
                <label className="font-label-caps text-label-caps uppercase text-primary font-semibold tracking-wider">
                  TARGET IDENTIFIER / ON-CHAIN WALLET (0x... OR TRON T...)
                </label>
                <span className="font-label-mono text-[10px] text-outline">AUTO-SANITY VERIFIED</span>
              </div>
              <div className="relative">
                <input
                  className="w-full bg-surface-container-lowest text-primary font-label-mono text-body-md px-3.5 py-2.5 border border-primary/40 focus:border-primary focus:outline-none transition-colors"
                  placeholder="ENTER EVM ADDRESS (0X...) OR TRON PUBLIC HASH (T...)"
                  type="text"
                  value={walletInput}
                  onChange={(e) => setWalletInput(e.target.value)}
                />
                {walletInput && (
                  <button
                    onClick={() => setWalletInput("")}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-outline hover:text-primary"
                    title="Clear Field"
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[16px]">backspace</span>
                  </button>
                )}
              </div>
            </div>

            {/* Input 2: Blockchain Selector */}
            <div className="lg:col-span-3 flex flex-col gap-1.5">
              <label className="font-label-caps text-label-caps uppercase text-primary font-semibold tracking-wider">
                LEDGER SUBSURFACE NETWORK
              </label>
              <div className="relative">
                <select
                  className="w-full bg-surface-container-lowest text-primary font-label-mono text-body-md px-3.5 py-2.5 border border-primary/40 focus:border-primary focus:outline-none appearance-none cursor-pointer"
                  value={selectedChain}
                  onChange={(e) => setSelectedChain(e.target.value)}
                >
                  <option value="eth">Ethereum Mainnet (ID: 01)</option>
                  <option value="bnb">BNB Smart Chain (ID: 56)</option>
                  <option value="polygon">Polygon PoS (ID: 137)</option>
                  <option value="tron">TRON Network (TRC20)</option>
                </select>
                <span className="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-outline text-[18px]">
                  unfold_more
                </span>
              </div>
            </div>

            {/* Input 3: Hop Depth */}
            <div className="lg:col-span-2 flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label className="font-label-caps text-label-caps uppercase text-primary font-semibold tracking-wider">
                  HOP DEPTH
                </label>
                <span className="font-label-mono text-[9px] text-secondary font-semibold">MAX DEPTH 5</span>
              </div>
              <select
                className="w-full bg-surface-container-lowest text-primary font-label-mono text-body-md px-3.5 py-2.5 border border-primary/40 focus:border-primary focus:outline-none appearance-none cursor-pointer"
                value={selectedHopDepth}
                onChange={(e) => setSelectedHopDepth(Number(e.target.value))}
              >
                <option value={1}>1 Hop (Direct Neighbours)</option>
                <option value={2}>2 Hops (Intermediaries)</option>
                <option value={3}>3 Hops (Standard Recon)</option>
                <option value={4}>4 Hops (Extended Perimeter)</option>
                <option value={5}>5 Hops (Deep Forensics)</option>
              </select>
            </div>

            {/* Action Button */}
            <div className="lg:col-span-2">
              <button
                onClick={handleRunTrace}
                className="w-full bg-secondary hover:bg-primary text-surface font-label-caps text-label-caps tracking-widest uppercase font-semibold py-3 px-4 flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-sm"
                type="button"
              >
                <span className="material-symbols-outlined text-[16px]">radar</span>
                <span>RUN TRACE</span>
              </button>
            </div>
          </div>

          {/* Warning Subtext */}
          <div className="mt-space-sm flex items-center gap-2 text-secondary font-label-mono text-body-sm">
            <span className="material-symbols-outlined text-[14px]">warning</span>
            <span>Depth &gt; 3 may exponentially expand trace graph density, activating peel-chain heuristic pruning.</span>
          </div>

          {/* Pre-Loaded Dossier Presets */}
          <div className="mt-space-md pt-space-md border-t border-primary/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-space-sm">
            <span className="font-label-caps text-label-caps uppercase text-outline font-semibold tracking-widest">
              SYNTHETIC BENCHMARK PRESETS:
            </span>
            <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
              <button
                className="px-2.5 py-1.5 bg-surface-container hover:bg-primary hover:text-surface text-primary border border-primary/30 font-label-mono text-body-sm flex items-center gap-1.5 transition-colors cursor-pointer"
                onClick={() => loadPreset("0x71C836e1471d497672288079633eA940026e89A2", "eth", 3)}
                type="button"
              >
                <span className="material-symbols-outlined text-[14px]">bookmark</span>
                <span>CASE 02: Short Path vs Volume</span>
                <span className="font-label-caps text-[9px] text-secondary font-bold ml-1">[LOAD]</span>
              </button>
              <button
                className="px-2.5 py-1.5 bg-surface-container hover:bg-primary hover:text-surface text-primary border border-primary/30 font-label-mono text-body-sm flex items-center gap-1.5 transition-colors cursor-pointer"
                onClick={() => loadPreset("0x88f21922c019d44e54880921bbfe4889c01991c0", "eth", 4)}
                type="button"
              >
                <span className="material-symbols-outlined text-[14px]">bookmark</span>
                <span>CASE 04: Peel Chain / Mixer</span>
                <span className="font-label-caps text-[9px] text-secondary font-bold ml-1">[LOAD]</span>
              </button>
              <button
                className="px-2.5 py-1.5 bg-surface-container hover:bg-primary hover:text-surface text-primary border border-primary/30 font-label-mono text-body-sm flex items-center gap-1.5 transition-colors cursor-pointer"
                onClick={() => loadPreset("0x90e44b91010b99182334ccfe771891bcaaff2281", "polygon", 3)}
                type="button"
              >
                <span className="material-symbols-outlined text-[14px]">bookmark</span>
                <span>CASE 05: Cross-Chain Bridge</span>
                <span className="font-label-caps text-[9px] text-secondary font-bold ml-1">[LOAD]</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Master Evidentiary Ledger / Recent Investigations */}
      <div className="relative z-10 w-full mb-space-xl">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-space-sm gap-2">
          <div>
            <span className="font-label-caps text-label-caps text-outline uppercase tracking-widest block font-semibold">
              REGISTRY FOLIO // SECTION 05
            </span>
            <h2 className="font-headline-md text-headline-md font-semibold text-primary tracking-tight">
              RECENT INVESTIGATION DOSSIERS
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center border border-primary/30 bg-surface px-2 py-1">
              <span className="material-symbols-outlined text-[16px] text-outline mr-1">filter_list</span>
              <button
                type="button"
                onClick={() =>
                  setStatusFilter(statusFilter === "ALL" ? "HIGH_RISK" : statusFilter === "HIGH_RISK" ? "COMPLETED" : "ALL")
                }
                className="font-label-mono text-body-sm uppercase text-primary cursor-pointer hover:underline"
              >
                FILTER: {statusFilter === "ALL" ? "ALL REGISTERS" : statusFilter === "HIGH_RISK" ? "HIGH RISK ONLY" : "COMPLETED ONLY"}
              </button>
            </div>
            <button
              onClick={() => {
                alert("Exporting Case Dossier CSV signed with SHA-256 Merkle anchor.");
              }}
              className="px-2.5 py-1 border border-primary/30 text-primary hover:bg-primary hover:text-surface font-label-mono text-body-sm uppercase transition-colors cursor-pointer"
              type="button"
            >
              EXPORT CSV
            </button>
          </div>
        </div>

        {/* Tabular Registry */}
        <div className="w-full border border-primary/30 overflow-x-auto bg-surface shadow-sm">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container border-b border-primary/30 text-on-surface font-label-caps text-label-caps tracking-widest uppercase">
                <th className="py-3 px-4 font-semibold">CASE REF</th>
                <th className="py-3 px-4 font-semibold">TARGET ADDRESS</th>
                <th className="py-3 px-4 font-semibold">CHAIN</th>
                <th className="py-3 px-4 font-semibold">STATUS</th>
                <th className="py-3 px-4 font-semibold">TOP VASP CANDIDATE</th>
                <th className="py-3 px-4 font-semibold">ATTRIB SCORE</th>
                <th className="py-3 px-4 font-semibold">TRANSIT RISK</th>
                <th className="py-3 px-4 font-semibold">UPDATED</th>
                <th className="py-3 px-4 font-semibold text-right">FORENSIC DISPATCH</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-primary/10 font-body-md">
              {filteredCases.map((item) => (
                <tr key={item.ref} className="hover:bg-surface-container-low transition-colors group">
                  <td className="py-3 px-4 font-label-mono text-body-sm font-semibold text-primary">
                    {item.ref}
                  </td>
                  <td className="py-3 px-4 font-label-mono text-body-sm text-on-surface">
                    <span className="bg-surface-container px-1.5 py-0.5 border border-primary/20">
                      {item.targetAddress}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-1.5 py-0.5 border border-primary/40 font-label-mono text-[10px] uppercase font-bold">
                      {item.chain}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 bg-primary text-surface font-label-caps text-label-caps uppercase font-bold">
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="font-medium text-primary flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px] text-secondary">verified</span>
                      <span className="font-bold">{item.topVasp}</span>
                      <span className="text-outline text-body-sm font-normal">{item.vaspSub}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-label-mono">
                    <span className="font-bold text-primary">{item.score}</span>
                    <span className="text-[10px] text-outline font-semibold ml-1">({item.scoreGrade})</span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-label-mono font-bold ${
                          item.transitRisk >= 70 ? "text-secondary" : "text-primary"
                        }`}
                      >
                        {item.transitRisk}
                      </span>
                      <span
                        className={`px-1 text-[9px] font-label-mono uppercase font-bold ${
                          item.transitRisk >= 70
                            ? "bg-secondary/10 text-secondary"
                            : "bg-surface-container text-outline"
                        }`}
                      >
                        {item.riskLevel}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-label-mono text-body-sm text-outline">
                    {item.updated}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() =>
                          onOpenWorkbench({
                            address: item.fullAddress,
                            chain: item.chain.toLowerCase(),
                            hopDepth: item.hopDepth,
                            caseRef: item.ref,
                          })
                        }
                        className="px-2.5 py-1 bg-primary text-surface hover:bg-secondary font-label-mono text-[10px] uppercase font-bold transition-colors cursor-pointer shadow-sm"
                        type="button"
                      >
                        WORKBENCH
                      </button>
                      <button
                        onClick={() => onOpenSahyog(item.ref)}
                        className="px-2.5 py-1 border border-primary text-primary hover:bg-primary hover:text-surface font-label-mono text-[10px] uppercase transition-colors cursor-pointer"
                        type="button"
                      >
                        SAHYOG
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
