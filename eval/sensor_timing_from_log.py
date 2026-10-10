#!/usr/bin/env python3
"""Rung 1: measure each sensor's RATE and DELAY from a dataflash log, for pre-registering the UKF/FGO capture-time
rule (ruling 2026-10-10 item 2: "the best estimate of the true capture time, decided from the real sensor's MEASURED
rate and delay ... pre-registered before any scoring"). The output values are what eval/bin2fgo.py takes as
--flow-delay-ms / --range-delay-ms. Nothing here is fed to an estimator.

  python3 eval/sensor_timing_from_log.py <log.BIN> [--truth sim2 | --truth-tum <mocap_on_FC_clock.tum>]
                                         [--window T0 T1] [--json out.json]

FLOW delay (no truth needed): a flow sensor's raw rate contains the body rotation, flowX ~ +w_x, flowY ~ +w_y (FRD;
ArduPilot's flow convention, a RH rotation gives a positive rate). For a trial lag L, the RAW RISI gyro (instance 0)
is averaged over each flow record's interval shifted by L, (a_{k-1} - L, a_k - L], a = OF.TimeUS (FC arrival), from
the cumulative RISI delta angle. Both series are high-passed (minus a centred ~1 s moving mean, which removes most of
the translational flow) and correlated; the L with the highest mean correlation over the excited axes is
  d_flow = arrival minus the END of the integration interval  (bin2fgo.py's definition).
Rotation excitation is needed: the sync wiggles / climb cycles of the flight profile, or --window around them. The
fitted gain and sign are reported per axis (sign must be +; the magnitude is a known open item, not a timing input).

RANGE delay (needs truth): range(t) against truth height above the floor minus the rangefinder lever,
h(t - L) = z_truth(t - L) - RNGFND_POS_Z (small-tilt), over samples with |dh/dt| > 0.1 m/s (climbs/descents; a hover
cannot show a delay). Truth: SIM2 on a SITL log (same clock), or a mocap TUM already mapped to the FC clock
(eval/mocap_align.py). Range rate from the spacing of consecutive RRNI changes (the backend update period).

IMU: frame rate, DVDT vs frame spacing, gaps (the IMU is the time base; no delay is estimated for it).
Validated on the SITL log cl_a_tex_half against the bag's capture stamps (eval/bin2fgo_sitl_check.py)."""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bin2fgo import read_bin


def hp(x, n):
    k = np.ones(n) / n
    return x - np.convolve(x, k, mode="same")


def flow_delay(frames_t, risi, of, lags, win=None, n_hp=31):
    t = risi[:, 0]; da = risi[:, 4:7]
    th = np.vstack([np.zeros(3), np.cumsum(da, axis=0)])                 # cumulative angle at frame ends (FRD)
    tt = np.concatenate([[t[0] - risi[0, 8]], t])
    a = of[:, 0]; fxy = of[:, 2:4]; q = of[:, 1]
    T = np.median(np.diff(a))
    use = np.ones(len(a), bool); use[0] = False
    use[1:] &= (np.diff(a) < 2.5 * T) & (q[1:] > 0) & (q[:-1] > 0)
    if win is not None:
        use &= (a >= win[0]) & (a <= win[1])
    out = []
    for L in lags:
        e1 = a - L; e0 = np.concatenate([[np.nan], a[:-1]]) - L
        ok = use & (e0 >= tt[0]) & (e1 <= tt[-1])
        th1 = np.column_stack([np.interp(e1, tt, th[:, i]) for i in range(2)])
        th0 = np.column_stack([np.interp(np.nan_to_num(e0), tt, th[:, i]) for i in range(2)])
        w = (th1 - th0) / (e1 - np.nan_to_num(e0))[:, None]
        cs, gs = [], []
        for ax in range(2):
            x = hp(w[ok, ax], n_hp); y = hp(fxy[ok, ax], n_hp)
            cs.append(float(np.corrcoef(x, y)[0, 1])); gs.append(float(np.dot(x, y) / np.dot(x, x)))
        out.append((L, cs, gs, float(np.std(hp(w[ok, 0], n_hp))), float(np.std(hp(w[ok, 1], n_hp))), int(ok.sum())))
    return out, T


def refine(xs, ys):
    i = int(np.argmax(ys))
    if 0 < i < len(ys) - 1:
        y0, y1, y2 = ys[i - 1], ys[i], ys[i + 1]
        den = y0 - 2 * y1 + y2
        if den < 0:
            return float(xs[i] + 0.5 * (y0 - y2) / den * (xs[1] - xs[0])), i
    return float(xs[i]), i


