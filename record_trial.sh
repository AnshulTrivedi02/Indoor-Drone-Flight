#!/usr/bin/env bash
# Record a single trial to a ROS2 bag.
#
# Usage: ./record_trial.sh <trial_name> [OPTIONS]
#
# Options:
#   --world NAME      Gazebo world name (default: iris_textured)
#   --velocity M/S    Target forward velocity for the trial
#   --altitude M      Target hover altitude for the trial
#   --notes TEXT      Free-form notes saved to metadata.yaml
#   --ardupilot-log-dir DIR  Directory to search for .BIN dataflash logs
#                            (default: ~/ardupilot/ArduCopter/logs)
#   --with-images            Also record /downward_camera/image and
#                            /downward_camera/camera_info (default: off —
#                            raw images are ~0.9 MB/frame)
#
# Assumes the full sim stack is running (./start_sim.sh) and that
# ground_truth_pub.py is publishing /ground_truth/pose.
# Stop recording with Ctrl+C.
#
# Output layout:
#   ~/thesis_data/trials/<trial_name>/              — trial directory
#   ~/thesis_data/trials/<trial_name>/bag/          — ROS2 bag
#   ~/thesis_data/trials/<trial_name>/metadata.yaml

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <trial_name> [--world NAME] [--velocity M/S]" \
         "[--altitude M] [--notes TEXT] [--with-images]" >&2
    exit 1
fi

TRIAL_NAME=""
WORLD="iris_textured"
VELOCITY=""
ALTITUDE=""
NOTES=""
WITH_IMAGES=false
ARDUPILOT_LOG_DIR="$HOME/ardupilot/ArduCopter/logs"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --world)              WORLD="$2";              shift 2 ;;
        --velocity)           VELOCITY="$2";           shift 2 ;;
        --altitude)           ALTITUDE="$2";           shift 2 ;;
        --notes)              NOTES="$2";              shift 2 ;;
        --ardupilot-log-dir)  ARDUPILOT_LOG_DIR="$2"; shift 2 ;;
        --with-images)        WITH_IMAGES=true;        shift   ;;
        -*)            echo "Unknown flag: $1" >&2; exit 1 ;;
        *)             TRIAL_NAME="$1";  shift   ;;
    esac
done

if [ -z "$TRIAL_NAME" ]; then
    echo "ERROR: trial_name is required." >&2
    exit 1
fi

OUTPUT_DIR="$HOME/thesis_data/trials/$TRIAL_NAME"

if [ -d "$OUTPUT_DIR" ]; then
    echo "ERROR: Trial directory already exists: $OUTPUT_DIR" >&2
    echo "Choose a different name, or remove the existing directory first." >&2
    exit 1
fi

# ROS setup scripts reference variables that may be unset; temporarily allow them.
set +u
source /opt/ros/jazzy/setup.bash
# Workspace overlay - needed so ros2 bag record can resolve the custom
# optical_flow_interfaces package; without it, /optical_flow/measurement is
# silently dropped from the bag (unknown type, not a fatal error).
source "$HOME/thesis_ws/install/setup.bash"
set -u

# Raw IMU is not bridged to ROS2 — ArduPilot handles it internally via
# MAVLink. Gyro rates are available via attitude_bridge.py's republish of
# MAVLink ATTITUDE on /attitude/angular_rates (recorded below), needed
# alongside raw flow so every estimator can derotate internally — see
# CLAUDE.md, Sensor Fusion Architecture.

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

# Write trial metadata before the bag starts so it exists even if recording
# is interrupted early.
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_HASH=$(git -C "$HOME/thesis_ws" rev-parse HEAD 2>/dev/null || echo "unknown")
HOST=$(hostname)

cat > "$OUTPUT_DIR/metadata.yaml" << EOF
trial_name: $TRIAL_NAME
timestamp_utc: $TIMESTAMP
world: $WORLD
target_velocity_m_s: ${VELOCITY:-""}
target_altitude_m: ${ALTITUDE:-""}
with_images: $WITH_IMAGES
git_commit: $GIT_HASH
hostname: $HOST
notes: "${NOTES:-""}"
EOF

echo "Metadata written → $OUTPUT_DIR/metadata.yaml"
echo "Recording trial '$TRIAL_NAME' → $OUTPUT_DIR"
echo "Arm, take off, fly, then press Ctrl+C to stop recording."
echo ""

# Ctrl+C sends SIGINT to the whole foreground process group, which would kill
# this script before the ArduPilot log copy runs.  The trap intercepts SIGINT
# in the shell so only the recorder is terminated; the script continues.
# set +e/set -e is kept as belt-and-braces for any other non-zero exit.
trap 'echo "Interrupt received — stopping recorder..."' INT
set +e
ros2 bag record \
    --storage sqlite3 \
    --use-sim-time \
    --output "$OUTPUT_DIR/bag" \
    --topics \
    /clock \
    /ground_truth/pose \
    /downward_lidar/range \
    /attitude/angular_rates \
    $FLOW_TOPICS \
    $CAMERA_TOPICS
set -e
trap - INT

echo ""
echo "Recording stopped."

# ── ArduPilot dataflash log ───────────────────────────────────────────────────
# Copy the most recent .BIN log alongside the bag for synchronised analysis.
# Non-fatal — the bag is still valid without it.
# Override the directory with --ardupilot-log-dir if SITL is launched elsewhere.
if [ -d "$ARDUPILOT_LOG_DIR" ]; then
    LATEST_BIN=$(find "$ARDUPILOT_LOG_DIR" -maxdepth 1 -name "*.BIN" -type f \
        -printf "%T@ %p\n" 2>/dev/null \
        | sort -n | tail -1 | cut -d' ' -f2-)
    if [ -n "$LATEST_BIN" ]; then
        cp "$LATEST_BIN" "$OUTPUT_DIR/ardupilot.bin"
        echo "Copied ArduPilot log: $(basename "$LATEST_BIN") → ardupilot.bin"
    else
        echo "WARNING: No .BIN log files found in $ARDUPILOT_LOG_DIR" \
             "— skipping ArduPilot log."
    fi
else
    echo "WARNING: ArduPilot log directory not found ($ARDUPILOT_LOG_DIR)" \
         "— skipping ArduPilot log."
fi

echo ""
echo "Trial '$TRIAL_NAME' complete. Output: $OUTPUT_DIR"
