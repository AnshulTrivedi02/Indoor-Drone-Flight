#!/usr/bin/env python3
"""R3 (rung 1): convert the UKF port's Replay output (`ukf_shadow.csv`, written by AP_NavUKF::log_state in
~/ardupilot_ukf Tools/Replay) to a TUM trajectory on the flight controller's clock, for scoring against mocap.

Input columns (AP_NavUKF.cpp set_csv/log_state):
  TimeUS,PN,PE,PD,VN,VE,VD,Roll,Pitch,Yaw,SVN,SVE,SS,Healthy,FlowAgeMs,FXa,FYa,Ra
  - TimeUS: microseconds on the FC clock (DAL time = the log's TimeUS), stamped at the UKF's FUSION HORIZON, which is the
    time the logged state refers to (the port logs the horizon state every 40 ms; resolution 1 ms).
  - PN/PE/PD: metres, NED, the UKF's own navigation frame (origin = where it initialised; yaw arbitrary, no compass).
  - Roll/Pitch/Yaw: degrees, 321 Euler, NED <- FRD (Yaw wrapped to [0, 360)).

Output: TUM `t x y z qx qy qz qw`, t in seconds on the FC clock.
  --frame enu (default): x = E, y = N, z = U, and the body FLU orientation in ENU, i.e.
    q_enu_flu = q_ned2enu * q_ned_frd * q_frd2flu (CLAUDE.md "EKF State Estimate - Stage B"). This is the frame
    eval/mocap_align.py writes the mocap truth in (it maps the FC estimator's NED with ned_to_enu).
  --frame ned: x = N, y = E, z = D and q_ned_frd: the frame eval/three_way_eval.py uses for EKF3 (XKF1).
  --identity-quat: write identity quaternions (as three_way_eval does for its reference/EKF3 TUMs), so evo's APE is the
    translation part only.
  --healthy-only: drop rows with Healthy = 0 (default: keep every row; the scorer decides).
  --t0-us / --t1-us: keep only rows inside [t0, t1] (FC clock, us).

Usage: python3 eval/ukf_csv_to_tum.py ukf_shadow.csv out.tum [--frame enu|ned] [--identity-quat] [--healthy-only]
       python3 eval/ukf_csv_to_tum.py --selftest
"""
import argparse, sys
import numpy as np
from scipy.spatial.transform import Rotation as Rot

# Fixed frame quaternions (scalar-last for scipy): 180 deg about (1,1,0)/sqrt2 maps NED <-> ENU; 180 deg about body x
# maps FRD <-> FLU. Both are self-inverse.
Q_NED2ENU = Rot.from_quat([np.sqrt(0.5), np.sqrt(0.5), 0.0, 0.0])
Q_FRD2FLU = Rot.from_quat([1.0, 0.0, 0.0, 0.0])
COLS = ("TimeUS", "PN", "PE", "PD", "Roll", "Pitch", "Yaw", "Healthy")


def load_csv(path):
    c = np.genfromtxt(path, delimiter=",", names=True)
    missing = [k for k in COLS if k not in c.dtype.names]
    if missing:
        sys.exit(f"{path}: not a ukf_shadow.csv (missing columns {missing})")
    return np.atleast_1d(c)


def convert(c, frame="enu", identity_quat=False, healthy_only=False, t0_us=None, t1_us=None):
    keep = np.ones(len(c), bool)
    if healthy_only:
        keep &= c["Healthy"] > 0.5
    if t0_us is not None:
        keep &= c["TimeUS"] >= t0_us
    if t1_us is not None:
        keep &= c["TimeUS"] <= t1_us
    c = c[keep]
    t = c["TimeUS"] / 1e6
    q_ned_frd = Rot.from_euler("ZYX", np.c_[c["Yaw"], c["Pitch"], c["Roll"]], degrees=True)   # 321: R = Rz Ry Rx
    if frame == "enu":
        p = np.c_[c["PE"], c["PN"], -c["PD"]]
        q = (Q_NED2ENU * q_ned_frd * Q_FRD2FLU).as_quat()
    elif frame == "ned":
        p = np.c_[c["PN"], c["PE"], c["PD"]]
        q = q_ned_frd.as_quat()
    else:
        raise ValueError(frame)
    if identity_quat:
        q = np.tile([0.0, 0.0, 0.0, 1.0], (len(t), 1))
    if len(t) > 1 and np.any(np.diff(t) <= 0):
        sys.exit("TimeUS is not strictly increasing: refusing to write an ambiguous TUM")
    return np.c_[t, p, q]


