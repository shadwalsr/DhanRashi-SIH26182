"use client";

import React, { useState } from "react";

export default function SettingsView() {
  const [flowWeight, setFlowWeight] = useState(0.70);
  const [tempWeight, setTempWeight] = useState(0.15);
  const [clusterWeight, setClusterWeight] = useState(0.10);
  const [hopPenalty, setHopPenalty] = useState(0.05);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    alert("Attribution polynomial weights saved. All subsequent graph calculations will adopt these calibrated coefficients.");
  };

  return (
    <div className="flex flex-col w-full space-y-space-md">
      {/* HEADER */}
      <div className="bg-surface-container-low p-gutter border border-primary/20 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md">
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
              ALGORITHMIC CALIBRATION // SYSTEM SETTINGS
            </span>
            <h1 className="font-headline-lg text-headline-lg font-serif font-bold text-primary tracking-tight">
              ATTRIBUTION ENGINE CONFIGURATION
            </h1>
            <p className="font-body-md text-on-surface-variant max-w-2xl">
              Calibrate the 10-Factor ATT-v1.0 polynomial weights, RPC cluster endpoints, and statutory jurisdiction mandates.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-surface border border-primary/20 p-space-md shadow-sm max-w-3xl space-y-space-md">
        <form onSubmit={handleSave} className="space-y-4 font-body-md">
          <div className="space-y-3">
            <h3 className="font-headline-sm font-serif font-bold text-primary border-b border-primary/10 pb-2">
              Polynomial Weight Coefficients
            </h3>

            <div>
              <div className="flex justify-between font-label-mono text-body-sm mb-1">
                <span>Flow Volume Share Weight (w_flow):</span>
                <span className="font-bold text-secondary">{flowWeight.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={flowWeight}
                onChange={(e) => setFlowWeight(Number(e.target.value))}
                className="w-full accent-secondary"
              />
            </div>

            <div>
              <div className="flex justify-between font-label-mono text-body-sm mb-1">
                <span>Temporal Decay Weight (w_temp):</span>
                <span className="font-bold text-secondary">{tempWeight.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.4"
                step="0.05"
                value={tempWeight}
                onChange={(e) => setTempWeight(Number(e.target.value))}
                className="w-full accent-secondary"
              />
            </div>

            <div>
              <div className="flex justify-between font-label-mono text-body-sm mb-1">
                <span>Cluster Confidence Weight (w_clus):</span>
                <span className="font-bold text-secondary">{clusterWeight.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.3"
                step="0.05"
                value={clusterWeight}
                onChange={(e) => setClusterWeight(Number(e.target.value))}
                className="w-full accent-secondary"
              />
            </div>

            <div>
              <div className="flex justify-between font-label-mono text-body-sm mb-1">
                <span>Hop Distance Penalty Coefficient (w_hop):</span>
                <span className="font-bold text-secondary">{hopPenalty.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.01"
                max="0.2"
                step="0.01"
                value={hopPenalty}
                onChange={(e) => setHopPenalty(Number(e.target.value))}
                className="w-full accent-secondary"
              />
            </div>
          </div>

          <div className="pt-2 border-t border-primary/10 flex justify-end">
            <button
              type="submit"
              className="px-5 py-2.5 bg-secondary text-on-secondary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-primary transition-colors cursor-pointer shadow-sm"
            >
              SAVE WEIGHT MATRIX
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
