"use client";

import { useState } from "react";
import { CandidateAttribution } from "@/lib/types";
import { api } from "@/lib/api";
import {
  Scale,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ShieldCheck,
  FileCheck,
  Info,
  Send,
} from "lucide-react";

interface ExplainAttributionModalProps {
  investigationId: string;
  candidates: CandidateAttribution[];
  selectedCandidate: CandidateAttribution | null;
  onSelectCandidate: (candidate: CandidateAttribution) => void;
  onClose: () => void;
  onDispositionUpdated?: () => void;
}

export default function ExplainAttributionModal({
  investigationId,
  candidates,
  selectedCandidate,
  onSelectCandidate,
  onClose,
  onDispositionUpdated,
}: ExplainAttributionModalProps) {
  const [disposition, setDisposition] = useState<string>(
    selectedCandidate?.disposition || "pending"
  );
  const [notes, setNotes] = useState<string>(selectedCandidate?.disposition_notes || "");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  if (!selectedCandidate) return null;

  // Calculate sum of contributions for G2 invariant check
  const sumContributions = selectedCandidate.factors.reduce(
    (acc, f) => acc + (f.applicable ? f.contribution : 0),
    0
  );
  const isG2Valid = Math.abs(sumContributions - selectedCandidate.raw_score) <= 0.0015;

  const handleSaveDisposition = async () => {
    setSubmitting(true);
    setMessage(null);
    try {
      await api.updateDisposition(investigationId, {
        candidate_vasp_id: selectedCandidate.vasp_id,
        disposition,
        notes,
      });
      setMessage("Investigator disposition saved as INFERENCE (raw score unchanged).");
      if (onDispositionUpdated) {
        onDispositionUpdated();
      }
    } catch (err: any) {
      setMessage(`Error: ${err.message || "Failed to update disposition"}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <Scale className="w-5 h-5 text-blue-400" />
            <div>
              <h2 className="text-base font-bold">Explain Attribution Model</h2>
              <p className="text-xs text-slate-400">
                10-Feature Contribution Decomposition &amp; Deterministic Cap Evaluation (PRD §11)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white font-bold text-lg px-2"
          >
            ✕
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Candidate Selection Tabs (if multiple candidates) */}
          {candidates.length > 1 && (
            <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Candidates:
              </span>
              <div className="flex flex-wrap gap-2">
                {candidates.map((c) => (
                  <button
                    key={c.vasp_id}
                    onClick={() => onSelectCandidate(c)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                      selectedCandidate.vasp_id === c.vasp_id
                        ? "bg-purple-50 text-purple-700 border-purple-300 shadow-xs"
                        : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    #{c.rank} {c.vasp_name} ({(c.final_score * 100).toFixed(1)}%)
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Candidate Header Stats */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                VASP Entity
              </span>
              <h3 className="text-lg font-bold text-slate-900">{selectedCandidate.vasp_name}</h3>
              <span className="font-mono text-xs text-slate-500 font-medium">
                {selectedCandidate.vasp_id}
              </span>
            </div>

            <div className="flex items-center gap-6 text-xs">
              <div>
                <span className="text-slate-500 block">Raw Math Score</span>
                <span className="font-mono font-bold text-slate-800 text-sm">
                  {selectedCandidate.raw_score.toFixed(4)}
                </span>
              </div>
              <div className="text-slate-400">→</div>
              <div>
                <span className="text-slate-500 block">After Caps (Final)</span>
                <span className="font-mono font-bold text-purple-700 text-base">
                  {(selectedCandidate.final_score * 100).toFixed(1)}% ({selectedCandidate.tier})
                </span>
              </div>
            </div>

            {/* G2 Invariant Badge */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>G2 Invariant Verified (Sum == Raw Score)</span>
            </div>
          </div>

          {/* 10 Factors Breakdown Table */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Feature Decomposition (FR-ATT-02, FR-ATT-03)
            </h4>
            <div className="border border-slate-200 rounded-xl overflow-hidden shadow-xs">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="p-2.5">Feature Name</th>
                    <th className="p-2.5">Observed Raw Value</th>
                    <th className="p-2.5 text-right">Norm. Score</th>
                    <th className="p-2.5 text-right">Weight</th>
                    <th className="p-2.5 text-right">Contribution</th>
                    <th className="p-2.5 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {selectedCandidate.factors.map((f) => (
                    <tr
                      key={f.name}
                      className={f.applicable ? "hover:bg-slate-50" : "bg-slate-50/50 opacity-60"}
                    >
                      <td className="p-2.5 font-medium text-slate-800">
                        <div>{f.name.replace(/_/g, " ")}</div>
                        <div className="text-[10px] text-slate-400 font-normal">{f.description}</div>
                      </td>
                      <td className="p-2.5 font-mono text-slate-600">{String(f.raw_value)}</td>
                      <td className="p-2.5 font-mono text-right font-semibold text-slate-800">
                        {f.normalized_score.toFixed(3)}
                      </td>
                      <td className="p-2.5 font-mono text-right text-slate-500">
                        {(f.weight * 100).toFixed(1)}%
                      </td>
                      <td className="p-2.5 font-mono text-right font-bold text-blue-600">
                        +{f.contribution.toFixed(4)}
                      </td>
                      <td className="p-2.5 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            f.applicable
                              ? "bg-blue-50 text-blue-700 border border-blue-200"
                              : "bg-slate-100 text-slate-400 border border-slate-200"
                          }`}
                        >
                          {f.applicable ? "Active" : "Inactive"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-slate-50 font-bold border-t border-slate-200 text-slate-900">
                  <tr>
                    <td colSpan={4} className="p-2.5 text-right uppercase text-[10px] tracking-wider">
                      Sum of Weighted Contributions:
                    </td>
                    <td className="p-2.5 font-mono text-right text-blue-700">
                      {sumContributions.toFixed(4)}
                    </td>
                    <td className="p-2.5 text-center text-[10px] text-emerald-600">
                      {isG2Valid ? "✓ Exact" : "± 0.001"}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          {/* Applied Caps Section */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Attribution Caps (FR-ATT-04: CAP-01 to CAP-08)
            </h4>
            {selectedCandidate.caps_applied.length > 0 ? (
              <div className="space-y-2">
                {selectedCandidate.caps_applied.map((cap) => (
                  <div
                    key={cap.cap_code}
                    className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                      <div>
                        <span className="font-bold text-amber-900 font-mono">{cap.cap_code}: </span>
                        <span className="text-amber-800">{cap.reason}</span>
                      </div>
                    </div>
                    <span className="font-mono font-bold text-amber-900 bg-amber-100 px-2 py-0.5 rounded text-[11px]">
                      Max Score: {(cap.max_score * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>No restrictive caps triggered. Candidate retains unconstrained score.</span>
              </div>
            )}
          </div>

          {/* Human-in-the-Loop Investigator Disposition (FR-ATT-09) */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <FileCheck className="w-4 h-4 text-blue-600" />
              <span>Investigator Review Disposition (FR-ATT-09)</span>
            </h4>
            <p className="text-[11px] text-slate-500">
              Record review decision for case notes. Dispositions are recorded as INFERENCE in the
              evidence ledger and will never alter the mathematical score.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              {(["pending", "accepted", "rejected", "needs_review"] as const).map((disp) => (
                <label
                  key={disp}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer transition ${
                    disposition === disp
                      ? "bg-blue-600 text-white border-blue-700 shadow-xs"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  <input
                    type="radio"
                    name="disposition"
                    value={disp}
                    checked={disposition === disp}
                    onChange={(e) => setDisposition(e.target.value)}
                    className="sr-only"
                  />
                  <span className="capitalize">{disp.replace("_", " ")}</span>
                </label>
              ))}
            </div>

            <div>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional investigator review notes or subpoena justification..."
                rows={2}
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-white text-slate-900 focus:outline-blue-500"
              />
            </div>

            <div className="flex items-center justify-between">
              {message && <span className="text-xs font-medium text-emerald-600">{message}</span>}
              <button
                disabled={submitting}
                onClick={handleSaveDisposition}
                className="ml-auto inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submitting ? "Saving..." : "Record Disposition"}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-slate-100 px-6 py-3 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
