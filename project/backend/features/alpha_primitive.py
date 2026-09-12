import polars as pl

# --- OPÉRATEURS TEMPORELS ---
def ts_delay(expr: pl.Expr, d: int) -> pl.Expr:
    """Retourne la valeur d'il y a d jours."""
    return expr.shift(d)

def ts_delta(expr: pl.Expr, d: int) -> pl.Expr:
    """Différence avec la valeur d'il y a d jours."""
    return expr.diff(d)

def ts_mean(expr: pl.Expr, d: int) -> pl.Expr:
    """Moyenne mobile sur d jours."""
    return expr.rolling_mean(window_size=d)

def ts_std(expr: pl.Expr, d: int) -> pl.Expr:
    """Écart-type mobile sur d jours."""
    return expr.rolling_std(window_size=d)

def ts_max(expr: pl.Expr, d: int) -> pl.Expr:
    """Maximum sur une fenêtre glissante."""
    return expr.rolling_max(window_size=d)

def ts_min(expr: pl.Expr, d: int) -> pl.Expr:
    """Minimum sur une fenêtre glissante."""
    return expr.rolling_min(window_size=d)

# --- OPÉRATEURS TRANSVERSAUX (Cross-Sectional / Math) ---
def add(expr1: pl.Expr, expr2: pl.Expr) -> pl.Expr:
    return expr1 + expr2

def sub(expr1: pl.Expr, expr2: pl.Expr) -> pl.Expr:
    return expr1 - expr2

def mul(expr1: pl.Expr, expr2: pl.Expr) -> pl.Expr:
    return expr1 * expr2

def div(expr1: pl.Expr, expr2: pl.Expr) -> pl.Expr:
    # Ajout d'une protection contre la division par zéro
    return expr1 / (expr2 + 1e-8)