def range_delay(rrni_t, rrni_d, rrni_s, T_r, t_end, truth_t, truth_z, lever, lags, win=None):
    rt, rd = [], []
    for i in range(len(rrni_t)):
        t0 = rrni_t[i]; t1 = rrni_t[i + 1] if i + 1 < len(rrni_t) else t_end
        if rrni_s[i] != 4:
            continue
        k = np.arange(t0, t1 - 1e-9, T_r); rt.append(k); rd.append(np.full(len(k), rrni_d[i]))
    rt = np.concatenate(rt); rd = np.concatenate(rd)
    h = truth_z - lever
    dh = np.gradient(h, truth_t)
    moving = np.abs(np.interp(rt, truth_t, dh)) > 0.1
    if win is not None:
        moving &= (rt >= win[0]) & (rt <= win[1])
    res = []
    for L in lags:
        e = rd - np.interp(rt - L, truth_t, h)
        em = e[moving]; em = em[np.abs(em) < 0.3]          # drop dropouts (single near-zero readings, Known Issue #5)
        res.append((L, float(np.sqrt(np.mean(em ** 2))) if len(em) else np.inf, float(np.sqrt(np.mean(e ** 2))), int(len(em))))
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("bin")
    ap.add_argument("--truth", default="none", help="sim2 | none")
    ap.add_argument("--truth-tum", default=None, help="mocap TUM on the FC clock (t x y z ...), z up, metres")
    ap.add_argument("--window", nargs=2, type=float, default=None, help="flow-delay fit window on the FC clock (s)")
    ap.add_argument("--range-window", nargs=2, type=float, default=None, help="range-delay fit window (FC clock, s)")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    P, frames, risi, of, rofh, rrni, rrnh, arm, dsf_dp, sim2 = read_bin(a.bin, 0, a.truth == "sim2")
    out = {"bin": os.path.abspath(a.bin)}
    df = np.diff(frames)
    out["imu"] = {"frame_period_ms_median": 1e3 * float(np.median(df)), "frame_rate_hz_mean": float(1 / np.mean(df)),
                  "dvdt_minus_frame_dt_ms_p99_abs": 1e3 * float(np.percentile(np.abs(risi[1:, 7] - np.diff(risi[:, 0])), 99)),
                  "n_gaps_gt_2p5x": int((df > 2.5 * np.median(df)).sum()), "dsf_dropped_blocks": int(dsf_dp)}
    lags = np.arange(-0.050, 0.2005, 0.001)
    fd, T = flow_delay(frames, risi, of, lags, a.window)
    # per axis: peak lag and correlation. In flight the PITCH axis (y) is contaminated by translation (pitching
    # accelerates the vehicle, so v_fwd/h tracks the integrated pitch rate), which biases its lag; on cl_a_tex_half the
    # x (roll) axis reproduced the true SITL delay to < 1 ms and y did not (handover). Rule: if the two axes agree within
    # 5 ms, the corr-weighted mean; otherwise the axis with the higher peak correlation, flagged. Pre-register from the
    # sync wiggles (rotation in place, --window), where translation is small on both axes.
    ax_L, ax_c = [], []
    for ax in range(2):
        c_ax = np.array([c[ax] for _, c, *_ in fd]); L_ax, i_ax = refine(lags, c_ax)
        ax_L.append(L_ax); ax_c.append(float(c_ax[i_ax]))
    agree = abs(ax_L[0] - ax_L[1]) <= 0.005
    if agree:
        Lb = float(np.dot(ax_L, ax_c) / np.sum(ax_c))
    else:
        Lb = ax_L[int(np.argmax(ax_c))]
    ib = int(np.argmin(np.abs(lags - Lb)))
    out["flow"] = {"rate_hz_median": float(1 / T), "interarrival_ms_p5_p50_p95": [1e3 * float(np.percentile(np.diff(of[:, 0]), q)) for q in (5, 50, 95)],
                   "delay_end_ms": 1e3 * Lb, "delay_per_axis_ms_xy": [1e3 * x for x in ax_L],
                   "peak_corr_per_axis_xy": ax_c, "axes_agree_within_5ms": bool(agree),
                   "corr_xy_at_best": fd[ib][1], "gain_xy_at_best": fd[ib][2], "hp_gyro_std_xy_radps": [fd[ib][3], fd[ib][4]],
                   "n_used": fd[ib][5], "corr_xy_at_zero_lag": fd[int(np.argmin(np.abs(lags)))][1],
                   "sign_ok": bool(all(g > 0 for g in fd[ib][2])),
                   "definition": "arrival (OF.TimeUS) minus the END of the flow integration interval",
                   "EK3_FLOW_DELAY_parm_ms": P.get("EK3_FLOW_DELAY")}
    # range
    R = rrni[rrni[:, 4] == 25]
    ch_t, ch_d, ch_s = R[:, 0], R[:, 2], R[:, 3].astype(int)
    d = np.diff(ch_t[ch_s == 4]); d = d[(d > 0.004) & (d < 0.3)]
    T_r = float(np.median(d)) if len(d) else None
    out["range"] = {"update_period_ms_from_changes": None if T_r is None else 1e3 * T_r, "n_changes": int(len(R))}
    truth = None
    if a.truth == "sim2" and len(sim2):
        truth = (sim2[:, 0], sim2[:, 3])
    elif a.truth_tum:
        M = np.loadtxt(a.truth_tum); truth = (M[:, 0], M[:, 3])
    if truth is not None and T_r is not None:
        n = int(R[0, 1]) + 1
        lever = P.get(f"RNGFND{n}_POS_Z", 0.0)
        rlags = np.arange(-0.050, 0.3005, 0.001)
        rr = range_delay(ch_t, ch_d, ch_s, T_r, float(frames[-1]), truth[0], truth[1], lever, rlags, a.range_window)
        rms = np.array([x[1] for x in rr]); ib = int(np.argmin(rms))
        out["range"].update({"delay_ms": 1e3 * float(rlags[ib]), "rms_moving_at_best_m": float(rms[ib]),
                             "rms_moving_at_zero_m": float(rr[int(np.argmin(np.abs(rlags)))][1]),
                             "n_moving_samples": rr[ib][3], "truth": "SIM2" if a.truth == "sim2" else a.truth_tum,
                             "definition": "emission (RRNI change frame, held at the update period) minus measurement"})
    else:
        out["range"]["delay_ms"] = None
        out["range"]["note"] = "range delay needs truth (--truth sim2 on SITL, --truth-tum mocap on the FC clock)"
    print(json.dumps(out, indent=1))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
