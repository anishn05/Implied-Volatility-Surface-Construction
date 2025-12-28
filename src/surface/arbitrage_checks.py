import numpy as np


def check_butterfly_arbitrage(strikes, vols):
    """
    Basic convexity check in strike dimension
    """
    second_diff = np.diff(vols, 2)
    return np.any(second_diff < 0)

def enforce_calendar_monotonicity(df):
    df = df.sort_values("maturity").copy()
    total_var = df["total_variance"].values
    for i in range(1, len(total_var)):
        if total_var[i] < total_var[i-1]:
            total_var[i] = total_var[i-1]
    df["total_variance"] = total_var
    return df
