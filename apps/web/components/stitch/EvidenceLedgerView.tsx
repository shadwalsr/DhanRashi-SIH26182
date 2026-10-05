"use client";

import React, { useState } from "react";

export default function EvidenceLedgerView() {
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifiedStatus, setVerifiedStatus] = useState<boolean | null>(true);

  const evidenceItems = [
    {
      id: "EVD-001",
      filename: "01_PRIMARY_HEURISTIC_TRACE.PDF",
      type: "Algorithmic Trace Dossier",
      sha256: "d8e1920b784a091c4912984bca1189ac021984218a09bcde4918230198421984",
      size: "2.4 MB",
      timestamp: "2026-10-05 14:12:08 UTC",
      verified: true,
      caseRef: "CASE-02",
    },
    {
      id: "EVD-002",
      filename: "02_RAW_RPC_RECEIPTS_ETH_MAINNET.JSON",
      type: "RPC Raw Transaction Receipts",
      sha256: "9b248a0112fc7890123456789abcdef0123456789abcdef0123456789abcdef0",
      size: "18.6 MB",
      timestamp: "2026-10-05 14:12:12 UTC",
      verified: true,
      caseRef: "CASE-02",
    },
    {
      id: "EVD-003",
      filename: "03_MULTI_HOP_FLOW_GRAPH_SNAPSHOT.PNG",
      type: "Vector Forensics Graph Render",
      sha256: "77a0bcde88ec0192837465019283746501928374650192837465019283746501",
      size: "4.1 MB",
      timestamp: "2026-10-05 14:12:15 UTC",
      verified: true,
      caseRef: "CASE-02",
    },
    {
      id: "EVD-004",
      filename: "04_INVESTIGATOR_AUDIT_LOG_SIG.BIN",
      type: "Ed25519 PKCS#11 Signature",
      sha256: "e8a9f001b401cdef0123456789abcdef0123456789abcdef0123456789abcdef",
      size: "512 B",
      timestamp: "2026-10-05 14:12:20 UTC",
      verified: true,
      caseRef: "CASE-02",
    },
    {
      id: "EVD-005",
      filename: "05_VASP_ALPHA_HOTWALLET_REGISTRY.CSV",
      type: "Cluster Ownership Record",
      sha256: "c31498e299102938475610293847561029384756102938475610293847561029",
      size: "142 KB",
      timestamp: "2026-10-05 14:12:24 UTC",
      verified: true,
      caseRef: "CASE-02",
    },
    {
      id: "EVD-006",
      filename: "06_CRPC_SEC91_REQUISITION_ORDER.DOC",
      type: "Statutory Lawful Notice",
      sha256: "f1982077ba019283746501928374650192837465019283746501928374650192",
      size: "340 KB",
      timestamp: "2026-10-05 14:12:30 UTC",
      verified: true,
      caseRef: "CASE-02",
    },
  ];

  const handleVerifyMerkle = () => {
    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      setVerifiedStatus(true);
      alert("Cryptographic Proof Valid: Merkle root matches 0x93FA...CE88. Zero hash divergence detected across all 6 records.");
    }, 800);
  };

  return (
    <div className="flex flex-col w-full space-y-space-md">
      {/* HEADER */}
      <div className="bg-surface-container-low p-gutter border border-primary/20 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md">
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
              PROVENANCE & INTEGRITY // SECTION 05
            </span>
            <h1 className="font-headline-lg text-headline-lg font-serif font-bold text-primary tracking-tight">
              EVIDENCE LEDGER & MERKLE ANCHOR
            </h1>
            <p className="font-body-md text-on-surface-variant max-w-2xl">
              Cryptographically sealed evidentiary packages, raw RPC proof receipts, and dual-state Merkle tree verification complying with judicial admissibility standards.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleVerifyMerkle}
              disabled={isVerifying}
              className="px-4 py-2.5 bg-secondary text-on-secondary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-primary transition-colors flex items-center gap-2 shadow-sm cursor-pointer disabled:opacity-70"
            >
              <span className={`material-symbols-outlined text-[16px] ${isVerifying ? "animate-spin" : ""}`}>
                verified
              </span>
              <span>{isVerifying ? "VERIFYING MERKLE ROOT..." : "VERIFY MERKLE ROOT"}</span>
            </button>
            <button
              onClick={() => alert("Downloading SHA-256 sealed ZIP containing all 6 evidence dockets and certificate.")}
              className="px-4 py-2.5 border border-primary text-primary hover:bg-primary hover:text-surface font-label-caps text-label-caps uppercase font-bold tracking-wider transition-colors flex items-center gap-2 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">download</span>
              <span>DOWNLOAD DOCKET (.ZIP)</span>
            </button>
          </div>
        </div>
      </div>

      {/* MERKLE ROOT STAT CARD */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md font-label-mono text-body-sm">
        <div className="bg-primary text-on-primary p-space-md flex flex-col justify-between shadow-sm">
          <span className="text-[10px] text-primary-fixed uppercase tracking-wider font-semibold">
            MERKLE ROOT ANCHOR
          </span>
          <div className="text-body-lg font-bold text-surface-bright mt-1 select-all truncate">
            0x93FA68B012CD...CE88
          </div>
          <div className="mt-2 text-[10px] text-primary-fixed-dim">
            Algorithmic Digest: Dual SHA-256 (Ed25519 Signed)
          </div>
        </div>

        <div className="bg-surface-container p-space-md border border-primary/20 flex flex-col justify-between">
          <span className="text-[10px] text-outline uppercase tracking-wider font-semibold">
            CHAIN OF CUSTODY INTEGRITY
          </span>
          <div className="text-headline-sm font-serif font-bold text-secondary mt-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-[20px]">security</span>
            <span>100.0% ADMISSIBLE</span>
          </div>
          <div className="mt-2 text-[10px] text-on-surface-variant">
            Section 65B Indian Evidence Act Conformance
          </div>
        </div>

        <div className="bg-surface-container p-space-md border border-primary/20 flex flex-col justify-between">
          <span className="text-[10px] text-outline uppercase tracking-wider font-semibold">
            ATTACHED ARTIFACTS
          </span>
          <div className="text-headline-sm font-serif font-bold text-primary mt-1">
            6 VERIFIED DOCKETS
          </div>
          <div className="mt-2 text-[10px] text-on-surface-variant">
            Timestamped on-chain block height: 21,084,912
          </div>
        </div>
      </div>

      {/* EVIDENCE TABLE */}
      <div className="border border-primary/20 bg-surface shadow-sm overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container border-b border-primary/20 font-label-caps text-label-caps uppercase text-on-surface tracking-wider">
              <th className="py-3 px-4">Artifact ID</th>
              <th className="py-3 px-4">Docket File Name</th>
              <th className="py-3 px-4">Classification</th>
              <th className="py-3 px-4">SHA-256 Digest</th>
              <th className="py-3 px-4">Size</th>
              <th className="py-3 px-4">Timestamp (UTC)</th>
              <th className="py-3 px-4 text-right">Integrity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-primary/10 font-body-md">
            {evidenceItems.map((e) => (
              <tr key={e.id} className="hover:bg-surface-container-low transition-colors">
                <td className="py-3 px-4 font-label-mono text-body-sm font-bold text-primary">
                  {e.id}
                </td>
                <td className="py-3 px-4">
                  <div className="font-bold text-primary flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-secondary">description</span>
                    <span>{e.filename}</span>
                  </div>
                  <div className="font-label-mono text-body-sm text-on-surface-variant">{e.caseRef}</div>
                </td>
                <td className="py-3 px-4 font-label-mono text-body-sm text-on-surface">
                  {e.type}
                </td>
                <td className="py-3 px-4 font-label-mono text-body-sm text-primary select-all">
                  <span className="bg-surface-container px-1 py-0.5 border border-primary/20">
                    {e.sha256.substring(0, 16)}...{e.sha256.substring(e.sha256.length - 8)}
                  </span>
                </td>
                <td className="py-3 px-4 font-label-mono text-body-sm text-on-surface-variant">
                  {e.size}
                </td>
                <td className="py-3 px-4 font-label-mono text-body-sm text-on-surface-variant">
                  {e.timestamp}
                </td>
                <td className="py-3 px-4 text-right">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary text-on-primary font-label-mono text-[10px] uppercase font-bold">
                    <span className="material-symbols-outlined text-[12px]">verified</span>
                    <span>PASS</span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
