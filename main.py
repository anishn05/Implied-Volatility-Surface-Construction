import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import yfinance as yf
from scipy.interpolate import interp1d, PchipInterpolator
from scipy.ndimage import gaussian_filter

from src.market_data.loader import load_option_chain
from src.market_data.forwards import compute_forward_price
from src.market_data.filters import clean_option_quotes
from src.pricing.implied_vol import implied_vol
from src.visualization.plots import plot_surface  
from src.surface.smile import  compute_surface_iv

# -----------------------
# Config
# -----------------------
T_MIN_FILTER = 40 / 365
MIN_POINTS_PER_MATURITY = 10
MAX_IV = 1.0
ATM_EPS = 0.02
BLEND_WIDTH = 0.05
INTERP_GRID = np.linspace(-0.5, 0.5, 201)
sigma_lm, sigma_T = 1.0, 1.0

ticker_symbol = "SPY"
min_volume = 1
min_open_interest = 1
risk_free_rate = 0.05
dividend_yield = 0.015

# -----------------------
# Helper functions
# -----------------------
def blend_weight(x, width=BLEND_WIDTH):
    return 0.5 * (1 + np.tanh(x / width))


# -----------------------
# Load and clean option data
# -----------------------
ticker = yf.Ticker(ticker_symbol)
spot_price = ticker.history(period="1d")["Close"].iloc[-1]

all_options = []
for expiry in ticker.options:
    df = load_option_chain(ticker, expiry)
    if not df.empty:
        all_options.append(df)
option_data = pd.concat(all_options, ignore_index=True) if all_options else pd.DataFrame()
cleaned_options = clean_option_quotes(option_data,
                                      min_volume=min_volume,
                                      min_open_interest=min_open_interest)

# Compute time to maturity
cleaned_options['T'] = (cleaned_options['expiry'] - datetime.utcnow()).dt.days / 365.0

# Compute forward per expiry
forward_prices = {expiry: compute_forward_price(spot_price, risk_free_rate, dividend_yield,
                                                cleaned_options[cleaned_options['expiry'] == expiry]['T'].iloc[0])
                  for expiry in cleaned_options['expiry'].unique()}
cleaned_options['forward'] = cleaned_options['expiry'].map(forward_prices)
cleaned_options = cleaned_options[cleaned_options['T'] > 0].copy()

# -----------------------
# Build smiles
# -----------------------
all_smiles = []

valuation_date = cleaned_options["valuation_date"].iloc[0]
for expiry, df_exp in cleaned_options.groupby("expiry"):
    T = (expiry - valuation_date).days / 365.0
    if T <= 0:
        continue

    forward = compute_forward_price(spot_price, risk_free_rate, dividend_yield, T)
    df = df_exp.copy()

    # intrinsic check
    df["intrinsic"] = np.where(df["option_type"]=="call",
                               np.maximum(spot_price - df["strike"], 0.0),
                               np.maximum(df["strike"] - spot_price, 0.0))
    df = df[df["mid"] >= df["intrinsic"]]

    # implied vol
    df["implied_vol"] = df.apply(
        lambda r: implied_vol(r["mid"], spot_price, r["strike"], T, risk_free_rate, r["option_type"]), axis=1)
    df = df.dropna(subset=["implied_vol"])

    df["log_moneyness"] = np.log(df["strike"]/forward)

    # ATM anchoring
    atm_band = df[np.abs(df["log_moneyness"]) < ATM_EPS]
    if atm_band.empty:
        continue
    atm_iv = np.average(atm_band["implied_vol"], weights=atm_band["openInterest"])

    puts = df[df["option_type"]=="put"].copy()
    calls = df[df["option_type"]=="call"].copy()
    if puts.empty or calls.empty:
        continue

    put_atm_idx = puts["log_moneyness"].abs().idxmin()
    call_atm_idx = calls["log_moneyness"].abs().idxmin()
    puts["implied_vol"] += atm_iv - puts.loc[put_atm_idx, "implied_vol"]
    calls["implied_vol"] += atm_iv - calls.loc[call_atm_idx, "implied_vol"]

    # blend
    blend_x = np.linspace(-BLEND_WIDTH, BLEND_WIDTH, 21)
    put_interp = interp1d(puts["log_moneyness"], puts["implied_vol"], kind="linear", fill_value="extrapolate")
    call_interp = interp1d(calls["log_moneyness"], calls["implied_vol"], kind="linear", fill_value="extrapolate")
    blend_region = pd.DataFrame({"log_moneyness": blend_x})
    blend_region["w"] = blend_weight(blend_region["log_moneyness"])
    blend_region["implied_vol"] = (1 - blend_region["w"])*put_interp(blend_x) + blend_region["w"]*call_interp(blend_x)
    blend_region["strike"] = forward * np.exp(blend_region["log_moneyness"])

    left = puts[puts["log_moneyness"] < -BLEND_WIDTH]
    right = calls[calls["log_moneyness"] > BLEND_WIDTH]
    smile = pd.concat([
        left[["strike", "log_moneyness", "implied_vol"]],
        blend_region[["strike", "log_moneyness", "implied_vol"]],
        right[["strike", "log_moneyness", "implied_vol"]]
    ])
    smile = smile.sort_values("log_moneyness").reset_index(drop=True)
    smile["expiry"] = expiry
    smile["maturity"] = T
    all_smiles.append(smile)

