"use client";

import { useState } from "react";
import { UserRole } from "@/lib/types";
import { DEMO_USERS, api } from "@/lib/api";
import { UserCheck, ShieldAlert, KeyRound, Building2 } from "lucide-react";

interface AuthBarProps {
  currentRole: UserRole;
  onRoleChange: (newRole: UserRole) => void;
}

export default function AuthBar({ currentRole, onRoleChange }: AuthBarProps) {
  const [switching, setSwitching] = useState(false);
  const currentUser = DEMO_USERS[currentRole];

  const handleRoleSelect = async (role: UserRole) => {
    if (role === currentRole) return;
    setSwitching(true);
    try {
      await api.login(role);
      onRoleChange(role);
    } catch (err) {
      console.error("Failed to switch role:", err);
    } finally {
      setSwitching(false);
    }
  };

  const getRoleBadgeColor = (role: UserRole) => {
    switch (role) {
      case "INV":
        return "bg-blue-600 text-white border-blue-700";
      case "FIA":
        return "bg-purple-600 text-white border-purple-700";
      case "SUP":
        return "bg-amber-600 text-white border-amber-700";
      case "AUD":
        return "bg-emerald-600 text-white border-emerald-700";
      case "ADM":
        return "bg-rose-600 text-white border-rose-700";
      case "RO":
        return "bg-slate-600 text-white border-slate-700";
    }
  };

  return (
    <div className="bg-slate-900 border-b border-slate-800 px-6 py-2 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-300">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-slate-400">
          <Building2 className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-semibold text-slate-200">Enforcement Org:</span>
          <span className="font-mono text-slate-400">DEMO-ORG-CENTRAL</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Active Persona:</span>
          <span
            className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] border ${getRoleBadgeColor(
              currentRole
            )}`}
          >
            {currentRole}
          </span>
          <span className="font-medium text-slate-100">{currentUser.name}</span>
          <span className="text-slate-500 font-mono">({currentUser.email})</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1 text-slate-400">
          <KeyRound className="w-3.5 h-3.5 text-amber-400" />
          <span>Quick RBAC Switch:</span>
        </div>
        <div className="flex items-center gap-1 bg-slate-800 p-0.5 rounded border border-slate-700">
          {(["INV", "FIA", "SUP", "AUD", "ADM", "RO"] as UserRole[]).map((role) => (
            <button
              key={role}
              disabled={switching}
              onClick={() => handleRoleSelect(role)}
              className={`px-2 py-1 rounded text-[11px] font-mono font-medium transition ${
                currentRole === role
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white hover:bg-slate-700/60"
              }`}
              title={DEMO_USERS[role].name}
            >
              {role}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
