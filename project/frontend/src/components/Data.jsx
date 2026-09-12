import React, { useState, useEffect, useMemo } from "react";
import { GlassCard } from "./utils";
import { API_BASE_URL } from "../config";

// ------------------------------------------------------------------
// Mini graphique en ligne, en SVG pur (remplace recharts LineChart)
// ------------------------------------------------------------------
function MiniLineChart({ data, dataKey = "price", color = "#a855f7" }) {
    const [hover, setHover] = useState(null);
    const width = 600;
    const height = 260;
    const padding = 30;

    const { points, minVal, maxVal } = useMemo(() => {
        if (!data || data.length === 0) return { points: [], minVal: 0, maxVal: 0 };
        const values = data.map((d) => d[dataKey]);
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);
        const range = maxVal - minVal || 1;

        const points = data.map((d, i) => {
            const x = padding + (i / (data.length - 1 || 1)) * (width - padding * 2);
            const y = height - padding - ((d[dataKey] - minVal) / range) * (height - padding * 2);
            return { x, y, raw: d };
        });
        return { points, minVal, maxVal };
    }, [data, dataKey]);

    if (points.length === 0) {
        return <div className="flex items-center justify-center h-full text-gray-500">Loading chart...</div>;
    }

    const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

    const handleMove = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const relX = ((e.clientX - rect.left) / rect.width) * width;
        let closest = points[0];
        let minDist = Infinity;
        for (const p of points) {
            const dist = Math.abs(p.x - relX);
            if (dist < minDist) {
                minDist = dist;
                closest = p;
            }
        }
        setHover(closest);
    };

    return (
        <div className="relative w-full h-full">
            <svg
                viewBox={`0 0 ${width} ${height}`}
                className="w-full h-full"
                onMouseMove={handleMove}
                onMouseLeave={() => setHover(null)}
            >
                {/* Grille horizontale */}
                {[0.25, 0.5, 0.75].map((f) => (
                    <line
                        key={f}
                        x1={padding}
                        x2={width - padding}
                        y1={padding + f * (height - padding * 2)}
                        y2={padding + f * (height - padding * 2)}
                        stroke="#ffffff10"
                    />
                ))}

                {/* Ligne principale */}
                <path d={pathD} fill="none" stroke={color} strokeWidth="2" />

                {/* Repère au survol */}
                {hover && (
                    <>
                        <line x1={hover.x} x2={hover.x} y1={padding} y2={height - padding} stroke="#ffffff20" />
                        <circle cx={hover.x} cy={hover.y} r="4" fill={color} />
                    </>
                )}

                {/* Labels min/max */}
                <text x={padding} y={padding - 8} fill="#9ca3af" fontSize="10">
                    {maxVal.toFixed(2)}
                </text>
                <text x={padding} y={height - padding + 14} fill="#9ca3af" fontSize="10">
                    {minVal.toFixed(2)}
                </text>
                <text x={padding} y={height - 4} fill="#9ca3af" fontSize="10">
                    {points[0].raw.date}
                </text>
                <text x={width - padding - 60} y={height - 4} fill="#9ca3af" fontSize="10">
                    {points[points.length - 1].raw.date}
                </text>
            </svg>

            {hover && (
                <div
                    className="absolute bg-[#16161A] border border-white/10 p-2 rounded-lg shadow-xl pointer-events-none text-xs"
                    style={{
                        left: `${(hover.x / width) * 100}%`,
                        top: `${(hover.y / height) * 100}%`,
                        transform: "translate(-50%, -120%)",
                    }}
                >
                    <p className="text-gray-400 mb-0.5">{hover.raw.date}</p>
                    <p className="text-white font-medium">
                        {dataKey}: <span style={{ color }}>{Number(hover.raw[dataKey]).toFixed(2)}</span>
                    </p>
                </div>
            )}
        </div>
    );
}

