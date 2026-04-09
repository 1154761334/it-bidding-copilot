import { create } from 'zustand';
import { useProjectContextStore } from './useProjectContextStore';
import { biddingService, DraftDetail, DraftContentSaveResult, ProjectDraftTaskResult, ProjectMaterialsPack } from '../services/api';

export interface AgentMessage {
  agentName: string;
  status: string; // 'thinking' | 'searching' | 'writing' | 'idle'
  log: string;
  timestamp: number;
  elapsed?: number;
  finalText?: string;
}

interface BiddingState {
  isConnected: boolean;
  messages: AgentMessage[];
  activeChapter: string;
  streamingText: string;
  generationTaskId: string | null;
  generationStatus: string;
  projectGenerationTaskId: string | null;
  projectGenerationStatus: string;
  projectGenerationProgress: ProjectDraftTaskResult | null;
  materialsPack: ProjectMaterialsPack | null;
  lastSavedDraft: DraftContentSaveResult | null;
  socket: WebSocket | null;
  outline: any[];
  draftDetails: DraftDetail[];
  fetchOutline: (projectId: number) => Promise<void>;
  fetchDraftDetails: (projectId: number) => Promise<void>;
  fetchMaterialsPack: (projectId: number) => Promise<void>;
  saveMaterialsPack: (
    projectId: number,
    payload: {
      selected_certificate_ids: number[];
      selected_case_ids: number[];
      selected_personnel_ids: number[];
      selected_material_ids: number[];
      drafting_notes: string;
      confirmed: boolean;
    },
  ) => Promise<ProjectMaterialsPack | null>;
  saveDraftContent: (draftId: string, contentMarkdown: string) => Promise<DraftContentSaveResult | null>;
  uploadProjectMaterial: (projectId: number, file: File) => Promise<void>;
  connect: (draftId: string) => void;
  disconnect: () => void;
  triggerGeneration: () => Promise<void>;
  pollGenerationStatus: (taskId: string) => Promise<void>;
  triggerProjectGeneration: (projectId: number, options?: { maxSections?: number; onlyIncomplete?: boolean }) => Promise<void>;
  pollProjectGenerationStatus: (taskId: string) => Promise<void>;
  setActiveChapter: (draftId: string) => void;
}

