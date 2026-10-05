"use client";

import React, { useState } from "react";
import StitchHeader from "@/components/stitch/StitchHeader";
import StitchSidebar, { StitchViewTab } from "@/components/stitch/StitchSidebar";
import LandingPage from "@/components/stitch/LandingPage";
import InvestigatorDashboard from "@/components/stitch/InvestigatorDashboard";
import InvestigationWorkbench from "@/components/stitch/InvestigationWorkbench";
import SahyogPortal from "@/components/stitch/SahyogPortal";
import VaspRegistryView from "@/components/stitch/VaspRegistryView";
import EvidenceLedgerView from "@/components/stitch/EvidenceLedgerView";
import AuditTrailView from "@/components/stitch/AuditTrailView";
import ProviderHealthView from "@/components/stitch/ProviderHealthView";
import ReportsVerificationView from "@/components/stitch/ReportsVerificationView";
import SettingsView from "@/components/stitch/SettingsView";

export default function Home() {
  const [currentTab, setCurrentTab] = useState<StitchViewTab>("dashboard");
  const [currentRole, setCurrentRole] = useState<"analyst" | "supervisor">("analyst");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Active workbench case parameters
  const [workbenchCase, setWorkbenchCase] = useState<{
    caseRef: string;
    address: string;
    chain: string;
    hopDepth: number;
  }>({
    caseRef: "CASE-02",
    address: "0x71C94828b8E85B438B0F2A389A2",
    chain: "ETH-MAINNET",
    hopDepth: 3,
  });

  const handleOpenWorkbench = (caseData?: {
    address: string;
    chain: string;
    hopDepth: number;
    caseRef?: string;
  }) => {
    if (caseData) {
      setWorkbenchCase({
        caseRef: caseData.caseRef || "CASE-CUSTOM",
        address: caseData.address,
        chain: caseData.chain,
        hopDepth: caseData.hopDepth,
      });
    }
    setCurrentTab("workbench");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleOpenSahyog = (caseRef?: string) => {
    setCurrentTab("sahyog");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    if (searchQuery.toLowerCase().includes("case") || searchQuery.startsWith("0x")) {
      handleOpenWorkbench({
        address: searchQuery.startsWith("0x") ? searchQuery : "0x71C94828b8E85B438B0F2A389A2",
        chain: "ETH-MAINNET",
        hopDepth: 3,
        caseRef: searchQuery.startsWith("CASE") ? searchQuery.toUpperCase() : "CASE-SEARCH",
      });
    } else {
      setCurrentTab("dashboard");
    }
  };

  // If on public landing page view
  if (currentTab === "landing") {
    return (
      <LandingPage
        currentRole={currentRole}
        onRoleChange={setCurrentRole}
        onLaunchWorkbench={(caseRef) => {
          if (caseRef) {
            setWorkbenchCase((prev) => ({ ...prev, caseRef }));
          }
          setCurrentTab("workbench");
        }}
        onOpenDashboard={() => setCurrentTab("dashboard")}
        onOpenSahyog={() => setCurrentTab("sahyog")}
      />
    );
  }

  // Dashboard / Workbench / SAHYOG institutional master view
  return (
    <div className="bg-surface font-body-md text-on-surface antialiased min-h-screen">
      {/* Top Banner and Institutional Header */}
      <StitchHeader
        currentRole={currentRole}
        onRoleChange={setCurrentRole}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSearchSubmit={handleSearchSubmit}
      />

      {/* Fixed Left Sidebar Navigation */}
      <StitchSidebar
        currentTab={currentTab}
        onTabChange={(tab) => {
          setCurrentTab(tab);
          window.scrollTo({ top: 0, behavior: "smooth" });
        }}
      />

      {/* Main Content Area */}
      <div className="pl-72">
        <main className="w-full pt-23 bg-surface min-h-screen">
          <div className="w-full max-w-[1600px] mx-auto p-gutter">
            {currentTab === "dashboard" && (
              <InvestigatorDashboard
                onOpenWorkbench={handleOpenWorkbench}
                onOpenSahyog={handleOpenSahyog}
                onNewInvestigation={() => handleOpenWorkbench()}
              />
            )}

            {currentTab === "workbench" && (
              <InvestigationWorkbench
                initialCaseRef={workbenchCase.caseRef}
                initialAddress={workbenchCase.address}
                initialChain={workbenchCase.chain}
                initialHopDepth={workbenchCase.hopDepth}
                onOpenFileSahyog={handleOpenSahyog}
                onVerifyEvidenceChain={() => setCurrentTab("evidence")}
              />
            )}

            {currentTab === "sahyog" && (
              <SahyogPortal
                currentRole={currentRole}
                onRoleSwitch={setCurrentRole}
              />
            )}

            {currentTab === "registry" && <VaspRegistryView />}

            {currentTab === "evidence" && <EvidenceLedgerView />}

            {currentTab === "reports" && <ReportsVerificationView />}

            {currentTab === "audit" && <AuditTrailView />}

            {currentTab === "health" && <ProviderHealthView />}

            {currentTab === "settings" && <SettingsView />}
          </div>
        </main>
      </div>
    </div>
  );
}
