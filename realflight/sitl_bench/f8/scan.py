"""F8: scan every bench session for (a) each touchdown and (b) each arming, reporting the EKF3 velocity error,
the flow gap before touchdown, the flow-gate lock-out (XKF5.NI >= 100) and the take-off excursion.

Truth = Gazebo pose as sent by the mocap forwarder (forwarder.csv; rows with mode 'normal' and the vehicle's own
body). Truth x = East, y = North (ENU). The FC (F) <-> wall (W) map is the median W - F of the FC events in the
session's analysis timelines (residual a few tens of ms, handover 2026-10-12 §2).

Usage: python scan.py <pkl_dir> [out_csv]
"""
import csv
import glob
import os
import pickle
import re
import sys

import numpy as np

WB = os.path.expanduser("~/thesis_data/wbench")


def offset_wf(sess):
    vals = []
    for f in glob.glob(os.path.join(WB, sess, "analysis", "*.txt")):
        for line in open(f, errors="replace"):
            m = re.match(r"^(\d+\.\d+) F=\s*(-?\d+\.\d+) FC", line)
            if m:
                vals.append(float(m.group(1)) - float(m.group(2)))
    return float(np.median(vals)) if vals else None


def truth(sess):
    p = os.path.join(WB, sess, "forwarder.csv")
    if not os.path.exists(p):
        return None
    seen = {}
    for r in csv.DictReader(open(p)):
        if r["mode"] != "normal" or not r["body"].endswith("#1") or r["dest"] != "1":
            continue
        seen[r["t_mocap"]] = (float(r["t_mocap"]), float(r["x"]), float(r["y"]), float(r["z"]))
    a = np.array(sorted(seen.values()))
    return a if len(a) else None


def series(d, k, f, c=None):
    r = [x for x in d.get(k, []) if c is None or x.get("C") == c]
    return np.array([x["TimeUS"] * 1e-6 for x in r]), np.array([x[f] for x in r], dtype=float)


def at(t, v, ts):
    i = np.searchsorted(t, ts) - 1
    return v[i] if 0 <= i < len(v) else np.nan


def truth_vel(T, w):
    """Mean true horizontal velocity (E, N) over [w-0.3, w-0.05] (ENU)."""
    m = (T[:, 0] >= w - 0.35) & (T[:, 0] <= w - 0.05)
    if m.sum() < 2:
        return np.nan, np.nan
    s = T[m]
    dt = s[-1, 0] - s[0, 0]
    return (s[-1, 1] - s[0, 1]) / dt, (s[-1, 2] - s[0, 2]) / dt


def main(pdir, out=None):
    rows = []
    for p in sorted(glob.glob(os.path.join(pdir, "wbench*.pkl"))):
        sess, binn = os.path.basename(p)[:-4].split("__")
        d = pickle.load(open(p, "rb"))
        off = offset_wf(sess)
        T = truth(sess)
        tof = np.array([x["TimeUS"] * 1e-6 for x in d.get("OF", [])])
        tn, ni = series(d, "XKF5", "NI")
        tv, vn0 = series(d, "XKF1", "VN", 0)
        _, ve0 = series(d, "XKF1", "VE", 0)
        tv1, vn1 = series(d, "XKF1", "VN", 1)
        _, ve1 = series(d, "XKF1", "VE", 1)
        _, roll0 = series(d, "XKF1", "Roll", 0)
        tr, rng = series(d, "RFND", "Dist")
        # touchdowns: anchored on each EV LAND_COMPLETE_MAYBE (Id 17, AP_Logger.h:29); the touchdown is the last
        # rangefinder down-crossing of 0.12 m in the 3 s before it. (A bare RFND crossing also fires on the climb-phase
        # rangefinder dropouts of Known Issue #5, so it is not used on its own.)
        tds = []
        for x in d.get("EV", []):
            if x["Id"] != 17:
                continue
            te = x["TimeUS"] * 1e-6
            cr = [tr[i] for i in range(1, len(rng)) if rng[i] <= 0.12 < rng[i - 1] and te - 3 <= tr[i] <= te]
            t = cr[-1] if cr else te
            if not tds or t - tds[-1] > 5:
                tds.append(t)
        events = [("touchdown", t) for t in tds]
        events += [("arm", x["TimeUS"] * 1e-6) for x in d.get("ARM", []) if x["ArmState"] == 1]
        for kind, t in sorted(events, key=lambda e: e[1]):
            # flow gap: longest gap between OF rows in the 5 s before the event
            m = (tof > t - 5) & (tof <= t)
            g = np.diff(np.concatenate([[t - 5], tof[m], [t]])).max() if m.any() else 5.0
            # the last OF row before the event
            lastof = t - tof[tof <= t][-1] if (tof <= t).any() else np.nan
            vh0 = np.hypot(at(tv, vn0, t), at(tv, ve0, t))
            vh1 = np.hypot(at(tv1, vn1, t), at(tv1, ve1, t))
            # post-event: max EKF |Vh| on the ground within 10 s, and lock-out (NI >= 100) seconds in 10 s
            m10 = (tv > t) & (tv < t + 10)
            vmax = np.hypot(vn0[m10], ve0[m10]).max() if m10.any() else np.nan
            mn = (tn > t) & (tn < t + 10)
            lock = (ni[mn] >= 100).sum() * np.median(np.diff(tn)) if mn.any() else np.nan
            row = dict(session=sess, bin=binn, kind=kind, F=round(t, 2), flowgap5s=round(g, 2),
                       last_of_age=round(lastof, 3), ekf_vh_c0=round(vh0, 3), ekf_vh_c1=round(vh1, 3),
                       ekf_ve_c0=round(at(tv, ve0, t), 3), ekf_vn_c0=round(at(tv, vn0, t), 3),
                       roll_c0=round(at(tv, roll0, t), 2), ni_at=at(tn, ni, t),
                       max_vh_10s=round(vmax, 3), ni_lock_s_10s=round(lock, 1))
            if T is not None and off is not None:
                w = t + off
                # (truth-velocity columns were dropped: near freezes and carries they are contaminated)
                if kind == "arm":
                    m5 = (T[:, 0] >= w) & (T[:, 0] <= w + 8)
                    if m5.any():
                        p0 = T[np.searchsorted(T[:, 0], w)]
                        dd = np.hypot(T[m5, 1] - p0[1], T[m5, 2] - p0[2])
                        row.update(takeoff_exc_8s=round(dd.max(), 2))
            rows.append(row)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    w = csv.DictWriter(open(out, "w") if out else sys.stdout, fieldnames=keys)
    w.writeheader()
    for r in rows:
        w.writerow(r)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
