import numpy as np
import pandas as pd


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
