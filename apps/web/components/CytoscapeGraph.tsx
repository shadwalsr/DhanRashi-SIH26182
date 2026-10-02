"use client";

import { useEffect, useRef, useState } from "react";
import cytoscape, { Core, EventObject } from "cytoscape";
import { GraphResponse, GraphNode, GraphEdge } from "@/lib/types";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  Flame,
  Filter,
  Layers,
  ArrowRight,
  Info,
} from "lucide-react";

interface CytoscapeGraphProps {
  graphData: GraphResponse | null;
  loading: boolean;
  onSelectEdge?: (edge: GraphEdge) => void;
  onSelectNode?: (node: GraphNode) => void;
}

export default function CytoscapeGraph({
  graphData,
  loading,
  onSelectEdge,
  onSelectNode,
}: CytoscapeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  const [riskOverlay, setRiskOverlay] = useState<boolean>(true);
  const [selectedChain, setSelectedChain] = useState<string>("all");
  const [minUsd, setMinUsd] = useState<number>(0);
  const [layoutName, setLayoutName] = useState<string>("breadthfirst");
  const [selectedElement, setSelectedElement] = useState<{
    type: "node" | "edge";
    data: any;
  } | null>(null);

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      boxSelectionEnabled: false,
      autounselectify: false,
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-valign": "bottom",
            "text-margin-y": 6,
            "font-size": "10px",
            "font-family": "monospace",
            color: "#334155",
            "background-color": "#64748b",
            width: 34,
            height: 34,
            "border-width": 2,
            "border-color": "#475569",
            "transition-property": "background-color, border-color, width, height",
            "transition-duration": 0.2,
          },
        },
        {
          selector: "node[nodeType = 'seed']",
          style: {
            "background-color": "#1d4ed8",
            "border-color": "#93c5fd",
            "border-width": 4,
            width: 44,
            height: 44,
            color: "#1e3a8a",
            "font-weight": "bold",
          },
        },
        {
          selector: "node[nodeType = 'vasp']",
          style: {
            "background-color": "#7c3aed",
            "border-color": "#c4b5fd",
            "border-width": 4,
            width: 46,
            height: 46,
            color: "#5b21b6",
            "font-weight": "bold",
          },
        },
        {
          selector: "node[nodeType = 'bridge']",
          style: {
            "background-color": "#0891b2",
            "border-color": "#a5f3fc",
            "border-width": 3,
            shape: "round-rectangle",
            width: 42,
            height: 42,
            color: "#155e75",
            "font-weight": "bold",
          },
        },
        {
          selector: "node[nodeType = 'mixer']",
          style: {
            "background-color": "#e11d48",
            "border-color": "#fecdd3",
            "border-width": 3,
            shape: "octagon",
            width: 40,
            height: 40,
            color: "#9f1239",
            "font-weight": "bold",
          },
        },
        {
          selector: "node[nodeType = 'cluster']",
          style: {
            "background-color": "#0d9488",
            "border-color": "#99f6e4",
            "border-width": 3,
            shape: "diamond",
            width: 38,
            height: 38,
            color: "#115e59",
          },
        },
        {
          selector: "node.risk-highlight",
          style: {
            "border-color": "#dc2626",
            "border-width": 6,
            "background-color": "#ef4444",
          },
        },
        {
          selector: "edge",
          style: {
            width: "mapData(amountNorm, 0, 100, 2, 7)",
            "line-color": "#94a3b8",
            "target-arrow-color": "#94a3b8",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "arrow-scale": 1.2,
            label: "data(edgeLabel)",
            "font-size": "9px",
            "font-family": "monospace",
            color: "#475569",
            "text-background-opacity": 0.8,
            "text-background-color": "#ffffff",
            "text-background-padding": "2px",
          },
        },
        {
          selector: "edge[isCrossChain]",
          style: {
            "line-style": "dashed",
            "line-color": "#06b6d4",
            "target-arrow-color": "#06b6d4",
            width: 4,
          },
        },
        {
          selector: "edge.risk-highlight",
          style: {
            "line-color": "#f43f5e",
            "target-arrow-color": "#f43f5e",
            width: 4,
          },
        },
        {
          selector: ":selected",
          style: {
            "border-color": "#f59e0b",
            "border-width": 4,
            "line-color": "#f59e0b",
            "target-arrow-color": "#f59e0b",
          },
        },
      ],
      layout: { name: "breadthfirst", directed: true, spacingFactor: 1.25 },
    });

    cy.on("tap", "node", (evt: EventObject) => {
      const node = evt.target;
      const data = node.data();
      setSelectedElement({ type: "node", data });
      if (onSelectNode && data.rawNode) {
        onSelectNode(data.rawNode);
      }
    });

    cy.on("tap", "edge", (evt: EventObject) => {
      const edge = evt.target;
      const data = edge.data();
      setSelectedElement({ type: "edge", data });
      if (onSelectEdge && data.rawEdge) {
        onSelectEdge(data.rawEdge);
      }
    });

    cy.on("tap", (evt: EventObject) => {
      if (evt.target === cy) {
        setSelectedElement(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update Cytoscape elements when graphData or filters change
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || !graphData) return;

    cy.batch(() => {
      cy.elements().remove();

      // Filter nodes and edges
      const activeEdges = graphData.edges.filter((e) => {
        if (selectedChain !== "all" && e.chain.toLowerCase() !== selectedChain.toLowerCase()) {
          return false;
        }
        if (minUsd > 0 && (e.usd_value || 0) < minUsd) {
          return false;
        }
        return true;
      });

      const activeNodeKeys = new Set<string>();
      activeEdges.forEach((e) => {
        activeNodeKeys.add(e.source_key);
        activeNodeKeys.add(e.destination_key);
      });

      // Always include seed node (hop == 0)
      graphData.nodes.forEach((n) => {
        if (n.hop === 0) activeNodeKeys.add(n.node_key);
      });

      const activeNodes = graphData.nodes.filter((n) => activeNodeKeys.has(n.node_key));

      // Add nodes
      activeNodes.forEach((n) => {
        const shortAddr =
          n.address.length > 10 ? `${n.address.slice(0, 6)}...${n.address.slice(-4)}` : n.address;
        const displayLabel = n.label ? `${n.label}\n(${shortAddr})` : shortAddr;

        cy.add({
          group: "nodes",
          data: {
            id: n.node_key,
            label: displayLabel,
            nodeType: n.hop === 0 ? "seed" : n.node_type,
            chain: n.chain,
            address: n.address,
            hop: n.hop,
            isTerminal: n.is_terminal,
            rawNode: n,
          },
          classes: riskOverlay && n.is_high_risk ? "risk-highlight" : "",
        });
      });

      // Add edges
      activeEdges.forEach((e) => {
        // Ensure both source and target exist in cy
        if (cy.getElementById(e.source_key).length && cy.getElementById(e.destination_key).length) {
          const edgeVal = e.usd_value ? `$${e.usd_value.toLocaleString()}` : `${e.amount} ${e.asset}`;
          const isCrossChain = Boolean(e.via_cross_chain_event_id);
          const edgeLabel = isCrossChain ? `[Bridge] ${edgeVal}` : edgeVal;

          cy.add({
            group: "edges",
            data: {
              id: e.id || `edge-${e.source_key}-${e.destination_key}`,
              source: e.source_key,
              target: e.destination_key,
              edgeLabel: edgeLabel,
              amountNorm: Math.min(100, Math.max(10, (e.usd_value || 10) / 100)),
              isCrossChain: isCrossChain,
              rawEdge: e,
            },
            classes: riskOverlay && e.is_high_risk ? "risk-highlight" : "",
          });
        }
      });
    });

    // Run layout
    runLayout(layoutName);
  }, [graphData, selectedChain, minUsd, riskOverlay, layoutName]);

  const runLayout = (name: string) => {
    const cy = cyRef.current;
    if (!cy) return;
    setLayoutName(name);

    if (name === "breadthfirst") {
      cy.layout({
        name: "breadthfirst",
        directed: true,
        padding: 40,
        spacingFactor: 1.4,
      } as any).run();
    } else if (name === "concentric") {
      cy.layout({
        name: "concentric",
        concentric: (node: any) => 10 - (node.data("hop") || 0),
        levelWidth: () => 1,
        padding: 40,
      } as any).run();
    } else {
      cy.layout({
        name: "cose",
        padding: 40,
        animate: false,
      } as any).run();
    }
  };

  const handleExportPng = () => {
    const cy = cyRef.current;
    if (!cy) return;
    const png64 = cy.png({ bg: "#ffffff", full: true, scale: 2 });
    const a = document.createElement("a");
    a.href = png64;
    a.download = `vasp-trace-graph-${Date.now()}.png`;
    a.click();
  };

  return (
    <div className="relative w-full h-[620px] bg-slate-50 border border-slate-200 rounded-xl overflow-hidden flex flex-col">
      {/* Top Toolbar */}
      <div className="bg-white border-b border-slate-200 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs z-10">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-semibold text-slate-700">
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            <span>Chain:</span>
            <select
              value={selectedChain}
              onChange={(e) => setSelectedChain(e.target.value)}
              className="bg-slate-100 border border-slate-200 rounded px-2 py-1 text-slate-800 font-medium"
            >
              <option value="all">All Chains</option>
              <option value="ethereum">Ethereum</option>
              <option value="polygon">Polygon</option>
              <option value="tron">Tron</option>
              <option value="bnb_chain">BNB Chain</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 font-semibold text-slate-700">
            <span>Min USD:</span>
            <input
              type="number"
              min="0"
              step="100"
              value={minUsd}
              onChange={(e) => setMinUsd(Number(e.target.value))}
              placeholder="0"
              className="w-20 bg-slate-100 border border-slate-200 rounded px-2 py-1 text-slate-800 font-mono"
            />
          </div>

          <div className="flex items-center gap-1.5 font-semibold text-slate-700">
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            <span>Layout:</span>
            <select
              value={layoutName}
              onChange={(e) => runLayout(e.target.value)}
              className="bg-slate-100 border border-slate-200 rounded px-2 py-1 text-slate-800 font-medium"
            >
              <option value="breadthfirst">Hierarchical Flow</option>
              <option value="concentric">Radial Hops</option>
              <option value="cose">Force-Directed</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Risk Overlay Toggle */}
          <button
            onClick={() => setRiskOverlay(!riskOverlay)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md font-medium border transition ${
              riskOverlay
                ? "bg-rose-50 text-rose-700 border-rose-200 shadow-sm"
                : "bg-slate-100 text-slate-500 border-slate-200 hover:bg-slate-200"
            }`}
          >
            <Flame className="w-3.5 h-3.5 text-rose-500" />
            <span>Risk Signals Overlay</span>
          </button>

          <div className="h-4 w-px bg-slate-200 mx-1" />

          {/* Canvas Controls */}
          <button
            onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.25)}
            className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded border border-slate-200"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
            className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded border border-slate-200"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => cyRef.current?.fit(undefined, 40)}
            className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded border border-slate-200"
            title="Fit to Screen"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleExportPng}
            className="flex items-center gap-1 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded border border-slate-200 font-medium"
            title="Export PNG"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export PNG</span>
          </button>
        </div>
      </div>

      {/* Graph Canvas Container */}
      <div className="flex-1 w-full h-full relative">
        <div ref={containerRef} className="w-full h-full" />

        {/* Loading Indicator */}
        {loading && (
          <div className="absolute inset-0 bg-white/70 backdrop-blur-xs flex items-center justify-center z-20">
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-md border border-slate-200 text-xs font-semibold text-slate-700">
              <span className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              Loading graph data...
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-xs border border-slate-200 rounded-lg p-2.5 shadow-sm text-[11px] space-y-1.5 z-10">
          <div className="font-bold text-slate-700 uppercase tracking-wider text-[10px] mb-1">
            Legend
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-600 border border-blue-300" />
            <span className="text-slate-600 font-medium">Seed Wallet (Hop 0)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-purple-600 border border-purple-300" />
            <span className="text-slate-600 font-medium">VASP Node (Terminal)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-xs bg-cyan-600 border border-cyan-300" />
            <span className="text-slate-600 font-medium">Bridge Contract</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-rose-600 rounded-full border border-rose-300" />
            <span className="text-slate-600 font-medium">Mixer / High Risk</span>
          </div>
          <div className="flex items-center gap-2 pt-1 border-t border-slate-100">
            <span className="w-4 border-t-2 border-dashed border-cyan-500" />
            <span className="text-slate-600">Cross-Chain Hop</span>
          </div>
        </div>

        {/* Element Details Inspector Drawer */}
        {selectedElement && (
          <div className="absolute top-3 right-3 w-80 bg-white/95 backdrop-blur-xs border border-slate-200 rounded-xl p-4 shadow-lg text-xs z-10 max-h-[560px] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
              <span className="font-bold text-slate-800 uppercase tracking-wider">
                {selectedElement.type === "node" ? "Node Inspector" : "Edge Inspector"}
              </span>
              <button
                onClick={() => setSelectedElement(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            {selectedElement.type === "node" && (
              <div className="space-y-2">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Node Address</span>
                  <span className="font-mono text-slate-900 break-all select-all font-semibold">
                    {selectedElement.data.address}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase">Chain</span>
                    <span className="font-semibold text-slate-700 capitalize">
                      {selectedElement.data.chain}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase">Hop Depth</span>
                    <span className="font-semibold text-slate-700">Hop {selectedElement.data.hop}</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase">Classification</span>
                    <span className="font-semibold text-purple-700 uppercase">
                      {selectedElement.data.nodeType}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase">Terminal Node</span>
                    <span className="font-semibold text-slate-700">
                      {selectedElement.data.isTerminal ? "Yes (Stop Tracing)" : "No"}
                    </span>
                  </div>
                </div>
                {selectedElement.data.rawNode?.label && (
                  <div className="pt-1">
                    <span className="text-slate-400 block text-[10px] uppercase">Entity Label</span>
                    <span className="font-semibold text-slate-800">
                      {selectedElement.data.rawNode.label}
                    </span>
                  </div>
                )}
              </div>
            )}

            {selectedElement.type === "edge" && (
              <div className="space-y-2">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Tx Hash</span>
                  <span className="font-mono text-slate-900 break-all select-all text-[11px]">
                    {selectedElement.data.rawEdge?.transaction_hash}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase">Amount Traced</span>
                    <span className="font-bold text-slate-900">
                      {selectedElement.data.rawEdge?.amount} {selectedElement.data.rawEdge?.asset}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase">USD Value</span>
                    <span className="font-bold text-emerald-600">
                      ${selectedElement.data.rawEdge?.usd_value?.toLocaleString() || "N/A"}
                    </span>
                  </div>
                </div>
                {selectedElement.data.rawEdge?.via_cross_chain_event_id && (
                  <div className="p-2 bg-cyan-50 rounded border border-cyan-200 mt-2">
                    <span className="font-bold text-cyan-800 block text-[10px] uppercase mb-0.5">
                      Cross-Chain Bridge Event
                    </span>
                    <span className="font-mono text-[10px] text-cyan-900">
                      Event ID: {selectedElement.data.rawEdge.via_cross_chain_event_id}
                    </span>
                  </div>
                )}
                {selectedElement.data.rawEdge?.evidence_ids?.length > 0 && (
                  <div className="pt-1">
                    <span className="text-slate-400 block text-[10px] uppercase mb-1">
                      Associated Evidence Records (FR-EVD-04)
                    </span>
                    <div className="space-y-1">
                      {selectedElement.data.rawEdge.evidence_ids.map((evId: string) => (
                        <div
                          key={evId}
                          className="font-mono text-[10px] bg-slate-100 px-2 py-0.5 rounded text-slate-700 border border-slate-200"
                        >
                          {evId}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
