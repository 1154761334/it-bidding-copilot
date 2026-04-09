import React from 'react';

const AIPromptBar = ({ placeholder = "试试说：‘根据官网信息自动补充公司简介’" }) => {
  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 w-full max-w-xl px-4 z-[100]">
      <div className="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-2xl p-2 rounded-2xl shadow-2xl border border-white/20 flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-zinc-950 flex items-center justify-center flex-shrink-0">
          <span className="material-symbols-outlined text-white text-xl filled">auto_awesome</span>
        </div>
        <input 
          className="flex-1 bg-transparent border-none focus:ring-0 text-sm placeholder:text-zinc-400" 
          placeholder={placeholder}
          type="text"
        />
        <button className="bg-zinc-100 hover:bg-zinc-200 transition-colors h-10 w-10 rounded-xl flex items-center justify-center text-zinc-900">
          <span className="material-symbols-outlined">send</span>
        </button>
      </div>
    </div>
  );
};

export default AIPromptBar;
