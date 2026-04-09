import React from 'react'
import { LayoutDashboard, Building2, FileText, PenTool, Search, Download } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

const Sidebar = () => {
  const location = useLocation()
  
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Enterprise Profile', path: '/profile', icon: Building2 },
    { name: 'RFP Analysis', path: '/rfp', icon: FileText },
    { name: 'Bidding Hall', path: '/bidding', icon: PenTool },
    { name: 'Review Cycle', path: '/review', icon: Search },
    { name: 'Export', path: '/export', icon: Download },
  ]

  return (
    <div className="w-72 bg-neutral text-neutral-content h-screen flex flex-col shadow-2xl border-r border-base-content/10">
      <div className="p-8 flex items-center gap-3">
        <div className="bg-primary p-2 rounded-xl shadow-lg shadow-primary/20">
          <Building2 className="text-primary-content" size={24} />
        </div>
        <h1 className="text-lg font-black tracking-tighter">BIDDING COPILOT</h1>
      </div>
      
      <nav className="flex-1 px-4 py-4 space-y-2">
        {navItems.map((item) => (
          <Link
            key={item.name}
            to={item.path}
            className={`flex items-center gap-4 px-4 py-3.5 rounded-xl transition-all duration-200 group ${
              location.pathname === item.path 
                ? 'bg-primary text-primary-content shadow-lg shadow-primary/20' 
                : 'hover:bg-neutral-content/10 text-neutral-content/60 hover:text-neutral-content'
            }`}
          >
            <item.icon size={20} className={location.pathname === item.path ? 'animate-pulse' : 'group-hover:scale-110 transition-transform'} />
            <span className="font-semibold text-sm">{item.name}</span>
          </Link>
        ))}
      </nav>

      <div className="p-4 mt-auto">
        <div className="bg-neutral-focus/30 rounded-2xl p-4 border border-neutral-content/10">
          <p className="text-[10px] font-bold uppercase tracking-widest text-neutral-content/40 mb-2">Current Project</p>
          <p className="text-sm font-bold truncate">Cloud Infra Bidding 2026</p>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
