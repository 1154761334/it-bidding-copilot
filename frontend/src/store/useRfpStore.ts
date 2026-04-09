import { create } from 'zustand';
import { useProjectContextStore } from './useProjectContextStore';
import { AnalysisCheck, RfpResult, rfpService } from '../services/api';

export interface BiddingRequirement {
  item: string;
  category?: string;
  is_mandatory?: boolean;
  requirement?: string; // for veto clauses
  source?: {
    page: number;
    bbox: number[];
    text: string;
  }
  // Industrial fields
  param_name?: string;
  required_value?: string;
  component?: string;
}

interface RfpState {
  isAnalyzing: boolean;
  taskId: string | null;
  taskStage: string;
  statusText: string;
  analysisResult: RfpResult | null;
  analysisCheck: AnalysisCheck | null;
  hydrateProjectAnalysis: (projectId: number) => Promise<void>;
  analyzeRfp: (file: File) => Promise<void>;
  pollStatus: (taskId: string) => Promise<void>;
}

export const useRfpStore = create<RfpState>((set, get) => ({
  isAnalyzing: false,
  taskId: null,
  taskStage: '',
  statusText: '',
  analysisResult: null,
  analysisCheck: null,

  hydrateProjectAnalysis: async (projectId: number) => {
    try {
      const [analysisResult, analysisCheck] = await Promise.all([
        rfpService.getProjectAnalysis(projectId),
        rfpService.getAnalysisCheck(projectId),
      ]);
      set({
        analysisResult,
        analysisCheck,
        taskStage: 'completed',
        statusText: '已恢复当前项目的采购文件分析结果',
      });
    } catch (error) {
      console.error('Failed to hydrate project analysis', error);
    }
  },

  analyzeRfp: async (file: File) => {
    set({ isAnalyzing: true, taskId: null, taskStage: 'uploading', statusText: '上传标书中...', analysisResult: null, analysisCheck: null });

    try {
      const data = await rfpService.analyze(file);
      const taskId = data.task_id;
      const result = data.result;
      if (result?.project_id) {
        useProjectContextStore.getState().setCurrentProjectId(result.project_id);
        useProjectContextStore.getState().setCurrentProjectName(result.project_name ?? null);
      }

      if (data.status === 'completed' && result) {
        const analysisCheck = result.project_id ? await rfpService.getAnalysisCheck(result.project_id) : null;
        set({
          taskId,
          isAnalyzing: false,
          taskStage: 'completed',
          statusText: '解析完成！',
          analysisResult: result,
          analysisCheck,
        });
        return;
      }

      set({ taskId, taskStage: 'queued', statusText: '标书已上传，正在创建解析任务...' });
      
      // Start polling
      get().pollStatus(taskId);
    } catch (e) {
      set({ isAnalyzing: false, taskStage: 'failed', statusText: '上传失败: ' + (e as Error).message });
    }
  },

  pollStatus: async (taskId: string) => {
    try {
      const data = await rfpService.getTaskStatus(taskId);
      
      if (data.status === 'completed') {
        const analysisCheck = data.result?.project_id ? await rfpService.getAnalysisCheck(data.result.project_id) : null;
        if (data.result?.project_id) {
          useProjectContextStore.getState().setCurrentProjectId(data.result.project_id);
          useProjectContextStore.getState().setCurrentProjectName(data.result.project_name ?? null);
        }
        set({ isAnalyzing: false, taskStage: 'completed', statusText: '解析完成！', analysisResult: data.result, analysisCheck });
      } else if (data.status === 'failed') {
        set({ isAnalyzing: false, taskStage: 'failed', statusText: '解析失败: ' + data.error });
      } else {
        const stageTextMap: Record<string, string> = {
          queued: '任务已创建，正在排队处理中...',
          ingesting_source: '正在写入招标源文件...',
          parsing_document: '正在解析招标文件结构与正文...',
          extracting_project_meta: '正在提取项目名称、编号、预算和截止时间...',
          classifying_sections: '正在识别章节结构与文档分区...',
          extracting_requirements: '正在提取废标条款、评分点和需求项...',
          matching_assets: '正在将招标要求与企业资产进行匹配...',
          calculating_decision: '正在计算可投性和中标建议...',
          validating_analysis: '正在执行分析质量校验与结果复核...',
        };
        set({ taskStage: data.stage || 'running', statusText: stageTextMap[data.stage] || 'AI 正在深度解构标书要求，提炼废标条款与核心评分点...' });
        setTimeout(() => get().pollStatus(taskId), 2000); // Polling interval 2s
      }
    } catch (e) {
       // if not found, keep trying or fail
       setTimeout(() => get().pollStatus(taskId), 2000);
    }
  }
}));
