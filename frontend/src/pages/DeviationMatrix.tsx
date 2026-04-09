import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, ArrowRight, CheckCircle, Edit3, Loader2, Save, Table as TableIcon } from 'lucide-react';
import { DeviationMatrixItem, rfpService } from '../services/api';
import { useRfpStore } from '../store/useRfpStore';
import { useProjectContextStore } from '../store/useProjectContextStore';

const DeviationMatrix = () => {
  const navigate = useNavigate();
  const { analysisResult, isAnalyzing } = useRfpStore();
  const { currentProjectId, currentProjectName, bootstrapContext } = useProjectContextStore();
  const [items, setItems] = useState<DeviationMatrixItem[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    bootstrapContext();
  }, [bootstrapContext]);

  useEffect(() => {
    if (!currentProjectId) return;

    rfpService
      .getDeviationMatrix(currentProjectId)
      .then((data) => {
        if (data && data.length > 0) {
          setItems(data);
          return;
        }
        if (analysisResult?.technical_requirements) {
          setItems(
            analysisResult.technical_requirements.map((req: any, idx: number) => ({
              id: idx,
              req: `${req.param_name || ''}: ${req.required_value || req.item}`,
              resp: '自动生成中：正在检索企业资产库以匹配最佳应答...',
              status: 'partial',
              is_fatal: false,
            })),
          );
        }
      })
      .catch((err) => console.error('Matrix fetch failed', err));
  }, [analysisResult, currentProjectId]);

  const analysisConfirmed =
    analysisResult?.project_status === 'ANALYSIS_CONFIRMED' || analysisResult?.project_status === 'DEVIATION_CONFIRMED';

  const saveMatrix = async () => {
    if (!currentProjectId) return;
    setIsSaving(true);
    setStatusMessage('');
    try {
      const payload = await rfpService.updateDeviationMatrix(currentProjectId, items);
      setStatusMessage(`已保存 ${payload.updated} 条偏离矩阵应答`);
      setEditingId(null);
    } catch (error) {
      setStatusMessage(`保存失败: ${(error as Error).message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const confirmMatrix = async () => {
    if (!currentProjectId) return;
    setIsConfirming(true);
    setStatusMessage('');
    try {
      await rfpService.updateDeviationMatrix(currentProjectId, items);
      await rfpService.confirmDeviationMatrix(currentProjectId);
      setStatusMessage('偏离矩阵已确认，正在进入编标大厅');
      navigate('/bidding');
    } catch (error) {
      setStatusMessage(`确认失败: ${(error as Error).message}`);
    } finally {
      setIsConfirming(false);
    }
  };

  const compliantCount = items.filter((item) => item.status === 'compliant').length;
  const partialCount = items.filter((item) => item.status === 'partial').length;
  const gapCount = items.filter((item) => item.status === 'gap').length;

  if (isAnalyzing) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center space-y-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-sm font-black uppercase tracking-widest text-secondary">AI 正在深度解构标书要求...</p>
      </div>
    );
  }

  if (!currentProjectId) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center space-y-6 px-8 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-zinc-100 text-zinc-300">
          <TableIcon size={40} />
        </div>
        <div>
          <h2 className="mb-2 text-xl font-bold">暂无偏离矩阵数据</h2>
          <p className="max-w-md text-sm text-secondary">请先在【RFP Analysis】页面上传并解析一份招标文件，AI 将自动在此为您生成点对点应答矩阵。</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in mx-auto max-w-7xl p-8 duration-700">
      <div className="mb-10 flex items-end justify-between">
        <div>
          <h1 className="mb-2 text-3xl font-black tracking-tight">点对点参数偏离矩阵</h1>
          <p className="text-base-content/60">
            正在分析项目：<span className="font-bold text-primary">{analysisResult?.project_name || currentProjectName || `项目 ${currentProjectId}`}</span>
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => void saveMatrix()} disabled={isSaving || isConfirming} className="btn btn-ghost gap-2 rounded-xl text-xs font-bold uppercase">
            {isSaving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />} 保存矩阵
          </button>
          <button
            onClick={() => void confirmMatrix()}
            disabled={isSaving || isConfirming || !analysisConfirmed}
            className="btn btn-primary gap-2 rounded-xl text-xs font-bold uppercase text-white shadow-lg shadow-primary/20"
          >
            确认本表并提交 <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {!analysisConfirmed && (
        <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50/70 px-5 py-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-amber-700">步骤未确认</p>
          <p className="mt-1 text-sm font-bold text-zinc-900">当前采购文件识别仍处于预览状态，请先回到标书解析页确认项目信息和关键要求，再进入偏离矩阵确认。</p>
          <button onClick={() => navigate('/rfp')} className="mt-3 rounded-xl bg-white px-4 py-2 text-xs font-black uppercase tracking-widest text-amber-700">
            返回标书解析确认
          </button>
        </div>
      )}

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-zinc-100 bg-white px-5 py-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">总条目</p>
          <p className="mt-2 text-2xl font-black text-zinc-900">{items.length}</p>
        </div>
        <div className="rounded-2xl border border-emerald-100 bg-emerald-50/60 px-5 py-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-emerald-600">完全满足</p>
          <p className="mt-2 text-2xl font-black text-emerald-700">{compliantCount}</p>
        </div>
        <div className="rounded-2xl border border-amber-100 bg-amber-50/60 px-5 py-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-amber-600">部分满足</p>
          <p className="mt-2 text-2xl font-black text-amber-700">{partialCount}</p>
        </div>
        <div className="rounded-2xl border border-rose-100 bg-rose-50/60 px-5 py-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-rose-600">待补充</p>
          <p className="mt-2 text-2xl font-black text-rose-700">{gapCount}</p>
        </div>
      </div>

      <div className="overflow-hidden rounded-3xl border border-base-300 bg-base-100 shadow-sm">
        <table className="table table-lg w-full">
          <thead className="bg-base-200/50">
            <tr className="border-b border-base-300">
              <th className="py-6 pl-8 text-[10px] font-black uppercase tracking-widest">偏离状态</th>
              <th className="py-6 text-[10px] font-black uppercase tracking-widest">标书要求原文</th>
              <th className="py-6 text-[10px] font-black uppercase tracking-widest">AI 推荐应答项</th>
              <th className="py-6 pr-8 text-right text-[10px] font-black uppercase tracking-widest">操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="group border-b border-base-200 transition-colors hover:bg-base-50/50">
                <td className="py-6 pl-8">
                  {item.status === 'compliant' ? (
                    <div className="badge badge-success gap-1 py-3 text-[9px] font-black uppercase">
                      <CheckCircle size={10} /> 完全满足
                    </div>
                  ) : item.status === 'gap' ? (
                    <div className="badge gap-1 border-0 bg-rose-100 py-3 text-[9px] font-black uppercase text-rose-700">
                      <AlertCircle size={10} /> 待补充
                    </div>
                  ) : (
                    <div className="badge badge-warning gap-1 py-3 text-[9px] font-black uppercase">
                      <AlertCircle size={10} /> 部分满足
                    </div>
                  )}
                </td>
                <td className="max-w-md py-6">
                  <p className="text-xs font-bold leading-relaxed">{item.req}</p>
                  {(item.original_section || item.evidence_required) && (
                    <p className="mt-2 text-[10px] font-medium text-zinc-400">
                      {[item.original_section, item.evidence_required ? `证明材料：${item.evidence_required}` : null].filter(Boolean).join(' · ')}
                    </p>
                  )}
                </td>
                <td className="py-6">
                  {editingId === item.id ? (
                    <div className="space-y-3">
                      <textarea
                        className="textarea textarea-bordered w-full bg-base-100 text-xs font-medium leading-relaxed"
                        value={item.resp}
                        rows={3}
                        onChange={(e) => {
                          setItems((current) => current.map((entry) => (entry.id === item.id ? { ...entry, resp: e.target.value } : entry)));
                        }}
                      />
                      <select
                        className="select select-bordered select-sm w-full max-w-[220px] text-xs font-bold"
                        value={item.status}
                        onChange={(e) => {
                          const value = e.target.value as DeviationMatrixItem['status'];
                          setItems((current) => current.map((entry) => (entry.id === item.id ? { ...entry, status: value } : entry)));
                        }}
                      >
                        <option value="compliant">完全满足</option>
                        <option value="partial">部分满足</option>
                        <option value="gap">待补充</option>
                        <option value="unknown">待判断</option>
                      </select>
                    </div>
                  ) : (
                    <p className="text-xs font-medium italic leading-relaxed text-base-content/80">"{item.resp}"</p>
                  )}
                </td>
                <td className="py-6 pr-8 text-right">
                  <button onClick={() => setEditingId(editingId === item.id ? null : item.id)} className="btn btn-ghost btn-sm btn-square rounded-lg transition-all hover:bg-primary/10 hover:text-primary">
                    {editingId === item.id ? <Save size={16} /> : <Edit3 size={16} />}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-10 flex items-center justify-between rounded-2xl border border-primary/10 bg-primary/5 p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 font-black text-primary">AI</div>
          <div>
            <p className="text-xs font-black uppercase tracking-widest text-primary">合规性应答策略</p>
            <p className="text-[11px] font-medium text-base-content/60">"通过自动资产库匹配完成初步应答。"</p>
          </div>
        </div>
        <div className="flex gap-2">
          <span className="badge badge-neutral py-3 font-mono text-[10px]">COMPLIANT: {compliantCount}</span>
          <span className="badge badge-neutral py-3 font-mono text-[10px]">PARTIAL: {partialCount}</span>
        </div>
      </div>
      {statusMessage && (
        <div className="mt-4 rounded-2xl border border-zinc-100 bg-white px-5 py-4 text-sm font-bold text-zinc-700">
          {statusMessage}
        </div>
      )}
    </div>
  );
};

export default DeviationMatrix;
