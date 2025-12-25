import numpy as np
from scipy.stats import norm


def bs_price(S, K, T, r, vol, option_type):
    """
    Black-Scholes option price
    """
    if T <= 0 or vol <= 0:
        return 0.0

    d1 = (np.log(S / K) + (r + 0.5 * vol ** 2) * T) / (vol * np.sqrt(T))
    d2 = d1 - vol * np.sqrt(T)

    if option_type == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
