"use client";

import React from "react";

interface StitchHeaderProps {
  currentRole: "analyst" | "supervisor";
  onRoleChange: (role: "analyst" | "supervisor") => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onSearchSubmit?: (e: React.FormEvent) => void;
}

export default function StitchHeader({
  currentRole,
  onRoleChange,
  searchQuery,
  onSearchChange,
  onSearchSubmit,
}: StitchHeaderProps) {
  return (
    <>
      {/* SYNTHETIC DATA / DEMONSTRATION ENVIRONMENT TOP BANNER */}
      <div className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between h-7 bg-secondary text-on-secondary font-label-mono text-body-sm tracking-wider px-gutter border-b border-on-secondary/20 shadow-none">
        <div className="flex items-center gap-space-sm overflow-hidden text-ellipsis whitespace-nowrap">
          <span className="w-1.5 h-1.5 rounded-full bg-surface-bright animate-pulse shrink-0"></span>
          <span className="uppercase font-semibold tracking-widest text-[10px] truncate">
            SYNTHETIC DATA — DEMONSTRATION ENVIRONMENT | NO DEMO ADDRESS, TRANSACTION HASH, VASP OR LABEL CORRESPONDS TO A REAL ENTITY.
          </span>
        </div>
        <div className="hidden lg:flex items-center gap-space-md text-[10px] tracking-widest font-bold shrink-0">
          <span>SYSTEM SPECIFICATION // SIH26182</span>
          <span>|</span>
          <span>STRICT PROVENANCE</span>
        </div>
      </div>

      {/* INSTITUTIONAL MASTHEAD HEADER */}
      <header className="fixed top-7 left-0 right-0 z-40 h-16 bg-primary-container text-on-primary border-b border-outline/30 px-gutter">
        <div className="h-full w-full flex items-center justify-between gap-space-lg">
          {/* Brand lockup */}
          <div className="flex items-center gap-space-md shrink-0 w-72">
            <div className="flex flex-col">
              <div className="flex items-center gap-space-xs">
                <span className="font-headline-sm text-headline-sm font-bold tracking-tight text-surface">
                  DHANRASHI
                </span>
                <span className="px-1.5 py-0.5 bg-secondary text-on-secondary font-label-mono text-[9px] uppercase tracking-widest font-semibold">
                  VASP-TRACE
                </span>
              </div>
              <span className="font-label-caps text-label-caps text-on-primary-container tracking-widest uppercase">
                BLOCKCHAIN INTELLIGENCE (SIH26182)
              </span>
            </div>
          </div>

          {/* Search bar */}
          <div className="flex-1 max-w-2xl">
            <form onSubmit={onSearchSubmit} className="relative flex items-center">
              <span className="material-symbols-outlined absolute left-3 text-on-primary-container text-[18px]">
                search
              </span>
              <input
                className="w-full bg-primary/70 text-surface placeholder-on-primary-container/60 font-label-mono text-body-sm pl-10 pr-4 py-2 border border-outline/40 focus:border-surface focus:outline-none transition-colors uppercase"
                placeholder="SEARCH CASES, WALLETS (0X...), TRANSACTION HASHES (0X...)"
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
              />
            </form>
          </div>

          {/* Institutional controls & role switch */}
          <div className="flex items-center gap-space-md shrink-0">
            <div className="hidden xl:flex items-center gap-1.5 px-2 py-1 bg-primary/60 border border-outline/30">
              <span className="w-2 h-2 rounded-full bg-secondary-container animate-pulse"></span>
              <span className="font-label-mono text-[10px] text-surface font-medium uppercase tracking-wider">
                DEMO ENVIRONMENT
              </span>
            </div>

            {/* Role switch */}
            <div className="hidden lg:flex items-center border border-outline/40 bg-primary/40 p-0.5 font-label-caps text-label-caps">
              <button
                type="button"
                onClick={() => onRoleChange("analyst")}
                className={`px-2.5 py-1 font-bold uppercase transition-all ${
                  currentRole === "analyst"
                    ? "bg-secondary text-on-secondary shadow-sm"
                    : "text-on-primary-container hover:text-surface"
                }`}
              >
                ANALYST
              </button>
              <span className="text-outline/40 px-0.5">|</span>
              <button
                type="button"
                onClick={() => onRoleChange("supervisor")}
                className={`px-2.5 py-1 font-bold uppercase transition-all ${
                  currentRole === "supervisor"
                    ? "bg-secondary text-on-secondary shadow-sm"
                    : "text-on-primary-container hover:text-surface"
                }`}
              >
                SUPERVISOR
              </button>
            </div>

            <div className="hidden 2xl:flex items-center gap-1 px-2 py-1 border border-outline/30 text-on-primary-container">
              <span className="material-symbols-outlined text-[14px]">verified_user</span>
              <span className="font-label-mono text-[10px] uppercase tracking-wider text-surface">
                SECURE // AUDITED
              </span>
            </div>

            <button
              className="relative p-1.5 text-on-primary-container hover:text-surface transition-colors"
              type="button"
              title="Notifications"
            >
              <span className="material-symbols-outlined text-[20px]">notifications</span>
              <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-secondary"></span>
            </button>

            {/* User profile */}
            <div className="flex items-center gap-space-sm pl-2 border-l border-outline/30">
              <div className="text-right hidden sm:block">
                <div className="font-label-caps text-label-caps text-surface font-semibold uppercase tracking-wider">
                  {currentRole === "analyst" ? "Insp. V. Sharma" : "Superintendent R. Verma"}
                </div>
                <div className="font-label-mono text-[9px] text-on-primary-container uppercase tracking-tight">
                  {currentRole === "analyst" ? "FIU-IND Lead Analyst" : "Supervisory Authority"}
                </div>
              </div>
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center border border-outline/40">
                <span className="material-symbols-outlined text-on-primary text-[18px]">
                  {currentRole === "analyst" ? "person" : "shield_person"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>
    </>
  );
}
