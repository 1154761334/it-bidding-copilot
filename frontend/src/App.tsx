import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import TopAppBar from './components/layout/TopAppBar';
import SideNavBar from './components/layout/SideNavBar';
import AIPromptBar from './components/layout/AIPromptBar';
import SettingsDialog from './components/layout/SettingsDialog';

import Dashboard from './pages/Dashboard';
import EnterpriseAI from './pages/EnterpriseAI';
import ManualProfile from './pages/ManualProfile';
import RFPAnalysis from './pages/RFPAnalysis';
import BiddingHall from './pages/BiddingHall';
import ReviewExport from './pages/ReviewExport';
import DeviationMatrix from './pages/DeviationMatrix';
import ReviewCycle from './pages/ReviewCycle';
import { useProjectContextStore } from './store/useProjectContextStore';

const App: React.FC = () => {
  const { bootstrapContext } = useProjectContextStore();

  React.useEffect(() => {
    bootstrapContext();
  }, [bootstrapContext]);

  return (
    <Router>
      <div className="flex min-h-screen bg-surface">
        <SideNavBar />
        <div className="flex-1 flex flex-col min-w-0">
          <TopAppBar />
          <main className="flex-1 overflow-y-auto no-scrollbar pb-32">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/profile" element={<EnterpriseAI />} />
              <Route path="/profile/basics" element={<ManualProfile />} />
              <Route path="/profile/manual" element={<ManualProfile />} />
              <Route path="/rfp" element={<RFPAnalysis />} />
              <Route path="/bidding" element={<BiddingHall />} />
              <Route path="/deviation" element={<DeviationMatrix />} />
              <Route path="/audit" element={<ReviewCycle />} />
              <Route path="/review" element={<ReviewExport />} />
              <Route path="*" element={<div className="p-20 text-center font-bold text-zinc-400">页面正在建设中...</div>} />
            </Routes>
          </main>
          <AIPromptBar />
        </div>
      </div>
      <SettingsDialog />
    </Router>
  );
};

export default App;
