#!/usr/bin/env python3
"""D9 precondition P3 (PRE-REGISTERED, METHODOLOGY "D9 precondition P3"): the UKF backend ground test
(AHRS_EKF_TYPE 12, armed hold, no take-off). G1 config from PARM; G2 armed; G3 ATT == XUKO (and != XKF1
where they differ by > 0.3 deg); G4 on-ground stability over the armed hold; G5 disarmed, no failsafe /
crash text. Usage (venv-ardupilot): python3 eval/ukf_p3_check.py BIN [--json OUT]"""
import argparse, json
import numpy as np
from pymavlink import mavutil
ap = argparse.ArgumentParser(); ap.add_argument("bin"); ap.add_argument("--json")
ap.add_argument("--heading", action="store_true", help="D17 V3 (PRE-REGISTERED): G1 adds AHRS_UKF_EXTYAW 1 and VISO_TYPE 1; "
                "G4 yaw = error vs SIM over the hold p95 <= 1.0, max <= 2.0 deg, plus >= 95%% of XUKH headings accepted")
a = ap.parse_args()
m = mavutil.mavlink_connection(a.bin)
P, ARM, ATT, O, X, S, SIM, MSG, HD = {}, [], [], [], [], [], [], [], []
while True:
    r = m.recv_match(type=["PARM", "ARM", "ATT", "XUKO", "XKF1", "XUKS", "SIM", "MSG", "ERR", "XUKH"])
    if r is None:
        break
    t = r.get_type(); ts = getattr(r, "TimeUS", 0) / 1e6
    if t == "PARM": P[r.Name] = r.Value
    elif t == "ARM": ARM.append((ts, r.ArmState))
    elif t == "ATT": ATT.append((ts, r.Roll, r.Pitch, r.Yaw))
    elif t == "XUKO": O.append((ts, r.PN, r.PE, r.PD, r.Roll, r.Pitch, r.Yaw, r.EvO))
    elif t == "XKF1" and r.C == 0: X.append((ts, r.Roll, r.Pitch, r.Yaw))
    elif t == "XUKS": S.append((ts, r.H))
    elif t == "SIM": SIM.append((ts, r.Alt, r.Yaw))
    elif t == "XUKH": HD.append((ts, r.Acc, r.Algn))
    elif t == "MSG": MSG.append((ts, r.Message))
    elif t == "ERR": MSG.append((ts, f"ERR subsys {r.Subsys} code {r.ECode}"))
ATT, O, X, S, SIM = map(np.array, (ATT, O, X, S, SIM))
out = {}
out["G1"] = {"AHRS_EKF_TYPE": P.get("AHRS_EKF_TYPE"), "AHRS_UKF_ENABLE": P.get("AHRS_UKF_ENABLE"),
             "pass": P.get("AHRS_EKF_TYPE") == 12 and P.get("AHRS_UKF_ENABLE") == 1}
if a.heading:
    out["G1"].update({"AHRS_UKF_EXTYAW": P.get("AHRS_UKF_EXTYAW"), "VISO_TYPE": P.get("VISO_TYPE")})
    out["G1"]["pass"] = out["G1"]["pass"] and P.get("AHRS_UKF_EXTYAW") == 1 and P.get("VISO_TYPE") == 1
