#!/usr/bin/env python3
"""Does the three-way table's evo `-a` ATE include the pre-arm/climb/land phases?
Recompute each estimator's evo ATE on FULL recording vs CRUISE-ONLY.

Cruise window is the SAME definition the apparatus metrics already use
(ukf_replay.py:120-135 / fgo_replay.py:113): GT ground speed > 0.30 m/s after a
25-sample boxcar, largest contiguous run.

EKF3 has no TUM on disk (the table's EKF3 column was produced ad hoc), so it is
rebuilt here from `XKF1` (est) and `SIM` (ref) in the .BIN, matching METHODOLOGY's
"EKF3 from XKF1-vs-SIM". Running full-window as well tests which window the
published 4.97 / 23.41 / 37.79 came from.

Note: `-a` re-solves the Umeyama alignment on whatever span it is given, so the
cruise-only number is NOT a sub-average of the full-window one — the transform
itself changes.

Read-only. Usage (any python with numpy + pymavlink): python3 plots/ate_window_check.py
"""
import os, re, math, subprocess
import numpy as np
from pymavlink import mavutil

HOME = os.path.expanduser("~")
EVO = f"{HOME}/venv-evo/bin/evo_ape"
TMP = "/tmp/claude-1000/-home-makerspace/4c2a355b-a793-40b6-80a5-525fbe537f7b/scratchpad/ate_win"
os.makedirs(TMP, exist_ok=True)
CONDS = {"textured": [f"dsn_tex_r{i}" for i in (1, 2, 3)],
         "transition": [f"dsn_trans_r{i}" for i in (1, 2, 3)],
         "blank": [f"dsn_blank_r{i}" for i in (1, 2, 3)]}


def read_tum(p):
    return np.loadtxt(p)


def write_tum(p, a):
    np.savetxt(p, a, fmt="%.6f")


def cruise_bounds(t, x, y):
    """GT-speed cruise window, identical rule to ukf_replay.py."""
    sp = np.convolve(np.hypot(np.gradient(x), np.gradient(y)) / np.gradient(t),
                     np.ones(25) / 25, mode="same")
    cr = sp > 0.30
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
    return t[bi], t[bj - 1]


def evo(ref, est, aligned):
    cmd = [EVO, "tum", ref, est, "--t_max_diff", "0.05", "--no_warnings"]
    if aligned:
        cmd.append("-a")
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    m = re.search(r'rmse\s+([\d.]+)', out)
    return float(m.group(1)) if m else float('nan')


def ekf3_tums(trial):
    """est = XKF1 (NED), ref = SIM (lat/lng/alt -> local NED). Same clock (TimeUS)."""
    m = mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{trial}/ardupilot.bin"))
    xk, sim = [], []
    while True:
        x = m.recv_match(type=['XKF1', 'SIM'])
        if x is None:
            break
        if x.get_type() == 'XKF1':
            if getattr(x, 'C', 0) != 0:
                continue
            xk.append((x.TimeUS / 1e6, x.PN, x.PE, x.PD))
        else:
            sim.append((x.TimeUS / 1e6, x.Lat, x.Lng, x.Alt))
    xk = np.array(xk); sim = np.array(sim)
    lat, lng = sim[:, 1].copy(), sim[:, 2].copy()
    if np.abs(lat).max() > 1000:
        lat /= 1e7; lng /= 1e7
    R = 6378137.0
    gN = np.radians(lat - lat[0]) * R
    gE = np.radians(lng - lng[0]) * R * math.cos(math.radians(lat.mean()))
    gD = -(sim[:, 3] - sim[0, 3])
    q = np.tile([0., 0., 0., 1.], (len(sim), 1))
    ref = np.c_[sim[:, 0], gN, gE, gD, q]
    est = np.c_[xk[:, 0], xk[:, 1], xk[:, 2], xk[:, 3], np.tile([0., 0., 0., 1.], (len(xk), 1))]
    return ref, est


rows = []
for cond, trials in CONDS.items():
    for tr in trials:
        d = os.path.expanduser(f"~/thesis_data/trials/{tr}")
        out = {'trial': tr, 'cond': cond}
        for name, ref_p, est_p in [
                ('UKF', f"{d}/ukf/ground_truth.tum", f"{d}/ukf/ukf_traj.tum"),
                ('FGO', f"{d}/fgo/ground_truth.tum", f"{d}/fgo/fgo_traj.tum")]:
            ref, est = read_tum(ref_p), read_tum(est_p)
            t0, t1 = cruise_bounds(ref[:, 0], ref[:, 1], ref[:, 2])
            rc = f"{TMP}/{tr}_{name}_ref.tum"; ec = f"{TMP}/{tr}_{name}_est.tum"
            write_tum(rc, ref[(ref[:, 0] >= t0) & (ref[:, 0] <= t1)])
            write_tum(ec, est[(est[:, 0] >= t0) & (est[:, 0] <= t1)])
            out[f'{name}_full_a'] = evo(ref_p, est_p, True)
            out[f'{name}_cru_a'] = evo(rc, ec, True)
            out[f'{name}_win'] = (t0, t1)
        ref, est = ekf3_tums(tr)
        rf = f"{TMP}/{tr}_EKF3_ref.tum"; ef = f"{TMP}/{tr}_EKF3_est.tum"
        write_tum(rf, ref); write_tum(ef, est)
        t0, t1 = cruise_bounds(ref[:, 0], ref[:, 1], ref[:, 2])
        rc = f"{TMP}/{tr}_EKF3_refc.tum"; ec = f"{TMP}/{tr}_EKF3_estc.tum"
        write_tum(rc, ref[(ref[:, 0] >= t0) & (ref[:, 0] <= t1)])
        write_tum(ec, est[(est[:, 0] >= t0) & (est[:, 0] <= t1)])
        out['EKF3_full_a'] = evo(rf, ef, True)
        out['EKF3_cru_a'] = evo(rc, ec, True)
        out['EKF3_win'] = (t0, t1)
        rows.append(out)
        print(f"  {tr}: EKF3 {out['EKF3_full_a']:.2f}/{out['EKF3_cru_a']:.2f}  "
              f"UKF {out['UKF_full_a']:.2f}/{out['UKF_cru_a']:.2f}  "
              f"FGO {out['FGO_full_a']:.2f}/{out['FGO_cru_a']:.2f}  "
              f"cruise=[{out['EKF3_win'][0]:.0f},{out['EKF3_win'][1]:.0f}]s", flush=True)

print(f"\n=== evo `-a` RMSE (m): FULL recording vs CRUISE-only ===")
print(f"{'condition':12}{'EKF3 full':>10}{'EKF3 cru':>10}{'UKF full':>10}{'UKF cru':>10}{'FGO full':>10}{'FGO cru':>10}")
for cond in CONDS:
    rs = [r for r in rows if r['cond'] == cond]
    f = lambda k: np.mean([r[k] for r in rs])
    print(f"{cond:12}{f('EKF3_full_a'):10.2f}{f('EKF3_cru_a'):10.2f}"
          f"{f('UKF_full_a'):10.2f}{f('UKF_cru_a'):10.2f}"
          f"{f('FGO_full_a'):10.2f}{f('FGO_cru_a'):10.2f}")
print("\npublished table (evo -a): textured 4.97 / 16.44 / 4.87 | transition 23.41 / 27.11 / 24.55"
      " | blank 37.79 / 39.84 / 43.28")
print(f"cruise windows (UKF/FGO GT clock): " +
      ", ".join(f"{r['trial']}=[{r['UKF_win'][0]:.0f},{r['UKF_win'][1]:.0f}]" for r in rows[:3]))
