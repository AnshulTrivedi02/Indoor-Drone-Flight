#!/usr/bin/env python3
"""Validation of the mocap <-> FC time sync on the 400 Hz RISI records (rung-1 item R8).

  synthetic  A fully synthetic flight with a KNOWN clock map (epoch-sized offset + a rate drift), sync wiggles at both
             ends, mocap at 120 Hz with orientation/position noise and dropouts, FC gyro as RISI-like 400 Hz deltas
             (stamped by the same rule as read_fc). Several seeds; the recovered offset and rate are compared with the
             truth.
  sitl       A SITL flight with LOG_REPLAY records, using /ground_truth/pose (Gazebo sim clock, ~110 Hz, with
             orientation) as a stand-in for mocap. The true sim <-> TimeUS map is NOT known, so:
               (a) differential: the GT stamps are re-mapped with a known offset + drift; the change in the recovered
                   map must equal the injection (the unknown base map cancels);
               (b) absolute: the recovered map is compared with two independent references:
                     - SIM2 (SITL physics position, 400 Hz, TimeUS) against the GT position, velocity-matched in the
                       same windows (position-based, independent of the gyro and of attitude);
                     - /imu/time_ref pairs (lower envelope; includes the minimum bridge latency, so it is an upper
                       bound on sim - FC, biased by >= 0);
               (c) the IMU (25 Hz, filtered) path for comparison;
               (d) the 10 Hz SIM self-test of mocap_align, re-run with RISI.
Usage (~/venv-ardupilot):
  python3 eval/mocap_align_validate.py synthetic --out OUT.json [--seeds 8]
  python3 eval/mocap_align_validate.py sitl --trial TRIAL --gt GT.tum --timeref TIMEREF.txt --out OUT.json
    (GT.tum: t x y z qx qy qz qw from /ground_truth/pose; TIMEREF.txt: header_t fc_t from /imu/time_ref.
     Extract them from a SCRATCH copy of a packed bag; the trial directory is only read.)"""
import argparse, json, math, os, sys
import numpy as np
from scipy.spatial.transform import Rotation as Rot, Slerp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mocap_align as MA

EPOCH_OFFSET = 1.7e9 + 0.123456       # s: an epoch-stamped mocap clock (so an inverse-map error cannot hide)
DRIFT_PPM = 150.0


# ---------------------------------------------------------------------------------------------- synthetic
def smooth_noise(rng, n, dt, tau, rms):
    x = rng.normal(0, 1, n); a = math.exp(-dt / tau); y = np.empty(n); y[0] = 0
    for i in range(1, n):
        y[i] = a * y[i - 1] + x[i]
    return rms * y / (np.std(y) + 1e-12)


