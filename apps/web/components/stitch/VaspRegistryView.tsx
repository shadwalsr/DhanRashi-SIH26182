"use client";

import React, { useState } from "react";

export default function VaspRegistryView() {
  const [search, setSearch] = useState("");
  const [filterJurisdiction, setFilterJurisdiction] = useState<string>("ALL");

  const vasps = [
    {
      id: "VASP-001",
      name: "Binance Custody India",
      code: "BINANCE-IN",
      jurisdiction: "IND",
      fiuStatus: "REGISTERED",
      hotAddresses: 48,
      coldAddresses: 12,
      confidence: "Grade A1 (98.4%)",
      complianceContact: "compliance@binance.in",
    },
    {
      id: "VASP-002",
      name: "CoinDCX (Neblio Technologies)",
      code: "COINDCX",
      jurisdiction: "IND",
      fiuStatus: "REGISTERED",
      hotAddresses: 32,
      coldAddresses: 8,
      confidence: "Grade A1 (99.1%)",
      complianceContact: "nodal@coindcx.com",
    },
    {
      id: "VASP-003",
      name: "WazirX (Zanmai Labs)",
      code: "WAZIRX",
      jurisdiction: "IND",
      fiuStatus: "REGISTERED",
      hotAddresses: 24,
      coldAddresses: 6,
      confidence: "Grade A2 (94.0%)",
      complianceContact: "legal@wazirx.com",
    },
    {
      id: "VASP-004",
      name: "Coinbase Global Custody",
      code: "COINBASE",
      jurisdiction: "USA",
      fiuStatus: "FOREIGN RECOGNIZED",
      hotAddresses: 112,
      coldAddresses: 45,
      confidence: "Grade A1 (99.5%)",
      complianceContact: "subpoena@coinbase.com",
    },
    {
      id: "VASP-005",
      name: "Kraken Digital Assets",
      code: "KRAKEN",
      jurisdiction: "USA/EU",
      fiuStatus: "FOREIGN RECOGNIZED",
      hotAddresses: 64,
      coldAddresses: 18,
      confidence: "Grade A1 (97.8%)",
      complianceContact: "compliance@kraken.com",
    },
    {
      id: "VASP-006",
      name: "OKX Exchange Operations",
      code: "OKX",
      jurisdiction: "SEY",
      fiuStatus: "NON-COOPERATIVE",
      hotAddresses: 84,
      coldAddresses: 22,
      confidence: "Grade B (82.1%)",
      complianceContact: "unknown@okx.com",
    },
  ];

  const filtered = vasps.filter((v) => {
    const matchesSearch =
      v.name.toLowerCase().includes(search.toLowerCase()) ||
      v.code.toLowerCase().includes(search.toLowerCase());
    const matchesJurisdiction =
      filterJurisdiction === "ALL" || v.jurisdiction === filterJurisdiction;
    return matchesSearch && matchesJurisdiction;
  });

  return (
    <div className="flex flex-col w-full space-y-space-md">
      {/* HEADER */}
      <div className="bg-surface-container-low p-gutter border border-primary/20 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md">
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
              REGISTRY FOLIO // SECTION 04
            </span>
            <h1 className="font-headline-lg text-headline-lg font-serif font-bold text-primary tracking-tight">
              VASP INTELLIGENCE REGISTRY
            </h1>
            <p className="font-body-md text-on-surface-variant max-w-2xl">
              Cryptographically verified deposit hot-wallets, cold vaults, and FIU-IND statutory compliance registry for Virtual Asset Service Providers.
            </p>
          </div>
          <button
            onClick={() => alert("Synchronizing registry with FIU-IND and global blockchain intelligence peers...")}
            className="px-4 py-2.5 bg-secondary text-on-secondary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-primary transition-colors flex items-center gap-2 shadow-sm cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">sync</span>
            <span>SYNC CLUSTERS</span>
          </button>
        </div>
      </div>

      {/* SEARCH & FILTERS */}
      <div className="bg-surface-container p-space-md flex flex-wrap items-center justify-between gap-space-md border border-primary/20">
        <div className="flex items-center gap-space-sm flex-1 max-w-md">
          <span className="material-symbols-outlined text-outline text-[18px]">search</span>
          <input
            type="text"
            placeholder="FILTER BY VASP NAME, IDENTIFIER, OR CODE..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-surface text-primary font-label-mono text-body-sm px-3 py-1.5 border border-primary/30 focus:border-primary focus:outline-none uppercase"
          />
        </div>

        <div className="flex items-center gap-1 font-label-caps text-label-caps font-bold">
          <span className="text-on-surface-variant uppercase mr-2">JURISDICTION:</span>
          {["ALL", "IND", "USA", "SEY"].map((j) => (
            <button
              key={j}
              type="button"
              onClick={() => setFilterJurisdiction(j)}
              className={`px-2.5 py-1 uppercase transition-colors cursor-pointer ${
                filterJurisdiction === j
                  ? "bg-primary text-on-primary shadow-sm"
                  : "bg-surface text-on-surface hover:bg-surface-dim"
              }`}
            >
              {j}
            </button>
          ))}
        </div>
      </div>

      {/* VASP TABLE */}
      <div className="border border-primary/20 bg-surface shadow-sm overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container border-b border-primary/20 font-label-caps text-label-caps uppercase text-on-surface tracking-wider">
              <th className="py-3 px-4">Registry ID</th>
              <th className="py-3 px-4">Entity Legal Name</th>
              <th className="py-3 px-4">Jurisdiction</th>
              <th className="py-3 px-4">FIU Compliance Status</th>
              <th className="py-3 px-4">Known Clusters</th>
              <th className="py-3 px-4">Attribution Reliability</th>
              <th className="py-3 px-4 text-right">Direct Requisition</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-primary/10 font-body-md">
            {filtered.map((v) => (
              <tr key={v.id} className="hover:bg-surface-container-low transition-colors">
                <td className="py-3 px-4 font-label-mono text-body-sm font-bold text-primary">
                  {v.id}
                </td>
                <td className="py-3 px-4">
                  <div className="font-bold text-primary">{v.name}</div>
                  <div className="font-label-mono text-body-sm text-on-surface-variant">{v.code}</div>
                </td>
                <td className="py-3 px-4 font-label-mono text-body-sm">
                  <span className="px-1.5 py-0.5 bg-surface-container border border-primary/20 font-bold">
                    {v.jurisdiction}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span
                    className={`px-2 py-0.5 font-label-caps text-label-caps uppercase font-bold ${
                      v.fiuStatus === "REGISTERED"
                        ? "bg-primary text-on-primary"
                        : v.fiuStatus === "FOREIGN RECOGNIZED"
                        ? "bg-primary-container text-surface"
                        : "bg-error text-on-error"
                    }`}
                  >
                    {v.fiuStatus}
                  </span>
                </td>
                <td className="py-3 px-4 font-label-mono text-body-sm">
                  <span>{v.hotAddresses} Hot / {v.coldAddresses} Cold</span>
                </td>
                <td className="py-3 px-4 font-label-mono text-body-sm font-bold text-secondary">
                  {v.confidence}
                </td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={() => alert(`Initiating Section 91 CrPC requisition against ${v.name} (${v.complianceContact})`)}
                    className="px-2.5 py-1 bg-secondary text-on-secondary font-label-mono text-[10px] uppercase font-bold hover:bg-primary transition-colors cursor-pointer"
                  >
                    DRAFT REQUISITION
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
