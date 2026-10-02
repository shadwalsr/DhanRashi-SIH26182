"use client";

import { useState } from "react";
import { Case, Investigation } from "@/lib/types";
import { validateAddress, validateDepth } from "@/lib/validation";
import { api } from "@/lib/api";
import {
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Play,
} from "lucide-react";

interface NewInvestigationModalProps {
  cases: Case[];
  selectedCaseId?: string;
  onClose: () => void;
  onCreated: (investigation: Investigation) => void;
}

export const DEMO_PRESETS = [
  {
    name: "Case 1: Direct Clean Deposit",
    chain: "ethereum",
    address: "0x1111111111111111111111111111111111111111",
    depth: 2,
    desc: "Single direct transfer reaching Binance deposit address.",
  },
  {
    name: "Case 2: 5% Hop-1 vs 88% Hop-3 (Ranking Invariant)",
    chain: "ethereum",
    address: "0x2222222222222222222222222222222222222222",
    depth: 3,
    desc: "Proves nearest VASP is not shortest path: hop 3 with 88% outranks hop 1 with 5%.",
  },
  {
    name: "Case 3: Conflicting Registry Labels",
    chain: "ethereum",
    address: "0x3333333333333333333333333333333333333333",
    depth: 2,
    desc: "Multiple intelligence sources dispute entity attribution (triggers CAP-04).",
  },
  {
    name: "Case 4: Mixer & Peel Chain (Risk 72 / HIGH)",
    chain: "ethereum",
    address: "0x4444444444444444444444444444444444444444",
    depth: 4,
    desc: "Mixer interaction (30) + Peel chain (24) + Rapid movement (18) = 72 HIGH.",
  },
  {
    name: "Case 5: Bridge Then Deposit (Cross-Chain)",
    chain: "ethereum",
    address: "0x5555555555555555555555555555555555555555",
    depth: 3,
    desc: "Funds bridge from Ethereum to Polygon and deposit into Kraken.",
  },
];

export default function NewInvestigationModal({
  cases,
  selectedCaseId,
  onClose,
  onCreated,
}: NewInvestigationModalProps) {
  const [caseId, setCaseId] = useState<string>(
    selectedCaseId || (cases[0]?.id ? cases[0].id : "")
  );
  const [chain, setChain] = useState<string>("ethereum");
  const [address, setAddress] = useState<string>("");
  const [depth, setDepth] = useState<number>(3);
  const [minUsd, setMinUsd] = useState<number>(100);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Real-time instant validation
  const validation = validateAddress(address, chain);
  const depthWarning = validateDepth(depth);

  const handleApplyPreset = (preset: (typeof DEMO_PRESETS)[0]) => {
    setChain(preset.chain);
    setAddress(preset.address);
    setDepth(preset.depth);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validation.valid) return;
    if (!caseId) {
      setError("Please select or create a Case first.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const inv = await api.createInvestigation({
        case_id: caseId,
        wallet_address: address.trim(),
        blockchain: chain,
        depth: depth,
        min_usd_threshold: minUsd,
      });

      // Automatically queue and run
      await api.runInvestigation(inv.id);
      onCreated(inv);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to start investigation");
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-150">
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
          <div>
            <h2 className="text-base font-bold">New Investigation</h2>
            <p className="text-xs text-slate-400">
              Submit unknown seed wallet to discover flow paths and attribute destination VASPs
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white font-bold text-lg px-2"
          >
            ✕
          </button>
        </div>

        {/* Demo Preset Pills */}
        <div className="p-6 bg-slate-50 border-b border-slate-200">
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700 uppercase tracking-wider mb-2.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span>SIH26182 Demo Scenarios (Pre-Seeded Fixtures)</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {DEMO_PRESETS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplyPreset(p)}
                className="text-left p-2.5 bg-white border border-slate-200 rounded-lg hover:border-blue-400 hover:bg-blue-50/30 transition text-xs group"
              >
                <div className="font-semibold text-slate-800 group-hover:text-blue-700">
                  {p.name}
                </div>
                <div className="text-[11px] text-slate-500 truncate mt-0.5">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 font-medium">
              {error}
            </div>
          )}

          {/* Case Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Associated Case
            </label>
            <select
              required
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-white text-slate-900 font-medium"
            >
              {cases.length === 0 && <option value="">No cases found</option>}
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.reference_number}: {c.title}
                </option>
              ))}
            </select>
          </div>

          {/* Blockchain & Depth Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Blockchain
              </label>
              <select
                value={chain}
                onChange={(e) => setChain(e.target.value)}
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-white text-slate-900 font-semibold capitalize"
              >
                <option value="ethereum">Ethereum (EVM)</option>
                <option value="polygon">Polygon (EVM)</option>
                <option value="tron">Tron (TRC-20)</option>
                <option value="bnb_chain">BNB Chain (EVM)</option>
                <option value="bitcoin">Bitcoin (Stub P2)</option>
                <option value="solana">Solana (Stub P2)</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Depth Hops
                </label>
                <span className="font-mono text-xs font-bold text-blue-600">{depth} hops</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Min USD Filter
              </label>
              <input
                type="number"
                min="0"
                step="50"
                value={minUsd}
                onChange={(e) => setMinUsd(Number(e.target.value))}
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-white text-slate-900 font-mono"
              />
            </div>
          </div>

          {/* Depth Warning */}
          {depthWarning.warning && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2 text-xs text-amber-800">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <span>{depthWarning.warning}</span>
            </div>
          )}

          {/* Seed Wallet Address */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Unknown Seed Wallet Address
              </label>
              {address && (
                <span className="flex items-center gap-1 text-[11px]">
                  {validation.valid ? (
                    <span className="text-emerald-600 font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Valid Format
                    </span>
                  ) : (
                    <span className="text-rose-600 font-semibold flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" /> {validation.error}
                    </span>
                  )}
                </span>
              )}
            </div>
            <input
              required
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="e.g. 0x1111111111111111111111111111111111111111 or Tron T..."
              className={`w-full text-xs font-mono p-3 rounded-lg border bg-white text-slate-900 focus:outline-blue-500 ${
                address && !validation.valid
                  ? "border-rose-400 bg-rose-50/20"
                  : "border-slate-200"
              }`}
            />
          </div>

          {/* Footer Submit */}
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || (Boolean(address) && !validation.valid)}
              className="inline-flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{submitting ? "Launching Engine..." : "Launch Investigation"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
