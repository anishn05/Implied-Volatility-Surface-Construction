import yfinance as yf
import pandas as pd
from datetime import datetime


def load_options_chain(ticker: str, expiry: str) -> pd.DataFrame:
    """
    Load options chain from Yahoo Finance
    """
    tk = yf.Ticker(ticker)
    chain = tk.option_chain(expiry)

    calls = chain.calls.copy()
    calls["option_type"] = "call"

    puts = chain.puts.copy()
    puts["option_type"] = "put"

    df = pd.concat([calls, puts], axis=0)
    df["expiry"] = pd.to_datetime(expiry)
    df["valuation_date"] = pd.to_datetime(datetime.today().date())

    return df.reset_index(drop=True)
