import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
});

export interface DashboardStats {
  project_count: number;
  asset_count: number;
  readiness: number;
  identity_verified: boolean;
  pending_tasks: number;
  active_projects: Array<{
    name: string;
    status: string;
    progress: number;
    time: string;
  }>;
}

export interface DashboardContext {
  current_company_id: number | null;
  current_company_name: string | null;
  current_project_id: number | null;
  current_project_name: string | null;
  current_draft_id: string | null;
}

export interface EnterpriseAssetsOverview {
  company_id: number;
  counts: {
    certificates: number;
    cases: number;
    personnel: number;
    source_documents: number;
    images: number;
  };
  certificates: Array<{
    id: number;
    raw_name: string;
    cert_type: string | null;
    cert_level: string | null;
    scope: string | null;
    expiry_date: string | null;
    image_url: string | null;
  }>;
  cases: Array<{
    id: number;
    project_name: string;
    industry: string | null;
    contract_amount: number | null;
    description: string | null;
  }>;
  personnel: Array<{
    id: number;
    name: string;
    role: string | null;
    level: string | null;
    years_of_experience: number;
    social_security_image_url: string | null;
  }>;
  source_documents: Array<{
    id: number;
    filename: string;
    file_type: string | null;
    upload_date: string | null;
  }>;
  images: Array<{
    id: string;
    asset_name: string;
    asset_tag: string | null;
    local_path: string | null;
  }>;
}

export interface EnterpriseAssetBrowserItem {
  id: string;
  kind: 'certificate' | 'case' | 'personnel' | 'source_document' | 'image';
  title: string;
  subtitle: string;
  summary: string;
  meta: Record<string, unknown>;
}

export interface EnterpriseAssetBrowserResponse {
  company_id: number;
  asset_kind: string;
  query: string;
  total: number;
  items: EnterpriseAssetBrowserItem[];
}

export interface EnterpriseIntakeReadiness {
  company_id: number;
  company_name: string;
  ready: boolean;
  checks: Array<{
    key: string;
    label: string;
    passed: boolean;
    detail: unknown;
  }>;
  warnings: string[];
}

export interface EnterpriseLatestIngestBatch {
  company_id: number;
  has_batch: boolean;
  batch_date: string | null;
  source_documents: Array<{
    id: number;
    filename: string;
    file_type: string | null;
    local_path: string | null;
  }>;
  counts: {
    source_documents: number;
    certificates: number;
    cases: number;
    images: number;
  };
  notes: string[];
}

export interface ModelCapabilities {
  provider: string;
  api_key_configured: boolean;
  base_url: string;
  llm_model: string;
  embedding_model: string | null;
  chat_enabled: boolean;
  embedding_enabled: boolean;
  fallbacks: Record<string, boolean>;
  compatibility_notes: string[];
}

export interface ReviewResult {
  project_id: number;
  win_rate: number;
  critical_risks: string[];
  optimization_suggestions: string[];
  winning_highlights: string[];
  section_reviews: Array<{
    draft_id: number;
    section_title: string;
    verdict: 'APPROVED' | 'REJECTED';
    feedback: string;
    source_fragments: string[];
    generation_status: string;
  }>;
  total_drafts: number;
  approved_drafts: number;
  round: string;
}

export interface ExportReadiness {
  project_id: number;
  project_name: string;
  project_status: string;
  ready: boolean;
  checks: Array<{
    key: string;
    label: string;
    passed: boolean;
    detail: unknown;
  }>;
  rejected_sections: Array<{
    draft_id: number;
    section_title: string;
    generation_status: string;
    audit_feedback?: string;
  }>;
}

export interface MaterialPackAsset {
  id: number;
  title: string;
  subtitle: string;
  summary: string;
  evidence_image_url?: string | null;
  social_security_image_url?: string | null;
  contract_amount?: number | null;
  level?: string | null;
  filename?: string;
  file_type?: string | null;
  upload_date?: string | null;
  parsed_excerpt?: string;
}

export interface ProjectMaterialsPack {
  project_id: number;
  project_name: string;
  project_status: string;
  confirmed: boolean;
  drafting_notes: string;
  selection: {
    certificate_ids: number[];
    case_ids: number[];
    personnel_ids: number[];
    material_ids: number[];
  };
  recommended: {
    certificate_ids: number[];
    case_ids: number[];
    personnel_ids: number[];
  };
  available: {
    certificates: MaterialPackAsset[];
    cases: MaterialPackAsset[];
    personnel: MaterialPackAsset[];
    materials: MaterialPackAsset[];
  };
  selected: {
    certificates: MaterialPackAsset[];
    cases: MaterialPackAsset[];
    personnel: MaterialPackAsset[];
    materials: MaterialPackAsset[];
  };
  summary: {
    requirements_total: number;
    certificates_selected: number;
    cases_selected: number;
    personnel_selected: number;
    materials_selected: number;
  };
}

