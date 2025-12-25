import numpy as np
from datetime import datetime
import pandas as pd

from src.market_data.loader import load_options_chain
from src.market_data.filters import clean_option_quotes
from src.market_data.forwards import compute_forward_price
from src.pricing.implied_vol import implied_vol
from src.surface.smile import build_smile
from src.visualization.plots import plot_smile

# Parameters
TICKER = "AAPL"
EXPIRY = "2026-01-30"
RISK_FREE_RATE = 0.03
DIVIDEND_YIELD = 0.005

# Load data
df = load_options_chain(TICKER, EXPIRY)
df.to_excel('Option Chain.xlsx')
df = clean_option_quotes(df)

# Market inputs
spot = df["lastPrice"].iloc[0]
valuation_date = df["valuation_date"].iloc[0]
expiry_date = df["expiry"].iloc[0]
T = (expiry_date - valuation_date).days / 365.0

forward = compute_forward_price(
    spot,
    RISK_FREE_RATE,
    DIVIDEND_YIELD,
    T
)

# Compute implied vols
df["implied_vol"] = df.apply(
    lambda x: implied_vol(
        x["mid"],
        spot,
        x["strike"],
        T,
        RISK_FREE_RATE,
        x["option_type"]
    ),
    axis=1
)

df = df.dropna(subset=["implied_vol"])

# Build and plot smile
smile = build_smile(df, forward, T)
plot_smile(smile["log_moneyness"], smile["implied_vol"], T)
