import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { rfpService } from '../services/api';
import { useRfpStore } from '../store/useRfpStore';
import { useProjectContextStore } from '../store/useProjectContextStore';

const formatCheckDetail = (detail: unknown) => {
  if (detail === null || detail === undefined || detail === '') {
    return '暂无详细信息';
  }
  if (typeof detail === 'string' || typeof detail === 'number' || typeof detail === 'boolean') {
    return String(detail);
  }
  if (Array.isArray(detail)) {
    return detail.length ? detail.map((item) => String(item)).join('，') : '暂无详细信息';
  }
  if (typeof detail === 'object') {
    return Object.entries(detail as Record<string, unknown>)
      .map(([key, value]) => `${key}: ${String(value)}`)
      .join('；');
  }
  return String(detail);
};

const RFPAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const { currentProjectId, bootstrapContext, setCurrentProjectName } = useProjectContextStore();
  const { isAnalyzing, statusText, taskStage, analysisResult, analysisCheck, analyzeRfp, hydrateProjectAnalysis } = useRfpStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState('商业资质');
  const [showAllChecks, setShowAllChecks] = useState(false);
  const [projectForm, setProjectForm] = useState({ name: '', budget: '', deadline: '' });
  const [editingRequirements, setEditingRequirements] = useState<Record<number, { description: string; evidence_required: string }>>({});
  const [isSavingConfirm, setIsSavingConfirm] = useState(false);
  const [confirmMessage, setConfirmMessage] = useState<string | null>(null);

  React.useEffect(() => {
    bootstrapContext();
  }, [bootstrapContext]);

  React.useEffect(() => {
    if (currentProjectId && (!analysisResult || analysisCheck?.project_id !== currentProjectId)) {
      void hydrateProjectAnalysis(currentProjectId);
    }
  }, [analysisCheck?.project_id, analysisResult, currentProjectId, hydrateProjectAnalysis]);

  React.useEffect(() => {
    if (!analysisResult) {
      setProjectForm({ name: '', budget: '', deadline: '' });
      setEditingRequirements({});
      setConfirmMessage(null);
      return;
    }
    setProjectForm({
      name: analysisResult.project_name || analysisResult.project_info?.name || '',
      budget: analysisResult.budget ? String(analysisResult.budget) : '',
      deadline: analysisResult.bid_deadline || '',
    });

    const nextEditingState: Record<number, { description: string; evidence_required: string }> = {};
    analysisResult.commercial_requirements.forEach((item) => {
      nextEditingState[item.id] = { description: item.item, evidence_required: item.evidence_required || '' };
    });
    analysisResult.technical_requirements.forEach((item) => {
      nextEditingState[item.id] = { description: item.required_value || item.item, evidence_required: item.evidence_required || '' };
    });
    analysisResult.veto_clauses.forEach((item) => {
      nextEditingState[item.id] = { description: item.requirement, evidence_required: item.evidence_required || '' };
    });
    setEditingRequirements(nextEditingState);
  }, [analysisResult]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      analyzeRfp(e.target.files[0]);
    }
  };

  const updateRequirementDraft = (id: number, field: 'description' | 'evidence_required', value: string) => {
    setEditingRequirements((prev) => ({
      ...prev,
      [id]: {
        description: prev[id]?.description || '',
        evidence_required: prev[id]?.evidence_required || '',
        [field]: value,
      },
    }));
  };

  const handleConfirmAnalysis = async () => {
    if (!analysisResult?.project_id) return;
    setIsSavingConfirm(true);
    setConfirmMessage(null);
    try {
      const requirements = [
        ...analysisResult.commercial_requirements.map((item) => ({
          id: item.id,
          description: editingRequirements[item.id]?.description || item.item,
          category: item.category,
          is_fatal: item.is_mandatory,
          evidence_required: editingRequirements[item.id]?.evidence_required || item.evidence_required || '',
          max_score: item.max_score,
        })),
        ...analysisResult.technical_requirements.map((item) => ({
          id: item.id,
          description: editingRequirements[item.id]?.description || item.required_value || item.item,
          category: item.category,
          is_fatal: false,
          evidence_required: editingRequirements[item.id]?.evidence_required || item.evidence_required || '',
          max_score: item.max_score,
        })),
        ...analysisResult.veto_clauses.map((item) => ({
          id: item.id,
          description: editingRequirements[item.id]?.description || item.requirement,
          category: item.category,
          is_fatal: true,
          evidence_required: editingRequirements[item.id]?.evidence_required || item.evidence_required || '',
          max_score: item.max_score,
        })),
      ];
      const response = await rfpService.confirmAnalysis(analysisResult.project_id, {
        project_info: {
          name: projectForm.name.trim(),
          budget: Number(projectForm.budget || 0),
          deadline: projectForm.deadline,
        },
        requirements,
      });
      setCurrentProjectName(projectForm.name.trim() || analysisResult.project_name);
      setConfirmMessage(`已确认并保存 ${response.updated_requirements} 条识别结果，项目可进入下一步。`);
      await hydrateProjectAnalysis(analysisResult.project_id);
    } catch (error) {
      setConfirmMessage(`保存失败：${(error as Error).message}`);
    } finally {
      setIsSavingConfirm(false);
    }
  };

  const activeRequirements = React.useMemo(() => {
    if (!analysisResult) return [];
    if (activeTab === '商业资质') {
      return analysisResult.commercial_requirements.map((item) => ({
        id: item.id,
        title: item.item,
        badge: item.category || 'QUALIFICATION',
        evidence: item.evidence_required || '',
        mandatory: !!item.is_mandatory,
      }));
    }
    if (activeTab === '技术规范') {
      return analysisResult.technical_requirements.map((item) => ({
        id: item.id,
        title: item.required_value || item.item,
        badge: item.component || item.category || 'TECHNICAL',
        evidence: item.evidence_required || '',
        mandatory: false,
      }));
    }
    if (activeTab === '废标条款') {
      return analysisResult.veto_clauses.map((item) => ({
        id: item.id,
        title: item.requirement,
        badge: item.category || 'FATAL',
        evidence: item.evidence_required || '',
        mandatory: true,
      }));
    }
    return [];
  }, [activeTab, analysisResult, editingRequirements]);

  const analysisConfirmed = analysisResult?.project_status === 'ANALYSIS_CONFIRMED' || analysisResult?.project_status === 'DEVIATION_CONFIRMED';
  const commercialCount = analysisResult?.commercial_requirements.length ?? 0;
  const technicalCount = analysisResult?.technical_requirements.length ?? 0;
  const vetoCount = analysisResult?.veto_clauses.length ?? 0;
  const scoringCount = Object.keys(analysisResult?.scoring_system || {}).length;
  const totalRequirements = commercialCount + technicalCount + vetoCount;
  const qualityWarnings = analysisCheck?.quality_report.warnings ?? [];
  const reviewNeeded = analysisCheck?.quality_report.status === 'needs_review';
  const editedRequirementCount = React.useMemo(() => {
    if (!analysisResult) return 0;

    let totalEdited = 0;
    const seen = new Set<number>();
    const countIfChanged = (id: number, originalDescription: string, originalEvidence: string) => {
      if (seen.has(id)) return;
      seen.add(id);

      const edited = editingRequirements[id];
      if (!edited) return;

      const normalizedDescription = (edited.description || '').trim();
      const normalizedEvidence = (edited.evidence_required || '').trim();
      if (
        normalizedDescription !== (originalDescription || '').trim() ||
        normalizedEvidence !== (originalEvidence || '').trim()
      ) {
        totalEdited += 1;
      }
    };

    analysisResult.commercial_requirements.forEach((item) => {
      countIfChanged(item.id, item.item, item.evidence_required || '');
    });
    analysisResult.technical_requirements.forEach((item) => {
      countIfChanged(item.id, item.required_value || item.item, item.evidence_required || '');
    });
    analysisResult.veto_clauses.forEach((item) => {
      countIfChanged(item.id, item.requirement, item.evidence_required || '');
    });

    return totalEdited;
  }, [analysisResult, editingRequirements]);
  const tabDefinitions = [
    { key: '商业资质', label: '商业资质', count: commercialCount },
    { key: '技术规范', label: '技术规范', count: technicalCount },
    { key: '废标条款', label: '废标条款', count: vetoCount },
    { key: '评分标准', label: '评分标准', count: scoringCount },
  ];
  const nextStepBlockedReason = reviewNeeded
    ? '当前 quality check 仍需人工复核，暂不允许进入偏离矩阵。'
    : !analysisConfirmed && analysisResult
      ? '当前仍是分析预览态，确认建档后才会作为正式项目基线。'
      : null;

  return (
    <div className="flex-1 overflow-y-auto no-scrollbar bg-surface pt-8 pb-32 px-12">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight text-primary mb-2">RFP 标书智能解构</h1>
            <p className="text-secondary text-lg font-light">上传招标文件，AI 将自动提取核心商务与技术要点，并评估投标可行性。</p>
          </div>
          <div className="flex gap-4">
              <button
                disabled
                className="px-6 py-2 border border-zinc-200 rounded-lg text-sm font-bold text-zinc-400 bg-zinc-50 cursor-not-allowed"
                title="历史报告页尚未进入当前迭代范围"
              >
                历史报告（后续）
              </button>
              <input type="file" ref={fileInputRef} className="hidden" accept=".pdf,.doc,.docx" onChange={handleFileUpload} />
              <button 
                onClick={() => fileInputRef.current?.click()}
                disabled={isAnalyzing}
                className="px-8 py-3 bg-primary text-on-primary rounded-xl text-sm font-bold tracking-widest uppercase hover:opacity-90 active:scale-95 transition-all ambient-shadow flex items-center gap-2 disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-lg">{isAnalyzing ? 'sync' : 'upload'}</span>
                {isAnalyzing ? '分析中...' : '上传标书'}
              </button>
          </div>
        </header>

        <div className="grid grid-cols-12 gap-8">
            {/* Left: Decomposition Tabs */}
            <div className="col-span-12 lg:col-span-8 space-y-8">
                <div className="bg-white rounded-2xl border border-zinc-100 ambient-shadow overflow-hidden">
                    <div className="flex flex-wrap border-b border-zinc-50 px-4">
                        {tabDefinitions.map((tab, idx) => (
                            <button 
                              key={idx} 
                              onClick={() => setActiveTab(tab.key)}
                              className={`px-6 py-4 text-sm font-bold tracking-tight transition-colors border-b-2 ${activeTab === tab.key ? 'border-primary text-primary' : 'border-transparent text-secondary hover:text-zinc-900'}`}
                            >
                                <span>{tab.label}</span>
                                <span className={`ml-2 rounded-full px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${activeTab === tab.key ? 'bg-primary/10 text-primary' : 'bg-zinc-100 text-zinc-500'}`}>
                                  {tab.count}
                                </span>
                            </button>
                        ))}
                    </div>
                    <div className="p-8 space-y-6">
                        {analysisResult && (
                          <div className={`rounded-2xl border p-5 ${analysisConfirmed ? 'border-emerald-200 bg-emerald-50/60' : 'border-amber-200 bg-amber-50/60'}`}>
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">确认工作台状态</p>
                                <p className="text-sm font-bold text-zinc-900">
                                  {analysisConfirmed ? '当前采购文件分析结果已确认建档' : '当前结果仍处于预览态，尚未写入正式项目基线'}
                                </p>
                              </div>
                              <span className={`rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-widest ${analysisConfirmed ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                                {analysisConfirmed ? '正式基线' : '仅预览'}
                              </span>
                            </div>
                            <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
                              <div className="rounded-xl bg-white/80 px-4 py-3">
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">要求总数</p>
                                <p className="mt-2 text-xl font-black text-zinc-900">{totalRequirements}</p>
                              </div>
                              <div className="rounded-xl bg-white/80 px-4 py-3">
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">已修改要求</p>
                                <p className="mt-2 text-xl font-black text-zinc-900">{editedRequirementCount}</p>
                              </div>
                              <div className="rounded-xl bg-white/80 px-4 py-3">
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">评分类别</p>
                                <p className="mt-2 text-xl font-black text-zinc-900">{scoringCount}</p>
                              </div>
                              <div className="rounded-xl bg-white/80 px-4 py-3">
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">质量警告</p>
                                <p className={`mt-2 text-xl font-black ${qualityWarnings.length > 0 ? 'text-amber-700' : 'text-emerald-700'}`}>{qualityWarnings.length}</p>
                              </div>
                            </div>
                            {!analysisConfirmed && (
                              <p className="mt-4 text-xs font-medium text-amber-800">
                                未确认前，这些修改仅作为当前分析预览，不应被视为后续偏离矩阵与编标阶段的正式输入。
                              </p>
                            )}
                          </div>
                        )}
                        {analysisResult && (
                          <div className="rounded-2xl border border-zinc-200 bg-zinc-50/60 p-5">
                            <div className="mb-4 flex items-center justify-between gap-4">
                              <div>
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">项目建档确认</p>
                                <p className="text-sm font-bold text-zinc-900">先修正项目信息和关键要求，再确认进入偏离矩阵与编标。</p>
                              </div>
                              <div className="flex items-center gap-3">
                                {analysisConfirmed && (
                                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-emerald-700">
                                    已确认建档
                                  </span>
                                )}
                                <button
                                  onClick={handleConfirmAnalysis}
                                  disabled={isSavingConfirm}
                                  className="rounded-xl bg-primary px-5 py-3 text-[11px] font-black uppercase tracking-[0.2em] text-white disabled:opacity-50"
                                >
                                  {isSavingConfirm ? '保存中...' : '确认分析结果'}
                                </button>
                                <button
                                  onClick={() => navigate('/deviation')}
                                  disabled={!analysisConfirmed || reviewNeeded}
                                  className="rounded-xl border border-zinc-200 bg-white px-5 py-3 text-[11px] font-black uppercase tracking-[0.2em] text-zinc-700 disabled:cursor-not-allowed disabled:opacity-40"
                                >
                                  进入偏离矩阵
                                </button>
                              </div>
                            </div>
                            <div className="grid gap-4 md:grid-cols-3">
                              <label className="space-y-2">
                                <span className="text-[11px] font-bold text-zinc-500">项目名称</span>
                                <input value={projectForm.name} onChange={(e) => setProjectForm((prev) => ({ ...prev, name: e.target.value }))} className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none focus:border-primary" />
                              </label>
                              <label className="space-y-2">
                                <span className="text-[11px] font-bold text-zinc-500">预算</span>
                                <input value={projectForm.budget} onChange={(e) => setProjectForm((prev) => ({ ...prev, budget: e.target.value }))} className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none focus:border-primary" />
                              </label>
                              <label className="space-y-2">
                                <span className="text-[11px] font-bold text-zinc-500">投标截止日</span>
                                <input type="date" value={projectForm.deadline} onChange={(e) => setProjectForm((prev) => ({ ...prev, deadline: e.target.value }))} className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none focus:border-primary" />
                              </label>
                            </div>
                            {confirmMessage ? <p className="mt-3 text-xs font-bold text-primary">{confirmMessage}</p> : null}
                            {nextStepBlockedReason ? <p className="mt-3 text-xs font-medium text-zinc-500">{nextStepBlockedReason}</p> : null}
                          </div>
                        )}
                        {analysisCheck && (
                          <div className={`rounded-xl border p-4 ${analysisCheck.quality_report.status === 'passed' ? 'border-emerald-200 bg-emerald-50/60' : 'border-amber-200 bg-amber-50/60'}`}>
                            <div className="flex items-center justify-between gap-4">
                              <div>
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Analysis Check</p>
                                <p className="text-sm font-bold text-zinc-900">
                                  {analysisCheck.quality_report.status === 'passed' ? '采购文件识别通过质量校验' : '采购文件识别需要人工复核'}
                                </p>
                              </div>
                              <span className={`rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-widest ${analysisCheck.quality_report.status === 'passed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                                {analysisCheck.quality_report.passed_checks}/{analysisCheck.quality_report.total_checks}
                              </span>
                            </div>
                            <div className="mt-4 grid grid-cols-2 gap-3 text-[11px] font-bold text-zinc-700 md:grid-cols-4">
                              <div className="rounded-lg bg-white/80 px-3 py-2">要求数 {analysisCheck.quality_report.metrics.requirements_total}</div>
                              <div className="rounded-lg bg-white/80 px-3 py-2">评分项 {analysisCheck.quality_report.metrics.scoring_count}</div>
                              <div className="rounded-lg bg-white/80 px-3 py-2">废标项 {analysisCheck.quality_report.metrics.fatal_count}</div>
                              <div className="rounded-lg bg-white/80 px-3 py-2">证据项 {analysisCheck.quality_report.metrics.evidence_count}</div>
                            </div>
                            {analysisCheck.quality_report.warnings.length > 0 && (
                              <div className="mt-4 space-y-2">
                                {analysisCheck.quality_report.warnings.slice(0, 3).map((warning, idx) => (
                                  <p key={idx} className="text-[11px] font-medium text-amber-700">{warning}</p>
                                ))}
                              </div>
                            )}
                            <div className="mt-4 rounded-xl bg-white/80 p-4">
                              <div className="mb-3 flex items-center justify-between">
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">完整检查项</p>
                                <button
                                  onClick={() => setShowAllChecks((value) => !value)}
                                  className="text-[10px] font-black uppercase tracking-widest text-primary"
                                >
                                  {showAllChecks ? '收起' : '展开'}
                                </button>
                              </div>
                              <div className="space-y-2">
                                {(showAllChecks ? analysisCheck.quality_report.checks : analysisCheck.quality_report.checks.slice(0, 4)).map((check) => (
                                  <div key={check.name} className="rounded-lg border border-zinc-100 bg-white px-3 py-2">
                                    <div className="flex items-center justify-between gap-4">
                                      <p className="text-xs font-bold text-zinc-800">{check.name}</p>
                                      <span className={`text-[10px] font-black uppercase tracking-widest ${check.passed ? 'text-emerald-600' : 'text-amber-600'}`}>
                                        {check.passed ? 'passed' : 'review'}
                                      </span>
                                    </div>
                                    <p className="mt-1 text-[11px] font-medium text-zinc-500 break-words">{formatCheckDetail(check.detail)}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}
                        <div className="bg-zinc-50/50 rounded-xl p-6 border border-zinc-50 min-h-[300px]">
                            <div className="mb-4 flex items-center justify-between gap-4">
                              <div>
                                <h4 className="text-xs font-black text-zinc-400 uppercase tracking-widest">关键提取指标</h4>
                                <p className="mt-1 text-[11px] font-medium text-zinc-500">
                                  {activeTab === '评分标准'
                                    ? `当前共识别 ${scoringCount} 类评分项。`
                                    : `当前分区共 ${activeRequirements.length} 条待确认要求。`}
                                </p>
                              </div>
                              {analysisResult && activeTab !== '评分标准' && (
                                <span className="rounded-full bg-white px-3 py-1 text-[10px] font-black uppercase tracking-widest text-zinc-500">
                                  {activeRequirements.length} items
                                </span>
                              )}
                            </div>
                            
                            {!analysisResult ? (
                              <div className="flex flex-col items-center justify-center h-48 text-zinc-400 space-y-4">
                                <span className={isAnalyzing ? "material-symbols-outlined text-4xl animate-spin" : "material-symbols-outlined text-4xl"}>
                                  {isAnalyzing ? 'sync' : 'document_scanner'}
                                </span>
                                <p className="text-sm font-bold">{isAnalyzing ? '系统正在分阶段解析采购文件...' : currentProjectId ? '正在恢复当前项目的分析结果...' : '请上传标书文件以启动 AI 分析'}</p>
                              </div>
                            ) : (
                              <div className="space-y-4 text-sm font-medium animate-in fade-in duration-500">
                                {['商业资质', '技术规范', '废标条款'].includes(activeTab) && activeRequirements.map((req) => (
                                  <div key={req.id} className="rounded-xl border border-zinc-100 bg-white px-4 py-4">
                                    <div className="mb-3 flex items-center justify-between gap-4">
                                      <div className="flex items-center gap-2">
                                        {req.mandatory && <span className="px-1.5 py-0.5 bg-red-100 text-red-600 text-[10px] rounded font-black tracking-widest uppercase">强制</span>}
                                        <span className="text-[10px] uppercase font-black tracking-widest text-zinc-500">{req.badge}</span>
                                      </div>
                                      <span className="text-[10px] font-black uppercase tracking-widest text-primary">ID {req.id}</span>
                                    </div>
                                    <textarea
                                      value={editingRequirements[req.id]?.description || req.title}
                                      onChange={(e) => updateRequirementDraft(req.id, 'description', e.target.value)}
                                      className="min-h-[92px] w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium leading-relaxed outline-none focus:border-primary"
                                    />
                                    <input
                                      value={editingRequirements[req.id]?.evidence_required || req.evidence}
                                      onChange={(e) => updateRequirementDraft(req.id, 'evidence_required', e.target.value)}
                                      placeholder="证明材料要求"
                                      className="mt-3 w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-xs font-medium outline-none focus:border-primary"
                                    />
                                  </div>
                                ))}
                                {activeTab === '评分标准' && Object.entries(analysisResult.scoring_system || {}).map(([category, weight]: [any, any], i: number) => (
                                  <div key={i} className="py-3 border-b border-zinc-100">
                                    <div className="flex justify-between font-bold">
                                      <span className="text-primary">{category}</span>
                                      <span className="text-zinc-900 bg-zinc-100 px-3 py-1 rounded-full text-[10px] uppercase font-black tracking-widest">权重: {weight}%</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                        </div>
                        {statusText && (
                          <div className="flex items-center justify-between gap-4">
                            <p className="text-primary font-bold text-sm leading-relaxed italic animate-pulse">
                                {statusText}
                            </p>
                            <span className="rounded-full bg-zinc-100 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-zinc-500">
                              {taskStage || 'idle'}
                            </span>
                          </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Right: Go/No-Go Decision */}
            <div className="col-span-12 lg:col-span-4 space-y-8">
                <div className="bg-zinc-950 text-white rounded-3xl p-8 ambient-shadow relative overflow-hidden group">
                    <div className="relative z-10">
                        <h3 className="text-lg font-bold tracking-tight mb-8">可行性评估 (Go/No-Go)</h3>
                        <div className="mb-12">
                             <div className="flex items-baseline gap-2 mb-2">
                                <span className="text-6xl font-black tracking-tighter">{analysisResult?.go_no_go?.score ?? '-'}</span>
                                <span className="text-xl font-bold text-zinc-600">%</span>
                             </div>
                             <p className="text-xs font-bold text-zinc-400 uppercase tracking-widest">中标概率预估 (由决策引擎生成)</p>
                        </div>
                        <div className="space-y-4 mb-10 min-h-[100px]">
                            {analysisResult?.go_no_go?.reasons?.map((reason: string, idx: number) => (
                              <div key={idx} className="flex items-start gap-4 animate-in slide-in-from-right duration-500" style={{ animationDelay: `${idx * 150}ms` }}>
                                  <span className={`material-symbols-outlined mt-0.5 ${reason.includes('缺少') ? 'text-amber-500' : 'text-green-500'}`}>
                                    {reason.includes('缺少') ? 'warning' : 'check_circle'}
                                  </span>
                                  <div className="text-xs leading-relaxed font-medium">{reason}</div>
                              </div>
                            ))}
                            {!analysisResult && <div className="text-xs text-zinc-500 italic">等待标书解析完成以获取决策建议...</div>}
                        </div>
                        <button
                            onClick={() => navigate(analysisResult ? '/deviation' : '/rfp')}
                            disabled={!analysisResult || analysisCheck?.quality_report.status === 'needs_review' || !analysisConfirmed}
                            className="w-full py-4 bg-white text-zinc-950 rounded-2xl font-black text-sm uppercase tracking-widest hover:bg-zinc-100 transition-colors"
                        >
                            {analysisCheck?.quality_report.status === 'needs_review'
                              ? '待人工复核后进入投标'
                              : analysisConfirmed
                                ? '进入偏离矩阵确认'
                                : '请先确认分析结果'}
                        </button>
                        {!analysisConfirmed && analysisResult && analysisCheck?.quality_report.status !== 'needs_review' && (
                          <p className="mt-3 text-xs font-medium text-zinc-400">
                            当前仍处于分析预览阶段。请先保存上方“项目建档确认”，再进入偏离矩阵和后续编标流程。
                          </p>
                        )}
                    </div>
                    <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-primary/20 blur-[100px] rounded-full group-hover:bg-primary/30 transition-all"></div>
                </div>

                <div className="rounded-3xl border border-zinc-100 bg-white p-6">
                    <div className="mb-5 flex items-start justify-between gap-4">
                        <div>
                            <h3 className="text-lg font-bold tracking-tight">确认总览</h3>
                            <p className="mt-1 text-xs font-medium text-zinc-500">按这个顺序完成确认，主流程会更稳定。</p>
                        </div>
                        <span className={`rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-widest ${analysisConfirmed ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                          {analysisConfirmed ? '已确认' : '待确认'}
                        </span>
                    </div>
                    <div className="space-y-3">
                        {[
                          { label: '采购文件已识别', passed: Boolean(analysisResult), detail: analysisResult?.project_name || '请先上传并解析标书' },
                          {
                            label: '质量校验已通过',
                            passed: Boolean(analysisCheck && analysisCheck.quality_report.status === 'passed'),
                            detail: analysisCheck ? `${analysisCheck.quality_report.passed_checks}/${analysisCheck.quality_report.total_checks}` : '等待分析结果',
                          },
                          {
                            label: '项目已确认建档',
                            passed: Boolean(analysisConfirmed),
                            detail: analysisConfirmed ? '当前结果已作为正式项目基线' : '未确认前仅作为预览结果',
                          },
                          {
                            label: '可进入偏离矩阵',
                            passed: Boolean(analysisResult && analysisConfirmed && !reviewNeeded),
                            detail: nextStepBlockedReason || '下一步可进入偏离矩阵确认',
                          },
                        ].map((item) => (
                          <div key={item.label} className="rounded-2xl border border-zinc-100 bg-zinc-50 px-4 py-3">
                            <div className="flex items-center justify-between gap-4">
                              <p className="text-sm font-bold text-zinc-900">{item.label}</p>
                              <span className={`text-[10px] font-black uppercase tracking-widest ${item.passed ? 'text-emerald-600' : 'text-amber-600'}`}>
                                {item.passed ? 'done' : 'pending'}
                              </span>
                            </div>
                            <p className="mt-1 text-[11px] font-medium text-zinc-500">{item.detail}</p>
                          </div>
                        ))}
                    </div>
                    {qualityWarnings.length > 0 && (
                      <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4">
                        <p className="text-[10px] font-black uppercase tracking-widest text-amber-700">当前质量警告</p>
                        <div className="mt-2 space-y-2">
                          {qualityWarnings.slice(0, 3).map((warning, idx) => (
                            <p key={idx} className="text-[11px] font-medium text-amber-900">{warning}</p>
                          ))}
                        </div>
                      </div>
                    )}
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default RFPAnalysis;
