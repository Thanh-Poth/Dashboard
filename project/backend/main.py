from fastapi import FastAPI, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from scipy import stats
import polars as pl
import random
import tempfile
import os
import io
import time
import uuid
import joblib
import logging
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
import mlflow
import mlflow.sklearn

from features.alpha_primitive import ts_delay, ts_delta, ts_mean, ts_std, ts_max, ts_min, add, sub, mul, div
from data.collector import get_collector, MT5Collector
from features.features import Features
from features.alpha_generator import AlphaGenerator
from features.selection import FeatureSelector
from models.optimizer import ModelOptimizer
from models.classifiers import Classifiers
from config_loader import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ML-Backend")

config = load_config("config.yaml")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
MLFLOW_EXPERIMENT_NAME = "Trading_Model_Optimization"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

app = FastAPI()

MODEL_STORAGE_DIR = tempfile.gettempdir()

# Stockage en mémoire de l'état des jobs
# En production avec plusieurs workers Uvicorn, remplacer par Redis
JOB_STORE: dict[str, dict] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # À restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# ENDPOINT DE MONITORING DU STATUT (POLLING FRONTEND)
# =====================================================================
@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Interrogé périodiquement par React (Alpha.jsx / Optimization.jsx).
    Retourne :
      - {"status": "processing"}
      - {"status": "completed", "result": {...}}
      - {"status": "failed", "error": "..."}
    """
    job = JOB_STORE.get(job_id)
    if not job:
        return {"status": "failed", "error": "Tâche introuvable ou expirée."}
    return job


# =====================================================================
# TÂCHES DE FOND (WORKERS SYNCHRONES)
# =====================================================================
def run_enrich_dataset_task(
    job_id: str,
    tmp_path: str,
    n_alphas: int,
    alphas_to_keep: int,
    max_correlation: float
):
    try:
        logger.info(f"[{job_id}] Démarrage enrichissement dataset...")
        df = pl.read_csv(tmp_path)

        if "Close" not in df.columns or "Open" not in df.columns:
            JOB_STORE[job_id] = {
                "status": "failed",
                "error": "Le fichier doit au moins contenir 'Open' et 'Close'."
            }
            return

        # 1. Création de la colonne cible "OC" si absente
        if "OC" not in df.columns:
            df = df.with_columns(
                pl.when(pl.col("Open") - pl.col("Close") < 0)
                .then(1)
                .otherwise(0)
                .shift(-1)
                .alias("OC")
            )
            df = df.drop_nulls(subset=["OC"])

        # 2. Génération des alphas
        alpha_cfg = {**config.get("alpha", {}), "n_alphas": n_alphas}
        generator = AlphaGenerator(config=alpha_cfg)
        df_enriched = generator.generate_features(df)

        alpha_cols = [col for col in df_enriched.columns if col.startswith("alpha_")]
        # 3. Filtrage basé sur la corrélation maximale
        if len(alpha_cols) > 1:
            df_alphas_pd = df_enriched.select(alpha_cols).to_pandas()
            selection_cfg = {**config.get("selection", {}), "max_correlation": max_correlation}
            selector = FeatureSelector(config=selection_cfg)
            kept_cols = selector._filter_correlation(df_alphas_pd, alpha_cols)
        else:
            kept_cols = alpha_cols

        # 4. Tronquer pour garder le quota demandé
        kept_cols = kept_cols[:alphas_to_keep]
        kept_count = len(kept_cols)

        # 5. Aperçu UI
        top_alphas_preview = [
            {
                "id": col,
                "name": col.replace("_", " ").title(),
                "formula": generator.formulas.get(col, "unknown"),
                "sharpe": "-",
                "return": "-"
            }
            for col in kept_cols[:3]
        ]

        # 6. Dataset enrichi final
        cols_to_keep = [col for col in df.columns if col not in alpha_cols] + kept_cols
        df_final = df_enriched.select(cols_to_keep)

        output_path = tmp_path.replace(".csv", "_enriched.csv")
        df_final.write_csv(output_path)
        download_url = f"http://127.0.0.1:8000/api/download?file_path={output_path}"

        # 7. Dataset des formules
        formulas_data = [{"Alpha_Name": col, "Formula": generator.formulas.get(col, "unknown")} for col in kept_cols]
        df_formulas = pl.DataFrame(formulas_data)
        
        formulas_output_path = tmp_path.replace(".csv", "_formulas.csv")
        df_formulas.write_csv(formulas_output_path)
        formulas_download_url = f"http://127.0.0.1:8000/api/download?file_path={formulas_output_path}"

        JOB_STORE[job_id] = {
            "status": "completed",
            "result": {
                "downloadUrl": download_url,
                "formulasDownloadUrl": formulas_download_url,
                "totalGenerated": n_alphas,
                "keptAfterFilter": kept_count,
                "topAlphas": top_alphas_preview
            }
        }
        logger.info(f"[{job_id}] Enrichissement terminé avec succès.")

    except Exception as e:
        logger.exception(f"[{job_id}] Erreur lors de l'enrichissement : {e}")
        JOB_STORE[job_id] = {
            "status": "failed",
            "error": str(e)
        }


def run_optimize_model_task(
    job_id: str,
    file_bytes: bytes,
    model_type: str,
    scoring: str,
    target_col: str
):
    try:
        logger.info(f"[{job_id}] Démarrage optimisation modèle ({model_type})...")
        df_raw = pd.read_csv(io.BytesIO(file_bytes))
        features = Features(df_raw)
        features.add_features()
        df_clean = features.clean()

        if target_col not in df_clean.columns:
            JOB_STORE[job_id] = {
                "status": "failed",
                "error": f"La colonne cible '{target_col}' est absente après feature engineering."
            }
            return

        excluded_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        feature_cols = [c for c in df_clean.columns if c not in excluded_cols]
        df_model_input = df_clean[feature_cols]

        if len(df_model_input) < 30:
            JOB_STORE[job_id] = {
                "status": "failed",
                "error": "Pas assez de lignes exploitables après nettoyage pour entraîner un modèle."
            }
            return

        optimizer = ModelOptimizer(df_model_input, target_col=target_col)

        start_time = time.time()
        result = optimizer.optimize(model_type, scoring=scoring)
        elapsed_seconds = round(time.time() - start_time, 1)

        # Sauvegarde locale du modèle
        model_filename = f"model_{model_type}_{uuid.uuid4().hex[:8]}.joblib"
        model_path = os.path.join(MODEL_STORAGE_DIR, model_filename)
        joblib.dump(result["best_model"], model_path)
        download_url = f"http://127.0.0.1:8000/api/download-model?file_path={model_path}"

        baseline = result["baseline_score"]
        best = result["test_score"]
        relative_improvement = (
            round((best - baseline) / baseline * 100, 1)
            if baseline not in (None, 0) and best is not None else None
        )

        # -----------------------------------------------------------------
        # LOGGING MLFLOW
        # -----------------------------------------------------------------
        with mlflow.start_run(run_name=f"{model_type}_{job_id[:8]}") as run:
            # 1. Hyperparamètres & métadonnées du run
            mlflow.log_params({
                "model_type": model_type,
                "scoring_metric": scoring,
                "target_col": target_col,
                "n_trials": result["n_trials"],
                "n_features": len(feature_cols),
                "n_samples": len(df_model_input),
                **{f"param_{k}": v for k, v in result["best_params"].items()}
            })

            # 2. Métriques scalaires
            metrics_to_log = {
                "training_time_seconds": elapsed_seconds,
                "best_cv_score": result["best_cv_score"]
            }
            if baseline is not None:
                metrics_to_log["baseline_score"] = baseline
            if best is not None:
                metrics_to_log["test_score"] = best
            if relative_improvement is not None:
                metrics_to_log["relative_improvement"] = relative_improvement

            # Métriques issues du classification report
            report = result.get("report", {})
            if isinstance(report, dict):
                if "macro avg" in report:
                    metrics_to_log["macro_f1"] = report["macro avg"].get("f1-score", 0)
                if "weighted avg" in report:
                    metrics_to_log["weighted_f1"] = report["weighted avg"].get("f1-score", 0)
                if "accuracy" in report:
                    metrics_to_log["report_accuracy"] = report["accuracy"]

            mlflow.log_metrics(metrics_to_log)

            # 3. Courbe d'apprentissage loggée par step (visualisable en courbe dans l'UI)
            for point in result.get("learning_curve", []):
                step = point["trainSize"]
                mlflow.log_metric("lc_train_score", point["trainScore"], step=step)
                mlflow.log_metric("lc_val_score", point["validationScore"], step=step)

            # 4. Artefacts : Fichier joblib + log_model standard MLflow
            mlflow.log_artifact(model_path, artifact_path="joblib")
            mlflow.sklearn.log_model(result["best_model"], artifact_path="model")

            # 5. Tags utiles
            mlflow.set_tags({
                "job_id": job_id,
                "deployed_via": "fastapi_backend"
            })

            run_id = run.info.run_id
            experiment_id = run.info.experiment_id

        # -----------------------------------------------------------------
        # REPONSE FRONTEND
        # -----------------------------------------------------------------
        JOB_STORE[job_id] = {
            "status": "completed",
            "result": {
                "modelType": model_type,
                "scoringMetric": scoring,
                "downloadUrl": download_url,
                "baselineScore": baseline,
                "bestCvScore": result["best_cv_score"],
                "testScore": best,
                "relativeImprovement": relative_improvement,
                "bestParams": result["best_params"],
                "classificationReport": result["report"],
                "confusionMatrix": result["confusion_matrix"],
                "optimizationHistory": result["optimization_history"],
                "paramImportance": result["param_importance"],
                "learningCurve": result["learning_curve"],
                "nTrials": result["n_trials"],
                "trainingTimeSeconds": elapsed_seconds,
                # Identifiants MLflow pour React
                "mlflow": {
                    "runId": run_id,
                    "experimentId": experiment_id,
                    "trackingUrl": f"http://127.0.0.1:5000/#/experiments/{experiment_id}/runs/{run_id}"
                }
            }
        }
        logger.info(f"[{job_id}] Optimisation terminée et loggée dans MLflow (Run ID: {run_id}).")

    except Exception as e:
        logger.exception(f"[{job_id}] Erreur lors de l'optimisation : {e}")
        JOB_STORE[job_id] = {
            "status": "failed",
            "error": str(e)
        }


# =====================================================================
# ENDPOINTS API PRINCIPAUX
# =====================================================================
@app.get("/api/data-analysis")
def get_data_analysis(
    ticker: str = "XAUUSD", 
    start_date: str = "2025-01-01", 
    end_date: str = "2026-07-01",
    timeframe: str = "1d",
    source: str = "mt5"
):
    try:
        collector = get_collector(source, ticker, start_date=start_date, end_date=end_date)
        df = collector.collect_data()
    except ValueError as e:
        return {"error": str(e)}
        
    if df.empty:
        return {"error": f"Aucune donnée trouvée pour {ticker} via {source.upper()}."}
        
    df = df.reset_index()
    
    features = Features(df)
    features.add_features()

    dates_full = pd.to_datetime(features.df['Date']).copy()
    df = features.clean()
    dates_aligned = dates_full.loc[df.index]
    
    df.insert(0, 'Date', dates_aligned)

    returns = df['Close'].pct_change().dropna()
    total_return = (df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1
    ann_volatility = returns.std() * np.sqrt(252)
    
    skew = float(returns.skew())
    kurt = float(returns.kurtosis())
    
    adf_result = adfuller(df['Close'].dropna())
    is_stationary = adf_result[1] < 0.05
    
    jb_test = stats.jarque_bera(returns)
    corr_matrix = df.select_dtypes(include=[np.number]).corr().iloc[:10, :10].to_dict()

    sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
    cumulative_returns = (1 + returns).cumprod()
    peak = cumulative_returns.cummax()
    max_drawdown = ((cumulative_returns - peak) / peak).min() * 100
    var_95 = np.percentile(returns, 5) * 100

    df['Daily_Return'] = df['Close'].pct_change() * 100
    df['Date_Str'] = df['Date'].dt.strftime('%Y-%m-%d')

    df_timeseries = df.dropna(subset=['Close', 'Daily_Return'])
    timeseries_data = df_timeseries[['Date_Str', 'Close', 'Daily_Return']].rename(
        columns={'Date_Str': 'date', 'Close': 'price', 'Daily_Return': 'daily_return'}
    ).to_dict(orient='records')

    df_export = df.drop(columns=['Date_Str'])
    csv_filename = f"dataset_{ticker.replace('.', '_')}_{uuid.uuid4().hex[:8]}.csv"
    csv_path = os.path.join(tempfile.gettempdir(), csv_filename)
    df_export.to_csv(csv_path, index=False)
    download_url = f"http://127.0.0.1:8000/api/download?file_path={csv_path}"

    return {
        "ticker": ticker,
        "observations": len(df),
        "return": round(total_return * 100, 2),
        "volatility": round(ann_volatility * 100, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown": round(max_drawdown, 2),
        "var_95": round(var_95, 2),
        "skewness": round(skew, 2),
        "kurtosis": round(kurt, 2),
        "adf_status": "Stationary" if is_stationary else "Non-Stationary",
        "normality_p_value": round(jb_test.pvalue, 4),
        "correlation_matrix": corr_matrix,
        "timeseries": timeseries_data,
        "downloadUrl": download_url
    }


@app.post("/api/enrich-dataset")
async def enrich_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    n_alphas: int = Form(default=config.get("alpha", {}).get("n_alphas", 100)),
    alphas_to_keep: int = Form(default=config.get("selection", {}).get("top_k", 20)),
    max_correlation: float = Form(default=config.get("selection", {}).get("max_correlation", 0.85))
):
    """
    Lance l'enrichissement en tâche de fond et répond immédiatement avec un job_id.
    """
    try:
        # Sauvegarde immédiate du fichier sur disque avant la libération du stream HTTP
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        job_id = str(uuid.uuid4())
        JOB_STORE[job_id] = {"status": "processing"}

        # Exécution de la tâche en arrière-plan
        background_tasks.add_task(
            run_enrich_dataset_task,
            job_id,
            tmp_path,
            n_alphas,
            alphas_to_keep,
            max_correlation
        )

        return {"job_id": job_id}

    except Exception as e:
        logger.exception("Erreur lors de la soumission du job d'enrichissement")
        return {"error": str(e)}


@app.post("/api/optimize-model")
async def optimize_model(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model_type: str = Form(...),
    scoring: str = Form("accuracy"),
    target_col: str = Form("OC")
):
    """
    Lance l'optimisation en tâche de fond et répond immédiatement avec un job_id.
    """
    if model_type not in ModelOptimizer.MODEL_REGISTRY:
        return {"error": f"model_type doit être l'un de {list(ModelOptimizer.MODEL_REGISTRY.keys())}"}

    try:
        # Lecture immédiate du fichier en mémoire avant de fermer la requête HTTP
        file_bytes = await file.read()

        job_id = str(uuid.uuid4())
        JOB_STORE[job_id] = {"status": "processing"}

        # Exécution de la tâche en arrière-plan
        background_tasks.add_task(
            run_optimize_model_task,
            job_id,
            file_bytes,
            model_type,
            scoring,
            target_col
        )

        return {"job_id": job_id}

    except Exception as e:
        logger.exception("Erreur lors de la soumission du job d'optimisation")
        return {"error": str(e)}


@app.get("/api/download")
async def download_file(file_path: str):
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path, 
            filename=os.path.basename(file_path), 
            media_type='text/csv'
        )
    return {"error": "Fichier introuvable"}


@app.get("/api/download-model")
async def download_model(file_path: str):
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type='application/octet-stream'
        )
    return {"error": "Fichier modèle introuvable"}


@app.post("/api/run-backtest")
async def run_backtest(
    file: UploadFile = File(...),
    model_file: UploadFile = File(...),
    ticker: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    try:
        df_formulas = pd.read_csv(file.file)
        if "Alpha_Name" not in df_formulas.columns or "Formula" not in df_formulas.columns:
            return {"error": "Le fichier CSV doit contenir les colonnes 'Alpha_Name' et 'Formula'."}
        
        formulas_dict = dict(zip(df_formulas['Alpha_Name'], df_formulas['Formula']))

        start_dt = pd.to_datetime(start_date) - pd.Timedelta(days=150)
        collector = MT5Collector(ticker, start_date=start_dt.strftime('%Y-%m-%d'), end_date=end_date)
        df_raw = collector.collect_data()
        
        if df_raw.empty:
            return {"error": f"Aucune donnée trouvée pour {ticker} via MT5. Vérifiez que MetaTrader 5 est bien lancé et connecté."}

        df_raw = df_raw.reset_index()

        date_col = next((col for col in df_raw.columns if str(col).strip().lower() in ['date', 'time', 'index']), None)
        if date_col:
            df_raw['Date'] = pd.to_datetime(df_raw[date_col])
        else:
            df_raw['Date'] = pd.to_datetime(df_raw.iloc[:, 0])

        features = Features(df_raw)
        features.add_features()
        df_features = features.df
        
        if 'OC' not in df_features.columns:
            df_features['OC'] = np.where(df_features['Open'] - df_features['Close'] < 0, 1, 0)
            df_features['OC'] = df_features['OC'].shift(-1)
            
        allowed_names = {
            'ts_delay': ts_delay, 'ts_delta': ts_delta, 'ts_mean': ts_mean, 
            'ts_std': ts_std, 'ts_max': ts_max, 'ts_min': ts_min,
            'add': add, 'sub': sub, 'mul': mul, 'div': div,
            'Open': pl.col('Open'), 'High': pl.col('High'), 
            'Low': pl.col('Low'), 'Close': pl.col('Close'), 'Volume': pl.col('Volume')
        }
        
        pl_df = pl.from_pandas(df_features)
        expressions = []
        for name, formula in formulas_dict.items():
            try:
                expr = eval(formula, {"__builtins__": {}}, allowed_names)
                expressions.append(expr.alias(name))
            except Exception as e:
                logger.warning(f"Erreur d'évaluation de l'alpha {name} ({formula}): {e}")
                
        if expressions:
            pl_df = pl_df.with_columns(expressions)
            
        df_enriched = pl_df.to_pandas()
        df_enriched.index = df_features.index

        dates_full = df_enriched['Date']
        df_clean = df_enriched.select_dtypes(include=[np.number])
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan).dropna()
        dates_aligned = dates_full.loc[df_clean.index]

        mask = (dates_aligned >= pd.to_datetime(start_date)) & (dates_aligned <= pd.to_datetime(end_date))
        df_period = df_clean.loc[mask].copy()
        dates_period = dates_aligned.loc[mask]

        if df_period.empty or len(df_period) < 5:
            return {"error": "Pas assez de données sur la fenêtre de backtest (vérifiez le ticker MT5 ou les dates)."}

        excluded_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'OC']
        feature_cols = [c for c in df_period.columns if c not in excluded_cols]

        X = df_period[feature_cols]
        y_true = df_period['OC'].astype(int)

        model_bytes = await model_file.read()
        try:
            model = joblib.load(io.BytesIO(model_bytes))
        except Exception:
            return {"error": "Impossible de charger le fichier modèle (.joblib)."}

        if hasattr(model, "feature_names_in_"):
            expected = list(model.feature_names_in_)
            missing = [c for c in expected if c not in X.columns]
            if missing:
                return {"error": f"Le modèle attend des colonnes absentes : {missing}"}
            X = X[expected]

        y_pred = model.predict(X)

        has_proba = hasattr(model, "predict_proba")
        if has_proba:
            proba_up = model.predict_proba(X)[:, 1]
            signal = 2 * proba_up - 1          
        else:
            signal = np.where(y_pred == 1, 1.0, -1.0)

        close_vals = df_period['Close'].values
        forward_return = np.empty(len(close_vals))
        forward_return[:-1] = close_vals[1:] / close_vals[:-1] - 1
        forward_return[-1] = np.nan

        valid = ~np.isnan(forward_return)
        strategy_returns = (signal[valid] * forward_return[valid])
        benchmark_returns = forward_return[valid]
        dates_valid = dates_period.values[valid]

        strategy_returns_pd = pd.Series(strategy_returns)

        equity_strategy = 10000 * (1 + strategy_returns).cumprod()
        equity_benchmark = 10000 * (1 + benchmark_returns).cumprod()

        n = len(equity_strategy)
        step = max(1, n // 80)
        equity_curve = [
            {
                "date": pd.to_datetime(dates_valid[i]).strftime('%Y-%m-%d'),
                "Strategie": round(float(equity_strategy[i]), 2),
                "Benchmark": round(float(equity_benchmark[i]), 2)
            }
            for i in range(0, n, step)
        ]

        days_passed = (pd.to_datetime(dates_valid[-1]) - pd.to_datetime(dates_valid[0])).days or 1
        years_passed = days_passed / 365.25
        total_return = equity_strategy[-1] / 10000 - 1
        cagr = (((equity_strategy[-1] / 10000) ** (1 / years_passed)) - 1) * 100 if years_passed > 0 else 0

        volatility = strategy_returns_pd.std() * np.sqrt(252)
        ann_volatility = volatility * 100
        sharpe = (strategy_returns_pd.mean() * 252) / volatility if volatility != 0 else 0

        cumulative = pd.Series(equity_strategy)
        peak = cumulative.cummax()
        max_dd = ((cumulative - peak) / peak).min() * 100

        downside_std = strategy_returns_pd[strategy_returns_pd < 0].std() * np.sqrt(252)
        sortino = (strategy_returns_pd.mean() * 252) / downside_std if pd.notna(downside_std) and downside_std != 0 else 0
        calmar = cagr / abs(max_dd) if max_dd != 0 else 0
        recovery_factor = (total_return * 100) / abs(max_dd) if max_dd != 0 else 0

        win_rate = (strategy_returns_pd > 0).sum() / len(strategy_returns_pd) * 100
        gross_profit = strategy_returns_pd[strategy_returns_pd > 0].sum()
        gross_loss = abs(strategy_returns_pd[strategy_returns_pd < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')

        avg_win = strategy_returns_pd[strategy_returns_pd > 0].mean()
        avg_loss = abs(strategy_returns_pd[strategy_returns_pd < 0].mean())
        reward_risk = avg_win / avg_loss if pd.notna(avg_loss) and avg_loss != 0 else float('inf')

        var_95 = np.percentile(strategy_returns_pd.dropna(), 5) * 100
        cvar_95 = strategy_returns_pd[strategy_returns_pd <= (var_95 / 100)].mean() * 100

        is_win = strategy_returns_pd > 0
        max_cons_wins = int(is_win.groupby((~is_win).cumsum()).sum().max())
        is_loss = strategy_returns_pd < 0
        max_cons_losses = int(is_loss.groupby((~is_loss).cumsum()).sum().max())

        y_true_valid = y_true.values[valid]
        y_pred_valid = y_pred[valid]
        accuracy = accuracy_score(y_true_valid, y_pred_valid) * 100
        precision = precision_score(y_true_valid, y_pred_valid, zero_division=0) * 100
        recall = recall_score(y_true_valid, y_pred_valid, zero_division=0) * 100
        f1 = f1_score(y_true_valid, y_pred_valid, zero_division=0) * 100
        cm = confusion_matrix(y_true_valid, y_pred_valid).tolist()

        auc = None
        if has_proba:
            try:
                auc = roc_auc_score(y_true_valid, proba_up[valid])
            except ValueError:
                pass

        return {
            "kpis": {
                "cagr": f"{cagr:.1f}%",
                "sharpe": f"{sharpe:.2f}",
                "sortino": f"{sortino:.2f}",
                "calmar": f"{calmar:.2f}",
                "maxDrawdown": f"{max_dd:.1f}%",
                "recoveryFactor": f"{recovery_factor:.2f}",
                "winRate": f"{win_rate:.1f}%",
                "profitFactor": f"{profit_factor:.2f}",
                "rewardRisk": f"{reward_risk:.2f}",
                "volatility": f"{ann_volatility:.1f}%",
                "var95": f"{var_95:.1f}%",
                "cvar95": f"{cvar_95:.1f}%",
                "maxConsWins": max_cons_wins,
                "maxConsLosses": max_cons_losses
            },
            "modelMetrics": {
                "accuracy": f"{accuracy:.1f}%",
                "precision": f"{precision:.1f}%",
                "recall": f"{recall:.1f}%",
                "f1": f"{f1:.1f}%",
                "auc": round(auc, 3) if auc is not None else None,
                "confusionMatrix": cm
            },
            "equityCurve": equity_curve,
            "nObservations": int(n)
        }

    except Exception as e:
        logger.exception(f"Erreur Backtest: {str(e)}")
        return {"error": str(e)}