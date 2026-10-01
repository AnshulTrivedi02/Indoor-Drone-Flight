#!/usr/bin/env python3
"""FGO live-shadow variant of eval/ukf_contact_prediction.py (D21: the FGO no-heading prediction from half-speed
data): --live TRIAL reads the FGO backend's current-time output XFGO instead of XUKO; otherwise identical.
Original text: D16 ruling check (2026-09-30): the no-heading contact prediction by the method VALIDATED in set (a)
(METHODOLOGY "(a) Prediction": open-loop East error of the estimator against truth reaches 9.58 m at cruise
+187 s; closed loop contact came at +186.2 s). The East error is taken from the spawn origin, NOT
re-referenced, so it contains the heading offset built up on the ground and in the climb.
Sources: the port's current-time output (Replay ukf_shadow.csv, or the live P2 log's XUKO) against SIM.
Also reported: the UKF heading error at take-off and at cruise start (deg; + = estimate clockwise of truth).
Usage (venv-ardupilot): fgo_contact_prediction_live.py --replay TRIAL CSV ... | --live TRIAL [--json OUT]"""
import argparse, json, math, sys, os
import numpy as np
from pymavlink import mavutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds
ap = argparse.ArgumentParser(); ap.add_argument("--replay", nargs=2, action="append", default=[]); ap.add_argument("--live", action="append", default=[])
ap.add_argument("--json"); a = ap.parse_args()
TD = os.path.expanduser("~/thesis_data/trials")
un = lambda d: np.degrees(np.unwrap(np.radians(d)))


def sim(trial, extra=()):
    m = mavutil.mavlink_connection(f"{TD}/{trial}/ardupilot.bin"); S = []; X = []
    while True:
        r = m.recv_match(type=["SIM", *extra])
        if r is None:
            break
        if r.get_type() == "SIM":
            S.append((r.TimeUS / 1e6, r.Lat, r.Lng, r.Alt, r.Yaw))
        else:
            X.append((r.TimeUS / 1e6, r.PN, r.PE, r.Yaw))
    S = np.array(S); lat, lng = S[:, 1], S[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    return np.c_[S[:, 0], N, E, S[:, 3] - S[0, 3], un(S[:, 4])], np.array(X)


def analyse(trial, t, PN, PE, Y, S):
    c0, c1 = cruise_bounds(S[:, 0], S[:, 2], S[:, 1])
    tk = S[np.argmax(S[:, 3] > 0.3), 0]                                   # take-off: SIM height +0.3 m
    Et = np.interp(t, S[:, 0], S[:, 2]); eE = PE - Et                    # East error from the spawn origin
    yerr = un(Y) - np.interp(t, S[:, 0], S[:, 4]); yerr = (yerr + 180) % 360 - 180
    w = (t >= c0) & (t <= c1)
    hit = np.where(w & (np.abs(eE) >= 9.58))[0]
    out = {"trial": trial, "cruise": [float(c0), float(c1)],
           "yaw_err_at_takeoff_deg": float(np.interp(tk, t, yerr)), "yaw_err_at_cruise_start_deg": float(np.interp(c0, t, yerr)),
           "east_err_at_cruise_start_m": float(np.interp(c0, t, eE)),
           "contact_s": None if not len(hit) else float(t[hit[0]] - c0),
           "wall": None if not len(hit) else ("west" if eE[hit[0]] > 0 else "east"),   # estimate East of truth -> vehicle steered West
           "east_err_end_m": float(eE[w][-1])}
    print(json.dumps(out)); return out


res = []
for tr, csv in a.replay:
    c = np.genfromtxt(csv, delimiter=",", names=True); S, _ = sim(tr)
    res.append(analyse(tr, c["TimeUS"] / 1e6, c["PN"], c["PE"], c["Yaw"], S))
for tr in a.live:
    S, X = sim(tr, ("XFGO",))
    res.append(analyse(tr + " (live XFGO)", X[:, 0], X[:, 1], X[:, 2], X[:, 3], S))
if a.json:
    json.dump(res, open(a.json, "w"), indent=1)
