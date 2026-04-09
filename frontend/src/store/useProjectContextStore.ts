import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { dashboardService } from '../services/api';

interface ProjectContextState {
  currentCompanyId: number | null;
  currentCompanyName: string | null;
  currentProjectId: number | null;
  currentProjectName: string | null;
  currentDraftId: string | null;
  bootstrapContext: () => Promise<void>;
  setCurrentCompanyId: (companyId: number | null) => void;
  setCurrentCompanyName: (companyName: string | null) => void;
  setCurrentProjectId: (projectId: number | null) => void;
  setCurrentProjectName: (projectName: string | null) => void;
  setCurrentDraftId: (draftId: string | null) => void;
  clearProjectContext: () => void;
}

export const useProjectContextStore = create<ProjectContextState>()(
  persist(
    (set) => ({
      currentCompanyId: null,
      currentCompanyName: null,
      currentProjectId: null,
      currentProjectName: null,
      currentDraftId: null,
      bootstrapContext: async () => {
        try {
          const data = await dashboardService.getContext();
          set((state) => ({
            currentCompanyId: data.current_company_id ?? state.currentCompanyId,
            currentCompanyName: data.current_company_name ?? state.currentCompanyName,
            currentProjectId: data.current_project_id ?? state.currentProjectId,
            currentProjectName: data.current_project_name ?? state.currentProjectName,
            currentDraftId: data.current_draft_id ?? state.currentDraftId,
          }));
        } catch (error) {
          console.error('Failed to bootstrap project context', error);
        }
      },
      setCurrentCompanyId: (companyId) => set({ currentCompanyId: companyId }),
      setCurrentCompanyName: (companyName) => set({ currentCompanyName: companyName }),
      setCurrentProjectId: (projectId) => set({ currentProjectId: projectId }),
      setCurrentProjectName: (projectName) => set({ currentProjectName: projectName }),
      setCurrentDraftId: (draftId) => set({ currentDraftId: draftId }),
      clearProjectContext: () => set({ currentProjectId: null, currentProjectName: null, currentDraftId: null }),
    }),
    {
      name: 'project-context',
    },
  ),
);
