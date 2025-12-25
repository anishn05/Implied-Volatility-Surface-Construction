import numpy as np


def compute_forward_price(spot: float,
                          rate: float,
                          dividend_yield: float,
                          maturity: float) -> float:
    """
    Simple forward price model
    """
    return spot * np.exp((rate - dividend_yield) * maturity)
