import React, { useEffect, useRef, useState } from 'react';
import { useBiddingStore } from '../store/useBiddingStore';
import { useProjectContextStore } from '../store/useProjectContextStore';
import TiptapEditor from '../components/editor/TiptapEditor';

const BiddingHall: React.FC = () => {
  const { 
    isConnected, messages, activeChapter, streamingText, outline, generationStatus,
    projectGenerationStatus, projectGenerationProgress, draftDetails, materialsPack, lastSavedDraft,
    connect, disconnect, triggerGeneration, triggerProjectGeneration, setActiveChapter, fetchOutline, fetchMaterialsPack, saveMaterialsPack, saveDraftContent, uploadProjectMaterial
  } = useBiddingStore();
  const { currentProjectId, bootstrapContext } = useProjectContextStore();
  const [selectedCertificates, setSelectedCertificates] = useState<number[]>([]);
  const [selectedCases, setSelectedCases] = useState<number[]>([]);
  const [selectedPersonnel, setSelectedPersonnel] = useState<number[]>([]);
  const [selectedMaterials, setSelectedMaterials] = useState<number[]>([]);
  const [draftingNotes, setDraftingNotes] = useState('');
  const [editorContent, setEditorContent] = useState('');

  const completedCount = outline.filter(s => s.status === 'COMPLETED').length;
  const reviewingCount = outline.filter(s => s.status === 'REVIEWING').length;
  const pendingCount = outline.filter(s => !['COMPLETED', 'REVIEWING'].includes(s.status)).length;
  const progressPercent = outline.length > 0 ? Math.round((completedCount / outline.length) * 100) : 0;
  const batchProgressPercent = projectGenerationProgress?.total_sections
    ? Math.round((projectGenerationProgress.completed_sections.length / projectGenerationProgress.total_sections) * 100)
    : 0;
  const currentDraft = draftDetails.find((item) => String(item.id) === activeChapter);
  const currentAuditFeedback = typeof currentDraft?.audit_logs?.final_feedback === 'string' ? currentDraft.audit_logs.final_feedback : '';
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const materialsConfirmed = materialsPack?.confirmed ?? false;

  useEffect(() => {
    bootstrapContext();
  }, [bootstrapContext]);

  useEffect(() => {
    if (currentProjectId) {
      fetchOutline(currentProjectId);
      void fetchMaterialsPack(currentProjectId);
    }
  }, [currentProjectId, fetchMaterialsPack, fetchOutline]);

  useEffect(() => {
    if (!materialsPack) return;
    setSelectedCertificates(materialsPack.selection.certificate_ids);
    setSelectedCases(materialsPack.selection.case_ids);
    setSelectedPersonnel(materialsPack.selection.personnel_ids);
    setSelectedMaterials(materialsPack.selection.material_ids);
    setDraftingNotes(materialsPack.drafting_notes || '');
  }, [materialsPack]);

  useEffect(() => {
    setEditorContent(currentDraft?.content_markdown || '');
  }, [currentDraft?.id, currentDraft?.content_markdown]);

  useEffect(() => {
    if (activeChapter) {
        connect(activeChapter);
    }
    return () => disconnect();
  }, [activeChapter]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleSelection = (id: number, values: number[], setter: React.Dispatch<React.SetStateAction<number[]>>) => {
    setter(values.includes(id) ? values.filter((item) => item !== id) : [...values, id]);
  };

  const applyRecommendedSelections = () => {
    if (!materialsPack) return;
    setSelectedCertificates(materialsPack.recommended.certificate_ids);
    setSelectedCases(materialsPack.recommended.case_ids);
    setSelectedPersonnel(materialsPack.recommended.personnel_ids);
  };

  const persistMaterialsPack = async (confirmed: boolean) => {
    if (!currentProjectId) return;
    await saveMaterialsPack(currentProjectId, {
      selected_certificate_ids: selectedCertificates,
      selected_case_ids: selectedCases,
      selected_personnel_ids: selectedPersonnel,
      selected_material_ids: selectedMaterials,
      drafting_notes: draftingNotes,
      confirmed,
    });
  };

  const handleSaveDraft = async () => {
    if (!activeChapter) return;
    await saveDraftContent(activeChapter, editorContent);
  };

  const handleAIRewrite = async (selectedText: string) => {
    if (!activeChapter) return;
    try {
      const response = await fetch(`/api/v1/bid/draft/${activeChapter}/rewrite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: selectedText }),
      });
      const data = await response.json();
      if (data.status === 'ok') {
        // We replace the selection in the editor. 
        // Note: For simplicity, we are returning the text, but the Tiptap component handles the state.
        // In a real implementation, we might want to use a more direct editor command.
        // For now, we'll alert or log that it's done. 
        console.log("Rewritten text:", data.rewritten_text);
        // Note: The parent update of editorContent will trigger Tiptap's useEffect to set content.
        // This is a bit heavy, but works for the current architecture.
        setEditorContent(prev => prev.replace(selectedText, data.rewritten_text));
      }
    } catch (error) {
      console.error("AI Rewrite failed:", error);
    }
  };

  return (
    <div className="flex h-full min-w-0">
      {/* 1. Left Sidebar: Document Outline Tree */}
      <div className="w-72 border-r border-zinc-100 dark:border-zinc-800 flex flex-col bg-zinc-50/50">
        <div className="p-6 border-b border-zinc-100 flex justify-between items-center bg-white shadow-[0_4px_12px_-4px_rgba(0,0,0,0.02)]">
          <h3 className="font-black text-sm tracking-widest uppercase">标书大纲</h3>
          <button className="material-symbols-outlined text-zinc-400 hover:text-primary transition-colors text-lg">add_circle</button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 no-scrollbar">
            {outline.map(section => (
                <div key={section.id} className="mb-4">
                    <div 
                        onClick={() => setActiveChapter(section.id)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${section.id === activeChapter ? 'bg-primary text-white shadow-lg' : 'text-secondary hover:bg-white hover:text-primary'}`}
                    >
                        <span className="material-symbols-outlined text-sm">{section.id === activeChapter ? 'description' : 'folder'}</span>
                        <span className="truncate flex-1">{section.title}</span>
                        {section.status === 'COMPLETED' && <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>}
                        {section.status === 'REVIEWING' && <div className="w-1.5 h-1.5 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.4)]"></div>}
                        {section.status === 'DRAFTING' && <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>}
                    </div>
                </div>
            ))}
        </div>
      </div>

      {/* 2. Main Canvas: Editor & AI Log */}
      <div className="flex-1 flex flex-col min-w-0 bg-surface">
          <div className="h-16 flex items-center justify-between px-8 border-b border-zinc-100 bg-white/80 backdrop-blur-md sticky top-0 z-10">
              <div className="flex items-center gap-4">
                  <span className="text-xs font-black text-secondary tracking-widest uppercase">正在编辑章节</span>
                  <div className="h-4 w-px bg-zinc-200"></div>
                  <h2 className="text-sm font-bold truncate">{outline.find(s => s.id === activeChapter)?.title || '请选择章节'}</h2>
              </div>
              <div className="flex gap-4">
                  <button
                     onClick={() => void handleSaveDraft()}
                     disabled={!activeChapter}
                     className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-zinc-50 border border-zinc-100 text-xs font-bold hover:bg-white transition-colors disabled:opacity-50"
                  >
                      <span className="material-symbols-outlined text-sm">save</span>
                      保存改稿
                  </button>
                  <div className="flex flex-col items-end mr-2 justify-center">
                    <span className="text-[10px] font-bold text-zinc-400">项目级批量生成</span>
                    <span className="text-[11px] font-black tracking-widest uppercase">{projectGenerationStatus}</span>
                  </div>
                  <div className="flex flex-col items-end mr-4 justify-center">
                    <span className="text-[10px] font-bold text-zinc-400">实时连接 (WS)</span>
                    <span className="text-[11px] font-black tracking-widest uppercase flex items-center gap-1">
                       <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
                       {isConnected ? '已连接' : '未连接'}
                    </span>
                  </div>
                  <button className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-zinc-50 border border-zinc-100 text-xs font-bold hover:bg-white transition-colors">
                      <span className="material-symbols-outlined text-sm">history</span>
                      版本
                  </button>
                  <button 
                     onClick={() => currentProjectId && void triggerProjectGeneration(currentProjectId)}
                     disabled={!currentProjectId || outline.length === 0 || !materialsConfirmed}
                     className="flex items-center gap-2 px-5 py-1.5 rounded-lg bg-zinc-950 text-white text-xs font-bold hover:bg-zinc-800 active:scale-95 disabled:opacity-50 transition-all"
                  >
                      <span className="material-symbols-outlined text-sm">playlist_play</span>
                      整项目自动续写
                  </button>
                  <button
                     onClick={() => currentProjectId && void triggerProjectGeneration(currentProjectId, { onlyIncomplete: true })}
                     disabled={!currentProjectId || (reviewingCount + pendingCount) === 0 || !materialsConfirmed}
                     className="flex items-center gap-2 px-5 py-1.5 rounded-lg bg-amber-500 text-white text-xs font-bold hover:bg-amber-600 active:scale-95 disabled:opacity-50 transition-all"
                  >
                      <span className="material-symbols-outlined text-sm">refresh</span>
                      重试未完成章节
                  </button>
                  <button 
                     onClick={() => void triggerGeneration()}
                     disabled={!activeChapter || !materialsConfirmed}
                     className="flex items-center gap-2 px-6 py-1.5 rounded-lg bg-primary text-on-primary text-xs font-bold hover:opacity-90 active:scale-95 disabled:opacity-50 transition-all"
                  >
                      <span className="material-symbols-outlined text-sm">auto_fix</span>
                      {currentDraft?.generation_status === 'REVIEWING' || currentDraft?.generation_status === 'PENDING' ? '重试当前章节' : '触发智能补全'}
                  </button>
              </div>
          </div>

          <div className="flex-1 overflow-y-auto no-scrollbar pt-12 pb-32 px-16">
              <div className="max-w-3xl mx-auto space-y-12">
                  <header>
                      <h1 className="text-4xl font-black tracking-tighter mb-8 text-primary">{outline.find(s => s.id === activeChapter)?.title || '未命名章节'}</h1>
                      <div className="flex items-center gap-4 text-xs font-bold text-zinc-400 mb-12">
                          <span className="text-emerald-500">
                            {lastSavedDraft?.draft_id === Number(activeChapter) ? `已保存版本 v${lastSavedDraft.version}` : '可在线编辑并手动保存'}
                          </span>
                          <span>•</span>
                          <span>{editorContent.length} 字符</span>
                          <span>•</span>
                          <span>{generationStatus}</span>
                          <span>•</span>
                          <span>{currentDraft?.generation_status || 'PENDING'}</span>
                          <span>•</span>
                          <span className="px-2 py-0.5 bg-zinc-100 rounded">技术撰写模态</span>
                      </div>
                      {currentProjectId && (
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                          <div className="rounded-2xl border border-zinc-100 bg-white p-4">
                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-2">章节总数</p>
                            <p className="text-2xl font-black text-zinc-900">{outline.length}</p>
                          </div>
                          <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
                            <p className="text-[10px] font-black uppercase tracking-widest text-emerald-500 mb-2">已完成</p>
                            <p className="text-2xl font-black text-emerald-700">{completedCount}</p>
                          </div>
                          <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4">
                            <p className="text-[10px] font-black uppercase tracking-widest text-amber-500 mb-2">待复核</p>
                            <p className="text-2xl font-black text-amber-700">{reviewingCount}</p>
                          </div>
                          <div className="rounded-2xl border border-zinc-100 bg-zinc-50 p-4">
                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-2">未生成</p>
                            <p className="text-2xl font-black text-zinc-700">{pendingCount}</p>
                          </div>
                        </div>
                      )}
                      {currentProjectId && materialsPack && (
                        <div className="rounded-2xl border border-zinc-100 bg-white p-5 mb-8 space-y-5">
                          <div className="flex items-start justify-between gap-6">
                            <div>
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-2">起草前素材确认</p>
                              <h3 className="text-lg font-black text-zinc-900">先确认本项目可用的企业资质、案例、人员与补充材料</h3>
                              <p className="text-xs font-medium text-zinc-500 mt-2">
                                当前项目已识别 {materialsPack.summary.requirements_total} 条需求。确认素材包后再启动 AI 起草更稳。
                              </p>
                            </div>
                            <div className={`rounded-full px-3 py-1 text-[11px] font-black uppercase tracking-widest ${materialsConfirmed ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                              {materialsConfirmed ? '素材包已确认' : '待确认'}
                            </div>
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <div className="rounded-xl border border-zinc-100 bg-zinc-50 px-4 py-3">
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">已选证书</p>
                              <p className="text-xl font-black text-zinc-900">{selectedCertificates.length}</p>
                            </div>
                            <div className="rounded-xl border border-zinc-100 bg-zinc-50 px-4 py-3">
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">已选案例</p>
                              <p className="text-xl font-black text-zinc-900">{selectedCases.length}</p>
                            </div>
                            <div className="rounded-xl border border-zinc-100 bg-zinc-50 px-4 py-3">
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">已选人员</p>
                              <p className="text-xl font-black text-zinc-900">{selectedPersonnel.length}</p>
                            </div>
                            <div className="rounded-xl border border-zinc-100 bg-zinc-50 px-4 py-3">
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">补充材料</p>
                              <p className="text-xl font-black text-zinc-900">{selectedMaterials.length}</p>
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-3">
                            <button onClick={applyRecommendedSelections} className="rounded-xl border border-zinc-200 px-4 py-2 text-xs font-black uppercase tracking-widest text-zinc-700 hover:bg-zinc-50">
                              智能推荐勾选
                            </button>
                            <button onClick={() => void persistMaterialsPack(false)} className="rounded-xl border border-zinc-200 px-4 py-2 text-xs font-black uppercase tracking-widest text-zinc-700 hover:bg-zinc-50">
                              保存素材包
                            </button>
                            <button onClick={() => void persistMaterialsPack(true)} className="rounded-xl bg-primary px-4 py-2 text-xs font-black uppercase tracking-widest text-white hover:opacity-90">
                              确认素材后开始起草
                            </button>
                            <label className="rounded-xl border border-zinc-200 px-4 py-2 text-xs font-black uppercase tracking-widest text-zinc-700 hover:bg-zinc-50 cursor-pointer">
                              上传补充材料
                              <input
                                type="file"
                                className="hidden"
                                onChange={(event) => {
                                  const file = event.target.files?.[0];
                                  if (file && currentProjectId) {
                                    void uploadProjectMaterial(currentProjectId, file);
                                  }
                                  event.currentTarget.value = '';
                                }}
                              />
                            </label>
                          </div>

                          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                            <div className="rounded-xl border border-zinc-100 p-4">
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3">证书与案例</p>
                              <div className="space-y-2 max-h-64 overflow-y-auto">
                                {materialsPack.available.certificates.slice(0, 8).map((item) => (
                                  <button
                                    key={`cert-${item.id}`}
                                    onClick={() => toggleSelection(item.id, selectedCertificates, setSelectedCertificates)}
                                    className={`w-full rounded-xl border px-3 py-2 text-left ${selectedCertificates.includes(item.id) ? 'border-primary bg-primary/5' : 'border-zinc-100 bg-zinc-50'}`}
                                  >
                                    <p className="text-sm font-bold text-zinc-900">{item.title}</p>
                                    <p className="text-xs text-zinc-500">{item.subtitle}</p>
                                  </button>
                                ))}
                                {materialsPack.available.cases.slice(0, 6).map((item) => (
                                  <button
                                    key={`case-${item.id}`}
                                    onClick={() => toggleSelection(item.id, selectedCases, setSelectedCases)}
                                    className={`w-full rounded-xl border px-3 py-2 text-left ${selectedCases.includes(item.id) ? 'border-primary bg-primary/5' : 'border-zinc-100 bg-zinc-50'}`}
                                  >
                                    <p className="text-sm font-bold text-zinc-900">{item.title}</p>
                                    <p className="text-xs text-zinc-500">{item.subtitle}</p>
                                  </button>
                                ))}
                              </div>
                            </div>

                            <div className="rounded-xl border border-zinc-100 p-4">
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3">人员与补充材料</p>
                              <div className="space-y-2 max-h-64 overflow-y-auto">
                                {materialsPack.available.personnel.slice(0, 8).map((item) => (
                                  <button
                                    key={`person-${item.id}`}
                                    onClick={() => toggleSelection(item.id, selectedPersonnel, setSelectedPersonnel)}
                                    className={`w-full rounded-xl border px-3 py-2 text-left ${selectedPersonnel.includes(item.id) ? 'border-primary bg-primary/5' : 'border-zinc-100 bg-zinc-50'}`}
                                  >
                                    <p className="text-sm font-bold text-zinc-900">{item.title}</p>
                                    <p className="text-xs text-zinc-500">{item.subtitle}</p>
                                  </button>
                                ))}
                                {materialsPack.available.materials.slice(0, 6).map((item) => (
                                  <button
                                    key={`material-${item.id}`}
                                    onClick={() => toggleSelection(item.id, selectedMaterials, setSelectedMaterials)}
                                    className={`w-full rounded-xl border px-3 py-2 text-left ${selectedMaterials.includes(item.id) ? 'border-primary bg-primary/5' : 'border-zinc-100 bg-zinc-50'}`}
                                  >
                                    <p className="text-sm font-bold text-zinc-900">{item.filename}</p>
                                    <p className="text-xs text-zinc-500">{item.parsed_excerpt || item.file_type}</p>
                                  </button>
                                ))}
                              </div>
                            </div>
                          </div>

                          <div className="rounded-xl border border-zinc-100 p-4">
                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3">本项目起草补充说明</p>
                            <textarea
                              value={draftingNotes}
                              onChange={(event) => setDraftingNotes(event.target.value)}
                              className="w-full min-h-24 rounded-xl border border-zinc-200 px-3 py-3 text-sm"
                              placeholder="补充本项目的方案策略、厂商约束、竞争对手风险、必须强调的得分点。"
                            />
                          </div>
                        </div>
                      )}
                      {projectGenerationProgress && (
                        <div className="rounded-2xl border border-zinc-100 bg-white p-5 mb-8">
                          <div className="flex items-center justify-between gap-4 mb-3">
                            <div>
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">项目级自动续写进度</p>
                              <p className="text-sm font-bold text-zinc-900">
                                {projectGenerationProgress.current_section_title
                                  ? `当前章节：${projectGenerationProgress.current_section_title}`
                                  : '已完成当前批次'}
                              </p>
                              <p className="text-[11px] font-bold text-zinc-500 mt-1">
                                {projectGenerationProgress.selection_mode === 'only_incomplete' ? '当前模式：仅重试未完成章节' : '当前模式：整项目自动续写'}
                              </p>
                            </div>
                            <span className="text-sm font-black text-primary">
                              {projectGenerationProgress.completed_sections.length}/{projectGenerationProgress.total_sections}
                            </span>
                          </div>
                          <div className="h-2 rounded-full bg-zinc-100 overflow-hidden mb-3">
                            <div className="h-full bg-primary transition-all duration-500" style={{ width: `${batchProgressPercent}%` }}></div>
                          </div>
                          <p className="text-xs font-medium text-zinc-500">
                            最近完成：
                            {projectGenerationProgress.completed_sections.length > 0
                              ? ` ${projectGenerationProgress.completed_sections.slice(-3).map((item) => item.section_title).join('、')}`
                              : ' 暂无'}
                          </p>
                        </div>
                      )}
                  </header>

                  <section className="space-y-6">
                      {!currentProjectId && (
                        <p className="text-lg leading-relaxed text-zinc-700 font-medium whitespace-pre-wrap">
                          请先完成企业建档和 RFP 解析，系统才能生成当前项目的大纲与章节。
                        </p>
                      )}
                      {currentProjectId && (
                        <div className="rounded-3xl border border-zinc-100 bg-white overflow-hidden shadow-sm">
                          <div className="flex items-center justify-between gap-4 px-5 py-3 border-b border-zinc-100 bg-zinc-50">
                            <div>
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Markdown 工作区</p>
                              <p className="text-xs text-zinc-500 mt-1">支持在线修改当前章节正文，保存后立即写回草稿版本。</p>
                            </div>
                            <div className="flex items-center gap-2 text-[11px] font-bold text-zinc-500">
                              <span className="rounded-full bg-zinc-100 px-3 py-1">版本 {currentDraft?.version || 1}</span>
                              <span className="rounded-full bg-zinc-100 px-3 py-1">{currentDraft?.generation_status || 'PENDING'}</span>
                            </div>
                          </div>
                          <TiptapEditor
                            content={editorContent}
                            onChange={(content) => setEditorContent(content)}
                            onAIRewrite={handleAIRewrite}
                            placeholder={currentProjectId ? '此章节尚未生成正文。点击“触发智能补全”以启动当前章节生成，或直接手工起草。' : ''}
                          />
                        </div>
                      )}
                      {currentAuditFeedback && (
                        <div className="rounded-2xl border border-amber-100 bg-amber-50 px-5 py-4 text-sm font-medium text-amber-900">
                          <p className="text-[10px] font-black uppercase tracking-widest mb-2">审稿反馈</p>
                          {currentAuditFeedback}
                        </div>
                      )}
                  </section>
              </div>
          </div>
      </div>

      {/* 3. Right Sidebar: Agent Reasoning Wall */}
      <div className="w-80 border-l border-zinc-100 bg-zinc-50 flex flex-col">
            <div className="p-6 border-b border-zinc-100 bg-white">
                <h3 className="font-black text-sm tracking-widest uppercase mb-4">实时协作智能体</h3>
                <div className="flex gap-3 overflow-x-auto no-scrollbar pb-2">
                    {[
                        { id: 'TECHNICAL', label: '技术' },
                        { id: 'COMMERCIAL', label: '商务' },
                        { id: 'REVIEWER', label: '合规' }
                    ].map(role => (
                        <div key={role.id} className={`shrink-0 w-10 h-10 rounded-xl flex items-center justify-center border-2 ${role.id === 'TECHNICAL' ? 'border-primary bg-primary/5 text-primary' : 'border-transparent bg-zinc-100 text-zinc-400'}`}>
                            <span className="text-[10px] font-black">{role.label}</span>
                        </div>
                    ))}
                    <div className="shrink-0 w-10 h-10 rounded-xl border-2 border-dashed border-zinc-200 flex items-center justify-center text-zinc-300 hover:border-zinc-400 hover:text-zinc-400 transition-all cursor-pointer">
                        <span className="material-symbols-outlined text-sm">add</span>
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
                {currentDraft?.source_fragments?.length ? (
                  <div className="space-y-4">
                    <div className="bg-white p-4 rounded-xl border border-zinc-100 shadow-sm">
                      <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-2">Evidence Chain</p>
                      <p className="text-xs leading-relaxed font-medium text-secondary">
                        当前章节已引用 {currentDraft.source_fragments.length} 条原始证据片段，可据此判断是否需要补材料或重试章节。
                      </p>
                    </div>
                    {currentDraft.source_fragments.slice(0, 6).map((fragment, idx) => (
                      <div key={`${currentDraft.id}-${idx}`} className="bg-white p-4 rounded-xl border border-zinc-100 shadow-sm">
                        <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-2">Source {idx + 1}</p>
                        <p className="text-xs leading-relaxed font-medium text-secondary whitespace-pre-wrap break-words">
                          {fragment}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : messages.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-zinc-300 text-xs font-bold">
                    [ AI 推理日志流 / 证据链 ]
                  </div>
                ) : (
                  messages.map((msg, idx) => (
                    msg.status === 'idle' ? (
                       <div key={idx} className="bg-primary p-4 rounded-xl shadow-lg shadow-primary/10 animate-in fade-in slide-in-from-right-4 duration-300">
                          <p className="text-[10px] font-black text-white/60 uppercase tracking-widest mb-2">Result • {new Date(msg.timestamp * 1000).toLocaleTimeString()}</p>
                          <p className="text-xs leading-relaxed font-bold text-white">
                              {msg.log}
                          </p>
                       </div>
                    ) : (
                       <div key={idx} className="bg-white p-4 rounded-xl border border-zinc-100 shadow-sm animate-in fade-in slide-in-from-right-4 duration-300">
                          <div className="flex justify-between items-center mb-2">
                             <p className="text-[10px] font-black text-primary uppercase tracking-widest flex items-center gap-1">
                                {msg.agentName} 
                                {msg.status === 'searching' && <span className="material-symbols-outlined text-[10px] font-bold">search</span>}
                                {msg.status === 'thinking' && <span className="material-symbols-outlined text-[10px] font-bold animate-pulse">more_horiz</span>}
                             </p>
                             <span className="text-[9px] font-bold text-zinc-300">{msg.elapsed}s</span>
                          </div>
                          <p className="text-xs leading-relaxed font-medium text-secondary break-words">
                              {msg.log}
                          </p>
                      </div>
                    )
                  ))
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="p-6 border-t border-zinc-100 bg-white">
                <div className="flex items-center gap-3">
                    <div className="flex-1 h-1.5 bg-zinc-100 rounded-full overflow-hidden">
                        <div className="h-full bg-primary transition-all duration-500" style={{ width: `${progressPercent}%` }}></div>
                    </div>
                    <span className="text-[10px] font-black text-primary">{progressPercent}%</span>
                </div>
                <p className="text-[10px] font-bold text-zinc-400 mt-2 uppercase tracking-widest">章节生成总进度</p>
            </div>
      </div>
    </div>
  );
};

export default BiddingHall;
