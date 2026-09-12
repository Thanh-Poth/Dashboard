import random
import polars as pl
from features.alpha_primitive import *

class AlphaGenerator:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.n_alphas = cfg.get("n_alphas", 50)
        self.max_depth = cfg.get("max_depth", 3)
        self.windows = cfg.get("windows", [5, 10, 20, 60])
        self.base_features = ["Open", "High", "Low", "Close", "Volume"]
        self.unary_ops = [ts_delay, ts_delta, ts_mean, ts_std, ts_max, ts_min]
        self.binary_ops = [add, sub, mul, div]
        self.formulas = {}

    def _generate_random_expr(self, depth: int):
        """Retourne (Expression Polars, Chaine de caractères de la formule)"""
        if depth >= self.max_depth or random.random() < 0.2:
            feature_name = random.choice(self.base_features)
            # On retourne la colonne et son nom
            return pl.col(feature_name), feature_name
        
        op_type = random.choice(["unary", "binary"])
        
        if op_type == "unary":
            op = random.choice(self.unary_ops)
            window = random.choice(self.windows)
            sub_expr, sub_str = self._generate_random_expr(depth + 1)
            
            # Construction de la chaîne textuelle (ex: "ts_mean(Close, 20)")
            formula_str = f"{op.__name__}({sub_str}, {window})"
            return op(sub_expr, window), formula_str
            
        else: # binary
            op = random.choice(self.binary_ops)
            sub_expr1, sub_str1 = self._generate_random_expr(depth + 1)
            sub_expr2, sub_str2 = self._generate_random_expr(depth + 1)
            
            # Construction de la chaîne textuelle (ex: "add(Open, Close)")
            formula_str = f"{op.__name__}({sub_str1}, {sub_str2})"
            return op(sub_expr1, sub_expr2), formula_str

    def generate_features(self, df: pl.DataFrame) -> pl.DataFrame:
        expressions = []
        for i in range(self.n_alphas):
            expr, formula_str = self._generate_random_expr(depth=0)
            alpha_name = f"alpha_{i}"
            
            # On stocke la formule dans le dictionnaire
            self.formulas[alpha_name] = formula_str
            
            expressions.append(expr.alias(alpha_name))
            
        return df.with_columns(expressions)