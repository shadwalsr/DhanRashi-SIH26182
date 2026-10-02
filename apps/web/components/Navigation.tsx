"use client";

import { UserRole } from "@/lib/types";
import {
  FolderKanban,
  GitFork,
  Scale,
  ScrollText,
  Building,
  ShieldAlert,
  History,
  Activity,
} from "lucide-react";

export type NavTab =
  | "cases"
  | "graph"
  | "attribution"
  | "evidence"
  | "registry"
  | "sahyog"
  | "audit"
  | "health";

interface NavigationProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  userRole: UserRole;
  activeInvestigationId?: string | null;
}

export default function Navigation({
  currentTab,
  onTabChange,
  userRole,
  activeInvestigationId,
}: NavigationProps) {
  const tabs = [
    {
      id: "cases" as NavTab,
      label: "Cases & Investigations",
      icon: FolderKanban,
      roles: ["INV", "FIA", "SUP", "AUD", "ADM", "RO"],
    },
    {
      id: "graph" as NavTab,
      label: "Graph Explorer",
      icon: GitFork,
      roles: ["INV", "FIA", "SUP", "RO"],
      requiresInvestigation: true,
    },
    {
      id: "attribution" as NavTab,
      label: "Attribution Engine",
      icon: Scale,
      roles: ["INV", "FIA", "SUP", "RO"],
      requiresInvestigation: true,
    },
    {
      id: "evidence" as NavTab,
      label: "Evidence Ledger",
      icon: ScrollText,
      roles: ["INV", "FIA", "SUP", "AUD", "RO"],
      requiresInvestigation: true,
    },
    {
      id: "registry" as NavTab,
      label: "VASP Registry",
      icon: Building,
      roles: ["INV", "FIA", "SUP", "AUD", "ADM", "RO"],
    },
    {
      id: "sahyog" as NavTab,
      label: "Approvals & SAHYOG",
      icon: ShieldAlert,
      roles: ["INV", "FIA", "SUP", "RO"],
    },
    {
      id: "audit" as NavTab,
      label: "Audit Trail",
      icon: History,
      roles: ["AUD", "ADM", "SUP", "INV", "FIA"],
    },
    {
      id: "health" as NavTab,
      label: "System Health",
      icon: Activity,
      roles: ["ADM", "SUP", "INV", "FIA", "AUD", "RO"],
    },
  ];

  return (
    <div className="bg-white border-b border-slate-200 px-6">
      <div className="flex space-x-1 overflow-x-auto scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isAllowed = tab.roles.includes(userRole);
          const isDisabled = !isAllowed || (tab.requiresInvestigation && !activeInvestigationId);

          return (
            <button
              key={tab.id}
              disabled={isDisabled}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-3 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
                currentTab === tab.id
                  ? "border-blue-600 text-blue-600 bg-blue-50/40"
                  : isDisabled
                  ? "border-transparent text-slate-300 cursor-not-allowed"
                  : "border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.requiresInvestigation && !activeInvestigationId && (
                <span className="text-[10px] text-slate-300 uppercase tracking-tight">
                  (select inv)
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
