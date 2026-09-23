"""IMU replay timing: dejitter the bridge receipt stamps (OI-2 ruling, 2026-09-24).

`imu_bridge.py` stamped `/imu/data_raw` at *receipt* (ROS sim clock) in every existing
bag, so the header stamps scatter about 0-12 ms around the true, regular 3 ms sampling.
EKF3 integrates on SITL's regular internal sensor time. For the UKF/FGO to get
equivalently regular IMU timing, the replay replaces each IMU stamp with a least-squares
line through the receipt stamps, t_i = a + b*i, in bag (= receipt) order. That removes
the jitter and keeps the mean receipt latency, so there is NO shift of the IMU against
the flow or range capture stamps.

This is the fairness correction ruled for OI-2 (METHODOLOGY). The reconstructed
sensor-time shift was rejected: it would be an offset fitted to a +-5 ms
reconstruction.

Validity (all nine dsn_* bags): period 3.00057 ms, residuals within +-13 ms, std 3.4 ms,
stamps monotonic, no step from a dropped sample. The guard below refuses a bag that
breaks these assumptions rather than silently mis-timing it. Offline replay only: the
fit uses the whole flight. A live estimator would use HIGHRES_IMU time_usec, which new
bags record on /imu/time_ref.
"""
import numpy as np

MAX_ABS_RESID_S = 0.025


def dejitter_imu(ev):
    """ev: list of (t, kind, payload) in BAG order. Returns (new_ev, stats); IMU stamps linearised."""
    idx = [k for k, e in enumerate(ev) if e[1] == "imu"]
    t = np.array([ev[k][0] for k in idx])
    if not np.all(np.diff(t) >= 0):
        raise ValueError("IMU receipt stamps not monotonic in bag order; refusing to dejitter")
    i = np.arange(len(t))
    b, a = np.polyfit(i, t, 1)
    fit = a + b * i
    res = t - fit
    if np.abs(res).max() > MAX_ABS_RESID_S:
        raise ValueError(f"IMU dejitter residual {np.abs(res).max()*1e3:.1f} ms > "
                         f"{MAX_ABS_RESID_S*1e3:.0f} ms (dropped samples?); refusing")
    new = list(ev)
    for k, tn in zip(idx, fit):
        new[k] = (float(tn), ev[k][1], ev[k][2])
    return new, {"period_ms": 1e3 * b, "resid_std_ms": 1e3 * res.std(), "resid_maxabs_ms": 1e3 * np.abs(res).max()}