arms = [t for t, s in ARM if s == 1]; disarms = [t for t, s in ARM if s == 0 and arms and t > arms[0]]
out["G2"] = {"armed_at": arms[0] if arms else None, "pass": bool(arms)}
if arms:
    t0 = arms[0]; t1 = disarms[0] if disarms else O[-1, 0]
    w = lambda T: (T[:, 0] >= t0 + 0.5) & (T[:, 0] <= t1 - 0.5)
    wa = w(ATT)
    wrap = lambda d: (d + 180) % 360 - 180
    oi = lambda k, tt: np.interp(tt, O[:, 0], np.degrees(np.unwrap(np.radians(O[:, k]))) if k == 6 else O[:, k])
    xi = lambda k, tt: np.interp(tt, X[:, 0], np.degrees(np.unwrap(np.radians(X[:, k]))) if k == 3 else X[:, k])
    tt = ATT[wa, 0]
    d_ukf = np.abs(np.c_[ATT[wa, 1] - oi(4, tt), ATT[wa, 2] - oi(5, tt), wrap(ATT[wa, 3] - oi(6, tt))])
    d_ekf = np.abs(np.c_[ATT[wa, 1] - xi(1, tt), ATT[wa, 2] - xi(2, tt), wrap(ATT[wa, 3] - xi(3, tt))])
    d_ue = np.abs(np.c_[oi(4, tt) - xi(1, tt), oi(5, tt) - xi(2, tt), wrap(oi(6, tt) - xi(3, tt))])
    disc = d_ue.max(axis=1) > 0.3
    g3 = {"att_vs_xuko_p95_deg": float(np.percentile(d_ukf.max(axis=1), 95)), "n": int(wa.sum()),
          "n_discriminating": int(disc.sum())}
    if disc.any():
        g3["att_vs_xkf1_median_where_discriminating_deg"] = float(np.median(d_ekf[disc].max(axis=1)))
        g3["att_closer_to_ukf_share"] = float(np.mean(d_ukf[disc].max(axis=1) < d_ekf[disc].max(axis=1)))
    g3["pass"] = g3["att_vs_xuko_p95_deg"] <= 0.1 and (not disc.any() or g3["att_closer_to_ukf_share"] >= 0.95)
    g3["discriminating"] = bool(disc.any())
    out["G3"] = g3
    wo = (O[:, 0] >= t0) & (O[:, 0] <= t1); Oh = O[wo]
    dne = np.hypot(Oh[:, 1] - Oh[0, 1], Oh[:, 2] - Oh[0, 2]).max()
    dyaw = np.abs(wrap(Oh[:, 6] - Oh[0, 6])).max()
    truth_pd = -(np.interp(Oh[:, 0], SIM[:, 0], SIM[:, 1]) - SIM[0, 1] + 0.20)     # rest base_link height 0.20 m (range 0.080 + 0.12)
    herr = np.abs(Oh[:, 3] - truth_pd)
    hs = S[(S[:, 0] >= t0) & (S[:, 0] <= t1)]
    out["G4"] = {"hold_s": float(t1 - t0), "max_dNE_m": float(dne), "max_dyaw_deg": float(dyaw),
                 "height_err_end_m": float(herr[-1]), "height_err_growth_m": float(herr.max() - herr[0]),
                 "healthy_all": bool(hs[:, 1].min() == 1) if len(hs) else None, "EvO_max": int(Oh[:, 7].max())}
    g = out["G4"]
    if a.heading:
        ys = np.degrees(np.unwrap(np.radians(SIM[:, 2])))
        ye = np.abs(wrap(np.degrees(np.unwrap(np.radians(Oh[:, 6]))) - np.interp(Oh[:, 0], SIM[:, 0], ys)))
        HDa = np.array(HD); wh = (HDa[:, 0] >= t0) & (HDa[:, 0] <= t1) & (HDa[:, 2] == 1) if len(HDa) else None
        g.update({"yaw_err_p95_deg": float(np.percentile(ye, 95)), "yaw_err_max_deg": float(ye.max()),
                  "headings_in_hold": int(wh.sum()) if wh is not None else 0,
                  "headings_accepted_pct": float(100 * HDa[wh, 1].mean()) if wh is not None and wh.any() else None})
        yaw_ok = g["yaw_err_p95_deg"] <= 1.0 and g["yaw_err_max_deg"] <= 2.0 and (g["headings_accepted_pct"] or 0) >= 95.0
    else:
        yaw_ok = g["max_dyaw_deg"] <= 1.0
    g["pass"] = (g["max_dNE_m"] <= 0.10 and yaw_ok and g["height_err_end_m"] <= 0.10
                 and g["height_err_growth_m"] <= 0.05 and g["healthy_all"] and g["EvO_max"] == 0)
# "PrecLand: Failsafe Measures" is an INFO message from the precision-landing state machine printed in every
# landing (also in the EKF3 datasets, e.g. dsn_tex_r2 at 334.5 s): not a vehicle failsafe, excluded.
bad = [msg for t, msg in MSG if "PrecLand" not in str(msg) and any(k in str(msg).lower() for k in ("failsafe", "crash", "ekf variance", "ukf unhealthy", "not initialised", "error"))]
out["G5"] = {"disarmed_at": disarms[0] if disarms else None, "bad_messages": bad[:20], "pass": bool(disarms) and not bad}
out["messages"] = [f"{t:.1f} {msg}" for t, msg in MSG][:60]
out["PASS"] = all(out[k]["pass"] for k in ("G1", "G2", "G3", "G4", "G5") if k in out) and "G4" in out
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
