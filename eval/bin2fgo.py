#!/usr/bin/env python3
"""Rung 1, item R1: ArduPilot dataflash (LOG_REPLAY=1) -> the FGO's input event stream.

docs/minimal_real_flight_plan.md §4.3; handover docs/handovers/2026-10-10_r1_converter.md.

  python3 eval/bin2fgo.py <log.BIN> -o <out.npz> --flow-delay-ms D --range-delay-ms D
                          [--imu-instance 0] [--range-instance auto] [--truth sim2|none] [--t-end S]

Writes <out.npz> (arrays) and <out.json> (metadata: every PARM value read, the geometry, delays, measured rates,
checks, the BIN sha256 and the code commit). fgo_replay.py reads the npz through its OFF-BY-DEFAULT events mode
(env FGO_EVENTS=<out.npz>); without that variable the FGO's bag path is unchanged.

ONE CLOCK: everything is on the flight controller's TimeUS (s). No Pi <-> FC map is needed for rung 1.

IMU (RISI, the DAL replay record = exactly the deltas EKF3 consumes; 400 Hz frames)
  - instance --imu-instance (default 0 = EKF3 core 0's IMU under the default EK3_IMU_MASK; checked against PARM);
  - acc = DV/DVDT, gyro = DA/DADT (FRD), -> FLU as (x, -y, -z); the deltas are accumulated from the RAW samples,
    before the INS low-pass filters (AP_InertialSensor_Backend.cpp:364-371), so no filter delay;
  - stamped at the RFRH frame time (the frame that carries them) minus --imu-delay-ms (default 0);
  - dt = DVDT is carried in the payload (the FGO integrates over the INS's own interval, not the stamp spacing);
  - samples whose 'ret'/'use' flags are not all set are dropped (counted); gaps from RFRH continuity and DSF.Dp.

FLOW (OF = AP_OpticalFlow::Log_Write_Optflow, written in update_state right after writeOptFlowMeas, so OF.TimeUS is
the FC arrival time; ROFH carries the identical values for EKF3 and is cross-checked)
  - flowX/flowY are the RAW (NOT body-rate compensated) sensor rates in rad/s, after FLOW_ORIENT_YAW and the
    FXSCALER/FYSCALER scalers (AP_OpticalFlow_*: _applyYaw(flowRate), scaling), in ArduPilot's flow convention:
    a RH body rotation gives a POSITIVE rate (AP_OpticalFlow.h:114). EKF3 negates them (AP_NavEKF3_Measurements.cpp:221)
    and adds bodyRate (:227-228). That convention IS the FGO's h_flow_pose convention (flow_x = +w_x + v_left/h,
    flow_y = -w_y(FLU) + v_fwd/h = +w_y(FRD) + v_fwd/h; EKF3 losPred at AP_NavEKF3_OptFlowFusion.cpp:334-335), so
    the mapping is the IDENTITY: flow_x_rad := flowX, flow_y_rad := flowY (as flow_bridge.py sends +flow_x_rad).
  - bodyX/bodyY are the body rates the backend averaged over the flow interval. For the MAV and Pixart backends that
    is AP::ahrs().get_gyro() (AP_OpticalFlow_MAV.cpp:39, AP_OpticalFlow_Pixart.cpp:291), i.e. the INS-filtered gyro
    MINUS THE ACTIVE EKF's GYRO BIAS (AP_AHRS.cpp:777-780 under AHRS_EKF_TYPE=3). HereFlow sends its own gyro.
    They are therefore NOT used by the FGO (that would hand it EKF3's bias estimate and correct the bias twice):
    the FGO derotates with its OWN raw-gyro interval average (FlowFrameGyroAverager over the RISI gyro) minus its
    own bias, exactly as in the simulation. bodyX/Y are kept in the npz for diagnostics only.
  - validity (stated rule, EKF3's own, AP_NavEKF3_Measurements.cpp:203): valid := Qual > 0. There is no inlier
    ratio; inlier := Qual/255 is a pass-through so the FGO's gate (valid and inlier > 0 and |rate| < 4.2) reduces
    to EKF3's (Qual > 0 and |flowRate| < 4.2). The camera-path rule (inlier >= 0.85, features >= 20) does NOT apply.
  - time (ruling 2026-10-10, METHODOLOGY "freeze scope; real-log flow timestamps"): the best estimate of the TRUE
    capture time = arrival - d_flow, d_flow = --flow-delay-ms, defined as arrival minus the END of the sensor's
    integration interval (the sim convention: the bag's flow stamp is the newer camera frame, the end of the flow
    interval), so the FGO's (previous flow, this flow] derotation window keeps its meaning. The value is to be
    PRE-REGISTERED from real data with eval/sensor_timing_from_log.py; the flight's measured rate is recorded.

RANGE (RRNI, the DAL record of what EKF3 reads, written ONLY ON CHANGE at the frame where the change is seen)
  - instance with Orient == 25 (down); valid only while Status == 4 (Good) and RNGFND1_MIN <= d <= RNGFND1_MAX;
  - the held value is emitted at the backend update period measured from the log (median spacing of consecutive
    changes), phase-anchored at each change (a new reading with an unchanged value is not logged by the DAL);
  - time = emission - d_range (--range-delay-ms, pre-registered like the flow delay).

GEOMETRY from PARM (never hard-coded): FLOW_POS_X/Y/Z, RNGFND<n>_POS_X/Y/Z, RNGFND<n>_MIN/MAX, RNGFND<n>_ORIENT,
FLOW_ORIENT_YAW, FLOW_TYPE, scalers, EK3_FLOW_DELAY, RNGFND<n>_GNDCLEAR; ROFH.posOffset and RRNI.pos_offset must agree.

ARMING from the ARM record (ArmState 1). INIT height: the first Good range sample at or before the levelling end
(first IMU + 0.5 s) if there is one, else the first Good one before arming, else RRNH.GCl (= RNGFND_GNDCLEAR), which
covers a sensor that reads out of range on the ground.

TRUTH (diagnostics only, never an input): --truth sim2 (SITL logs) stores SIM2 as ENU (PE, PN, -PD) on the same clock.
"""
import argparse, hashlib, json, os, subprocess, sys
import numpy as np
from pymavlink import DFReader