def synth_flight(seed, T=200.0, boot=12.0, noise=1.0, bias=1.0, wiggle_gain=1.0):
    """Truth on the FC clock tf in [boot, boot + T]. Returns fc dict, mocap dict, truth map, windows."""
    rng = np.random.default_rng(seed); dt = 0.001; tf = np.arange(boot, boot + T, dt); n = len(tf); tau = tf - boot
    w = np.c_[[smooth_noise(rng, n, dt, 0.5, r) for r in (0.15, 0.15, 0.08)]].T          # gentle flight motion
    for c in (10.0, T - 12.0):                                                           # sync wiggles: 6 s, 1-2 Hz
        m = (tau > c - 3) & (tau < c + 3); ph = 2 * math.pi * 1.5 * (tau[m] - c)
        w[m, 0] += wiggle_gain * 1.2 * np.sin(ph); w[m, 1] += wiggle_gain * 0.8 * np.sin(1.3 * ph + 0.7)
        w[m, 2] += wiggle_gain * 0.6 * np.sin(0.7 * ph)
    dq = Rot.from_rotvec(w[:-1] * dt).as_quat()                                         # body rates -> attitude
    q = np.empty((n, 4)); q[0] = (0.0, 0.0, 0.0, 1.0); x0, y0, z0, w0 = q[0]
    for i in range(n - 1):                                                               # q_{i+1} = q_i * dq_i (x,y,z,w)
        x1, y1, z1, w1 = dq[i]
        x0, y0, z0, w0 = (w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1, w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1,
                          w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1, w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1)
        q[i + 1] = (x0, y0, z0, w0)
    q /= np.linalg.norm(q, axis=1)[:, None]
    # position: take-off at tau 20 s to 1.2 m, a 3 m x 2 m rectangle, land at T - 25
    z = np.clip((tau - 20) / 3, 0, 1) * 1.2 * np.clip((T - 25 - tau) / 3, 0, 1)
    x = 1.5 * np.sin(2 * math.pi * np.clip(tau - 30, 0, None) / 60) * (z > 1.1)
    y = 1.0 * (1 - np.cos(2 * math.pi * np.clip(tau - 30, 0, None) / 60)) * (z > 1.1)
    p = np.c_[x, y, z]
    # FC: RISI-like deltas, 2.5 ms frames, DADT 2.5 ms ending at the frame stamp, + bias + noise; stamped at centre
    fr = np.arange(boot + 0.0025, boot + T, 0.0025); dadt = 0.0025
    cum = np.vstack([np.zeros(3), np.cumsum(w[:-1] * dt, axis=0)])
    da = np.c_[[np.interp(fr, tf, cum[:, k]) - np.interp(fr - dadt, tf, cum[:, k]) for k in range(3)]].T
    gyro = da / dadt + bias * np.array([0.01, -0.006, 0.004]) + noise * rng.normal(0, 0.003, da.shape)
    fc = {"gyro": np.c_[fr - dadt / 2, gyro], "gyro_src": "RISI", "imu_instance": 0, "risi_dadt_median_s": dadt,
          "params": {}, "arm": [(boot + 15.0, 1)],
          "rfnd": np.c_[fr[::12], np.interp(fr[::12], tf, z) + 0.05 + rng.normal(0, 0.003, len(fr[::12]))],
          "est": np.c_[fr[::40], np.interp(fr[::40], tf, y), np.interp(fr[::40], tf, x), -np.interp(fr[::40], tf, z)]}
    # mocap at 120 Hz of TRUE time, its own clock tm = tf + O + k (tf - tf0); noise; dropouts
    tmo_f = np.arange(boot + 0.3, boot + T - 0.3, 1 / 120.0)
    keep = np.ones(len(tmo_f), bool)
    for a, b in ((14.0, 14.3), (60.0, 61.0), (120.0, 122.0), (T - 15.0, T - 14.6)):   # one inside each fit window
        keep &= ~((tmo_f - boot > a) & (tmo_f - boot < b))
    tmo_f = tmo_f[keep]
    qi = Slerp(tf, Rot.from_quat(q))(np.clip(tmo_f, tf[0], tf[-1]))
    qn = (qi * Rot.from_rotvec(noise * rng.normal(0, math.radians(0.05), (len(tmo_f), 3)))).as_quat()
    pm = np.c_[[np.interp(tmo_f, tf, p[:, k]) for k in range(3)]].T + rng.normal(0, 0.0003, (len(tmo_f), 3))
    tf0 = boot; O = EPOCH_OFFSET + rng.uniform(-0.5, 0.5); k = DRIFT_PPM * 1e-6 * rng.choice([-1, 1])
    tm = tmo_f + O + k * (tmo_f - tf0) + noise * rng.normal(0, 0.0002, len(tmo_f))            # 0.2 ms stamp jitter
    mo = {"t": tm, "p": pm, "q": qn}
    truth = {"O_s": O, "k": k, "tf0": tf0}
    early, late = (boot + 15.0 - 10, boot + 15.0 + 15), (boot + T - 25 - 13, boot + T - 25 + 15)
    return fc, mo, truth, early, late, (boot + 15.0, boot + 45.0)


