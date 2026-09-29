#!/usr/bin/env python3
"""Sim-time timing of the estimator inputs, and flow delivery latency into live EKF3.

This is the Phase 1 revised confound test (METHODOLOGY): it checks directly whether
the estimator inputs keep their `dsn_*` sim-time timing, which is what the RTF
threshold was a proxy for.

(a) For each estimator input (`/imu/data_raw`, `/optical_flow/measurement`,
    `/downward_lidar/range`), over the cruise window, from HEADER stamps (sim time):
    count, mean rate, median gap, p99 gap, and the % of gaps > 1.5x the nominal
    period (a dropped or late sample).
(b) Flow delivery latency into EKF3. Each valid flow frame is matched to the dataflash
    `OF` record that logged it, by value: `flow_bridge.py` sends
    `flow_rate_x = -flow_x_rad` (before the 2026-09-29 sign fix; `+flow_x_rad` after — the
    sign is detected per trial), `flow_rate_y = +flow_y_rad`, and `OF.flowX` /
    `OF.flowY` log exactly those rates. Latency = (`OF.TimeUS` - clock offset) -
    frame header stamp, with TimeUS mapped to the sim clock by clock_map() (offset
    AND rate, fitted early and late in the flight). The two clocks do NOT share an epoch exactly: the first
    attempt, without an offset, gave a median of -19.9 ms, i.e. `OF` apparently logged
    before the frame existed. So the offset (dataflash TimeUS minus bag sim time) is
    estimated per trial by aligning SITL's `SIM` truth with `/ground_truth/pose` on
    their velocity profiles (clock_offset()). Also reported: the fraction of valid
    frames that reached EKF3 (matched).

Usage (venv-evo; the dataflash log is read through ~/venv-ardupilot):
  python3 eval/input_timing.py TRIAL [TRIAL...] [--json OUT]
"""
import argparse, glob, json, os, subprocess
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from cruise_window import cruise_bounds

TRIALS_DIR = os.path.expanduser("~/thesis_data/trials")
PY_AP = os.path.expanduser("~/venv-ardupilot/bin/python3")
INPUTS = {"/imu/data_raw": 0.003, "/optical_flow/measurement": 0.033, "/downward_lidar/range": 0.033}

ts = get_typestore(Stores.ROS2_JAZZY)
_msg = glob.glob(os.path.expanduser("~/thesis_ws/src/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(_msg).read(), "optical_flow_interfaces/msg/OpticalFlow"))

_OF_DUMP = r"""
import sys, numpy as np
from pymavlink import mavutil
m = mavutil.mavlink_connection(sys.argv[1]); out = []
while True:
    x = m.recv_match(type='OF')
    if x is None: break
    out.append((x.TimeUS / 1e6, x.flowX, x.flowY))
np.save(sys.argv[2], np.array(out, dtype=np.float64))
"""


_SIM_DUMP = r"""
import sys, math, numpy as np
from pymavlink import mavutil
m = mavutil.mavlink_connection(sys.argv[1]); out = []
while True:
    x = m.recv_match(type='SIM')
    if x is None: break
    out.append((x.TimeUS / 1e6, x.Lat, x.Lng, x.Alt))
a = np.array(out, dtype=np.float64)
if np.abs(a[:, 1]).max() > 1000: a[:, 1:3] /= 1e7
R = 6378137.0
n = np.radians(a[:, 1] - a[0, 1]) * R
e = np.radians(a[:, 2] - a[0, 2]) * R * math.cos(math.radians(a[:, 1].mean()))
np.save(sys.argv[2], np.c_[a[:, 0], e, n, a[:, 3] - a[0, 3]])
"""


def sim_truth(trial):
    """SITL SIM truth (TimeUS clock), ENU relative to its first sample."""
    p = f"{TRIALS_DIR}/{trial}/ekf3/sim_enu.npy"
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        subprocess.run([PY_AP, "-c", _SIM_DUMP, f"{TRIALS_DIR}/{trial}/ardupilot.bin", p], check=True)
    return np.load(p)


def clock_offset(sim, gt):
    """offset = TimeUS clock - bag sim clock, from SIM truth vs /ground_truth/pose.

    Both velocity profiles pass through the SAME central difference at the SIM sample
    spacing (+-h), so the filter is identical and the shift estimate is unbiased; any
    constant position offset drops out. Least squares over the whole flight (climb,
    cruise start/stop, landing give the features), on a 0.25 ms grid. The residual
    curvature gives the fit's resolution."""
    ts_, h = sim[:, 0], np.median(np.diff(sim[:, 0]))
    vs = [(sim[2:, k] - sim[:-2, k]) / (ts_[2:] - ts_[:-2]) for k in (1, 2, 3)]
    tc = ts_[1:-1]
    def cost(d):
        tt = tc - d
        ok = (tt - h >= gt[0, 0]) & (tt + h <= gt[-1, 0])
        c = 0.0
        for k, v in zip((1, 2, 3), vs):
            vg = (np.interp(tt[ok] + h, gt[:, 0], gt[:, k]) - np.interp(tt[ok] - h, gt[:, 0], gt[:, k])) / (2 * h)
            c += np.sum((v[ok] - vg) ** 2)
        return c / ok.sum()
    grid = np.arange(-1.0, 1.0, 0.0025)
    coarse = grid[np.argmin([cost(d) for d in grid])]
    fine = np.arange(coarse - 0.005, coarse + 0.005, 0.00025)
    cs = np.array([cost(d) for d in fine])
    return float(fine[np.argmin(cs)]), float(cs.min())


EARLY_WIN, LATE_WIN = (0.0, 70.0), (290.0, 1e9)     # TimeUS seconds


def clock_map(sim, gt):
    """Linear map TimeUS -> bag sim clock: offset(t) = o1 + (o2 - o1)(t - t1)/(t2 - t1).

    The two clocks differ in RATE as well as offset: SITL's TimeUS runs ~0.017% slow
    against Gazebo sim time (dsn_tex_r1..r3: offset -7 ms early, -52 to -60 ms late).
    A single whole-flight offset would therefore smear any TimeUS-vs-bag comparison by
    up to about +-25 ms. Offsets are fitted (clock_offset) separately in an early window
    (takeoff, cruise start) and a late window (cruise stop, landing), each at its mean
    TimeUS. Returns (to_sim(t_us_array), o1, o2, t1, t2)."""
    fits = []
    for lo, hi in (EARLY_WIN, LATE_WIN):
        w = sim[(sim[:, 0] >= lo) & (sim[:, 0] <= hi)]
        o, _ = clock_offset(w, gt)
        fits.append((float(np.mean(w[:, 0])), o))
    (t1, o1), (t2, o2) = fits
    to_sim = lambda t: t - (o1 + (o2 - o1) * (t - t1) / (t2 - t1))
    return to_sim, o1, o2, t1, t2


def of_records(trial):
    p = f"{TRIALS_DIR}/{trial}/ekf3/of.npy"
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        subprocess.run([PY_AP, "-c", _OF_DUMP, f"{TRIALS_DIR}/{trial}/ardupilot.bin", p], check=True)
    return np.load(p)


def stamp(h):
    return h.stamp.sec + h.stamp.nanosec * 1e-9


def analyse(trial):
    stamps = {k: [] for k in INPUTS}
    gt, flow = [], []
    with Reader(f"{TRIALS_DIR}/{trial}/bag") as r:
        conns = [c for c in r.connections if c.topic in list(INPUTS) + ["/ground_truth/pose"]]
        for con, _, raw in r.messages(connections=conns):
            m = ts.deserialize_cdr(raw, con.msgtype)
            if con.topic == "/ground_truth/pose":
                gt.append((stamp(m.header), m.pose.position.x, m.pose.position.y, m.pose.position.z))
                continue
            stamps[con.topic].append(stamp(m.header))
            if con.topic == "/optical_flow/measurement" and m.valid:
                flow.append((stamp(m.header), m.flow_x_rad, m.flow_y_rad))
    gt = np.array(sorted(gt))
    t0, t1 = cruise_bounds(gt[:, 0], gt[:, 1], gt[:, 2])
    out = {"cruise_s": [t0, t1], "inputs": {}}
    for k, nominal in INPUTS.items():
        s = np.sort(np.array(stamps[k]))
        s = s[(s >= t0) & (s <= t1)]
        d = np.diff(s)
        out["inputs"][k] = {"n": int(len(s)), "rate_hz": float((len(s) - 1) / (s[-1] - s[0])),
                            "gap_mean_ms": float(1e3 * np.mean(d)),
                            "gap_median_ms": float(1e3 * np.median(d)), "gap_p99_ms": float(1e3 * np.percentile(d, 99)),
                            "pct_gap_gt_1.5x": float(100 * (d > 1.5 * np.median(d)).mean())}
    to_sim, o1, o2, ta, tb = clock_map(sim_truth(trial), gt)
    out["clock_offset_ms"] = 1e3 * (o1 + o2) / 2       # mean TimeUS-minus-sim offset (diagnostic)
    out["clock_offset_early_late_ms"] = [1e3 * o1, 1e3 * o2]
    out["clock_rate_diff_pct"] = 100 * (o2 - o1) / (tb - ta)
    of = of_records(trial)
    key = lambda fx, fy: (np.float32(fx).tobytes(), np.float32(fy).tobytes())
    of_t = {}
    for t, fx, fy in of:
        of_t.setdefault(key(fx, fy), t)             # first log of that sample
    fl = np.array(flow)
    fl = fl[(fl[:, 0] >= t0) & (fl[:, 0] <= t1)]
    # The bridge's X sign changed on 2026-09-29 (lateral-sign fix: -flow_x_rad -> +flow_x_rad).
    # Use whichever sign actually matches this trial's OF log, and record it.
    n_by = {sx: sum(key(sx * fx, fy) in of_t for _, fx, fy in fl) for sx in (-1.0, 1.0)}
    sx = max(n_by, key=n_by.get)
    out["bridge_flow_x_sign"] = sx
    lat = [to_sim(of_t[key(sx * fx, fy)]) - t for t, fx, fy in fl if key(sx * fx, fy) in of_t]
    lat = 1e3 * np.array(lat)
    out["flow_to_ekf3"] = {"valid_frames": int(len(fl)), "matched_pct": float(100 * len(lat) / len(fl)),
                           "lat_median_ms": float(np.median(lat)), "lat_p5_ms": float(np.percentile(lat, 5)),
                           "lat_p95_ms": float(np.percentile(lat, 95)), "lat_p99_ms": float(np.percentile(lat, 99)),
                           "lat_max_ms": float(lat.max())}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("trials", nargs="+")
    ap.add_argument("--json")
    a = ap.parse_args()
    res = {t: analyse(t) for t in a.trials}
    for t, r in res.items():
        f = r["flow_to_ekf3"]
        print(f"{t:22} clock offset early/late {r['clock_offset_early_late_ms'][0]:+7.2f}/{r['clock_offset_early_late_ms'][1]:+7.2f} ms (rate {r['clock_rate_diff_pct']:+.4f}%)")
        print(f"{'':22} flow->EKF3 matched {f['matched_pct']:5.1f}%  latency median {f['lat_median_ms']:6.1f} "
              f"p5 {f['lat_p5_ms']:6.1f} p95 {f['lat_p95_ms']:6.1f} p99 {f['lat_p99_ms']:6.1f} max {f['lat_max_ms']:6.1f} ms")
        for k, v in r["inputs"].items():
            print(f"{'':22}   {k:28} {v['rate_hz']:8.2f} Hz  gap mean {v['gap_mean_ms']:7.4f} med {v['gap_median_ms']:6.2f} "
                  f"p99 {v['gap_p99_ms']:6.2f} ms  >1.5x {v['pct_gap_gt_1.5x']:5.2f}%")
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
