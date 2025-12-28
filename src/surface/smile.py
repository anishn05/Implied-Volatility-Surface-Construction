import numpy as np
import pandas as pd

from src.surface.arbitrage_checks import enforce_calendar_monotonicity
from scipy.interpolate import interp1d, PchipInterpolator

def build_smile(df: pd.DataFrame,
                forward: float,
                maturity: float) -> pd.DataFrame:
    """
    Convert strikes to log-moneyness for smile construction
    """
    smile = df.copy()
    smile["log_moneyness"] = np.log(smile["strike"] / forward)
    smile["maturity"] = maturity

    return smile[["strike", "log_moneyness", "implied_vol", "maturity"]]

def smile_diagnostics(df_smile):
    df = df_smile.sort_values("log_moneyness")
    lm, iv = df["log_moneyness"].values, df["implied_vol"].values
    if len(lm) < 6:
        return None
    d1 = np.gradient(iv, lm)
    d2 = np.gradient(d1, lm)
    return {"max_slope": np.max(np.abs(d1)),
            "max_curvature": np.max(np.abs(d2)),
            "iv_range": iv.max() - iv.min()}

def drop_kinky_points(df_smile, slope_q=0.99):
    df = df_smile.sort_values("log_moneyness").copy()
    lm, iv = df["log_moneyness"].values, df["implied_vol"].values
    d1 = np.gradient(iv, lm)
    slope_thresh = np.quantile(np.abs(d1), slope_q)
    df["bad_point"] = np.abs(d1) > slope_thresh
    return df[~df["bad_point"]]

def compute_surface_iv(interp_smiles):
    surface_grid = interp_smiles.groupby("log_moneyness", group_keys=False).apply(enforce_calendar_monotonicity)
    surface_interpolators = {}
    for lm, df_lm in surface_grid.groupby("log_moneyness"):
        T_vals = df_lm["maturity"].values
        w_vals = df_lm["total_variance"].values
        surface_interpolators[lm] = PchipInterpolator(T_vals, w_vals, extrapolate=True)

    def surface_iv_func(log_m, T):
        if T <= 0:
            return 0.0
        lm_nodes = np.array(sorted(surface_interpolators.keys()))
        total_var_nodes = np.array([surface_interpolators[lm](T) for lm in lm_nodes])
        interp_total_var = PchipInterpolator(lm_nodes, total_var_nodes, extrapolate=True)
        total_var = float(interp_total_var(log_m))
        return np.sqrt(max(total_var / T, 0.0))

    return surface_iv_func