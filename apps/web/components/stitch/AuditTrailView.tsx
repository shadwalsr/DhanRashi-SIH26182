"use client";

import React, { useState } from "react";

export default function AuditTrailView() {
  const [filterAction, setFilterAction] = useState<string>("ALL");

  const auditEvents = [
    {
      id: "AUD-8921",
      timestamp: "2026-10-05 14:32:10 UTC",
      officer: "Insp. V. Sharma",
      role: "ANALYST (FIU-IND)",
      action: "ADJUDICATION_ACCEPTED",
      details: "Accepted Lead #1 (VASP Alpha, Score: 87.4) on CASE-02.",
      sig: "0x89ab...c120",
    },
    {
      id: "AUD-8920",
      timestamp: "2026-10-05 14:30:45 UTC",
      officer: "Insp. V. Sharma",
      role: "ANALYST (FIU-IND)",
      action: "ATTRIBUTION_EXECUTE",
      details: "Ran ATT-v1.0 multi-hop flow model across 3 hops on 0x71C9...89A2.",
      sig: "0x12dc...f991",
    },
    {
      id: "AUD-8919",
      timestamp: "2026-10-05 14:15:22 UTC",
      officer: "DySP R. Verma",
      role: "SUPERVISOR",
      action: "SAHYOG_DISPATCH_SIGN",
      details: "Digitally signed Section 91 CrPC notice SYG-2026-0039 targeting VASP KAPPA.",
      sig: "0x33be...7741",
    },
    {
      id: "AUD-8918",
      timestamp: "2026-10-05 13:58:04 UTC",
      officer: "System Administrator",
      role: "ADMIN",
      action: "REGISTRY_UPDATE",
      details: "Updated cluster keys for Binance Custody IND (#VASP-ALP-09).",
      sig: "0x77ff...bb02",
    },
    {
      id: "AUD-8917",
      timestamp: "2026-10-05 12:44:19 UTC",
      officer: "Insp. V. Sharma",
      role: "ANALYST (FIU-IND)",
      action: "CASE_INGESTION",
      details: "Ingested synthetic benchmark case CASE-02 (Short Path vs Volume).",
      sig: "0xaa44...9988",
    },
  ];

  const filtered = auditEvents.filter(
    (e) => filterAction === "ALL" || e.action.includes(filterAction)
  );

  return (
    <div className="flex flex-col w-full space-y-space-md">
      {/* HEADER */}
      <div className="bg-surface-container-low p-gutter border border-primary/20 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md">
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
              SOVEREIGN INTEGRITY // SECTION 08
            </span>
            <h1 className="font-headline-lg text-headline-lg font-serif font-bold text-primary tracking-tight">
              IMMUTABLE AUDIT TRAIL
            </h1>
            <p className="font-body-md text-on-surface-variant max-w-2xl">
              Append-only cryptographic event ledger tracking all analyst adjudications, algorithmic executions, supervisor authorizations, and dispatch transmissions.
            </p>
          </div>
          <button
            onClick={() => alert("Audit trail exported with signed verification certificate.")}
            className="px-4 py-2.5 bg-primary text-on-primary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-secondary transition-colors flex items-center gap-2 shadow-sm cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">file_download</span>
            <span>EXPORT AUDIT LOG</span>
          </button>
        </div>
      </div>

      {/* FILTER STRIP */}
      <div className="bg-surface-container p-space-md flex items-center justify-between border border-primary/20">
        <div className="flex items-center gap-1 font-label-caps text-label-caps font-bold">
          <span className="text-on-surface-variant uppercase mr-2">ACTION FILTER:</span>
          {["ALL", "ADJUDICATION", "ATTRIBUTION", "DISPATCH", "REGISTRY"].map((act) => (
            <button
              key={act}
              type="button"
              onClick={() => setFilterAction(act)}
              className={`px-2.5 py-1 uppercase transition-colors cursor-pointer ${
                filterAction === act
                  ? "bg-primary text-on-primary shadow-sm"
                  : "bg-surface text-on-surface hover:bg-surface-dim"
              }`}
            >
              {act}
            </button>
          ))}
        </div>
        <div className="font-label-mono text-body-sm text-on-surface-variant">
          CHAIN STATE: <strong className="text-primary font-bold">TAMPER-PROOF (HASH ANCHORED)</strong>
        </div>
      </div>

      {/* AUDIT TABLE */}
      <div className="border border-primary/20 bg-surface shadow-sm overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container border-b border-primary/20 font-label-caps text-label-caps uppercase text-on-surface tracking-wider">
              <th className="py-3 px-4">Event ID</th>
              <th className="py-3 px-4">Timestamp (UTC)</th>
              <th className="py-3 px-4">Officer & Role</th>
              <th className="py-3 px-4">Action Type</th>
              <th className="py-3 px-4">Operational Details</th>
              <th className="py-3 px-4 text-right">Ed25519 Sig</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-primary/10 font-body-md">
            {filtered.map((ev) => (
              <tr key={ev.id} className="hover:bg-surface-container-low transition-colors">
                <td className="py-3 px-4 font-label-mono text-body-sm font-bold text-primary">
                  {ev.id}
                </td>
                <td className="py-3 px-4 font-label-mono text-body-sm text-on-surface-variant">
                  {ev.timestamp}
                </td>
                <td className="py-3 px-4">
                  <div className="font-bold text-primary">{ev.officer}</div>
                  <div className="font-label-mono text-[10px] text-on-surface-variant uppercase">{ev.role}</div>
                </td>
                <td className="py-3 px-4">
                  <span className="px-2 py-0.5 bg-surface-container border border-primary/20 font-label-mono text-[10px] uppercase font-bold text-primary">
                    {ev.action}
                  </span>
                </td>
                <td className="py-3 px-4 font-body-sm text-on-surface max-w-md">
                  {ev.details}
                </td>
                <td className="py-3 px-4 text-right font-label-mono text-body-sm text-secondary font-bold">
                  {ev.sig}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
