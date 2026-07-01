#!/usr/bin/env bash
# Record a single trial to a ROS2 bag.
#
# Usage: ./record_trial.sh <trial_name> [--with-images]
#
# Options:
#   --with-images   Also record /downward_camera/image and
#                   /downward_camera/camera_info (default: off —
#                   raw images are ~0.9 MB/frame)
#
# Assumes the full sim stack is running (./start_sim.sh) and that
# ground_truth_pub.py is publishing /ground_truth/pose.
# Stop recording with Ctrl+C.
#
# Output layout:
#   ~/thesis_data/trials/<trial_name>/        — trial directory
#   ~/thesis_data/trials/<trial_name>/bag/    — ROS2 bag (created by ros2 bag record)

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <trial_name> [--with-images]" >&2
    exit 1
fi

TRIAL_NAME="$1"
shift

WITH_IMAGES=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --with-images) WITH_IMAGES=true; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

OUTPUT_DIR="$HOME/thesis_data/trials/$TRIAL_NAME"

if [ -d "$OUTPUT_DIR" ]; then
    echo "ERROR: Trial directory already exists: $OUTPUT_DIR" >&2
    echo "Choose a different name, or remove the existing directory first." >&2
    exit 1
fi

# ROS setup scripts reference variables that may be unset; temporarily allow them.
set +u
source /opt/ros/jazzy/setup.bash
set -u

# No IMU topics are available on ROS2 — ArduPilot handles IMU internally
# via MAVLink and does not bridge it to ROS2 in this stack.

# Discover optical flow topics (catches /optical_flow/measurement and any
# additional publishers added in future work).
FLOW_TOPICS=$(ros2 topic list 2>/dev/null \
    | grep -E "^/(flow|optical_flow)" \
    | tr '\n' ' ' \
    || true)

if [ -n "$FLOW_TOPICS" ]; then
    echo "Found optical flow topics: $FLOW_TOPICS"
else
    echo "WARNING: No optical flow topics detected —" \
         "/optical_flow/measurement may not be publishing."
fi

# Raw camera images are excluded by default (~0.9 MB/frame makes a 90 s trial
# multi-gigabyte). Pass --with-images for dedicated flow-development runs.
CAMERA_TOPICS=""
if [ "$WITH_IMAGES" = true ]; then
    CAMERA_TOPICS="/downward_camera/image /downward_camera/camera_info"
    echo "Image recording enabled (--with-images) — expect large bag files."
fi

# Non-fatal warning if ground truth is not yet live.
if ! timeout 5 ros2 topic hz /ground_truth/pose --window 5 2>/dev/null \
        | grep -q "average rate"; then
    echo "WARNING: /ground_truth/pose may not be publishing yet." \
         "Ensure ground_truth_pub.py is running."
fi

mkdir -p "$OUTPUT_DIR"
echo "Recording trial '$TRIAL_NAME' → $OUTPUT_DIR"
echo "Arm, take off, fly, then press Ctrl+C to stop recording."
echo ""

ros2 bag record \
    --storage sqlite3 \
    --use-sim-time \
    --output "$OUTPUT_DIR/bag" \
    --topics \
    /clock \
    /ground_truth/pose \
    $FLOW_TOPICS \
    $CAMERA_TOPICS
