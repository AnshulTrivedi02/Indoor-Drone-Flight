#!/usr/bin/env python3
"""S2 ("the estimator is valid throughout") for the no-heading FGO corridor flights, window arming-to-CONTACT.

Why this script exists: `eval/closed_loop_score.py` never computes S2 for `--set a` (no heading) at all (confirmed
in its source); D140's precedent (`--set b --est <est>`, used for the UKF's no-heading set) computes S2 over
arm-to-disarm-or-last-sample instead, which for a flight that ends in a watcher-triggered wall-contact stop (no
clean disarm) extends past contact into the FGO node's own shutdown tail (see
`eval/results/refly_priors_s2/<trial>_setb_est_fgo.json`, 99.8-99.84%). METHODOLOGY's own entries for this exact
cell (`cl_fgo_a_tex_half_v2`/`_v3`) instead report "XFGO.OV 100% from arming to contact" -- the registered wording
("the estimator is valid throughout") does not specify an endpoint for a flight with no clean disarm, so this is
the window that cell's original PASS used, not the scorer's own code path. Re-derived here, not merely cited
(docs/thesis/tier1/decisions_log.md D142; docs/thesis/tier1/open_questions.md OQ-R5 for the coordinator's ruling
between this window and the scorer's D140-style window).

Also reports the EKF failsafe ("EKF Failsafe: changed to Land Mode") time relative to contact, via
`eval/results/closed_loop_extras_s2/failsafe_check.py`'s dataflash ERR/MSG scan (re-used, not duplicated).

Usage (PYTHONPATH=~/.cache/thesis_pyshim ~/venv-evo/bin/python):
  python3 eval/results/refly_priors_s2/s2_to_contact.py TRIAL [TRIAL...] [--json OUT]
"""
import argparse, json, os, sys
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

TS = get_typestore(Stores.ROS2_JAZZY)


def clock_map(trial):
    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    tref = []
    with Reader(f"{D}/bag") as r:
        cs = [c for c in r.connections if c.topic == "/imu/time_ref"]
        for con, _, raw in r.messages(connections=cs):
            m = TS.deserialize_cdr(raw, con.msgtype)
            t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            tref.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, t))
    tref = np.array(sorted(tref))
    sitl, recv = tref[:, 0], tref[:, 1]
    dd = recv - sitl
    env = []
    for lo in np.arange(sitl.min(), sitl.max(), 5.0):
        q = (sitl >= lo) & (sitl < lo + 5)
        if q.sum() > 50:
            i = np.argmin(dd[q])
            env.append((sitl[q][i], dd[q][i]))
    env = np.array(env)
    kk, cc = np.polyfit(env[:, 0], env[:, 1], 1)
    to_sim = lambda s: s + kk * s + cc
    to_dataflash = lambda bagtime: (bagtime - cc) / (1 + kk)
    return to_sim, to_dataflash


def run(trial):
    scorefile = os.path.expanduser(f"~/thesis_ws/eval/results/closed_loop_{trial}.json")
    j = json.load(open(scorefile))
    c0 = j["cruise_s"][0]
    contact_bagtime = c0 + j["contact"]["t_rel_cruise_s"]
    to_sim, to_dataflash = clock_map(trial)
    contact_dfclock = to_dataflash(contact_bagtime)

    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    mm = mavutil.mavlink_connection(f"{D}/ardupilot.bin")
    fov, arm, failsafe_t = [], [], None
    while True:
        rr = mm.recv_match(type=["XFGO", "ARM", "MSG"])
        if rr is None:
            break
        ty = rr.get_type()
        if ty == "XFGO":
            fov.append((rr.TimeUS / 1e6, int(rr.OV)))
        elif ty == "ARM":
            arm.append((rr.TimeUS / 1e6, rr.ArmState))
        elif ty == "MSG" and "EKF Failsafe" in str(rr.Message):
            failsafe_t = rr.TimeUS / 1e6
    fov = np.array(fov)
    arms = [t for t, s in arm if s == 1]
    t0 = arms[0]
    ws = (fov[:, 0] >= t0) & (fov[:, 0] <= contact_dfclock)
    n = int(ws.sum())
    bad = fov[ws][fov[ws][:, 1] == 0]
    out = {
        "trial": trial,
        "contact_bagtime_s": contact_bagtime,
        "arm_dataflash_s": t0,
        "contact_dataflash_s": contact_dfclock,
        "n_samples_arm_to_contact": n,
        "n_invalid_arm_to_contact": int(len(bad)),
        "ov_pct_arm_to_contact": float(100 * (1 - len(bad) / max(n, 1))),
    }
    if failsafe_t is not None:
        failsafe_bagtime = to_sim(failsafe_t)
        out["failsafe_dataflash_s"] = failsafe_t
        out["failsafe_bagtime_s"] = failsafe_bagtime
        out["failsafe_minus_contact_s"] = failsafe_bagtime - contact_bagtime
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trials", nargs="+")
    ap.add_argument("--json")
    a = ap.parse_args()
    res = [run(t) for t in a.trials]
    for r in res:
        print(json.dumps(r, indent=1))
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
        print(f"wrote {a.json}")


if __name__ == "__main__":
    main()
