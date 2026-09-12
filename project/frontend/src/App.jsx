import { GlassCard } from "./components/utils";
import Menu from "./components/Menu";
import Data from "./components/Data";
import Alpha from "./components/Alpha";
import Optimization from "./components/Optimization";
import Backtest from "./components/Backtest";
import React, { useState } from 'react';



function App() {
  const [activeDashboard, setActiveDashboard] = useState(null)
  const toggleDashboard = (dashboardName) => {
    setActiveDashboard(dashboardName);
  };
  return (
    <div className="flex h-screen text-white bg-black overflow-hidden">
      <div className="blob-gpu top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>
      <aside className="fixed top-[38.2%] -translate-y-1/2 left-0 z-50 w-64 p-auto text-left">
        <Menu toggleDashboard={toggleDashboard} activeTab={activeDashboard} />
      </aside>
      
      <main className="ml-72 flex-1 p-2 m-4 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600">
        <div className={activeDashboard === 'data' ? 'block' : 'hidden'}>
          <h2 className="text-xl font-bold text-white mb-4"></h2>
          <Data />
        </div>

        <div className={activeDashboard === 'alpha' ? 'block' : 'hidden'}>
          <h2 className="text-xl font-bold text-white mb-4"></h2>
          <Alpha />
        </div>

        <div className={activeDashboard === 'backtest' ? 'block' : 'hidden'}>
          <h2 className="text-xl font-bold text-white mb-4"></h2>
          <Backtest />
        </div>

        <div className={activeDashboard === 'optimization' ? 'block' : 'hidden'}>
          <h2 className="text-xl font-bold text-white mb-4"></h2>
          <Optimization />
        </div>

        
      </main>
    </div>
  );
}

export default App;
