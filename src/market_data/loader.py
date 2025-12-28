import yfinance as yf
import pandas as pd
from datetime import datetime
from pathlib import Path


def _remove_timezone(x):
    if hasattr(x, "dt"):
        return x.dt.tz_localize(None)
    if hasattr(x, "tz_localize"):
        return x.tz_localize(None)
    return x


def load_option_chain(
    ticker: yf.Ticker,
    expiry: str,
    write_to_excel: bool = False,
    output_dir: str = "data/raw"
) -> pd.DataFrame:
    """
    Load call options for a given expiry and clean timestamps for Excel
    """
    try:
        chain = ticker.option_chain(expiry)
    except Exception:
        return pd.DataFrame()
    
    calls = chain.calls.copy()
    calls["option_type"] = "call"
    puts = chain.puts.copy()
    puts["option_type"] = "put"

    df = pd.concat([calls, puts], ignore_index=True)

    df["expiry"] = pd.to_datetime(expiry)
    df["valuation_date"] = pd.to_datetime(datetime.utcnow().date())

    for col in ["lastTradeDate", "expiry", "valuation_date"]:
        if col in df.columns:
            df[col] = _remove_timezone(df[col])

    if write_to_excel:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        df.to_excel(
            Path(output_dir) / f"{ticker.ticker}_calls_{expiry}.xlsx",
            index=False
        )

    return df.reset_index(drop=True)
