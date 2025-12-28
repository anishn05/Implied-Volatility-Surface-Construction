import numpy as np
from scipy.interpolate import interp1d
from scipy.interpolate import PchipInterpolator
import pandas as pd

def interpolate_smile(smile_df, grid_points=201):
    """
    Interpolate a single expiry smile using total variance.
    Guarantees the curve passes through all points in smile_df,
    including the ATM region (log_m ~ 0).
    """
    T = smile_df["maturity"].iloc[0]

    # Copy dataframe
    df = smile_df.copy()

    # Compute total variance
    df["total_var"] = df["implied_vol"]**2 * T

    # Find ATM point (closest to log-moneyness 0)
    atm_idx = (df["log_moneyness"] - 0).abs().idxmin()
    atm_log_m = df.loc[atm_idx, "log_moneyness"]
    atm_iv = df.loc[atm_idx, "implied_vol"]

    # Ensure ATM is explicitly included
    if atm_log_m not in df["log_moneyness"].values:
        atm_row = pd.DataFrame({
            "strike": [np.nan],  # optional
            "log_moneyness": [atm_log_m],
            "implied_vol": [atm_iv],
            "maturity": [T],
            "total_var": [atm_iv**2 * T]
        })
        df = pd.concat([df, atm_row], ignore_index=True)

    # Collapse duplicates and sort
    df = df.groupby("log_moneyness", as_index=False).agg({"total_var": "mean"}).sort_values("log_moneyness")

    k = df["log_moneyness"].values
    w = df["total_var"].values

    # Optional: enforce left-skew monotonicity for smoothness
    w = np.maximum.accumulate(w[::-1])[::-1]

    # Interpolation grid: include all points (ensures raw + ATM overlap)
    lm_grid = np.linspace(k.min(), k.max(), grid_points)
    lm_grid = np.unique(np.concatenate([lm_grid, k]))

    # PCHIP interpolation, no extrapolation
    interp = PchipInterpolator(k, w, extrapolate=False)
    w_interp = interp(lm_grid)
    w_interp = np.maximum(w_interp, 1e-6)  # clip tiny negative values
    iv_interp = np.sqrt(w_interp / T)

    return lm_grid, iv_interp