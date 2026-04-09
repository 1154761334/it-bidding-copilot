import React, { useEffect, useState } from 'react';
import { useSettingsStore } from '../../store/useSettingsStore';

const recommendedModels = [
  { value: 'Doubao-Seed-Code', label: 'Doubao-Seed-Code', note: '当前默认推荐，适合编标与工作流联调' },
  { value: 'Doubao-Seed-2.0-Code', label: 'Doubao-Seed-2.0-Code', note: '偏代码与工具调用能力' },
  { value: 'Doubao-Seed-2.0-pro', label: 'Doubao-Seed-2.0-pro', note: '复杂推理与长链路任务' },
  { value: 'Doubao-Seed-2.0-lite', label: 'Doubao-Seed-2.0-lite', note: '速度优先的通用模型' },
  { value: 'MiniMax-M2.5', label: 'MiniMax-M2.5', note: '编程与工具调用兼顾' },
  { value: 'Kimi-K2.5', label: 'Kimi-K2.5', note: '前端与长上下文能力较强' },
  { value: 'GLM-4.7', label: 'GLM-4.7', note: '长代码库理解与 Agent 任务' },
  { value: 'DeepSeek-V3.2', label: 'DeepSeek-V3.2', note: '轻量开发与通用任务' },
  { value: 'Auto', label: 'Auto', note: '智能调度，但结构化调用兼容性较弱' },
];