export interface AnalysisCheck {
  project_id: number;
  project_name: string;
  quality_report: {
    status: 'passed' | 'needs_review';
    passed_checks: number;
    total_checks: number;
    checks: Array<{
      name: string;
      passed: boolean;
      detail: unknown;
    }>;
    warnings: string[];
    metrics: {
      requirements_total: number;
      fatal_count: number;
      scoring_count: number;
      evidence_count: number;
      category_distribution: Record<string, number>;
    };
  };
}

export interface RfpResult {
  project_id?: number;
  project_name: string;
  project_status?: string;
  project_info?: {
    name: string;
    budget: number;
  };
  budget: number;
  bid_deadline: string;
  veto_clauses: Array<{
    id: number;
    clause_index?: string | null;
    category?: string;
    requirement: string;
    evidence_required?: string | null;
    max_score?: number;
    original_section?: string | null;
    source?: {
      page: number;
      bbox: number[];
      text: string;
    };
  }>;
  commercial_requirements: Array<{
    id: number;
    clause_index?: string | null;
    category?: string;
    item: string;
    is_mandatory?: boolean;
    evidence_required?: string | null;
    max_score?: number;
    original_section?: string | null;
    source?: {
      page: number;
      bbox: number[];
      text: string;
    };
  }>;
  technical_requirements: Array<{
    id: number;
    category?: string;
    item: string;
    param_name?: string;
    required_value?: string;
    component?: string;
    evidence_required?: string | null;
    max_score?: number;
    original_section?: string | null;
    source?: {
      page: number;
      bbox: number[];
      text: string;
    };
  }>;
  scoring_system: Record<string, number>;
  go_no_go?: {
    score: number;
    reasons: string[];
    status: string;
  };
}

export interface DeviationMatrixItem {
  id: number;
  req: string;
  resp: string;
  status: 'compliant' | 'partial' | 'gap' | 'unknown';
  is_fatal: boolean;
  category?: string;
  evidence_required?: string | null;
  original_section?: string | null;
}

export interface DraftTaskResult {
  draft_id: number;
  project_id: number;
  content: string;
  audit_feedback: string;
}

export interface DraftDetail {
  id: number;
  project_id: number;
  section_title: string;
  section_index: string;
  content_markdown: string | null;
  generation_status: string;
  audit_logs?: Record<string, unknown> | null;
  source_fragments?: string[] | null;
  winning_points?: string | null;
  version?: number;
}

export interface DraftContentSaveResult {
  status: string;
  draft_id: number;
  version: number;
  generation_status: string;
  last_updated: string | null;
}

export interface ProjectDraftTaskResult {
  project_id: number;
  total_sections: number;
  selection_mode?: 'all' | 'only_incomplete';
  current_section_index?: number;
  current_section_title?: string;
  completed_sections: Array<{
    draft_id: number;
    section_title: string;
    content_length: number;
    approved: boolean;
  }>;
}

export interface DraftTaskStatus {
  status: string;
  stage: string;
  result?: DraftTaskResult;
  error?: string;
}

export interface ProjectDraftTaskStatus {
  status: string;
  stage: string;
  result?: ProjectDraftTaskResult;
  error?: string;
}

export const dashboardService = {
  getStats: async () => (await api.get<DashboardStats>('/dashboard/stats')).data,
  getContext: async () => (await api.get<DashboardContext>('/dashboard/context')).data,
};

export const configService = {
  get: async () => (await api.get('/config/')).data,
  getCapabilities: async () => (await api.get<ModelCapabilities>('/config/capabilities')).data,
  update: async (payload: { llm_model: string; api_key?: string; base_url: string; embedding_model?: string }) =>
    (await api.post('/config/update', payload)).data,
  testConnection: async () => (await api.post('/config/test-connection')).data,
};

