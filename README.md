# Implied Volatility Surface Construction from Market Option Quotes

## Overview

This project implements a full **implied volatility surface construction pipeline** using publicly available option market data.  
Starting from raw option quotes, the framework builds **clean, arbitrage-aware volatility smiles** for each maturity and interpolates them into a continuous implied volatility surface.


> ⚠️ **Disclaimer**  
> Option data is sourced from Yahoo Finance and is inherently noisy and incomplete.  
> Despite extensive filtering and diagnostics, minor local irregularities may persist.

---

## Key Features

- Raw option data ingestion and cleaning  
- Forward-price-based log-moneyness normalization  
- ATM-anchored volatility smile construction  
- Smooth put–call blending around ATM  
- Shape-preserving smile interpolation (PCHIP)  
- Total variance surface construction  
- Calendar monotonicity enforcement  
- Smile diagnostics and instability detection  
- Continuous callable implied volatility surface  
- 3D surface visualization with optional smoothing  

---

## Data Source

- **Underlying:** SPY
- **Options:** Yahoo Finance (`yfinance`)
- **Pricing input:** Mid prices
- **Liquidity filters:** Volume and open interest

---

## Methodology

### 1. Data Cleaning & Preprocessing

Raw option quotes are filtered to remove:
- Illiquid contracts
- Quotes violating intrinsic value constraints
- Expired or near-zero maturity options

Each option is assigned:
- Time to maturity (years)
- Forward price using continuous compounding
- Log-moneyness:

---

### 2. Implied Volatility Calculation

Implied volatility is computed per option via numerical inversion of the Black–Scholes pricing formula.  
Non-convergent or invalid solutions are discarded.

---

### 3. ATM Anchoring & Smile Construction

For each maturity:
- ATM implied volatility is estimated using a weighted average near zero log-moneyness
- Put and call wings are **shifted** to meet at the ATM point
- This avoids artificial jumps caused by bid/ask asymmetry

---

### 4. Put–Call Blending Around ATM

A smooth transition between put and call wings is constructed using:
- A hyperbolic tangent blending function
- A fixed blending region around ATM log-moneyness

This avoids hard joins and ensures local smoothness.

---

### 5. Shape-Preserving Smile Interpolation

Each smile is interpolated onto a dense log-moneyness grid using:

- **PCHIP (Piecewise Cubic Hermite Interpolation)**


---

### 6. Conversion to Total Variance

Interpolated smiles are converted to total variance.

Working in total variance space simplifies:
- Calendar arbitrage detection
- Cross-maturity interpolation

---

### 7. Maturity Filtering & Stability Controls

To improve robustness:
- Extremely short maturities are excluded
- Maturities with insufficient strike coverage are removed
- Upper bounds are applied to implied volatility

---

### 8. Smile Diagnostics & Outlier Detection

Each maturity is analyzed using:
- First derivative (slope)
- Second derivative (curvature)
- Implied volatility range

Highly unstable smiles are flagged for review.  

---

### 9. Calendar Monotonicity Enforcement

For each log-moneyness slice:
- Total variance is enforced to be non-decreasing in maturity

This prevents calendar arbitrage.

---

### 10. Surface Interpolation

The surface is built using a two-stage interpolation:
1. PCHIP interpolation in maturity for fixed log-moneyness
2. PCHIP interpolation across log-moneyness for a fixed maturity