// ------------------------------------------------------------------
// Mini histogramme, en SVG pur (remplace recharts BarChart)
// ------------------------------------------------------------------
function MiniBarChart({ data, dataKey = "daily_return", color = "#34d399", negColor = "#fb7185" }) {
    const [hoverIdx, setHoverIdx] = useState(null);
    const width = 600;
    const height = 260;
    const padding = 30;

    const { bars, maxAbs } = useMemo(() => {
        if (!data || data.length === 0) return { bars: [], maxAbs: 1 };
        const maxAbs = Math.max(...data.map((d) => Math.abs(d[dataKey]))) || 1;
        const barWidth = (width - padding * 2) / data.length;
        const zeroY = height / 2;

        const bars = data.map((d, i) => {
            const x = padding + i * barWidth;
            const barHeight = (Math.abs(d[dataKey]) / maxAbs) * (height / 2 - padding / 2);
            const y = d[dataKey] >= 0 ? zeroY - barHeight : zeroY;
            return { x, y, width: Math.max(barWidth - 2, 1), height: barHeight, raw: d };
        });
        return { bars, maxAbs };
    }, [data, dataKey]);

    if (bars.length === 0) {
        return <div className="flex items-center justify-center h-full text-gray-500">Loading chart...</div>;
    }

    const zeroY = height / 2;

    return (
        <div className="relative w-full h-full">
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
                <line x1={padding} x2={width - padding} y1={zeroY} y2={zeroY} stroke="#ffffff20" />
                {bars.map((b, i) => (
                    <rect
                        key={i}
                        x={b.x}
                        y={b.y}
                        width={b.width}
                        height={b.height}
                        fill={b.raw[dataKey] >= 0 ? color : negColor}
                        rx="1"
                        onMouseEnter={() => setHoverIdx(i)}
                        onMouseLeave={() => setHoverIdx(null)}
                    />
                ))}
                <text x={padding} y={height - 4} fill="#9ca3af" fontSize="10">
                    {bars[0].raw.date}
                </text>
                <text x={width - padding - 60} y={height - 4} fill="#9ca3af" fontSize="10">
                    {bars[bars.length - 1].raw.date}
                </text>
            </svg>

            {hoverIdx !== null && (
                <div
                    className="absolute bg-[#16161A] border border-white/10 p-2 rounded-lg shadow-xl pointer-events-none text-xs"
                    style={{
                        left: `${(bars[hoverIdx].x / width) * 100}%`,
                        top: "10%",
                        transform: "translate(-50%, 0)",
                    }}
                >
                    <p className="text-gray-400 mb-0.5">{bars[hoverIdx].raw.date}</p>
                    <p className="text-white font-medium">
                        {dataKey}:{" "}
                        <span style={{ color: bars[hoverIdx].raw[dataKey] >= 0 ? color : negColor }}>
                            {Number(bars[hoverIdx].raw[dataKey]).toFixed(2)}%
                        </span>
                    </p>
                </div>
            )}
        </div>
    );
}

