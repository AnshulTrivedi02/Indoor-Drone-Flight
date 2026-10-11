#!/usr/bin/env python3
"""R1 hardware-free acceptance checks: eval/bin2fgo.py's output from a SITL LOG_REPLAY log against the SAME flight's
bag (the inputs the FGO consumed in simulation). Diagnostic; nothing here feeds an estimator.

  python3 eval/bin2fgo_sitl_check.py <events.npz> <bag_dir> <log.BIN> [--json out.json]

The npz must be converted with --flow-delay-ms 0 --range-delay-ms 0 (arrival stamps), so the delays measured here are
the SITL pipeline's TRUE arrival-minus-capture delays (the reference for eval/sensor_timing_from_log.py).

Clock: FC TimeUS <-> bag sim clock from /imu/time_ref (HIGHRES_IMU.time_usec, the FC clock, against the bag header
stamp): the lower envelope of (stamp - time_usec) in 5 s bins, fitted linearly (as eval/closed_loop_score.py).
IMU:   the bag IMU sample at time_ref s is compared with the RISI-derived rate whose interval contains s (same clock,
       no map needed). HIGHRES_IMU is AFTER the INS 20 Hz low-pass, RISI BEFORE it, so the comparison is on 0.1 s
       block means, plus the lag that best aligns the two gyro streams (expected: about the filter group delay).
FLOW:  each OF record is matched to the bag flow message with float32-equal (flow_x_rad, flow_y_rad); Qual must equal
       round(inlier*255) (flow_bridge.py); delay = OF arrival - capture stamp (mapped to the FC clock).
RANGE: the converter's held/emitted range against the bag's range; the lag minimising the difference is the SITL
       pipeline's range delay; residual at that lag (DISTANCE_SENSOR is integer cm: expect <= ~5 mm plus motion).
DEROTATION: OF.bodyX/Y minus the raw RISI gyro averaged over the same flow interval, against EKF3's gyro bias
       (XKF1 core 0 GX/GY): if bodyRate = AHRS gyro (= INS gyro - EKF3 bias) the difference tracks -bias."""
import argparse, json, os, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from pymavlink import DFReader

ap = argparse.ArgumentParser(); ap.add_argument("npz"); ap.add_argument("bag"); ap.add_argument("bin")
ap.add_argument("--json"); a = ap.parse_args()
Z = np.load(a.npz); META = json.load(open(a.npz[:-4] + ".json"))
assert META["delays_ms"]["flow"] == 0 and META["delays_ms"]["range"] == 0, "convert with zero delays for this check"
ts = get_typestore(Stores.ROS2_JAZZY)
here = os.path.dirname(os.path.abspath(__file__))
ts.register(get_types_from_msg(open(os.path.join(here, "..", "src", "optical_flow_interfaces", "msg", "OpticalFlow.msg")).read(),
                               "optical_flow_interfaces/msg/OpticalFlow"))
st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
imu, tref, flow, rng = [], [], [], []
with Reader(a.bag) as r:
    cs = [c for c in r.connections if c.topic in ("/imu/data_raw", "/imu/time_ref", "/optical_flow/measurement", "/downward_lidar/range")]
    for con, _, raw in r.messages(connections=cs):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/data_raw":
            imu.append((st(m.header), m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z,
                        m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z))
        elif con.topic == "/imu/time_ref":
            tref.append((st(m.header), m.time_ref.sec + m.time_ref.nanosec * 1e-9))
        elif con.topic == "/optical_flow/measurement":
            flow.append((st(m.header), m.flow_x_rad, m.flow_y_rad, float(m.valid), m.inlier_ratio))
        else:
            rng.append((st(m.header), m.range))
imu, tref, flow, rng = (np.array(x) for x in (imu, tref, flow, rng))
out = {"npz": a.npz, "bag": a.bag}

# ---- clock map FC -> bag (lower envelope of stamp - time_usec) ----
s_fc, s_bag = tref[:, 1], tref[:, 0]; dd = s_bag - s_fc; env = []
for lo in np.arange(s_fc.min(), s_fc.max(), 5.0):
    q = (s_fc >= lo) & (s_fc < lo + 5)
    if q.sum() > 50:
        i = np.argmin(dd[q]); env.append((s_fc[q][i], dd[q][i]))
env = np.array(env); kk, cc = np.polyfit(env[:, 0], env[:, 1], 1)
fc2bag = lambda s: s + kk * s + cc
bag2fc = lambda b: (b - cc) / (1 + kk)
out["clock_map"] = {"offset_ms_at_start": 1e3 * float(kk * env[0, 0] + cc), "rate_ppm": 1e6 * float(kk),
                    "env_resid_ms_maxabs": 1e3 * float(np.max(np.abs(env[:, 1] - (kk * env[:, 0] + cc))))}

