import React, { useState } from "react";
import { GlassCard } from "./utils";
import { API_BASE_URL } from "../config";

export default function Alpha() {
    const [file, setFile] = useState(null);
    const [nAlphas, setNAlphas] = useState(1000);
    const [alphasToKeep, setAlphasToKeep] = useState(50);
    const [maxCorrelation, setMaxCorrelation] = useState(0.85);
    
    const [isProcessing, setIsProcessing] = useState(false);
    const [results, setResults] = useState(null); 
    const [error, setError] = useState(null);

    const inputStyle = "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm outline-none focus:border-purple-500/50 focus:bg-white/10 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300 placeholder:text-gray-500";

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
        }
    };

    const pollStatus = async (jobId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/status/${jobId}`);
            if (!response.ok) throw new Error("Erreur réseau");
            
            const data = await response.json();
            
            if (data.status === "completed") {
                setResults(data.result);
                setIsProcessing(false);
            } else if (data.status === "failed") {
                setError(data.error || "L'enrichissement a échoué côté serveur.");
                setIsProcessing(false);
            } else {
                // Si 'processing' ou 'pending', on re-tente dans 2 secondes
                setTimeout(() => pollStatus(jobId), 2000);
            }
        } catch (err) {
            console.error("Erreur de polling:", err);
            setError("Perte de connexion avec le serveur lors de la vérification du statut.");
            setIsProcessing(false);
        }
    };

    const processDataset = async () => {
        if (!file) {
            alert("Veuillez sélectionner un dataset (CSV) d'abord.");
            return;
        }

        setIsProcessing(true);
        setResults(null);
        setError(null);

        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("n_alphas", nAlphas);
            formData.append("alphas_to_keep", alphasToKeep);
            formData.append("max_correlation", maxCorrelation);

            const response = await fetch(`${API_BASE_URL}/api/enrich-dataset`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error(`Erreur serveur (${response.status})`);
            
            const data = await response.json();

            if (data.error) {
                setError(data.error);
                setIsProcessing(false);
            } else if (data.job_id) {
                pollStatus(data.job_id);
            } else {
                setError("Format de réponse inattendu du serveur.");
                setIsProcessing(false);
            }
        } catch (error) {
            console.error("Erreur d'initialisation:", error);
            setError("Impossible de contacter le serveur pour lancer la tâche.");
            setIsProcessing(false);
        }
    };

    // Le reste du return() reste strictement identique à l'original...
    return (
        <div className="flex flex-col gap-6 p-6 w-full max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex flex-col gap-1 mb-2">
                <h1 className="text-2xl font-semibold text-white">Dataset Alpha Enrichment</h1>
                <p className="text-sm text-gray-400">Upload your raw market data, generate thousands of alphas, filter the noise and download the enriched dataset.</p>
            </div>

            {/* LIGNE 1 : Configuration et Upload */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-5 items-stretch">
                <GlassCard text="Raw Dataset (CSV)" isActive={true}>
                    <div className="pt-2">
                        <input 
                            type="file" 
                            accept=".csv"
                            onChange={handleFileChange}
                            className="block w-full text-sm text-gray-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-white/10 file:text-white hover:file:bg-white/20 transition-all cursor-pointer"
                        />
                    </div>
                </GlassCard>
                
                <GlassCard text="Alphas to Generate">
                    <div className="pt-2 relative">
                        <input type="number" min="10" max="10000" step="100" value={nAlphas} onChange={(e) => setNAlphas(parseInt(e.target.value))} className={inputStyle} />
                    </div>
                </GlassCard>                
                
                <GlassCard text="Alphas to Keep">
                    <div className="pt-2">
                        <input type="number" min="1" max="1000" step="1" value={alphasToKeep} onChange={(e) => setAlphasToKeep(parseInt(e.target.value))} className={inputStyle} />
                    </div>
                </GlassCard>            

                <GlassCard text="Max Correlation">
                    <div className="pt-2">
                        <input type="number" min="0" max="1" step="0.01" value={maxCorrelation} onChange={(e) => setMaxCorrelation(parseFloat(e.target.value))} className={inputStyle} />
                    </div>
                </GlassCard>

                <GlassCard text="Action">
                    <div className="pt-2">
                        <button onClick={processDataset} disabled={isProcessing || !file} className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-xl px-4 py-2.5 transition-colors disabled:opacity-50 shadow-[0_0_15px_rgba(147,51,234,0.3)] flex items-center justify-center gap-2">
                            {isProcessing ? (
                                <>
                                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                    Crunching...
                                </>
                            ) : "Enrich Dataset"}
                        </button>
                    </div>
                </GlassCard>
            </div>

            <hr className="border-white/10 my-4" />

            {error && <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-4 text-rose-400 text-sm">{error}</div>}

            {results && (
                <div className="flex flex-col gap-6 animate-fade-in">
                    <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-6">
                        <div>
                            <h2 className="text-emerald-400 text-xl font-bold mb-1">Enrichment Complete !</h2>
                            <p className="text-gray-300 text-sm">Generated <strong>{results.totalGenerated}</strong> alphas. Kept the top <strong>{results.keptAfterFilter}</strong> uncorrelated alphas.</p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-3">
                            <a href={results.downloadUrl} download="enriched_dataset.csv" className="bg-emerald-500 hover:bg-emerald-600 text-white px-5 py-3 rounded-xl font-medium transition-colors shadow-[0_0_15px_rgba(16,185,129,0.4)] flex items-center gap-2 text-sm">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg> Dataset
                            </a>
                            <a href={results.formulasDownloadUrl} download="alphas_formulas.csv" className="bg-purple-500 hover:bg-purple-600 text-white px-5 py-3 rounded-xl font-medium transition-colors shadow-[0_0_15px_rgba(168,85,247,0.4)] flex items-center gap-2 text-sm">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg> Formulas
                            </a>
                        </div>
                    </div>

                    <GlassCard text="Preview : Top Alphas Discovered">
                        <div className="pt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                            {results.topAlphas.map((alpha) => (
                                <div key={alpha.id} className="bg-white/5 border border-white/10 p-4 rounded-xl flex flex-col gap-3">                                    
                                    <div className="bg-[#0D0D12] border border-white/5 rounded-md p-2 overflow-x-auto">
                                        <code className="text-blue-300 text-xs whitespace-nowrap">{alpha.formula}</code>
                                    </div>
                                    <div>
                                        <p className="text-gray-500 text-xs">Backtested Return</p>
                                        <p className="text-emerald-400 font-semibold">+{alpha.return}%</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </GlassCard>
                </div>
            )}
            
            {isProcessing && !results && (
                <div className="flex flex-col items-center justify-center py-20 text-gray-400 gap-4">
                    <svg className="animate-spin h-10 w-10 text-purple-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    <p className="text-sm">Applying {nAlphas} alpha formulas to your dataset...</p>
                </div>
            )}
        </div>
    );
}