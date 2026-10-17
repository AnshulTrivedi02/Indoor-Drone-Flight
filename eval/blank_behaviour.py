#!/usr/bin/env python3
"""Behaviour under total loss of flow aiding (user ruling 2026-09-29, consolidated re-run).

Blank floor, and the blank half of the transition world: after the roll-gain correction no
frame is flow_tracker-valid there, so NO estimator receives flow. Reported as behaviour, not
as an accuracy ranking. Per trial:
  flow loss time t_loss = the last flow_tracker-valid frame inside the pinned cruise window
                          (blank: usually none in cruise -> t_loss = cruise start).
  EKF3  XKF4.SS nav_filter_status bits (AP_Nav_Common.h) over the cruise, split before/after
        t_loss: shares of horiz_vel, horiz_pos_rel, const_pos_mode, pred_horiz_pos_rel,
        dead_reckoning; the times they change after t_loss; EKF3 MSG text (aiding stopped...).
  All   position error (estimate - GT, each in its own frame as three_way_eval uses it; the
        estimate re-referenced to GT at t_loss) at t_loss + 10/30/60/120 s and at cruise end,
        along-track and cross-track, plus the estimated along-track distance travelled after
        t_loss against GT (a displacement ratio after flow loss).
Usage (venv-ardupilot: numpy + pymavlink; bags via rosbags if present):
  python3 eval/blank_behaviour.py [--base DIR] TRIAL [...] [--arms ukf,fgo] [--json OUT]
"""
import argparse, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from cruise_window import cruise_bounds

BITS = {"horiz_vel": 1, "horiz_pos_rel": 3, "horiz_pos_abs": 4, "const_pos_mode": 7, "pred_horiz_pos_rel": 8,
        "dead_reckoning": 18}
ap = argparse.ArgumentParser(); ap.add_argument("trials", nargs="+"); ap.add_argument("--base", default="~/thesis_data/trials")
ap.add_argument("--arms", default="ukf,fgo", help="replay subfolders (TUM) to include, e.g. ukf,fgo or ukf_baseline,fgo_baseline")
ap.add_argument("--json"); a = ap.parse_args()
BASE = os.path.expanduser(a.base)


def tum(p):
    x = np.loadtxt(p); return x[:, 0], x[:, 1], x[:, 2]


def valid_frames(trial):
    """(stamp, valid) of /optical_flow/measurement from the bag (sim clock)."""
    import glob
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore, get_types_from_msg
    ts = get_typestore(Stores.ROS2_JAZZY)
    ts.register(get_types_from_msg(open(glob.glob(os.path.join(os.path.dirname(HERE), "src/**/OpticalFlow.msg"), recursive=True)[0]).read(),
                                   "optical_flow_interfaces/msg/OpticalFlow"))
    out = []
    with Reader(f"{BASE}/{trial}/bag") as r:
        cs = [c for c in r.connections if c.topic == "/optical_flow/measurement"]
        for con, _, raw in r.messages(connections=cs):
            m = ts.deserialize_cdr(raw, con.msgtype)
            out.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, float(m.valid)))
    return np.array(out)


def err_growth(t, x, y, gt_t, gx, gy, t_loss, t_end, along_axis):
    """Estimate re-referenced to GT at t_loss; error at offsets and at the end, along/cross track."""
    i0 = np.argmin(np.abs(t - t_loss)); g0 = (np.interp(t_loss, gt_t, gx), np.interp(t_loss, gt_t, gy))
    ex = x - x[i0] + g0[0]; ey = y - y[i0] + g0[1]
    res = {}
    for dt in (10, 30, 60, 120, None):
        tq = t_end if dt is None else t_loss + dt
        if tq > t_end + 1e-6:
            continue
        j = np.argmin(np.abs(t - tq)); gxq, gyq = np.interp(tq, gt_t, gx), np.interp(tq, gt_t, gy)
        dxe, dye = ex[j] - gxq, ey[j] - gyq
        al, cr = (dxe, dye) if along_axis == 0 else (dye, dxe)
        res["end" if dt is None else f"+{dt}s"] = {"along_m": float(al), "cross_m": float(cr)}
    je = np.argmin(np.abs(t - t_end))
    est_d = (ex[je] - ex[i0]) if along_axis == 0 else (ey[je] - ey[i0])
    gt_d = (np.interp(t_end, gt_t, gx) - g0[0]) if along_axis == 0 else (np.interp(t_end, gt_t, gy) - g0[1])
    res["disp_ratio_after_loss"] = float(est_d / gt_d) if abs(gt_d) > 1 else None
    return res


