"use client";

import { useEffect, useState } from "react";
import { AuditLog, UserRole } from "@/lib/types";
import { api } from "@/lib/api";
import {
  History,
  Lock,
  CheckCircle2,
  XCircle,
  Hash,
  ShieldCheck,
  Download,
} from "lucide-react";

interface AuditViewProps {
  userRole: UserRole;
}

export default function AuditView({ userRole }: AuditViewProps) {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] = useState<{
    valid: boolean;
    total_events: number;
    checked_at: string;
  } | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.listAuditLogs();
      setLogs(data);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await api.verifyAuditChain();
      setVerificationResult(res);
    } catch (err) {
      setVerificationResult({
        valid: false,
        total_events: logs.length,
        checked_at: new Date().toISOString(),
      });
    } finally {
      setVerifying(false);
    }
  };

  const handleExportCsv = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      ["Seq,Timestamp,Actor,Role,Action,Resource,Outcome,Hash"]
        .concat(
          logs.map(
            (l) =>
              `${l.sequence_num},"${l.timestamp}","${l.actor_email || ""}","${
                l.actor_role || ""
              }","${l.action}","${l.resource_type}:${l.resource_id || ""}","${l.outcome}","${
                l.entry_hash
              }"`
          )
        )
        .join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `audit-ledger-${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <History className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-slate-900">
              Immutable Audit Ledger &amp; Chain Verification (Journey J4)
            </h3>
          </div>
          <p className="text-xs text-slate-500 max-w-xl">
            Append-only, SHA-256 hash-chained log of every system access, permission evaluation,
            investigation run, and supervisor approval.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCsv}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={handleVerifyChain}
            disabled={verifying}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs disabled:opacity-50"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>{verifying ? "Verifying..." : "Verify Audit Hash Chain (J4)"}</span>
          </button>
        </div>
      </div>

      {/* Verification Banner */}
      {verificationResult && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-medium animate-in fade-in duration-200 ${
            verificationResult.valid
              ? "bg-emerald-50 text-emerald-800 border-emerald-300"
              : "bg-rose-50 text-rose-800 border-rose-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {verificationResult.valid ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            ) : (
              <XCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            )}
            <div>
              <p className="font-bold">
                {verificationResult.valid
                  ? "Audit Chain Verification Passed — Zero Tampering Detected"
                  : "Audit Chain Integrity Compromised"}
              </p>
              <p className="text-[11px] opacity-80">
                Verified {verificationResult.total_events} consecutive hash-chained events. Every
                event satisfies SHA256(H[i-1] || payload). Checked at{" "}
                {new Date(verificationResult.checked_at).toLocaleTimeString()}.
              </p>
            </div>
          </div>
          <button
            onClick={() => setVerificationResult(null)}
            className="text-slate-400 hover:text-slate-600 font-bold px-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Logs Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Loading audit ledger...</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">No audit events recorded.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3 w-14 text-center">Seq</th>
                  <th className="p-3">Actor / Email</th>
                  <th className="p-3">Role</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Resource</th>
                  <th className="p-3">Outcome</th>
                  <th className="p-3">Cryptographic Event Hash</th>
                  <th className="p-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="p-3 text-center font-mono font-bold text-slate-400">
                      #{log.sequence_num}
                    </td>
                    <td className="p-3 text-slate-900 font-semibold">{log.actor_email || "System"}</td>
                    <td className="p-3">
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                        {log.actor_role || "CORE"}
                      </span>
                    </td>
                    <td className="p-3 font-mono font-bold text-blue-700">{log.action}</td>
                    <td className="p-3 text-slate-600 font-mono text-[11px]">
                      {log.resource_type}
                      {log.resource_id ? `:${log.resource_id.slice(0, 8)}...` : ""}
                    </td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                          log.outcome === "ALLOW"
                            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                            : "bg-rose-50 text-rose-700 border-rose-200"
                        }`}
                      >
                        {log.outcome}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-[11px] text-slate-500">
                      <div className="flex items-center gap-1" title={log.entry_hash}>
                        <Hash className="w-3 h-3 text-slate-400" />
                        <span>{log.entry_hash.slice(0, 14)}...</span>
                      </div>
                    </td>
                    <td className="p-3 text-slate-400 text-[11px] whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