# ---- IMU ----
ti, acc, gyr = Z["imu_t"], Z["imu_acc"], Z["imu_gyro"]
tr_by_stamp = {round(b, 9): f for b, f in tref}          # time_ref carries the SAME header stamp as its data_raw
pair = np.array([round(t_, 9) in tr_by_stamp for t_ in imu[:, 0]])
out["imu_pairing"] = {"n_data_raw": int(len(imu)), "n_time_ref": int(len(tref)), "n_paired_by_stamp": int(pair.sum())}
imu = imu[pair]; imu = imu[np.argsort(imu[:, 0])]
s = np.array([tr_by_stamp[round(t_, 9)] for t_ in imu[:, 0]])   # FC time of each bag IMU sample
k = np.searchsorted(ti, s)                            # RISI interval (ti[k-1], ti[k]] containing s
ok = (k > 0) & (k < len(ti))
B_acc, B_gyr = imu[ok, 1:4], imu[ok, 4:7]; R_acc, R_gyr = acc[k[ok]], gyr[k[ok]]
out["imu"] = {"bag_rate_hz": float(1 / np.median(np.diff(s))), "conv_rate_hz_mean": float(1 / np.mean(np.diff(ti))),
              "n_paired": int(ok.sum())}
rest = s[ok] < META["t_arm"] - 1.0
out["imu"]["rest_mean_acc_flu_bag"] = B_acc[rest].mean(0).tolist()
out["imu"]["rest_mean_acc_flu_conv"] = R_acc[rest].mean(0).tolist()
out["imu"]["rest_mean_gyro_flu_bag"] = B_gyr[rest].mean(0).tolist()
out["imu"]["rest_mean_gyro_flu_conv"] = R_gyr[rest].mean(0).tolist()
# 0.1 s block means over the airborne part
blk = np.floor(s[ok] / 0.1).astype(int); ub, inv = np.unique(blk, return_inverse=True)
cnt = np.bincount(inv)
bm = lambda X: np.column_stack([np.bincount(inv, X[:, j]) / cnt for j in range(3)])
dA, dG = bm(B_acc) - bm(R_acc), bm(B_gyr) - bm(R_gyr)
out["imu"]["block0p1s_acc_diff_rms_xyz"] = np.sqrt(np.mean(dA ** 2, 0)).tolist()
out["imu"]["block0p1s_gyro_diff_rms_xyz"] = np.sqrt(np.mean(dG ** 2, 0)).tolist()
out["imu"]["block0p1s_corr_acc_xyz"] = [float(np.corrcoef(bm(B_acc)[:, j], bm(R_acc)[:, j])[0, 1]) for j in range(3)]
out["imu"]["block0p1s_corr_gyro_xyz"] = [float(np.corrcoef(bm(B_gyr)[:, j], bm(R_gyr)[:, j])[0, 1]) for j in range(3)]
# lag: shift the RISI stream by L (interval-mid interpolation) to best match the filtered HIGHRES gyro
tmid = ti - Z["imu_dt"] / 2
best = []
for L in np.arange(-0.010, 0.0305, 0.0005):
    G = np.column_stack([np.interp(s[ok] - L, tmid, gyr[:, j]) for j in range(3)])
    best.append((float(np.sqrt(np.mean((G - B_gyr) ** 2))), float(L)))
best.sort()
out["imu"]["gyro_lag_bag_behind_conv_ms"] = 1e3 * best[0][1]
out["imu"]["gyro_rms_at_lag_vs_0"] = [best[0][0], [b for b in best if abs(b[1]) < 1e-9][0][0]]

# ---- FLOW ----
fa, fxy, q = Z["flow_t_arrival"], Z["flow_xy"].astype(np.float32), Z["flow_qual"]
fb = flow[np.argsort(flow[:, 0])]
fb_fc = bag2fc(fb[:, 0])
key = {}
for i in range(len(fb)):
    if fb[i, 3] != 1:
        continue                                      # flow_bridge.py sends valid messages only
    key.setdefault((np.float32(fb[i, 1]).tobytes(), np.float32(fb[i, 2]).tobytes()), []).append(i)
match = np.full(len(fa), -1)
for j in range(len(fa)):
    c = key.get((fxy[j, 0].tobytes(), fxy[j, 1].tobytes()), [])
    c = [i for i in c if fa[j] - 0.5 < fb_fc[i] <= fa[j] + 0.01]
    if c:
        match[j] = max(c, key=lambda i: fb_fc[i])
m = match >= 0
dl = fa[m] - fb_fc[match[m]]
qual_ok = np.array_equal(q[m], np.clip(np.round(fb[match[m], 4] * 255.0), 0, 255).astype(int))
out["flow"] = {"n_of": int(len(fa)), "n_bag": int(len(fb)), "n_bag_valid": int(fb[:, 3].sum()),
               "n_matched_exact_float32": int(m.sum()), "matched_frac": float(m.mean()),
               "unmatched_all_exact_zero": bool(np.all(fxy[~m] == 0)),
               "unmatched_before_bag_start": int((fa[~m] < fb_fc[0]).sum()),
               "qual_equals_round_inlier_x255": bool(qual_ok),
               "true_delay_arrival_minus_capture_ms_p5_p50_p95_mean": [1e3 * float(np.percentile(dl, p)) for p in (5, 50, 95)] + [1e3 * float(dl.mean())],
               "sign_identity": "values are float32-identical, so the converter's mapping is the identity (no sign/axis change)"}