out = {}
for tr in a.trials:
    d = f"{BASE}/{tr}"; r = {}
    # GT and window (sim clock) from the replay's ground_truth.tum when present, else EKF3's (TimeUS)
    gtp = next((f"{d}/{s}/ground_truth.tum" for s in a.arms.split(",") if os.path.exists(f"{d}/{s}/ground_truth.tum")), None)
    vf = valid_frames(tr)
    if gtp:
        gt_t, gx, gy = tum(gtp); c0, c1 = cruise_bounds(gt_t, gx, gy)
        # flow-loss point (METHODOLOGY "Loss-of-flow analysis - flow-loss point defined"): last valid frame
        # while airborne (GT z > 0.5 m) up to cruise end; if none, take-off; case A/B/C
        gz = np.loadtxt(gtp)[:, 3]
        t_to = float(gt_t[np.argmax(gz > 0.5)])
        z_at = np.interp(vf[:, 0], gt_t, gz)
        air_valid = vf[(vf[:, 1] > 0) & (z_at > 0.5) & (vf[:, 0] <= c1), 0]
        if len(air_valid):
            t_loss = float(air_valid[-1]); case = "A" if t_loss < c0 else "B"
        else:
            t_loss = t_to; case = "C"
        w = (vf[:, 0] >= c0) & (vf[:, 0] <= c1)
        r.update({"window_s": [float(c0), float(c1)], "takeoff_s": t_to, "t_loss_s": t_loss, "case": case,
                  "t_loss_after_cruise_start_s": t_loss - float(c0),
                  "valid_frames_in_cruise": int((w & (vf[:, 1] > 0)).sum()), "valid_frames_airborne": int(len(air_valid))})
        along = 1 if abs(gy[-1] - gy[0]) > abs(gx[-1] - gx[0]) else 0          # ENU: corridor along +Y
        for s in a.arms.split(","):
            p = f"{d}/{s}/{s.split('_')[0]}_traj.tum"
            if os.path.exists(p):
                t, x, y = tum(p)
                # UKF/FGO TUMs are in the take-off-heading frame (x = North, y = West); GT is ENU. Relabel into ENU,
                # (E, N) = (-y, x), as eval/phase5_analysis.py:12-14 (METHODOLOGY "FINDING (2026-10-17): axis mislabel in
                # eval/blank_behaviour.py"; user rulings 2026-10-18, item 7). EKF3 (NED vs NED, below) is unaffected.
                x, y = -y, x
                r[s] = err_growth(t, x, y, gt_t, gx, gy, t_loss, float(c1), along)
    # EKF3: its own clock (TimeUS); map t_loss by the per-trial clock offset (tens of ms; negligible here)
    e = f"{d}/ekf3"
    if os.path.exists(f"{e}/ekf3_traj.tum") and gtp:
        et, ex_, ey_ = tum(f"{e}/ekf3_traj.tum"); gt2_t, g2x, g2y = tum(f"{e}/ground_truth.tum")
        c0e, c1e = cruise_bounds(gt2_t, g2x, g2y); off = c0e - r["window_s"][0]
        tl = t_loss + off
        alonge = 0 if abs(g2x[-1] - g2x[0]) > abs(g2y[-1] - g2y[0]) else 1        # NED: corridor along North (x)
        r["EKF3"] = err_growth(et, ex_, ey_, gt2_t, g2x, g2y, tl, float(c1e), alonge)
        from pymavlink import mavutil
        m = mavutil.mavlink_connection(f"{d}/ardupilot.bin"); ss, msgs, ofr = [], [], []
        while True:
            x = m.recv_match(type=["XKF4", "MSG", "OF"])
            if x is None:
                break
            if x.get_type() == "OF":
                ofr.append(x.TimeUS / 1e6)
            elif x.get_type() == "XKF4" and x.C == 0:
                ss.append((x.TimeUS / 1e6, int(x.SS)))
            elif x.get_type() == "MSG" and "EKF3" in x.Message and c0e - 30 <= x.TimeUS / 1e6 <= c1e + 30:
                msgs.append((round(x.TimeUS / 1e6 - tl, 2), x.Message))
        # airborne by the SAME rule (GT z > 0.5 m), OF TimeUS mapped to the sim clock by the cruise-start offset
        of_air = [t_ for t_ in ofr if np.interp(t_ - off, gt_t, gz) > 0.5] if gtp else []
        r["EKF3_OF_records_airborne"] = len(of_air)
        r["flow_fused_airborne"] = bool(r.get("valid_frames_airborne", 0) > 0 or len(of_air) > 0)
        ss = np.array(ss); ssb = ss[:, 1].astype(np.int64); wc = (ss[:, 0] >= c0e) & (ss[:, 0] <= c1e)
        bef, aft = wc & (ss[:, 0] < tl), wc & (ss[:, 0] >= tl)
        flags = {}
        for k, b in BITS.items():
            bit = (ssb >> b) & 1
            ch = ss[aft & (bit != np.r_[bit[:1], bit[:-1]]), 0]
            flags[k] = {"before_loss_pct": None if not bef.any() else float(100 * bit[bef].mean()),
                        "after_loss_pct": None if not aft.any() else float(100 * bit[aft].mean()),
                        "changes_after_loss_s": [round(float(x - tl), 2) for x in ch[:6]]}
        r["EKF3_flags"] = flags; r["EKF3_messages_rel_loss_s"] = msgs[:12]
        # EVALUATION RULE (METHODOLOGY, ruling 2026-09-29): EKF3 position is INVALID when horiz_pos_rel,
        # pred_horiz_pos_rel and horiz_pos_abs are all 0; such output (the origin) is not scored.
        inval = ((ssb >> 3) & 1) + ((ssb >> 8) & 1) + ((ssb >> 4) & 1) == 0
        after_to = ss[:, 0] >= tl - 5.0
        iv = np.where(inval & after_to & (ss[:, 0] <= c1e))[0]
        if len(iv):
            r["EKF3_invalid_period"] = {"start_rel_loss_s": round(float(ss[iv[0], 0] - tl), 2),
                                        "duration_in_cruise_s": round(float(np.sum(np.diff(ss[:, 0])[iv[iv < len(ss) - 1]])), 1),
                                        "valid_until_cruise_end": False}
            # re-score EKF3 error growth on its VALID period only (up to the invalid start)
            t_inv = float(ss[iv[0], 0])
            if t_inv > tl + 1:
                r["EKF3_valid_period"] = err_growth(et, ex_, ey_, gt2_t, g2x, g2y, tl, t_inv, alonge)
            r.pop("EKF3", None)
        else:
            r["EKF3_invalid_period"] = None
    out[tr] = r
    print(tr, json.dumps({k: v for k, v in r.items() if k in ("case", "t_loss_after_cruise_start_s", "valid_frames_in_cruise",
                                                             "valid_frames_airborne", "EKF3_OF_records_airborne", "flow_fused_airborne")}),
          {k: r[k].get("disp_ratio_after_loss") for k in r if isinstance(r[k], dict) and "disp_ratio_after_loss" in r[k]}, flush=True)
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
