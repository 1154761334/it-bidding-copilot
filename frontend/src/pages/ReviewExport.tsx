import React, { useMemo, useState } from 'react';
import { biddingService, ExportReadiness, ReviewResult } from '../services/api';
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

const ReviewExport: React.FC = () => {
    const [isExporting, setIsExporting] = useState(false);
    const [reviewData, setReviewData] = useState<ReviewResult | null>(null);
    const [readiness, setReadiness] = useState<ExportReadiness | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { currentProjectId, bootstrapContext } = useProjectContextStore();

    const fetchReview = React.useCallback(() => {
        if (!currentProjectId) {
            setIsLoading(false);
            return Promise.resolve();
        }

        setIsLoading(true);
        setError(null);
        return Promise.all([
            biddingService.getReview(currentProjectId),
            biddingService.getExportReadiness(currentProjectId),
        ])
            .then(([review, readinessPayload]) => {
                setReviewData(review);
                setReadiness(readinessPayload);
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Review fetch failed", err);
                setError((err as Error).message);
                setIsLoading(false);
            });
    }, [currentProjectId]);

    React.useEffect(() => {
        bootstrapContext();
    }, [bootstrapContext]);

    React.useEffect(() => {
        void fetchReview();
    }, [fetchReview]);

    const rejectedCount = useMemo(
        () => reviewData?.section_reviews.filter((item) => item.verdict === 'REJECTED').length ?? 0,
        [reviewData],
    );
    const canExport = Boolean(currentProjectId && reviewData && readiness?.ready && rejectedCount === 0 && reviewData.approved_drafts === reviewData.total_drafts);

    const handleExport = async () => {
        if (!canExport) {
            alert("当前仍有未完成或未通过审标的章节，禁止导出最终版。");
            return;
        }
        setIsExporting(true);
        try {
            if (!currentProjectId) {
                throw new Error("No active project selected");
            }

            const blob = await biddingService.exportDocx(currentProjectId);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `投标文件.docx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            alert("Export failed: " + (e as Error).message);
        } finally {
            setIsExporting(false);
        }
    };
    return (
        <div className="flex-1 overflow-y-auto no-scrollbar bg-surface pt-8 pb-32 px-12">
            <div className="max-w-6xl mx-auto">
                <header className="mb-12">
                     <h1 className="text-4xl font-extrabold tracking-tight text-primary mb-2">标书终审与离线导出</h1>
                     <p className="text-secondary text-lg font-light">进行红队 AI 评估，完善封标前的最后合规性检查，并生成正式版招标文件。</p>
                </header>

                <div className="grid grid-cols-12 gap-8">
                    {/* Red Team Analysis Card */}
                    <div className="col-span-12 lg:col-span-7 space-y-6">
                        <div className="bg-white rounded-3xl p-8 ambient-shadow border border-zinc-100 min-h-[500px] flex flex-col">
                            <div className="flex justify-between items-center mb-10">
                                <h3 className="text-xl font-bold tracking-tight">红队 AI 模拟评估</h3>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-bold text-secondary uppercase tracking-widest">迭代轮次 Round 3</span>
                                    <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                                </div>
                            </div>

                            <div className="flex-1 space-y-8">
                                {isLoading ? (
                                    <div className="flex flex-col items-center justify-center h-48 text-zinc-400 animate-pulse">
                                        <span className="material-symbols-outlined text-4xl mb-2">security</span>
                                        <p className="text-sm font-bold">红队 AI 正在深度扫描合规性...</p>
                                    </div>
                                ) : !currentProjectId ? (
                                    <div className="flex flex-col items-center justify-center h-48 text-zinc-400">
                                        <span className="material-symbols-outlined text-4xl mb-2">assignment</span>
                                        <p className="text-sm font-bold">请先完成 RFP 解析并建立当前项目。</p>
                                    </div>
                                ) : error ? (
                                    <div className="flex flex-col items-center justify-center h-48 text-error">
                                        <span className="material-symbols-outlined text-4xl mb-2">error</span>
                                        <p className="text-sm font-bold">{error}</p>
                                    </div>
                                ) : (
                                    <>
                                        {reviewData?.critical_risks?.map((risk: string, i: number) => (
                                            <div key={i} className="flex items-start gap-6 group animate-in slide-in-from-left duration-300">
                                                <div className="w-10 h-10 rounded-xl bg-error/10 flex items-center justify-center shrink-0">
                                                    <span className="material-symbols-outlined text-error">dangerous</span>
                                                </div>
                                                <div>
                                                    <p className="text-xs font-black text-error uppercase tracking-widest mb-1">关键改进建议 (Critical)</p>
                                                    <p className="text-sm leading-relaxed font-bold text-zinc-900 border-b border-zinc-100 pb-4">
                                                        {risk}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                         {reviewData?.optimization_suggestions?.map((sug: string, i: number) => (
                                            <div key={i} className="flex items-start gap-6 group animate-in slide-in-from-left duration-500" style={{ animationDelay: '100ms' }}>
                                                <div className="w-10 h-10 rounded-xl bg-primary/5 flex items-center justify-center shrink-0">
                                                    <span className="material-symbols-outlined text-primary">tips_and_updates</span>
                                                </div>
                                                <div>
                                                    <p className="text-xs font-black text-primary uppercase tracking-widest mb-1">优化建议 (Warning)</p>
                                                    <p className="text-sm leading-relaxed font-medium text-secondary">
                                                        {sug}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                        
                                        {/* Strategy Highlights */}
                                        {reviewData?.winning_highlights?.length > 0 && (
                                            <div className="mt-8 pt-8 border-t border-zinc-100 flex flex-col gap-4">
                                                <h4 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-400">投标竞争力要点 (Winning Strategy)</h4>
                                                <div className="bg-primary/5 rounded-2xl p-6 border border-primary/10">
                                                    <ul className="space-y-3">
                                                        {reviewData.winning_highlights.map((highlight: string, i: number) => (
                                                            <li key={i} className="flex gap-3 text-sm font-bold text-primary italic">
                                                                <span className="material-symbols-outlined filled text-[18px]">verified</span>
                                                                {highlight}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>

                            <div className="mt-8 pt-8 border-t border-zinc-50 flex items-center justify-between">
                                <div className="flex items-center gap-6">
                                     <div className="flex items-baseline gap-2">
                                        <span className="text-4xl font-black">{reviewData?.win_rate || '--'}</span>
                                        <span className="text-sm font-bold text-zinc-400">%</span>
                                     </div>
                                     <p className="text-xs font-black text-secondary uppercase tracking-widest leading-none">模拟胜率预估 (AI Auditor)</p>
                                </div>
                                <button onClick={() => void fetchReview()} className="px-6 py-2 bg-zinc-950 text-white rounded-xl text-xs font-bold tracking-widest uppercase hover:bg-zinc-800 transition-all">重新跑测一份评分报告</button>
                            </div>
                        </div>
                    </div>

                    {/* Seal & Pack Checklist */}
                    <div className="col-span-12 lg:col-span-5 space-y-8">
                         <div className="bg-zinc-50 rounded-3xl p-8 border border-zinc-100">
                             <h3 className="text-lg font-bold tracking-tight mb-8 uppercase tracking-widest">封标封包清单</h3>
                             <div className="space-y-6">
                                {(readiness?.checks ?? []).map((item, idx) => (
                                    <div key={idx} className="flex items-center justify-between">
                                        <div className="pr-4">
                                          <span className={`text-sm font-bold ${item.passed ? 'text-zinc-400 line-through' : 'text-zinc-900'}`}>{item.label}</span>
                                          <p className="mt-1 text-[11px] font-medium text-zinc-500 break-words">{formatCheckDetail(item.detail)}</p>
                                        </div>
                                        <div className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center ${item.passed ? 'border-primary bg-primary text-white' : 'border-zinc-200 bg-white'}`}>
                                            {item.passed && <span className="material-symbols-outlined text-[16px] font-bold">check</span>}
                                        </div>
                                    </div>
                                ))}
                                {!readiness?.checks?.length && (
                                  <p className="text-sm font-medium text-zinc-400">请先建立当前项目并完成一轮审标。</p>
                                )}
                             </div>
                         </div>

                         <div className={`rounded-3xl p-6 border ${canExport ? 'bg-emerald-50 border-emerald-100 text-emerald-900' : 'bg-amber-50 border-amber-100 text-amber-900'}`}>
                             <p className="text-xs font-black uppercase tracking-widest mb-2">{canExport ? '导出条件已满足' : '导出条件未满足'}</p>
                             <p className="text-sm font-bold leading-relaxed">
                                {canExport
                                    ? `当前 ${reviewData?.approved_drafts}/${reviewData?.total_drafts} 章节全部通过审标，可以导出最终版。`
                                    : reviewData
                                        ? `当前仍有 ${rejectedCount} 个章节未完成或未通过审标。请先回到编标大厅补齐内容，再重新执行审标。`
                                        : readiness && !readiness.ready
                                            ? '当前导出前检查项未全部通过，请先完成偏离确认、章节生成和证据链补齐。'
                                        : '请先生成章节并完成一轮审标，系统才会开放最终导出。'}
                             </p>
                             {!canExport && readiness?.rejected_sections?.length ? (
                                <div className="mt-4 space-y-2 border-t border-amber-200/70 pt-4">
                                    {readiness.rejected_sections.slice(0, 5).map((section) => (
                                        <div key={section.draft_id} className="rounded-2xl bg-white/70 px-4 py-3 text-xs text-amber-950">
                                            <p className="font-bold">{section.section_title}</p>
                                            <p className="mt-1 text-[11px] font-medium text-amber-800">
                                                当前状态：{section.generation_status}
                                                {section.audit_feedback ? `；审标意见：${section.audit_feedback}` : ''}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                             ) : null}
                         </div>

                         <div className="bg-primary rounded-3xl p-10 text-white flex flex-col justify-between min-h-[240px] ambient-shadow">
                             <div>
                                <h3 className="text-xl font-bold tracking-tight mb-2">终审导出</h3>
                                <p className="text-zinc-400 text-xs font-bold uppercase tracking-widest">最后一步</p>
                             </div>
                             <button 
                                onClick={handleExport}
                                disabled={isExporting || !canExport}
                                className="w-full py-5 bg-white text-primary rounded-2xl flex items-center justify-center gap-4 font-black text-sm uppercase tracking-[0.2em] shadow-xl shadow-white/5 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:hover:scale-100"
                             >
                                <span className={isExporting ? "material-symbols-outlined animate-spin" : "material-symbols-outlined"}>
                                    {isExporting ? 'sync' : 'download'}
                                </span>
                                {isExporting ? '正在生成编排文档...' : '生成并导出 Word (.docx)'}
                             </button>
                         </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ReviewExport;
