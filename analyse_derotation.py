#!/usr/bin/env python3
"""
Analyse a pure-rotation validation bag: does derotated flow collapse toward
zero while raw flow does not?

Reads /optical_flow/measurement (raw + derotated flow) and /attitude/angular_rates
(rollspeed/pitchspeed/yawspeed) from a bag, joins each flow sample to the
nearest attitude sample by timestamp, and prints a per-message table plus
summary statistics for the x and y axes separately.

Usage:
    python3 analyse_derotation.py <bag_path> [--csv OUT.csv]
"""

import argparse
import bisect
import csv as csv_module
import statistics
from pathlib import Path

from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from rclpy.serialization import deserialize_message
from optical_flow_interfaces.msg import OpticalFlow
from geometry_msgs.msg import Vector3Stamped


def stamp_to_sec(stamp) -> float:
    return stamp.sec + stamp.nanosec * 1e-9


def read_bag(bag_path: Path):
    reader = SequentialReader()
    reader.open(
        StorageOptions(uri=str(bag_path), storage_id="sqlite3"),
        ConverterOptions(input_serialization_format="cdr", output_serialization_format="cdr"),
    )

    flow_msgs = []
    rate_msgs = []
    while reader.has_next():
        topic, data, _t = reader.read_next()
        if topic == "/optical_flow/measurement":
            msg = deserialize_message(data, OpticalFlow)
            if msg.valid:
                flow_msgs.append((stamp_to_sec(msg.header.stamp), msg))
        elif topic == "/attitude/angular_rates":
            msg = deserialize_message(data, Vector3Stamped)
            rate_msgs.append((stamp_to_sec(msg.header.stamp), msg))

    flow_msgs.sort(key=lambda x: x[0])
    rate_msgs.sort(key=lambda x: x[0])
    return flow_msgs, rate_msgs


def nearest_rate(rate_msgs, rate_times, t):
    if not rate_msgs:
        return None
    i = bisect.bisect_left(rate_times, t)
    candidates = []
    if i < len(rate_msgs):
        candidates.append(rate_msgs[i])
    if i > 0:
        candidates.append(rate_msgs[i - 1])
    best = min(candidates, key=lambda rm: abs(rm[0] - t))
    return best[1]


def summarise(label, raw_vals, derot_vals):
    if not raw_vals:
        print(f"  {label}: no data")
        return
    med_raw = statistics.median(abs(v) for v in raw_vals)
    med_derot = statistics.median(abs(v) for v in derot_vals)
    reduction = (1 - med_derot / med_raw) * 100 if med_raw > 0 else 0.0
    print(
        f"  {label}: median|raw|={med_raw:7.2f} px/s  "
        f"median|derot|={med_derot:7.2f} px/s  "
        f"reduction={reduction:+.0f}%"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bag_path")
    ap.add_argument("--csv", default=None, help="Optional path to dump a joined CSV")
    ap.add_argument(
        "--last-seconds",
        type=float,
        default=None,
        help="Only analyse flow messages from the last N seconds of the bag",
    )
    args = ap.parse_args()

    flow_msgs, rate_msgs = read_bag(Path(args.bag_path))
    rate_times = [t for t, _ in rate_msgs]

    if args.last_seconds is not None and flow_msgs:
        cutoff = flow_msgs[-1][0] - args.last_seconds
        flow_msgs = [(t, f) for t, f in flow_msgs if t >= cutoff]
        print(f"Restricted to last {args.last_seconds:.0f}s of the bag.")

    print(f"Flow messages (valid): {len(flow_msgs)}")
    print(f"Attitude samples:      {len(rate_msgs)}")
    if not flow_msgs:
        print("No valid flow messages found — nothing to analyse.")
        return

    rows = []
    for t, flow in flow_msgs:
        rate = nearest_rate(rate_msgs, rate_times, t)
        rollspeed = rate.vector.x if rate else float("nan")
        pitchspeed = rate.vector.y if rate else float("nan")
        yawspeed = rate.vector.z if rate else float("nan")
        rows.append(
            dict(
                t=t,
                flow_x_raw=flow.flow_x_raw,
                flow_x=flow.flow_x,
                flow_y_raw=flow.flow_y_raw,
                flow_y=flow.flow_y,
                rollspeed=rollspeed,
                pitchspeed=pitchspeed,
                yawspeed=yawspeed,
                feature_count=flow.feature_count,
                inlier_ratio=flow.inlier_ratio,
            )
        )

    t0 = rows[0]["t"]
    for r in rows:
        print(
            f"t={r['t'] - t0:6.2f}s  "
            f"raw=({r['flow_x_raw']:+7.2f},{r['flow_y_raw']:+7.2f})  "
            f"derot=({r['flow_x']:+7.2f},{r['flow_y']:+7.2f})  "
            f"roll={r['rollspeed']:+.3f} pitch={r['pitchspeed']:+.3f} yaw={r['yawspeed']:+.3f} rad/s  "
            f"feat={r['feature_count']:3d} inlier={r['inlier_ratio']:.2f}"
        )

    print("\n── Summary ──")
    summarise("flow_x", [r["flow_x_raw"] for r in rows], [r["flow_x"] for r in rows])
    summarise("flow_y", [r["flow_y_raw"] for r in rows], [r["flow_y"] for r in rows])

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv_module.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nCSV written → {args.csv}")


if __name__ == "__main__":
    main()