smiles = pd.concat(all_smiles, ignore_index=True)
smiles.to_excel("smiles.xlsx")

# -----------------------
# Interpolate smiles
# -----------------------
all_interp_smiles = []
for expiry, smile in smiles.groupby("expiry"):
    smile = smile.sort_values("log_moneyness")
    x, y = smile["log_moneyness"].values, smile["implied_vol"].values
    if len(x) < 5 or np.any(np.diff(x) <= 0) or np.min(np.abs(x)) > 1e-3:
        continue
    interp_x = INTERP_GRID[(INTERP_GRID >= x.min()) & (INTERP_GRID <= x.max())]
    interp_vol = PchipInterpolator(x, y)(interp_x)
    interp_smile = pd.DataFrame({"expiry": expiry, "maturity": smile["maturity"].iloc[0],
                                 "log_moneyness": interp_x, "implied_vol": interp_vol})
    all_interp_smiles.append(interp_smile)
interp_smiles = pd.concat(all_interp_smiles, ignore_index=True)

# -----------------------
# Clean and filter interpolated smiles
# -----------------------
interp_smiles["total_variance"] = interp_smiles["implied_vol"]**2 * interp_smiles["maturity"]
interp_smiles = interp_smiles[interp_smiles["maturity"] >= T_MIN_FILTER]
valid_maturities = interp_smiles.groupby("maturity")["log_moneyness"].count()
valid_maturities = valid_maturities[valid_maturities >= MIN_POINTS_PER_MATURITY].index
interp_smiles = interp_smiles[interp_smiles["maturity"].isin(valid_maturities)].copy()
interp_smiles["total_variance"] = np.minimum(interp_smiles["total_variance"], (MAX_IV**2)*interp_smiles["maturity"])

# -----------------------
# Build IV surface
# -----------------------
surface_iv_func = compute_surface_iv(interp_smiles)

lm_min, lm_max = interp_smiles["log_moneyness"].min(), interp_smiles["log_moneyness"].max()
T_min, T_max = interp_smiles["maturity"].min(), interp_smiles["maturity"].max()
lm_grid = np.linspace(lm_min, lm_max, 100)
T_grid = np.linspace(T_min, T_max, 100)
LM, T = np.meshgrid(lm_grid, T_grid)
IV = np.vectorize(surface_iv_func)(LM, T)
IV = np.clip(IV, 0, MAX_IV)
IV_smooth = gaussian_filter(IV, sigma=[sigma_T, sigma_lm])

# -----------------------
# Plot surface
# -----------------------
plot_surface(LM, T, IV_smooth, ticker_symbol)
