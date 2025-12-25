from scipy.optimize import brentq
from .black_scholes import bs_price


def implied_vol(price, S, K, T, r, option_type):
    """
    Implied volatility via Brent root finding
    """

    def objective(vol):
        return bs_price(S, K, T, r, vol, option_type) - price

    try:
        return brentq(objective, 1e-6, 5.0)
    except ValueError:
        return None
