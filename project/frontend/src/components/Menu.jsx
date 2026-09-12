import { GlassCard } from "./utils";

export default function Menu({ toggleDashboard, activeTab }) {
  // Ajout d'icônes SVG pour chaque onglet afin de moderniser le rendu
  const tabs = [
    { 
      id: 'data', 
      label: 'Data',
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
    },
    { 
      id: 'alpha', 
      label: 'Alpha',
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
    },
    { 
      id: 'optimization', 
      label: 'Optimization',
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
    },
    { 
      id: 'backtest', 
      label: 'Backtest',
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
    }
  ];

  return (
    // On laisse le parent gérer la largeur totale du composant (ex: w-64 dans le layout principal)
    <div className="h-full">
      <GlassCard text="ML Project">
        <div className="flex flex-col gap-2 pt-2">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            
            return (
              <button 
                key={tab.id}
                onClick={() => toggleDashboard(tab.id)} 
                // Style dynamique de l'onglet
                className={`group flex items-center gap-3 w-full px-4 py-3 rounded-xl cursor-pointer border outline-none font-medium text-sm transition-all duration-300 ${
                  isActive 
                    ? 'bg-gradient-to-r from-purple-500/20 to-transparent border-purple-500/30 text-white shadow-sm' 
                    : 'bg-transparent border-transparent text-gray-400 hover:bg-white/5 hover:border-white/5 hover:text-white'
                }`}
              >
                {/* Couleur de l'icône qui s'adapte à l'état actif/inactif */}
                <span className={`transition-colors duration-300 ${isActive ? 'text-purple-400' : 'text-gray-500 group-hover:text-gray-300'}`}>
                  {tab.icon}
                </span>
                {tab.label}
              </button>
            );
          })}
        </div>
      </GlassCard>
    </div>
  );
}