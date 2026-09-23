"""The pinned cruise window: defined once here, imported by every evaluation script.

Definition (METHODOLOGY, "Cruise window — pinned definition and clock sensitivity"):
horizontal ground speed |d(x,y)/dt| from ground truth, smoothed by a centred moving
average of CRUISE_BOXCAR_S; the window is the largest contiguous run where the smoothed
speed exceeds CRUISE_SPEED. Dependency-free apart from numpy.
"""
import numpy as np

CRUISE_SPEED = 0.30      # m/s
CRUISE_BOXCAR_S = 0.42   # s, centred moving average


def cruise_bounds(t, x, y, speed=None):
    """[t0, t1] (same clock as t) of the largest contiguous run above `speed`."""
    speed = CRUISE_SPEED if speed is None else speed
    sp = np.hypot(np.gradient(x, t), np.gradient(y, t))
    c = np.r_[0.0, np.cumsum(sp)]
    lo = np.searchsorted(t, t - CRUISE_BOXCAR_S / 2, "left")
    hi = np.searchsorted(t, t + CRUISE_BOXCAR_S / 2, "right")
    cr = (c[hi] - c[lo]) / (hi - lo) > speed
    bi = bj = i = 0
    while i < len(cr):
        if cr[i]:
            j = i
            while j < len(cr) and cr[j]:
                j += 1
            if j - i > bj - bi:
                bi, bj = i, j
            i = j
        else:
            i += 1
    return float(t[bi]), float(t[bj - 1])