def selftest():
    """Synthetic rows with known answers (no log needed)."""
    names = "TimeUS,PN,PE,PD,VN,VE,VD,Roll,Pitch,Yaw,SVN,SVE,SS,Healthy,FlowAgeMs,FXa,FYa,Ra"
    rows = [
        (1_000_000, 1.0, 2.0, -3.0, 0, 0, 0, 0.0, 0.0, 0.0, 0, 0, 0, 1, 0, 0, 0, 0),    # level, facing North
        (1_040_000, 1.0, 2.0, -3.0, 0, 0, 0, 0.0, 0.0, 90.0, 0, 0, 0, 0, 0, 0, 0, 0),   # level, facing East, unhealthy
        (1_080_000, 0.0, 0.0, -1.0, 0, 0, 0, 10.0, 0.0, 0.0, 0, 0, 0, 1, 0, 0, 0, 0),   # 10 deg right roll
    ]
    dt = [(n, float) for n in names.split(",")]
    c = np.array(rows, dtype=dt)
    e = convert(c, "enu")
    ok = True

    def chk(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name)
        ok &= bool(cond)

    chk("t in seconds", np.allclose(e[:, 0], [1.0, 1.04, 1.08]))
    chk("ENU position = (E, N, -D)", np.allclose(e[0, 1:4], [2.0, 1.0, 3.0]))
    # ENU yaw from East, counter-clockwise: facing North = +90 deg, facing East = 0 deg (CLAUDE.md Stage B: yaw ~90 at rest)
    yaw_enu = Rot.from_quat(e[:, 4:8]).as_euler("ZYX", degrees=True)[:, 0]
    chk("facing North -> ENU yaw +90", abs(yaw_enu[0] - 90.0) < 1e-9)
    chk("facing East -> ENU yaw 0", abs(yaw_enu[1]) < 1e-9)
    # right roll (FRD, +10 deg) is a rotation about forward (ENU +y when facing North) that lowers the right side (ENU +x):
    # body FLU y-axis (left) then points up-left: its z component is +sin(10 deg)
    left = Rot.from_quat(e[2, 4:8]).apply([0.0, 1.0, 0.0])
    chk("right roll raises the FLU left axis", abs(left[2] - np.sin(np.radians(10.0))) < 1e-9 and left[0] < 0)
    n = convert(c, "ned")
    chk("NED position unchanged", np.allclose(n[0, 1:4], [1.0, 2.0, -3.0]))
    chk("healthy-only drops row 2", len(convert(c, healthy_only=True)) == 2)
    chk("window", len(convert(c, t0_us=1_030_000, t1_us=1_050_000)) == 1)
    chk("identity quaternions", np.allclose(convert(c, identity_quat=True)[:, 4:8], [0, 0, 0, 1]))
    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--frame", choices=("enu", "ned"), default="enu")
    ap.add_argument("--identity-quat", action="store_true")
    ap.add_argument("--healthy-only", action="store_true")
    ap.add_argument("--t0-us", type=float)
    ap.add_argument("--t1-us", type=float)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.csv or not a.out:
        ap.error("csv and out are required (or --selftest)")
    tum = convert(load_csv(a.csv), a.frame, a.identity_quat, a.healthy_only, a.t0_us, a.t1_us)
    np.savetxt(a.out, tum, fmt="%.6f")
    print(f"{a.out}: {len(tum)} poses, t {tum[0, 0]:.3f}..{tum[-1, 0]:.3f} s (FC clock), frame {a.frame}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
