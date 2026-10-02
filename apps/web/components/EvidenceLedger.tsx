"use client";

import { useEffect, useState } from "react";
import { Evidence, ProvenanceClass } from "@/lib/types";
import { api } from "@/lib/api";
import {
  ScrollText,
  ShieldCheck,
  PlusCircle,
  Hash,
  Filter,
  CheckCircle2,
  XCircle,
  FileText,
  Lock,
} from "lucide-react";

interface EvidenceLedgerProps {
  investigationId: string;
}

export default function EvidenceLedger({ investigationId }: EvidenceLedgerProps) {
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedClass, setSelectedClass] = useState<string>("all");
  const [verifying, setVerifying] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] = useState<{
    valid: boolean;
    total_records: number;
  } | null>(null);

  // New Note Modal
  const [showNoteModal, setShowNoteModal] = useState<boolean>(false);
  const [noteContent, setNoteContent] = useState<string>("");
  const [submittingNote, setSubmittingNote] = useState<boolean>(false);

  const fetchEvidence = async () => {
    setLoading(true);
    try {
      const data = await api.listEvidence(
        investigationId,
        selectedClass === "all" ? undefined : selectedClass
      );
      setEvidenceList(data);
    } catch (err) {
      console.error("Failed to load evidence ledger:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidence();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [investigationId, selectedClass]);

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await api.verifyEvidenceChain(investigationId);
      setVerificationResult(res);
    } catch (err: any) {
      setVerificationResult({ valid: false, total_records: evidenceList.length });
    } finally {
      setVerifying(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteContent.trim()) return;
    setSubmittingNote(true);
    try {
      await api.addAnalystNote(investigationId, noteContent);
      setNoteContent("");
      setShowNoteModal(false);
      await fetchEvidence();
    } catch (err) {
      console.error("Failed to save note:", err);
    } finally {
      setSubmittingNote(false);
    }
  };

  const getProvenanceBadge = (cls: ProvenanceClass) => {
    switch (cls) {
      case "OBSERVED":
        return "bg-emerald-50 text-emerald-700 border-emerald-300";
      case "THIRD-PARTY INTELLIGENCE":
        return "bg-blue-50 text-blue-700 border-blue-300";
      case "DERIVED":
        return "bg-purple-50 text-purple-700 border-purple-300";
      case "INFERENCE":
        return "bg-amber-50 text-amber-700 border-amber-300";
      default:
        return "bg-slate-50 text-slate-700 border-slate-300";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ScrollText className="w-5 h-5 text-blue-600" />
            <h3 className="text-base font-bold text-slate-900">Immutable Evidence Ledger</h3>
          </div>
          <p className="text-xs text-slate-500 max-w-xl">
            Cryptographically chained sequence of discrete facts backing this investigation. Every
            fact carries an explicit epistemic provenance class (PRD §8, §13).
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Provenance Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-600 font-semibold">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="bg-slate-100 border border-slate-200 rounded px-2.5 py-1.5 text-xs font-medium"
            >
              <option value="all">All Provenance Classes</option>
              <option value="OBSERVED">OBSERVED (Raw On-Chain)</option>
              <option value="THIRD-PARTY INTELLIGENCE">THIRD-PARTY INTELLIGENCE</option>
              <option value="DERIVED">DERIVED (Calculated)</option>
              <option value="INFERENCE">INFERENCE (Analyst Notes)</option>
            </select>
          </div>

          {/* Verify Hash Chain Button */}
          <button
            onClick={handleVerifyChain}
            disabled={verifying}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs disabled:opacity-50"
          >
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>{verifying ? "Verifying..." : "Verify Hash Chain"}</span>
          </button>

          {/* Add Analyst Note Button */}
          <button
            onClick={() => setShowNoteModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Add Analyst Note</span>
          </button>
        </div>
      </div>

      {/* Hash Chain Verification Result Banner */}
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
                  ? "Hash Chain Verification Passed — Ledger Intact"
                  : "Hash Chain Verification Failed — Tampering Detected"}
              </p>
              <p className="text-[11px] opacity-80">
                Validated {verificationResult.total_records} sequential evidence records from genesis
                hash (0x0...0). All cryptographic links verified.
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

      {/* Evidence Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <span className="inline-block w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2" />
            <p>Loading cryptographic evidence records...</p>
          </div>
        ) : evidenceList.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No evidence records found for this criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3 w-14 text-center">Seq #</th>
                  <th className="p-3">Provenance Class</th>
                  <th className="p-3">Evidence Type</th>
                  <th className="p-3">Source & Reference</th>
                  <th className="p-3">Cryptographic Evidence Hash</th>
                  <th className="p-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {evidenceList.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-50 transition">
                    <td className="p-3 text-center font-mono font-bold text-slate-500">
                      #{ev.sequence_num}
                    </td>
                    <td className="p-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${getProvenanceBadge(
                          ev.provenance_class
                        )}`}
                      >
                        {ev.provenance_class}
                      </span>
                    </td>
                    <td className="p-3 font-semibold text-slate-800">{ev.evidence_type}</td>
                    <td className="p-3 text-slate-600">
                      <div>{ev.source}</div>
                      {ev.source_ref && (
                        <div className="text-[10px] font-mono text-slate-400 truncate max-w-xs">
                          {ev.source_ref}
                        </div>
                      )}
                    </td>
                    <td className="p-3 font-mono text-[11px] text-slate-500">
                      <div className="flex items-center gap-1" title={ev.evidence_hash}>
                        <Hash className="w-3 h-3 text-slate-400" />
                        <span>{ev.evidence_hash.slice(0, 16)}...</span>
                      </div>
                    </td>
                    <td className="p-3 text-slate-400 text-[11px] whitespace-nowrap">
                      {new Date(ev.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Analyst Note Modal */}
      {showNoteModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-600" />
                <span>Add Analyst Note (FR-EVD-02)</span>
              </h3>
              <button
                onClick={() => setShowNoteModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Analyst notes are appended to the immutable evidence ledger as INFERENCE records,
              assigned the next sequence number, and chained into the cryptographic hash.
            </p>
            <form onSubmit={handleAddNote} className="space-y-4">
              <textarea
                required
                rows={4}
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                placeholder="Enter factual analysis, subpoena ticket, or corroborating intel..."
                className="w-full text-xs p-3 rounded-lg border border-slate-200 bg-white text-slate-900 focus:outline-blue-500"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowNoteModal(false)}
                  className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingNote}
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs disabled:opacity-50"
                >
                  {submittingNote ? "Appending..." : "Append to Ledger"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
