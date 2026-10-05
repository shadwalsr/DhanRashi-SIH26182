"use client";

import React from "react";

export type StitchViewTab =
  | "landing"
  | "dashboard"
  | "workbench"
  | "sahyog"
  | "registry"
  | "evidence"
  | "reports"
  | "audit"
  | "health"
  | "settings";

interface StitchSidebarProps {
  currentTab: StitchViewTab;
  onTabChange: (tab: StitchViewTab) => void;
}

export default function StitchSidebar({
  currentTab,
  onTabChange,
}: StitchSidebarProps) {
  const primaryNav = [
    {
      id: "dashboard" as StitchViewTab,
      label: "Overview / Dashboard",
      num: "01",
      icon: "grid_view",
    },
    {
      id: "workbench" as StitchViewTab,
      label: "Investigation Workbench",
      num: "02",
      icon: "account_tree",
    },
    {
      id: "registry" as StitchViewTab,
      label: "VASP Intelligence Registry",
      num: "03",
      icon: "assured_workload",
    },
    {
      id: "evidence" as StitchViewTab,
      label: "Evidence Ledger",
      num: "04",
      icon: "receipt_long",
    },
    {
      id: "reports" as StitchViewTab,
      label: "Reports & Verification",
      num: "05",
      icon: "assignment_turned_in",
    },
    {
      id: "sahyog" as StitchViewTab,
      label: "SAHYOG Portal",
      num: "06",
      icon: "hub",
      badge: "MOCK",
    },
    {
      id: "audit" as StitchViewTab,
      label: "Audit Trail",
      num: "07",
      icon: "history_edu",
    },
  ];

  return (
    <aside className="fixed left-0 top-23 bottom-0 w-72 bg-primary-container text-on-primary z-30 flex flex-col border-r border-outline/30 overflow-y-auto select-none">
      {/* SECTION TITLE */}
      <div className="px-space-md py-space-sm border-b border-outline/20">
        <span className="font-label-caps text-label-caps text-on-primary-container uppercase tracking-widest font-semibold">
          PRIMARY INTELLIGENCE
        </span>
      </div>

      {/* PRIMARY NAV ITEMS */}
      <nav className="flex flex-col py-1">
        {primaryNav.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center justify-between px-space-md py-2.5 font-label-caps text-label-caps tracking-wider uppercase transition-colors text-left ${
                isActive
                  ? "bg-secondary text-on-secondary font-semibold border-l-4 border-surface shadow-sm"
                  : "text-on-primary-container hover:bg-primary hover:text-surface"
              }`}
            >
              <span className="flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-[18px]">
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </span>
              {item.badge ? (
                <span className="px-1.5 py-0.5 bg-tertiary text-on-tertiary font-label-mono text-[9px] uppercase">
                  {item.badge}
                </span>
              ) : (
                <span className={`font-label-mono text-[9px] ${isActive ? "text-on-secondary" : "text-on-primary-container/80"}`}>
                  {item.num}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* ADMINISTRATION & SYSTEM SECTION */}
      <div className="mt-space-sm px-space-md py-space-sm border-t border-b border-outline/20">
        <span className="font-label-caps text-label-caps text-on-primary-container uppercase tracking-widest font-semibold">
          ADMINISTRATION & SYSTEM
        </span>
      </div>

      <nav className="flex flex-col py-1">
        <button
          type="button"
          onClick={() => onTabChange("health")}
          className={`w-full flex items-center gap-space-sm px-space-md py-2 font-label-caps text-label-caps tracking-wider uppercase transition-colors text-left ${
            currentTab === "health"
              ? "bg-secondary text-on-secondary font-semibold border-l-4 border-surface shadow-sm"
              : "text-on-primary-container hover:bg-primary hover:text-surface"
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">monitor_heart</span>
          <span>Provider Health</span>
        </button>

        <button
          type="button"
          onClick={() => onTabChange("settings")}
          className={`w-full flex items-center gap-space-sm px-space-md py-2 font-label-caps text-label-caps tracking-wider uppercase transition-colors text-left ${
            currentTab === "settings"
              ? "bg-secondary text-on-secondary font-semibold border-l-4 border-surface shadow-sm"
              : "text-on-primary-container hover:bg-primary hover:text-surface"
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">tune</span>
          <span>Settings</span>
        </button>

        <button
          type="button"
          onClick={() => onTabChange("landing")}
          className={`w-full flex items-center justify-between px-space-md py-2 font-label-caps text-label-caps tracking-wider uppercase transition-colors text-left ${
            currentTab === "landing"
              ? "bg-secondary text-on-secondary font-semibold border-l-4 border-surface shadow-sm"
              : "text-primary-fixed hover:bg-primary hover:text-surface"
          }`}
        >
          <span className="flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-[18px]">auto_stories</span>
            <span>Public Folio / Landing</span>
          </span>
          <span className="px-1 bg-primary text-[8px] font-label-mono text-primary-fixed uppercase">
            FOLIO
          </span>
        </button>
      </nav>

      {/* SYSTEM CORE FOOTER */}
      <div className="mt-auto p-space-md bg-primary/80 border-t border-outline/30 flex flex-col gap-space-xs">
        <div className="flex items-center justify-between">
          <span className="font-label-caps text-[9px] text-on-primary-container uppercase tracking-widest">
            SYSTEM CORE
          </span>
          <span className="flex items-center gap-1 font-label-mono text-[9px] text-surface">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary-container animate-pulse"></span>
            4 CHAINS
          </span>
        </div>
        <div className="font-label-mono text-[10px] text-surface font-semibold tracking-tight">
          ALL ENGINES OPERATIONAL
        </div>
        <div className="pt-space-xs border-t border-outline/20 flex items-center justify-between text-on-primary-container font-label-mono text-[9px]">
          <span>ATT-v1.0</span>
          <span>SNAP-00182</span>
        </div>
      </div>
    </aside>
  );
}
