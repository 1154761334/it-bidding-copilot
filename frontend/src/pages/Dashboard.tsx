import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboardService, DashboardStats } from '../services/api';
import { useEnterpriseStore } from '../store/useEnterpriseStore';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { profile, fetchProfile } = useEnterpriseStore();
  const [stats, setStats] = React.useState<DashboardStats | null>(null);

  useEffect(() => {
    fetchProfile();
    dashboardService
      .getStats()
      .then(data => setStats(data))
      .catch(err => console.error("Stats fetch failed", err));
  }, [fetchProfile]);

  return (
    <div className="flex-1 overflow-y-auto no-scrollbar bg-surface pt-8 pb-32 px-8">
      <header className="mb-12">
        <h1 className="text-3xl font-black tracking-tighter text-primary">欢迎回来，管理员</h1>
        <p className="text-secondary text-sm font-medium mt-1 uppercase tracking-widest">系统运行中 • 智能助手模式已激活</p>
      </header>

      <div className="bento-grid">
        {/* Card 1: Knowledge Health */}
        <div className="col-span-12 lg:col-span-8 bg-white rounded-3xl p-8 ambient-shadow border border-zinc-100 flex flex-col justify-between min-h-[320px]">
          <div>
            <div className="flex justify-between items-start mb-6">
              <h3 className="text-xl font-bold tracking-tight">档案完备度</h3>
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">知识库健康度</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-7xl font-black tracking-tighter">{stats?.readiness || '0.0'}</span>
              <span className="text-2xl font-bold text-zinc-300">%</span>
            </div>
          </div>
          <div className="mt-8 flex gap-4">
            <div className="flex-1 h-3 bg-zinc-100 rounded-full overflow-hidden">
                <div className="h-full bg-primary transition-all duration-1000" style={{ width: `${stats?.readiness || 0}%` }}></div>
            </div>
            <span className="text-xs font-bold text-primary uppercase">准备就绪程度</span>
          </div>
          <p className="mt-6 text-sm text-secondary font-medium leading-relaxed max-w-md">
            您的企业资产档案库目前包含 {stats?.asset_count || 0} 份关键文档，支持约 {stats?.readiness || 0}% 的商务条款自动填充。
          </p>
        </div>

        {/* Card 2: Quick Start */}
        <div className="col-span-12 lg:col-span-4 bg-primary rounded-3xl p-8 ambient-shadow text-white flex flex-col justify-between min-h-[320px]">
           <div>
              <h3 className="text-xl font-bold tracking-tight mb-2">快速启动</h3>
              <p className="text-zinc-400 text-xs font-medium uppercase tracking-widest">Quick Actions</p>
           </div>
           <div className="flex flex-col gap-3">
              <button onClick={() => navigate('/rfp')} className="w-full py-4 bg-white/10 hover:bg-white/20 transition-colors rounded-2xl flex items-center justify-center gap-3 font-bold text-sm">
                <span className="material-symbols-outlined">upload_file</span>
                解析新标书
              </button>
              <button onClick={() => navigate('/bidding')} className="w-full py-4 bg-white text-primary hover:bg-zinc-100 transition-colors rounded-2xl flex items-center justify-center gap-3 font-bold text-sm">
                <span className="material-symbols-outlined filled">edit_square</span>
                继续编标
              </button>
           </div>
        </div>

        {/* Card 3: Trust Scores */}
        <div className="col-span-12 lg:col-span-4 bg-white rounded-3xl p-8 ambient-shadow border border-zinc-100 min-h-[400px] flex flex-col">
            <h3 className="text-lg font-bold tracking-tight mb-8">核心资信盘</h3>
            <div className="space-y-6 flex-1">
                <div className="flex justify-between items-center pb-4 border-b border-zinc-50">
                    <span className="text-sm font-bold text-secondary">身份核验</span>
                    <span className={`text-xs font-bold px-2 py-1 ${stats?.identity_verified ? 'bg-green-50 text-green-600' : 'bg-zinc-100 text-zinc-400'} rounded uppercase`}>
                        {stats?.identity_verified ? '已通过' : '待核验'}
                    </span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-zinc-50">
                    <span className="text-sm font-bold text-secondary">资产档案数</span>
                    <span className="text-sm font-black uppercase text-primary">{stats?.asset_count || 0} 份文档</span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-zinc-50">
                    <span className="text-sm font-bold text-secondary">进行中任务</span>
                    <span className="text-sm font-black uppercase text-primary text-amber-500">{stats?.pending_tasks || 0} 项</span>
                </div>
            </div>
            <div className="mt-8 pt-8 border-t border-zinc-100">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-zinc-50 rounded-xl flex items-center justify-center">
                         <span className="material-symbols-outlined text-zinc-400">security</span>
                    </div>
                    <div>
                        <p className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">实时安全防护</p>
                        <p className="text-xs font-bold">数据加密隧道已开启</p>
                    </div>
                </div>
            </div>
        </div>

        {/* Card 4: My Bidding Items */}
        <div className="col-span-12 lg:col-span-8 bg-white rounded-3xl p-8 ambient-shadow border border-zinc-100 min-h-[400px]">
             <div className="flex justify-between items-center mb-8">
                <h3 className="text-lg font-bold tracking-tight">进行中的投标</h3>
                <button className="text-xs font-bold text-secondary hover:text-primary uppercase tracking-widest border-b border-zinc-200 pb-0.5">查看全部</button>
             </div>
             <div className="space-y-4">
                {(stats?.active_projects || [
                  { name: "无进行中项目", status: "空闲", progress: 0, time: "--" }
                ]).map((item: any, idx: number) => (
                  <div key={idx} className="group p-4 hover:bg-zinc-50 transition-colors rounded-2xl flex items-center justify-between border border-transparent hover:border-zinc-100">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-zinc-100 flex items-center justify-center group-hover:bg-white transition-colors">
                        <span className="material-symbols-outlined text-zinc-400 group-hover:text-primary transition-colors">description</span>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-zinc-900">{item.name}</p>
                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-0.5">{item.time}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-8">
                        <div className="hidden md:block w-32">
                           <div className="h-1.5 bg-zinc-100 rounded-full overflow-hidden">
                              <div className="h-full bg-primary" style={{ width: `${item.progress}%` }}></div>
                           </div>
                        </div>
                        <span className="text-xs font-bold py-1.5 px-3 bg-zinc-50 border border-zinc-100 rounded-lg">{item.status}</span>
                    </div>
                  </div>
                ))}
             </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
