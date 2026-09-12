import React, { useState } from 'react';
import { GlassCard } from "./utils";
import {
  LineChart, Line, ScatterChart, Scatter, BarChart, Bar,
  XAxis, YAxis, ZAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer
} from 'recharts';
import { API_BASE_URL } from "../config";

export default function Optimization() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const [file, setFile] = useState(null);
  const [modelType, setModelType] = useState("random_forest");
  const [scoring, setScoring] = useState("accuracy");

  const inputStyle = "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm outline-none focus:border-purple-500/50 focus:bg-white/10 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300 appearance-none cursor-pointer";
  const fileInputStyle = "w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-500/10 file:text-purple-400 hover:file:bg-purple-500/20 file:cursor-pointer cursor-pointer focus:outline-none";

  const pollOptimizationStatus = async (jobId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/status/${jobId}`);
      if (!response.ok) throw new Error("Erreur réseau");

      const data = await response.json();

      if (data.status === "completed") {
        setResult(data.result);
        setLoading(false);
      } else if (data.status === "failed") {
        setError(data.error || "L'optimisation du modèle a échoué.");
        setLoading(false);
      } else {
        setTimeout(() => pollOptimizationStatus(jobId), 2000);
      }
    } catch (err) {
      console.error("Erreur de polling:", err);
      setError("Perte de connexion avec le serveur.");
      setLoading(false);
    }
  };

  const runOptimization = async () => {
    if (!file) {
      alert("Veuillez sélectionner un fichier dataset (CSV) !");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("model_type", modelType);
      formData.append("scoring", scoring);

      const response = await fetch(`${API_BASE_URL}/api/optimize-model`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      
      if (data.error) {
        setError(data.error);
        setLoading(false);
      } else if (data.job_id) {
        pollOptimizationStatus(data.job_id);
      } else {
        setError("Format de réponse inattendu.");
        setLoading(false);
      }
    } catch (err) {
      console.error("Erreur Backend :", err);
      setError("Impossible de contacter le serveur d'optimisation.");
      setLoading(false);
    }
  };

  const copyRunId = (runId) => {
    if (!runId) return;
    navigator.clipboard.writeText(runId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const scoringLabel = {
    accuracy: "Accuracy", f1: "F1-Score", precision: "Precision",
    recall: "Recall", roc_auc: "ROC-AUC"
  }[scoring] || scoring;

  const paramImportanceData = result
    ? Object.entries(result.paramImportance || {}).map(([name, value]) => ({ name, importance: value }))
        .sort((a, b) => b.importance - a.importance)
    : [];

  const cm = result?.confusionMatrix;

  return (
    <div className="flex flex-col gap-6 p-6 w-full max-w-7xl mx-auto">
      {/* LIGNE 1 : Inputs de configuration */}
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-2xl font-semibold text-white">Model Optimization</h1>
        <p className="text-sm text-gray-400">Tune hyperparameters and evaluate model performance.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 items-stretch">
        <GlassCard text="Dataset (CSV)" isActive={true}>
          <div className="pt-2 flex flex-col gap-1 h-full">
            <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0])} className={fileInputStyle} />
            {file && <span className="text-xs text-gray-500 truncate">{file.name}</span>}
          </div>
        </GlassCard>

        <GlassCard text="Modèle">
          <div className="pt-2 relative">
            <select value={modelType} onChange={(e) => setModelType(e.target.value)} className={`${inputStyle} bg-[#16161A]`}>
              <option value="random_forest" className="bg-[#16161A]">Random Forest</option>
              <option value="lgbm" className="bg-[#16161A]">LightGBM</option>
              <option value="svm" className="bg-[#16161A]">SVM</option>
            </select>
          </div>
        </GlassCard>

        <GlassCard text="Métrique cible">
          <div className="pt-2 relative">
            <select value={scoring} onChange={(e) => setScoring(e.target.value)} className={`${inputStyle} bg-[#16161A]`}>
              <option value="accuracy" className="bg-[#16161A]">Accuracy</option>
              <option value="f1" className="bg-[#16161A]">F1-Score</option>
              <option value="precision" className="bg-[#16161A]">Precision</option>
              <option value="recall" className="bg-[#16161A]">Recall</option>
              <option value="roc_auc" className="bg-[#16161A]">ROC-AUC</option>
            </select>
          </div>
        </GlassCard>
      </div>

      {/* BOUTON DE LANCEMENT */}
      <div className="flex items-center gap-4">
        <button 
          onClick={runOptimization} 
          disabled={loading} 
          className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium py-2.5 px-8 rounded-xl shadow-lg shadow-purple-500/20 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-0.5 active:translate-y-0"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              Optimizing & Tracking...
            </span>
          ) : 'Run Optimization'}
        </button>
        {error && <span className="text-sm text-rose-400">{error}</span>}
      </div>

      {result && (
        <div className="flex flex-col gap-5 animate-in fade-in duration-700">
          {/* LIGNE 2 : KPIs d'amélioration */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 items-stretch">
            <GlassCard text={`Score Défaut (Baseline) — ${scoringLabel}`}>
              <div className="flex items-baseline gap-2 pt-1">
                <span className="text-3xl font-bold text-gray-300">{result.baselineScore ?? "N/A"}</span>
              </div>
            </GlassCard>

            <GlassCard text={`Score Optimisé (Test set) — ${scoringLabel}`}>
              <div className="flex items-baseline gap-2 pt-1">
                <span className="text-3xl font-bold text-emerald-400">{result.testScore ?? "N/A"}</span>
                <span className="text-xs text-gray-500">CV: {result.bestCvScore}</span>
              </div>
            </GlassCard>

            <GlassCard text="Amélioration Relative">
              <div className="flex items-baseline gap-2 pt-1">
                <span className="text-3xl font-bold text-purple-400">
                  {result.relativeImprovement !== null ? `${result.relativeImprovement > 0 ? '+' : ''}${result.relativeImprovement}%` : "N/A"}
                </span>
                <span className="text-xs text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-full">vs baseline</span>
              </div>
            </GlassCard>
          </div>

          {/* LIGNE 3 : Graphiques principaux */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-stretch min-h-[400px]">
            <div className="lg:col-span-2">
              <GlassCard text="Courbes d'apprentissage (Train vs Validation)">
                <div className="w-full h-[350px] pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={result.learningCurve}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                      <XAxis dataKey="trainSize" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} label={{ value: "Taille du train set", position: "insideBottom", offset: -5, fill: "#64748b", fontSize: 11 }} />
                      <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#16161A', color: '#f8fafc', border: '1px solid #ffffff10', borderRadius: '12px' }} />
                      <Legend iconType="circle" />
                      <Line type="monotone" dataKey="trainScore" name="Train" stroke="#8B5CF6" strokeWidth={3} dot={false} />
                      <Line type="monotone" dataKey="validationScore" name="Validation" stroke="#475569" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            </div>
            <div className="lg:col-span-1">
              <GlassCard text="Historique d'optimisation">
                <div className="w-full h-[350px] pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                      <XAxis dataKey="trial" name="Essai" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis dataKey="score" name="Score" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                      <ZAxis range={[40, 40]} />
                      <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#16161A', color: '#f8fafc', border: '1px solid #ffffff10', borderRadius: '12px' }} />
                      <Scatter data={result.optimizationHistory} fill="#8B5CF6" />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            </div>
          </div>

          {/* LIGNE 4 : Analyse détaillée & Tracking */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
            <div className="lg:col-span-3 flex flex-col gap-5">
              <GlassCard text="Meilleurs Hyperparamètres">
                <div className="text-sm text-gray-400 mt-2 space-y-3">
                  {Object.entries(result.bestParams || {}).map(([key, value], i, arr) => (
                    <div key={key} className={`flex justify-between ${i < arr.length - 1 ? 'border-b border-white/5 pb-2' : 'pb-1'}`}>
                      <span>{key}</span>
                      <span className="font-mono text-purple-400">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </GlassCard>

              <div className="grid grid-cols-2 gap-5">
                <GlassCard text="Temps total">
                  <div className="pt-2 text-lg font-semibold text-white">{result.trainingTimeSeconds}s</div>
                </GlassCard>
                <GlassCard text="Trials">
                  <div className="pt-2 text-lg font-semibold text-white">{result.nTrials}</div>
                </GlassCard>
              </div>

              {/* CARTE MLFLOW TRACKING */}
              {result.mlflow && (
                <GlassCard text="MLflow Run Tracker">
                  <div className="flex flex-col gap-3 pt-2">
                    <div>
                      <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                        <span>Run ID</span>
                        <button 
                          onClick={() => copyRunId(result.mlflow.runId)}
                          className="text-purple-400 hover:text-purple-300 text-[11px] underline cursor-pointer"
                        >
                          {copied ? 'Copié !' : 'Copier'}
                        </button>
                      </div>
                      <div className="font-mono text-xs text-slate-300 bg-white/5 px-2.5 py-1.5 rounded-lg border border-white/5 truncate select-all">
                        {result.mlflow.runId}
                      </div>
                    </div>

                    <a
                      href={result.mlflow.trackingUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-1.5 w-full py-2 px-3 rounded-xl bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-300 hover:text-purple-200 text-xs font-semibold tracking-wide transition-all duration-200"
                    >
                      Inspecter le run dans MLflow ↗
                    </a>
                  </div>
                </GlassCard>
              )}

              <a 
                href={result.downloadUrl} 
                className="text-center bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium py-2.5 px-4 rounded-xl transition-all duration-300"
              >
                Télécharger le modèle (.joblib)
              </a>
            </div>

            <div className="lg:col-span-4 flex">
              <div className="w-full h-full min-h-[300px]">
                <GlassCard text="Importance des Hyperparamètres">
                  <div className="w-full h-[280px] mt-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={paramImportanceData} layout="vertical" margin={{ left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={false} />
                        <XAxis type="number" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} unit="%" />
                        <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} width={90} />
                        <Tooltip contentStyle={{ backgroundColor: '#16161A', color: '#f8fafc', border: '1px solid #ffffff10', borderRadius: '12px' }} />
                        <Bar dataKey="importance" fill="#8B5CF6" radius={[0, 6, 6, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Approximation basée sur l'écart de score par valeur de paramètre (GridSearchCV), pas une vraie importance Optuna.</p>
                </GlassCard>
              </div>
            </div>

            <div className="lg:col-span-5 flex">
              <div className="w-full h-full min-h-[300px]">
                <GlassCard text="Matrice de Confusion (Modèle Optimisé, test set)">
                  {cm && (
                    <div className="flex items-center justify-center h-full w-full mt-4">
                      <table className="text-center text-sm text-gray-300 border-separate" style={{ borderSpacing: '6px' }}>
                        <thead>
                          <tr>
                            <th></th>
                            <th className="text-xs text-gray-500 font-normal pb-1">Prédit: 0</th>
                            <th className="text-xs text-gray-500 font-normal pb-1">Prédit: 1</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="text-xs text-gray-500 pr-2">Réel: 0</td>
                            <td className="bg-emerald-500/20 rounded-lg px-6 py-4 font-bold text-emerald-400">{cm[0][0]}</td>
                            <td className="bg-rose-500/10 rounded-lg px-6 py-4 font-bold text-rose-400">{cm[0][1]}</td>
                          </tr>
                          <tr>
                            <td className="text-xs text-gray-500 pr-2">Réel: 1</td>
                            <td className="bg-rose-500/10 rounded-lg px-6 py-4 font-bold text-rose-400">{cm[1][0]}</td>
                            <td className="bg-emerald-500/20 rounded-lg px-6 py-4 font-bold text-emerald-400">{cm[1][1]}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  )}
                </GlassCard>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}