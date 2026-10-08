#!/usr/bin/env python3
"""Input-path diagnostic (user ruling 2026-10-08; docs/handovers/2026-10-08_input_path_diagnostic.md): extract the
inputs EKF3 consumed INSIDE ArduPilot from a flight's dataflash Replay records, on the bag clock, for the OFF-by-default
`UKF_APIN` option of ukf_replay.py / room_ukf_replay.py. DIAGNOSTIC ONLY: no thesis result uses it.

  IMU   RISI (instance 0 = EKF3 core 0's IMU), one record per FC frame, paired with that frame's RFRH TimeUS:
        DAX..DAZ / DVX..DVZ = the delta angle / delta velocity the INS accumulated since the last frame (what
        EKF3's readIMUData consumes through DAL), DADT/DVDT their integration times. FRD -> FLU = (x, -y, -z).
  Flow  ROFH (DAL's record of each writeOptFlowMeas call): FX, FY = rawFlowRates (the MAVLink flow_rate_x/y as
        received), GX, GY = rawGyroRates (AP_OpticalFlow_MAV's bodyRate, the FC's AHRS gyro averaged between flow
        messages, FRD), Tms = msecFlowMeas, Qual = rawFlowQuality. Time on EKF3's rule: Tms - EK3_FLOW_DELAY
        - 50 - 6 ms, clamped to the 60 ms horizon (= Tms - 60 ms; the UKF port's rule).
  Clock TimeUS / Tms -> bag clock by the /imu/time_ref lower envelope (receipt - HIGHRES_IMU time_usec, the 5 s-window
        minimum, linear fit), exactly eval/h_score.py's map.

Also quantifies the bag-vs-FC input differences (written to the JSON): IMU rate/filter/lag, flow time offset, flow
value match and the derotation-gyro difference.

Usage (venv-tags: rosbags + pymavlink):  python3 eval/apin_extract.py <trial> [--trials-dir DIR]
Writes <trials-dir>/<trial>/apin/ap_inputs.npz and apin/extract_stats.json."""
import argparse, glob, json, math, os
import numpy as np
from pymavlink import DFReader
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg

ap = argparse.ArgumentParser(); ap.add_argument("trial")
ap.add_argument("--trials-dir", default=os.path.expanduser("~/thesis_data/trials")); a = ap.parse_args()
D = f"{a.trials_dir}/{a.trial}"; OUT = f"{D}/apin"; os.makedirs(OUT, exist_ok=True)
ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/src/optical_flow_interfaces/msg/OpticalFlow.msg"))[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9

# ---------- bag: /imu/time_ref (clock map), /imu/data_raw and flow (for the comparison only) ----------
TR, BI, BF = [], [], []
with Reader(f"{D}/bag") as r:
    cs = {c.topic: c for c in r.connections}
    for con, _, raw in r.messages(connections=[cs[x] for x in ("/imu/time_ref", "/imu/data_raw", "/optical_flow/measurement")]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, st(m.header)))
        elif con.topic == "/imu/data_raw":
            BI.append((st(m.header), m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z,
                       m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z))
        else:
            BF.append((st(m.header), m.flow_x_rad, m.flow_y_rad, float(m.valid), m.inlier_ratio))
