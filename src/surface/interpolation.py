import numpy as np
from scipy.interpolate import interp1d


def interpolate_smile(log_m, vols):
    """
    Interpolate implied vol smile
    """
    interp = interp1d(
        log_m,
        vols,
        kind="cubic",
        fill_value="extrapolate"
    )
    return interp
