import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useEnterpriseStore } from '../store/useEnterpriseStore';

const ManualProfile: React.FC = () => {
  const { profile, assetsOverview, fetchProfile, updateProfile, isLoading } = useEnterpriseStore();
  const [formData, setFormData] = useState({
    company_name: '',
    unified_social_credit_code: '',
    legal_representative: '',
    registered_capital: '',
    address: '',
  });
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    void fetchProfile();
  }, [fetchProfile]);

  useEffect(() => {
    setFormData({
      company_name: profile?.company_name || '',
      unified_social_credit_code: profile?.unified_social_credit_code || '',
      legal_representative: profile?.legal_representative || '',
      registered_capital: profile?.registered_capital || '',
      address: profile?.address || '',
    });
  }, [profile]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateProfile(formData);
    setSaveMessage('企业基础信息已更新');
  };

  if (isLoading && !profile) {
    return <div className="flex-1 flex items-center justify-center text-secondary">正在加载企业档案...</div>;
  }

  return (
    <div className="flex-1 overflow-y-auto no-scrollbar bg-surface pt-8 pb-24 px-12">
      <div className="max-w-6xl mx-auto">
        <header className="mb-10">
          <p className="text-[11px] font-black uppercase tracking-[0.25em] text-primary mb-3">Enterprise Profile</p>
          <h1 className="text-4xl font-black tracking-tight text-zinc-950 mb-3">企业主体信息维护</h1>
          <p className="text-secondary text-base max-w-3xl leading-relaxed">
            这个页面只负责维护企业名称、统一社会信用代码、法定代表人和办公地址等基础字段。
            证书、案例、人员和图片证据以系统已入库结果为准，请回到企业资产中心继续上传与整理。
          </p>
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          <section className="xl:col-span-7 bg-white rounded-3xl border border-zinc-100 p-8 ambient-shadow">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-2xl font-black tracking-tight text-primary">基础信息</h2>
                <p className="text-sm text-secondary font-medium mt-1">这些字段会直接影响企业档案、仪表盘和后续项目上下文。</p>
              </div>
              <NavLink to="/profile" className="text-xs font-black uppercase tracking-widest text-primary hover:underline">
                返回企业资产中心
              </NavLink>
            </div>

            <form className="grid grid-cols-1 md:grid-cols-2 gap-6" onSubmit={handleSave}>
              <div className="md:col-span-2">
                <label className="block text-[11px] font-black uppercase tracking-widest text-zinc-400 mb-2">企业名称</label>
                <input
                  className="w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-4 text-lg font-bold text-zinc-900 outline-none focus:border-primary"
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-zinc-400 mb-2">统一社会信用代码</label>
                <input
                  className="w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold text-zinc-900 outline-none focus:border-primary"
                  type="text"
                  value={formData.unified_social_credit_code}
                  onChange={(e) => setFormData({ ...formData, unified_social_credit_code: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-zinc-400 mb-2">法定代表人</label>
                <input
                  className="w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold text-zinc-900 outline-none focus:border-primary"
                  type="text"
                  value={formData.legal_representative}
                  onChange={(e) => setFormData({ ...formData, legal_representative: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-zinc-400 mb-2">注册资本</label>
                <input
                  className="w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold text-zinc-900 outline-none focus:border-primary"
                  type="text"
                  value={formData.registered_capital}
                  onChange={(e) => setFormData({ ...formData, registered_capital: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-zinc-400 mb-2">办公地址</label>
                <input
                  className="w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold text-zinc-900 outline-none focus:border-primary"
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                />
              </div>

              {saveMessage && (
                <div className="md:col-span-2 rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700">
                  {saveMessage}
                </div>
              )}

              <div className="md:col-span-2 flex justify-end gap-3 pt-2">
                <NavLink to="/profile" className="px-5 py-3 text-sm font-bold text-zinc-500 hover:text-primary transition-colors">
                  返回
                </NavLink>
                <button
                  type="submit"
                  className="rounded-2xl bg-primary px-8 py-3 text-sm font-black uppercase tracking-widest text-white shadow-lg shadow-primary/20 hover:opacity-90"
                >
                  保存基础信息
                </button>
              </div>
            </form>
          </section>

          <aside className="xl:col-span-5 space-y-6">
            <div className="rounded-3xl border border-zinc-100 bg-white p-7 ambient-shadow">
              <h3 className="text-sm font-black uppercase tracking-widest text-primary mb-5">当前资产统计</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-2xl bg-zinc-50 p-4 border border-zinc-100">
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-2">证书</p>
                  <p className="text-3xl font-black text-zinc-900">{assetsOverview?.counts.certificates ?? 0}</p>
                </div>
                <div className="rounded-2xl bg-zinc-50 p-4 border border-zinc-100">
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-2">案例</p>
                  <p className="text-3xl font-black text-zinc-900">{assetsOverview?.counts.cases ?? 0}</p>
                </div>
                <div className="rounded-2xl bg-zinc-50 p-4 border border-zinc-100">
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-2">人员</p>
                  <p className="text-3xl font-black text-zinc-900">{assetsOverview?.counts.personnel ?? 0}</p>
                </div>
                <div className="rounded-2xl bg-zinc-50 p-4 border border-zinc-100">
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-2">图片证据</p>
                  <p className="text-3xl font-black text-zinc-900">{assetsOverview?.counts.images ?? 0}</p>
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-zinc-100 bg-white p-7 ambient-shadow">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-black uppercase tracking-widest text-primary">页面职责说明</h3>
                <NavLink to="/profile" className="text-[11px] font-black uppercase tracking-widest text-primary hover:underline">
                  去资产中心
                </NavLink>
              </div>
              <div className="space-y-4 text-sm text-zinc-600 leading-relaxed">
                <div className="rounded-2xl border border-zinc-100 bg-zinc-50 px-4 py-4">
                  <p className="font-bold text-zinc-900 mb-1">这里维护什么</p>
                  <p>企业名称、统一社会信用代码、法定代表人、注册资本、办公地址等主体字段。</p>
                </div>
                <div className="rounded-2xl border border-zinc-100 bg-zinc-50 px-4 py-4">
                  <p className="font-bold text-zinc-900 mb-1">哪里维护资产</p>
                  <p>证书、案例、人员、源文件和图片证据都在企业资产中心维护、编辑和删除。</p>
                </div>
                <div className="rounded-2xl border border-zinc-100 bg-zinc-50 px-4 py-4">
                  <p className="font-bold text-zinc-900 mb-1">建议操作顺序</p>
                  <p>先在企业资产中心整理材料，再回到这里确认公司主体信息，最后进入采购文件识别和编标流程。</p>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default ManualProfile;
