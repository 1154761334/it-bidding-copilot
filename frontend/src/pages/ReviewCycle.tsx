import React, { useEffect, useMemo, useState } from 'react';
import { Search, ShieldAlert, History, ArrowRight, Loader2, Link2, BookOpen, CheckCircle2 } from 'lucide-react';
import { biddingService, ReviewResult } from '../services/api';
import { useProjectContextStore } from '../store/useProjectContextStore';

const describeEvidenceFragment = (fragment: string | undefined, fallback: string) => {
  if (!fragment) {
    return { filename: '未提供证据材料', snippet: fallback };
  }
  const trimmed = fragment.trim();
  if (trimmed.startsWith('[IMAGE:')) {
    const imagePath = trimmed.slice(7, -1);
    const imageName = imagePath.split('/').pop() || imagePath;
    return {
      filename: `图片证据：${imageName}`,
      snippet: '该章节已引用图片型资质或社保证明，请回到企业资产中心核验图片原件。',
    };
  }
  return {
    filename: '文本证据片段',
    snippet: trimmed,
  };
};

const ReviewCycle = () => {
  const { currentProjectId, currentProjectName, bootstrapContext } = useProjectContextStore();
  const [loading, setLoading] = useState(false);
  const [reviewData, setReviewData] = useState<ReviewResult | null>(null);
  const [selectedSource, setSelectedSource] = useState<{ filename: string; snippet: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    bootstrapContext();
  }, [bootstrapContext]);

  const rejectedCount = useMemo(
    () => reviewData?.section_reviews.filter((item) => item.verdict === 'REJECTED').length ?? 0,
    [reviewData],
  );
  const hasIncompleteDrafts = useMemo(
    () => reviewData?.section_reviews.some((item) => item.generation_status !== 'COMPLETED') ?? false,
    [reviewData],
  );

  const startReview = async () => {
    if (!currentProjectId) {
      setError('请先完成 RFP 解析并生成当前项目。');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await biddingService.getReview(currentProjectId);
      setReviewData(data);
      const firstSource = data.section_reviews?.find((item) => item.source_fragments?.length)?.source_fragments?.[0];
      setSelectedSource(
        firstSource
          ? describeEvidenceFragment(firstSource, data.section_reviews[0]?.feedback || '当前章节暂无额外证据片段。')
          : null,
      );
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-10">
        <h1 className="text-3xl font-black tracking-tight mb-2">红队终审</h1>
        <p className="text-base-content/60">
          {currentProjectName ? `当前项目：${currentProjectName}` : '按采购要求与证据链对章节草稿进行终审复核。'}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        <div className="lg:col-span-5 space-y-8">
           <section className="bg-base-200 p-8 rounded-3xl border border-base-300">
              <h3 className="text-sm font-black uppercase tracking-widest mb-6">发起终审</h3>
              <p className="text-xs text-base-content/60 mb-6 leading-relaxed">
                系统会按废标项、评分项、章节完整性和证据引用情况，对当前项目进行一轮严格复核。
              </p>
              <button 
                className={`btn btn-primary btn-block rounded-xl gap-2 shadow-lg ${loading ? 'btn-disabled' : 'shadow-primary/20'}`}
                onClick={startReview}
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Search size={18} />}
                {loading ? '正在执行终审...' : '开始终审'}
              </button>
           </section>

           {error && (
             <div className="alert alert-error rounded-2xl shadow-lg border-none animate-in fade-in slide-in-from-left-4">
                <ShieldAlert size={24} />
                <div>
                   <h3 className="font-bold text-sm uppercase">审标失败</h3>
                   <div className="text-xs opacity-80">{error}</div>
                </div>
             </div>
           )}

           {reviewData && rejectedCount > 0 && (
             <div className="alert alert-error rounded-2xl shadow-lg border-none animate-in fade-in slide-in-from-left-4">
                <ShieldAlert size={24} />
                <div>
                   <h3 className="font-bold text-sm uppercase">发现关键风险</h3>
                   <div className="text-xs opacity-80">{reviewData.critical_risks[0] || '存在待修正章节，请查看右侧审计历史。'}</div>
                </div>
             </div>
           )}

           {reviewData && hasIncompleteDrafts && (
             <div className="alert rounded-2xl shadow-lg border-none bg-amber-50 text-amber-900 animate-in fade-in slide-in-from-left-4">
                <ShieldAlert size={24} />
                <div>
                   <h3 className="font-bold text-sm uppercase">章节尚未收口</h3>
                   <div className="text-xs opacity-80">存在未完成或待复核章节。请先回到编标大厅完成批量生成，再执行最终审标。</div>
                </div>
             </div>
           )}

           {reviewData && rejectedCount === 0 && (
             <div className="alert alert-success rounded-2xl shadow-lg border-none animate-in fade-in slide-in-from-left-4">
                <CheckCircle2 size={24} />
                <div>
                   <h3 className="font-bold text-sm uppercase">终审通过</h3>
                   <div className="text-xs opacity-80">当前章节均通过审计，可进入导出阶段。</div>
                </div>
             </div>
           )}

           {reviewData && (
             <div className="space-y-4 animate-in fade-in slide-in-from-left-4">
                <div className="bg-emerald-50 border border-emerald-100 p-6 rounded-3xl">
                   <p className="text-[10px] font-black uppercase tracking-widest text-emerald-600 mb-3">Winning Highlights</p>
                   <ul className="space-y-2">
                     {(reviewData.winning_highlights || []).map((h, i) => (
                       <li key={i} className="text-xs font-bold text-emerald-800 flex items-center gap-2">
                         <div className="w-1 h-1 rounded-full bg-emerald-400"></div> {h}
                       </li>
                     ))}
                   </ul>
                </div>
                <div className="bg-zinc-50 border border-zinc-200 p-6 rounded-3xl">
                   <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3">Optimization Suggestions</p>
                   <ul className="space-y-2">
                     {(reviewData.optimization_suggestions || []).map((s, i) => (
                       <li key={i} className="text-xs font-medium text-zinc-600 flex items-center gap-2">
                         <ArrowRight size={10} className="text-zinc-300" /> {s}
                       </li>
                     ))}
                   </ul>
                </div>
             </div>
           )}

            <section className="bg-neutral text-neutral-content p-8 rounded-3xl shadow-xl overflow-hidden relative">
               <div className="relative z-10">
                  <h3 className="text-xs font-black uppercase tracking-widest mb-6 opacity-60 flex items-center gap-2">
                    <Link2 size={14} /> 章节证据链
                  </h3>
                  {selectedSource ? (
                    <div className="space-y-4 animate-in fade-in zoom-in-95">
                       <div className="bg-white/10 p-4 rounded-xl border border-white/10">
                          <p className="text-[10px] font-black text-primary uppercase mb-2">证据类型</p>
                          <p className="text-xs font-bold truncate">{selectedSource.filename}</p>
                       </div>
                       <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                          <p className="text-[10px] font-black text-primary uppercase mb-1">证据摘要</p>
                          <p className="text-[11px] leading-relaxed italic opacity-80">
                            "{selectedSource.snippet}"
                          </p>
                       </div>
                    </div>
                  ) : (
                    <div className="py-10 text-center opacity-30">
                       <BookOpen size={40} className="mx-auto mb-4" />
                       <p className="text-[10px] font-bold italic">执行一次终审后，点击右侧章节可查看其证据链。</p>
                    </div>
                  )}
               </div>
               <div className="absolute -right-10 -bottom-10 w-32 h-32 bg-primary/20 blur-3xl rounded-full"></div>
            </section>
        </div>

        <div className="lg:col-span-7 space-y-6">
           <div className="bg-base-100 p-8 rounded-3xl border border-base-300 h-full">
              <div className="flex justify-between items-center mb-8">
                <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
                  <History size={16} /> 审标记录
                </h3>
                <span className="badge badge-neutral font-bold text-[10px]">{reviewData ? `${reviewData.approved_drafts}/${reviewData.total_drafts} 章节通过` : '等待终审'}</span>
              </div>

              {reviewData ? (
                <div className="space-y-6">
                  {reviewData.section_reviews.map((item, index) => (
                    <div key={item.draft_id} className="relative pl-8 border-l-2 border-primary/20 pb-8">
                      <div className={`absolute -left-2 top-0 w-4 h-4 rounded-full border-4 border-base-100 ${item.verdict === 'APPROVED' ? 'bg-emerald-500' : 'bg-primary'}`}></div>
                      <p className="text-[10px] font-black text-primary uppercase mb-1">{reviewData.round} • 第 {index + 1} 节</p>
                      <div
                        className="bg-base-200 p-4 rounded-2xl border border-base-300 group cursor-pointer hover:border-primary transition-all"
                        onClick={() =>
                          setSelectedSource(describeEvidenceFragment(item.source_fragments?.[0], item.feedback || '当前章节暂无额外证据片段。'))
                        }
                      >
                        <p className={`text-xs font-bold mb-2 tracking-tight flex justify-between items-center ${item.verdict === 'APPROVED' ? 'text-emerald-600' : 'text-error'}`}>
                          结论：{item.verdict === 'APPROVED' ? '通过' : '需修正'}
                          <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity">查看证据</span>
                        </p>
                        <p className="text-xs font-black mb-2">{item.section_title}</p>
                        <p className="text-[11px] font-bold text-zinc-500 mb-2">
                          当前状态：{item.generation_status === 'COMPLETED' ? '已完成' : item.generation_status === 'REVIEWING' ? '待复核' : '未完成'}
                        </p>
                        <p className="text-[11px] text-base-content/60 font-mono leading-relaxed whitespace-pre-wrap">
                          {item.feedback || '当前未生成额外审稿意见。'}
                        </p>
                      </div>
                    </div>
                  ))}
                  <button className="btn btn-neutral btn-block rounded-xl gap-2 font-black group" disabled>
                    {hasIncompleteDrafts ? '请先完成全部章节生成' : '按审标意见自动修复并重写'}
                    <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>
              ) : (
                <div className="h-64 flex flex-col items-center justify-center border-2 border-base-200 border-dashed rounded-3xl bg-base-100/50">
                   <Search className="text-base-content/5 mb-4" size={60} strokeWidth={1} />
                   <p className="text-xs text-base-content/30 font-bold italic text-center px-10">
                     还没有终审记录。点击左侧按钮开始一轮正式审标。
                   </p>
                </div>
              )}
           </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewCycle;
