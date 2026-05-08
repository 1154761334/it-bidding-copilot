import { create } from 'zustand';

import {
  approvePlan,
  type ArtifactInfo,
  type BidProject,
  type BidProjectDetail,
  createProject,
  type EvidenceResult,
  type EvidenceTraceRecord,
  getArtifact,
  getHealth,
  getProject,
  type HealthResponse,
  listArtifacts,
  listProjects,
  runDemoRealCase,
  runExecute,
  runPlan,
  runReview,
  searchEvidence,
  uploadFile,
} from '@/services/bidding';

const DEFAULT_ARTIFACT_ORDER = [
  'handoff.md',
  'draft.md',
  'response_matrix.md',
  'review.md',
  'plan.md',
  'evidence_trace.json',
];

const pickDefaultArtifact = (artifacts: ArtifactInfo[], preferred?: string) => {
  if (preferred && artifacts.some((artifact) => artifact.name === preferred)) return preferred;

  return (
    DEFAULT_ARTIFACT_ORDER.find((name) => artifacts.some((artifact) => artifact.name === name)) ??
    artifacts[0]?.name ??
    null
  );
};

const parseEvidenceTrace = (content: string): EvidenceTraceRecord[] => {
  try {
    const parsed = JSON.parse(content);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export interface BiddingState {
  approvePlanAction: (projectId: string) => Promise<void>;
  artifactLoading: boolean;

  // Artifacts
  artifacts: ArtifactInfo[];
  clearError: () => void;
  createNewProject: (name: string, bidder?: string) => Promise<string>;

  currentArtifact: string | null;
  currentArtifactName: string | null;
  currentEvidenceTrace: EvidenceTraceRecord[];
  currentProject: BidProjectDetail | null;
  demoResult: any | null;
  // Demo
  demoRunning: boolean;
  evidenceLoading: boolean;

  // Evidence
  evidenceResults: EvidenceResult[];
  executeResult: any | null;
  fetchArtifactContent: (projectId: string, name: string) => Promise<void>;

  fetchArtifacts: (projectId: string) => Promise<void>;
  // Actions
  fetchHealth: () => Promise<void>;

  fetchProjects: () => Promise<void>;
  // Health
  health: HealthResponse | null;

  healthLoading: boolean;
  // Workflow
  planResult: any | null;
  // Projects
  projects: BidProject[];
  projectsLoading: boolean;
  reviewResult: any | null;
  runDemo: () => Promise<string | null>;
  runExecuteAction: (projectId: string) => Promise<void>;
  runPlanAction: (projectId: string) => Promise<void>;
  runReviewAction: (projectId: string) => Promise<void>;
  searchEvidenceAction: (query: string, category?: string) => Promise<void>;
  selectProject: (id: string) => Promise<void>;
  uploadProjectFile: (projectId: string, file: File, purpose: string) => Promise<void>;
  workflowError: string | null;
  workflowLoading: boolean;
}

export const useBiddingStore = create<BiddingState>((set, get) => ({
  health: null,
  healthLoading: false,
  projects: [],
  currentProject: null,
  projectsLoading: false,
  planResult: null,
  executeResult: null,
  reviewResult: null,
  workflowLoading: false,
  workflowError: null,
  artifacts: [],
  currentArtifact: null,
  currentArtifactName: null,
  currentEvidenceTrace: [],
  artifactLoading: false,
  evidenceResults: [],
  evidenceLoading: false,
  demoRunning: false,
  demoResult: null,

  fetchHealth: async () => {
    set({ healthLoading: true });
    try {
      const health = await getHealth();
      set({ health, healthLoading: false });
    } catch {
      set({ healthLoading: false, health: null });
    }
  },

  fetchProjects: async () => {
    set({ projectsLoading: true });
    try {
      const { projects } = await listProjects();
      set({ projects, projectsLoading: false });
    } catch {
      set({ projectsLoading: false });
    }
  },

  createNewProject: async (name, bidder = '') => {
    set({ workflowLoading: true, workflowError: null });
    try {
      const { project_id } = await createProject(name, bidder);
      await get().fetchProjects();
      set({ workflowLoading: false });
      return project_id;
    } catch (e: any) {
      set({ workflowLoading: false, workflowError: e.message });
      throw e;
    }
  },

  selectProject: async (id) => {
    set({
      projectsLoading: true,
      workflowError: null,
      artifacts: [],
      currentArtifact: null,
      currentArtifactName: null,
      currentEvidenceTrace: [],
    });
    try {
      const project = await getProject(id);
      const { artifacts } = await listArtifacts(id);
      const projects = get().projects;
      set({
        currentProject: project,
        artifacts,
        projects: projects.some((item) => item.id === project.id)
          ? projects.map((item) => (item.id === project.id ? project : item))
          : [project, ...projects],
        projectsLoading: false,
      });
    } catch (e: any) {
      set({ projectsLoading: false, workflowError: e.message });
    }
  },

  uploadProjectFile: async (projectId, file, purpose) => {
    set({ workflowLoading: true, workflowError: null });
    try {
      await uploadFile(projectId, file, purpose);
      await get().selectProject(projectId);
      set({ workflowLoading: false });
    } catch (e: any) {
      set({ workflowLoading: false, workflowError: e.message });
    }
  },

  runPlanAction: async (projectId) => {
    set({ workflowLoading: true, workflowError: null, planResult: null });
    try {
      const result = await runPlan(projectId);
      set({ planResult: result, workflowLoading: false });
      await get().selectProject(projectId);
    } catch (e: any) {
      set({ workflowLoading: false, workflowError: e.message });
    }
  },

  approvePlanAction: async (projectId) => {
    set({ workflowLoading: true, workflowError: null });
    try {
      await approvePlan(projectId);
      set({ workflowLoading: false });
      await get().selectProject(projectId);
    } catch (e: any) {
      set({ workflowLoading: false, workflowError: e.message });
    }
  },

  runExecuteAction: async (projectId) => {
    set({ workflowLoading: true, workflowError: null, executeResult: null });
    try {
      const result = await runExecute(projectId);
      set({ executeResult: result, workflowLoading: false });
      await get().selectProject(projectId);
      const artifactName = pickDefaultArtifact(get().artifacts, 'draft.md');
      if (artifactName) await get().fetchArtifactContent(projectId, artifactName);
    } catch (e: any) {
      set({ workflowLoading: false, workflowError: e.message });
    }
  },

  runReviewAction: async (projectId) => {
    set({ workflowLoading: true, workflowError: null, reviewResult: null });
    try {
      const result = await runReview(projectId);
      set({ reviewResult: result, workflowLoading: false });
      await get().selectProject(projectId);
      const artifactName = pickDefaultArtifact(get().artifacts, 'handoff.md');
      if (artifactName) await get().fetchArtifactContent(projectId, artifactName);
    } catch (e: any) {
      set({ workflowLoading: false, workflowError: e.message });
    }
  },

  fetchArtifacts: async (projectId) => {
    try {
      const { artifacts } = await listArtifacts(projectId);
      set({ artifacts });
    } catch (e: any) {
      set({ workflowError: e.message });
    }
  },

  fetchArtifactContent: async (projectId, name) => {
    set({ artifactLoading: true, currentArtifact: null, currentArtifactName: name });
    try {
      const shouldFetchTrace =
        name !== 'evidence_trace.json' &&
        get().currentEvidenceTrace.length === 0 &&
        get().artifacts.some((artifact) => artifact.name === 'evidence_trace.json');
      const [content, traceContent] = await Promise.all([
        getArtifact(projectId, name),
        shouldFetchTrace
          ? getArtifact(projectId, 'evidence_trace.json').catch(() => null)
          : Promise.resolve(null),
      ]);
      set({
        currentArtifact: content,
        currentEvidenceTrace:
          name === 'evidence_trace.json'
            ? parseEvidenceTrace(content)
            : traceContent
              ? parseEvidenceTrace(traceContent)
              : get().currentEvidenceTrace,
        artifactLoading: false,
      });
    } catch (e: any) {
      set({ artifactLoading: false, currentArtifactName: null, workflowError: e.message });
    }
  },

  searchEvidenceAction: async (query, category) => {
    set({ evidenceLoading: true, evidenceResults: [] });
    try {
      const { results } = await searchEvidence(query, category);
      set({ evidenceResults: results, evidenceLoading: false });
    } catch (e: any) {
      set({ evidenceLoading: false, workflowError: e.message });
    }
  },

  runDemo: async () => {
    set({ demoRunning: true, demoResult: null, workflowError: null });
    try {
      const result = await runDemoRealCase();
      await get().fetchProjects();
      await get().selectProject(result.project_id);
      const artifactName = pickDefaultArtifact(get().artifacts, 'draft.md');
      if (artifactName) await get().fetchArtifactContent(result.project_id, artifactName);
      set({ demoResult: result, demoRunning: false });
      return result.project_id;
    } catch (e: any) {
      set({ demoRunning: false, workflowError: e.message });
      return null;
    }
  },

  clearError: () => set({ workflowError: null }),
}));
