"use client";

import { AttributionResponse, RiskAssessment, Investigation } from "@/lib/types";
import {
  Building2,
  ShieldCheck,
  Flame,
  PieChart,
  AlertTriangle,
  ArrowUpRight,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";

interface InvestigationOverviewProps {
  investigation: Investigation;
  attribution: AttributionResponse | null;
  risk: RiskAssessment | null;
  onOpenExplain: () => void;
}

export default function InvestigationOverview({
  investigation,
  attribution,
  risk,
  onOpenExplain,
}: InvestigationOverviewProps) {
  const topCandidate = attribution?.top_candidate;

  const getTierColor = (tier?: string) => {
    switch (tier) {
      case "HIGH":
        return "bg-emerald-50 text-emerald-700 border-emerald-300";
      case "MEDIUM":
        return "bg-amber-50 text-amber-700 border-amber-300";
      case "LOW":
        return "bg-slate-100 text-slate-700 border-slate-300";
      default:
        return "bg-rose-50 text-rose-700 border-rose-300";
    }
  };

  const getRiskColor = (tier?: string) => {
    switch (tier) {
      case "SEVERE":
        return "bg-rose-100 text-rose-800 border-rose-400";
      case "HIGH":
        return "bg-rose-50 text-rose-700 border-rose-300";
      case "MEDIUM":
        return "bg-amber-50 text-amber-700 border-amber-300";
      default:
        return "bg-emerald-50 text-emerald-700 border-emerald-300";
    }
  };

  return (
    <div className="space-y-6">
      {/* 4 Separate Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Top Candidate VASP */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Top Candidate VASP
              </span>
              <Building2 className="w-4 h-4 text-purple-600" />
            </div>
            {topCandidate ? (
              <div>
                <h3 className="text-xl font-bold text-slate-900 tracking-tight">
                  {topCandidate.vasp_name}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-mono text-xs text-slate-500 font-medium">
                    {topCandidate.vasp_id}
                  </span>
                  {attribution.competing_candidates && (
                    <span className="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-semibold">
                      Competing (Margin &lt; 0.15)
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-sm text-slate-400 py-2">No candidate identified</div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Candidate Score:</span>
            <span className="font-mono font-bold text-slate-900 text-sm">
              {topCandidate ? (topCandidate.final_score * 100).toFixed(1) + "%" : "0.0%"}
            </span>
          </div>
        </div>

        {/* Card 2: Attribution Tier (Explainable Multi-Factor) */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Attribution Tier
              </span>
              <ShieldCheck className="w-4 h-4 text-blue-600" />
            </div>
            <div className="mt-1">
              <span
                className={`inline-block px-3 py-1 rounded-md text-sm font-bold border tracking-wide uppercase ${getTierColor(
                  topCandidate?.tier
                )}`}
              >
                {topCandidate?.tier || "INSUFFICIENT"} CONFIDENCE
              </span>
              <p className="text-xs text-slate-500 mt-2">
                Evaluated from 10 explainable features with deterministic cap filters (CAP-01..08).
              </p>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <button
              onClick={onOpenExplain}
              className="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1"
            >
              <span>Explain Attribution</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
            <span className="text-slate-400">10 Features</span>
          </div>
        </div>

        {/* Card 3: Independent Risk Score & Tier (FR-RISK-01..04) */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Risk Tier (Transit Trail)
              </span>
              <Flame className="w-4 h-4 text-rose-600" />
            </div>
            <div className="mt-1">
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900">
                  {risk?.risk_score !== undefined ? risk.risk_score : "--"}
                </span>
                <span className="text-xs text-slate-400 font-semibold">/ 100</span>
                <span
                  className={`ml-auto px-2.5 py-0.5 rounded text-xs font-bold border uppercase ${getRiskColor(
                    risk?.risk_tier
                  )}`}
                >
                  {risk?.risk_tier || "LOW"}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Laundering signals on flow transit (Mixers, Peeling, Rapid hops).
              </p>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Independent of VASP (AT-12)</span>
            <span className="font-semibold text-rose-600">
              {risk?.signals.filter((s) => s.triggered).length || 0} Flagged
            </span>
          </div>
        </div>

        {/* Card 4: Flow Coverage & Tracing Bounds */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Graph Coverage
              </span>
              <PieChart className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="mt-1 space-y-1">
              <div className="flex justify-between text-xs text-slate-600">
                <span>Depth Traversed:</span>
                <span className="font-semibold text-slate-900 font-mono">
                  {investigation.depth} Hops
                </span>
              </div>
              <div className="flex justify-between text-xs text-slate-600">
                <span>Traced Nodes / Edges:</span>
                <span className="font-semibold text-slate-900 font-mono">
                  {investigation.node_count || 0} nodes / {investigation.edge_count || 0} edges
                </span>
              </div>
              <div className="flex justify-between text-xs text-slate-600">
                <span>Execution State:</span>
                <span
                  className={`font-semibold font-mono ${
                    investigation.state === "COMPLETED"
                      ? "text-emerald-600"
                      : investigation.state === "PARTIAL"
                      ? "text-amber-600"
                      : "text-blue-600"
                  }`}
                >
                  {investigation.state}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400">
            Chain: <span className="capitalize font-semibold text-slate-700">{investigation.blockchain}</span>
          </div>
        </div>
      </div>

      {/* Disclaimers & Limitations Banner (PRD §10.3, §10.4) */}
      <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 flex items-start gap-3 text-xs text-amber-900">
        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold">Investigative Lead Disclaimer (Non-Conclusive Attribution)</p>
          <p className="text-amber-800 leading-relaxed">
            Attribution scores represent mathematical correlation over observed blockchain topologies and
            intelligence registries. They are not legal proof of wallet ownership or criminal culpability.
            Scores below 0.40 must not be used as the sole basis for statutory disclosure requests.
          </p>
          {topCandidate?.limitations && topCandidate.limitations.length > 0 && (
            <div className="mt-2 pt-2 border-t border-amber-200/60">
              <span className="font-semibold block mb-0.5">Active Candidate Limitations:</span>
              <ul className="list-disc pl-4 space-y-0.5 text-amber-800">
                {topCandidate.limitations.map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
