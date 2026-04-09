import React, { useEffect, useMemo, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { EnterpriseAssetBrowserItem, enterpriseService } from '../services/api';
import { useEnterpriseStore } from '../store/useEnterpriseStore';

const assetKindOptions = [
  { value: 'all', label: '全部资产' },
  { value: 'certificate', label: '证书' },
  { value: 'case', label: '案例' },
  { value: 'personnel', label: '人员' },
  { value: 'source_document', label: '源文件' },
  { value: 'image', label: '图片证据' },
];

const editableKinds = ['certificate', 'case', 'personnel'] as const;
type EditableKind = (typeof editableKinds)[number];

const kindLabelMap: Record<string, string> = {
  certificate: '证书',
  case: '案例',
  personnel: '人员',
  source_document: '源文件',
  image: '图片证据',
};

const kindIconMap: Record<string, string> = {
  certificate: 'verified_user',
  case: 'analytics',
  personnel: 'groups',
  source_document: 'description',
  image: 'image',
};

const kindToneMap: Record<string, string> = {
  certificate: 'bg-amber-50 text-amber-600',
  case: 'bg-emerald-50 text-emerald-600',
  personnel: 'bg-violet-50 text-violet-600',
  source_document: 'bg-sky-50 text-sky-600',
  image: 'bg-rose-50 text-rose-600',
};

const buildAssetForm = (item: EnterpriseAssetBrowserItem | null): Record<string, string> => {
  if (!item) return {};
  if (item.kind === 'certificate') {
    return {
      raw_name: item.title,
      cert_type: String(item.meta.cert_type || ''),
      cert_level: String(item.meta.cert_level || ''),
      certification_scope: String(item.meta.certification_scope || item.summary || ''),
      expiry_date: String(item.meta.expiry_date || ''),
    };
  }
  if (item.kind === 'case') {
    return {
      project_name: item.title,
      industry: String(item.meta.industry || item.subtitle || ''),
      contract_amount: String(item.meta.contract_amount || ''),
      description: item.summary || '',
      compliance_keywords: String(item.meta.compliance_keywords || ''),
    };
  }
  if (item.kind === 'personnel') {
    return {
      name: item.title,
      role: item.subtitle || '',
      level: String(item.meta.level || ''),
      years_of_experience: String(item.meta.years_of_experience || ''),
      resume_text: String(item.meta.resume_text || item.summary || ''),
    };
  }
  return {};
};

const emptyCreateForm = (kind: EditableKind): Record<string, string> => {
  if (kind === 'certificate') {
    return { raw_name: '', cert_type: '', cert_level: '', certification_scope: '', expiry_date: '' };
  }
  if (kind === 'case') {
    return { project_name: '', industry: '', contract_amount: '', description: '', compliance_keywords: '' };
  }
  return { name: '', role: '', level: '', years_of_experience: '', resume_text: '' };
};

const formatMetaValue = (value: unknown) => {
  if (value === null || value === undefined || value === '') return '-';
  return String(value);
};

const getEditableRecordId = (item: EnterpriseAssetBrowserItem | null): number | null => {
  if (!item) return null;
  const metaId = Number(item.meta.record_id);
  if (Number.isFinite(metaId) && metaId > 0) return metaId;
  const [, rawId] = item.id.split('-');
  const parsed = Number(rawId);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
};

const EnterpriseAI: React.FC = () => {
  const {
    profile,
    trustScore,
    assetsOverview,
    intakeReadiness,
    latestIngestBatch,
    assetsBrowser,
    fetchProfile,
    fetchAssetsBrowser,
    uploadAssets,
    uploadQueue,
    isLoading,
  } = useEnterpriseStore();

  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [assetKind, setAssetKind] = useState('all');
  const [query, setQuery] = useState('');
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [assetForm, setAssetForm] = useState<Record<string, string>>({});
  const [createKind, setCreateKind] = useState<EditableKind>('certificate');
  const [createForm, setCreateForm] = useState<Record<string, string>>(emptyCreateForm('certificate'));
  const [assetActionMessage, setAssetActionMessage] = useState<string | null>(null);
  const [workspaceMode, setWorkspaceMode] = useState<'detail' | 'create' | 'edit'>('detail');

  useEffect(() => {
    void fetchProfile();
  }, [fetchProfile]);

  useEffect(() => {
    if (!profile?.id) return;
    void fetchAssetsBrowser(profile.id, assetKind, query);
  }, [assetKind, query, profile?.id, fetchAssetsBrowser]);

  useEffect(() => {
    const firstId = assetsBrowser?.items?.[0]?.id ?? null;
    if (!selectedAssetId || !assetsBrowser?.items.some((item) => item.id === selectedAssetId)) {
      setSelectedAssetId(firstId);
    }
    setSelectedIds((prev) => prev.filter((id) => assetsBrowser?.items.some((item) => item.id === id)));
  }, [assetsBrowser, selectedAssetId]);

  const selectedAsset = useMemo<EnterpriseAssetBrowserItem | null>(
    () => assetsBrowser?.items.find((item) => item.id === selectedAssetId) ?? null,
    [assetsBrowser, selectedAssetId],
  );
  const companyId = useMemo(
    () =>
      profile?.id ??
      assetsOverview?.company_id ??
      assetsBrowser?.company_id ??
      intakeReadiness?.company_id ??
      latestIngestBatch?.company_id ??
      null,
    [assetsBrowser?.company_id, assetsOverview?.company_id, intakeReadiness?.company_id, latestIngestBatch?.company_id, profile?.id],
  );

  useEffect(() => {
    setAssetForm(buildAssetForm(selectedAsset));
    setAssetActionMessage(null);
    setWorkspaceMode((prev) => {
      if (prev === 'create') return prev;
      if (prev === 'edit' && (!selectedAsset || !editableKinds.includes(selectedAsset.kind as EditableKind))) {
        return 'detail';
      }
      return prev;
    });
  }, [selectedAsset]);

  useEffect(() => {
    setCreateForm(emptyCreateForm(createKind));
  }, [createKind]);

  useEffect(() => {
    if (workspaceMode === 'edit' && (!selectedAsset || !editableKinds.includes(selectedAsset.kind as EditableKind))) {
      setWorkspaceMode('detail');
    }
  }, [workspaceMode, selectedAsset]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      void uploadAssets(profile?.id ?? 0, Array.from(e.target.files));
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]));
  };

  const selectedBatchItems = useMemo(
    () =>
      (assetsBrowser?.items ?? []).filter((item) => selectedIds.includes(item.id) && editableKinds.includes(item.kind as EditableKind)),
    [assetsBrowser, selectedIds],
  );

  const isEditableAsset = selectedAsset ? editableKinds.includes(selectedAsset.kind as EditableKind) : false;

  const handleAssetFieldChange = (field: string, value: string) => {
    setAssetForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleCreateFieldChange = (field: string, value: string) => {
    setCreateForm((prev) => ({ ...prev, [field]: value }));
  };

  const refreshCurrentAssets = async () => {
    if (!companyId) return;
    await fetchProfile();
    await fetchAssetsBrowser(companyId, assetKind, query);
  };

  const handleSaveAsset = async () => {
    if (!selectedAsset || !companyId || !isEditableAsset) return;
    const recordId = getEditableRecordId(selectedAsset);
    if (!recordId) {
      setAssetActionMessage('当前资产缺少可编辑记录 ID');
      return;
    }
    try {
      const payload: Record<string, unknown> = { ...assetForm };
      if (selectedAsset.kind === 'case') payload.contract_amount = assetForm.contract_amount ? Number(assetForm.contract_amount) : null;
      if (selectedAsset.kind === 'personnel') payload.years_of_experience = assetForm.years_of_experience ? Number(assetForm.years_of_experience) : 0;
      await enterpriseService.updateAsset(selectedAsset.kind as EditableKind, recordId, payload);
      setAssetActionMessage('资产信息已保存');
      await refreshCurrentAssets();
    } catch (error) {
      setAssetActionMessage(`保存失败：${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  const handleDeleteAsset = async () => {
    if (!selectedAsset || !companyId || !isEditableAsset) return;
    const recordId = getEditableRecordId(selectedAsset);
    if (!recordId) {
      setAssetActionMessage('当前资产缺少可删除记录 ID');
      return;
    }
    try {
      await enterpriseService.deleteAsset(selectedAsset.kind as EditableKind, recordId);
      setSelectedAssetId(null);
      setAssetActionMessage('资产已删除');
      setWorkspaceMode('detail');
      await refreshCurrentAssets();
    } catch (error) {
      setAssetActionMessage(`删除失败：${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  const handleCreateAsset = async () => {
    if (!companyId) {
      setAssetActionMessage('当前企业上下文未就绪，请刷新后重试');
      return;
    }
    try {
      const payload: Record<string, unknown> = { ...createForm };
      if (createKind === 'case') payload.contract_amount = createForm.contract_amount ? Number(createForm.contract_amount) : null;
      if (createKind === 'personnel') payload.years_of_experience = createForm.years_of_experience ? Number(createForm.years_of_experience) : 0;
      await enterpriseService.createAsset(createKind, payload);
      setAssetActionMessage('资产已新增');
      setCreateForm(emptyCreateForm(createKind));
      setWorkspaceMode('detail');
      await refreshCurrentAssets();
    } catch (error) {
      setAssetActionMessage(`新增失败：${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedBatchItems.length === 0) return;
    const items = selectedBatchItems
      .map((item) => {
        const id = getEditableRecordId(item);
        if (!id) return null;
        return { kind: item.kind as EditableKind, id };
      })
      .filter((item): item is { kind: EditableKind; id: number } => item !== null);
    if (items.length === 0) {
      setAssetActionMessage('当前选择中没有可删除的结构化资产');
      return;
    }
    await enterpriseService.batchDeleteAssets(
      items
    );
    setSelectedIds([]);
    setSelectedAssetId(null);
    setAssetActionMessage(`已批量删除 ${items.length} 条资产`);
    await refreshCurrentAssets();
  };

  return (
    <div className="flex-1 overflow-y-auto no-scrollbar bg-surface pt-8 pb-32 px-12">
      <div className="max-w-7xl mx-auto w-full">
        <section className="mb-12">
          <h3 className="text-4xl md:text-5xl font-black tracking-tighter text-primary mb-4">企业资产中心</h3>
          <p className="text-secondary text-lg max-w-4xl leading-relaxed font-light">
            这里统一展示企业资产名称、介绍、结构化信息和佐证材料。证书、案例、人员支持新增、修改、删除和批量删除，图片证据可直接预览。
          </p>
          {intakeReadiness && (
            <div className={`mt-6 rounded-2xl border px-5 py-4 ${intakeReadiness.ready ? 'border-emerald-200 bg-emerald-50/70' : 'border-amber-200 bg-amber-50/70'}`}>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">企业建库确认</p>
                  <p className="text-sm font-bold text-zinc-900">
                    {intakeReadiness.ready ? '企业资质库已具备新建投标项目的基础条件。' : '请先确认企业资料是否齐全，再进入新建投标项目。'}
                  </p>
                </div>
                <span className={`rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-widest ${intakeReadiness.ready ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                  {intakeReadiness.checks.filter((item) => item.passed).length}/{intakeReadiness.checks.length}
                </span>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {intakeReadiness.checks.map((check) => (
                  <div key={check.key} className="rounded-xl bg-white/80 px-4 py-3">
                    <p className="text-[11px] font-bold text-zinc-800">{check.label}</p>
                    <p className={`mt-1 text-[11px] font-black uppercase tracking-widest ${check.passed ? 'text-emerald-600' : 'text-amber-600'}`}>
                      {check.passed ? 'ready' : 'missing'}
                    </p>
                  </div>
                ))}
              </div>
              {intakeReadiness.warnings.length > 0 && (
                <div className="mt-4 space-y-2">
                  {intakeReadiness.warnings.slice(0, 3).map((warning, idx) => (
                    <p key={idx} className="text-xs font-medium text-amber-800">{warning}</p>
                  ))}
                </div>
              )}
            </div>
          )}
          {latestIngestBatch?.has_batch && (
            <div className="mt-4 rounded-2xl border border-zinc-200 bg-white px-5 py-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">本轮新入库资产待确认</p>
                  <p className="mt-1 text-sm font-bold text-zinc-900">
                    最近导入批次日期 {latestIngestBatch.batch_date}，请优先核对本轮进入企业资产库的文件和结构化结果。
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 text-[11px] font-bold text-zinc-700">
                  <span className="rounded-full bg-zinc-100 px-3 py-1">源文件 {latestIngestBatch.counts.source_documents}</span>
                  <span className="rounded-full bg-zinc-100 px-3 py-1">证书 {latestIngestBatch.counts.certificates}</span>
                  <span className="rounded-full bg-zinc-100 px-3 py-1">案例 {latestIngestBatch.counts.cases}</span>
                  <span className="rounded-full bg-zinc-100 px-3 py-1">图片 {latestIngestBatch.counts.images}</span>
                </div>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                {latestIngestBatch.source_documents.slice(0, 6).map((document) => (
                  <div key={document.id} className="rounded-xl border border-zinc-100 bg-zinc-50 px-4 py-3">
                    <p className="text-xs font-bold text-zinc-900">{document.filename}</p>
                    <p className="mt-1 text-[11px] font-black uppercase tracking-widest text-primary">{document.file_type || 'UNKNOWN'}</p>
                    <p className="mt-2 line-clamp-2 text-[11px] font-medium text-zinc-500">{document.local_path || '未记录路径'}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 space-y-1">
                {latestIngestBatch.notes.map((note, index) => (
                  <p key={index} className="text-[11px] font-medium text-zinc-500">{note}</p>
                ))}
              </div>
            </div>
          )}
        </section>

        <div className="bento-grid">
          <div className="col-span-12 lg:col-span-7 bg-white p-8 rounded-3xl ambient-shadow border border-zinc-100">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h4 className="text-xl font-bold tracking-tight text-primary">资产上传</h4>
                <p className="text-sm text-secondary font-medium">上传营业执照、ISO 认证、历史案例、人员简历和图片证据</p>
              </div>
              <span className="material-symbols-outlined text-primary text-3xl filled">cloud_upload</span>
            </div>

            <input type="file" multiple ref={fileInputRef} className="hidden" onChange={handleFileChange} />

            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-zinc-200 rounded-2xl p-12 flex flex-col items-center justify-center bg-zinc-50/30 hover:bg-zinc-50 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-5xl text-zinc-300 mb-4">upload_file</span>
              <p className="text-sm font-bold mb-1">拖拽文件至此处，或 <span className="text-primary underline underline-offset-4">点击上传</span></p>
              <p className="text-xs text-secondary font-medium">支持 PDF, DOCX, XLSX, PNG, JPG (最大 50MB)</p>
            </div>

            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
              {uploadQueue.length > 0 ? uploadQueue.map((item, idx) => (
                <div key={idx} className="flex items-center gap-3 p-4 bg-zinc-50 rounded-xl">
                  <span className="material-symbols-outlined text-zinc-400">description</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold truncate">{item.name}</p>
                    <div className="w-full bg-zinc-200 h-1 mt-1 rounded-full overflow-hidden">
                      <div className="bg-primary h-full transition-all duration-500" style={{ width: `${item.progress}%` }}></div>
                    </div>
                  </div>
                  {item.status === 'completed' ? <span className="material-symbols-outlined text-xs text-emerald-500 filled">check_circle</span> : <span className="text-[10px] font-black text-secondary">{item.progress}%</span>}
                </div>
              )) : (
                <div className="col-span-2 text-center py-4 text-xs text-zinc-400 italic font-medium">暂无正在上传的资产文件</div>
              )}
            </div>
          </div>

          <div className="col-span-12 lg:col-span-5 bg-primary text-white p-8 rounded-3xl ambient-shadow flex flex-col justify-between">
            <div>
              <h4 className="text-xl font-bold tracking-tight mb-2">资质验证状态</h4>
              <p className="text-white/60 text-sm font-medium mb-10">AI 实时验证企业信用与合规性</p>
              <div className="flex items-end gap-2 mb-1">
                <span className="text-7xl font-black tracking-tighter">{trustScore?.score ?? '0.0'}</span>
                <span className="text-2xl font-bold mb-3">/100</span>
              </div>
              <p className="text-xs font-bold text-white/80 uppercase tracking-widest mb-8">AI 综合信任评分</p>
              <div className="space-y-6">
                <div className="flex items-center justify-between"><span className="text-sm font-bold">身份核验</span><span className="text-xs font-bold text-emerald-400">{trustScore?.identity_verified ? '已通过' : '未判定'}</span></div>
                <div className="flex items-center justify-between"><span className="text-sm font-bold">合规性扫描</span><span className="text-xs font-bold">{trustScore?.compliance_status || '未知'}</span></div>
                <div className="flex items-center justify-between"><span className="text-sm font-bold">财务稳健度</span><span className="text-xs font-bold text-emerald-400">{trustScore?.financial_health || '未评级'}</span></div>
              </div>
            </div>
            <div className="mt-12 bg-white/10 p-4 rounded-2xl backdrop-blur-md text-xs leading-relaxed text-white/80 italic font-medium">
              {assetsOverview ? `当前已沉淀 ${assetsOverview.counts.certificates} 项证书、${assetsOverview.counts.cases} 个案例、${assetsOverview.counts.personnel} 位人员。` : '当前尚未建立企业资产总览。'}
            </div>
          </div>

          <div className="col-span-12 bg-white p-6 rounded-3xl ambient-shadow border border-zinc-100">
            <div className="mb-4 min-w-0">
              <h4 className="text-xl font-black tracking-tight text-primary uppercase">资产展示与维护</h4>
              <p className="mt-1 text-sm text-secondary font-medium">按名称、介绍、结构化信息和佐证材料统一管理企业资产。</p>
            </div>

            <div className="mb-4 rounded-2xl border border-zinc-100 bg-zinc-50 px-4 py-3">
              <div className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-5">
              {[
                { label: '证书', value: assetsOverview?.counts.certificates ?? 0 },
                { label: '案例', value: assetsOverview?.counts.cases ?? 0 },
                { label: '人员', value: assetsOverview?.counts.personnel ?? 0 },
                { label: '源文件', value: assetsOverview?.counts.source_documents ?? 0 },
                { label: '图片证据', value: assetsOverview?.counts.images ?? 0 },
              ].map((item) => (
                  <div key={item.label} className="rounded-xl border border-zinc-100 bg-white px-3 py-2.5">
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">{item.label}</p>
                  <p className="mt-1 text-xl font-black text-primary leading-none">{item.value}</p>
                </div>
              ))}
              </div>
            </div>

            <div className="rounded-2xl border border-zinc-100 bg-zinc-50 p-4 mb-6 space-y-3">
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-3">
                <div className="xl:col-span-7 rounded-xl bg-white border border-zinc-100 p-4">
                  <p className="text-[11px] font-black uppercase tracking-widest text-primary mb-2">筛选与搜索</p>
                  <div className="flex flex-wrap gap-2">
                    {assetKindOptions.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setAssetKind(option.value)}
                        className={`rounded-full px-3 py-1.5 text-xs font-black transition-all ${assetKind === option.value ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'bg-zinc-50 text-zinc-500 border border-zinc-200 hover:border-primary hover:text-primary'}`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="xl:col-span-5 rounded-xl bg-white border border-zinc-100 p-4">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <p className="text-[11px] font-black uppercase tracking-widest text-primary">关键词检索</p>
                    <div className="flex flex-wrap gap-2">
                      <button onClick={() => void refreshCurrentAssets()} className="rounded-lg bg-primary px-3 py-2 text-[11px] font-black text-white hover:opacity-90">
                        刷新
                      </button>
                      <NavLink to="/profile/basics" className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-[11px] font-black text-zinc-600 hover:bg-zinc-50">
                        主体信息维护
                      </NavLink>
                    </div>
                  </div>
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="搜索证书名、项目名、人员角色、文件名"
                    className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-2.5 text-sm font-medium text-zinc-900 outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="rounded-xl border border-zinc-100 bg-white px-4 py-3">
                <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                  <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">当前结果</span>
                      <span className="text-lg font-black text-primary leading-none">{assetsBrowser?.total ?? 0}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">批量选择</span>
                      <span className="font-bold text-zinc-700">{selectedIds.length > 0 ? `已勾选 ${selectedIds.length} 条` : '尚未勾选资产'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">说明</span>
                      <span className="font-medium text-zinc-600">图片和源文件以浏览为主，结构化资产支持维护。</span>
                    </div>
                  </div>

                  <button
                    onClick={() => void handleBatchDelete()}
                    disabled={selectedBatchItems.length === 0}
                    className="shrink-0 rounded-xl border border-red-200 px-4 py-2 text-xs font-black uppercase tracking-widest text-red-600 hover:bg-red-50 disabled:opacity-40"
                  >
                    批量删除已选资产
                  </button>
                </div>
              </div>
              <p className="text-[11px] text-zinc-500 font-medium">批量删除仅支持证书、案例、人员三类；主体信息维护已并入上方工具区。</p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
              <div className="xl:col-span-5 rounded-2xl border border-zinc-100 bg-zinc-50 p-6">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h5 className="text-[11px] font-black uppercase tracking-widest text-primary">资产列表</h5>
                    <p className="text-xs text-zinc-500 font-medium mt-1">点击查看详情。可维护资产支持勾选和批量删除。</p>
                  </div>
                  {isLoading && <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">loading</span>}
                </div>
                <div className="space-y-3 max-h-[720px] overflow-y-auto no-scrollbar pr-1">
                  {(assetsBrowser?.items ?? []).map((item) => {
                    const checked = selectedIds.includes(item.id);
                    const canSelect = editableKinds.includes(item.kind as EditableKind);
                    return (
                      <div key={item.id} className={`group rounded-2xl border px-4 py-4 transition-all ${selectedAsset?.id === item.id ? 'border-primary bg-white shadow-lg shadow-primary/5' : 'border-zinc-100 bg-white hover:border-zinc-300 hover:bg-zinc-50/60'}`}>
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            checked={checked}
                            disabled={!canSelect}
                            onChange={() => toggleSelection(item.id)}
                            className="mt-1 h-4 w-4 rounded border-zinc-300 text-primary focus:ring-primary disabled:opacity-30"
                          />
                          <div className={`mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${kindToneMap[item.kind] || 'bg-zinc-100 text-zinc-500'}`}>
                            <span className="material-symbols-outlined text-[20px]">{kindIconMap[item.kind] || 'description'}</span>
                          </div>
                          <button onClick={() => {
                            setSelectedAssetId(item.id);
                            setWorkspaceMode('detail');
                          }} className="flex-1 text-left">
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-1">{kindLabelMap[item.kind]}</p>
                                <p className="text-sm font-bold text-zinc-900">{item.title}</p>
                                <p className="mt-1 text-[11px] font-medium text-zinc-500">{item.subtitle}</p>
                              </div>
                              <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedAssetId(item.id);
                                    setWorkspaceMode('detail');
                                  }}
                                  className="rounded-lg p-2 text-zinc-400 hover:bg-white hover:text-zinc-700"
                                >
                                  <span className="material-symbols-outlined text-[18px]">visibility</span>
                                </button>
                                <button
                                  type="button"
                                  disabled={!canSelect}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedAssetId(item.id);
                                    setWorkspaceMode('edit');
                                  }}
                                  className="rounded-lg p-2 text-zinc-400 hover:bg-white hover:text-zinc-700 disabled:opacity-30"
                                >
                                  <span className="material-symbols-outlined text-[18px]">edit</span>
                                </button>
                              </div>
                            </div>
                            <p className="mt-2 text-xs text-zinc-600 line-clamp-2">{item.summary}</p>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                  {!assetsBrowser?.items.length && (
                    <div className="rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-center">
                      <p className="text-xs font-medium italic text-zinc-400">当前筛选下没有找到资产。可以切换分类、手动新增或重新上传材料。</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="xl:col-span-7 space-y-6">
                <div className="overflow-hidden rounded-2xl border border-zinc-100 bg-white shadow-sm">
                  <div className="border-b border-zinc-100 bg-zinc-50 px-6 pt-5">
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => setWorkspaceMode('detail')}
                        className={`rounded-t-xl px-4 py-2.5 text-xs font-black transition-all ${workspaceMode === 'detail' ? 'border-x border-t border-zinc-200 bg-white text-primary' : 'text-zinc-500 hover:text-zinc-800'}`}
                      >
                        详情
                      </button>
                      <button
                        onClick={() => setWorkspaceMode('create')}
                        className={`rounded-t-xl px-4 py-2.5 text-xs font-black transition-all ${workspaceMode === 'create' ? 'border-x border-t border-zinc-200 bg-white text-primary' : 'text-zinc-500 hover:text-zinc-800'}`}
                      >
                        新增
                      </button>
                      <button
                        onClick={() => isEditableAsset && setWorkspaceMode('edit')}
                        disabled={!isEditableAsset}
                        className={`rounded-t-xl px-4 py-2.5 text-xs font-black transition-all ${workspaceMode === 'edit' ? 'border-x border-t border-zinc-200 bg-white text-primary' : 'text-zinc-500 hover:text-zinc-800'} disabled:opacity-40`}
                      >
                        编辑
                      </button>
                    </div>
                  </div>
                  <div className="border-b border-zinc-100 bg-zinc-50 px-6 py-4">
                    <h5 className="text-[11px] font-black uppercase tracking-widest text-primary">右侧工作区</h5>
                    <p className="mt-1 text-xs font-medium text-zinc-500">单工作区模式。详情、新增、编辑分开处理，避免在同一面板里堆叠多个表单。</p>
                  </div>
                  <div className="bg-zinc-50 p-6">

                  {workspaceMode === 'detail' && (
                    <>
                  <div className="mb-4">
                    <h5 className="text-[11px] font-black uppercase tracking-widest text-primary">资产详情</h5>
                    <p className="text-xs text-zinc-500 font-medium mt-1">美观展示名称、介绍、结构化信息和佐证材料。</p>
                  </div>
                  {selectedAsset ? (
                    <div className="space-y-4">
                      <div className="rounded-2xl bg-white p-5 border border-zinc-100">
                        <div className="mb-4 flex items-start justify-between gap-4">
                          <div className="flex items-start gap-4">
                            <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${kindToneMap[selectedAsset.kind] || 'bg-zinc-100 text-zinc-500'}`}>
                              <span className="material-symbols-outlined text-[24px]">{kindIconMap[selectedAsset.kind] || 'description'}</span>
                            </div>
                            <div>
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-2">{kindLabelMap[selectedAsset.kind]}</p>
                              <h6 className="text-2xl font-black text-zinc-900 mb-1">{selectedAsset.title}</h6>
                              <p className="text-sm font-bold text-primary">{selectedAsset.subtitle}</p>
                            </div>
                          </div>
                          <div className="rounded-xl border border-zinc-100 bg-zinc-50 px-3 py-2 text-right">
                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">记录 ID</p>
                            <p className="mt-1 text-xs font-mono text-zinc-700">{formatMetaValue(selectedAsset.meta.record_id || selectedAsset.id)}</p>
                          </div>
                        </div>
                        <p className="text-sm leading-relaxed text-zinc-600 whitespace-pre-wrap">{selectedAsset.summary}</p>
                      </div>

                      <div className="rounded-2xl bg-white p-5 border border-zinc-100">
                        <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3">相关信息</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-3">
                          {Object.entries(selectedAsset.meta).map(([key, value]) => (
                            <div key={key} className="rounded-xl border border-zinc-100 bg-zinc-50 px-4 py-3">
                              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-1">{key}</p>
                              <p className="text-sm font-medium text-zinc-700 break-all">{formatMetaValue(value)}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {selectedAsset.kind === 'image' && typeof selectedAsset.meta.preview_url === 'string' && (
                        <div className="rounded-2xl bg-white p-5 border border-zinc-100">
                          <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3">佐证材料预览</p>
                          <img src={selectedAsset.meta.preview_url} alt={selectedAsset.title} className="w-full rounded-xl border border-zinc-100 bg-zinc-50 object-contain max-h-[320px]" />
                        </div>
                      )}

                      {selectedAsset.kind === 'certificate' && typeof selectedAsset.meta.image_url === 'string' && selectedAsset.meta.image_url && (
                        <div className="rounded-2xl bg-white p-5 border border-zinc-100">
                          <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3">证书佐证材料</p>
                          <img src={String(selectedAsset.meta.image_url)} alt={selectedAsset.title} className="w-full rounded-xl border border-zinc-100 bg-zinc-50 object-contain max-h-[320px]" />
                        </div>
                      )}

                      {selectedAsset.kind === 'personnel' && typeof selectedAsset.meta.social_security_image_url === 'string' && selectedAsset.meta.social_security_image_url && (
                        <div className="rounded-2xl bg-white p-5 border border-zinc-100">
                          <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3">社保证明</p>
                          <img src={String(selectedAsset.meta.social_security_image_url)} alt={selectedAsset.title} className="w-full rounded-xl border border-zinc-100 bg-zinc-50 object-contain max-h-[320px]" />
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-center">
                      <p className="text-xs font-medium italic text-zinc-400">请选择左侧任意一条资产，查看详情和佐证材料。</p>
                    </div>
                  )}
                    </>
                  )}

                  {workspaceMode === 'create' && (
                    <div className="space-y-5">
                      <div className="flex items-center justify-between">
                        <div>
                          <h5 className="text-[11px] font-black uppercase tracking-widest text-primary">新增资产</h5>
                          <p className="text-xs text-zinc-500 font-medium mt-1">先选资产类别，再填写结构化字段。保存后会回到详情视图。</p>
                        </div>
                        {assetActionMessage && <span className="text-xs font-bold text-emerald-600">{assetActionMessage}</span>}
                      </div>

                      <div className="rounded-2xl bg-white p-4 border border-zinc-100 space-y-3">
                        <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">新增资产类别</p>
                        <div className="grid grid-cols-3 gap-2">
                          {editableKinds.map((kind) => (
                            <button
                              key={kind}
                              onClick={() => setCreateKind(kind)}
                              className={`rounded-xl px-3 py-2 text-xs font-black transition-all ${createKind === kind ? 'bg-primary text-white' : 'bg-zinc-50 text-zinc-600 border border-zinc-200'}`}
                            >
                              {kindLabelMap[kind]}
                            </button>
                          ))}
                        </div>

                        {createKind === 'certificate' && (
                          <div className="space-y-3">
                            <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.raw_name || ''} onChange={(e) => handleCreateFieldChange('raw_name', e.target.value)} placeholder="证书名称" />
                            <div className="grid grid-cols-2 gap-3">
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.cert_type || ''} onChange={(e) => handleCreateFieldChange('cert_type', e.target.value)} placeholder="证书类型" />
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.cert_level || ''} onChange={(e) => handleCreateFieldChange('cert_level', e.target.value)} placeholder="证书等级" />
                            </div>
                            <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.expiry_date || ''} onChange={(e) => handleCreateFieldChange('expiry_date', e.target.value)} placeholder="有效期 YYYY-MM-DD" />
                            <textarea className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm min-h-24" value={createForm.certification_scope || ''} onChange={(e) => handleCreateFieldChange('certification_scope', e.target.value)} placeholder="证书介绍 / 适用范围" />
                          </div>
                        )}

                        {createKind === 'case' && (
                          <div className="space-y-3">
                            <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.project_name || ''} onChange={(e) => handleCreateFieldChange('project_name', e.target.value)} placeholder="案例名称" />
                            <div className="grid grid-cols-2 gap-3">
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.industry || ''} onChange={(e) => handleCreateFieldChange('industry', e.target.value)} placeholder="行业" />
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.contract_amount || ''} onChange={(e) => handleCreateFieldChange('contract_amount', e.target.value)} placeholder="合同金额" />
                            </div>
                            <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.compliance_keywords || ''} onChange={(e) => handleCreateFieldChange('compliance_keywords', e.target.value)} placeholder="合规关键词" />
                            <textarea className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm min-h-24" value={createForm.description || ''} onChange={(e) => handleCreateFieldChange('description', e.target.value)} placeholder="案例介绍" />
                          </div>
                        )}

                        {createKind === 'personnel' && (
                          <div className="space-y-3">
                            <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.name || ''} onChange={(e) => handleCreateFieldChange('name', e.target.value)} placeholder="姓名" />
                            <div className="grid grid-cols-3 gap-3">
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.role || ''} onChange={(e) => handleCreateFieldChange('role', e.target.value)} placeholder="角色" />
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.level || ''} onChange={(e) => handleCreateFieldChange('level', e.target.value)} placeholder="级别" />
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={createForm.years_of_experience || ''} onChange={(e) => handleCreateFieldChange('years_of_experience', e.target.value)} placeholder="经验年限" />
                            </div>
                            <textarea className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm min-h-24" value={createForm.resume_text || ''} onChange={(e) => handleCreateFieldChange('resume_text', e.target.value)} placeholder="人员介绍" />
                          </div>
                        )}

                        <div className="flex justify-end">
                          <button
                            data-testid="enterprise-create-asset-submit"
                            onClick={() => void handleCreateAsset()}
                            className="rounded-xl bg-primary px-5 py-2 text-xs font-black uppercase tracking-widest text-white hover:opacity-90"
                          >
                            新增资产
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {workspaceMode === 'edit' && (
                    <div className="space-y-5">
                      <div className="flex items-center justify-between">
                        <div>
                          <h5 className="text-[11px] font-black uppercase tracking-widest text-primary">编辑当前资产</h5>
                          <p className="text-xs text-zinc-500 font-medium mt-1">先从左侧选择一条证书、案例或人员资产，再在这里修改。</p>
                        </div>
                        {assetActionMessage && <span className="text-xs font-bold text-emerald-600">{assetActionMessage}</span>}
                      </div>

                      {isEditableAsset && selectedAsset ? (
                        <div className="rounded-2xl bg-white p-4 border border-zinc-100 space-y-3">
                          <div className="rounded-xl border border-zinc-100 bg-zinc-50 px-4 py-3">
                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-1">当前对象</p>
                            <p className="text-sm font-bold text-zinc-900">{selectedAsset.title}</p>
                            <p className="text-xs text-zinc-500 mt-1">{selectedAsset.subtitle}</p>
                          </div>

                          {selectedAsset.kind === 'certificate' && (
                            <div className="space-y-3">
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.raw_name || ''} onChange={(e) => handleAssetFieldChange('raw_name', e.target.value)} placeholder="证书名称" />
                              <div className="grid grid-cols-2 gap-3">
                                <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.cert_type || ''} onChange={(e) => handleAssetFieldChange('cert_type', e.target.value)} placeholder="证书类型" />
                                <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.cert_level || ''} onChange={(e) => handleAssetFieldChange('cert_level', e.target.value)} placeholder="证书等级" />
                              </div>
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.expiry_date || ''} onChange={(e) => handleAssetFieldChange('expiry_date', e.target.value)} placeholder="有效期 YYYY-MM-DD" />
                              <textarea className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm min-h-24" value={assetForm.certification_scope || ''} onChange={(e) => handleAssetFieldChange('certification_scope', e.target.value)} placeholder="资质覆盖范围" />
                            </div>
                          )}

                          {selectedAsset.kind === 'case' && (
                            <div className="space-y-3">
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.project_name || ''} onChange={(e) => handleAssetFieldChange('project_name', e.target.value)} placeholder="案例名称" />
                              <div className="grid grid-cols-2 gap-3">
                                <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.industry || ''} onChange={(e) => handleAssetFieldChange('industry', e.target.value)} placeholder="行业" />
                                <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.contract_amount || ''} onChange={(e) => handleAssetFieldChange('contract_amount', e.target.value)} placeholder="合同金额" />
                              </div>
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.compliance_keywords || ''} onChange={(e) => handleAssetFieldChange('compliance_keywords', e.target.value)} placeholder="合规关键词" />
                              <textarea className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm min-h-24" value={assetForm.description || ''} onChange={(e) => handleAssetFieldChange('description', e.target.value)} placeholder="案例介绍" />
                            </div>
                          )}

                          {selectedAsset.kind === 'personnel' && (
                            <div className="space-y-3">
                              <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.name || ''} onChange={(e) => handleAssetFieldChange('name', e.target.value)} placeholder="姓名" />
                              <div className="grid grid-cols-3 gap-3">
                                <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.role || ''} onChange={(e) => handleAssetFieldChange('role', e.target.value)} placeholder="角色" />
                                <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.level || ''} onChange={(e) => handleAssetFieldChange('level', e.target.value)} placeholder="级别" />
                                <input className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm" value={assetForm.years_of_experience || ''} onChange={(e) => handleAssetFieldChange('years_of_experience', e.target.value)} placeholder="经验年限" />
                              </div>
                              <textarea className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm min-h-24" value={assetForm.resume_text || ''} onChange={(e) => handleAssetFieldChange('resume_text', e.target.value)} placeholder="人员介绍" />
                            </div>
                          )}

                          <div className="flex justify-end gap-3">
                            <button
                              data-testid="enterprise-delete-asset-submit"
                              onClick={() => void handleDeleteAsset()}
                              className="rounded-xl border border-red-200 px-4 py-2 text-xs font-black uppercase tracking-widest text-red-600 hover:bg-red-50"
                            >
                              删除资产
                            </button>
                            <button
                              data-testid="enterprise-save-asset-submit"
                              onClick={() => void handleSaveAsset()}
                              className="rounded-xl bg-primary px-5 py-2 text-xs font-black uppercase tracking-widest text-white hover:opacity-90"
                            >
                              保存修改
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-center">
                          <p className="text-xs font-medium italic text-zinc-400">当前未选择可编辑资产。请先在左侧选择一条证书、案例或人员，再切到编辑视图。</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnterpriseAI;