def run_synthetic(seeds):
    rows = []
    for s in range(seeds):
        fc, mo, tr, early, late, init = synth_flight(s)
        res, tfc, _, to_fc = MA.align(fc, mo, early, late, init)
        c = res["clock"]; t1 = c["map"]["t1_fc_s"]
        true_o1 = tr["O_s"] + tr["k"] * (t1 - tr["tf0"])
        # end-to-end: map every mocap stamp back to the FC clock and compare with the true FC time
        tf_true = (mo["t"] - tr["O_s"] + tr["k"] * tr["tf0"]) / (1 + tr["k"])
        err = to_fc(mo["t"]) - tf_true
        rows.append({"seed": s, "true_offset_s": true_o1, "true_rate_ppm": tr["k"] * 1e6,
                     "offset_err_ms": 1e3 * (c["map"]["o1_s"] - true_o1), "rate_err_ppm": c["map"]["rate_ppm"] - tr["k"] * 1e6,
                     "mapped_time_err_ms_rms": 1e3 * float(np.sqrt(np.mean(err ** 2))),
                     "mapped_time_err_ms_max": 1e3 * float(np.abs(err).max()),
                     "coarse_peak_ratio": c["coarse"].get("peak_ratio"), "corr": [w["corr"] for w in c["windows"]]})
        print(f"seed {s}: offset err {rows[-1]['offset_err_ms']:+.3f} ms, rate err {rows[-1]['rate_err_ppm']:+.2f} ppm, "
              f"mapped |err| max {rows[-1]['mapped_time_err_ms_max']:.3f} ms", flush=True)
    oe = np.array([r["offset_err_ms"] for r in rows]); re_ = np.array([r["rate_err_ppm"] for r in rows])
    me = np.array([r["mapped_time_err_ms_max"] for r in rows])
    return {"seeds": rows, "summary": {"offset_err_ms_mean": float(oe.mean()), "offset_err_ms_absmax": float(np.abs(oe).max()),
                                       "rate_err_ppm_mean": float(re_.mean()), "rate_err_ppm_absmax": float(np.abs(re_).max()),
                                       "mapped_time_err_ms_max_over_seeds": float(me.max())},
            "setup": {"offset": "1.7e9 s + U(-0.5, 0.5) s", "drift_ppm": f"+-{DRIFT_PPM}", "mocap_hz": 120,
                      "mocap_noise": "0.05 deg/axis orientation, 0.3 mm position, 0.2 ms stamp jitter",
                      "fc": "RISI-like 400 Hz deltas, DADT 2.5 ms, bias + 0.003 rad/s noise",
                      "dropouts_s": "0.3, 1.0, 2.0, 0.4 (one inside each fit window)", "flight_s": 200}}


# ---------------------------------------------------------------------------------------------- SITL
def sim2_vs_gt_offset(sim2, gt, lo, hi, d0, half=0.2):
    """GT clock - FC clock from SIM2 (NED position, FC clock, 400 Hz) against GT (ENU position): identical velocity
    pipeline on a 2.5 ms grid, least squares over the 3 axes. Independent of the gyro and attitude."""
    g = 0.0025; grid = np.arange(lo, hi, g); sm = 0.05
    s_enu = np.c_[sim2[:, 2], sim2[:, 1], -sim2[:, 3]]
    vs = [MA.boxcar(np.gradient(np.interp(grid, sim2[:, 0], s_enu[:, k]), g), sm, g) for k in range(3)]
    def cost(d):
        return sum(np.mean((v - MA.boxcar(np.gradient(np.interp(grid + d, gt[:, 0], gt[:, k + 1]), g), sm, g)) ** 2)
                   for k, v in enumerate(vs))
    g1 = np.arange(d0 - half, d0 + half, 0.001); c0 = g1[np.argmin([cost(d) for d in g1])]
    g2 = np.arange(c0 - 0.002, c0 + 0.002, 0.00005); return float(g2[np.argmin([cost(d) for d in g2])])


