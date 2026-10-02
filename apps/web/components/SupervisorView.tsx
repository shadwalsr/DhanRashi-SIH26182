"use client";

import { useEffect, useState } from "react";
import { Report, SahyogRequest, UserRole } from "@/lib/types";
import { api, DEMO_USERS } from "@/lib/api";
import {
  ShieldAlert,
  FileCheck,
  Send,
  AlertCircle,
  CheckCircle2,
  Clock,
  Building,
  UserCheck,
} from "lucide-react";

interface SupervisorViewProps {
  userRole: UserRole;
  currentUserId?: string;
  onRefreshNeeded?: () => void;
}

export default function SupervisorView({ userRole, currentUserId, onRefreshNeeded }: SupervisorViewProps) {
  const [reports, setReports] = useState<Report[]>([]);
  const [sahyogRequests, setSahyogRequests] = useState<SahyogRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Approval Dialog
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [approvalComment, setApprovalComment] = useState<string>("");
  const [submittingApproval, setSubmittingApproval] = useState<boolean>(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const canApprove = userRole === "SUP";

  const fetchData = async () => {
    setLoading(true);
    try {
      const [reportsData, sahyogData] = await Promise.all([
        api.listReports(),
        api.listSahyogRequests(),
      ]);
      setReports(reportsData);
      setSahyogRequests(sahyogData);
    } catch (err) {
      console.error("Failed to fetch reports/sahyog:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApprove = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReport) return;

    // Separation of duties rule: creator cannot approve
    if (selectedReport.created_by === currentUserId) {
      setActionMsg("Separation of Duties Violation: You cannot approve a report that you generated.");
      return;
    }

    setSubmittingApproval(true);
    setActionMsg(null);
    try {
      await api.approveReport(selectedReport.id, approvalComment);
      setActionMsg(`Report ${selectedReport.title} successfully APPROVED.`);
      setSelectedReport(null);
      setApprovalComment("");
      await fetchData();
      if (onRefreshNeeded) onRefreshNeeded();
    } catch (err: any) {
      setActionMsg(`Approval Error: ${err.message}`);
    } finally {
      setSubmittingApproval(false);
    }
  };

  const handleSubmitSahyog = async (requestId: string) => {
    try {
      await api.submitSahyogRequest(requestId);
      setActionMsg("Mock SAHYOG Request submitted. Status transitioned to SUBMITTED → ACKNOWLEDGED.");
      await fetchData();
      if (onRefreshNeeded) onRefreshNeeded();
    } catch (err: any) {
      setActionMsg(`Submission Error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Prominent Mandatory Mock Banner (PRD Task 10) */}
      <div className="bg-rose-500 text-white font-bold px-5 py-3 rounded-xl border border-rose-600 shadow-sm flex items-center gap-3 text-xs tracking-wide">
        <ShieldAlert className="w-5 h-5 flex-shrink-0 animate-pulse text-amber-200" />
        <div>
          <span className="uppercase tracking-wider font-black">
            MOCK DISCLOSURE SYSTEM · NOT TRANSMITTED TO ANY AUTHORITY
          </span>
          <p className="text-[11px] font-normal text-rose-100 mt-0.5">
            Demonstration mode only. No actual legal orders, Section 91 notices, or freezing
            directives are communicated to external Virtual Asset Service Providers or regulatory
            agencies.
          </p>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 bg-blue-50 text-blue-800 border border-blue-200 rounded-lg text-xs font-semibold flex items-center justify-between">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)}>✕</button>
        </div>
      )}

      {/* Supervisor Review Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <UserCheck className="w-5 h-5 text-amber-600" />
            <h3 className="text-base font-bold text-slate-900">
              Supervisor Oversight &amp; SAHYOG Pipeline (Journey J3)
            </h3>
          </div>
          <p className="text-xs text-slate-500 max-w-xl">
            Review investigator-generated attribution reports, enforce separation of duties, and
            authorize mock statutory disclosure bundles for Indian FIU / law enforcement.
          </p>
        </div>

        <div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold font-mono border ${
              canApprove
                ? "bg-amber-50 text-amber-800 border-amber-300"
                : "bg-slate-100 text-slate-500 border-slate-200"
            }`}
          >
            Role: {userRole} ({canApprove ? "Authorized to Approve" : "Approval Restricted to SUP"})
          </span>
        </div>
      </div>

      {/* Reports Awaiting Approval */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="bg-slate-50 px-5 py-3 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-blue-600" />
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Attribution Reports ({reports.length})
            </h4>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400 text-xs">Loading reports...</div>
        ) : reports.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No reports generated yet. Investigators can generate PDF reports from the overview tab.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3">Report Title</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Author (Generated By)</th>
                  <th className="p-3">Approval Status</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {reports.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50">
                    <td className="p-3 font-semibold text-slate-900">{r.title}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                          r.status === "APPROVED"
                            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                            : r.status === "PENDING_APPROVAL"
                            ? "bg-amber-50 text-amber-700 border-amber-200"
                            : "bg-slate-100 text-slate-600 border-slate-200"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="p-3 text-slate-600 font-mono text-[11px]">
                      {r.created_by_email || r.created_by}
                    </td>
                    <td className="p-3 text-slate-600">
                      {r.approved_by_email ? (
                        <span className="text-emerald-700 font-medium">
                          Approved by {r.approved_by_email}
                        </span>
                      ) : (
                        <span className="text-slate-400">Awaiting supervisor review</span>
                      )}
                    </td>
                    <td className="p-3 text-right">
                      {r.status === "PENDING_APPROVAL" && (
                        <button
                          disabled={!canApprove}
                          onClick={() => setSelectedReport(r)}
                          className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs font-semibold shadow-xs disabled:opacity-40"
                        >
                          Review &amp; Approve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* SAHYOG Requests Pipeline */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="bg-slate-50 px-5 py-3 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Building className="w-4 h-4 text-purple-600" />
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              SAHYOG Lawful Disclosure Bundles ({sahyogRequests.length})
            </h4>
          </div>
        </div>

        {sahyogRequests.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No SAHYOG disclosure requests created yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3">Reference #</th>
                  <th className="p-3">Target VASP</th>
                  <th className="p-3">Workflow State</th>
                  <th className="p-3">Data Classification</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {sahyogRequests.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="p-3 font-mono font-bold text-slate-900">
                      {s.reference_number}
                    </td>
                    <td className="p-3 font-semibold text-purple-700">
                      {s.target_vasp_name} ({s.target_vasp_id})
                    </td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                          s.status === "ACKNOWLEDGED"
                            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                            : s.status === "SUBMITTED"
                            ? "bg-blue-50 text-blue-700 border-blue-200"
                            : "bg-amber-50 text-amber-700 border-amber-200"
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-bold font-mono">
                        MOCK TEST RUN
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      {s.status === "DRAFT" && (
                        <button
                          disabled={!canApprove}
                          onClick={() => handleSubmitSahyog(s.id)}
                          className="inline-flex items-center gap-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold shadow-xs disabled:opacity-40"
                        >
                          <Send className="w-3 h-3" />
                          <span>Submit Mock</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Report Approval Dialog */}
      {selectedReport && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-sm font-bold text-slate-900">
                Supervisor Report Approval (FR-RPT-04)
              </h3>
              <button
                onClick={() => setSelectedReport(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="bg-amber-50 p-3 rounded-lg border border-amber-200 text-xs text-amber-900 space-y-1">
              <p className="font-bold flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                <span>Separation of Duties Verification</span>
              </p>
              <p>
                Report generated by: <strong className="font-mono">{selectedReport.created_by_email || selectedReport.created_by}</strong>.
                As supervisor ({DEMO_USERS[userRole].name}), your sign-off verifies evidence completeness and limitations disclosure.
              </p>
            </div>

            <form onSubmit={handleApprove} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Supervisor Review Comment (Audited)
                </label>
                <textarea
                  required
                  rows={3}
                  value={approvalComment}
                  onChange={(e) => setApprovalComment(e.target.value)}
                  placeholder="Record formal supervisory review comment and statutory clearance..."
                  className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-slate-900 focus:outline-blue-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setSelectedReport(null)}
                  className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingApproval || !approvalComment.trim()}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold shadow-xs disabled:opacity-50"
                >
                  {submittingApproval ? "Approving..." : "Approve Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