const SettingsDialog: React.FC = () => {
  const {
    isSettingsOpen,
    closeSettings,
    fetchConfig,
    fetchCapabilities,
    updateConfig,
    testConnectivity,
    llmApiKey,
    llmBaseUrl,
    llmModel,
    embeddingModel,
    capabilities,
  } = useSettingsStore();
  
  const [key, setKey] = useState(llmApiKey);
  const [url, setUrl] = useState(llmBaseUrl);
  const [model, setModel] = useState(llmModel);
  const [embedding, setEmbedding] = useState(embeddingModel);
  const [testResult, setTestResult] = useState<{ status: 'success' | 'error'; message: string } | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const modelOptions = recommendedModels.some((item) => item.value === model)
    ? recommendedModels
    : [...recommendedModels, { value: model, label: `${model}（当前配置）`, note: '当前运行时已配置的自定义模型' }];

  useEffect(() => {
    if (isSettingsOpen) {
      fetchConfig();
      fetchCapabilities();
      setTestResult(null);
    }
  }, [isSettingsOpen, fetchConfig, fetchCapabilities]);

  useEffect(() => {
    // Update local state when store fetch completes
    setKey(llmApiKey);
    setUrl(llmBaseUrl);
    setModel(llmModel);
    setEmbedding(embeddingModel);
  }, [llmApiKey, llmBaseUrl, llmModel, embeddingModel]);

  useEffect(() => {
    if (!isSettingsOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeSettings();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeSettings, isSettingsOpen]);

  if (!isSettingsOpen) return null;

  const handleSave = () => {
    updateConfig({
      LLM_API_KEY: key !== '********' ? key : undefined, // Only update if masked value was overwritten
      LLM_BASE_URL: url,
      LLM_MODEL: model,
      EMBEDDING_MODEL: embedding,
    });
  };

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await testConnectivity();
      setTestResult(res);
    } catch (err) {
      setTestResult({ status: 'error', message: '服务连接超时' });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-zinc-900/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl p-8 max-w-lg w-full ambient-shadow shadow-2xl relative animate-in fade-in zoom-in duration-200">
        <button 
          onClick={closeSettings}
          className="absolute top-6 right-6 text-zinc-400 hover:text-zinc-600 transition-colors"
        >
          <span className="material-symbols-outlined">close</span>
        </button>
        
        <h2 className="text-2xl font-black text-primary mb-2">系统核心配置</h2>
        <p className="text-sm text-secondary font-medium mb-8">
          配置底层引擎调用的 LLM API 密钥及相关参数。这些配置将即时生效并应用于所有智能体工作流。
        </p>

        <div className="space-y-6">
          <div>
            <label className="block text-[11px] font-black text-secondary uppercase tracking-widest mb-2">
              LLM Model (模型引擎)
            </label>
            <select 
              value={model}
              onChange={e => setModel(e.target.value)}
              className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 text-sm font-bold text-primary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all appearance-none outline-none"
            >
              {modelOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="text-[10px] text-zinc-400 font-medium mt-2">
              {modelOptions.find((option) => option.value === model)?.note || '建议优先使用显式模型名，避免结构化调用兼容性波动。'}
            </p>
          </div>

          <div>
            <label className="block text-[11px] font-black text-secondary uppercase tracking-widest mb-2">
              API Base URL (端点地址)
            </label>
            <input 
              type="text" 
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="例如: https://ark.cn-beijing.volces.com/api/coding/v3"
              className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 text-sm font-medium text-primary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
            />
            <p className="text-[10px] text-zinc-400 font-medium mt-2">
              当前项目默认按 Ark OpenAI 兼容协议运行，推荐地址为 `https://ark.cn-beijing.volces.com/api/coding/v3`。
            </p>
          </div>

          <div>
            <label className="block text-[11px] font-black text-secondary uppercase tracking-widest mb-2">
              API Key (接口密钥)
            </label>
            <input 
              type="password" 
              value={key}
              onChange={e => setKey(e.target.value)}
              placeholder="sk-..."
              className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 text-sm font-mono text-primary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
            />
            <p className="text-[10px] text-zinc-400 font-medium mt-2">
              如果已有保存的密钥，输入框将显示掩码 `********`。输入新密钥将覆写当前配置。
            </p>
          </div>

          <div>
            <label className="block text-[11px] font-black text-secondary uppercase tracking-widest mb-2">
              Embedding Model (向量模型)
            </label>
            <input 
              type="text" 
              value={embedding}
              onChange={e => setEmbedding(e.target.value)}
              placeholder="未配置时可留空，系统将降级为零向量"
              className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 text-sm font-medium text-primary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
            />
          </div>

          {testResult && (
            <div className={`p-4 rounded-xl text-xs font-bold flex items-center gap-3 animate-in slide-in-from-top-2 ${testResult.status === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
              <span className="material-symbols-outlined text-lg">{testResult.status === 'success' ? 'check_circle' : 'error'}</span>
              {testResult.message}
            </div>
          )}

          {capabilities && (
            <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-widest text-secondary">Runtime Capabilities</p>
                  <p className="text-xs text-zinc-500 font-medium mt-1">当前模型、向量与 fallback 运行状态</p>
                </div>
                <span className={`text-[10px] font-black uppercase tracking-widest ${capabilities.chat_enabled ? 'text-emerald-600' : 'text-red-600'}`}>
                  {capabilities.chat_enabled ? 'chat ready' : 'chat unavailable'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="rounded-xl bg-white p-3 border border-zinc-100">
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-1">LLM</p>
                  <p className="text-xs font-bold text-primary break-all">{capabilities.llm_model}</p>
                </div>
                <div className="rounded-xl bg-white p-3 border border-zinc-100">
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-1">Embedding</p>
                  <p className="text-xs font-bold text-primary break-all">{capabilities.embedding_model || '未配置'}</p>
                </div>
              </div>
              <div className="space-y-2">
                {Object.entries(capabilities.fallbacks).map(([keyName, enabled]) => (
                  <div key={keyName} className="flex items-center justify-between rounded-xl bg-white px-3 py-2 border border-zinc-100">
                    <span className="text-[11px] font-bold text-zinc-600">{keyName}</span>
                    <span className={`text-[10px] font-black uppercase tracking-widest ${enabled ? 'text-emerald-600' : 'text-zinc-400'}`}>
                      {enabled ? 'enabled' : 'disabled'}
                    </span>
                  </div>
                ))}
              </div>
              {capabilities.compatibility_notes.length > 0 && (
                <div className="mt-4 space-y-2">
                  {capabilities.compatibility_notes.map((note) => (
                    <div key={note} className="rounded-xl bg-amber-50 border border-amber-100 px-3 py-2 text-[11px] font-medium text-amber-900">
                      {note}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="mt-10 flex justify-end gap-3">
          <button 
            onClick={handleTest}
            disabled={isTesting}
            className="px-6 py-3 text-xs font-black uppercase tracking-widest text-zinc-500 hover:bg-zinc-50 rounded-xl transition-colors flex items-center gap-2 border border-zinc-200"
          >
            <span className={`material-symbols-outlined text-sm ${isTesting ? 'animate-spin' : ''}`}>sync</span>
            {isTesting ? '正在测试...' : '测试接口连通性'}
          </button>
          <button 
            onClick={handleSave}
            className="px-8 py-3 text-xs font-black uppercase tracking-widest bg-primary text-white rounded-xl shadow-lg shadow-primary/20 hover:opacity-90 active:scale-95 transition-all flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm filled">save</span>
            保存并应用
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsDialog;
