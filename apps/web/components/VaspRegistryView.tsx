"use client";

import { useEffect, useState } from "react";
import { VaspRecord, VaspAddressRecord, UserRole } from "@/lib/types";
import { api } from "@/lib/api";
import {
  Building2,
  Search,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Shield,
  Layers,
} from "lucide-react";

interface VaspRegistryViewProps {
  userRole: UserRole;
  onRefreshNeeded?: () => void;
}

export default function VaspRegistryView({ userRole, onRefreshNeeded }: VaspRegistryViewProps) {
  const [vasps, setVasps] = useState<VaspRecord[]>([]);
  const [addresses, setAddresses] = useState<VaspAddressRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"vasps" | "addresses" | "conflicts">("vasps");

  // Conflict Resolution Dialog
  const [selectedConflictAddr, setSelectedConflictAddr] = useState<VaspAddressRecord | null>(null);
  const [resolutionType, setResolutionType] = useState<"superseded" | "disputed">("superseded");
  const [justification, setJustification] = useState<string>("");
  const [resolving, setResolving] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const canManageRegistry = ["FIA", "ADM"].includes(userRole);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [vaspsData, addrsData] = await Promise.all([
        api.listVasps(),
        api.listVaspAddresses(),
      ]);
      setVasps(vaspsData);
      setAddresses(addrsData);
    } catch (err) {
      console.error("Failed to load VASP registry:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter conflicting or disputed addresses (J2)
  const conflictAddresses = addresses.filter(
    (a) => a.status === "disputed" || a.status === "stale"
  );

  const handleResolveConflict = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConflictAddr || !justification.trim()) return;

    setResolving(true);
    setSuccessMsg(null);
    try {
      await api.resolveLabelConflict(selectedConflictAddr.id, resolutionType, justification);
      setSuccessMsg(`Address marked as ${resolutionType.toUpperCase()} with audit justification.`);
      setSelectedConflictAddr(null);
      setJustification("");
      await fetchData();
      if (onRefreshNeeded) onRefreshNeeded();
    } catch (err: any) {
      console.error("Failed to resolve label conflict:", err);
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Building2 className="w-5 h-5 text-purple-600" />
            <h3 className="text-base font-bold text-slate-900">
              VASP Intelligence &amp; Entity Registry
            </h3>
          </div>
          <p className="text-xs text-slate-500 max-w-xl">
            Curated intelligence database mapping known exchange deposit wallets, hot/cold clusters,
            and regulatory entity profiles (PRD §10).
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search VASP or address..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="text-xs pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 w-64"
            />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab("vasps")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeTab === "vasps"
              ? "bg-slate-900 text-white"
              : "bg-white text-slate-600 hover:bg-slate-100"
          }`}
        >
          Entities ({vasps.length})
        </button>
        <button
          onClick={() => setActiveTab("addresses")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeTab === "addresses"
              ? "bg-slate-900 text-white"
              : "bg-white text-slate-600 hover:bg-slate-100"
          }`}
        >
          Labeled Addresses ({addresses.length})
        </button>
        <button
          onClick={() => setActiveTab("conflicts")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeTab === "conflicts"
              ? "bg-amber-600 text-white"
              : "bg-white text-slate-600 hover:bg-slate-100"
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Label Conflicts &amp; Staleness ({conflictAddresses.length})</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-lg text-xs font-medium flex items-center justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)}>✕</button>
        </div>
      )}

      {/* Content Tables */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <span className="inline-block w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2" />
            <p>Loading registry intelligence...</p>
          </div>
        ) : activeTab === "vasps" ? (
          /* Entities Table */
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3">Entity Name</th>
                  <th className="p-3">VASP ID</th>
                  <th className="p-3">Jurisdiction</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Data Class</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {vasps
                  .filter(
                    (v) =>
                      v.name.toLowerCase().includes(search.toLowerCase()) ||
                      v.vasp_id.toLowerCase().includes(search.toLowerCase())
                  )
                  .map((v) => (
                    <tr key={v.vasp_id} className="hover:bg-slate-50 transition">
                      <td className="p-3 font-bold text-slate-900">{v.name}</td>
                      <td className="p-3 font-mono text-purple-700 font-semibold">{v.vasp_id}</td>
                      <td className="p-3 text-slate-600">{v.jurisdiction || "Global / Unspecified"}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase">
                          {v.status || "ACTIVE"}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                          {v.is_synthetic ? "SYNTHETIC FIXTURE" : "PRODUCTION"}
                        </span>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : activeTab === "addresses" ? (
          /* Labeled Addresses Table */
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3">Address</th>
                  <th className="p-3">Chain</th>
                  <th className="p-3">Mapped VASP</th>
                  <th className="p-3">Address Type</th>
                  <th className="p-3">Confidence</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {addresses
                  .filter(
                    (a) =>
                      a.address.toLowerCase().includes(search.toLowerCase()) ||
                      a.vasp_id.toLowerCase().includes(search.toLowerCase())
                  )
                  .map((a) => (
                    <tr key={a.id} className="hover:bg-slate-50 transition">
                      <td className="p-3 font-mono text-slate-900 select-all">{a.address}</td>
                      <td className="p-3 capitalize font-medium text-slate-600">{a.chain}</td>
                      <td className="p-3 font-bold text-purple-700">{a.vasp_id}</td>
                      <td className="p-3 text-slate-700 uppercase text-[10px] font-semibold">
                        {a.address_type}
                      </td>
                      <td className="p-3 font-mono text-blue-600 font-semibold">
                        {(a.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                            a.status === "active"
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                              : a.status === "disputed"
                              ? "bg-rose-50 text-rose-700 border-rose-200"
                              : "bg-amber-50 text-amber-700 border-amber-200"
                          }`}
                        >
                          {a.status}
                        </span>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Conflict Resolution Tab (Journey J2) */
          <div className="p-6 space-y-4">
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-900">
              <p className="font-bold mb-1">
                Journey J2 — Analyst Label Conflict &amp; Staleness Resolution
              </p>
              <p className="leading-relaxed">
                When multiple intelligence providers disagree or labels age over 365 days, CAP-04 /
                CAP-07 triggers in attribution. Analysts can mark one record as SUPERSEDED or
                DISPUTED with mandatory justification. All changes are recorded in the audit trail.
              </p>
            </div>

            {conflictAddresses.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                No active conflicts or stale records requiring curation.
              </div>
            ) : (
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                    <tr>
                      <th className="p-3">Target Address</th>
                      <th className="p-3">Chain</th>
                      <th className="p-3">Associated VASP</th>
                      <th className="p-3">Current Status</th>
                      <th className="p-3">Source &amp; Reference</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium">
                    {conflictAddresses.map((ca) => (
                      <tr key={ca.id} className="hover:bg-slate-50">
                        <td className="p-3 font-mono select-all text-slate-900">{ca.address}</td>
                        <td className="p-3 capitalize">{ca.chain}</td>
                        <td className="p-3 font-bold text-purple-700">{ca.vasp_id}</td>
                        <td className="p-3 font-mono font-bold text-amber-700 uppercase">
                          {ca.status}
                        </td>
                        <td className="p-3 text-slate-500 text-[11px]">
                          {ca.source} ({ca.evidence_type})
                        </td>
                        <td className="p-3 text-right">
                          <button
                            disabled={!canManageRegistry}
                            onClick={() => setSelectedConflictAddr(ca)}
                            className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs font-semibold shadow-xs disabled:opacity-40"
                          >
                            Resolve (J2)
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Conflict Resolution Modal */}
      {selectedConflictAddr && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-sm font-bold text-slate-900">Resolve Intelligence Conflict (J2)</h3>
              <button
                onClick={() => setSelectedConflictAddr(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="text-xs space-y-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div>
                <span className="text-slate-400 text-[10px] uppercase block">Target Address:</span>
                <span className="font-mono font-semibold text-slate-900 select-all">
                  {selectedConflictAddr.address}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-400 text-[10px] uppercase block">Mapped VASP:</span>
                  <span className="font-semibold text-purple-700">
                    {selectedConflictAddr.vasp_id}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] uppercase block">Chain:</span>
                  <span className="font-semibold capitalize text-slate-700">
                    {selectedConflictAddr.chain}
                  </span>
                </div>
              </div>
            </div>

            <form onSubmit={handleResolveConflict} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Resolution Decision
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-1.5 cursor-pointer font-medium">
                    <input
                      type="radio"
                      name="resType"
                      value="superseded"
                      checked={resolutionType === "superseded"}
                      onChange={() => setResolutionType("superseded")}
                    />
                    <span>Mark as SUPERSEDED (Overridden by verified source)</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer font-medium">
                    <input
                      type="radio"
                      name="resType"
                      value="disputed"
                      checked={resolutionType === "disputed"}
                      onChange={() => setResolutionType("disputed")}
                    />
                    <span>Mark as DISPUTED (Triggers CAP-04)</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Analyst Justification &amp; Source Proof (Required)
                </label>
                <textarea
                  required
                  rows={3}
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  placeholder="State evidence document, ticket id, or rationale for overriding this entity label..."
                  className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-slate-900 focus:outline-blue-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setSelectedConflictAddr(null)}
                  className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resolving || !justification.trim()}
                  className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-semibold shadow-xs disabled:opacity-50"
                >
                  {resolving ? "Recording..." : "Apply & Audit Resolution"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
