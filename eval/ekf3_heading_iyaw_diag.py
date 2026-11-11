#!/usr/bin/env python3
"""DIAGNOSTIC (preregistration section 6 metric 3, "forward-measurement ... NIS of the tested
measurements", EKF3-side acceptance per section 0 item 4).

XKF3 (log_XKF3) is logged at EKF3's own LOGGING cadence (~10 Hz, matching XKF1 -- checked: core
100's XKF3 row count equals its XKF1 row count on every bag below), NOT once per yaw fusion --
arm (ii) injects camera heading at ~30 Hz, so each logged XKF3 row is a SNAPSHOT of whichever
innovation happened to be current at that log tick, not a one-to-one fused-measurement record.
No EKF3-logged field was found that carries a yaw test ratio or an explicit accept/reject flag
for this stage (yawTestRatio itself, AP_NavEKF3_MagFusion.cpp:1108, is not in log_XKF3's field
list; XKF4.FS/SM were not independently checked against getFilterFaults()/getVariances() for a
yaw-gate bit in this stage -- NOT verified, stated as an open item, not assumed negative).

So this script reports what the log DOES support: IYAW (the logged innovation angle) summary
statistics, restricted to rows at or after the FIRST injected record's own timestamp (a simple,
verifiable partition -- not a "yaw aligned" boundary, which this session could not locate as a
timestamped BIN record for the ExternalNav path; it only appears as an un-timestamped Replay
stdout TOGCS: line for OTHER yaw sources in one example log). Fused/rejected counts are NOT
claimed from this.

Usage: eval/ekf3_heading_iyaw_diag.py [--json OUT]
"""
import argparse, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS_ROOT = os.path.expanduser("~/thesis_data/ekf3_heading_replay/arms")
RECORDS_DIR = os.path.expanduser("~/thesis_data/ekf3_heading_replay/arm_ii_records")
BAGS = [f"{p}_{w}_r{r}" for p in ("fwdc", "fwdplainc") for w in ("tex", "trans", "blank") for r in (1, 2, 3)]


def latest_bin(bag):
    logs = sorted(glob.glob(os.path.join(ARMS_ROOT, bag, "heading", "logs", "*.BIN")), key=os.path.getmtime)
    return logs[-1]


def analyse(bag):
    from pymavlink import mavutil
    records = json.load(open(os.path.join(RECORDS_DIR, f"{bag}.json")))
    first_ts_us = min(r["timeStamp_ms"] for r in records) * 1000
    m = mavutil.mavlink_connection(latest_bin(bag))
    xkf1_n, xkf3_rows = 0, []
    while True:
        x = m.recv_match(type=["XKF1", "XKF3"])
        if x is None:
            break
        if int(getattr(x, "C", -1)) != 100:
            continue
        if x.get_type() == "XKF1":
            xkf1_n += 1
        else:
            xkf3_rows.append((x.TimeUS, float(x.IYAW)))
    after = [iy for t, iy in xkf3_rows if t >= first_ts_us]
    import numpy as np
    iy = np.array(after) if after else np.array([0.0])
    return {"n_xkf1_core100": xkf1_n, "n_xkf3_core100": len(xkf3_rows),
            "n_xkf3_at_or_after_first_injection": len(after),
            "iyaw_deg_after_first_injection": {
                "mean": float(iy.mean()), "median": float(np.median(iy)),
                "p95_abs": float(np.percentile(np.abs(iy), 95)), "max_abs": float(np.abs(iy).max())},
            "note": "log-cadence snapshot (matches XKF1's own row count), not per-fusion; "
                    "fused/rejected count not recoverable from this dataflash log (see module docstring)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    out = {}
    for bag in BAGS:
        r = analyse(bag)
        out[bag] = r
        s = r["iyaw_deg_after_first_injection"]
        print(f"{bag:20} n_xkf3={r['n_xkf3_core100']:5d} (==n_xkf1 {r['n_xkf1_core100'] == r['n_xkf3_core100']})  "
              f"IYAW mean={s['mean']:+.4f} median={s['median']:+.4f} p95_abs={s['p95_abs']:.4f} max_abs={s['max_abs']:.4f} deg")
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
        print(f"[out] {a.json}")


if __name__ == "__main__":
    main()
