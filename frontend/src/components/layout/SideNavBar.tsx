import React from 'react';
import { NavLink } from 'react-router-dom';
import { useSettingsStore } from '../../store/useSettingsStore';

const SideNavBar: React.FC = () => {
  const { openSettings } = useSettingsStore();
  
  const getLinkClasses = ({ isActive }: { isActive: boolean }) => {
    const base = "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-transform duration-200 hover:translate-x-1 ";
    if (isActive) {
      return base + "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 font-semibold shadow-sm";
    }
    return base + "text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800/50 font-medium";
  };

  return (
    <aside className="hidden md:flex flex-col py-6 px-4 gap-2 h-screen w-64 border-r border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 sticky top-0 shrink-0">
      <div className="flex items-center gap-3 px-2 mb-10">
        <div className="w-10 h-10 bg-primary flex items-center justify-center rounded-lg">
          <span className="material-symbols-outlined text-white filled">business_center</span>
        </div>
        <div>
          <h1 className="text-xl font-black text-zinc-900 dark:text-zinc-50 leading-none">标书助手</h1>
          <p className="text-[10px] uppercase tracking-widest text-secondary mt-1 font-bold">IT 招标全流程套件</p>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        <NavLink to="/dashboard" className={getLinkClasses}>
          <span className="material-symbols-outlined text-[20px]">dashboard</span>
          <span>控制面板</span>
        </NavLink>
        <NavLink to="/profile" className={getLinkClasses}>
          <span className="material-symbols-outlined text-[20px]">business_center</span>
          <span>企业资产档案</span>
        </NavLink>
        <NavLink to="/rfp" className={getLinkClasses}>
          <span className="material-symbols-outlined text-[20px]">analytics</span>
          <span>标书解析建议</span>
        </NavLink>
        <NavLink to="/bidding" className={getLinkClasses}>
          <span className="material-symbols-outlined text-[20px]">gavel</span>
          <span>智能编标大厅</span>
        </NavLink>
        <NavLink to="/deviation" className={getLinkClasses}>
          <span className="material-symbols-outlined text-[20px]">checklist</span>
          <span>参数偏离矩阵</span>
        </NavLink>
        <NavLink to="/audit" className={getLinkClasses}>
          <span className="material-symbols-outlined text-[20px]">security</span>
          <span>红队 AI 评估</span>
        </NavLink>
        <NavLink to="/review" className={getLinkClasses}>
          <span className="material-symbols-outlined text-[20px]">ios_share</span>
          <span>内容审计与导出</span>
        </NavLink>
        <button onClick={openSettings} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800/50 font-medium transition-colors w-full cursor-pointer text-left">
          <span className="material-symbols-outlined text-[20px]">settings</span>
          <span>系统核心设置</span>
        </button>
      </nav>

      <div className="mt-auto px-2">
        <div className="p-4 bg-surface-container-low rounded-xl">
          <p className="text-[11px] font-bold text-secondary uppercase tracking-wider mb-2">系统状态</p>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-xs font-medium">AI 核心已就绪</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default SideNavBar;