# ---- RANGE ----
rt, rd = Z["rng_t"], Z["rng"]
rb = rng[np.argsort(rng[:, 0])]; rb_fc = bag2fc(rb[:, 0])
okb = (rb[:, 1] >= 0.05) & (rb[:, 1] <= 40)
res = []
for L in np.arange(0.0, 0.2005, 0.0025):
    e = rd - np.interp(rt - L, rb_fc[okb], rb[okb, 1])
    e = e[np.abs(e) < 0.3]
    res.append((float(np.sqrt(np.mean(e ** 2))), float(L), float(np.percentile(np.abs(e), 99))))
res.sort()
e0 = rd - np.interp(rt, rb_fc[okb], rb[okb, 1])
out["range"] = {"n_conv": int(len(rt)), "n_bag": int(len(rb)), "conv_period_ms": float(1e3 * np.median(np.diff(rt))),
                "bag_period_ms": float(1e3 * np.median(np.diff(rb[:, 0]))),
                "best_lag_ms": 1e3 * res[0][1], "rms_at_best_m": res[0][0], "p99abs_at_best_m": res[0][2],
                "rms_at_zero_lag_m": float(np.sqrt(np.mean(e0[np.abs(e0) < 0.3] ** 2))),
                "frac_abs_diff_gt_0p3_at_zero": float(np.mean(np.abs(e0) >= 0.3)),
                "hover_median_diff_m": float(np.median(e0[(rt > META["t_arm"] + 30) & (rt < rt[-1] - 30)]))}
# true arrival delay at value changes: each RRNI change (value v at frame t) vs the first bag sample that rounds to v
# (DISTANCE_SENSOR is cm) and is not after t
ch = np.where(np.diff(rd) != 0)[0] + 1
dly = []
for j in ch:
    cand = np.where((np.round(rb[:, 1] * 100) == np.round(rd[j] * 100)) & (rb_fc <= rt[j] + 1e-6) & (rb_fc > rt[j] - 0.4))[0]
    if len(cand):
        dly.append(rt[j] - rb_fc[cand[-1]])
dly = np.array(dly)
out["range"]["true_change_delay_ms_p5_p50_p95"] = [1e3 * float(np.percentile(dly, p)) for p in (5, 50, 95)] if len(dly) else None
out["range"]["n_changes_matched"] = int(len(dly))

# ---- DEROTATION source ----
r = DFReader.DFReader_binary(a.bin, zero_time_base=False)
xk, par = [], {}
while True:
    mm = r.recv_match(type=["XKF1", "PARM"])
    if mm is None:
        break
    if mm.get_type() == "PARM":
        par[mm.Name] = mm.Value
    elif mm.C == 0:
        xk.append((mm.TimeUS * 1e-6, np.radians(mm.GX), np.radians(mm.GY)))
xk = np.array(xk)
gfrd = gyr * np.array([1, -1, -1])                    # back to FRD
th = np.vstack([np.zeros(3), np.cumsum(gfrd * Z["imu_dt"][:, None], 0)]); tt = np.concatenate([[ti[0] - Z["imu_dt"][0]], ti])
e1 = fa[1:]; e0 = fa[:-1]
avg = np.column_stack([(np.interp(e1, tt, th[:, j]) - np.interp(e0, tt, th[:, j])) / (e1 - e0) for j in range(2)])
dbody = Z["flow_body_frd"][1:] - avg
bias = np.column_stack([np.interp(e1, xk[:, 0], xk[:, 1]), np.interp(e1, xk[:, 0], xk[:, 2])])
air = (e1 > META["t_arm"] + 10) & (np.diff(fa) < 0.06)
blk = np.floor(e1[air] / 10.0).astype(int); ub, inv = np.unique(blk, return_inverse=True); cnt = np.bincount(inv)
bmean = lambda X: np.column_stack([np.bincount(inv, X[:, j]) / cnt for j in range(2)])
Db, Bb = bmean(dbody[air]), bmean(bias[air])
out["derotation"] = {"AHRS_EKF_TYPE": par.get("AHRS_EKF_TYPE"), "FLOW_TYPE": par.get("FLOW_TYPE"),
                     "block10s_mean_body_minus_rawavg_radps_xy": Db.mean(0).tolist(),
                     "block10s_mean_ekf3_bias_radps_xy": Bb.mean(0).tolist(),
                     "block10s_corr_with_minus_bias_xy": [float(np.corrcoef(Db[:, j], -Bb[:, j])[0, 1]) for j in range(2)],
                     "block10s_rms_of_body_minus_rawavg_plus_bias_xy": np.sqrt(np.mean((Db + Bb) ** 2, 0)).tolist(),
                     "block10s_rms_of_body_minus_rawavg_xy": np.sqrt(np.mean(Db ** 2, 0)).tolist(),
                     "n_blocks": int(len(ub))}
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
