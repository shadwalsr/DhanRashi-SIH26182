"use client";

import React, { useState } from "react";

export default function ProviderHealthView() {
  const [refreshing, setRefreshing] = useState(false);

  const providers = [
    {
      chain: "ETHEREUM (MAINNET)",
      chainId: 1,
      rpcEndpoint: "rpc.ankr.com/eth (Fallback: Infura)",
      blockHeight: "21,084,912",
      latency: "42 ms",
      peers: 64,
      status: "HEALTHY",
      syncStatus: "100% SYNCHRONIZED",
    },
    {
      chain: "BNB SMART CHAIN",
      chainId: 56,
      rpcEndpoint: "bsc-dataseed.binance.org",
      blockHeight: "43,892,104",
      latency: "68 ms",
      peers: 48,
      status: "HEALTHY",
      syncStatus: "100% SYNCHRONIZED",
    },
    {
      chain: "POLYGON PoS",
      chainId: 137,
      rpcEndpoint: "polygon-rpc.com",
      blockHeight: "64,129,088",
      latency: "35 ms",
      peers: 72,
      status: "HEALTHY",
      syncStatus: "100% SYNCHRONIZED",
    },
    {
      chain: "TRON (TRC-20)",
      chainId: 728126428,
      rpcEndpoint: "api.trongrid.io",
      blockHeight: "66,419,230",
      latency: "84 ms",
      peers: 36,
      status: "HEALTHY",
      syncStatus: "100% SYNCHRONIZED",
    },
  ];

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      setRefreshing(false);
      alert("Provider health re-polled: All 4 blockchain RPC gateways responsive.");
    }, 600);
  };

  return (
    <div className="flex flex-col w-full space-y-space-md">
      {/* HEADER */}
      <div className="bg-surface-container-low p-gutter border border-primary/20 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md">
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
              SYSTEM TELEMETRY // ADMINISTRATION
            </span>
            <h1 className="font-headline-lg text-headline-lg font-serif font-bold text-primary tracking-tight">
              BLOCKCHAIN PROVIDER HEALTH & RPC MESH
            </h1>
            <p className="font-body-md text-on-surface-variant max-w-2xl">
              Real-time monitoring of decentralized node gateways, block tip synchronization, and query latency across monitored distributed ledgers.
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2.5 bg-secondary text-on-secondary font-label-caps text-label-caps uppercase font-bold tracking-wider hover:bg-primary transition-colors flex items-center gap-2 shadow-sm cursor-pointer disabled:opacity-70"
          >
            <span className={`material-symbols-outlined text-[16px] ${refreshing ? "animate-spin" : ""}`}>
              refresh
            </span>
            <span>{refreshing ? "PINGING NODES..." : "PING RPC NODES"}</span>
          </button>
        </div>
      </div>

      {/* METRIC CHIPS */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-space-md font-label-mono text-body-sm">
        <div className="bg-primary text-on-primary p-space-md shadow-sm">
          <span className="text-[10px] text-primary-fixed uppercase">OVERALL CLUSTER HEALTH</span>
          <div className="text-data-metric font-serif font-bold text-surface-bright mt-1">100.0%</div>
          <div className="text-[10px] text-primary-fixed-dim mt-1">4 of 4 Networks Operational</div>
        </div>
        <div className="bg-surface-container p-space-md border border-primary/20">
          <span className="text-[10px] text-outline uppercase">AVERAGE RPC LATENCY</span>
          <div className="text-data-metric font-serif font-bold text-secondary mt-1">57 ms</div>
          <div className="text-[10px] text-on-surface-variant mt-1">Sub-100ms threshold satisfied</div>
        </div>
        <div className="bg-surface-container p-space-md border border-primary/20">
          <span className="text-[10px] text-outline uppercase">BLOCK TIP LAG</span>
          <div className="text-data-metric font-serif font-bold text-primary mt-1">0 BLOCKS</div>
          <div className="text-[10px] text-on-surface-variant mt-1">Full Real-Time Head Sync</div>
        </div>
        <div className="bg-surface-container p-space-md border border-primary/20">
          <span className="text-[10px] text-outline uppercase">INGESTION THROUGHPUT</span>
          <div className="text-data-metric font-serif font-bold text-primary mt-1">1,240 tx/s</div>
          <div className="text-[10px] text-on-surface-variant mt-1">Decentralized Mempool & Logs</div>
        </div>
      </div>

      {/* PROVIDER CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
        {providers.map((p) => (
          <div key={p.chain} className="bg-surface border border-primary/20 p-space-md shadow-sm space-y-space-sm">
            <div className="flex items-center justify-between pb-space-xs border-b border-primary/10">
              <div>
                <span className="font-label-caps text-[10px] text-secondary font-bold uppercase">
                  CHAIN ID: {p.chainId}
                </span>
                <h3 className="font-title-editorial font-bold text-primary font-serif">{p.chain}</h3>
              </div>
              <span className="px-2 py-0.5 bg-primary text-on-primary font-label-mono text-[10px] uppercase font-bold">
                {p.status}
              </span>
            </div>

            <div className="space-y-1 font-label-mono text-body-sm text-on-surface">
              <div className="flex justify-between py-1 bg-surface-container px-2">
                <span className="text-on-surface-variant">Endpoint:</span>
                <span className="font-bold text-primary truncate max-w-xs">{p.rpcEndpoint}</span>
              </div>
              <div className="flex justify-between py-1 bg-surface-container-low px-2">
                <span className="text-on-surface-variant">Block Tip:</span>
                <span className="font-bold text-primary">{p.blockHeight}</span>
              </div>
              <div className="flex justify-between py-1 bg-surface-container px-2">
                <span className="text-on-surface-variant">Query Latency:</span>
                <span className="font-bold text-secondary">{p.latency}</span>
              </div>
              <div className="flex justify-between py-1 bg-surface-container-low px-2">
                <span className="text-on-surface-variant">Peer Connections:</span>
                <span className="font-bold text-primary">{p.peers} Mesh Nodes</span>
              </div>
              <div className="flex justify-between py-1 bg-surface-container px-2">
                <span className="text-on-surface-variant">Sync State:</span>
                <span className="font-bold text-primary">{p.syncStatus}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
