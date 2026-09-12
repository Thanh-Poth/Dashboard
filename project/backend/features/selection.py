import logging
import pandas as pd
import numpy as np
from sklearn.feature_selection import mutual_info_classif

logger = logging.getLogger(__name__)

class FeatureSelector:
    def __init__(self, config: dict | None = None, target_col: str = "OC", estimator=None):
        cfg = config or {}
        self.target_col = target_col
        self.max_correlation = cfg.get("max_correlation", 0.85)
        self.top_k = cfg.get("top_k", 20)
        self.estimator = estimator
        self.selected_features_ = None

    def _filter_correlation(self, df: pd.DataFrame, feature_cols: list) -> list:
        corr_matrix = df[feature_cols].corr().abs()
        upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

        to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > self.max_correlation)]
        selected_features = [col for col in feature_cols if col not in to_drop]

        logger.info(f"Filtrage corrélation (train) : {len(to_drop)} features supprimées.")
        return selected_features

    def _filter_importance(self, df: pd.DataFrame, feature_cols: list) -> list:
        X = df[feature_cols]
        y = df[self.target_col]

        if self.estimator is not None:
            self.estimator.fit(X, y)
            if hasattr(self.estimator, "feature_importances_"):
                importances = self.estimator.feature_importances_
            elif hasattr(self.estimator, "coef_"):
                importances = np.abs(self.estimator.coef_[0])
            else:
                logger.error("L'estimateur fourni ne possède ni 'feature_importances_' ni 'coef_'.")
                raise ValueError("L'estimateur fourni ne possède ni 'feature_importances_' ni 'coef_'.")
        else:
            importances = mutual_info_classif(X, y, random_state=42)

        importance_series = pd.Series(importances, index=X.columns)
        importances_sorted = importance_series.sort_values(ascending=False)

        top_features = importances_sorted.head(self.top_k).index.tolist()
        logger.info(f"Filtrage importance (train) : {len(top_features)} features conservées sur {len(feature_cols)}.")
        return top_features

    def fit(self, df_train: pd.DataFrame) -> "FeatureSelector":
        excluded_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', self.target_col]
        feature_cols = [col for col in df_train.columns if col not in excluded_cols]

        uncorrelated_features = self._filter_correlation(df_train, feature_cols)
        self.selected_features_ = self._filter_importance(df_train, uncorrelated_features)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.selected_features_ is None:
            logger.error("FeatureSelector n'a pas été fit(). Appelez fit(df_train) avant transform().")
            raise RuntimeError("FeatureSelector n'a pas été fit(). Appelez fit(df_train) avant transform().")

        base_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', self.target_col]
        cols_to_keep = [c for c in base_cols if c in df.columns] + self.selected_features_
        return df[cols_to_keep]

    def fit_transform(self, df_train: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df_train).transform(df_train)