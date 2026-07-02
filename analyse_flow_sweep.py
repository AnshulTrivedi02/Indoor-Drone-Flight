#!/usr/bin/env python3
"""
Optical flow velocity-sweep validation script.

Reads three ROS2 bags from a velocity sweep, compares measured optical flow
against kinematic theory (flow = v/h * f), and produces a validation figure.

Usage:
    source /opt/ros/jazzy/setup.bash
    source ~/thesis_ws/install/setup.bash
    python3 ~/thesis_ws/analyse_flow_sweep.py

Both the ROS2 installation and the workspace must be sourced so that
rclpy and optical_flow_interfaces are importable.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── Configuration ─────────────────────────────────────────────────────────────

# Each entry: (trial_name, commanded_velocity_m_s)
TRIALS = [
    ("sweep_v0p25", 0.25),
    ("sweep_v0p5",  0.50),
    ("sweep_v1p0",  1.00),
]

TRIAL_BASE_DIR  = os.path.expanduser("~/thesis_data/trials")
OUTPUT_FIGURE   = os.path.expanduser("~/thesis_data/flow_validation.png")

ALTITUDE_M      = 2.0    # hover altitude during all sweeps (metres)
FOCAL_LENGTH_PX = 554.0  # camera focal length (pixels); confirmed 640×480, 60° FOV

# Minimum feature count for a frame to be counted as a quality measurement.
MIN_FEATURES = 30

# Minimum RANSAC inlier ratio for a frame to be trusted (rejects noisy flow).
MIN_INLIER_RATIO = 0.5

# Minimum |flow_y| (px/s) for a frame to count as steady translation rather
# than hover — trials contain hovering before and after the forward-flight
# segment, and position-based trimming doesn't reliably remove it.
MIN_FLOW_MAGNITUDE = 50.0

# Below this many surviving frames, the steady-flight result is untrustworthy.
MIN_FRAMES_WARNING = 20

# ── Kinematic prediction ───────────────────────────────────────────────────────

def predicted_flow(velocity_m_s: float) -> float:
    """Return theoretical optical flow in px/s: flow = (v / h) * f."""
    return (velocity_m_s / ALTITUDE_M) * FOCAL_LENGTH_PX


# ── Bag reading ───────────────────────────────────────────────────────────────

def read_flow_bag(bag_dir: str):
    """
    Read all /optical_flow/measurement messages from a ROS2 bag.

    Returns a list of dicts with keys: flow_y, feature_count, inlier_ratio, valid.
    Raises ImportError if rosbag2_py is unavailable.
    """
    try:
        import rosbag2_py
        from rclpy.serialization import deserialize_message
        from optical_flow_interfaces.msg import OpticalFlow
    except ImportError as exc:
        raise ImportError(
            "rosbag2_py or optical_flow_interfaces not found. "
            "Ensure both /opt/ros/jazzy/setup.bash and "
            "~/thesis_ws/install/setup.bash are sourced."
        ) from exc

    storage_options = rosbag2_py.StorageOptions(
        uri=bag_dir,
        storage_id="sqlite3",
    )
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )

    reader = rosbag2_py.SequentialReader()
    reader.open(storage_options, converter_options)

    # Build a map of topic → type so we can filter efficiently.
    topic_types = {
        info.name: info.type
        for info in reader.get_all_topics_and_types()
    }

    if "/optical_flow/measurement" not in topic_types:
        print(f"  WARNING: /optical_flow/measurement not found in {bag_dir}.")
        return []

    filter_ = rosbag2_py.StorageFilter(topics=["/optical_flow/measurement"])
    reader.set_filter(filter_)

    records = []
    while reader.has_next():
        _, data, _ = reader.read_next()
        msg = deserialize_message(data, OpticalFlow)
        records.append({
            "flow_y":        msg.flow_y,
            "feature_count": msg.feature_count,
            "inlier_ratio":  msg.inlier_ratio,
            "valid":         msg.valid,
        })

    return records


# ── Per-trial statistics ───────────────────────────────────────────────────────

def steady_state_flow(records: list) -> tuple:
    """
    Compute steady-state median |flow_y| using content-based frame selection
    instead of position-based trimming, so hovering at the start/end of a
    trial doesn't drag the result toward zero.

    Selection is two-stage:
      1. Keep quality frames: valid=True and inlier_ratio >= MIN_INLIER_RATIO.
      2. Of those, keep moving frames: |flow_y| >= MIN_FLOW_MAGNITUDE
         (excludes hover, which is a quality frame with near-zero flow).

    Returns (median_flow_px_s, n_frames_used, n_frames_total, median_feature_count).
    Returns (None, 0, n_frames_total, 0) if no usable frames remain.
    """
    n = len(records)
    if n == 0:
        return None, 0, 0, 0

    quality = [
        r for r in records
        if r["valid"] and r["feature_count"] >= MIN_FEATURES
        and r["inlier_ratio"] >= MIN_INLIER_RATIO
    ]
    moving = [r for r in quality if abs(r["flow_y"]) >= MIN_FLOW_MAGNITUDE]

    if not moving:
        return None, 0, n, 0

    flow_vals    = np.array([abs(r["flow_y"])   for r in moving])
    feature_vals = np.array([r["feature_count"] for r in moving])

    return float(np.median(flow_vals)), len(moving), n, float(np.median(feature_vals))


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    results = []

    for trial_name, velocity in TRIALS:
        bag_dir = os.path.join(TRIAL_BASE_DIR, trial_name, "bag")

        if not os.path.isdir(bag_dir):
            print(f"SKIP: {trial_name} — bag directory not found ({bag_dir})")
            continue

        print(f"Reading {trial_name} ({velocity} m/s) …")
        try:
            records = read_flow_bag(bag_dir)
        except ImportError as exc:
            print(f"  ERROR: {exc}")
            sys.exit(1)

        if not records:
            print(f"  WARNING: no messages read from {bag_dir}, skipping.")
            continue

        measured, n_frames, n_total, med_features = steady_state_flow(records)
        predicted = predicted_flow(velocity)

        if measured is None:
            print(f"  WARNING: no moving quality frames remain after selection, skipping.")
            continue

        if n_frames < MIN_FRAMES_WARNING:
            print(
                f"  WARNING: only {n_frames} frames survived selection "
                f"(< {MIN_FRAMES_WARNING}) — too little steady flight to trust this result."
            )

        error_pct = (measured - predicted) / predicted * 100.0

        results.append({
            "trial":          trial_name,
            "velocity":       velocity,
            "predicted":      predicted,
            "measured":       measured,
            "error_pct":      error_pct,
            "n_frames":       n_frames,
            "n_total":        n_total,
            "med_features":   med_features,
        })

    if not results:
        print("\nNo valid results — nothing to plot.")
        sys.exit(1)

    # ── Summary table ─────────────────────────────────────────────────────────
    header = (
        f"{'Velocity':>10}  {'Predicted':>12}  {'Measured':>10}  "
        f"{'Error %':>8}  {'Frames (used/total)':>20}  {'Med features':>13}"
    )
    sep = "-" * len(header)
    print()
    print(sep)
    print("Optical flow vs kinematic theory")
    print(f"  Altitude: {ALTITUDE_M} m   Focal length: {FOCAL_LENGTH_PX} px")
    print(
        f"  Quality filter: valid=True, feature_count >= {MIN_FEATURES}, "
        f"inlier_ratio >= {MIN_INLIER_RATIO}"
    )
    print(f"  Motion filter: |flow_y| >= {MIN_FLOW_MAGNITUDE} px/s (excludes hover)")
    print(sep)
    print(header)
    print(sep)
    for r in results:
        frames_str = f"{r['n_frames']:d}/{r['n_total']:d}"
        print(
            f"{r['velocity']:>9.2f}  "
            f"{r['predicted']:>10.1f} px/s  "
            f"{r['measured']:>8.1f} px/s  "
            f"{r['error_pct']:>+7.1f}%  "
            f"{frames_str:>20}  "
            f"{r['med_features']:>13.0f}"
        )
    print(sep)

    # ── Validation figure ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))

    # Theoretical line across the velocity range.
    v_range = np.linspace(0.0, max(r["velocity"] for r in results) * 1.15, 200)
    ax.plot(
        v_range,
        [predicted_flow(v) for v in v_range],
        linestyle="--",
        color="steelblue",
        linewidth=1.8,
        label=f"Theory: flow = (v / {ALTITUDE_M} m) × {FOCAL_LENGTH_PX:.0f} px",
    )

    # Measured points.
    ax.scatter(
        [r["velocity"] for r in results],
        [r["measured"] for r in results],
        color="darkorange",
        s=80,
        zorder=5,
        label="Measured (median |flow_y|, quality frames)",
    )

    # Annotate each point with its error.
    for r in results:
        ax.annotate(
            f"{r['error_pct']:+.1f}%",
            xy=(r["velocity"], r["measured"]),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xlabel("Forward velocity (m/s)")
    ax.set_ylabel("Optical flow (px/s)")
    ax.set_title("Optical flow validation — velocity sweep")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.set_xlim(left=0.0)
    ax.set_ylim(bottom=0.0)

    os.makedirs(os.path.dirname(OUTPUT_FIGURE), exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURE, dpi=150)
    print(f"\nFigure saved → {OUTPUT_FIGURE}")


if __name__ == "__main__":
    main()
