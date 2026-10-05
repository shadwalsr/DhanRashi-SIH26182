"use client";

import React, { useState } from "react";

interface SahyogPortalProps {
  currentRole: "analyst" | "supervisor";
  onRoleSwitch?: (role: "analyst" | "supervisor") => void;
}

export default function SahyogPortal({
  currentRole,
  onRoleSwitch,
}: SahyogPortalProps) {
  const [selectedReqId, setSelectedReqId] = useState<string>("41");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "PENDING" | "VERIFIED">("ALL");
  const [showNewModal, setShowNewModal] = useState<boolean>(false);
  const [signedState, setSignedState] = useState<Record<string, boolean>>({});

  // New Request Form State
  const [newCaseRef, setNewCaseRef] = useState("CASE-02");
  const [newVasp, setNewVasp] = useState("VASP ALPHA");
  const [newOrderType, setNewOrderType] = useState("EMERGENCY FREEZE & KYC");
  const [newTargetWallet, setNewTargetWallet] = useState("0x71C836e1471d497672288079633eA940026e89A2");
  const [newMandate, setNewMandate] = useState("Section 91 CrPC (Criminal Procedure Code)");

  const requests = [
    {
      id: "41",
      reqNum: "SYG-2026-0041",
      caseRef: "CASE-02 (Short Path)",
      vasp: "VASP ALPHA",
      vaspNode: "Registered Node IND",
      scope: "EMERGENCY FREEZE & KYC",
      mandate: "CrPC Sec. 91 Warrant",
      report: "REP-2026-02-V1",
      sha: "e8a9...b401",
      status: "PENDING SUPERVISOR",
      officer: "Insp. V. Sharma",
      isPending: true,
      risk: 72,
      flowShare: "88.0%",
      score: "87.4/100",
      targetWallet: "0x71C8366420A8...89A2",
      cluster: "#VASP-ALP-09 (Hot-Wallet Sweeper)",
    },
    {
      id: "39",
      reqNum: "SYG-2026-0039",
      caseRef: "CASE-01 (Clean Deposit)",
      vasp: "VASP KAPPA",
      vaspNode: "FIU Certified VASP",
      scope: "KYC IDENTITY DISCLOSURE",
      mandate: "IT Act Sec. 69 Order",
      report: "REP-2026-01-FINAL",
      sha: "3b71...cc92",
      status: "ACKNOWLEDGED VASP",
      officer: "DySP R. Verma",
      isPending: false,
      risk: 18,
      flowShare: "94.1%",
      score: "94.1/100",
      targetWallet: "0x3d9129aa48bfe028198f480018b84102919323c1",
      cluster: "#VASP-KAP-01 (Direct Deposit Ledger)",
    },
    {
      id: "38",
      reqNum: "SYG-2026-0038",
      caseRef: "CASE-04 (Peel Chain Mixer)",
      vasp: "VASP DELTA",
      vaspNode: "Foreign Jurisdiction Node",
      scope: "ASSET TRACE & HOLD",
      mandate: "Cross-Border Directive",
      report: "REP-2026-04-V2",
      sha: "9a11...02fc",
      status: "REJECTED (EVIDENCE)",
      officer: "Insp. V. Sharma",
      isPending: false,
      risk: 86,
      flowShare: "64.8%",
      score: "64.8/100",
      targetWallet: "0x88f21922c019d44e54880921bbfe4889c01991c0",
      cluster: "#VASP-DEL-04 (Transit Mixer Sink)",
    },
  ];

  const activeReq = requests.find((r) => r.id === selectedReqId) || requests[0];
  const isReqSigned = signedState[activeReq.id] || false;

  const handleSign = () => {
    if (currentRole !== "supervisor") {
      alert("Separation of Duties Violation: Insp. V. Sharma (Author) cannot authorize legal dispatch under Rule 7(a). Please switch role to SUPERVISOR in the top right bar.");
      return;
    }
    setSignedState((prev) => ({ ...prev, [activeReq.id]: true }));
    alert(`Success: Request ${activeReq.reqNum} has been cryptographically signed with Ed25519-Gov key and queued to VASP ${activeReq.vasp} peer node.`);
  };

  const handleCreateRequest = (e: React.FormEvent) => {
    e.preventDefault();
    setShowNewModal(false);
    alert(`New SAHYOG request created for ${newCaseRef} targeting ${newVasp}. Status set to DRAFT.`);
  };

  return (
    <div className="flex flex-col w-full">
      {/* REGULATORY SOVEREIGN BANNER */}
      <div className="w-full bg-secondary-container text-on-secondary-container px-gutter py-2 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-space-sm">
          <span className="material-symbols-outlined text-[18px]">gavel</span>
          <span className="font-label-caps text-label-caps uppercase tracking-widest font-semibold">
            MOCK — NOT TRANSMITTED TO ANY AUTHORITY | DEMONSTRATION OF INTER-AGENCY COOPERATION FRAMEWORK
          </span>
        </div>
        <div className="hidden md:flex items-center gap-space-md">
          <span className="font-label-mono text-body-sm uppercase tracking-wider">
            PIPELINE VERIFICATION: ACTIVE // STRICT CONFORMANCE
          </span>
          <span className="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
        </div>
      </div>

      {/* EDITORIAL MASTHEAD & PRIMARY ACTIONS */}
      <div className="w-full bg-surface-container-low p-gutter shadow-sm mt-space-sm border border-primary/20">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-space-md">
          <div className="max-w-4xl space-y-space-xs">
            <div className="flex items-center gap-space-sm">
              <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
                SECTION 91 CrPC // SECTION 69 IT ACT
              </span>
              <span className="text-outline-variant font-label-mono text-body-sm">|</span>
              <span className="font-label-mono text-body-sm text-on-surface-variant uppercase">
                REGULATION-REF // 2026-DHANRASHI-LEAD
              </span>
            </div>
            <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight font-serif font-bold">
              SAHYOG PORTAL // LAW ENFORCEMENT & VASP DATA DISPATCH
            </h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-3xl">
              Formal request generation and cryptographic chain dispatch for cryptocurrency transaction freeze, custodial account isolation, and mandatory KYC disclosure.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-space-sm shrink-0">
            <button
              onClick={() => setShowNewModal(true)}
              className="px-space-md py-2.5 bg-secondary text-on-secondary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-primary transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
              id="btnNewRequest"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">add_task</span>
              <span>+ NEW SAHYOG REQUEST</span>
            </button>
            <button
              onClick={() => alert("Audit trail verified: All dispatched requests anchored in Merkle tree with zero tampering.")}
              className="px-space-md py-2.5 bg-surface-container-highest text-primary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-primary-container hover:text-on-primary transition-colors flex items-center gap-1.5 shadow-sm border border-primary/20 cursor-pointer"
              id="btnVerifyAudit"
              type="button"
            >
              <span className="material-symbols-outlined text-[16px]">verified</span>
              <span>VERIFY SHA-256 AUDIT TRAIL</span>
            </button>
          </div>
        </div>
      </div>

      {/* WORKFLOW LIFECYCLE & SEPARATION OF DUTIES STRIP */}
      <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-space-md mt-space-md">
        {/* LIFECYCLE STAGES */}
        <div className="lg:col-span-8 bg-surface-container-lowest p-space-md shadow-sm flex flex-col justify-between border border-primary/20">
          <div className="flex items-center justify-between pb-space-sm border-b border-primary/10">
            <span className="font-label-caps text-label-caps text-primary uppercase tracking-widest font-bold flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px]">linear_scale</span>
              WORKFLOW DISPATCH PIPELINE (SOVEREIGN CHAIN OF CUSTODY)
            </span>
            <span className="font-label-mono text-body-sm text-on-surface-variant font-bold">
              {isReqSigned ? "STAGE 04 / 05 SUBMITTED" : "STAGE 03 / 05 ACTIVE"}
            </span>
          </div>

          {/* PIPELINE STEPPER */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-space-xs mt-space-sm">
            {/* 01 DRAFT */}
            <div className="bg-surface-container p-space-sm flex flex-col justify-between border-l-2 border-primary">
              <div className="flex items-center justify-between">
                <span className="font-label-mono text-body-sm text-on-surface-variant font-bold">01</span>
                <span className="material-symbols-outlined text-[16px] text-primary">check_circle</span>
              </div>
              <div className="mt-2">
                <div className="font-label-caps text-label-caps uppercase font-bold text-primary">DRAFT</div>
                <div className="font-label-mono text-body-sm text-on-surface-variant truncate">Investigator (Filed)</div>
              </div>
            </div>

            {/* 02 REVIEW */}
            <div className="bg-surface-container p-space-sm flex flex-col justify-between border-l-2 border-primary">
              <div className="flex items-center justify-between">
                <span className="font-label-mono text-body-sm text-on-surface-variant font-bold">02</span>
                <span className="material-symbols-outlined text-[16px] text-primary">check_circle</span>
              </div>
              <div className="mt-2">
                <div className="font-label-caps text-label-caps uppercase font-bold text-primary">REVIEW</div>
                <div className="font-label-mono text-body-sm text-on-surface-variant truncate">Sr. Analyst Passed</div>
              </div>
            </div>

            {/* 03 SUPERVISOR APPROVAL */}
            <div
              className={`p-space-sm flex flex-col justify-between shadow-sm transition-all ${
                isReqSigned
                  ? "bg-surface-container border-l-2 border-primary text-primary"
                  : "bg-secondary text-on-secondary"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-label-mono text-body-sm font-bold">03</span>
                <span className={`material-symbols-outlined text-[16px] ${isReqSigned ? "text-primary" : "text-surface-bright animate-pulse"}`}>
                  {isReqSigned ? "check_circle" : "pending"}
                </span>
              </div>
              <div className="mt-2">
                <div className="font-label-caps text-label-caps uppercase font-bold">SUPERVISOR</div>
                <div className="font-label-mono text-body-sm opacity-90 truncate">
                  {isReqSigned ? "Signed & Sealed" : "Digital Sign-off Req."}
                </div>
              </div>
            </div>

            {/* 04 SUBMITTED */}
            <div
              className={`p-space-sm flex flex-col justify-between ${
                isReqSigned ? "bg-secondary text-on-secondary shadow-sm" : "bg-surface-container-low"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-label-mono text-body-sm font-bold">04</span>
                <span className={`material-symbols-outlined text-[16px] ${isReqSigned ? "animate-pulse" : "text-outline"}`}>
                  {isReqSigned ? "pending" : "radio_button_unchecked"}
                </span>
              </div>
              <div className="mt-2">
                <div className="font-label-caps text-label-caps uppercase font-bold">SUBMITTED</div>
                <div className="font-label-mono text-body-sm opacity-90 truncate">VASP Node Queue</div>
              </div>
            </div>

            {/* 05 ACKNOWLEDGED */}
            <div className="bg-surface-container-low p-space-sm flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="font-label-mono text-body-sm text-outline font-bold">05</span>
                <span className="material-symbols-outlined text-[16px] text-outline">radio_button_unchecked</span>
              </div>
              <div className="mt-2">
                <div className="font-label-caps text-label-caps uppercase font-bold text-on-surface-variant">ACKNOWLEDGED</div>
                <div className="font-label-mono text-body-sm text-outline truncate">Custody Locked</div>
              </div>
            </div>
          </div>
        </div>

        {/* SEPARATION OF DUTIES NOTICE */}
        <div className="lg:col-span-4 bg-tertiary-container text-on-tertiary p-space-md shadow-sm flex flex-col justify-between border border-tertiary">
          <div>
            <div className="flex items-center gap-space-xs text-secondary-fixed">
              <span className="material-symbols-outlined text-[18px]">security</span>
              <span className="font-label-caps text-label-caps uppercase tracking-widest font-bold">
                SEPARATION OF DUTIES MANDATE
              </span>
            </div>
            <p className="font-body-md text-body-md text-surface-container-low mt-space-sm leading-relaxed">
              <strong>Inspector V. Sharma (Author)</strong> cannot authorize legal dispatch directly under Rule 7(a). 
              Requires multi-party cryptographically anchored sign-off from <strong>Superintendent / Authorized Supervisory Officer</strong> before push to VASP peer nodes.
            </p>
          </div>
          <div className="pt-space-sm flex items-center justify-between text-surface-dim font-label-mono text-body-sm border-t border-outline/30 mt-2">
            <span>GATEWAY: FIU-IND-PROV-401</span>
            <span className="bg-tertiary px-2 py-0.5 text-on-tertiary text-label-caps font-bold">
              {currentRole === "supervisor" ? "AUTHORIZATION UNLOCKED" : "LOCKED (ANALYST)"}
            </span>
          </div>
        </div>
      </div>

      {/* MAIN EDITORIAL SPLIT WORKBENCH */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-space-md mt-space-md">
        {/* LEFT 7 COLUMNS: ACTIVE SAHYOG REQUESTS REPOSITORY */}
        <div className="xl:col-span-7 flex flex-col gap-space-md">
          {/* TABLE CARD */}
          <div className="bg-surface-container-lowest shadow-sm flex flex-col border border-primary/20">
            {/* HEADER */}
            <div className="p-space-md bg-surface-container flex items-center justify-between border-b border-primary/20">
              <div>
                <span className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest font-bold">
                  LEDGER INDEX // 08-SAHYOG
                </span>
                <h2 className="font-headline-sm text-headline-sm text-primary font-bold">
                  Active Legal Dispatch Requests
                </h2>
              </div>
              <div className="flex items-center gap-space-xs font-label-mono text-body-sm text-on-surface-variant">
                <span className="w-2 h-2 rounded-full bg-secondary-container"></span>
                <span>3 RECORDED DOSSIERS</span>
              </div>
            </div>

            {/* TABLE FILTERS / CONTROLS */}
            <div className="px-space-md py-space-sm bg-surface-container-low flex flex-wrap items-center justify-between gap-space-sm border-b border-primary/10">
              <div className="flex items-center gap-space-xs font-label-caps text-label-caps">
                <span className="uppercase text-on-surface-variant font-bold">FILTER BY STATUS:</span>
                <button
                  type="button"
                  onClick={() => setStatusFilter("ALL")}
                  className={`px-2 py-1 uppercase font-bold transition-colors cursor-pointer ${
                    statusFilter === "ALL" ? "bg-primary text-on-primary" : "bg-surface-variant text-on-surface hover:bg-surface-dim"
                  }`}
                >
                  ALL (3)
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter("PENDING")}
                  className={`px-2 py-1 uppercase font-bold transition-colors cursor-pointer ${
                    statusFilter === "PENDING" ? "bg-primary text-on-primary" : "bg-surface-variant text-on-surface hover:bg-surface-dim"
                  }`}
                >
                  PENDING (1)
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter("VERIFIED")}
                  className={`px-2 py-1 uppercase font-bold transition-colors cursor-pointer ${
                    statusFilter === "VERIFIED" ? "bg-primary text-on-primary" : "bg-surface-variant text-on-surface hover:bg-surface-dim"
                  }`}
                >
                  VERIFIED (1)
                </button>
              </div>
              <div className="font-label-mono text-body-sm text-on-surface-variant">
                AUTONOMOUS AUDIT SYNC: <strong className="text-primary font-bold">00:03:42</strong>
              </div>
            </div>

            {/* DATA TABLE */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-high text-on-surface border-b border-primary/20">
                    <th className="py-2.5 px-3 font-label-caps text-label-caps uppercase tracking-wider">Request ID</th>
                    <th className="py-2.5 px-3 font-label-caps text-label-caps uppercase tracking-wider">Target VASP</th>
                    <th className="py-2.5 px-3 font-label-caps text-label-caps uppercase tracking-wider">Scope / Order</th>
                    <th className="py-2.5 px-3 font-label-caps text-label-caps uppercase tracking-wider">Report & SHA-256</th>
                    <th className="py-2.5 px-3 font-label-caps text-label-caps uppercase tracking-wider">Status</th>
                    <th className="py-2.5 px-3 font-label-caps text-label-caps uppercase tracking-wider text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="font-body-md text-body-md divide-y divide-primary/10">
                  {requests.map((r) => {
                    const isSelected = selectedReqId === r.id;
                    return (
                      <tr
                        key={r.id}
                        onClick={() => setSelectedReqId(r.id)}
                        className={`cursor-pointer transition-colors ${
                          isSelected ? "bg-surface-container" : "bg-surface-container-lowest hover:bg-surface-container-low"
                        }`}
                      >
                        <td className="py-3 px-3 align-top">
                          <div className="font-label-mono text-body-sm font-bold text-primary">{r.reqNum}</div>
                          <div className="font-label-caps text-label-caps text-on-surface-variant">{r.caseRef}</div>
                        </td>
                        <td className="py-3 px-3 align-top">
                          <div className="font-body-md text-body-md font-bold text-on-surface">{r.vasp}</div>
                          <div className="font-label-mono text-body-sm text-on-surface-variant">{r.vaspNode}</div>
                        </td>
                        <td className="py-3 px-3 align-top">
                          <span className="inline-block px-1.5 py-0.5 bg-secondary text-on-secondary font-label-caps text-label-caps uppercase font-bold tracking-tight">
                            {r.scope}
                          </span>
                          <div className="font-label-mono text-body-sm text-secondary-container mt-1">{r.mandate}</div>
                        </td>
                        <td className="py-3 px-3 align-top">
                          <div className="font-label-mono text-body-sm text-primary font-bold">{r.report}</div>
                          <div className="font-label-mono text-body-sm text-primary-fixed-dim bg-primary-container px-1 py-0.5 inline-flex items-center gap-1 mt-0.5">
                            <span className="material-symbols-outlined text-[12px]">verified</span>
                            <span>{r.sha}</span>
                          </div>
                        </td>
                        <td className="py-3 px-3 align-top">
                          <div className="flex items-center gap-1.5">
                            <span
                              className={`w-2 h-2 rounded-full ${
                                r.isPending ? "bg-secondary-container animate-ping" : "bg-primary-fixed"
                              }`}
                            ></span>
                            <span
                              className={`font-label-caps text-label-caps uppercase font-bold ${
                                r.isPending ? "text-secondary" : "text-primary"
                              }`}
                            >
                              {signedState[r.id] ? "SIGNED & DISPATCHED" : r.status}
                            </span>
                          </div>
                          <div className="font-label-mono text-body-sm text-on-surface-variant mt-0.5">{r.officer}</div>
                        </td>
                        <td className="py-3 px-3 align-top text-right">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedReqId(r.id);
                            }}
                            className="px-2.5 py-1.5 bg-primary text-on-primary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-secondary transition-colors cursor-pointer shadow-sm"
                          >
                            INSPECT
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* INTER-AGENCY COOPERATION TELEMETRY & MERKLE VISUAL */}
          <div className="bg-surface-container-low p-space-md shadow-sm border border-primary/20">
            <div className="flex items-center justify-between pb-space-sm border-b border-primary/10">
              <div>
                <span className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest font-bold">
                  TELEMETRY & VASP PEERING NODE STATUS
                </span>
                <div className="font-headline-sm text-headline-sm text-primary font-bold">
                  Cryptographic Verification Cluster
                </div>
              </div>
              <span className="bg-primary text-on-primary font-label-mono text-body-sm px-2 py-0.5 uppercase font-bold">
                4 PEERS LINKED
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-space-sm mt-space-sm">
              <div className="bg-surface-container-lowest p-space-sm shadow-sm flex flex-col justify-between border border-primary/10">
                <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">SIGNATURE PROTOCOL</span>
                <div className="font-data-metric text-headline-sm text-primary my-1 font-bold">Ed25519-Gov</div>
                <div className="font-label-mono text-body-sm text-on-surface-variant">PKCS#11 FIPS-140-3 Hardware Token</div>
              </div>
              <div className="bg-surface-container-lowest p-space-sm shadow-sm flex flex-col justify-between border border-primary/10">
                <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">DISPATCH LATENCY</span>
                <div className="font-data-metric text-headline-sm text-secondary my-1 font-bold">142 ms</div>
                <div className="font-label-mono text-body-sm text-on-surface-variant">Encrypted Direct TLS 1.3 Channel</div>
              </div>
              <div className="bg-surface-container-lowest p-space-sm shadow-sm flex flex-col justify-between border border-primary/10">
                <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">EVIDENCE IMMUTABILITY</span>
                <div className="font-data-metric text-headline-sm text-primary my-1 font-bold">100.0%</div>
                <div className="font-label-mono text-body-sm text-on-surface-variant">Dual-State Merkle Tree Anchor</div>
              </div>
            </div>

            {/* FORENSIC EVIDENCE DISPATCH ARCHITECTURE SVG */}
            <div className="bg-surface-container-lowest p-space-md mt-space-sm shadow-sm border border-primary/10">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-caps text-label-caps text-primary uppercase font-bold">
                  EVIDENTIARY MERKLE PROOF TOPOLOGY
                </span>
                <span className="font-label-mono text-body-sm text-on-surface-variant">
                  ROOT: 0x93FA...CE88
                </span>
              </div>
              <div className="w-full flex items-center justify-center py-2">
                <svg className="w-full h-24 text-primary" fill="none" viewBox="0 0 600 80" xmlns="http://www.w3.org/2000/svg">
                  <path d="M300 15 L150 45 M300 15 L450 45" stroke="currentColor" strokeDasharray="2 2" strokeWidth="1.5"></path>
                  <path d="M150 45 L80 70 M150 45 L220 70" stroke="currentColor" strokeWidth="1.5"></path>
                  <path d="M450 45 L380 70 M450 45 L520 70" stroke="currentColor" strokeWidth="1.5"></path>
                  <rect fill="#182c22" height="20" width="100" x="250" y="5"></rect>
                  <text fill="#ffffff" fontFamily="JetBrains Mono" fontSize="9" fontWeight="bold" textAnchor="middle" x="300" y="19">MERKLE ROOT</text>
                  <rect fill="#2e4237" height="20" width="90" x="105" y="35"></rect>
                  <text fill="#ffffff" fontFamily="JetBrains Mono" fontSize="8" textAnchor="middle" x="150" y="49">H(TX-LEAF 1-3)</text>
                  <rect fill="#2e4237" height="20" width="90" x="405" y="35"></rect>
                  <text fill="#ffffff" fontFamily="JetBrains Mono" fontSize="8" textAnchor="middle" x="450" y="49">H(RPC-LEAF 4-6)</text>
                  <rect fill="#efeeea" height="16" stroke="#182c22" strokeWidth="0.5" width="70" x="45" y="62"></rect>
                  <text fill="#182c22" fontFamily="JetBrains Mono" fontSize="7" textAnchor="middle" x="80" y="73">TX_HASH_01</text>
                  <rect fill="#efeeea" height="16" stroke="#182c22" strokeWidth="0.5" width="70" x="185" y="62"></rect>
                  <text fill="#182c22" fontFamily="JetBrains Mono" fontSize="7" textAnchor="middle" x="220" y="73">BLOCK_HDR</text>
                  <rect fill="#efeeea" height="16" stroke="#182c22" strokeWidth="0.5" width="70" x="345" y="62"></rect>
                  <text fill="#182c22" fontFamily="JetBrains Mono" fontSize="7" textAnchor="middle" x="380" y="73">RECEIPT_SIG</text>
                  <rect fill="#efeeea" height="16" stroke="#182c22" strokeWidth="0.5" width="70" x="485" y="62"></rect>
                  <text fill="#182c22" fontFamily="JetBrains Mono" fontSize="7" textAnchor="middle" x="520" y="73">KYC_MATCH</text>
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT 5 COLUMNS: FORMAL REQUEST PREVIEW & EVIDENCE PACKAGE INSPECTOR */}
        <div className="xl:col-span-5 flex flex-col gap-space-md">
          {/* EXECUTIVE DISPATCH DOSSIER CARD */}
          <div className="bg-surface-container-lowest shadow-md flex flex-col border border-primary/20">
            {/* CARD HEADER STRIP */}
            <div className="bg-primary text-on-primary p-space-md flex items-center justify-between">
              <div>
                <span className="font-label-caps text-label-caps text-primary-fixed uppercase tracking-widest font-bold">
                  SOVEREIGN MEMORANDUM // EVIDENTIARY DOSSIER
                </span>
                <div className="font-headline-sm text-headline-sm text-surface font-semibold tracking-tight font-serif">
                  {activeReq.reqNum}
                </div>
              </div>
              <span className="bg-secondary text-on-secondary px-2 py-0.5 font-label-mono text-body-sm uppercase font-semibold">
                URGENT FREEZE
              </span>
            </div>

            {/* DOSSIER BODY (ARCHIVAL LEGAL STYLE) */}
            <div className="p-space-md space-y-space-md bg-surface-bright">
              {/* OFFICIAL SEAL & MEMO HEADING */}
              <div className="bg-surface-container-low p-space-sm flex items-start gap-space-sm border border-primary/10">
                <div className="w-10 h-10 bg-primary flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-surface text-[22px]">policy</span>
                </div>
                <div className="space-y-0.5">
                  <div className="font-label-caps text-label-caps text-primary uppercase font-bold tracking-wider">
                    OFFICE OF CYBER FORENSICS & ASSET TRACE
                  </div>
                  <div className="font-body-md text-body-md text-on-surface font-semibold">
                    FORMAL CRYPTOGRAPHIC DIRECTIVE UNDER SEC 91 CrPC
                  </div>
                  <div className="font-label-mono text-body-sm text-on-surface-variant">
                    SERIAL: DHANRASHI/{activeReq.vasp.replace(" ", "-")}/FREEZE-{activeReq.id}/2026
                  </div>
                </div>
              </div>

              {/* KEY ATTRIBUTES TABLE */}
              <div className="bg-surface-container-lowest p-space-sm shadow-sm space-y-space-xs font-body-md border border-primary/10">
                <div className="flex items-center justify-between py-1 bg-surface-container px-2">
                  <span className="font-label-caps text-label-caps text-on-surface-variant uppercase font-semibold">
                    Target Wallet
                  </span>
                  <div className="flex items-center gap-1 font-label-mono text-body-sm font-bold text-primary">
                    <span>{activeReq.targetWallet}</span>
                    <button
                      onClick={() => alert(`Copied target wallet: ${activeReq.targetWallet}`)}
                      className="text-on-surface-variant hover:text-primary cursor-pointer"
                      title="Copy Address"
                    >
                      <span className="material-symbols-outlined text-[14px]">content_copy</span>
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between py-1 bg-surface-container-low px-2">
                  <span className="font-label-caps text-label-caps text-on-surface-variant uppercase font-semibold">
                    Identified VASP
                  </span>
                  <div className="text-right">
                    <span className="font-body-md text-body-md font-bold text-primary">{activeReq.vasp}</span>
                    <span className="font-label-mono text-body-sm text-on-surface-variant block">
                      (Attribution: {activeReq.score} | Flow: {activeReq.flowShare})
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between py-1 bg-surface-container px-2">
                  <span className="font-label-caps text-label-caps text-on-surface-variant uppercase font-semibold">
                    Transit Risk Velocity
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-label-mono text-body-sm font-bold text-secondary">
                      {activeReq.risk} / 100 [HIGH RISK]
                    </span>
                    <span className="w-16 h-2 bg-surface-variant relative overflow-hidden inline-block">
                      <span className="absolute left-0 top-0 bottom-0 bg-secondary" style={{ width: `${activeReq.risk}%` }}></span>
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between py-1 bg-surface-container-low px-2">
                  <span className="font-label-caps text-label-caps text-on-surface-variant uppercase font-semibold">
                    Provenance Rigor
                  </span>
                  <div className="flex items-center gap-1">
                    <span className="bg-primary text-on-primary font-label-caps text-label-caps px-1.5 py-0.5">
                      OBSERVED
                    </span>
                    <span className="bg-surface-variant text-on-surface font-label-caps text-label-caps px-1.5 py-0.5">
                      THIRD-PARTY
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between py-1 bg-surface-container px-2">
                  <span className="font-label-caps text-label-caps text-on-surface-variant uppercase font-semibold">
                    Cluster Identifier
                  </span>
                  <span className="font-label-mono text-body-sm text-on-surface">{activeReq.cluster}</span>
                </div>
              </div>

              {/* MERKLE-VERIFIED ATTACHMENTS (6 ITEMS) */}
              <div className="space-y-space-xs">
                <div className="flex items-center justify-between">
                  <span className="font-label-caps text-label-caps text-primary uppercase font-bold tracking-wider">
                    ATTACHED EVIDENTIARY RECORDS (6 ITEMS)
                  </span>
                  <span className="font-label-mono text-body-sm text-secondary-container font-semibold">
                    MERKLE ANCHORED
                  </span>
                </div>
                <div className="bg-surface-container-low p-space-sm space-y-1 font-label-mono text-body-sm border border-primary/10">
                  {[
                    { name: "01_PRIMARY_HEURISTIC_TRACE.PDF", sha: "d8e1...4a09", icon: "receipt_long" },
                    { name: "02_RAW_RPC_RECEIPTS_ETH_MAINNET.JSON", sha: "9b24...f011", icon: "token" },
                    { name: "03_MULTI_HOP_FLOW_GRAPH_SNAPSHOT.PNG", sha: "77a0...88ec", icon: "account_tree" },
                    { name: "04_INVESTIGATOR_AUDIT_LOG_SIG.BIN", sha: "e8a9...b401", icon: "fingerprint" },
                    { name: "05_VASP_ALPHA_HOTWALLET_REGISTRY.CSV", sha: "c314...e299", icon: "database" },
                    { name: "06_CRPC_SEC91_REQUISITION_ORDER.DOC", sha: "f198...77ba", icon: "description" },
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between text-on-surface hover:bg-surface p-0.5">
                      <span className="flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[14px] text-primary">{item.icon}</span>
                        <span>{item.name}</span>
                      </span>
                      <span className="text-on-surface-variant">SHA256: {item.sha}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* STATUTORY & LEGAL DISCLAIMER */}
              <div className="bg-surface-container p-space-sm text-on-surface-variant border-l-2 border-secondary">
                <div className="flex items-center gap-1 text-secondary font-label-caps text-label-caps uppercase font-bold">
                  <span className="material-symbols-outlined text-[14px]">warning</span>
                  <span>STATUTORY NOTICE OF PROBABILISTIC HEURISTICS</span>
                </div>
                <p className="font-body-sm text-body-sm mt-1 leading-normal italic">
                  &quot;Attribution represents an investigative lead based on probabilistic multi-factor graph heuristics and on-chain transactional velocity. It does not constitute conclusive evidence of guilt or ownership until independently corroborated by depository KYC disclosure from the recipient institution.&quot;
                </p>
              </div>

              {/* SIGN-OFF METADATA STRIP */}
              <div className="bg-surface-container-high p-space-sm flex items-center justify-between font-label-mono text-body-sm border border-primary/10">
                <div>
                  <span className="text-on-surface-variant block text-label-caps">ORIGINATING INVESTIGATOR</span>
                  <span className="font-bold text-primary">Insp. V. Sharma (ID: FIU-7729)</span>
                </div>
                <div className="text-right">
                  <span className="text-on-surface-variant block text-label-caps">REQUIRED SIGNER</span>
                  <span className="font-bold text-secondary">Superintendent / Jt. Director</span>
                </div>
              </div>

              {/* ACTION CONTROLS & DISPATCH OPERATIONAL TRIGGERS */}
              <div className="pt-space-xs space-y-space-xs">
                <button
                  onClick={handleSign}
                  className={`w-full py-3 font-label-caps text-label-caps font-bold uppercase tracking-widest transition-colors flex items-center justify-center gap-space-xs shadow-md cursor-pointer ${
                    isReqSigned
                      ? "bg-primary text-on-primary"
                      : "bg-secondary text-on-secondary hover:bg-primary"
                  }`}
                  id="btnSignGov"
                  type="button"
                >
                  <span className="material-symbols-outlined text-[18px]">key</span>
                  <span>{isReqSigned ? "CRYPTOGRAPHICALLY SIGNED // DISPATCHED" : "SIGN WITH PIV / GOV CRYPTO-TOKEN"}</span>
                </button>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-xs">
                  <button
                    onClick={() => alert(`Downloading Merkle-sealed evidence package: ${activeReq.reqNum}_EVIDENCE.ZIP`)}
                    className="py-2.5 bg-surface-container-highest text-primary font-label-caps text-label-caps font-bold uppercase tracking-wider hover:bg-primary-container hover:text-on-primary transition-colors flex items-center justify-center gap-1.5 shadow-sm border border-primary/20 cursor-pointer"
                    id="btnDownloadPkg"
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[16px]">folder_zip</span>
                    <span>DOWNLOAD EVIDENCE (.ZIP)</span>
                  </button>
                  <button
                    onClick={() => alert("Reason for return logged to immutable audit ledger.")}
                    className="py-2.5 bg-surface-container-highest text-error font-label-caps text-label-caps font-bold uppercase tracking-wider hover:bg-error hover:text-on-error transition-colors flex items-center justify-center gap-1.5 shadow-sm border border-error/20 cursor-pointer"
                    id="btnRejectAudit"
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[16px]">cancel</span>
                    <span>REJECT WITH COMMENT</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* NEW SAHYOG REQUEST MODAL */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 bg-primary/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border-2 border-primary max-w-xl w-full p-space-lg shadow-2xl space-y-space-md">
            <div className="flex items-center justify-between border-b border-primary/20 pb-2">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-[24px]">gavel</span>
                <h3 className="font-headline-sm text-headline-sm font-bold text-primary font-serif">
                  GENERATE LAWFUL REQUISITION // SEC 91 CrPC
                </h3>
              </div>
              <button
                onClick={() => setShowNewModal(false)}
                className="text-on-surface-variant hover:text-primary p-1 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleCreateRequest} className="space-y-3 font-body-md text-body-md">
              <div>
                <label className="block font-label-caps text-label-caps uppercase text-primary font-bold mb-1">
                  CASE REFERENCE & INCIDENT
                </label>
                <input
                  type="text"
                  value={newCaseRef}
                  onChange={(e) => setNewCaseRef(e.target.value)}
                  className="w-full bg-surface-container-lowest font-label-mono text-body-md px-3 py-2 border border-primary/40 focus:border-primary focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block font-label-caps text-label-caps uppercase text-primary font-bold mb-1">
                  TARGET RECIPIENT VASP
                </label>
                <input
                  type="text"
                  value={newVasp}
                  onChange={(e) => setNewVasp(e.target.value)}
                  className="w-full bg-surface-container-lowest font-label-mono text-body-md px-3 py-2 border border-primary/40 focus:border-primary focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block font-label-caps text-label-caps uppercase text-primary font-bold mb-1">
                  SUSPICIOUS WALLET ADDRESS
                </label>
                <input
                  type="text"
                  value={newTargetWallet}
                  onChange={(e) => setNewTargetWallet(e.target.value)}
                  className="w-full bg-surface-container-lowest font-label-mono text-body-md px-3 py-2 border border-primary/40 focus:border-primary focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block font-label-caps text-label-caps uppercase text-primary font-bold mb-1">
                  STATUTORY JURISDICTION MANDATE
                </label>
                <input
                  type="text"
                  value={newMandate}
                  onChange={(e) => setNewMandate(e.target.value)}
                  className="w-full bg-surface-container-lowest font-label-mono text-body-md px-3 py-2 border border-primary/40 focus:border-primary focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block font-label-caps text-label-caps uppercase text-primary font-bold mb-1">
                  DIRECTIVE SCOPE
                </label>
                <select
                  value={newOrderType}
                  onChange={(e) => setNewOrderType(e.target.value)}
                  className="w-full bg-surface-container-lowest font-label-mono text-body-md px-3 py-2 border border-primary/40 focus:border-primary focus:outline-none"
                >
                  <option value="EMERGENCY FREEZE & KYC">Emergency Asset Freeze & KYC Disclosure</option>
                  <option value="KYC IDENTITY DISCLOSURE">KYC & Fiat On/Off Ramp Identity Disclosure</option>
                  <option value="TRANSACTION LOG AUDIT">Transaction Telemetry & IP Address Logs</option>
                </select>
              </div>

              <div className="p-2 bg-surface-container border border-primary/20 text-[11px] font-label-mono text-on-surface-variant">
                * Note: Submission logs draft to immutable audit ledger. Formal push to VASP peer nodes will require digital signature authorization from the designated Supervisory Officer.
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-primary/20">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 border border-primary text-primary font-label-caps text-label-caps uppercase tracking-wider font-bold hover:bg-surface-variant transition-colors cursor-pointer"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-secondary text-on-secondary font-label-caps text-label-caps uppercase tracking-wider font-bold hover:bg-primary transition-colors cursor-pointer shadow-md"
                >
                  SUBMIT TO PIPELINE
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
