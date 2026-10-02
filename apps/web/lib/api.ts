import {
  Case,
  Investigation,
  GraphResponse,
  AttributionResponse,
  RiskAssessment,
  Evidence,
  VaspRecord,
  VaspAddressRecord,
  CrossChainEvent,
  AuditLog,
  Report,
  SahyogRequest,
  UserRole,
  UserSession,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Pre-seeded demo user profiles for instant switching without re-authenticating
export const DEMO_USERS: Record<UserRole, { email: string; name: string; role: UserRole }> = {
  INV: { email: "inv@dhanrashi.local", name: "Agent Vikram (Lead Investigator)", role: "INV" },
  FIA: { email: "fia@dhanrashi.local", name: "Ananya Roy (Senior Intel Analyst)", role: "FIA" },
  SUP: { email: "sup@dhanrashi.local", name: "Rajesh Sharma (Superintendent)", role: "SUP" },
  AUD: { email: "aud@dhanrashi.local", name: "Sunil Mehra (Internal Auditor)", role: "AUD" },
  ADM: { email: "adm@dhanrashi.local", name: "System Administrator", role: "ADM" },
  RO: { email: "ro@dhanrashi.local", name: "Liaison Officer (Read Only)", role: "RO" },
};

class ApiClient {
  private token: string | null = null;
  private currentRole: UserRole = "INV";

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("vasp_trace_token");
      this.currentRole = (localStorage.getItem("vasp_trace_role") as UserRole) || "INV";
    }
  }

  setSession(session: UserSession) {
    this.token = session.token;
    this.currentRole = session.role;
    if (typeof window !== "undefined") {
      localStorage.setItem("vasp_trace_token", session.token);
      localStorage.setItem("vasp_trace_role", session.role);
      localStorage.setItem("vasp_trace_user", JSON.stringify(session));
    }
  }

  getCurrentSession(): UserSession | null {
    if (typeof window === "undefined") return null;
    const stored = localStorage.getItem("vasp_trace_user");
    if (!stored) return null;
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  }

  getCurrentRole(): UserRole {
    return this.currentRole;
  }

  private async fetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const errorText = await res.text();
      let errorJson: any;
      try {
        errorJson = JSON.parse(errorText);
      } catch {
        errorJson = null;
      }
      const message = errorJson?.detail || errorJson?.error?.message || errorText || `HTTP ${res.status}`;
      throw new Error(message);
    }

    return res.json();
  }

  // --- Auth ---
  async login(role: UserRole = "INV"): Promise<UserSession> {
    const demoUser = DEMO_USERS[role];
    const formData = new URLSearchParams();
    formData.append("username", demoUser.email);
    formData.append("password", "Password123!");

    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });

    if (!res.ok) {
      throw new Error(`Login failed for ${demoUser.email}`);
    }

    const data = await res.json();
    const session: UserSession = {
      id: data.user_id || "demo-user-id",
      email: demoUser.email,
      fullName: demoUser.name,
      role: role,
      orgId: data.org_id || "demo-org-id",
      token: data.access_token,
    };

    this.setSession(session);
    return session;
  }

  // --- Cases ---
  async listCases(): Promise<Case[]> {
    return this.fetch<Case[]>("/api/v1/cases");
  }

  async getCase(caseId: string): Promise<Case> {
    return this.fetch<Case>(`/api/v1/cases/${caseId}`);
  }

  async createCase(payload: { reference_number: string; title: string; description?: string }): Promise<Case> {
    return this.fetch<Case>("/api/v1/cases", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // --- Investigations ---
  async listInvestigations(caseId?: string): Promise<Investigation[]> {
    const query = caseId ? `?case_id=${caseId}` : "";
    return this.fetch<Investigation[]>(`/api/v1/investigations${query}`);
  }

  async getInvestigation(id: string): Promise<Investigation> {
    return this.fetch<Investigation>(`/api/v1/investigations/${id}`);
  }

  async createInvestigation(payload: {
    case_id: string;
    wallet_address: string;
    blockchain: string;
    depth?: number;
    min_usd_threshold?: number;
  }): Promise<Investigation> {
    return this.fetch<Investigation>("/api/v1/investigations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async runInvestigation(id: string): Promise<{ status: string; investigation_id: string }> {
    return this.fetch<{ status: string; investigation_id: string }>(`/api/v1/investigations/${id}/run`, {
      method: "POST",
    });
  }

  async getInvestigationStatus(id: string): Promise<any> {
    return this.fetch<any>(`/api/v1/investigations/${id}/status`);
  }

  async getInvestigationGraph(id: string): Promise<GraphResponse> {
    return this.fetch<GraphResponse>(`/api/v1/investigations/${id}/graph`);
  }

  // --- Attribution ---
  async getAttribution(investigationId: string): Promise<AttributionResponse> {
    return this.fetch<AttributionResponse>(`/api/v1/investigations/${investigationId}/attribution`);
  }

  async getExplainAttribution(investigationId: string): Promise<any> {
    return this.fetch<any>(`/api/v1/investigations/${investigationId}/attribution/explain`);
  }

  async updateDisposition(
    investigationId: string,
    payload: { candidate_vasp_id: string; disposition: string; notes?: string }
  ): Promise<any> {
    return this.fetch<any>(`/api/v1/investigations/${investigationId}/attribution/disposition`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // --- Risk Engine ---
  async getRiskAssessment(investigationId: string): Promise<RiskAssessment> {
    return this.fetch<RiskAssessment>(`/api/v1/investigations/${investigationId}/risk`);
  }

  async runRiskAssessment(investigationId: string): Promise<RiskAssessment> {
    return this.fetch<RiskAssessment>(`/api/v1/investigations/${investigationId}/risk/run`, {
      method: "POST",
    });
  }

  // --- Evidence Ledger ---
  async listEvidence(investigationId: string, provenanceClass?: string): Promise<Evidence[]> {
    const query = provenanceClass ? `?provenance_class=${encodeURIComponent(provenanceClass)}` : "";
    return this.fetch<Evidence[]>(`/api/v1/investigations/${investigationId}/evidence${query}`);
  }

  async addAnalystNote(investigationId: string, note: string): Promise<Evidence> {
    return this.fetch<Evidence>(`/api/v1/investigations/${investigationId}/evidence/note`, {
      method: "POST",
      body: JSON.stringify({ note }),
    });
  }

  async verifyEvidenceChain(investigationId: string): Promise<{ valid: boolean; total_records: number; details?: string }> {
    return this.fetch<any>(`/api/v1/investigations/${investigationId}/evidence/verify`);
  }

  // --- Cross-Chain ---
  async getCrossChainEvents(investigationId: string): Promise<CrossChainEvent[]> {
    return this.fetch<CrossChainEvent[]>(`/api/v1/investigations/${investigationId}/cross-chain`);
  }

  // --- VASP Registry ---
  async listVasps(): Promise<VaspRecord[]> {
    return this.fetch<VaspRecord[]>("/api/v1/vasps");
  }

  async listVaspAddresses(vaspId?: string): Promise<VaspAddressRecord[]> {
    const query = vaspId ? `?vasp_id=${vaspId}` : "";
    return this.fetch<VaspAddressRecord[]>(`/api/v1/vasps/addresses${query}`);
  }

  async resolveLabelConflict(addressId: string, resolution: "superseded" | "disputed", justification: string): Promise<any> {
    return this.fetch<any>(`/api/v1/vasps/addresses/${addressId}/resolve`, {
      method: "POST",
      body: JSON.stringify({ resolution, justification }),
    });
  }

  // --- Reports ---
  async listReports(caseId?: string): Promise<Report[]> {
    const query = caseId ? `?case_id=${caseId}` : "";
    return this.fetch<Report[]>(`/api/v1/reports${query}`);
  }

  async generateReport(caseId: string, investigationId: string, title: string): Promise<Report> {
    return this.fetch<Report>("/api/v1/reports/generate", {
      method: "POST",
      body: JSON.stringify({ case_id: caseId, investigation_id: investigationId, title }),
    });
  }

  async approveReport(reportId: string, comment: string): Promise<Report> {
    return this.fetch<Report>(`/api/v1/reports/${reportId}/approve`, {
      method: "POST",
      body: JSON.stringify({ comment }),
    });
  }

  // --- SAHYOG ---
  async listSahyogRequests(): Promise<SahyogRequest[]> {
    return this.fetch<SahyogRequest[]>("/api/v1/sahyog/requests");
  }

  async createSahyogDraft(payload: {
    case_id: string;
    investigation_id: string;
    report_id: string;
    target_vasp_id: string;
  }): Promise<SahyogRequest> {
    return this.fetch<SahyogRequest>("/api/v1/sahyog/draft", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async submitSahyogRequest(requestId: string): Promise<SahyogRequest> {
    return this.fetch<SahyogRequest>(`/api/v1/sahyog/requests/${requestId}/submit`, {
      method: "POST",
    });
  }

  // --- Audit ---
  async listAuditLogs(): Promise<AuditLog[]> {
    return this.fetch<AuditLog[]>("/api/v1/audit/logs");
  }

  async verifyAuditChain(): Promise<{ valid: boolean; total_events: number; checked_at: string }> {
    return this.fetch<any>("/api/v1/audit/verify-chain");
  }

  // --- Health ---
  async getHealth(): Promise<any> {
    return this.fetch<any>("/health/live");
  }

  async getReady(): Promise<any> {
    return this.fetch<any>("/health/ready");
  }
}

export const api = new ApiClient();
