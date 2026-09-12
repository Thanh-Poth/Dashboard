// CORRECTION : les composants utilisaient un mélange incohérent de
// "http://127.0.0.1:8000" (Alpha.jsx) et "http://localhost:8000"
// (Data.jsx, Backtest.jsx, Optimization.jsx). Ça fonctionnait quand même
// grâce à allow_origins=["*"] côté FastAPI, mais mieux vaut une seule
// source de vérité pour l'URL du backend.
export const API_BASE_URL = "http://localhost:8000";
