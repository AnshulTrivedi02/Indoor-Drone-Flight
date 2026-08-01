#!/usr/bin/env python3
"""Degraded-sensing FAILURE analysis (nomag dsn_*, all three estimators). Blank and
transition are not accuracy comparisons (all diverge) — report failure metrics:
final displacement magnitude vs true travel (freeze vs dead-reckon), divergence onset
(true-y where the estimate departs GT by >15 m), and the textured per-repeat spread.
EKF3 from XKF1/SIM (.BIN); UKF/FGO from their TUM trajectories. venv-ardupilot."""
import os, math
import numpy as np
from pymavlink import mavutil

HOME = os.path.expanduser("~")
COND = {"tex": [f"dsn_tex_r{i}" for i in (1, 2, 3)],
        "trans": [f"dsn_trans_r{i}" for i in (1, 2, 3)],
        "blank": [f"dsn_blank_r{i}" for i in (1, 2, 3)]}


def cruise_win(dN, dE, t):
    dt = np.gradient(t)
    spd = np.convolve(np.hypot(np.gradient(dN)/dt, np.gradient(dE)/dt), np.ones(25)/25, mode="same")
    cr = spd > 0.30; bi = bj = 0; i = 0
    while i < len(cr):
        if cr[i]:
            j = i
            while j < len(cr) and cr[j]:
                j += 1
            if j-i > bj-bi:
                bi, bj = i, j
            i = j
        else:
            i += 1
    return bi, bj


def analyse(t, eN, eE, gN, gE):
    """t sorted; e*=estimate N/E, g*=GT N/E (same length/time). Returns dict."""
    bi, bj = cruise_win(gN, gE, t)
    w = slice(bi, bj)
    dE_est = eE[w]-eE[bi]; dN_est = eN[w]-eN[bi]
    dE_gt = gE[w]-gE[bi]; dN_gt = gN[w]-gN[bi]
    d_est = np.hypot(dE_est, dN_est); d_gt = np.hypot(dE_gt, dN_gt)
    true_travel = d_gt[-1]
    final_disp = d_est[-1]
    gN_y = gN[w]-gN[bi]                       # GT along-corridor position (from cruise start)
    # divergence onset: first sustained |d_est - d_gt| > 15 m
    dev = np.abs(d_est - d_gt)
    onset_i = None
    for k in range(len(dev)):
        if dev[k] > 15.0 and np.median(dev[k:min(k+40, len(dev))]) > 15.0:
            onset_i = k; break
    onset_y = float(gN_y[onset_i]) if onset_i is not None else None
    return dict(true=true_travel, final=final_disp, ratio=final_disp/true_travel,
                onset_y=onset_y, tw=t[w])


def load_ekf3(tr):
    m = mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{tr}/ardupilot.bin"))
    xk = {'t': [], 'PN': [], 'PE': []}; sim = {'t': [], 'Lat': [], 'Lng': []}
    while True:
        x = m.recv_match(type=['XKF1', 'SIM'])
        if x is None:
            break
        T = x.get_type()
        if T == 'XKF1' and getattr(x, 'C', 0) == 0:
            xk['t'].append(x.TimeUS); xk['PN'].append(x.PN); xk['PE'].append(x.PE)
        elif T == 'SIM':
            sim['t'].append(x.TimeUS); sim['Lat'].append(x.Lat); sim['Lng'].append(x.Lng)
    for d in (xk, sim):
        for k in d:
            d[k] = np.asarray(d[k], float)
    t = xk['t']/1e6
    lat = sim['Lat'].copy(); lng = sim['Lng'].copy()
    if abs(lat).max() > 1000:
        lat /= 1e7; lng /= 1e7
    R = 6378137.0; la0 = math.radians(lat.mean())
    sN = np.radians(lat-lat[0])*R; sE = np.radians(lng-lng[0])*R*math.cos(la0)
    gN = np.interp(t, sim['t']/1e6, sN); gE = np.interp(t, sim['t']/1e6, sE)
    return analyse(t, xk['PN'], xk['PE'], gN, gE), (t, xk['PN'], xk['PE'], gN, gE)


def load_tum(tr, est):
    d = os.path.expanduser(f"~/thesis_data/trials/{tr}/{est}")
    a = np.loadtxt(f"{d}/{est}_traj.tum"); g = np.loadtxt(f"{d}/ground_truth.tum")
    t = a[:, 0]; eE = a[:, 1]; eN = a[:, 2]
    gE = np.interp(t, g[:, 0], g[:, 1]); gN = np.interp(t, g[:, 0], g[:, 2])
    return analyse(t, eN, eE, gN, gE)


def umeyama_rmse(eN, eE, gN, gE):
    """2D SE(2) aligned RMSE (evo -a proxy) for EKF3 XKF1 vs SIM over a stride."""
    P = np.vstack([eE, eN]); Q = np.vstack([gE, gN])
    mp = P.mean(1, keepdims=True); mq = Q.mean(1, keepdims=True)
    Pc = P-mp; Qc = Q-mq
    U, _, Vt = np.linalg.svd(Qc @ Pc.T)
    S = np.diag([1, np.linalg.det(U @ Vt)])
    Rm = U @ S @ Vt
    err = Q - (Rm @ Pc + mq)
    return float(np.sqrt(np.mean(np.sum(err**2, 0))))


print("===== FINAL DISPLACEMENT MAGNITUDE vs true travel (freeze<1 / track~1 / dead-reckon>1) =====")
print(f"{'cond':6}{'estimator':10}{'|disp|':>9}{'true':>7}{'ratio':>7}{'onset_y(m)':>12}")
tex_e3 = []
for cond, trials in COND.items():
    for est in ('ekf3', 'ukf', 'fgo'):
        rs = []
        for tr in trials:
            if est == 'ekf3':
                r, raw = load_ekf3(tr)
                if cond == 'tex':
                    t, PN, PE, gN, gE = raw
                    bi, bj = cruise_win(gN, gE, t); w = slice(bi, bj)
                    tex_e3.append(umeyama_rmse(PN[w], PE[w], gN[w], gE[w]))
            else:
                r = load_tum(tr, est)
            rs.append(r)
        rat = np.mean([r['ratio'] for r in rs])
        fin = np.mean([r['final'] for r in rs]); tru = np.mean([r['true'] for r in rs])
        ons = [r['onset_y'] for r in rs if r['onset_y'] is not None]
        onstr = f"{np.mean(ons):.0f} (n={len(ons)})" if ons else "no divergence"
        print(f"{cond:6}{est:10}{fin:>9.0f}{tru:>7.0f}{rat:>7.2f}{onstr:>12}")
    print()

print("===== TEXTURED per-repeat evo -a (all three) =====")
print(f"  EKF3 (SE2-aligned XKF1 vs SIM): {[round(v,2) for v in tex_e3]}  mean={np.mean(tex_e3):.2f} range={max(tex_e3)-min(tex_e3):.2f}")
import json
res = json.load(open(f"{HOME}/thesis_ws/plots/rerun_results.json"))
for est in ('ukf', 'fgo'):
    v = [res[t][est]['ate_a'] for t in COND['tex']]
    print(f"  {est.upper():4} (evo -a): {[round(x,2) for x in v]}  mean={np.mean(v):.2f} range={max(v)-min(v):.2f}")
