import React from 'react';
import { useSettingsStore } from '../../store/useSettingsStore';
import { useProjectContextStore } from '../../store/useProjectContextStore';

const TopAppBar = ({ projectName = "2024 云计算基础设施招标" }) => {
  const { openSettings } = useSettingsStore();
  const { currentProjectName } = useProjectContextStore();
  const displayProjectName = currentProjectName || projectName;
  
  return (
    <header className="flex justify-between items-center px-8 h-16 w-full bg-white/80 dark:bg-zinc-950/80 backdrop-blur-xl sticky top-0 border-b border-zinc-100 dark:border-zinc-800 z-50">
      <div className="flex items-center gap-6">
        <span className="text-lg font-bold tracking-tighter text-zinc-900 dark:text-zinc-50">BidCore 企业级套件</span>
        <div className="h-4 w-px bg-outline-variant/30 hidden md:block"></div>
        <div className="hidden lg:flex gap-6 items-center">
            <span className="material-symbols-outlined text-sm text-zinc-500 filled">folder_open</span>
            <span className="text-zinc-500 dark:text-zinc-400 text-sm font-medium">{displayProjectName}</span>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="relative hidden sm:block">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-secondary text-lg">search</span>
          <input 
            className="pl-10 pr-4 py-1.5 bg-surface-container-low border-none rounded-lg text-sm focus:ring-1 focus:ring-primary w-48" 
            placeholder="搜索标书..." 
            type="text"
          />
        </div>
        <button className="p-2 text-zinc-500 hover:text-zinc-900 transition-colors relative">
          <span className="material-symbols-outlined">notifications</span>
          <span className="absolute top-2 right-2 w-2 h-2 bg-error rounded-full"></span>
        </button>
        <button onClick={openSettings} className="p-2 text-zinc-500 hover:text-zinc-900 transition-colors">
          <span className="material-symbols-outlined">settings</span>
        </button>
        <div className="w-8 h-8 rounded-full overflow-hidden border border-zinc-200">
          <img 
            alt="Administrator Profile" 
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuChRukWmVfvrtmEQGPXxERpm_tr6kM0Fkjk4QJxQ8phrQf9vf0Fv1RVq7cUyBoqL8OHN_UXKXXodkyr_ITzgi852k1MhQwQsuhA2Mk1DzAR6BQTqcbDtqQtZEQ09BKPfVTC5dBDo4X1iW9-j9xP3V4pVi_v0oQhjlsg3A3uozyNC1JBVDiZQPMaPCKT0gfNLiq-xEwuPP8iQmxvmZOerCk5VxX57koZCDqBRiH_HByVt3K28hnMUWgxg_L-GiNEgvtnbJA9fABg64I"
          />
        </div>
      </div>
    </header>
  );
};

export default TopAppBar;
