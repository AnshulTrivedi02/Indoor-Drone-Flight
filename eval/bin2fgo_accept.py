#!/usr/bin/env python3
"""Rung 1: the CONVERTER ACCEPTANCE BAND on a real log (pre-registered 2026-10-12, docs/rung1_preregistration.md
sec. 5b). The converter (eval/bin2fgo.py) is accepted on the FIRST real log (a verification sortie: B, H or V) only if
every test below passes; until then no FGO row is scored. The band checks the converter against EKF3's OWN inputs in the
same log (the DAL replay records and the FC's logged sensor records), so it needs no bag and no truth.

  python3 eval/bin2fgo_accept.py --conv <out.npz> --bin <flight.BIN> [--timing-json <sensor_timing_from_log.json>]
                                 [--json OUT]

  A1  LOG_REPLAY = 1 (PARM)                                                                   (exact)
  A2  DSF dropped blocks = 0 over the whole log                                               (exact)
  A3  IMU: RISI samples dropped for flags = 0; |DVDT - DADT| > 0.5 ms in <= 0.1 % of samples; DVDT within 0.5 ms of the
      frame spacing in >= 99 % of samples
  A4  IMU frame rate (MEAN frame period: SITL frames alternate 2/3 ms) within +-2 % of SCHED_LOOP_RATE
  A5  IMU against the FC's own logged IMU record (same instance; INS-filtered, ~25 Hz): the converter's raw rates passed
      through the INS 2-pole low-pass filters (INS_GYRO_FILTER / INS_ACCEL_FILTER) and interpolated at the IMU record
      stamps, over the DISARMED spans only (log start to the first arming, the last disarming to the log end: the sync
      wiggles, the best excitation; in flight, prop vibration point-sampled at 25 Hz would leave tenths of m/s^2 that
      the replica does not model, a false rejection). Best common lag within +-10 ms; per axis RMS difference
      <= 0.05 rad/s (gyro) and <= 0.3 m/s^2 (accel); correlation >= 0.95 on every axis whose IMU-record std exceeds
      0.1 rad/s / 0.5 m/s^2. If no gyro axis exceeds 0.1 rad/s there (no wiggle), A5 is NOT TESTED and the converter is
      NOT accepted on that log. Tests the FRD -> FLU frame, the units, the instance, the delta/dt scaling and the stamps
      (a sign or axis error gives RMS ~ the signal, a unit error ~1000x; the bounds leave room for the notch filters and
      the record's logging time, which the replica does not model).
  A6  Rest: over [arming - 3 s, arming - 0.5 s], if the vehicle is still (gyro std < 0.05 rad/s): |mean specific force|
      within 9.80665 +- 0.15 m/s^2 and |mean gyro| < 0.05 rad/s. Otherwise reported as NOT TESTED (not a failure).
  A7  Flow equals EKF3's flow input exactly: OF and ROFH counts equal, flowX/Y, bodyX/Y float32-identical, Qual equal.
  A8  Geometry: FLOW_POS_* = ROFH.posOffset and RNGFNDn_POS_* = RRNI.pos_offset (1e-6).
  A9  Range against the FC's logged RFND (same instance, Stat Good): at each converter range sample (arrival time), the
      RFND sample within 60 ms: median |difference| <= 0.02 m and 95th percentile <= 0.05 m, over >= 50 pairs.
  A10 Flow sign and response (needs --timing-json, eval/sensor_timing_from_log.py run with --window on a sync wiggle):
      gain > 0 on both axes (sign_ok) and peak correlation >= 0.5 on both axes. Without it: NOT TESTED, and the
      converter is NOT accepted (the sign is the converter's identity-mapping assumption).
  Reported, no bound: flow rate and inter-arrival percentiles, the range update period, the Qual > 0 fraction, the
  initial-height source and |init_range - RNGFNDn_GNDCLR|.
ACCEPTED = A1-A5 and A7-A10 pass, and A6 passes or is NOT TESTED.
"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FRD2FLU = np.array([1.0, -1.0, -1.0])
BAND = {"dvdt_ne_dadt_frac_max": 0.001, "dvdt_vs_frame_frac_min": 0.99, "imu_rate_rel_tol": 0.02,
        "gyro_rms_max": 0.05, "acc_rms_max": 0.3, "corr_min": 0.95, "gyro_corr_std": 0.1, "acc_corr_std": 0.5,
        "lag_max_ms": 10.0,
        "rest_g": 9.80665, "rest_g_tol": 0.15, "rest_gyro_max": 0.05, "range_pair_s": 0.06, "range_med_max": 0.02,
        "range_p95_max": 0.05, "range_min_pairs": 50, "flow_corr_min": 0.5}


def lpf2p(x, fs, fc):
    """ArduPilot's 2-pole low-pass (DigitalBiquadFilter, Butterworth, filters/LowPassFilter2p.cpp), per column, started
    at the first sample (no transient)."""
    if not fc or fc <= 0:
        return x.copy()
    ohm = np.tan(np.pi * fc / fs); c = 1.0 + 2.0 * np.cos(np.pi / 4) * ohm + ohm * ohm
    b0 = ohm * ohm / c; b1 = 2.0 * b0; b2 = b0; a1 = 2.0 * (ohm * ohm - 1.0) / c
    a2 = (1.0 - 2.0 * np.cos(np.pi / 4) * ohm + ohm * ohm) / c
    from scipy.signal import lfilter, lfilter_zi
    bb, aa = np.array([b0, b1, b2]), np.array([1.0, a1, a2]); zi = lfilter_zi(bb, aa)
    return np.column_stack([lfilter(bb, aa, x[:, k], zi=zi * x[0, k])[0] for k in range(x.shape[1])])


def imu_vs_onboard(conv_t, conv_g, conv_a, imu, fs, f_gyro, f_acc, band=BAND, spans=None):
    """A5 from arrays: conv_* (FLU, the RAW RISI rates at the frame stamps) through the INS low-pass filters
    (INS_GYRO_FILTER / INS_ACCEL_FILTER, at the frame rate fs), interpolated at the logged IMU record stamps (FRD ->
    FLU), sample by sample over the overlap, restricted to `spans` [(t0, t1), ...] (the DISARMED spans). The best
    common lag (-20...+20 ms, 0.5 ms steps; minimum total gyro RMS) must lie within +-lag_max_ms; at that lag, per axis
    RMS difference <= the bound, and correlation >= corr_min on every axis whose IMU-record std exceeds corr_std."""
    ti, gi, ai = imu[0], imu[1] * FRD2FLU, imu[2] * FRD2FLU
    m = (ti >= conv_t[0] + 0.5) & (ti <= conv_t[-1] - 0.5)
    if spans is not None:
        m &= np.any([(ti >= a) & (ti <= b) for a, b in spans], axis=0) if spans else np.zeros(len(ti), bool)
    ti, gi, ai = ti[m], gi[m], ai[m]
    if len(ti) < 100:
        return {"error": f"only {len(ti)} IMU records in the disarmed spans {spans}", "pass": False}
    if not np.any(np.std(gi, axis=0) > band["gyro_corr_std"]):
        # no rotation to test signs, axes or the lag against: NOT TESTED, which does not accept (a sync wiggle or a
        # bench rotation is required in the disarmed spans)
        return {"not_tested": f"no gyro axis with record std > {band['gyro_corr_std']} rad/s in the disarmed spans "
                              "(a sync wiggle is required)", "gyro_std_xyz": np.std(gi, axis=0).tolist(), "pass": False}
    gf, af = lpf2p(conv_g, fs, f_gyro), lpf2p(conv_a, fs, f_acc)
    at = lambda x, L: np.c_[[np.interp(ti - L, conv_t, x[:, k]) for k in range(3)]].T
    lags = np.arange(-0.020, 0.02001, 0.0005)
    cost = [float(np.sum((at(gf, L) - gi) ** 2)) for L in lags]
    L = float(lags[int(np.argmin(cost))])
    res = {"best_lag_ms": 1e3 * L, "lag_bound_ms": band["lag_max_ms"], "n_samples": int(m.sum()),
           "filters_hz": {"gyro": f_gyro, "acc": f_acc}, "frame_rate_hz": fs}
    ok_all = abs(1e3 * L) <= band["lag_max_ms"] and m.sum() >= 100
    for name, xc, xi, lim, cs in (("gyro", gf, gi, band["gyro_rms_max"], band["gyro_corr_std"]),
                                  ("acc", af, ai, band["acc_rms_max"], band["acc_corr_std"])):
        xa = at(xc, L); rms = np.sqrt(np.mean((xa - xi) ** 2, axis=0))
        corr = [float(np.corrcoef(xa[:, k], xi[:, k])[0, 1]) if np.std(xi[:, k]) > cs else None for k in range(3)]
        p = bool(np.all(rms <= lim) and all(c >= band["corr_min"] for c in corr if c is not None))
        res[name] = {"rms_diff_xyz": rms.tolist(), "bound": lim, "corr_xyz": corr, "corr_tested_if_std_gt": cs, "pass": p}
        ok_all &= p
    res["pass"] = bool(ok_all)
    return res


def evaluate(meta, npz, recs, timing=None, band=BAND):
    """The band from the converter outputs (meta json, npz arrays), the flight log's records {IMU, RFND, ARM} and the
    optional sensor-timing JSON. Pure function (tests)."""
    c = meta["checks"]; P = meta["parm"]; T = {}
    T["A1_log_replay"] = {"value": P.get("LOG_REPLAY"), "pass": P.get("LOG_REPLAY") == 1}
    T["A2_dsf_dropped"] = {"value": c["dsf_dropped_blocks"], "pass": c["dsf_dropped_blocks"] == 0}
    n_imu = len(npz["imu_t"]) + c["imu_dropped_flags"]
    f_ne = c["imu_dvdt_ne_dadt_gt_0p5ms"] / max(n_imu, 1) if "imu_dvdt_ne_dadt_gt_0p5ms" in c else None
    f_fr = 1.0 - c["imu_dvdt_vs_frame_dt_n_gt_0p5ms"] / max(n_imu, 1)
    T["A3_imu_internal"] = {"dropped_flags": c["imu_dropped_flags"], "dvdt_ne_dadt_frac": f_ne, "dvdt_vs_frame_frac": f_fr,
                            "pass": c["imu_dropped_flags"] == 0 and f_ne is not None
                            and f_ne <= band["dvdt_ne_dadt_frac_max"] and f_fr >= band["dvdt_vs_frame_frac_min"]}
    slr = P.get("SCHED_LOOP_RATE")
    fp = c.get("imu_frame_period_ms_mean")
    rel = None if not slr or fp is None else abs(fp * 1e-3 * slr - 1.0)
    T["A4_imu_rate"] = {"frame_period_ms_mean": fp, "SCHED_LOOP_RATE": slr, "rel_err": rel,
                        "pass": rel is not None and rel <= band["imu_rate_rel_tol"]}
    inst = meta["imu_instance"]
    I = [r for r in recs["IMU"] if r["I"] == inst]
    arm = [r["TimeUS"] / 1e6 for r in recs["ARM"] if r["ArmState"] == 1]
    dis = [r["TimeUS"] / 1e6 for r in recs["ARM"] if r["ArmState"] == 0]
    t_lo, t_hi = float(npz["imu_t"][0]), float(npz["imu_t"][-1])
    spans = [(t_lo, arm[0])] if arm else [(t_lo, t_hi)]                 # disarmed: before the first arming ...
    if arm and dis and dis[-1] > arm[-1]:
        spans.append((dis[-1], t_hi))                                    # ... and after the last disarming
    imu = (np.array([r["TimeUS"] / 1e6 for r in I]), np.array([[r["GyrX"], r["GyrY"], r["GyrZ"]] for r in I]),
           np.array([[r["AccX"], r["AccY"], r["AccZ"]] for r in I]))
    fs = 1e3 / c["imu_frame_period_ms_mean"] if c.get("imu_frame_period_ms_mean") else None
    a5 = (imu_vs_onboard(npz["imu_t"], npz["imu_gyro"], npz["imu_acc"], imu, fs, P.get("INS_GYRO_FILTER"),
                         P.get("INS_ACCEL_FILTER"), band, spans) if len(I) > 100 and fs else None)
    if a5 is not None and "not_tested" in a5:          # DIAGNOSTIC only (not counted): the replica on the whole log
        d = imu_vs_onboard(npz["imu_t"], npz["imu_gyro"], npz["imu_acc"], imu, fs, P.get("INS_GYRO_FILTER"),
                           P.get("INS_ACCEL_FILTER"), {**band, "gyro_corr_std": 0.0, "acc_corr_std": 1e9}, None)
        a5["diagnostic_whole_log_not_counted"] = {k: d.get(k) for k in ("best_lag_ms", "n_samples")} | {
            "gyro_rms_diff_xyz": d.get("gyro", {}).get("rms_diff_xyz"), "acc_rms_diff_xyz": d.get("acc", {}).get("rms_diff_xyz")}
    T["A5_imu_vs_onboard_IMU"] = {"instance": inst, "disarmed_spans_fc_s": spans,
                                  **(a5 or {"error": "no IMU records or no frame rate"}),
                                  "pass": bool(a5 and a5["pass"])}
    if arm:
        w = (npz["imu_t"] >= arm[0] - 3.0) & (npz["imu_t"] <= arm[0] - 0.5)
        g, a = npz["imu_gyro"][w], npz["imu_acc"][w]
        if w.sum() > 100 and np.max(np.std(g, 0)) < band["rest_gyro_max"]:
            gn = float(np.linalg.norm(a.mean(0))); gm = float(np.max(np.abs(g.mean(0))))
            T["A6_rest"] = {"tested": True, "specific_force": gn, "gyro_abs_mean_max": gm,
                            "pass": abs(gn - band["rest_g"]) <= band["rest_g_tol"] and gm < band["rest_gyro_max"]}
        else:
            T["A6_rest"] = {"tested": False, "why": "not still in [arm - 3 s, arm - 0.5 s]", "pass": None}
    else:
        T["A6_rest"] = {"tested": False, "why": "no ARM record", "pass": None}
    T["A7_flow_equals_rofh"] = {"value": c.get("rofh_equals_of"), "pass": c.get("rofh_equals_of") is True}
    T["A8_geometry"] = {"flow": c.get("flow_pos_parm_matches_rofh"), "range": c.get("range_pos_parm_matches_rrni"),
                        "pass": c.get("flow_pos_parm_matches_rofh") is True and c.get("range_pos_parm_matches_rrni") is True}
    rinst = meta["range_instance"]
    Rf = np.array([(r["TimeUS"] / 1e6, r["Dist"]) for r in recs["RFND"] if r["Instance"] == rinst and r["Stat"] == 4])
    if len(Rf) and len(npz["rng_t"]):
        ta = npz["rng_t"] + meta["delays_ms"]["range"] * 1e-3          # back to the emission (arrival) time
        j = np.searchsorted(Rf[:, 0], ta).clip(1, len(Rf) - 1)
        j = np.where(np.abs(Rf[j - 1, 0] - ta) < np.abs(Rf[j, 0] - ta), j - 1, j)
        ok = np.abs(Rf[j, 0] - ta) <= band["range_pair_s"]
        d = np.abs(Rf[j[ok], 1] - npz["rng"][ok])
        med, p95 = (float(np.median(d)), float(np.percentile(d, 95))) if len(d) else (None, None)
        T["A9_range_vs_RFND"] = {"n_pairs": int(ok.sum()), "median_abs_m": med, "p95_abs_m": p95,
                                 "pass": len(d) >= band["range_min_pairs"] and med <= band["range_med_max"]
                                 and p95 <= band["range_p95_max"]}
    else:
        T["A9_range_vs_RFND"] = {"error": "no Good RFND records or no converter range samples", "pass": False}
    if timing is None:
        T["A10_flow_sign"] = {"tested": False, "why": "no --timing-json (sensor_timing_from_log.py on a sync wiggle)",
                              "pass": False}
    else:
        f = timing["flow"]; pc = f["peak_corr_per_axis_xy"]
        T["A10_flow_sign"] = {"tested": True, "sign_ok": f["sign_ok"], "gain_xy": f["gain_xy_at_best"], "peak_corr_xy": pc,
                              "pass": bool(f["sign_ok"]) and min(pc) >= band["flow_corr_min"]}
    n = meta["range_instance"] + 1
    gcl = P.get(f"RNGFND{n}_GNDCLR")
    rep = {"flow_rate_hz_median": c.get("flow_rate_hz_median"), "flow_interarrival_ms_p5_p50_p95": c.get("flow_interarrival_ms_p5_p50_p95"),
           "range_update_period_ms": c.get("range_update_period_ms_from_changes"), "flow_qual_gt0_frac": c.get("flow_qual_gt0_frac"),
           "init_range": meta.get("init_range"), "init_range_source": meta.get("init_range_source"),
           f"RNGFND{n}_GNDCLR": gcl, "init_minus_gndclr_m": None if gcl is None else meta.get("init_range") - gcl}
    need = [k for k in T if k != "A6_rest"]
    accepted = all(T[k]["pass"] is True for k in need) and T["A6_rest"]["pass"] in (True, None)
    return {"accepted": bool(accepted), "tests": T, "reported": rep, "band": band}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--conv", required=True, help="bin2fgo's <out>.npz (its <out>.json is read beside it)")
    ap.add_argument("--bin", required=True, help="the flight's .BIN (the one the converter read)")
    ap.add_argument("--timing-json", default=None); ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    from df_reader import read_records
    meta = json.load(open(a.conv[:-4] + ".json")); npz = dict(np.load(a.conv))
    recs, _ = read_records(a.bin, ["IMU", "RFND", "ARM"])
    out = evaluate(meta, npz, recs, json.load(open(a.timing_json)) if a.timing_json else None)
    out["inputs"] = {"conv": os.path.abspath(a.conv), "bin": os.path.abspath(a.bin), "bin_sha256_in_meta": meta["bin_sha256"],
                     "timing_json": a.timing_json}
    print(json.dumps({k: (None if v["pass"] is None else bool(v["pass"])) for k, v in out["tests"].items()}, indent=1)); print("ACCEPTED" if out["accepted"] else "NOT ACCEPTED")
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return out


if __name__ == "__main__":
    main()
