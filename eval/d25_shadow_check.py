#!/usr/bin/env python3
"""D25 confirming shadow (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION: D25 confirming shadow run"):
C1 XFGO.OV = 1 at every sample from the first received state (XFGI) to disarm (= the FGO pre-arm check,
   healthy() = output_valid(), could not have refused "FGO invalid or stale");
C2 0 negative-age samples (1e6 < Age < UINT32_MAX) in the whole log;
C3 first state >= 10 s (sim) after the node's first /imu/time_ref (clock-map diagnostics), and before arming.
Also: the start-up raw offsets (first 20 s) and the outlier counters.
Usage (venv-ardupilot + numpy): python3 eval/d25_shadow_check.py TRIAL [--json OUT]"""
import argparse, json, os
import numpy as np
from pymavlink import mavutil
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
m = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); O, I, ARM = [], [], []
while True:
    r = m.recv_match(type=["XFGO", "XFGI", "ARM"])
    if r is None:
        break
    t = r.TimeUS / 1e6
    if r.get_type() == "XFGO": O.append((t, r.OV, r.Age))
    elif r.get_type() == "XFGI": I.append((t, r.Tv / 1e3))
    else: ARM.append((t, r.ArmState))
O, I = np.array(O), np.array(I)
arm = [t for t, s in ARM if s == 1]; dis = [t for t, s in ARM if s == 0 and arm and t > arm[0]]
t_first = float(I[0, 0]); t_dis = dis[0] if dis else float(O[-1, 0])
w = (O[:, 0] >= t_first + 0.04) & (O[:, 0] <= t_dis)            # first XFGO log after the first state
neg = (O[:, 2] > 1e6) & (O[:, 2] < 4294967295)
out = {"trial": a.trial, "first_state_s": t_first, "armed_s": arm[0] if arm else None, "disarm_s": t_dis}
out["C1"] = {"n": int(w.sum()), "ov0_after_first_state": int((O[w, 1] == 0).sum()),
             "ov0_times": [round(float(x), 2) for x in O[w][O[w, 1] == 0, 0][:10]], "pass": bool(w.any() and (O[w, 1] == 1).all())}
out["C2"] = {"negative_age_samples": int(neg.sum()), "min_ms": int(O[neg, 2].min() - 2**32) if neg.any() else None, "pass": bool(not neg.any())}
cm = np.load(f"{D}/fgo_node_stats_clockmap.npz")
t0 = float(cm["tref_t0"])
# C3 as pre-registered: the first state ARRIVES (XFGI TimeUS) >= 10 s after the first /imu/time_ref. (First version,
# a checker bug: it used the state's own stamp Tv, which lags the settle instant by the horizon + step, ~0.1 s.)
out["C3"] = {"first_time_ref_header_s": t0, "first_state_arrival_s": t_first, "first_state_tv_s": float(I[0, 1]),
             "settle_s": float(t_first - t0), "first_state_stamp_minus_t0_s": float(I[0, 1] - t0),
             "pass": bool(t_first - t0 >= 10.0 and (not arm or t_first < arm[0]))}
e = cm["early"]
out["diag"] = {"n_unsettled_queries": int(cm["n_unsettled"]), "maps_with_outliers": int(cm["n_maps_with_outliers"]),
               "max_outliers_in_window": int(cm["n_outliers_max"])}
if len(e):
    med = np.median(e[:, 1])
    out["diag"].update({"early_offsets_ms": {"first_5": [round(1e3 * x, 1) for x in e[:5, 1]], "min": 1e3 * float(e[:, 1].min()),
                                             "median": 1e3 * float(med), "max": 1e3 * float(e[:, 1].max())},
                        "early_low_outliers_gt20ms": int((e[:, 1] < med - 0.020).sum()),
                        "early_low_outlier_times_s": [round(float(x - t0), 3) for x in e[e[:, 1] < med - 0.020, 0][:10]]})
out["PASS"] = bool(out["C1"]["pass"] and out["C2"]["pass"] and out["C3"]["pass"])
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
