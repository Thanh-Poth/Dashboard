import React, { useState } from 'react';
import { GlassCard } from "./utils";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from 'recharts';
import { API_BASE_URL } from "../config";

export default function Backtest() {
  const [loading, setLoading] = useState(false);
  const [backtestData, setBacktestData] = useState(null);
  const [error, setError] = useState(null);
  // States pour les paramètres d'entrée
  const [modelFile, setModelFile] = useState(null); // Fichier de poids du modèle (.joblib / .pkl)
  const [file, setFile] = useState(null); // State pour le fichier dataset
  const [ticker, setTicker] = useState("AAPL");
  const [startDate, setStartDate] = useState("2025-01-01");
  const [endDate, setEndDate] = useState("2026-01-01");

  // Styles
  const inputStyle = "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm outline-none focus:border-purple-500/50 focus:bg-white/10 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300 placeholder:text-gray-500";
  const selectStyle = `${inputStyle} appearance-none cursor-pointer bg-[#16161A]`;
  
  // Style spécifique pour l'input file avec Tailwind
  const fileInputStyle = "w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-500/10 file:text-purple-400 hover:file:bg-purple-500/20 file:cursor-pointer cursor-pointer focus:outline-none";

  const startBacktest = async () => {
    if (!file) {
      alert("Veuillez sélectionner un fichier dataset (ex: .csv) !");
      return;
    }
    if (!modelFile) {
      alert("Veuillez sélectionner un fichier de modèle entraîné (.joblib / .pkl) !");
      return;
    }

    setLoading(true);
    try {
      // Utilisation de FormData pour envoyer les fichiers et les autres champs
      const formData = new FormData();
      formData.append("file", file);
      formData.append("model_file", modelFile);
      formData.append("ticker", ticker);
      formData.append("start_date", startDate);
      formData.append("end_date", endDate);

      const response = await fetch(`${API_BASE_URL}/api/run-backtest`, {
        method: "POST",
        // Ne PAS définir le Content-Type manuellement ici. 
        // Le navigateur le définira automatiquement sur "multipart/form-data" avec le bon "boundary"
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Erreur lors du backtest");
      }

      const result = await response.json();

      if (result.error) {
        setError(result.error);      // il te faut ajouter un state `error` comme dans Alpha.jsx
        setBacktestData(null);
      } else {
        setBacktestData(result);
      }
    } catch (error) {
      console.error("Erreur Backend :", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6 w-full max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-2xl font-semibold text-white">Strategy Backtesting</h1>
        <p className="text-sm text-gray-400">Upload your dataset and evaluate model performance.</p>
      </div>

      {/* SECTION CONTRÔLES / INPUTS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-5 items-stretch">
        <GlassCard text="Model (weights)" isActive={true}>
          <div className="pt-2 flex flex-col gap-1 h-full">
            <input
              type="file"
              accept=".pkl,.joblib"
              onChange={(e) => setModelFile(e.target.files[0])}
              className={fileInputStyle}
            />
            {modelFile && (
              <span className="text-xs text-gray-500 truncate">{modelFile.name}</span>
            )}
          </div>
        </GlassCard>

        <GlassCard text="Alpha Formulas (CSV)">
          <div className="pt-2 flex items-center h-full">
            <input 
              type="file" 
              accept=".csv" 
              onChange={(e) => setFile(e.target.files[0])}
              className={fileInputStyle}
            />
          </div>
        </GlassCard>

        <GlassCard text="Ticker">
          <div className="pt-2">
            <input 
              type="text" 
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="Ex: AAPL" 
              className={inputStyle}
            />
          </div>
        </GlassCard>

        <GlassCard text="Start Date">
          <div className="pt-2">
            <input 
              type="date" 
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className={`${inputStyle} [color-scheme:dark] cursor-pointer`}
            />
          </div>
        </GlassCard>

        <GlassCard text="End Date">
          <div className="pt-2">
            <input 
              type="date" 
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className={`${inputStyle} [color-scheme:dark] cursor-pointer`}
            />
          </div>
        </GlassCard>
      </div>

      {/* BOUTON DE LANCEMENT */}
      <div className="flex items-center">
        <button 
          onClick={startBacktest} 
          disabled={loading}
          className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium py-2.5 px-8 rounded-xl shadow-lg shadow-purple-500/20 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-0.5 active:translate-y-0"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              Uploading & Running...
            </span>
          ) : 'Run Backtest'}
        </button>
      </div>
      {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-4 text-rose-400 text-sm">
            {error}
          </div>
      )}
      {/* RÉSULTATS */}
      {backtestData && (
        <div className="flex flex-col gap-5 animate-in fade-in duration-700">
          
          {/* GRILLE KPIs TRADING - 14 Indicateurs */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 items-stretch">
            {/* Ligne 1 : Rendements & Risques globaux */}
            <GlassCard text="CAGR">
                <span className="text-2xl font-bold text-emerald-400">{backtestData.kpis?.cagr}</span>
            </GlassCard>
            <GlassCard text="Max Drawdown">
                <span className="text-2xl font-bold text-rose-400">{backtestData.kpis?.maxDrawdown}</span>
            </GlassCard>
            <GlassCard text="Volatility">
                <span className="text-2xl font-bold text-white">{backtestData.kpis?.volatility}</span>
            </GlassCard>
            <GlassCard text="VaR 95%">
                <span className="text-2xl font-bold text-rose-400">{backtestData.kpis?.var95}</span>
            </GlassCard>
            <GlassCard text="CVaR 95%">
                <span className="text-2xl font-bold text-rose-400">{backtestData.kpis?.cvar95}</span>
            </GlassCard>

            {/* Ligne 2 : Ratios d'efficacité */}
            <GlassCard text="Sharpe Ratio">
                <span className="text-2xl font-bold text-white">{backtestData.kpis?.sharpe}</span>
            </GlassCard>
            <GlassCard text="Sortino Ratio">
                <span className="text-2xl font-bold text-white">{backtestData.kpis?.sortino}</span>
            </GlassCard>
            <GlassCard text="Calmar Ratio">
                <span className="text-2xl font-bold text-white">{backtestData.kpis?.calmar}</span>
            </GlassCard>
            <GlassCard text="Profit Factor">
                <span className="text-2xl font-bold text-emerald-400">{backtestData.kpis?.profitFactor}</span>
            </GlassCard>
            <GlassCard text="Recovery Factor">
                <span className="text-2xl font-bold text-white">{backtestData.kpis?.recoveryFactor}</span>
            </GlassCard>

            {/* Ligne 3 : Statistiques Trade par Trade */}
            <GlassCard text="Win Rate">
                <span className="text-2xl font-bold text-white">{backtestData.kpis?.winRate}</span>
            </GlassCard>
            <GlassCard text="Reward / Risk">
                <span className="text-2xl font-bold text-white">{backtestData.kpis?.rewardRisk}</span>
            </GlassCard>
            <GlassCard text="Max Cons. Wins">
                <span className="text-2xl font-bold text-emerald-400">{backtestData.kpis?.maxConsWins}</span>
            </GlassCard>
            <GlassCard text="Max Cons. Losses">
                <span className="text-2xl font-bold text-rose-400">{backtestData.kpis?.maxConsLosses}</span>
            </GlassCard>
          </div>

          {backtestData.modelMetrics && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5 items-stretch">
              <GlassCard text="Accuracy">
                <div className="flex items-baseline gap-2 pt-1">
                  <span className="text-2xl font-bold text-white">{backtestData.modelMetrics?.accuracy}</span>
                </div>
              </GlassCard>
              <GlassCard text="Precision">
                <div className="flex items-baseline gap-2 pt-1">
                  <span className="text-2xl font-bold text-white">{backtestData.modelMetrics?.precision}</span>
                </div>
              </GlassCard>
              <GlassCard text="Recall">
                <div className="flex items-baseline gap-2 pt-1">
                  <span className="text-2xl font-bold text-white">{backtestData.modelMetrics?.recall}</span>
                </div>
              </GlassCard>
              <GlassCard text="F1 Score">
                <div className="flex items-baseline gap-2 pt-1">
                  <span className="text-2xl font-bold text-white">{backtestData.modelMetrics?.f1}</span>
                </div>
              </GlassCard>
              <GlassCard text="AUC">
                <div className="flex items-baseline gap-2 pt-1">
                  <span className="text-2xl font-bold text-white">
                    {backtestData.modelMetrics?.auc !== null && backtestData.modelMetrics?.auc !== undefined
                      ? backtestData.modelMetrics.auc
                      : "N/A"}
                  </span>
                </div>
              </GlassCard>
            </div>
          )}

          <div className="grid grid-cols-1 gap-5">
            <GlassCard text="Equity Curve (Strategy vs Benchmark)">
              <div className="w-full h-[400px] pt-4 pb-2 mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={backtestData.equityCurve}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                    <YAxis domain={['auto', 'auto']} stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} dx={-10} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#16161A', color: '#f8fafc', border: '1px solid #ffffff10', borderRadius: '12px' }}
                      itemStyle={{ color: '#f8fafc' }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
                    <Line type="monotone" dataKey="Strategie" stroke="#8B5CF6" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="Benchmark" stroke="#475569" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>
          </div>
          
        </div>
      )}
    </div>
  );
}