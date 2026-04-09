import { create } from 'zustand';
import { configService, ModelCapabilities } from '../services/api';

interface SettingsState {
  isSettingsOpen: boolean;
  llmApiKey: string;
  llmBaseUrl: string;
  llmModel: string;
  embeddingModel: string;
  capabilities: ModelCapabilities | null;
  openSettings: () => void;
  closeSettings: () => void;
  fetchConfig: () => Promise<void>;
  fetchCapabilities: () => Promise<void>;
  updateConfig: (config: { LLM_API_KEY?: string; LLM_BASE_URL?: string; LLM_MODEL?: string; EMBEDDING_MODEL?: string }) => Promise<void>;
  testConnectivity: () => Promise<{ status: 'success' | 'error'; message: string }>;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  isSettingsOpen: false,
  llmApiKey: '',
  llmBaseUrl: 'https://ark.cn-beijing.volces.com/api/coding/v3',
  llmModel: 'Doubao-Seed-Code',
  embeddingModel: '',
  capabilities: null,
  openSettings: () => set({ isSettingsOpen: true }),
  closeSettings: () => set({ isSettingsOpen: false }),
  fetchConfig: async () => {
    try {
      const data = await configService.get();
      set({
        llmApiKey: data.LLM_API_KEY,
        llmBaseUrl: data.LLM_BASE_URL,
        llmModel: data.LLM_MODEL,
        embeddingModel: data.EMBEDDING_MODEL || '',
      });
    } catch (e) {
      console.error("Failed to fetch config", e);
    }
  },
  fetchCapabilities: async () => {
    try {
      const data = await configService.getCapabilities();
      set({ capabilities: data });
    } catch (e) {
      console.error("Failed to fetch capabilities", e);
    }
  },
  updateConfig: async (config) => {
    try {
      const payload = {
        llm_model: config.LLM_MODEL || "Doubao-Seed-Code",
        api_key: config.LLM_API_KEY,
        base_url: config.LLM_BASE_URL || "https://ark.cn-beijing.volces.com/api/coding/v3",
        embedding_model: config.EMBEDDING_MODEL ?? "",
      };
      await configService.update(payload);
      // Re-fetch to ensure sync
      const data = await configService.get();
      set({
        llmApiKey: data.LLM_API_KEY,
        llmBaseUrl: data.LLM_BASE_URL,
        llmModel: data.LLM_MODEL,
        embeddingModel: data.EMBEDDING_MODEL || '',
        isSettingsOpen: false, 
      });
      await useSettingsStore.getState().fetchCapabilities();
    } catch (e) {
      console.error("Failed to update config", e);
    }
  },
  testConnectivity: async () => {
    try {
      return await configService.testConnection();
    } catch (e) {
      return { status: 'error', message: 'Network error or service unavailable' };
    }
  }
}));