def run_sitl(trial, gt_path, timeref_path):
    path = os.path.expanduser(f"~/thesis_data/trials/{trial}/ardupilot.bin")
    fc = MA.read_fc(path, "XKF1", "RISI")
    gt = np.loadtxt(gt_path); gt = gt[np.r_[True, np.diff(gt[:, 0]) > 0]]
    mo = {"t": gt[:, 0], "p": gt[:, 1:4], "q": gt[:, 4:8]}
    early, late, init = MA.legacy_windows(fc, min_dist=1.0)   # SITL: no sync wiggles (pre-2026-10-11 rule)
    out = {"trial": trial, "windows_fc_s": [list(early), list(late)], "gt_rate_hz": float(1 / np.median(np.diff(gt[:, 0]))),
           "risi_dadt_median_s": fc["risi_dadt_median_s"]}
    base, _, _, _ = MA.align(fc, mo, early, late, init)
    bc = base["clock"]; o1, r, t1 = bc["map"]["o1_s"], bc["map"]["rate_ppm"] * 1e-6, bc["map"]["t1_fc_s"]
    out["base"] = {"o1_ms": 1e3 * o1, "rate_ppm": r * 1e6, "t1_fc_s": t1, "late_offset_ms": 1e3 * bc["mocap_minus_fc_late_s"],
                   "corr": [w["corr"] for w in bc["windows"]], "coarse": bc["coarse"]}
    # (a) differential: tm' = (1 + k) tm + D
    k, D = DRIFT_PPM * 1e-6, EPOCH_OFFSET
    mo2 = {"t": (1 + k) * mo["t"] + D, "p": mo["p"], "q": mo["q"]}
    inj, _, _, to_fc2 = MA.align(fc, mo2, early, late, init); ic = inj["clock"]
    pred_o1 = o1 + k * (t1 + o1) + D; pred_rate = (1 + k) * (1 + r) - 1
    tf_base = (mo["t"] - o1 + r * t1) / (1 + r)
    out["differential"] = {"injected": {"D_s": D, "k_ppm": k * 1e6},
                           "offset_err_ms": 1e3 * (ic["map"]["o1_s"] - pred_o1), "rate_err_ppm": (ic["map"]["rate_ppm"] * 1e-6 - pred_rate) * 1e6,
                           "mapped_time_diff_ms_max": 1e3 * float(np.abs(to_fc2(mo2["t"]) - tf_base).max())}
    # (b) absolute references
    refs = {}
    oe = sim2_vs_gt_offset(fc["sim2"], gt, *early, o1); ol = sim2_vs_gt_offset(fc["sim2"], gt, *late, bc["mocap_minus_fc_late_s"])
    tc = [0.5 * sum(early), 0.5 * sum(late)]; rr = (ol - oe) / (tc[1] - tc[0])
    refs["sim2_velocity"] = {"early_ms": 1e3 * oe, "late_ms": 1e3 * ol, "rate_ppm": rr * 1e6,
                             "r8_minus_ref_early_ms": 1e3 * (bc["windows"][0]["mocap_minus_fc_s"] - oe),
                             "r8_minus_ref_late_ms": 1e3 * (bc["windows"][-1]["mocap_minus_fc_s"] - ol),
                             "r8_minus_ref_rate_ppm": (r - rr) * 1e6}
    P = np.loadtxt(timeref_path); P = P[np.argsort(P[:, 1])]
    pm = MA.pi_fc_map_pairs(P)
    ref_at = lambda t: pm["pi_minus_fc_at_start_s"] + pm["rate_ppm"] * 1e-6 * (t - pm["t0_fc_s"])
    refs["imu_time_ref_lower_envelope"] = {**pm, "r8_minus_ref_early_ms": 1e3 * (bc["windows"][0]["mocap_minus_fc_s"] - ref_at(tc[0])),
                                           "r8_minus_ref_late_ms": 1e3 * (bc["windows"][-1]["mocap_minus_fc_s"] - ref_at(tc[1])),
                                           "r8_minus_ref_rate_ppm": r * 1e6 - pm["rate_ppm"],
                                           "note": "includes the minimum bridge latency (>= 0): r8 - ref is expected <= 0 by that much"}
    out["absolute"] = refs
    # (c) the old IMU path for comparison
    fci = MA.read_fc(path, "XKF1", "IMU")
    imu, _, _, _ = MA.align(fci, mo, early, late, init); icl = imu["clock"]
    out["imu_path"] = {"o1_ms": 1e3 * icl["map"]["o1_s"], "rate_ppm": icl["map"]["rate_ppm"],
                       "group_delay_ms_compensated": icl["gyro_filter_delay_ms_compensated"],
                       "imu_minus_risi_early_ms": 1e3 * (icl["windows"][0]["mocap_minus_fc_s"] - bc["windows"][0]["mocap_minus_fc_s"]),
                       "imu_minus_risi_late_ms": 1e3 * (icl["windows"][-1]["mocap_minus_fc_s"] - bc["windows"][-1]["mocap_minus_fc_s"])}
    # (d) the 10 Hz SIM self-test with RISI
    st = MA.selftest(trial, None, gyro_src="RISI")
    out["sim_selftest_risi"] = st["selftest"]
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["synthetic", "sitl"]); ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", type=int, default=8); ap.add_argument("--trial"); ap.add_argument("--gt"); ap.add_argument("--timeref")
    a = ap.parse_args()
    res = run_synthetic(a.seeds) if a.mode == "synthetic" else run_sitl(a.trial, a.gt, a.timeref)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res.get("summary", res), indent=1))


if __name__ == "__main__":
    main()
