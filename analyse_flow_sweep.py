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
    ("sweep_v1p25",  0.25),
    ("sweep_v1p50",  0.50),
    ("sweep_v1p100", 1.00),
]

TRIAL_BASE_DIR  = os.path.expanduser("~/thesis_data/trials")
OUTPUT_FIGURE   = os.path.expanduser("~/thesis_data/flow_validation.png")

FLOW_TOPIC = "/optical_flow/measurement"
POSE_TOPIC = "/ground_truth/pose"

# Downward camera is mounted 0.25 m below base_link on the Z axis (see
# iris_with_standoffs/model.sdf, sensor "downward_camera": <pose>0 0 -0.25 ...>).
# /ground_truth/pose reports base_link's world-frame z, with the floor plane at
# world z = 0, so the camera's true height above the floor is
# base_link_z - CAMERA_Z_OFFSET, not the commanded/assumed hover altitude.
CAMERA_Z_OFFSET = 0.25   # metres, camera below base_link origin

FOCAL_LENGTH_PX = 554.0  # camera focal length (pixels); confirmed 640×480, 60° FOV

# Minimum feature count for a flow frame to be counted as a quality measurement.
MIN_FEATURES = 30

# Minimum RANSAC inlier ratio for a flow frame to be trusted (rejects noisy flow).
MIN_INLIER_RATIO = 0.5

# Minimum ground-truth horizontal speed (m/s) for the drone to be considered
# genuinely translating. Trials contain hovering before and after the forward-
# flight segment; this defines the "moving window" from ground truth, which is
# independent of the flow measurement itself.
GT_SPEED_THRESHOLD = 0.1

# ── Kinematic prediction ───────────────────────────────────────────────────────

def predicted_flow(velocity_m_s: float, height_m: float) -> float:
    """Return theoretical optical flow in px/s: flow = (v / h) * f."""
    return (velocity_m_s / height_m) * FOCAL_LENGTH_PX


# ── Bag reading ───────────────────────────────────────────────────────────────

def _stamp_to_sec(stamp) -> float:
    """Convert a builtin_interfaces/Time header stamp to seconds (sim time)."""
    return stamp.sec + stamp.nanosec * 1e-9


def read_bag_records(bag_dir: str):
    """
    Read /optical_flow/measurement and /ground_truth/pose messages from a
    single ROS2 bag in one pass.

    Returns (flow_records, pose_records):
      flow_records: list of dicts {t, flow_y, feature_count, inlier_ratio, valid}
      pose_records: list of dicts {t, x, y, z}
    Timestamps (t) are sim-time seconds taken from each message's header stamp,
    not the bag's recording-time index.

    Raises ImportError if rosbag2_py or the message packages are unavailable.
    """
    try:
        import rosbag2_py
        from rclpy.serialization import deserialize_message
        from optical_flow_interfaces.msg import OpticalFlow
        from geometry_msgs.msg import PoseStamped
    except ImportError as exc:
        raise ImportError(
            "rosbag2_py, optical_flow_interfaces or geometry_msgs not found. "
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

    topic_types = {
        info.name: info.type
        for info in reader.get_all_topics_and_types()
    }

    if FLOW_TOPIC not in topic_types:
        print(f"  WARNING: {FLOW_TOPIC} not found in {bag_dir}.")
    if POSE_TOPIC not in topic_types:
        print(f"  WARNING: {POSE_TOPIC} not found in {bag_dir}.")

    wanted_topics = [t for t in (FLOW_TOPIC, POSE_TOPIC) if t in topic_types]
    if not wanted_topics:
        return [], []

    filter_ = rosbag2_py.StorageFilter(topics=wanted_topics)
    reader.set_filter(filter_)

    flow_records = []
    pose_records = []

    while reader.has_next():
        topic, data, _ = reader.read_next()
        if topic == FLOW_TOPIC:
            msg = deserialize_message(data, OpticalFlow)
            flow_records.append({
                "t":             _stamp_to_sec(msg.header.stamp),
                "flow_y":        msg.flow_y,
                "feature_count": msg.feature_count,
                "inlier_ratio":  msg.inlier_ratio,
                "valid":         msg.valid,
            })
        elif topic == POSE_TOPIC:
            msg = deserialize_message(data, PoseStamped)
            pose_records.append({
                "t": _stamp_to_sec(msg.header.stamp),
                "x": msg.pose.position.x,
                "y": msg.pose.position.y,
                "z": msg.pose.position.z,
            })

    flow_records.sort(key=lambda r: r["t"])
    pose_records.sort(key=lambda r: r["t"])

    return flow_records, pose_records


# ── Ground-truth motion window ─────────────────────────────────────────────────

def ground_truth_motion(pose_records: list) -> tuple:
    """
    Differentiate consecutive ground-truth positions with respect to their
    header timestamps to get horizontal speed, and pair each interval with
    its mean base_link world-frame z (the midpoint of the two samples).

    Returns (speed_times, speeds, z_values) as numpy arrays, one entry per
    consecutive pose pair with a positive time delta. Returns three empty
    arrays if fewer than two pose samples are available.
    """
    if len(pose_records) < 2:
        return np.array([]), np.array([]), np.array([])

    t = np.array([r["t"] for r in pose_records])
    x = np.array([r["x"] for r in pose_records])
    y = np.array([r["y"] for r in pose_records])
    z = np.array([r["z"] for r in pose_records])

    dt = np.diff(t)
    dx = np.diff(x)
    dy = np.diff(y)
    z_mid = (z[:-1] + z[1:]) / 2.0

    # Guard against duplicate/out-of-order timestamps producing dt <= 0.
    valid = dt > 0
    speeds = np.sqrt(dx[valid] ** 2 + dy[valid] ** 2) / dt[valid]
    speed_times = t[1:][valid]
    z_values = z_mid[valid]

    return speed_times, speeds, z_values


def nearest_neighbour(query_times: np.ndarray, sample_times: np.ndarray,
                       sample_values: np.ndarray) -> np.ndarray:
    """
    For each query timestamp, return the value from sample_values whose
    sample_times entry is closest. sample_times must be sorted ascending.
    Used to time-align flow frames (fast) to ground-truth speed samples (slow).
    """
    idx = np.searchsorted(sample_times, query_times)
    idx = np.clip(idx, 1, len(sample_times) - 1)
    left_t  = sample_times[idx - 1]
    right_t = sample_times[idx]
    choose_right = (query_times - left_t) > (right_t - query_times)
    final_idx = np.where(choose_right, idx, idx - 1)
    return sample_values[final_idx]


# ── Per-trial statistics ───────────────────────────────────────────────────────

def steady_state_flow(flow_records: list, pose_records: list) -> dict:
    """
    Compute steady-state median |flow_y| over the ground-truth motion window,
    along with the mean base_link height (world-frame z) over that same
    window, used to derive the camera's true height above the floor.

    A flow frame is kept if:
      1. Its nearest-in-time ground-truth speed sample exceeds
         GT_SPEED_THRESHOLD (the drone is genuinely translating), and
      2. valid=True, feature_count >= MIN_FEATURES and
         inlier_ratio >= MIN_INLIER_RATIO (the measurement itself is trusted).

    Returns a dict with keys: measured, mean_gt_speed, mean_base_link_z,
    camera_height, n_frames. Values are None (measured/mean_gt_speed/
    mean_base_link_z/camera_height) or 0 (n_frames) if no usable frames
    remain.
    """
    empty = {
        "measured": None, "mean_gt_speed": None,
        "mean_base_link_z": None, "camera_height": None, "n_frames": 0,
    }

    speed_times, speeds, z_values = ground_truth_motion(pose_records)
    if len(speed_times) == 0 or not flow_records:
        return empty

    moving_mask = speeds > GT_SPEED_THRESHOLD
    if not moving_mask.any():
        return empty
    mean_gt_speed = float(np.mean(speeds[moving_mask]))
    mean_base_link_z = float(np.mean(z_values[moving_mask]))
    camera_height = mean_base_link_z - CAMERA_Z_OFFSET

    t_flow = np.array([r["t"] for r in flow_records])
    nearest_speed = nearest_neighbour(t_flow, speed_times, speeds)

    quality_mask = np.array([
        r["valid"] and r["feature_count"] >= MIN_FEATURES
        and r["inlier_ratio"] >= MIN_INLIER_RATIO
        for r in flow_records
    ])
    moving_flow_mask = (nearest_speed > GT_SPEED_THRESHOLD) & quality_mask

    if not moving_flow_mask.any():
        return {
            "measured": None, "mean_gt_speed": mean_gt_speed,
            "mean_base_link_z": mean_base_link_z, "camera_height": camera_height,
            "n_frames": 0,
        }

    flow_y = np.array([r["flow_y"] for r in flow_records])
    measured = float(np.median(np.abs(flow_y[moving_flow_mask])))

    return {
        "measured":         measured,
        "mean_gt_speed":    mean_gt_speed,
        "mean_base_link_z": mean_base_link_z,
        "camera_height":    camera_height,
        "n_frames":         int(moving_flow_mask.sum()),
    }


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
            flow_records, pose_records = read_bag_records(bag_dir)
        except ImportError as exc:
            print(f"  ERROR: {exc}")
            sys.exit(1)

        if not flow_records or not pose_records:
            print(f"  WARNING: missing flow or ground-truth pose data in {bag_dir}, skipping.")
            continue

        stats = steady_state_flow(flow_records, pose_records)

        if stats["mean_gt_speed"] is None:
            print(f"  WARNING: no ground-truth motion window found (speed never exceeded "
                  f"{GT_SPEED_THRESHOLD} m/s), skipping.")
            continue

        if stats["measured"] is None:
            print(f"  WARNING: no quality flow frames found within the motion window, skipping.")
            continue

        predicted = predicted_flow(stats["mean_gt_speed"], stats["camera_height"])
        error_pct = (stats["measured"] - predicted) / predicted * 100.0

        results.append({
            "trial":            trial_name,
            "velocity":         velocity,
            "mean_gt_speed":    stats["mean_gt_speed"],
            "mean_base_link_z": stats["mean_base_link_z"],
            "camera_height":    stats["camera_height"],
            "predicted":        predicted,
            "measured":         stats["measured"],
            "error_pct":        error_pct,
            "n_frames":         stats["n_frames"],
        })

    if not results:
        print("\nNo valid results — nothing to plot.")
        sys.exit(1)

    # Diagnostic: raw mean ground-truth base_link z for one trial, to settle
    # whether the drone actually hovers at world z ≈ 2.0 m or ≈ 2.195 m
    # (spawn standoff height 0.195 m + a 2 m AGL climb) during the motion
    # window. This is the number that determines which altitude
    # interpretation was producing the flow bias.
    diag = results[0]
    print(
        f"\n[diagnostic] {diag['trial']}: raw mean GT base_link z over the "
        f"motion window = {diag['mean_base_link_z']:.3f} m "
        f"(world z=2.0 m ⇒ ~2.000 m; spawn 0.195 m + 2 m climb ⇒ ~2.195 m)"
    )

    # ── Summary table ─────────────────────────────────────────────────────────
    header = (
        f"{'Commanded':>10}  {'GT speed':>9}  {'GT z':>7}  {'Cam h':>7}  "
        f"{'Predicted':>12}  {'Measured':>10}  {'Error %':>8}  {'Frames':>7}"
    )
    sep = "-" * len(header)
    print()
    print(sep)
    print("Optical flow vs kinematic theory (ground-truth motion window)")
    print(
        f"  Camera height derived per trial as mean GT base_link z minus "
        f"CAMERA_Z_OFFSET ({CAMERA_Z_OFFSET} m)   Focal length: {FOCAL_LENGTH_PX} px"
    )
    print(f"  Motion window: ground-truth horizontal speed > {GT_SPEED_THRESHOLD} m/s")
    print(
        f"  Quality filter: valid=True, feature_count >= {MIN_FEATURES}, "
        f"inlier_ratio >= {MIN_INLIER_RATIO}"
    )
    print(f"  Predicted flow uses mean ground-truth speed and mean GT-derived camera height")
    print(sep)
    print(header)
    print(sep)
    for r in results:
        print(
            f"{r['velocity']:>9.2f}  "
            f"{r['mean_gt_speed']:>7.2f}  "
            f"{r['mean_base_link_z']:>5.3f}  "
            f"{r['camera_height']:>5.3f}  "
            f"{r['predicted']:>10.1f} px/s  "
            f"{r['measured']:>8.1f} px/s  "
            f"{r['error_pct']:>+7.1f}%  "
            f"{r['n_frames']:>7d}"
        )
    print(sep)

    # ── Validation figure ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))

    # Theoretical line across the velocity range, using the mean GT-derived
    # camera height across all sweep trials (they share one hover altitude).
    mean_camera_height = float(np.mean([r["camera_height"] for r in results]))
    v_range = np.linspace(0.0, max(r["velocity"] for r in results) * 1.15, 200)
    ax.plot(
        v_range,
        [predicted_flow(v, mean_camera_height) for v in v_range],
        linestyle="--",
        color="steelblue",
        linewidth=1.8,
        label=f"Theory: flow = (v / {mean_camera_height:.3f} m) × {FOCAL_LENGTH_PX:.0f} px",
    )

    # Measured points, plotted against actual ground-truth speed reached.
    ax.scatter(
        [r["mean_gt_speed"] for r in results],
        [r["measured"] for r in results],
        color="darkorange",
        s=80,
        zorder=5,
        label="Measured (median |flow_y|, GT motion window)",
    )

    # Annotate each point with its error.
    for r in results:
        ax.annotate(
            f"{r['error_pct']:+.1f}%",
            xy=(r["mean_gt_speed"], r["measured"]),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xlabel("Ground-truth horizontal speed (m/s)")
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
