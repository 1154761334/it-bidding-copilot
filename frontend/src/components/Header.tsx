import React from 'react'
import { Bell, User, Search } from 'lucide-react'

const Header = () => {
  return (
    <header className="h-20 bg-base-100 border-b border-base-300 px-8 flex items-center justify-between sticky top-0 z-40">
      <div className="flex-1 max-w-xl">
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-base-content/40 group-focus-within:text-primary transition-colors">
            <Search size={18} />
          </div>
          <input
            type="text"
            className="input input-ghost w-full pl-12 bg-base-200/50 hover:bg-base-200 focus:bg-base-100 transition-all text-sm font-medium"
            placeholder="Search projects, documents, or insights..."
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <button className="btn btn-ghost btn-circle btn-sm relative">
            <Bell size={20} className="text-base-content/70" />
            <span className="absolute top-2 right-2 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
          </button>
        </div>
        
        <div className="h-8 w-px bg-base-300 mx-1"></div>

        <div className="flex items-center gap-3 pl-2">
             <div className="text-right hidden sm:block">
               <p className="text-sm font-bold">Alex Chen</p>
               <p className="text-[10px] text-base-content/50 uppercase tracking-wider">Lead Architect</p>
             </div>
             <div className="avatar">
               <div className="w-10 h-10 rounded-xl bg-neutral text-neutral-content flex items-center justify-center font-bold shadow-md">
                 AC
               </div>
             </div>
        </div>
      </div>
    </header>
  )
}

export default Header
