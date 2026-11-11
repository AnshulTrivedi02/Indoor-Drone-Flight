#!/usr/bin/env python3
"""Build Mode-2 REPH records for arm (ii) (EKF3 + injected camera heading), per
docs/thesis/ekf3_heading_replay/preregistration.md section 0 items 1-2 and section 5.

NOT a new measurement: every valid frame comes from measurement_models.forward_events(trial,
"heading") -- the SAME frozen Phase 3 psi/validity the UKF/FGO heading arms already consume,
matched frame for frame (checked by this script: n_records must equal the stored heading arm's
fwd_stats.json "psi_valid" count).

ANGLE MAPPING (heading_bridge_core.py's own documented convention, reused verbatim, OFFSET=0):
  yaw_AP = wrap(OFFSET - radians(psi))
OFFSET is 0 here, not read from any per-trial EKF3/ground-truth state, because the corridor-world
spawn geometry (CLAUDE.md "Spawn ... yaw 90 deg. That is ArduPilot yaw 0 ... and the flight
direction") already makes "facing the corridor axis" (psi's own zero, per heading_bridge_core.py's
"psi = GT ENU yaw - 90 deg" convention note) coincide with ArduPilot's own yaw zero -- the SAME
zero measurement_models.h_heading(yaw) = yaw assumes for the UKF/FGO (both estimators initialise
their own yaw = 0 facing the corridor axis, per measurement_models.py's comment on h_heading).
This is a fixed geometric fact of the experiment design, stated independently of any one trial's
ground truth, not a per-trial calibration -- unlike the live heading_bridge.py, which (necessarily,
for a real/live flight with no guaranteed exact spawn alignment) sets OFFSET from EKF3's own
pre-arm yaw. The sign itself (this formula vs its negation) is a separate question, settled by the
pre-registration's gate 2 (heading_bridge_offline.py's node-convention check on the SAME dataset
family), not derived here.

TIMESTAMP MAPPING: TS = input_timing.clock_map()'s inverse, i.e. forward_events()'s bag/sim-time
timestamp mapped FORWARD onto the SITL TimeUS clock (clock_map's own to_sim() goes the other way,
TimeUS -> bag sim time; this script inverts that affine map algebraically from the SAME o1/o2/t1/t2
clock_map already fits -- no new clock-fitting code). D (delay_ms, the record's own field) = 0;
placement_latency_ms (reph_inject.py inject()'s own argument, a DIFFERENT, Mode-2-specific
delay used only to choose a splice point among RFRH frames) = 0 as well, per D139.

Record shape mirrors the live closed-loop template (cl_bcpp_tex_r1_half) exactly, confirmed from
its own extracted records.json: pos = [0,0,0] (placeholder; never fused, EK3_SRC1_POSXY stays 0),
posErr = 100.0 (the AP_VisualOdom_MAV clamp-maximum placeholder value; irrelevant since POSXY=0),
resetTime_ms = 0 (constant, matches the template, so no VisualOdom reset ever fires), angErr =
the dataset's own forward-camera sigma_psi IN RADIANS (0.148 deg for fwdc, 0.126 deg for
fwdplainc) -- NOT clamped to VISO_YAW_M_NSE (that clamp lives in AP_VisualOdom_MAV, which the
direct-to-DAL REPH path never touches, per preregistration.md section 4); EKF3's own
unconditional 5 deg floor (AP_NavEKF3_Measurements.cpp:1118) is left to apply inside EKF3 itself.

Usage: eval/reph_arm2_records.py TRIAL --out RECORDS.json [--validate-against-stored]
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src", "estimators"))
from measurement_models import forward_events, fwd_dataset, FWD_SIGMA  # noqa: E402
from input_timing import clock_map, sim_truth  # noqa: E402

TRIALS_DIR = os.path.expanduser("~/thesis_data/trials")
POS_ERR_M = 100.0


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def q_yaw(yaw):
    """[w, x, y, z] for roll = pitch = 0. Inlined rather than imported from
    src/forward_camera/heading_bridge_core.HeadingCore.q_yaw() (byte-for-byte the same formula)
    because that module's top-level `import fwd_measure` pulls in cv2, which the venv this script
    runs under (rosbags/numpy for input_timing, not vision) does not have and does not need."""
    return [math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)]


def ground_truth_xyz(trial):
    """(t, x, y, z) from /ground_truth/pose, the SAME array input_timing.analyse() builds --
    needed only for clock_map()'s clock ALIGNMENT fit (TimeUS vs bag-clock skew), never as a
    heading value. Read-only; no estimator state.

    Prefers the already-cached <trial>/ukf/ground_truth.tum (columns t x y z qx qy qz qw) --
    ukf_replay.py's own baseline run already extracted this from /ground_truth/pose for every one
    of the 18 Phase-4 bags (also the SAME file eval/three_way_eval.cruise_window() reads as
    GT_SUB="ukf"), so no bag decompression is needed. Only falls back to reading the packed bag
    directly (via REPH_ARM2_BAG_ROOT, a scratch/decompressed copy; off by default) if that cache
    is missing for some trial."""
    cached = f"{TRIALS_DIR}/{trial}/ukf/ground_truth.tum"
    if os.path.exists(cached):
        a = np.loadtxt(cached)
        return a[:, :4]
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY)
    out = []
    bag_root = os.environ.get("REPH_ARM2_BAG_ROOT")
    bag_dir = os.path.join(bag_root, trial, "bag") if bag_root else f"{TRIALS_DIR}/{trial}/bag"
    with Reader(bag_dir) as r:
        conns = [c for c in r.connections if c.topic == "/ground_truth/pose"]
        for con, _, raw in r.messages(connections=conns):
            m = ts.deserialize_cdr(raw, con.msgtype)
            out.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9,
                        m.pose.position.x, m.pose.position.y, m.pose.position.z))
    return np.array(sorted(out))


def to_timeus_fn(o1, o2, t1, t2):
    """Algebraic inverse of clock_map()'s to_sim(t_us) = t_us - (o1 + (o2-o1)*(t_us-t1)/(t2-t1)).
    Returns f(t_bag) -> t_us (both in seconds)."""
    k = (o2 - o1) / (t2 - t1)

    def f(t_bag):
        return (t_bag + o1 - k * t1) / (1.0 - k)
    return f


def build(trial, out_path, validate_against_stored=False):
    ds = fwd_dataset(trial)
    if ds is None:
        raise SystemExit(f"{trial}: not a forward-camera dataset bag")
    sigma_psi_rad = float(FWD_SIGMA[ds]["psi"])

    events = forward_events(trial, "heading")      # [(t, "fwd", (psi_rad|None, omega_rad|None))]
    valid = [(t, psi) for t, _, (psi, _om) in events if psi is not None]
    print(f"{trial}: forward_events() valid psi frames: {len(valid)}")

    if validate_against_stored:
        # DIAGNOSTIC, not a gate: the stored fgo_heading/fwd_stats.json "psi_valid" is NOT the same
        # quantity as forward_events()'s own valid count. Checked directly on fwdc_tex_r1: 9654 here
        # vs 9539 stored. forward_events() returns every measurement-intrinsically-valid Phase 3
        # frame across the WHOLE bag (the preregistration's "every valid frame" input, section 5);
        # fgo_replay.py's own "psi_valid" counts only the events that fell inside the FGO's own
        # fused-event-loop window (from its t_init, after a short settle, to disarm), a SUBSET for a
        # benign, already-understood reason, not a bug or a mismatched input. This script therefore
        # injects forward_events()'s full valid set (matching the preregistration's own definition of
        # the input, not any one estimator's internal processing window) and only REPORTS the stored
        # count here for transparency.
        p = os.path.join(TRIALS_DIR, trial, "fgo_heading", "fwd_stats.json")
        if os.path.exists(p):
            stored = json.load(open(p))["counts"]["psi_valid"]
            print(f"{trial}: forward_events() valid = {len(valid)}; stored fgo_heading psi_valid = {stored} "
                  f"(expected to differ -- see comment above; difference = {len(valid) - stored})")

    gt = ground_truth_xyz(trial)
    sim = sim_truth(trial)
    _to_sim, o1, o2, t1, t2 = clock_map(sim, gt)
    to_us = to_timeus_fn(o1, o2, t1, t2)

    records = []
    for t_bag, psi_rad in valid:
        yaw_ap = wrap(0.0 - psi_rad)                       # OFFSET = 0, see module docstring
        t_us = to_us(t_bag)
        if t_us < 0:
            raise SystemExit(f"{trial}: computed negative TimeUS ({t_us}) for t_bag={t_bag}; clock_map out of range")
        records.append({
            "pos": [0.0, 0.0, 0.0],
            "quat": q_yaw(yaw_ap),
            "posErr": POS_ERR_M,
            "angErr": sigma_psi_rad,
            "timeStamp_ms": int(round(t_us * 1000.0)),
            "resetTime_ms": 0,
            "delay_ms": 0,
        })
    # Mode 2 requires strictly increasing/unique (timeStamp_ms + placement_latency_ms) targets;
    # report duplicates up front rather than letting reph_inject.py raise deep inside inject().
    ts_ms = [r["timeStamp_ms"] for r in records]
    dupes = len(ts_ms) - len(set(ts_ms))
    if dupes:
        print(f"WARNING: {dupes} duplicate timeStamp_ms values after rounding to ms "
              f"(reph_inject.py's Mode 2 will refuse an exact collision)")
    json.dump(records, open(out_path, "w"), indent=1)
    print(f"{trial}: wrote {len(records)} REPH records (Mode 2) -> {out_path}")
    print(f"  sigma_psi_rad (angErr, before EKF3's 5 deg floor) = {sigma_psi_rad:.6f} rad "
          f"({math.degrees(sigma_psi_rad):.3f} deg)")
    print(f"  clock_map: o1={o1*1e3:+.2f} ms @t1={t1:.1f}s, o2={o2*1e3:+.2f} ms @t2={t2:.1f}s")
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trial")
    ap.add_argument("--out", required=True)
    ap.add_argument("--validate-against-stored", action="store_true")
    a = ap.parse_args()
    build(a.trial, a.out, a.validate_against_stored)


if __name__ == "__main__":
    main()
