/**
 * Bidding-agent FastAPI client.
 * All data comes from the real API - no mock data.
 */

const API_BASE = process.env.NEXT_PUBLIC_BIDDING_API_BASE_URL || 'http://localhost:8000';

export interface BidProject {
  bidder: string;
  created_at: string;
  id: string;
  name: string;
  progress: number;
  readiness_summary?: ProjectReadinessSummary | null;
  stage: string;
  updated_at: string;
}

export interface ProjectReadinessSummary {
  attachment_needs_page_hint: number;
  attachment_ready: number;
  attachment_total: number;
  commercial_needs_page_hint: number;
  commercial_ready: number;
  commercial_tender_only: number;
  commercial_total: number;
  contract_needs_page_hint: number;
  contract_ready: number;
  contract_tender_only: number;
  contract_total: number;
  risk_statuses: Record<string, string>;
  scoring_needs_bidder_evidence: number;
  scoring_needs_page_hint: number;
  scoring_ready: number;
  scoring_total: number;
  status: string;
}

export interface BidProjectDetail extends BidProject {
  draft_markdown?: string;
  draft_sections: any[];
  execution: any;
  plan: any;
  review: any;
  source_files: any[];
}

export interface EvidenceResult {
  asset_paths: string[];
  category: string;
  content: string;
  evidence_id: string;
  heading_path: string;
  page_hint: string;
  source_doc: string;
  sub_type: string;
  summary: string;
  title: string;
  verified_status: string;
}

class ApiError extends Error {
  constructor(
    public status: number,
    public error: string,
    public detail: string,
  ) {
    super(`${status}: ${error} - ${detail}`);
    this.name = 'ApiError';
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errorBody: any;
    try {
      errorBody = await res.json();
    } catch {
      errorBody = { error: res.statusText, message: await res.text().catch(() => '') };
    }
    throw new ApiError(
      res.status,
      errorBody.error || 'Unknown',
      errorBody.message || errorBody.detail || '',
    );
  }

  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return res.json();
  }
  return res.text() as unknown as T;
}

// --- Health ---

export interface HealthResponse {
  core_available: boolean;
  data_dir: string;
  evidence_count: number;
  evidence_store_available: boolean;
  project_count: number;
  status: string;
  timestamp: string;
  version: string;
}

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health');
}

// --- Projects ---

export async function createProject(
  name: string,
  bidder = '',
  project_role = '',
): Promise<{ project_id: string; project: BidProject }> {
  return apiFetch('/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, bidder, project_role }),
  });
}

export async function listProjects(): Promise<{ projects: BidProject[] }> {
  return apiFetch('/projects');
}

export async function getProject(projectId: string): Promise<BidProjectDetail> {
  return apiFetch(`/projects/${projectId}`);
}

// --- Files ---

export async function uploadFile(projectId: string, file: File, purpose: string): Promise<any> {
  const form = new FormData();
  form.append('file', file);
  return apiFetch(`/projects/${projectId}/files?purpose=${encodeURIComponent(purpose)}`, {
    method: 'POST',
    body: form,
  });
}

// --- Workflow ---

export async function runPlan(projectId: string): Promise<any> {
  return apiFetch(`/projects/${projectId}/plan`, { method: 'POST' });
}

export async function approvePlan(projectId: string): Promise<any> {
  return apiFetch(`/projects/${projectId}/approve-plan`, { method: 'POST' });
}

export async function runExecute(projectId: string): Promise<any> {
  return apiFetch(`/projects/${projectId}/execute`, { method: 'POST' });
}

export async function runReview(projectId: string): Promise<any> {
  return apiFetch(`/projects/${projectId}/review`, { method: 'POST' });
}

// --- Artifacts ---

export interface ArtifactInfo {
  modified: string;
  name: string;
  size: number;
}

export interface MaterialGroup {
  binding_hint: string;
  evidence_ids: string[];
  key: string;
  label: string;
  missing_rows: string[];
  owner: string;
  row_ids: string[];
  status: string;
}

export interface EvidenceTraceRecord {
  asset_paths?: string[];
  evidence_id: string;
  heading_path: string;
  material_group?: string;
  material_group_key?: string;
  material_owner?: string;
  page_hint: string;
  row_id: string;
  source_doc: string;
  title: string;
}

export async function listArtifacts(
  projectId: string,
): Promise<{ project_id: string; artifacts: ArtifactInfo[] }> {
  return apiFetch(`/projects/${projectId}/artifacts`);
}

export async function getArtifact(projectId: string, artifactName: string): Promise<string> {
  return apiFetch<string>(`/projects/${projectId}/artifacts/${encodeURIComponent(artifactName)}`);
}

// --- Evidence ---

export interface EvidenceSearchResponse {
  category: string | null;
  count: number;
  query: string;
  results: EvidenceResult[];
}

export async function searchEvidence(
  query: string,
  category?: string,
  topK = 10,
): Promise<EvidenceSearchResponse> {
  const params = new URLSearchParams({ query, top_k: String(topK) });
  if (category) params.set('category', category);
  return apiFetch(`/evidence/search?${params}`);
}

// --- Demo ---

export interface DemoRealCaseResponse {
  artifacts: string[];
  output_dir: string;
  project_id: string;
  status: string;
}

export async function runDemoRealCase(): Promise<DemoRealCaseResponse> {
  return apiFetch('/demo/real-case', { method: 'POST' });
}