NEED = ["RFRH", "RISI", "OF", "ROFH", "RRNI", "RRNH", "PARM", "ARM", "DSF", "SIM2"]
FRD2FLU = np.array([1.0, -1.0, -1.0])


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_bin(path, imu_inst, want_truth):
    r = DFReader.DFReader_binary(path, zero_time_base=False)
    types = [t for t in NEED if want_truth or t != "SIM2"]
    P = {}; frames = []; risi = []; of = []; rofh = []; rrni = []; rrnh = None; arm = []; dsf_dp = 0; sim2 = []
    t_frame = None
    while True:
        m = r.recv_match(type=types)
        if m is None:
            break
        k = m.get_type()
        if k == "RFRH":
            t_frame = m.TimeUS * 1e-6; frames.append(t_frame)
        elif k == "RISI":
            if m.I == imu_inst and t_frame is not None:
                risi.append((t_frame, m.DVX, m.DVY, m.DVZ, m.DAX, m.DAY, m.DAZ, m.DVDT, m.DADT, m.Flags))
        elif k == "OF":
            of.append((m.TimeUS * 1e-6, m.Qual, m.flowX, m.flowY, m.bodyX, m.bodyY))
        elif k == "ROFH":
            rofh.append((t_frame if t_frame is not None else np.nan, m.FX, m.FY, m.GX, m.GY, m.Tms, m.PX, m.PY, m.PZ, m.Qual))
        elif k == "RRNI":
            rrni.append((t_frame if t_frame is not None else np.nan, m.I, m.Dist, m.Status, m.Orient, m.PX, m.PY, m.PZ))
        elif k == "RRNH":
            rrnh = {"GCl": float(m.GCl), "MaxD": float(m.MaxD), "NumSensors": int(m.NumSensors)}
        elif k == "PARM":
            P[m.Name] = float(m.Value)
        elif k == "ARM":
            arm.append((m.TimeUS * 1e-6, int(m.ArmState)))
        elif k == "DSF":
            dsf_dp = max(dsf_dp, int(m.Dp))           # Dp is a running count of dropped blocks
        elif k == "SIM2":
            sim2.append((m.TimeUS * 1e-6, m.PE, m.PN, -m.PD))
    return (P, np.array(frames), np.array(risi), np.array(of), np.array(rofh), np.array(rrni), rrnh, arm, dsf_dp,
            np.array(sim2))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bin"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--flow-delay-ms", type=float, required=True,
                    help="arrival minus END of the flow integration interval (ms); pre-registered (0 is allowed, stated)")
    ap.add_argument("--range-delay-ms", type=float, required=True, help="range arrival minus measurement time (ms)")
    ap.add_argument("--imu-delay-ms", type=float, default=0.0)
    ap.add_argument("--imu-instance", type=int, default=0)
    ap.add_argument("--range-instance", default="auto", help="'auto' = the instance with Orient 25 (down)")
    ap.add_argument("--truth", choices=["sim2", "none"], default="none")
    ap.add_argument("--t-end", type=float, default=None, help="drop everything after this FC time (s); smoke tests only")
    a = ap.parse_args()

    P, frames, risi, of, rofh, rrni, rrnh, arm, dsf_dp, sim2 = read_bin(a.bin, a.imu_instance, a.truth == "sim2")
    chk = {}
    assert len(risi) and len(frames), "no RISI/RFRH: the log was not recorded with LOG_REPLAY=1"
    assert len(of), "no OF records: no optical-flow sensor logged"
    for k in ("FLOW_TYPE", "FLOW_POS_X", "FLOW_POS_Y", "FLOW_POS_Z"):
        assert k in P, f"PARM {k} missing"

    # ---------------- IMU ----------------
    t = risi[:, 0]; dv = risi[:, 1:4]; da = risi[:, 4:7]; dvdt = risi[:, 7]; dadt = risi[:, 8]; flags = risi[:, 9].astype(int)
    ok = ((flags & 15) == 15) & (dvdt > 0) & (dadt > 0)
    chk["imu_dropped_flags"] = int((~ok).sum())
    t, dv, da, dvdt, dadt = t[ok], dv[ok], da[ok], dvdt[ok], dadt[ok]
    acc = dv / dvdt[:, None] * FRD2FLU
    gyr = da / dadt[:, None] * FRD2FLU
    dtf = np.diff(t)
    per = float(np.median(np.diff(frames)))
    chk["imu_frame_period_ms_median"] = 1e3 * per
    chk["imu_rate_hz"] = 1.0 / per
    chk["imu_dvdt_ne_dadt"] = int((np.abs(dvdt - dadt) > 1e-6).sum())
    chk["imu_dvdt_vs_frame_dt_maxabs_ms"] = float(1e3 * np.max(np.abs(dvdt[1:] - dtf))) if len(dtf) else None
    chk["imu_dvdt_vs_frame_dt_n_gt_0p5ms"] = int((np.abs(dvdt[1:] - dtf) > 5e-4).sum())
    gaps = np.where(dtf > 2.5 * per)[0]
    chk["imu_gaps"] = [(float(t[i]), float(1e3 * dtf[i])) for i in gaps[:50]]
    chk["imu_n_gaps"] = int(len(gaps))
    chk["dsf_dropped_blocks"] = int(dsf_dp)
    t_imu = t - a.imu_delay_ms * 1e-3
    imu_dt = dvdt                 # the INS's own integration interval (DVDT; DADT differs on chk["imu_dvdt_ne_dadt"] samples)

    # ---------------- flow ----------------
    t_arr = of[:, 0]
    qual = of[:, 1].astype(int); fxy = of[:, 2:4]; bxy = of[:, 4:6]
    chk["flow_n"] = int(len(of))
    dfa = np.diff(t_arr)
    chk["flow_rate_hz_median"] = float(1.0 / np.median(dfa))
    chk["flow_interarrival_ms_p5_p50_p95"] = [float(1e3 * np.percentile(dfa, q)) for q in (5, 50, 95)]
    chk["flow_qual_gt0_frac"] = float(np.mean(qual > 0))
    if len(rofh) == len(of):
        chk["rofh_equals_of"] = bool(np.array_equal(rofh[:, 1:3].astype(np.float32), fxy.astype(np.float32))
                                     and np.array_equal(rofh[:, 3:5].astype(np.float32), bxy.astype(np.float32))
                                     and np.array_equal(rofh[:, 9].astype(int), qual))
    else:
        chk["rofh_equals_of"] = f"count differs: ROFH {len(rofh)} OF {len(of)}"
    if len(rofh):
        chk["rofh_posoffset_unique"] = np.unique(rofh[:, 6:9], axis=0).tolist()
    t_flow = t_arr - a.flow_delay_ms * 1e-3
    valid = qual > 0
    inlier = qual / 255.0

    # ---------------- range ----------------
    rng_inst = None
    if len(rrni):
        if a.range_instance == "auto":
            down = np.unique(rrni[rrni[:, 4] == 25, 1])
            assert len(down) >= 1, "no downward (Orient 25) rangefinder in RRNI"
            rng_inst = int(down[0])
        else:
            rng_inst = int(a.range_instance)
    assert rng_inst is not None, "no RRNI records"
    n = rng_inst + 1
    rmin = P.get(f"RNGFND{n}_MIN", 0.05); rmax = P.get(f"RNGFND{n}_MAX", 40.0)
    R = rrni[rrni[:, 1] == rng_inst]
    ch_t = R[:, 0]; ch_d = R[:, 2]; ch_s = R[:, 3].astype(int)
    good_ch = (ch_s == 4)
    dch = np.diff(ch_t[good_ch])
    dch = dch[(dch > 0.004) & (dch < 0.3)]
    T_r = float(np.median(dch)) if len(dch) else 0.05
    chk["range_update_period_ms_from_changes"] = 1e3 * T_r
    chk["range_n_changes"] = int(len(R))
    chk["range_status_values"] = sorted(set(int(s) for s in ch_s))
    chk["range_posoffset_unique"] = np.unique(R[:, 5:8], axis=0).tolist()
    t_end_log = float(frames[-1])
    rt, rd = [], []
    for i in range(len(R)):
        t0 = ch_t[i]; t1 = ch_t[i + 1] if i + 1 < len(R) else t_end_log
        if ch_s[i] != 4 or not (rmin <= ch_d[i] <= rmax):
            continue
        k = np.arange(t0, t1 - 1e-9, T_r)
        rt.append(k); rd.append(np.full(len(k), ch_d[i]))
    rt = np.concatenate(rt) if rt else np.zeros(0); rd = np.concatenate(rd) if rd else np.zeros(0)
    t_rng = rt - a.range_delay_ms * 1e-3
    chk["range_n_emitted"] = int(len(rt))

    # ---------------- arming, init ----------------
    t_arm = next((ta for ta, s in arm if s == 1), None)
    t_imu0 = float(t_imu[0]); t_lvl = t_imu0 + 0.5
    pre = np.where(t_rng <= t_lvl)[0]
    if len(pre):
        init_range, init_src = float(rd[pre[-1]]), "range at levelling end"
    elif t_arm is not None and np.any(t_rng < t_arm):
        init_range, init_src = float(rd[np.where(t_rng < t_arm)[0][0]]), "first Good range before arming"
    else:
        init_range, init_src = float(rrnh["GCl"]), "RRNH.GCl (RNGFND_GNDCLEAR)"

    if a.t_end is not None:
        mI, mF, mR = t_imu <= a.t_end, t_flow <= a.t_end, t_rng <= a.t_end
        t_imu, acc, gyr, imu_dt = t_imu[mI], acc[mI], gyr[mI], imu_dt[mI]
        t_flow, t_arr, fxy, bxy, valid, inlier, qual = t_flow[mF], t_arr[mF], fxy[mF], bxy[mF], valid[mF], inlier[mF], qual[mF]
        t_rng, rd = t_rng[mR], rd[mR]
        if len(sim2):
            sim2 = sim2[sim2[:, 0] <= a.t_end]

    # ---------------- geometry ----------------
    geom = {"flow_pos_frd": [P["FLOW_POS_X"], P["FLOW_POS_Y"], P["FLOW_POS_Z"]],
            "range_pos_frd": [P.get(f"RNGFND{n}_POS_X", 0.0), P.get(f"RNGFND{n}_POS_Y", 0.0), P.get(f"RNGFND{n}_POS_Z", 0.0)],
            "rng_min": rmin, "rng_max": rmax}
    if len(rofh):
        chk["flow_pos_parm_matches_rofh"] = bool(np.allclose(np.unique(rofh[:, 6:9], axis=0), [geom["flow_pos_frd"]], atol=1e-6))
    chk["range_pos_parm_matches_rrni"] = bool(np.allclose(np.unique(R[:, 5:8], axis=0), [geom["range_pos_frd"]], atol=1e-6))
    parm_keys = sorted(k for k in P if k.startswith(("FLOW_", "RNGFND", "EK3_FLOW", "EK3_RNG", "EK3_SRC1", "EK3_IMU_MASK",
                                                      "AHRS_EKF_TYPE", "INS_GYRO_FILTER", "INS_ACCEL_FILTER",
                                                      "SCHED_LOOP_RATE", "LOG_REPLAY", "LOG_DISARMED", "EK3_DRV_OPTIONS")))
    try:
        code = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(__file__)), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        code = None
    meta = {"bin": os.path.abspath(a.bin), "bin_sha256": sha256(a.bin), "code_commit": code,
            "imu_instance": a.imu_instance, "range_instance": rng_inst,
            "delays_ms": {"flow": a.flow_delay_ms, "range": a.range_delay_ms, "imu": a.imu_delay_ms},
            "delay_definition": {"flow": "FC arrival (OF.TimeUS) minus END of the flow integration interval",
                                 "range": "emission (RRNI change frame, held at the measured update period) minus measurement",
                                 "imu": "RFRH frame time minus the end of the RISI delta interval"},
            "flow_validity_rule": "valid := Qual > 0; inlier := Qual/255 (pass-through); FGO gate adds |rate| < 4.2 (EKF3 :203)",
            "derotation": "FGO's own raw-gyro interval average (RISI); OF.bodyX/Y NOT used (AHRS gyro = EKF3-bias-corrected)",
            "geometry": geom, "parm": {k: P[k] for k in parm_keys}, "rrnh": rrnh,
            "t_arm": t_arm, "init_range": init_range, "init_range_source": init_src, "t_end": a.t_end,
            "truth": a.truth, "checks": chk}
    if P.get("LOG_REPLAY", 0) != 1:
        print("[warn] LOG_REPLAY != 1 in PARM")
    if f"EK3_IMU_MASK" in P and not (int(P["EK3_IMU_MASK"]) >> a.imu_instance) & 1:
        print(f"[warn] EK3_IMU_MASK {int(P['EK3_IMU_MASK'])} does not include IMU {a.imu_instance}")
    out = a.out if a.out.endswith(".npz") else a.out + ".npz"
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    np.savez_compressed(out, imu_t=t_imu, imu_acc=acc, imu_gyro=gyr, imu_dt=imu_dt,
                        flow_t=t_flow, flow_t_arrival=t_arr, flow_xy=fxy, flow_body_frd=bxy, flow_valid=valid,
                        flow_inlier=inlier, flow_qual=qual, rng_t=t_rng, rng=rd,
                        truth=(sim2 if len(sim2) else np.zeros((0, 4))))
    json.dump(meta, open(out[:-4] + ".json", "w"), indent=1)
    print(json.dumps({k: meta[k] for k in ("geometry", "delays_ms", "t_arm", "init_range", "init_range_source")}, indent=1))
    print(json.dumps(chk, indent=1)[:4000])
    print(f"[out] {out}  imu {len(t_imu)}  flow {len(t_flow)}  range {len(t_rng)}  truth {len(sim2)}")


if __name__ == "__main__":
    main()