export const enterpriseService = {
  list: async () => (await api.get('/enterprise')).data,
  get: async (id: string) => (await api.get(`/enterprise/${id}`)).data,
  create: async (data: unknown) => (await api.post('/enterprise', data)).data,
  getProfile: async () => (await api.get('/enterprise/profile')).data,
  updateProfile: async (data: unknown) => (await api.put('/enterprise/profile', data)).data,
  getTrustScore: async () => (await api.get('/enterprise/trust-score')).data,
  getAssetsOverview: async (companyId: number) => (await api.get<EnterpriseAssetsOverview>(`/enterprise/assets-overview/${companyId}`)).data,
  getIntakeReadiness: async (companyId: number) => (await api.get<EnterpriseIntakeReadiness>(`/enterprise/intake-readiness/${companyId}`)).data,
  getLatestIngestBatch: async (companyId: number) => (await api.get<EnterpriseLatestIngestBatch>(`/enterprise/latest-ingest-batch/${companyId}`)).data,
  getAssetsBrowser: async (companyId: number, assetKind = 'all', query = '') =>
    (
      await api.get<EnterpriseAssetBrowserResponse>(`/enterprise/assets-browser/${companyId}`, {
        params: { asset_kind: assetKind, query },
      })
    ).data,
  createAsset: async (kind: 'certificate' | 'case' | 'personnel', data: Record<string, unknown>) =>
    (await api.post(`/enterprise/assets/${kind}`, data)).data,
  updateAsset: async (kind: 'certificate' | 'case' | 'personnel', id: number, data: Record<string, unknown>) =>
    (await api.put(`/enterprise/assets/${kind}/${id}`, data)).data,
  deleteAsset: async (kind: 'certificate' | 'case' | 'personnel', id: number) =>
    (await api.delete(`/enterprise/assets/${kind}/${id}`)).data,
  batchDeleteAssets: async (items: Array<{ kind: 'certificate' | 'case' | 'personnel'; id: number }>) =>
    (await api.post('/enterprise/assets/batch-delete', { items })).data,
  bulkIngest: async (companyId: number, files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    return (
      await api.post(`/enterprise/bulk-ingest/${companyId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data;
  },
};

export const rfpService = {
  analyze: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return (
      await api.post('/rfp/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data;
  },
  getTaskStatus: async (taskId: string) => (await api.get(`/rfp/status/${taskId}`)).data,
  getProjectAnalysis: async (projectId: number) => (await api.get<RfpResult>(`/rfp/projects/${projectId}`)).data,
  getAnalysisCheck: async (projectId: number) => (await api.get<AnalysisCheck>(`/rfp/projects/${projectId}/analysis-check`)).data,
  confirmAnalysis: async (
    projectId: number,
    payload: {
      project_info: { name: string; budget: number; deadline: string };
      requirements: Array<{
        id: number;
        description: string;
        category?: string;
        is_fatal?: boolean;
        evidence_required?: string;
        max_score?: number;
      }>;
    },
  ) => (await api.post(`/rfp/projects/${projectId}/analysis-confirm`, payload)).data,
  getDeviationMatrix: async (projectId: number) => (await api.get<DeviationMatrixItem[]>(`/rfp/projects/${projectId}/deviation`)).data,
  updateDeviationMatrix: async (projectId: number, items: DeviationMatrixItem[]) =>
    (await api.put(`/rfp/projects/${projectId}/deviation`, { items: items.map(({ id, resp, status }) => ({ id, resp, status })) })).data,
  confirmDeviationMatrix: async (projectId: number) => (await api.post(`/rfp/projects/${projectId}/deviation/confirm`)).data,
};

export const biddingService = {
  getOutline: async (projectId: number) => (await api.get(`/bid/outline/${projectId}`)).data,
  getProjectDrafts: async (projectId: number) => (await api.get<DraftDetail[]>(`/bid/projects/${projectId}/drafts`)).data,
  saveDraftContent: async (draftId: string, contentMarkdown: string) =>
    (await api.put<DraftContentSaveResult>(`/bid/draft/${draftId}/content`, { content_markdown: contentMarkdown })).data,
  getMaterialsPack: async (projectId: number) => (await api.get<ProjectMaterialsPack>(`/bid/projects/${projectId}/materials-pack`)).data,
  saveMaterialsPack: async (
    projectId: number,
    payload: {
      selected_certificate_ids: number[];
      selected_case_ids: number[];
      selected_personnel_ids: number[];
      selected_material_ids: number[];
      drafting_notes: string;
      confirmed: boolean;
    },
  ) => (await api.put<ProjectMaterialsPack>(`/bid/projects/${projectId}/materials-pack`, payload)).data,
  uploadProjectMaterial: async (projectId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return (
      await api.post(`/bid/upload-material/${projectId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data;
  },
  startDrafting: async (draftId: string) => (await api.post(`/bid/draft/${draftId}`)).data,
  getDraftTaskStatus: async (taskId: string) => (await api.get<DraftTaskStatus>(`/bid/draft/status/${taskId}`)).data,
  startProjectDrafting: async (projectId: number, options?: { maxSections?: number; onlyIncomplete?: boolean }) =>
    (
      await api.post(`/bid/projects/${projectId}/draft-all`, {
        ...(options?.maxSections ? { max_sections: options.maxSections } : {}),
        ...(options?.onlyIncomplete ? { only_incomplete: true } : {}),
      })
    ).data,
  getProjectDraftTaskStatus: async (taskId: string) => (await api.get<ProjectDraftTaskStatus>(`/bid/draft/status/${taskId}`)).data,
  getReview: async (projectId: number) => (await api.post<ReviewResult>(`/bid/review/${projectId}`)).data,
  getExportReadiness: async (projectId: number) => (await api.get<ExportReadiness>(`/bid/export-readiness/${projectId}`)).data,
  exportDocx: async (projectId: number) =>
    (
      await api.post(`/bid/export-docx/${projectId}`, {}, {
        responseType: 'blob',
      })
    ).data as Blob,
};

export default api;
