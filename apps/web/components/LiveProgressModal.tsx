"use client";

import { useEffect, useState } from "react";
import { InvestigationState, Investigation } from "@/lib/types";
import { api } from "@/lib/api";
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  Play,
  RotateCw,
  AlertCircle,
} from "lucide-react";

interface LiveProgressModalProps {
  investigationId: string;
  onFinished: (investigation: Investigation) => void;
  onClose: () => void;
}

const STAGES: InvestigationState[] = [
  "CREATED",
  "VALIDATING",
  "FETCHING_DATA",
  "TRACING",
  "ANALYZING",
  "COMPLETED",
];

export default function LiveProgressModal({
  investigationId,
  onFinished,
  onClose,
}: LiveProgressModalProps) {
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [pollCount, setPollCount] = useState<number>(0);

  useEffect(() => {
    let interval: any = null;

    const pollStatus = async () => {
      try {
        const inv = await api.getInvestigation(investigationId);
        setInvestigation(inv);
        setPollCount((prev) => prev + 1);

        if (["COMPLETED", "PARTIAL", "FAILED", "CANCELLED"].includes(inv.state)) {
          clearInterval(interval);
          onFinished(inv);
        }
      } catch (err) {
        console.error("Polling status failed:", err);
      }
    };

    pollStatus();
    interval = setInterval(pollStatus, 1500);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [investigationId]);

  const currentState = investigation?.state || "CREATED";
  const currentIndex = STAGES.indexOf(currentState);

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-xl w-full p-6 space-y-6 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Live Investigation Progress
            </h3>
            <p className="text-xs text-slate-500 font-mono">
              Investigation ID: {investigationId.slice(0, 18)}...
            </p>
          </div>
          {["COMPLETED", "PARTIAL", "FAILED"].includes(currentState) && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 font-bold"
            >
              ✕
            </button>
          )}
        </div>

        {/* Stepper Display */}
        <div className="space-y-3">
          {STAGES.map((stage, idx) => {
            const isDone = currentIndex > idx || currentState === "COMPLETED";
            const isCurrent = currentState === stage;
            const isPending = currentIndex < idx && currentState !== "COMPLETED";

            return (
              <div
                key={stage}
                className={`flex items-center gap-3 p-3 rounded-xl border text-xs font-semibold transition ${
                  isCurrent
                    ? "bg-blue-50 border-blue-300 text-blue-900 shadow-xs"
                    : isDone
                    ? "bg-emerald-50/60 border-emerald-200 text-emerald-800"
                    : "bg-slate-50/60 border-slate-200 text-slate-400"
                }`}
              >
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                ) : isCurrent ? (
                  <RotateCw className="w-4 h-4 text-blue-600 animate-spin flex-shrink-0" />
                ) : (
                  <Clock className="w-4 h-4 text-slate-300 flex-shrink-0" />
                )}
                <div className="flex-1 flex justify-between items-center">
                  <span>{stage.replace(/_/g, " ")}</span>
                  {isCurrent && (
                    <span className="text-[10px] text-blue-600 uppercase font-mono">
                      Executing...
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Partial State Banner (Journey J5) */}
        {currentState === "PARTIAL" && (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 space-y-1">
            <div className="flex items-center gap-1.5 font-bold">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Investigation Returned PARTIAL Results (Journey J5)</span>
            </div>
            <p className="text-amber-800">
              {investigation?.partial_reason ||
                "Branch exploration halted due to explosion caps or provider rate bounds. Traced subtrees are preserved and attributed with CAP-06."}
            </p>
          </div>
        )}

        {/* Live Metrics */}
        {investigation && (
          <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
            <div>
              <span className="text-slate-400 text-[10px] uppercase block">Traced Graph:</span>
              <span className="font-mono font-bold text-slate-800">
                {investigation.node_count || 0} nodes · {investigation.edge_count || 0} edges
              </span>
            </div>
            <div>
              <span className="text-slate-400 text-[10px] uppercase block">Depth Boundary:</span>
              <span className="font-mono font-bold text-slate-800">
                {investigation.depth} hops max
              </span>
            </div>
          </div>
        )}

        {/* Done Action */}
        {["COMPLETED", "PARTIAL", "FAILED"].includes(currentState) && (
          <div className="flex justify-end pt-2 border-t border-slate-100">
            <button
              onClick={onClose}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs"
            >
              Open Investigation Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
