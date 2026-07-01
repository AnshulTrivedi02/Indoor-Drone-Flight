#!/usr/bin/env bash
# Record a single trial to a ROS2 bag.
#
# Usage: ./record_trial.sh <trial_name>
#
# Assumes the full sim stack is already running (./start_sim.sh) and that
# ground_truth_pub.py is publishing /ground_truth/pose.
# Stop recording with Ctrl+C.
#
# Output: ~/thesis_data/trials/<trial_name>/  (contains metadata.yaml + .db3)

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <trial_name>  (e.g. test_001)" >&2
    exit 1
fi

TRIAL_NAME="$1"
OUTPUT_DIR="$HOME/thesis_data/trials/$TRIAL_NAME"

if [ -d "$OUTPUT_DIR" ]; then
    echo "ERROR: Trial directory already exists: $OUTPUT_DIR" >&2
    echo "Choose a different name, or remove the existing directory first." >&2
    exit 1
fi

source /opt/ros/jazzy/setup.bash

# Discover optical flow topics in case flow_tracker is publishing (future).
FLOW_TOPICS=$(ros2 topic list 2>/dev/null \
    | grep -E "^/(flow|optical_flow)" \
    | tr '\n' ' ' \
    || true)

if [ -n "$FLOW_TOPICS" ]; then
    echo "Found optical flow topics: $FLOW_TOPICS"
else
    echo "No optical flow topics detected — recording core topics only."
fi

# Verify ground truth is live before starting.
if ! ros2 topic hz /ground_truth/pose --window 5 2>/dev/null | grep -q "average rate"; then
    echo "WARNING: /ground_truth/pose may not be publishing yet." \
         "Ensure ground_truth_pub.py is running."
fi

mkdir -p "$OUTPUT_DIR"
echo "Recording trial '$TRIAL_NAME' → $OUTPUT_DIR"
echo "Arm, take off, fly, then press Ctrl+C to stop recording."
echo ""

ros2 bag record \
    --storage sqlite3 \
    --output "$OUTPUT_DIR" \
    /clock \
    /ground_truth/pose \
    /downward_camera/image \
    /downward_camera/camera_info \
    $FLOW_TOPICS