export const useBiddingStore = create<BiddingState>((set, get) => ({
  isConnected: false,
  messages: [],
  activeChapter: '',
  streamingText: '',
  generationTaskId: null,
  generationStatus: 'idle',
  projectGenerationTaskId: null,
  projectGenerationStatus: 'idle',
  projectGenerationProgress: null,
  materialsPack: null,
  lastSavedDraft: null,
  socket: null,
  outline: [],
  draftDetails: [],

  fetchOutline: async (projectId: number) => {
    try {
      const data = await biddingService.getOutline(projectId);
      const currentActiveChapter = get().activeChapter;
      set({ outline: data.outline });
      if (data.outline.length > 0 && !currentActiveChapter) {
        set({ activeChapter: data.outline[0].id });
        useProjectContextStore.getState().setCurrentDraftId(data.outline[0].id);
      }
      await get().fetchDraftDetails(projectId);
    } catch (e) {
      console.error("Failed to fetch outline", e);
    }
  },

  fetchDraftDetails: async (projectId: number) => {
    try {
      const drafts = await biddingService.getProjectDrafts(projectId);
      set({ draftDetails: drafts });
      const activeDraft = drafts.find((item) => String(item.id) === get().activeChapter);
      if (activeDraft?.content_markdown) {
        set({ streamingText: activeDraft.content_markdown });
      }
    } catch (e) {
      console.error('Failed to fetch draft details', e);
    }
  },

  fetchMaterialsPack: async (projectId: number) => {
    try {
      const data = await biddingService.getMaterialsPack(projectId);
      set({ materialsPack: data });
    } catch (e) {
      console.error('Failed to fetch materials pack', e);
    }
  },

  saveMaterialsPack: async (projectId, payload) => {
    try {
      const data = await biddingService.saveMaterialsPack(projectId, payload);
      set({ materialsPack: data });
      return data;
    } catch (e) {
      console.error('Failed to save materials pack', e);
      return null;
    }
  },

  saveDraftContent: async (draftId, contentMarkdown) => {
    try {
      const data = await biddingService.saveDraftContent(draftId, contentMarkdown);
      set({ lastSavedDraft: data });
      const currentProjectId = useProjectContextStore.getState().currentProjectId;
      if (currentProjectId) {
        await get().fetchDraftDetails(currentProjectId);
      }
      return data;
    } catch (e) {
      console.error('Failed to save draft content', e);
      return null;
    }
  },

  uploadProjectMaterial: async (projectId, file) => {
    try {
      await biddingService.uploadProjectMaterial(projectId, file);
      await get().fetchMaterialsPack(projectId);
    } catch (e) {
      console.error('Failed to upload project material', e);
    }
  },

  setActiveChapter: (draftId: string) => {
    const { socket, activeChapter, draftDetails } = get();
    const activeDraft = draftDetails.find((item) => String(item.id) === draftId);
    const nextStreamingText = activeDraft?.content_markdown || '';
    if (socket && draftId !== activeChapter) {
        socket.close();
        set({ isConnected: false, messages: [], streamingText: nextStreamingText, activeChapter: draftId, generationStatus: 'idle', generationTaskId: null });
        useProjectContextStore.getState().setCurrentDraftId(draftId);
        get().connect(draftId);
    } else {
        set({ activeChapter: draftId, streamingText: nextStreamingText, generationStatus: 'idle', generationTaskId: null });
        useProjectContextStore.getState().setCurrentDraftId(draftId);
    }
  },

  connect: (draftId: string) => {
    if (!draftId) return;
    // Prevent multiple connections
    if (get().socket) return;
    
    // Use proper ws/wss protocol dynamically
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use window.location.host for production portability
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/api/v1/bid/stream/${draftId}`);

    ws.onopen = () => {
      set({ isConnected: true, socket: ws });
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'agent_stream') {
        const msg = data as AgentMessage;
        set((state) => ({ 
            messages: [...state.messages, msg],
        }));
        
        if (msg.finalText) {
             set((state) => ({ streamingText: state.streamingText + msg.finalText }));
        }
      }
    };

    ws.onclose = () => {
      set({ isConnected: false, socket: null });
      // In production, implement exponential backoff reconnection here
    };
  },

  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.close();
      set({ socket: null, isConnected: false });
    }
  },

  triggerGeneration: async () => {
    const { activeChapter } = get();
    if (!activeChapter) return;

    try {
      const data = await biddingService.startDrafting(activeChapter);
      set({
        streamingText: '',
        generationTaskId: data.task_id,
        generationStatus: '任务排队中',
        messages: [],
      });
      get().pollGenerationStatus(data.task_id);
    } catch (e) {
      console.error('Failed to start draft generation', e);
    }
  },

  triggerProjectGeneration: async (projectId: number, options) => {
    try {
      const data = await biddingService.startProjectDrafting(projectId, options);
      set({
        projectGenerationTaskId: data.task_id,
        projectGenerationStatus: options?.onlyIncomplete ? '未完成章节重试排队中' : '项目级任务排队中',
        projectGenerationProgress: null,
      });
      get().pollProjectGenerationStatus(data.task_id);
    } catch (e) {
      console.error('Failed to start project draft generation', e);
    }
  },

  pollGenerationStatus: async (taskId: string) => {
    try {
      const data = await biddingService.getDraftTaskStatus(taskId);
      const currentProjectId = useProjectContextStore.getState().currentProjectId;
      if (data.status === 'completed') {
        set({
          generationStatus: 'completed',
          streamingText: data.result?.content || '',
        });
        if (currentProjectId) {
          await get().fetchOutline(currentProjectId);
        }
        return;
      }

      if (data.status === 'failed') {
        set({ generationStatus: 'failed' });
        if (currentProjectId) {
          await get().fetchOutline(currentProjectId);
        }
        return;
      }

      const stageLabelMap: Record<string, string> = {
        queued: '任务排队中',
        researching: '正在检索企业资产与章节证据',
        completed: '章节生成完成',
      };
      set({ generationStatus: stageLabelMap[data.stage] || data.stage || 'running' });
      setTimeout(() => get().pollGenerationStatus(taskId), 2000);
    } catch (e) {
      console.error('Failed to poll draft task status', e);
      setTimeout(() => get().pollGenerationStatus(taskId), 2000);
    }
  },

  pollProjectGenerationStatus: async (taskId: string) => {
    try {
      const data = await biddingService.getProjectDraftTaskStatus(taskId);
      const currentProjectId = useProjectContextStore.getState().currentProjectId;
      if (data.status === 'completed') {
        set({
          projectGenerationStatus: '项目章节生成完成',
          projectGenerationProgress: data.result || null,
        });
        if (currentProjectId) {
          await get().fetchOutline(currentProjectId);
        }
        return;
      }

      if (data.status === 'failed') {
        set({ projectGenerationStatus: 'failed', projectGenerationProgress: data.result || null });
        if (currentProjectId) {
          await get().fetchOutline(currentProjectId);
        }
        return;
      }

      const stageLabelMap: Record<string, string> = {
        queued: '项目级任务排队中',
        starting: '正在初始化章节批量生成',
        generating_section: '正在逐章生成内容',
        completed: '项目章节生成完成',
      };
      set({
        projectGenerationStatus: stageLabelMap[data.stage] || data.stage || 'running',
        projectGenerationProgress: data.result || null,
      });
      setTimeout(() => get().pollProjectGenerationStatus(taskId), 2500);
    } catch (e) {
      console.error('Failed to poll project draft task status', e);
      setTimeout(() => get().pollProjectGenerationStatus(taskId), 2500);
    }
  },
}));
