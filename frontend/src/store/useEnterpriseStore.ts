import { create } from 'zustand';
import { useProjectContextStore } from './useProjectContextStore';
import {
  EnterpriseAssetBrowserResponse,
  EnterpriseAssetsOverview,
  EnterpriseIntakeReadiness,
  EnterpriseLatestIngestBatch,
  enterpriseService,
} from '../services/api';

interface EnterpriseState {
  profile: any;
  trustScore: any;
  assetsOverview: EnterpriseAssetsOverview | null;
  intakeReadiness: EnterpriseIntakeReadiness | null;
  latestIngestBatch: EnterpriseLatestIngestBatch | null;
  assetsBrowser: EnterpriseAssetBrowserResponse | null;
  isLoading: boolean;
  error: string | null;
  fetchProfile: () => Promise<void>;
  fetchAssetsBrowser: (companyId: number, assetKind?: string, query?: string) => Promise<void>;
  updateProfile: (data: any) => Promise<void>;
  uploadAssets: (companyId: number, files: File[]) => Promise<void>;
  uploadQueue: any[];
}

export const useEnterpriseStore = create<EnterpriseState>((set) => ({
  profile: null,
  trustScore: null,
  assetsOverview: null,
  intakeReadiness: null,
  latestIngestBatch: null,
  assetsBrowser: null,
  isLoading: false,
  error: null,
  uploadQueue: [],
  fetchProfile: async () => {
    set({ isLoading: true });
    try {
      const dataProfile = await enterpriseService.getProfile();
      useProjectContextStore.getState().setCurrentCompanyId(dataProfile.id ?? null);
      useProjectContextStore.getState().setCurrentCompanyName(dataProfile.company_name ?? null);

      const dataScore = await enterpriseService.getTrustScore();
      const dataAssetsOverview = dataProfile.id ? await enterpriseService.getAssetsOverview(dataProfile.id) : null;
      const dataAssetsBrowser = dataProfile.id ? await enterpriseService.getAssetsBrowser(dataProfile.id) : null;
      const dataIntakeReadiness = dataProfile.id ? await enterpriseService.getIntakeReadiness(dataProfile.id) : null;
      const dataLatestIngestBatch = dataProfile.id ? await enterpriseService.getLatestIngestBatch(dataProfile.id) : null;

      set({
        profile: dataProfile,
        trustScore: dataScore,
        assetsOverview: dataAssetsOverview,
        intakeReadiness: dataIntakeReadiness,
        latestIngestBatch: dataLatestIngestBatch,
        assetsBrowser: dataAssetsBrowser,
        isLoading: false,
      });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },
  fetchAssetsBrowser: async (companyId, assetKind = 'all', query = '') => {
    if (!companyId) {
      set({ assetsBrowser: null });
      return;
    }

    set({ isLoading: true });
    try {
      const data = await enterpriseService.getAssetsBrowser(companyId, assetKind, query);
      set({ assetsBrowser: data, isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },
  updateProfile: async (data) => {
    set({ isLoading: true });
    try {
      const result = await enterpriseService.updateProfile(data);
      set({ profile: result.profile, isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },
  uploadAssets: async (companyId, files) => {
    if (!companyId) {
      set({ error: '请先完善企业档案，再上传资产。' });
      return;
    }

    set({ isLoading: true });
    
    // 初始化上传队列
    const initialQueue = files.map(f => ({ name: f.name, progress: 10, status: 'uploading' }));
    set({ uploadQueue: initialQueue });

    try {
      await enterpriseService.bulkIngest(companyId, files);
      
      // 更新成功后的队列状态
      set({ 
        uploadQueue: files.map(f => ({ name: f.name, progress: 100, status: 'completed' })),
        isLoading: false 
      });
      
      await useEnterpriseStore.getState().fetchProfile();
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },
}));