export default function Data() {
    const inputStyle = "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm outline-none focus:border-purple-500/50 focus:bg-white/10 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300 placeholder:text-gray-500";

    const [ticker, setTicker] = useState("XAUUSD");
    const [timeframe, setTimeframe] = useState("1d");
    const [source, setSource] = useState("mt5"); // NOUVEAU STATE
    const [startDate, setStartDate] = useState("2025-01-01");
    const [endDate, setEndDate] = useState("2026-07-01");

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null); // STATE POUR LES ERREURS

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/api/data-analysis?ticker=${ticker}&start_date=${startDate}&end_date=${endDate}&timeframe=${timeframe}&source=${source}`);
            const result = await response.json();
            
            if (result.error) {
                setError(result.error);
                setData(null);
            } else {
                setData(result);
            }
        } catch (error) {
            console.error("Erreur lors de la récupération des données backend :", error);
            setError("Erreur de connexion au serveur.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <div className="flex flex-col gap-6 p-6 w-full max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex flex-col gap-1 mb-2">
                <h1 className="text-2xl font-semibold text-white">Data Configuration & Backend Sync</h1>
                <p className="text-sm text-gray-400">Connected to Python pipeline for {ticker}.</p>
            </div>

            {/* LIGNE 1 : Inputs dynamiques */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5 items-stretch">
                <GlassCard text="Source" isActive={true}>
                    <div className="pt-2 relative">
                        <select value={source} onChange={(e) => setSource(e.target.value)} className={`${inputStyle} appearance-none cursor-pointer bg-[#16161A]`}>
                            <option value="mt5" className="bg-[#16161A]">MetaTrader 5</option>
                            <option value="yahoo" className="bg-[#16161A]">Yahoo Finance</option>
                        </select>
                    </div>
                </GlassCard>
                <GlassCard text="Ticker">
                    <div className="pt-2">
                        <input type="text" value={ticker} onChange={(e) => setTicker(e.target.value)} placeholder="Ex: XAUUSD" className={inputStyle} />
                    </div>
                </GlassCard>
                <GlassCard text="Timeframe">
                    <div className="pt-2 relative">
                        <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} className={`${inputStyle} appearance-none cursor-pointer bg-[#16161A]`}>
                            <option value="15m" className="bg-[#16161A]">15 Minutes</option>
                            <option value="1h" className="bg-[#16161A]">1 Heure</option>
                            <option value="1d" className="bg-[#16161A]">1 Jour</option>
                        </select>
                    </div>
                </GlassCard>
                <GlassCard text="Start date">
                    <div className="pt-2">
                        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className={`${inputStyle} [color-scheme:dark] cursor-pointer`} />
                    </div>
                </GlassCard>
                <GlassCard text="End date">
                    <div className="pt-2 flex gap-2 items-center">
                        {/* On remplace w-full par flex-1 min-w-0 pour éviter le débordement */}
                        <input 
                            type="date" 
                            value={endDate} 
                            onChange={(e) => setEndDate(e.target.value)} 
                            className={`${inputStyle.replace('w-full', 'flex-1 min-w-0')} [color-scheme:dark] cursor-pointer`} 
                        />
                        
                        <button 
                            onClick={fetchData} 
                            className="px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-medium transition-all whitespace-nowrap flex-shrink-0"
                        >
                            {loading ? "..." : "Load"}
                        </button>
                        
                        {/* Le bouton de téléchargement apparaît si l'URL est disponible */}
                        {data?.downloadUrl && (
                            <a 
                                href={data.downloadUrl} 
                                download={`${ticker}_dataset.csv`} 
                                className="px-3 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl flex items-center justify-center transition-all flex-shrink-0"
                                title="Download Full Dataset"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                                </svg>
                            </a>
                        )}
                    </div>
                </GlassCard>
            </div>

            {/* Affichage des erreurs */}
            {error && (
                <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-4 text-rose-400 text-sm">
                    {error}
                </div>
            )}

            {/* LIGNE 2 : Statistiques Principales */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-5 items-stretch">
                <GlassCard text="Return">
                    <div className="flex items-baseline gap-2 pt-1">
                        <span className={`text-2xl font-bold ${data?.return >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {data ? `${data.return > 0 ? "+" : ""}${data.return}%` : "..."}
                        </span>
                    </div>
                </GlassCard>
                <GlassCard text="Ann. Volatility">
                    <div className="flex items-baseline gap-2 pt-1">
                        <span className="text-2xl font-bold text-rose-400">{data ? `${data.volatility}%` : "..."}</span>
                    </div>
                </GlassCard>
                <GlassCard text="Sharpe Ratio">
                    <div className="flex items-baseline gap-2 pt-1">
                        <span className="text-2xl font-bold text-blue-400">{data ? data.sharpe_ratio : "..."}</span>
                        <span className="text-xs text-blue-500 bg-blue-500/10 px-2 py-0.5 rounded-full">Risk/Reward</span>
                    </div>
                </GlassCard>
                <GlassCard text="Max Drawdown">
                    <div className="flex items-baseline gap-2 pt-1">
                        <span className="text-2xl font-bold text-rose-500">{data ? `${data.max_drawdown}%` : "..."}</span>
                    </div>
                </GlassCard>
                <GlassCard text="Value at Risk (95%)">
                    <div className="flex items-baseline gap-2 pt-1">
                        <span className="text-2xl font-bold text-orange-400">{data ? `${data.var_95}%` : "..."}</span>
                    </div>
                </GlassCard>
            </div>

            {/* LIGNE 3 : Graphiques (SVG maison, sans recharts) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-stretch h-[350px]">
                <GlassCard text="Price Evolution">
                    <div className="h-full w-full pt-4 pb-8 pr-4">
                        <MiniLineChart data={data?.timeseries} dataKey="price" color="#a855f7" />
                    </div>
                </GlassCard>

                <GlassCard text="Daily Returns Distribution">
                    <div className="h-full w-full pt-4 pb-8 pr-4">
                        <MiniBarChart
                            data={data?.timeseries ? data.timeseries.slice(-50) : null}
                            dataKey="daily_return"
                            color="#34d399"
                            negColor="#fb7185"
                        />
                    </div>
                </GlassCard>
            </div>

            {/* LIGNE 4 : Métriques statistiques & Matrice de corrélation */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
                <div className="lg:col-span-3 flex flex-col gap-5">
                    <GlassCard text="Skewness">
                        <div className="pt-2 text-xl font-semibold text-white">{data ? data.skewness : "..."}</div>
                    </GlassCard>
                    <GlassCard text="Kurtosis">
                        <div className="pt-2 text-xl font-semibold text-white">{data ? data.kurtosis : "..."}</div>
                    </GlassCard>
                    <GlassCard text="ADF Test (Stationarity)">
                        <div className="pt-2 text-xl font-semibold text-emerald-400">{data ? data.adf_status : "..."}</div>
                    </GlassCard>
                    <GlassCard text="Observations">
                        <div className="pt-2 text-xl font-semibold text-white">{data ? data.observations.toLocaleString() : "..."} jours</div>
                    </GlassCard>
                </div>

                <div className="lg:col-span-9 flex">
                    <div className="w-full h-full min-h-[300px]">
                        <GlassCard text="Correlation Matrix">
                            <div className="p-4 text-xs overflow-auto max-h-[350px] custom-scrollbar">
                                {data && data.correlation_matrix ? (
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr>
                                                <th className="p-2 border-b border-white/10 text-gray-400 font-medium">Features</th>
                                                {Object.keys(data.correlation_matrix).map((col) => (
                                                    <th key={col} className="p-2 border-b border-white/10 text-gray-400 font-medium">{col}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {Object.entries(data.correlation_matrix).map(([rowKey, rowValues]) => (
                                                <tr key={rowKey} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                                    <td className="p-2 font-medium text-gray-300">{rowKey}</td>
                                                    {Object.values(rowValues).map((val, idx) => {
                                                        let colorClass = "text-gray-400";
                                                        if (val >= 0.7 && val < 1) colorClass = "text-emerald-400 font-semibold";
                                                        if (val <= -0.7) colorClass = "text-rose-400 font-semibold";
                                                        if (val === 1) colorClass = "text-gray-600";

                                                        return (
                                                            <td key={idx} className={`p-2 ${colorClass}`}>
                                                                {Number(val).toFixed(2)}
                                                            </td>
                                                        );
                                                    })}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                ) : (
                                    <div className="flex items-center justify-center h-full text-gray-500">
                                        Loading matrix...
                                    </div>
                                )}
                            </div>
                        </GlassCard>
                    </div>
                </div>
            </div>
        </div>
    );
}