import numpy as np


def check_butterfly_arbitrage(strikes, vols):
    """
    Basic convexity check in strike dimension
    """
    second_diff = np.diff(vols, 2)
    return np.any(second_diff < 0)
