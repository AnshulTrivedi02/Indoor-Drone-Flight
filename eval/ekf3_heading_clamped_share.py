#!/usr/bin/env python3
"""DIAGNOSTIC (preregistration section 0 item 1): per-bag share of arm (ii) injected records
whose EKF3-requested fusion time falls behind EKF3's own delayed-fusion horizon and is therefore
clamped UP to it (NavEKF3_core::writeExtNavData(), AP_NavEKF3_Measurements.cpp -- see the
preregistration's section 4 finding on this clamp).

DERIVED, NOT INSTRUMENTED: the pinned Replay binary cannot be modified in this stage to log the
clamp directly, so this computes the two quantities the clamp compares, from the SAME inputs
reph_inject.py's Mode 2 search already uses (the records.json + the injected.bin's own RFRH
stream), plus EKF3's own buffer-sizing formula read from AP_NavEKF3_core.cpp:88 directly:

  imu_buffer_length = (maxTimeDelay_ms / EKF_TARGET_DT_MS) + 1   (integer division, both uint16_t)

maxTimeDelay_ms, in THIS config (no GPS, no airspeed, AP_VisualOdom never enabled under direct
REPH/DAL injection so its delay does not contribute -- preregistration section 4): the MAX of
_hgtDelay_ms, _flowDelay_ms, _rngBcnDelay_ms (contributes regardless of beacon USE, per the
source at AP_NavEKF3_core.cpp:42-45), magDelay_ms and EKF_TARGET_DT_MS itself. Read directly
from this session's own Replay PARM dump (fwdc_tex_r1, arm ii): EK3_HGT_DELAY=60,
EK3_FLOW_DELAY=10, EK3_BCN_DELAY=50 ms (EK3_MAG_DELAY not found in the PARM stream -- magDelay_ms
may be a frontend constant, not a settable param; NOT independently re-derived here, so
maxTimeDelay_ms=60 (the HGT delay) is used as the dominant, directly-measured term, and this is
flagged as a possible UNDER-estimate if magDelay_ms independently exceeds 60 ms).

  imu_buffer_length = 60 // 12 + 1 = 6  (EKF_TARGET_DT_MS = 12, AP_NavEKF3_core.h)
  horizon_lag_ms = (imu_buffer_length - 1) * 12 = 60 ms

The horizon at a record's splice point is approximated as (that record's splice RFRH time_us) -
horizon_lag_ms*1000. The record's own requested fusion time is
(timeStamp_ms*1000 - delay_ms*1000 - localFilterTimeStep_ms/2*1000), with
localFilterTimeStep_ms = 12.5 (EKF_TARGET_DT_MS, the ACTUAL EKF3 prediction period measured
elsewhere in this project -- CLAUDE.md "EKF3 Prediction dt"), delay_ms = D = 0 per D139.

Also reports: records whose timeStamp_ms gap to the PRECEDING record is < extNavIntervalMin_ms
(20 ms, AP_NavEKF3.h:518) -- writeExtNavData() silently drops these (preregistration section 8.4);
expected 0.

Usage: eval/ekf3_heading_clamped_share.py [--json OUT]
"""
import argparse, bisect, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reph_inject as R  # noqa: E402

TRIALS = os.path.expanduser("~/thesis_data/trials")
RECORDS_DIR = os.path.expanduser("~/thesis_data/ekf3_heading_replay/arm_ii_records")
ARMS_ROOT = os.path.expanduser("~/thesis_data/ekf3_heading_replay/arms")
BAGS = [f"{p}_{w}_r{r}" for p in ("fwdc", "fwdplainc") for w in ("tex", "trans", "blank") for r in (1, 2, 3)]

EKF_TARGET_DT_MS = 12          # AP_NavEKF3_core.h EKF_TARGET_DT_MS (integer constant used in the C++ division)
LOCAL_FILTER_TIME_STEP_MS = 12.5  # the measured actual EKF3 predict period (CLAUDE.md "EKF3 Prediction dt")
EXT_NAV_INTERVAL_MIN_MS = 20
MAX_TIME_DELAY_MS = 60          # EK3_HGT_DELAY, the dominant directly-measured term -- see module docstring
IMU_BUFFER_LENGTH = MAX_TIME_DELAY_MS // EKF_TARGET_DT_MS + 1
HORIZON_LAG_MS = (IMU_BUFFER_LENGTH - 1) * EKF_TARGET_DT_MS


def analyse_bag(bag):
    records = json.load(open(os.path.join(RECORDS_DIR, f"{bag}.json")))
    src_bin = os.path.join(TRIALS, bag, "ardupilot.bin")
    data, recs, reph_ty, reph_f, rfrh_f = R.load(src_bin)
    rfrh_entries = R._rfrh_targets(data, recs, rfrh_f)  # [(time_us, offset), ...] ascending
    rfrh_times = [t for t, _ in rfrh_entries]

    n_clamped = 0
    n_short_gap = 0
    prev_ts = None
    for rec in sorted(records, key=lambda r: r["timeStamp_ms"]):
        ts_ms = rec["timeStamp_ms"]
        target_us = ts_ms * 1000  # + placement_latency_ms(=0)*1000
        # same search as reph_inject.inject()'s Mode 2: first RFRH strictly after the target
        idx = bisect.bisect_right(rfrh_times, target_us)
        if idx >= len(rfrh_times):
            continue  # would have appended at EOF -- not the case for any of the 18 bags (checked separately)
        splice_time_us = rfrh_times[idx]
        horizon_us = splice_time_us - HORIZON_LAG_MS * 1000
        requested_us = ts_ms * 1000 - rec["delay_ms"] * 1000 - int(LOCAL_FILTER_TIME_STEP_MS / 2 * 1000)
        if requested_us < horizon_us:
            n_clamped += 1
        if prev_ts is not None and (ts_ms - prev_ts) < EXT_NAV_INTERVAL_MIN_MS:
            n_short_gap += 1
        prev_ts = ts_ms

    n = len(records)
    return {"n_records": n, "n_clamped": n_clamped, "clamped_share": n_clamped / n if n else None,
            "n_short_gap_lt_20ms": n_short_gap}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    out = {"derivation": {"maxTimeDelay_ms_dominant_term": MAX_TIME_DELAY_MS,
                           "imu_buffer_length": IMU_BUFFER_LENGTH, "horizon_lag_ms": HORIZON_LAG_MS,
                           "local_filter_time_step_ms": LOCAL_FILTER_TIME_STEP_MS,
                           "ext_nav_interval_min_ms": EXT_NAV_INTERVAL_MIN_MS},
           "per_bag": {}}
    for bag in BAGS:
        r = analyse_bag(bag)
        out["per_bag"][bag] = r
        print(f"{bag:20} n={r['n_records']:5d}  clamped={r['n_clamped']:4d} ({100*r['clamped_share']:.2f}%)  "
              f"short_gap<20ms={r['n_short_gap_lt_20ms']}")
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
        print(f"[out] {a.json}")


if __name__ == "__main__":
    main()
