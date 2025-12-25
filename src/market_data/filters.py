import pandas as pd


def clean_option_quotes(df: pd.DataFrame,
                         min_volume: int = 1,
                         min_open_interest: int = 1) -> pd.DataFrame:
    """
    Clean raw option quotes
    """
    df = df.copy()

    df = df[df["bid"] > 0]
    df = df[df["ask"] > 0]
    df = df[df["volume"] >= min_volume]
    df = df[df["openInterest"] >= min_open_interest]

    df["mid"] = 0.5 * (df["bid"] + df["ask"])

    return df.reset_index(drop=True)
