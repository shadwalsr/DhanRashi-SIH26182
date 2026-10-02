"use client";

import { useEffect, useState, useCallback } from "react";
import { CheckCircle2, XCircle, RefreshCw, Server, Shield, Database, Cpu } from "lucide-react";


interface HealthData {
  status: string;
  service: string;
  environment: string;
  demo_mode: boolean;
  live_mode: boolean;
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>("");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/health/live`, { cache: "no-store" });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data: HealthData = await res.json();
      setHealth(data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message || "Failed to connect to VASP-Trace API");
      setLastChecked(new Date().toLocaleTimeString());
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);


  return (
    <div className="max-w-6xl mx-auto px-6 py-10 w-full flex-1 flex flex-col justify-between">
      <div>
        {/* Welcome Banner */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200">
                Phase 0 · Foundation & Tooling
              </span>
              <h2 className="text-2xl font-bold text-slate-900 mt-3">
                Automated Attribution of Unknown Cryptocurrency Wallets
              </h2>
              <p className="text-slate-600 text-sm mt-1 max-w-2xl">
                VASP-Trace reconstructs bounded transaction flow graphs and evaluates
                10-factor explainable attribution models to identify destination VASPs
                and generate evidence packages for lawful disclosure requests.
              </p>
            </div>
            <button
              onClick={fetchHealth}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50 transition shadow-sm"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Re-check API Health
            </button>
          </div>
        </div>

        {/* API Connection Status Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Backend API (/health/live)
                </span>
                <Server className="w-4 h-4 text-slate-400" />
              </div>
              <div className="flex items-center gap-3">
                {loading ? (
                  <div className="flex items-center gap-2 text-slate-500 text-sm">
                    <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                    Connecting to {apiUrl}...
                  </div>
                ) : error ? (
                  <div className="flex items-start gap-2 text-rose-600 text-sm">
                    <XCircle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
                    <div>
                      <p className="font-semibold">Unreachable</p>
                      <p className="text-xs text-rose-500">{error}</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-emerald-600 text-sm">
                    <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600" />
                    <span className="font-semibold text-slate-900 text-base">Healthy & Responsive</span>
                  </div>
                )}
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex justify-between text-xs text-slate-400">
              <span>Target: {apiUrl}</span>
              {lastChecked && <span>Checked: {lastChecked}</span>}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Execution Mode
                </span>
                <Shield className="w-4 h-4 text-slate-400" />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">DEMO_MODE</span>
                  <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {health?.demo_mode ? "ENABLED (Deterministic)" : "DISABLED"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">LIVE_MODE</span>
                  <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                    {health?.live_mode ? "ACTIVE" : "OFFLINE / SAFE"}
                  </span>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-400">
              Environment: <span className="font-mono text-slate-600">{health?.environment || "development"}</span>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Worker & Queue Subsystem
                </span>
                <Cpu className="w-4 h-4 text-slate-400" />
              </div>
              <div className="space-y-1.5 text-xs text-slate-600">
                <div className="flex justify-between">
                  <span>Celery Queues:</span>
                  <span className="font-mono font-medium text-slate-800">fetch, trace, analyze, report</span>
                </div>
                <div className="flex justify-between">
                  <span>Scheduler:</span>
                  <span className="font-mono font-medium text-slate-800">Celery Beat heartbeat</span>
                </div>
                <div className="flex justify-between">
                  <span>Concurrency:</span>
                  <span className="font-mono font-medium text-slate-800">4 worker processes</span>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-400">
              PostgreSQL 15 + Redis 7 backing
            </div>
          </div>
        </div>

        {/* Phase Checklist Status */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-600" />
            Phase 0 Foundation Checklist
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
              <span className="font-semibold text-slate-800 block mb-1">1. Monorepo Setup</span>
              <p className="text-slate-500">apps/web, services/api, data/demo, docker-compose.yml</p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
              <span className="font-semibold text-slate-800 block mb-1">2. FastAPI Backend</span>
              <p className="text-slate-500">Pydantic v2 settings, health routes, error envelope, logging</p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
              <span className="font-semibold text-slate-800 block mb-1">3. Database & Migrations</span>
              <p className="text-slate-500">SQLAlchemy 2 base, Alembic initial migration generated</p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
              <span className="font-semibold text-slate-800 block mb-1">4. Worker Queues</span>
              <p className="text-slate-500">Celery 4-queue architecture, beat scheduler, noop test task</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