TR, BI, BF = np.array(TR), np.array(BI), np.array(BF)
sitl, dd = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):          # eval/h_score.py's envelope, verbatim in effect
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(dd[w]); env.append((sitl[w][i], dd[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
to_bag = lambda x: x + (kk * x + c0)

# ---------- dataflash Replay records ----------
f = DFReader.DFReader_binary(f"{D}/ardupilot.bin")
fr_t = None; imu = []; flo = []; par = {}
for m in iter(f.recv_msg, None):
    t = m.get_type()
    if t == "RFRH":
        fr_t = m.TimeUS * 1e-6
    elif t == "RISI" and m.I == 0 and fr_t is not None:
        imu.append((fr_t, m.DADT, m.DVDT, m.DAX, m.DAY, m.DAZ, m.DVX, m.DVY, m.DVZ))
    elif t == "ROFH":
        flo.append((fr_t if fr_t is not None else np.nan, m.Tms * 1e-3, m.FX, m.FY, m.GX, m.GY, m.Qual))
    elif t == "PARM" and m.Name in ("EK3_FLOW_DELAY", "INS_GYRO_FILTER", "INS_ACCEL_FILTER", "LOG_REPLAY",
                                    "SCHED_LOOP_RATE", "FLOW_OPTIONS", "FLOW_FXSCALER", "FLOW_FYSCALER", "FLOW_ORIENT_YAW"):
        par[m.Name] = float(m.Value)
imu = np.array(imu); flo = np.array(flo)
assert par.get("LOG_REPLAY") == 1.0, par
ok = imu[:, 1] > 0
imu = imu[ok]
dt = imu[:, 1]
da = np.c_[imu[:, 3], -imu[:, 4], -imu[:, 5]]                # FRD -> FLU
dv = np.c_[imu[:, 6], -imu[:, 7], -imu[:, 8]]
t_imu = to_bag(imu[:, 0])
FLOW_DELAY = par["EK3_FLOW_DELAY"] * 1e-3
# EKF3's flow time (AP_NavEKF3_Measurements.cpp:232-236): arrival - EK3_FLOW_DELAY - flowTimeDeltaAvg_ms/2 (100/2,
# AP_NavEKF3.h:511) - localFilterTimeStep_ms/2 (12/2), clamped to the delayed horizon (EK3_HGT_DELAY 60 ms, the largest
# delay: AP_NavEKF3_core.cpp:42-46). The UKF port's rule exactly (AP_NavUKF.cpp:37, flow block of update()):
# max(Tms - 66, Tms - 60) = Tms - 60 ms. Arrival = Tms (the DAL ms of the writeOptFlowMeas call).
t_flow = to_bag(flo[:, 1] - min(FLOW_DELAY + 0.050 + 0.006, 0.060))
# EKF3 alone also rate-limits flow to >= sensorIntervalMin_ms = 50 ms between accepted calls
# (AP_NavEKF3_Measurements.cpp:178-180, AP_NavEKF3.h:516); the port does not. Recorded, not applied.
acc50 = np.zeros(len(flo), bool); last = -1e9
for k in range(len(flo)):
    if flo[k, 1] - last >= 0.050 - 1e-9:
        acc50[k] = True; last = flo[k, 1]
t_flow_tms = to_bag(flo[:, 1])

# ---------- flow axis mapping (empirical, per flight): ROFH FX/FY vs the bag's camera-frame flow ----------
bfv = BF[BF[:, 3] > 0]
j = np.searchsorted(bfv[:, 0], t_flow_tms)
pairs = []
for k, jj in enumerate(j):        # nearest bag flow with |value| match: the bridge sends each valid frame once
    best = None
    for q in (jj - 2, jj - 1, jj, jj + 1, jj + 2):
        if 0 <= q < len(bfv):
            e = min(abs(abs(flo[k, 2]) - abs(bfv[q, 1])) + abs(abs(flo[k, 3]) - abs(bfv[q, 2])), 1e9)
            if best is None or e < best[0]:
                best = (e, q)
    if best and best[0] < 1e-5 and (abs(flo[k, 2]) + abs(flo[k, 3])) > 1e-3:
        pairs.append((k, best[1]))
pairs = np.array(pairs)
sx = float(np.sign(np.median(flo[pairs[:, 0], 2] * bfv[pairs[:, 1], 1])))
sy = float(np.sign(np.median(flo[pairs[:, 0], 3] * bfv[pairs[:, 1], 2])))
flow_xy = np.c_[sx * flo[:, 2], sy * flo[:, 3]]               # camera-optical frame, as the bag's flow_x_rad/flow_y_rad
gyro_flu = np.c_[flo[:, 4], -flo[:, 5]]                       # bodyRate FRD (roll, pitch) -> FLU (x, y)
lag_cap = t_flow[pairs[:, 0]] - bfv[pairs[:, 1], 0]                         # EKF3 flow time - bag capture stamp, same frame
lag_tms = t_flow_tms[pairs[:, 0]] - bfv[pairs[:, 1], 0]

# ---------- IMU comparison: FC delta rate vs the bag's 20 Hz-filtered instantaneous sample ----------
w_fc = da / dt[:, None]; a_fc = dv / dt[:, None]
tc = t_imu - dt / 2                                           # centre of each delta interval
air = (tc > tc[0] + 30) & (tc < tc[-1] - 30)
bt = BI[:, 0]
def lag_xcorr(ch_fc, ch_bag):
    g = np.arange(tc[air][0] + 5, tc[air][-1] - 5, 0.001)
    x = np.interp(g, tc, ch_fc); best = None
    for L in np.arange(-0.040, 0.0405, 0.0005):
        y = np.interp(g + L, bt, ch_bag)
        c = np.corrcoef(x - x.mean(), y - y.mean())[0, 1]
        if best is None or c > best[1]:
            best = (L, c)
    return best
lags = {n: lag_xcorr(w_fc[:, i], BI[:, 1 + i]) for i, n in enumerate(("gx", "gy", "gz"))}
lags.update({n: lag_xcorr(a_fc[:, i], BI[:, 4 + i]) for i, n in enumerate(("ax", "ay", "az"))})
# per 15 ms step: integrated delta difference (bag rectangular sum of dejitter-free stamps vs FC deltas), RMS
g15 = np.arange(tc[air][0] + 5, tc[air][-1] - 5, 0.015)
cum_fc = np.cumsum(da, 0); cum_fc_t = t_imu
bdt = np.diff(bt, prepend=bt[0]); cum_b = np.cumsum(BI[:, 1:4] * bdt[:, None], 0)
step = lambda T, C, g: np.diff(np.c_[[np.interp(g, T, C[:, i]) for i in range(3)]].T, axis=0)
d15 = step(cum_fc_t, cum_fc, g15) - step(bt, cum_b, g15)
cum_vfc = np.cumsum(dv, 0); cum_vb = np.cumsum(BI[:, 4:7] * bdt[:, None], 0)
v15 = step(cum_fc_t, cum_vfc, g15) - step(bt, cum_vb, g15)
# derotation gyro: ROFH bodyRate vs the bag-IMU frame average over the same flow interval
bcap = bfv[pairs[:, 1], 0]; prevcap = np.r_[np.nan, bcap[:-1]]
cb = np.cumsum(BI[:, 1:3] * bdt[:, None], 0)
okp = (bcap > tc[0] + 30) & (bcap < tc[-1] - 30) & (bcap - prevcap > 0.01) & (bcap - prevcap < 0.1)
avg_bag = np.c_[[(np.interp(bcap[okp], bt, cb[:, i]) - np.interp(prevcap[okp], bt, cb[:, i])) / (bcap[okp] - prevcap[okp]) for i in range(2)]].T
gdiff = gyro_flu[pairs[okp, 0]] - avg_bag

stats = {
    "trial": a.trial, "params": par,
    "clock_map": {"k": float(kk), "c0_s": float(c0), "n_env": int(len(env))},
    "imu": {"n_frames": int(len(imu)), "frame_dt_ms": {"median": float(1e3 * np.median(np.diff(imu[:, 0]))),
            "p1": float(1e3 * np.percentile(np.diff(imu[:, 0]), 1)), "p99": float(1e3 * np.percentile(np.diff(imu[:, 0]), 99))},
            "DADT_ms": {"median": float(1e3 * np.median(dt)), "min": float(1e3 * dt.min()), "max": float(1e3 * dt.max())},
            "sum_DADT_over_span": float(dt.sum() / (imu[-1, 0] - imu[0, 0])),
            "bag_minus_fc_lag_s_and_corr": {k: [float(v[0]), float(v[1])] for k, v in lags.items()},
            "delta_angle_15ms_diff_rms_rad": [float(x) for x in np.sqrt(np.mean(d15 ** 2, 0))],
            "delta_vel_15ms_diff_rms_mps": [float(x) for x in np.sqrt(np.mean(v15 ** 2, 0))],
            "delta_vel_15ms_diff_mean_mps": [float(x) for x in np.mean(v15, 0)],
            "delta_angle_15ms_diff_mean_rad": [float(x) for x in np.mean(d15, 0)],
            "rate_rms_fc_air": [float(x) for x in np.sqrt(np.mean(w_fc[air] ** 2, 0))]},
    "flow": {"n_rofh": int(len(flo)), "n_paired_to_bag": int(len(pairs)), "sign_x": sx, "sign_y": sy,
             "ekf3_time_minus_capture_ms": {"median": float(1e3 * np.median(lag_cap)), "p5": float(1e3 * np.percentile(lag_cap, 5)),
                                            "p95": float(1e3 * np.percentile(lag_cap, 95))},
             "tms_minus_capture_ms": {"median": float(1e3 * np.median(lag_tms)), "p5": float(1e3 * np.percentile(lag_tms, 5)),
                                      "p95": float(1e3 * np.percentile(lag_tms, 95))},
             "qual_zero_share": float(np.mean(flo[:, 6] == 0)),
             "ekf3_50ms_rate_limit_accept_share": float(acc50.mean()),
             "derot_gyro_rofh_minus_bag_frame_avg": {"n": int(okp.sum()), "rms_rad_s": [float(x) for x in np.sqrt(np.mean(gdiff ** 2, 0))],
                                                     "mean_rad_s": [float(x) for x in gdiff.mean(0)],
                                                     "bag_avg_rms_rad_s": [float(x) for x in np.sqrt(np.mean(avg_bag ** 2, 0))],
                                                     "slope_rofh_on_bag": [float(np.polyfit(avg_bag[:, i], gyro_flu[pairs[okp, 0], i], 1)[0]) for i in range(2)]}},
}
np.savez_compressed(f"{OUT}/ap_inputs.npz", imu_t=t_imu, imu_dt=dt, imu_da=da, imu_dv=dv, flow_t=t_flow,
                    flow_xy=flow_xy, flow_gyro=gyro_flu, flow_qual=flo[:, 6], pair_rofh=pairs[:, 0], pair_bag_t=bfv[pairs[:, 1], 0])
json.dump(stats, open(f"{OUT}/extract_stats.json", "w"), indent=1)
print(json.dumps(stats, indent=1))
