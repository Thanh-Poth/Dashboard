export const GlassCard = ({ text, width, height, isActive = false, children }) => {
  return (
    <div 
      className="relative group cursor-pointer transition-transform duration-300 hover:-translate-y-1" 
      style={{ width: width ? `${width}px` : 'auto', height: height ? `${height}px` : 'auto' }}
    >
      {/* Lueur externe subtile aux couleurs du thème */}
      <div className="absolute -inset-0.5 bg-gradient-to-br from-purple-500/20 to-transparent rounded-2xl blur-md opacity-0 group-hover:opacity-100 transition duration-500"></div>
      
      {/* Corps de la carte avec bascule d'état (Actif / Inactif) */}
      <div className={`relative w-full h-full rounded-2xl p-5 border backdrop-blur-2xl shadow-2xl transition-all duration-300 overflow-hidden ${
        isActive 
          ? 'bg-gradient-to-br from-[#8B5CF6]/30 via-[#1A1A24]/90 to-[#12121A] border-purple-500/30' 
          : 'bg-[#16161A]/90 border-white/5 group-hover:border-white/10'
      }`}>
        
        {/* Reflet supérieur (inner-glow) pour l'effet premium */}
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-50"></div>

        {/* En-tête : Titre et menu d'options */}
        {text && (
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-medium text-gray-400">{text}</h3>
            <svg className="w-5 h-5 text-gray-600 hover:text-white transition-colors" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 12a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zm8 0a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zm8 0a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
            </svg>
          </div>
        )}
        
        {/* Contenu */}
        <div className="relative z-10 text-white">
          {children}
        </div>
      </div>
    </div>
  );
};