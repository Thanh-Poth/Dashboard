import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit, learning_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score
)
from lightgbm import LGBMClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


class ModelOptimizer:
    """
    Entraîne et optimise un modèle de classification (GridSearchCV) sur un
    dataset donné, et fournit toutes les infos nécessaires pour juger la
    qualité de l'entraînement :
      - score baseline (hyperparamètres par défaut) vs score optimisé
      - historique des essais de la grid search
      - importance approximative de chaque hyperparamètre
      - courbe d'apprentissage (train vs validation)
      - rapport de classification + matrice de confusion
    """

    MODEL_REGISTRY = {
        "random_forest": "optimize_random_forest",
        "lgbm": "optimize_lgbm",
        "svm": "optimize_svm",
    }

    PARAM_GRIDS = {
        "random_forest": {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 10, None],
            'min_samples_split': [2, 5, 10],
            'max_features': ['sqrt', 'log2']
        },
        "lgbm": {
            'n_estimators': [100, 200, 500],
            'learning_rate': [0.01, 0.05, 0.1],
            'num_leaves': [31, 50, 100],
            'max_depth': [-1, 5, 10]
        },
        "svm": {
            'svm__C': [0.1, 1, 10],
            'svm__kernel': ['linear', 'rbf'],
            'svm__gamma': ['scale', 'auto']
        }
    }

    def __init__(self, df: pd.DataFrame, target_col: str = 'OC', test_size: float = 0.33, n_splits: int = 3):
        self.df = df
        self.target_col = target_col
        self.X = self.df.drop(columns=[target_col])
        self.y = self.df[target_col]

        # Split temporel, sans mélange : ce sont des séries temporelles de marché
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=test_size, shuffle=False
        )

        # Un seul schéma de validation croisée temporelle, réutilisé pour TOUS les modèles
        # (avant : RF utilisait TimeSeriesSplit mais LGBM/SVM utilisaient un cv=3 classique,
        # ce qui provoque de la fuite temporelle sur ce type de données)
        self.tscv = TimeSeriesSplit(n_splits=n_splits)

    # ------------------------------------------------------------------
    # Dispatcher générique : le endpoint FastAPI n'a qu'à appeler ça
    # ------------------------------------------------------------------
    def optimize(self, model_type: str, scoring: str = "accuracy") -> dict:
        if model_type not in self.MODEL_REGISTRY:
            raise ValueError(f"model_type doit être l'un de {list(self.MODEL_REGISTRY.keys())}")
        method = getattr(self, self.MODEL_REGISTRY[model_type])
        return method(scoring=scoring)

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------
    def _default_estimator(self, model_type: str):
        if model_type == "random_forest":
            return RandomForestClassifier(random_state=42)
        if model_type == "lgbm":
            return LGBMClassifier(random_state=42, verbose=-1)
        if model_type == "svm":
            return Pipeline([('scaler', StandardScaler()), ('svm', SVC(probability=True, random_state=42))])
        raise ValueError(model_type)

    def _score(self, model, X, y, scoring: str):
        y_pred = model.predict(X)
        if scoring == "f1":
            return f1_score(y, y_pred, zero_division=0)
        if scoring == "precision":
            return precision_score(y, y_pred, zero_division=0)
        if scoring == "recall":
            return recall_score(y, y_pred, zero_division=0)
        if scoring == "roc_auc":
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(X)[:, 1]
                return roc_auc_score(y, proba)
            return None
        return accuracy_score(y, y_pred)  # "accuracy" par défaut

    def _baseline_score(self, model_type: str, scoring: str):
        """Score obtenu SANS aucun tuning, pour mesurer le vrai gain de l'optimisation."""
        baseline_model = self._default_estimator(model_type)
        baseline_model.fit(self.X_train, self.y_train)
        return self._score(baseline_model, self.X_test, self.y_test, scoring)

    def _run_grid_search(self, estimator, param_grid, scoring: str):
        grid_search = GridSearchCV(
            estimator=estimator,
            param_grid=param_grid,
            cv=self.tscv,
            scoring=scoring,
            n_jobs=-1,
            verbose=1
        )
        grid_search.fit(self.X_train, self.y_train)
        return grid_search

    def _diagnostics(self, grid_search: GridSearchCV, model_type: str, scoring: str) -> dict:
        best_model = grid_search.best_estimator_
        best_params = {k.replace("svm__", ""): v for k, v in grid_search.best_params_.items()}
        best_cv_score = grid_search.best_score_

        test_score = self._score(best_model, self.X_test, self.y_test, scoring)
        y_pred = best_model.predict(self.X_test)
        report = classification_report(self.y_test, y_pred, output_dict=True, zero_division=0)
        cm = confusion_matrix(self.y_test, y_pred).tolist()

        # --- Historique d'optimisation : un point par combinaison d'hyperparamètres testée ---
        cv_results = grid_search.cv_results_
        history = [
            {
                "trial": i,
                "score": round(float(cv_results["mean_test_score"][i]), 4),
                "params": {k.replace("svm__", ""): v for k, v in cv_results["params"][i].items()}
            }
            for i in range(len(cv_results["params"]))
        ]

        # --- Importance approximative des hyperparamètres ---
        # Pas d'Optuna ici (GridSearchCV) : on approxime en mesurant, pour chaque
        # paramètre, l'écart entre son meilleur et son pire score moyen (marginalisé
        # sur les autres paramètres). Un écart important = paramètre influent.
        param_names = list(grid_search.param_grid.keys())
        raw_importance = {}
        for p in param_names:
            scores_by_value = {}
            for i, params in enumerate(cv_results["params"]):
                val = params[p]
                scores_by_value.setdefault(val, []).append(cv_results["mean_test_score"][i])
            means = [np.mean(v) for v in scores_by_value.values()]
            clean_name = p.replace("svm__", "")
            raw_importance[clean_name] = float(max(means) - min(means)) if len(means) > 1 else 0.0

        total = sum(raw_importance.values()) or 1.0
        param_importance = {k: round(v / total * 100, 1) for k, v in raw_importance.items()}

        # --- Courbe d'apprentissage (train vs validation) sur le meilleur modèle ---
        lc_scoring = scoring if scoring != "accuracy" else "accuracy"
        try:
            train_sizes, train_scores, val_scores = learning_curve(
                best_model, self.X_train, self.y_train,
                cv=self.tscv, scoring=lc_scoring,
                train_sizes=np.linspace(0.2, 1.0, 5), n_jobs=-1
            )
            learning_curve_data = [
                {
                    "trainSize": int(train_sizes[i]),
                    "trainScore": round(float(train_scores[i].mean()), 4),
                    "validationScore": round(float(val_scores[i].mean()), 4)
                }
                for i in range(len(train_sizes))
            ]
        except Exception:
            # Certaines combinaisons (ex: trop peu de données) peuvent faire échouer
            # la courbe d'apprentissage ; on continue sans bloquer le reste des résultats.
            learning_curve_data = []

        baseline_score = self._baseline_score(model_type, scoring)

        return {
            "best_model": best_model,
            "best_params": best_params,
            "best_cv_score": round(float(best_cv_score), 4),
            "baseline_score": round(float(baseline_score), 4) if baseline_score is not None else None,
            "test_score": round(float(test_score), 4) if test_score is not None else None,
            "report": report,
            "confusion_matrix": cm,
            "optimization_history": history,
            "param_importance": param_importance,
            "learning_curve": learning_curve_data,
            "n_trials": len(cv_results["params"])
        }

    # ------------------------------------------------------------------
    # Méthodes spécifiques par modèle
    # ------------------------------------------------------------------
    def optimize_random_forest(self, scoring: str = "accuracy") -> dict:
        rf = RandomForestClassifier(random_state=42)
        grid_search = self._run_grid_search(rf, self.PARAM_GRIDS["random_forest"], scoring)
        return self._diagnostics(grid_search, "random_forest", scoring)

    def optimize_lgbm(self, scoring: str = "accuracy") -> dict:
        lgbm = LGBMClassifier(random_state=42, verbose=-1)
        grid_search = self._run_grid_search(lgbm, self.PARAM_GRIDS["lgbm"], scoring)
        return self._diagnostics(grid_search, "lgbm", scoring)

    def optimize_svm(self, scoring: str = "accuracy") -> dict:
        pipeline = Pipeline([('scaler', StandardScaler()), ('svm', SVC(probability=True, random_state=42))])
        grid_search = self._run_grid_search(pipeline, self.PARAM_GRIDS["svm"], scoring)
        return self._diagnostics(grid_search, "svm", scoring)