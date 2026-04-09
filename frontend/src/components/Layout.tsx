import React from 'react'
import Sidebar from './Sidebar'
import Header from './Header'

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex bg-base-100 min-h-screen text-base-content overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        <Header />
        <main className="flex-1 overflow-y-auto bg-base-100">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout
