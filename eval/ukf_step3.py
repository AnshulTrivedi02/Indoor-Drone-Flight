#!/usr/bin/env python3
"""UKF port validation STEP 3 (a REPORT, not pass/fail; METHODOLOGY "Step 1 ... Step 3"): the cost of
the port's ArduPilot input path, attributed by swapping ONE input at a time into the step-2 event
stream and driving the port harness (examples/UKF_Equiv) with each variant.

Inputs: the step-2 export with event times (eval/ukf_event_export.py -> PREFIX.npz), and the port's
own inputs as consumed in Replay of the same flight (ukf_inputs.csv, Tools/Replay with the step-3
input dump): 'I' rows = every update() call (DAL ms, INS delta angle/velocity FRD + dt, range as
seen), 'F' rows = every flow message delivered (DAL ms, quality, raw rates, AHRS-paired gyro).
DAL ms are mapped to the bag's sim clock with the /imu/time_ref lower envelope.

Variants (all start from the offline UKF's own initial state; only the named input changes):
  V0  step-2 stream (the offline UKF's inputs)                       -> must reproduce step 2
  V1  IMU path: predicts from the DAL INS deltas, accumulated by the port's own rule (EKF3's
      12 ms target, 400 Hz frames) instead of the bridged 333 Hz samples
  V2  flow gyro: the AHRS gyro ArduPilot pairs with each flow message (arrival window) instead of
      the frame-averaged /imu/data_raw gyro
  V3  flow timing: each flow fused at its ARRIVAL time (no delay buffer) instead of capture time
  V4  range: the port's own range sampling (DAL rangefinder, cm-quantised, >= 33 ms) instead of the
      bag's float ranges at their stamps
  V5  V1 + V2 + V3 + V4 together
  V3e flow fused at EKF3's time (the D5 delay buffer): arrival - 66 ms clamped to the 60 ms horizon
  V5e V1 + V2 + V3e + V4: the port WITH the delay buffer (ruling D5)
Reported per variant against the offline UKF (V0's Python states): position and yaw difference over
the pinned cruise window (at +60 s, +150 s, end, max), and the gate acceptance counts.
Usage (~/venv-evo): python3 eval/ukf_step3.py PREFIX UKF_INPUTS_CSV TRIAL [--json OUT]"""
import argparse, json, math, os, struct, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds

ap = argparse.ArgumentParser(); ap.add_argument("prefix"); ap.add_argument("inputs_csv"); ap.add_argument("trial")
ap.add_argument("--json"); a = ap.parse_args()
HARNESS = os.path.expanduser("~/ardupilot_ukf/build/sitl/examples/UKF_Equiv")
e = np.load(a.prefix + ".npz")
typ, inp, xpy, tpy = e["type"], e["inputs"], e["x_after"], e["time"]
x0, P0 = e["x0"], e["P0"]

# ---- clock map DAL ms (SITL) -> sim s, from the bag's /imu/time_ref ----
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
ts = get_typestore(Stores.ROS2_JAZZY); pr = []
with Reader(os.path.expanduser(f"~/thesis_data/trials/{a.trial}/bag")) as rd:
    for con, _, raw in rd.messages(connections=[c for c in rd.connections if c.topic == "/imu/time_ref"]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        pr.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
pr = np.array(pr); dd = pr[:, 1] - pr[:, 0]; env = []
for lo in np.arange(pr[:, 0].min(), pr[:, 0].max(), 5.0):
    q = (pr[:, 0] >= lo) & (pr[:, 0] < lo + 5)
    if q.sum() > 50:
        i = np.argmin(dd[q]); env.append((pr[q, 0][i], dd[q][i]))
env = np.array(env); kk, cc = np.polyfit(env[:, 0], env[:, 1], 1)
to_sim = lambda sitl_s: sitl_s + kk * sitl_s + cc

# ---- the port's inputs (Replay dump) ----
I, Fr = [], []
for line in open(a.inputs_csv):
    f = line.rstrip().split(",")
    if f[0] == "I":
        I.append([float(v) for v in f[1:]])
    elif f[0] == "F":
        Fr.append([float(v) for v in f[1:]])
I, Fr = np.array(I), np.array(Fr)            # I: ms, dax, day, daz, dta, dvx, dvy, dvz, dtv, rng ; F: ms, msecMeas, q, rx, ry, gx, gy
tI, tF = to_sim(I[:, 0] / 1e3), to_sim(Fr[:, 0] / 1e3)
t_start = tpy[0]

# V1: predicts by the port's accumulation rule, from the first DAL frame after the offline init
pred = []
da, dv, dtacc = np.zeros(3), np.zeros(3), 0.0
for k in np.where(tI >= t_start)[0]:
    r = I[k]
    if r[4] <= 0 or r[8] <= 0:
        continue
    da += r[1:4]; dv += r[5:8]; dtacc += 0.5 * (r[4] + r[8])
    if dtacc >= 0.012 - 0.5 * r[4]:
        pred.append((tI[k], 0, [*da, *dv, dtacc])); da, dv, dtacc = np.zeros(3), np.zeros(3), 0.0
# V4: range as the port samples it (rng > 0, >= 33 ms apart, DAL time)
rng_ev, last = [], -1e9
for k in np.where(tI >= t_start)[0]:
    if I[k, 9] > 0 and I[k, 0] - last >= 33:
        rng_ev.append((tI[k], 1, [I[k, 9], 0, 0, 0, 0, 0, 0])); last = I[k, 0]
# V2/V3: match each delivered flow (quality > 0) to its bag frame BY VALUE (float32 via MAVLink)
fl_idx = np.where(typ == 2)[0]
fq = Fr[Fr[:, 2] > 0]; tfq = tF[Fr[:, 2] > 0]
match = {}
fq32 = fq[:, 3:5].astype(np.float32)
for k in fl_idx:                  # exact float32 value match, arrival within [capture - 10 ms, capture + 300 ms]
    lo, hi = np.searchsorted(tfq, tpy[k] - 0.01), np.searchsorted(tfq, tpy[k] + 0.3)
    fx, fy = np.float32(inp[k, 0]), np.float32(inp[k, 1])
    hit = np.where((fq32[lo:hi, 0] == fx) & (fq32[lo:hi, 1] == fy))[0]
    if len(hit):
        match[k] = lo + int(hit[0])
lat = np.array([tfq[j] - tpy[k] for k, j in match.items()])


FLOW_EKF3_OFFSET_S = 0.060   # ruling D5: EKF3's flow time, arrival - 10 - 100/2 - 12/2 = arrival - 66 ms, clamped to the
                             # 60 ms horizon (AP_NavEKF3_Measurements.cpp:232-236) -> arrival - 60 ms


def build(v1=False, v2=False, v3=False, v4=False, v3e=False, v3c=False):
    evs = []
    for k in range(len(typ)):
        t_, ty = tpy[k], int(typ[k])
        if ty == 0 and v1:
            continue
        if ty == 1 and v4:
            continue
        row = list(inp[k])
        if ty == 2 and k in match:
            j = match[k]
            if v2:
                row[2], row[3] = fq[j, 5], fq[j, 6]
            if v3:
                t_ = tfq[j]
            if v3e:
                t_ = tfq[j] - FLOW_EKF3_OFFSET_S
            if v3c:                            # DIAGNOSTIC: the offline UKF's own time (capture), via arrival - measured latency
                t_ = tpy[k]
        evs.append((t_, ty, row))
    if v1:
        evs += pred
    if v4:
        evs += rng_ev
    evs.sort(key=lambda z: (z[0], z[1]))
    return evs


def run(evs, name):
    base = f"{a.prefix}_s3_{name}"
    with open(base + ".bin", "wb") as f:
        f.write(b"UKFEV001"); f.write(struct.pack("<15d", *x0)); f.write(struct.pack("<225d", *P0.ravel()))
        f.write(struct.pack("<Q", len(evs)))
        for _, ty, row in evs:
            f.write(struct.pack("<b7d", ty, *row))
    subprocess.run([HARNESS], env={**os.environ, "UKF_EQ_IN": base + ".bin", "UKF_EQ_OUT": base + "_port.bin"},
                   check=True, stdout=subprocess.DEVNULL)
    raw = np.fromfile(base + "_port.bin", dtype=np.uint8).reshape(len(evs), 122)
    xs = raw[:, :120].copy().view(np.float64).reshape(len(evs), 15); fls = raw[:, 120:].astype(np.int8)
    return np.array([z[0] for z in evs]), np.array([z[1] for z in evs]), xs, fls


gt = np.loadtxt(a.prefix + "_replay_out/ukf/ground_truth.tum")
c0, c1 = cruise_bounds(gt[:, 0], gt[:, 1], gt[:, 2])
pyp = np.where(typ == 0)[0]                     # compare at the offline UKF's predict instants
tpp = tpy[pyp]
out = {"trial": a.trial, "window_s": [float(c0), float(c1)], "flow_matched": len(match), "flow_delivered_q_gt0": int(len(fq)),
       "flow_arrival_minus_capture_ms": {q: float(1e3 * np.percentile(lat, p)) for q, p in (("min", 0), ("median", 50), ("p95", 95), ("max", 100))},
       "clock_map": {"offset_ms": float(1e3 * (kk * env[0, 0] + cc)), "rate_ppm": float(1e6 * kk)}, "variants": {}}
for name, kw in (("V0", {}), ("V1_imu", {"v1": True}), ("V2_flow_gyro", {"v2": True}), ("V3_flow_arrival", {"v3": True}),
                 ("V4_range", {"v4": True}), ("V5_all", {"v1": True, "v2": True, "v3": True, "v4": True}),
                 ("V3e_flow_ekf3_time", {"v3e": True}), ("V5e_all_ekf3_time", {"v1": True, "v2": True, "v3e": True, "v4": True}),
                 ("V5c_all_capture_time_DIAG", {"v1": True, "v2": True, "v3c": True, "v4": True})):
    tv, ty, xs, fls = run(build(**kw), name)
    # port state at each offline predict instant: last port event at or before it
    idx = np.searchsorted(tv, tpp, side="right") - 1
    dp = np.linalg.norm(xs[idx, 0:3] - xpy[pyp, 0:3], axis=1)
    dy = np.degrees(np.abs((xs[idx, 8] - xpy[pyp, 8] + math.pi) % (2 * math.pi) - math.pi))
    w = (tpp >= c0) & (tpp <= c1)
    at = lambda s: int(np.argmin(np.abs(tpp - (c0 + s))))
    out["variants"][name] = {"dpos_m": {"+60s": float(dp[at(60)]), "+150s": float(dp[at(150)]), "end": float(dp[w][-1]), "max": float(dp[w].max())},
                             "dyaw_deg": {"+60s": float(dy[at(60)]), "+150s": float(dy[at(150)]), "end": float(dy[w][-1]), "max": float(dy[w].max())},
                             "flow_accepted_xy": [int(fls[ty == 2, 0].sum()), int(fls[ty == 2, 1].sum())],
                             "range_accepted": int(fls[ty == 1, 0].sum()), "yaw_fired": int(fls[ty == 3, 0].sum()), "predicts": int((ty == 0).sum())}
    print(name, json.dumps(out["variants"][name]))
print(json.dumps({k: v for k, v in out.items() if k != "variants"}))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
