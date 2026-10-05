"use client";

import React, { useState } from "react";

export default function ReportsVerificationView() {
  const [selectedCase, setSelectedCase] = useState("CASE-02");
  const [reportFormat, setReportFormat] = useState("PDF_OFFICIAL");
  const [generating, setGenerating] = useState(false);

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      alert(`Report generated: DHANRASHI_${selectedCase}_FORENSIC_DOCKET.PDF signed with Ed25519-Gov key and anchored in Merkle tree.`);
    }, 900);
  };

  return (
    <div className="flex flex-col w-full space-y-space-md">
      {/* HEADER */}
      <div className="bg-surface-container-low p-gutter border border-primary/20 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md">
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
              JUDICIAL EVIDENCE COMPILATION // SECTION 06
            </span>
            <h1 className="font-headline-lg text-headline-lg font-serif font-bold text-primary tracking-tight">
              REPORTS & SOVEREIGN VERIFICATION
            </h1>
            <p className="font-body-md text-on-surface-variant max-w-2xl">
              Compile court-admissible forensic dockets with Section 65B Indian Evidence Act certificates, complete multi-hop path visualizations, and mathematical polynomial proofs.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">
        {/* REPORT GENERATOR PANEL */}
        <div className="lg:col-span-6 bg-surface border border-primary/20 p-space-md shadow-sm space-y-space-md">
          <div className="flex items-center gap-2 border-b border-primary/10 pb-2">
            <span className="material-symbols-outlined text-secondary text-[22px]">assignment</span>
            <h2 className="font-headline-sm text-headline-sm font-serif font-bold text-primary">
              Generate Admissible Case Report
            </h2>
          </div>

          <form onSubmit={handleGenerate} className="space-y-4 font-body-md">
            <div>
              <label className="block font-label-caps text-label-caps uppercase text-primary font-bold mb-1">
                SELECT INVESTIGATION DOSSIER
              </label>
              <select
                value={selectedCase}
                onChange={(e) => setSelectedCase(e.target.value)}
                className="w-full bg-surface-container-lowest font-label-mono text-body-md px-3 py-2 border border-primary/40 focus:border-primary focus:outline-none"
              >
                <option value="CASE-02">CASE-02: Shorter Path vs. Larger Flow Discrepancy (Flagship)</option>
                <option value="CASE-01">CASE-01: Direct Exchange Deposit & Clean Sweep</option>
                <option value="CASE-04">CASE-04: Peel-Chain Mixer Wash & Bridge Hop</option>
                <option value="CASE-05">CASE-05: Cross-Chain Bridge Liquidity Jump</option>
                <option value="CASE-03">CASE-03: Multi-Inflow TRON Layering</option>
              </select>
            </div>

            <div>
              <label className="block font-label-caps text-label-caps uppercase text-primary font-bold mb-1">
                REPORT CLASSIFICATION / MANDATE
              </label>
              <select
                value={reportFormat}
                onChange={(e) => setReportFormat(e.target.value)}
                className="w-full bg-surface-container-lowest font-label-mono text-body-md px-3 py-2 border border-primary/40 focus:border-primary focus:outline-none"
              >
                <option value="PDF_OFFICIAL">Judicial Formal Docket (PDF) with Section 65B Certificate</option>
                <option value="EXECUTIVE_SUMMARY">Executive Intelligence Briefing (PDF)</option>
                <option value="RAW_EVIDENCE_ZIP">Complete Raw RPC & Evidence Bundle (.ZIP)</option>
              </select>
            </div>

            <div className="space-y-2 border-t border-primary/10 pt-2 font-label-mono text-body-sm">
              <span className="font-label-caps text-label-caps uppercase text-primary font-bold block mb-1">
                ATTACHED PROOF DOCKETS INCLUDED:
              </span>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" defaultChecked className="accent-secondary" />
                <span>Multi-Hop Flow Vector Graph with Divergence Analysis</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" defaultChecked className="accent-secondary" />
                <span>10-Factor ATT-v1.0 Polynomial Breakdown Table</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" defaultChecked className="accent-secondary" />
                <span>Raw On-Chain Transaction Hashes & RPC Receipts</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" defaultChecked className="accent-secondary" />
                <span>Ed25519 Cryptographic Signature of Lead Investigator</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={generating}
              className="w-full py-3 bg-secondary hover:bg-primary text-on-secondary font-label-caps text-label-caps uppercase font-bold tracking-widest transition-colors flex items-center justify-center gap-2 shadow-md cursor-pointer disabled:opacity-70"
            >
              <span className={`material-symbols-outlined text-[18px] ${generating ? "animate-spin" : ""}`}>
                print
              </span>
              <span>{generating ? "COMPILING DOCKET..." : "COMPILE JUDICIAL DOSSIER"}</span>
            </button>
          </form>
        </div>

        {/* VERIFICATION VALIDATOR PANEL */}
        <div className="lg:col-span-6 bg-surface border border-primary/20 p-space-md shadow-sm space-y-space-md">
          <div className="flex items-center gap-2 border-b border-primary/10 pb-2">
            <span className="material-symbols-outlined text-secondary text-[22px]">verified_user</span>
            <h2 className="font-headline-sm text-headline-sm font-serif font-bold text-primary">
              Verify Third-Party Evidence File
            </h2>
          </div>

          <p className="font-body-md text-on-surface-variant">
            Upload or paste any DHANRASHI exported docket, PDF report, or SHA-256 hash to cryptographically verify authenticity against the on-chain Merkle root anchor.
          </p>

          <div className="border-2 border-dashed border-primary/30 p-space-lg text-center bg-surface-container-lowest cursor-pointer hover:bg-surface-container transition-colors">
            <span className="material-symbols-outlined text-primary text-[36px]">upload_file</span>
            <div className="font-label-caps text-label-caps uppercase font-bold text-primary mt-2">
              DRAG & DROP EVIDENCE DOCKET OR CLICK TO BROWSE
            </div>
            <div className="font-label-mono text-body-sm text-outline mt-1">
              Supports .PDF, .JSON, .ZIP, .BIN files
            </div>
          </div>

          <div className="p-3 bg-surface-container border border-primary/20 font-label-mono text-body-sm space-y-1">
            <div className="text-primary font-bold">LATEST VERIFIED RECORD:</div>
            <div className="text-secondary font-bold select-all">01_PRIMARY_HEURISTIC_TRACE.PDF</div>
            <div className="text-[11px] text-on-surface-variant truncate">
              Merkle Root: 0x93FA68B012CD...CE88 (MATCH CONFIRMED)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
