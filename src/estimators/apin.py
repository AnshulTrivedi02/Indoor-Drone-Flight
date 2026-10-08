"""Input-path diagnostic (user ruling 2026-10-08): OFF-by-default substitution of the offline UKF's bag inputs by the
inputs EKF3 consumed inside ArduPilot (eval/apin_extract.py -> <trial>/apin/ap_inputs.npz). DIAGNOSTIC ONLY.

Env UKF_APIN (unset = off; the replays' default path never imports this module's effect):
  imu   /imu/data_raw replaced by the FC's INS deltas (RISI instance 0, one per FC frame, on the bag clock). Each
        event carries (accel = DV/DADT, gyro = DA/DADT, DADT), so the replay's sums reproduce DA and DV exactly. The
        same stream feeds the frame-averaged flow-derotation gyro and the take-off detector, as the bag IMU does.
  flow  /optical_flow/measurement replaced by ROFH: the flow as delivered to EKF3 (camera-frame values), stamped on
        EKF3's / the UKF port's time rule (arrival - 60 ms), with EKF3's derotation gyro (AP_OpticalFlow_MAV bodyRate,
        FLU x/y) in place of the frame-averaged IMU gyro. Valid = Qual > 0, inlier = Qual / 255.
  both  imu + flow.
Split of the flow path (added after the first results, 2026-10-08; DIAGNOSTIC):
  flowgyro  bag flow values and capture stamps; derotation gyro = ROFH bodyRate of the same frame (paired by value).
  flowtime  ROFH values at EKF3's time (arrival - 60 ms); derotation gyro = the bag-IMU frame average (as (a)).
  biascorr  NO input substitution: bag inputs, but h_flow derotates with (gyro average - the UKF's own gyro-bias
            estimate), as EKF3 (delAngCorrected, flowGyroBias) and the FGO do. A FORMULATION variant, not an input one.
Range, tags, attitude rates: unchanged (bag)."""
import os
import numpy as np

MODES = {"imu": ("imu",), "flow": ("flow",), "both": ("imu", "flow"), "flowgyro": (), "flowtime": ("flow",), "biascorr": ()}


def mode():
    m = os.environ.get("UKF_APIN", "")
    if m and m not in MODES:
        raise SystemExit(f"UKF_APIN={m!r}: expected one of {sorted(MODES)}")
    return m


def outdir_suffix(m):
    return "" if not m else ("_apin" if m == "both" else f"_apin_{m}")


def substitute(ev, trial_dir, m):
    z = np.load(f"{trial_dir}/apin/ap_inputs.npz")
    parts = MODES[m]
    keep = [e for e in ev if e[1] not in parts]
    if "imu" in parts:
        dt = z["imu_dt"]
        acc = z["imu_dv"] / dt[:, None]; gyr = z["imu_da"] / dt[:, None]
        keep += [(float(t), "imu", (acc[i], gyr[i], float(dt[i]))) for i, t in enumerate(z["imu_t"])]
    if "flow" in parts:
        q = z["flow_qual"]
        g = (lambda i: (z["flow_gyro"][i].astype(float),)) if m != "flowtime" else (lambda i: ())
        keep += [(float(t), "flow", (z["flow_xy"][i].astype(float), bool(q[i] > 0), float(q[i]) / 255.0) + g(i))
                 for i, t in enumerate(z["flow_t"])]
    if m == "flowgyro":
        gmap = {round(float(tb), 6): z["flow_gyro"][k].astype(float) for k, tb in zip(z["pair_rofh"], z["pair_bag_t"])}
        keep = [(e[0], e[1], e[2] + (gmap[round(e[0], 6)],)) if e[1] == "flow" and round(e[0], 6) in gmap else e for e in keep]
    return keep


def imu_period_stats(ev):
    """Stand-in for dejitter_imu's stats when the IMU is the FC's (already on the FC clock): no re-stamping."""
    dt = np.array([e[2][2] for e in ev if e[1] == "imu"])
    return ev, {"period_ms": 1e3 * float(np.median(dt)), "resid_std_ms": 0.0, "resid_maxabs_ms": 0.0}
