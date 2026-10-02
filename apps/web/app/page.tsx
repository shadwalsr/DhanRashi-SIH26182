"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Case,
  Investigation,
  GraphResponse,
  AttributionResponse,
  RiskAssessment,
  UserRole,
  CandidateAttribution,
} from "@/lib/types";
import { api, DEMO_USERS } from "@/lib/api";
import AuthBar from "@/components/AuthBar";
import Navigation, { NavTab } from "@/components/Navigation";
import CytoscapeGraph from "@/components/CytoscapeGraph";
import InvestigationOverview from "@/components/InvestigationOverview";
import ExplainAttributionModal from "@/components/ExplainAttributionModal";
import EvidenceLedger from "@/components/EvidenceLedger";
import NewInvestigationModal from "@/components/NewInvestigationModal";
import LiveProgressModal from "@/components/LiveProgressModal";
import VaspRegistryView from "@/components/VaspRegistryView";
import SupervisorView from "@/components/SupervisorView";
import AuditView from "@/components/AuditView";
import ProviderHealthView from "@/components/ProviderHealthView";
import {
  FolderKanban,
  Play,
  PlusCircle,
  RefreshCw,
  GitFork,
  Scale,
  ScrollText,
  FileCheck,
  Building2,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";

export default function Home() {
  const [role, setRole] = useState<UserRole>("INV");
  const [currentTab, setCurrentTab] = useState<NavTab>("cases");

  // Cases & Investigations state
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>("");
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [activeInvestigationId, setActiveInvestigationId] = useState<string | null>(null);

  // Active investigation data
  const [activeInvestigation, setActiveInvestigation] = useState<Investigation | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [attribution, setAttribution] = useState<AttributionResponse | null>(null);
  const [risk, setRisk] = useState<RiskAssessment | null>(null);
  const [loadingGraph, setLoadingGraph] = useState<boolean>(false);

  // Modals state
  const [showNewInvModal, setShowNewInvModal] = useState<boolean>(false);
  const [runningInvId, setRunningInvId] = useState<string | null>(null);
  const [showExplainModal, setShowExplainModal] = useState<boolean>(false);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateAttribution | null>(null);

  // New Case modal
  const [showNewCaseModal, setShowNewCaseModal] = useState<boolean>(false);
  const [newCaseRef, setNewCaseRef] = useState<string>("");
  const [newCaseTitle, setNewCaseTitle] = useState<string>("");

  // Initialize Auth
  useEffect(() => {
    api.login(role).catch(() => {});
  }, [role]);

  // Load initial Cases
  const loadCases = useCallback(async () => {
    try {
      const casesData = await api.listCases();
      setCases(casesData);
      if (casesData.length > 0 && !selectedCaseId) {
        setSelectedCaseId(casesData[0].id);
      }
    } catch (err) {
      console.error("Failed to load cases:", err);
    }
  }, [selectedCaseId]);

  useEffect(() => {
    loadCases();
  }, [loadCases]);

  // Load Investigations when selectedCaseId changes
  const loadInvestigations = useCallback(async () => {
    if (!selectedCaseId) return;
    try {
      const invs = await api.listInvestigations(selectedCaseId);
      setInvestigations(invs);
      if (invs.length > 0 && !activeInvestigationId) {
        setActiveInvestigationId(invs[0].id);
      }
    } catch (err) {
      console.error("Failed to load investigations:", err);
    }
  }, [selectedCaseId, activeInvestigationId]);

  useEffect(() => {
    loadInvestigations();
  }, [loadInvestigations]);

  // Load Investigation Details when activeInvestigationId changes
  const loadInvestigationDetails = useCallback(async () => {
    if (!activeInvestigationId) return;
    setLoadingGraph(true);
    try {
      const [inv, graph, attr, riskData] = await Promise.all([
        api.getInvestigation(activeInvestigationId),
        api.getInvestigationGraph(activeInvestigationId).catch(() => null),
        api.getAttribution(activeInvestigationId).catch(() => null),
        api.getRiskAssessment(activeInvestigationId).catch(() => null),
      ]);
      setActiveInvestigation(inv);
      setGraphData(graph);
      setAttribution(attr);
      setRisk(riskData);
      if (attr?.top_candidate) {
        setSelectedCandidate(attr.top_candidate);
      }
    } catch (err) {
      console.error("Failed to load investigation details:", err);
    } finally {
      setLoadingGraph(false);
    }
  }, [activeInvestigationId]);

  useEffect(() => {
    loadInvestigationDetails();
  }, [loadInvestigationDetails]);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCaseRef.trim() || !newCaseTitle.trim()) return;
    try {
      const created = await api.createCase({
        reference_number: newCaseRef.trim(),
        title: newCaseTitle.trim(),
      });
      setShowNewCaseModal(false);
      setNewCaseRef("");
      setNewCaseTitle("");
      await loadCases();
      setSelectedCaseId(created.id);
    } catch (err) {
      console.error("Failed to create case:", err);
    }
  };

  const handleRunInvestigation = async (invId: string) => {
    try {
      await api.runInvestigation(invId);
      setRunningInvId(invId);
    } catch (err) {
      console.error("Failed to start run:", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-50 min-h-screen">
      {/* Role-Aware Auth Bar (Persona Switcher) */}
      <AuthBar currentRole={role} onRoleChange={(newRole) => setRole(newRole)} />

      {/* Main Navigation Bar */}
      <Navigation
        currentTab={currentTab}
        onTabChange={(tab) => setCurrentTab(tab)}
        userRole={role}
        activeInvestigationId={activeInvestigationId}
      />

      {/* Case & Investigation Selector Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px]">
              Active Case:
            </span>
            <select
              value={selectedCaseId}
              onChange={(e) => {
                setSelectedCaseId(e.target.value);
                setActiveInvestigationId(null);
              }}
              className="bg-slate-100 border border-slate-200 rounded px-2.5 py-1 text-slate-900 font-semibold"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.reference_number} · {c.title}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px]">
              Investigation:
            </span>
            <select
              value={activeInvestigationId || ""}
              onChange={(e) => setActiveInvestigationId(e.target.value || null)}
              className="bg-slate-100 border border-slate-200 rounded px-2.5 py-1 text-slate-900 font-mono font-medium max-w-xs truncate"
            >
              {investigations.length === 0 && <option value="">No investigations</option>}
              {investigations.map((inv) => (
                <option key={inv.id} value={inv.id}>
                  [{inv.blockchain.toUpperCase()}] {inv.wallet_address.slice(0, 10)}... (
                  {inv.state})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {["INV", "FIA", "SUP"].includes(role) && (
            <>
              <button
                onClick={() => setShowNewCaseModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold border border-slate-200"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>New Case</span>
              </button>
              <button
                onClick={() => setShowNewInvModal(true)}
                className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold shadow-xs"
              >
                <Play className="w-3 h-3 fill-current" />
                <span>New Investigation</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main View Area */}
      <div className="p-6 max-w-7xl mx-auto w-full flex-1">
        {/* Tab 1: Cases & Investigations */}
        {currentTab === "cases" && (
          <div className="space-y-6">
            {/* Active Investigation Card Deck */}
            {activeInvestigation && (
              <InvestigationOverview
                investigation={activeInvestigation}
                attribution={attribution}
                risk={risk}
                onOpenExplain={() => setShowExplainModal(true)}
              />
            )}

            {/* Investigations List */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
              <div className="bg-slate-50 px-5 py-3 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FolderKanban className="w-4 h-4 text-blue-600" />
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Investigations in this Case ({investigations.length})
                  </h3>
                </div>
              </div>

              {investigations.length === 0 ? (
                <div className="p-12 text-center text-slate-400 text-xs">
                  No investigations launched for this case yet. Click &quot;New Investigation&quot; to
                  start tracing an unknown wallet address.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                      <tr>
                        <th className="p-3">Seed Wallet</th>
                        <th className="p-3">Blockchain</th>
                        <th className="p-3">Depth Bound</th>
                        <th className="p-3">Execution State</th>
                        <th className="p-3">Nodes / Edges</th>
                        <th className="p-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-medium">
                      {investigations.map((inv) => (
                        <tr
                          key={inv.id}
                          className={`hover:bg-slate-50 transition cursor-pointer ${
                            activeInvestigationId === inv.id ? "bg-blue-50/40" : ""
                          }`}
                          onClick={() => setActiveInvestigationId(inv.id)}
                        >
                          <td className="p-3 font-mono font-bold text-slate-900 select-all">
                            {inv.wallet_address}
                          </td>
                          <td className="p-3 capitalize font-semibold text-slate-700">
                            {inv.blockchain}
                          </td>
                          <td className="p-3 font-mono text-slate-600">{inv.depth} hops</td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                                inv.state === "COMPLETED"
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                  : inv.state === "PARTIAL"
                                  ? "bg-amber-50 text-amber-700 border-amber-200"
                                  : "bg-blue-50 text-blue-700 border-blue-200"
                              }`}
                            >
                              {inv.state}
                            </span>
                          </td>
                          <td className="p-3 font-mono text-slate-500">
                            {inv.node_count || 0} / {inv.edge_count || 0}
                          </td>
                          <td className="p-3 text-right space-x-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setActiveInvestigationId(inv.id);
                                setCurrentTab("graph");
                              }}
                              className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold"
                            >
                              View Graph
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRunInvestigation(inv.id);
                              }}
                              className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold"
                            >
                              Re-Run
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Cytoscape Graph Explorer */}
        {currentTab === "graph" && (
          <div className="space-y-4">
            <CytoscapeGraph graphData={graphData} loading={loadingGraph} />
          </div>
        )}

        {/* Tab 3: Attribution Engine & Candidate Comparison */}
        {currentTab === "attribution" && (
          <div className="space-y-6">
            {activeInvestigation && (
              <InvestigationOverview
                investigation={activeInvestigation}
                attribution={attribution}
                risk={risk}
                onOpenExplain={() => setShowExplainModal(true)}
              />
            )}

            {/* Candidates Comparison Table */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
              <div className="bg-slate-50 px-5 py-3 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Scale className="w-4 h-4 text-purple-600" />
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Candidate VASPs Ranked by 10-Feature Attribution Model
                  </h3>
                </div>
                <button
                  onClick={() => setShowExplainModal(true)}
                  className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold shadow-xs"
                >
                  Explain Attribution (FR-ATT-07)
                </button>
              </div>

              {!attribution || attribution.candidates.length === 0 ? (
                <div className="p-12 text-center text-slate-400 text-xs">
                  No attributed VASP candidates discovered for this flow path.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                      <tr>
                        <th className="p-3 w-12 text-center">Rank</th>
                        <th className="p-3">Candidate VASP</th>
                        <th className="p-3">VASP ID</th>
                        <th className="p-3 text-right">Raw Score</th>
                        <th className="p-3 text-right">Final Score</th>
                        <th className="p-3">Confidence Tier</th>
                        <th className="p-3">Investigator Disposition</th>
                        <th className="p-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-medium">
                      {attribution.candidates.map((c) => (
                        <tr key={c.vasp_id} className="hover:bg-slate-50">
                          <td className="p-3 text-center font-bold text-slate-400">#{c.rank}</td>
                          <td className="p-3 font-bold text-slate-900">{c.vasp_name}</td>
                          <td className="p-3 font-mono text-purple-700">{c.vasp_id}</td>
                          <td className="p-3 font-mono text-right text-slate-500">
                            {c.raw_score.toFixed(4)}
                          </td>
                          <td className="p-3 font-mono text-right font-bold text-slate-900">
                            {(c.final_score * 100).toFixed(1)}%
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                                c.tier === "HIGH"
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                  : c.tier === "MEDIUM"
                                  ? "bg-amber-50 text-amber-700 border-amber-200"
                                  : "bg-slate-100 text-slate-700 border-slate-200"
                              }`}
                            >
                              {c.tier}
                            </span>
                          </td>
                          <td className="p-3">
                            <span className="font-mono text-[10px] uppercase font-semibold text-slate-600">
                              {c.disposition || "pending"}
                            </span>
                          </td>
                          <td className="p-3 text-right">
                            <button
                              onClick={() => {
                                setSelectedCandidate(c);
                                setShowExplainModal(true);
                              }}
                              className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold"
                            >
                              Decompose
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 4: Evidence Ledger */}
        {currentTab === "evidence" && activeInvestigationId && (
          <EvidenceLedger investigationId={activeInvestigationId} />
        )}

        {/* Tab 5: VASP Registry & Conflicts (Journey J2) */}
        {currentTab === "registry" && (
          <VaspRegistryView userRole={role} onRefreshNeeded={loadInvestigationDetails} />
        )}

        {/* Tab 6: Approvals & SAHYOG Mock (Journey J3) */}
        {currentTab === "sahyog" && (
          <SupervisorView
            userRole={role}
            currentUserId={DEMO_USERS[role].email}
            onRefreshNeeded={loadInvestigationDetails}
          />
        )}

        {/* Tab 7: Audit Trail & Hash-Chain Verification (Journey J4) */}
        {currentTab === "audit" && <AuditView userRole={role} />}

        {/* Tab 8: System & Provider Health (Journey J6) */}
        {currentTab === "health" && <ProviderHealthView />}
      </div>

      {/* New Investigation Modal */}
      {showNewInvModal && (
        <NewInvestigationModal
          cases={cases}
          selectedCaseId={selectedCaseId}
          onClose={() => setShowNewInvModal(false)}
          onCreated={(inv) => {
            setActiveInvestigationId(inv.id);
            setRunningInvId(inv.id);
            loadInvestigations();
          }}
        />
      )}

      {/* Live Progress Stepper Modal */}
      {runningInvId && (
        <LiveProgressModal
          investigationId={runningInvId}
          onFinished={(inv) => {
            setRunningInvId(null);
            loadInvestigationDetails();
            loadInvestigations();
          }}
          onClose={() => setRunningInvId(null)}
        />
      )}

      {/* Explain Attribution Modal */}
      {showExplainModal && activeInvestigationId && attribution && (
        <ExplainAttributionModal
          investigationId={activeInvestigationId}
          candidates={attribution.candidates}
          selectedCandidate={selectedCandidate || attribution.top_candidate || null}
          onSelectCandidate={(c) => setSelectedCandidate(c)}
          onClose={() => setShowExplainModal(false)}
          onDispositionUpdated={loadInvestigationDetails}
        />
      )}

      {/* New Case Modal */}
      {showNewCaseModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-sm font-bold text-slate-900">Create New Investigation Case</h3>
              <button
                onClick={() => setShowNewCaseModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateCase} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Case Reference Number
                </label>
                <input
                  required
                  type="text"
                  value={newCaseRef}
                  onChange={(e) => setNewCaseRef(e.target.value)}
                  placeholder="e.g. CASE-2026-0042"
                  className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-slate-900 font-mono"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Case Title
                </label>
                <input
                  required
                  type="text"
                  value={newCaseTitle}
                  onChange={(e) => setNewCaseTitle(e.target.value)}
                  placeholder="e.g. Operation CrypticFlow - Ransomware Laundering"
                  className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-slate-900"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowNewCaseModal(false)}
                  className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold shadow-xs"
                >
                  Create Case
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
