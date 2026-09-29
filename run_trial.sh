#!/usr/bin/env bash
# Automated, unattended trial harness — one command runs a complete trial:
# launch the full headless stack, arm, climb, cruise, land, record, tear
# down, all with zero manual intervention.
#
# Two hard-won constraints shape every wait in this script (see CLAUDE.md,
# Known Issues — RTF on this machine is low, roughly 0.05-0.17):
#   1. Flight-progress waits (altitude reached, cruise duration) NEVER gate
#      on a fixed wall-clock sleep — they poll measured state instead (see
#      fly_trial.py, which does the actual flight). A wall-clock sleep(N)
#      at RTF~0.1 only buys ~N*RTF seconds of sim time; an earlier attempt
#      at this produced a near-empty 7-12s flight log because of exactly
#      this mistake.
#   2. Process-startup readiness waits (Gazebo up, SITL connectable, topics
#      publishing) are NOT sim-time phenomena — they're real-world process
#      launch latency, unrelated to RTF — so bounding them with a
#      wall-clock cap is correct here, and they still poll the actual
#      condition rather than assuming a fixed duration is enough.
#
# Usage:
#   ./run_trial.sh --world iris_textured --velocity 0.4 --altitude 2.0 \
#       --duration 30 [--trial-name my_trial]
#
# duration is cruise duration in SIM SECONDS (not wall-clock).
# trial_name auto-increments (trial_001, trial_002, ...) if omitted.
#
# Output: ~/thesis_data/trials/<trial_name>/
#   bag/            ROS2 bag (clock, ground_truth, ekf pose, lidar, attitude, flow)
#   metadata.yaml
#   ardupilot.bin
#   run_trial.log   full stdout/stderr of this run

set -euo pipefail

# Fixed OpenCV RANSAC seed for flow_tracker — makes flow processing reproducible
# across re-flights (recorded in metadata.yaml). See METHODOLOGY.md.
RANSAC_SEED=42

# ── Argument parsing ─────────────────────────────────────────────────────
WORLD=""
VELOCITY=""
ALTITUDE=""
DURATION=""
TRIAL_NAME=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --world)      WORLD="$2";      shift 2 ;;
        --velocity)   VELOCITY="$2";   shift 2 ;;
        --altitude)   ALTITUDE="$2";   shift 2 ;;
        --duration)   DURATION="$2";   shift 2 ;;
        --trial-name) TRIAL_NAME="$2"; shift 2 ;;
        *) echo "Unknown flag: $1" >&2; exit 1 ;;
    esac
done

if [ -z "$WORLD" ] || [ -z "$VELOCITY" ] || [ -z "$ALTITUDE" ] || [ -z "$DURATION" ]; then
    echo "Usage: $0 --world NAME --velocity M/S --altitude M --duration SIM_SECONDS [--trial-name NAME]" >&2
    exit 1
fi

if [ -z "$TRIAL_NAME" ]; then
    n=1
    while [ -d "$HOME/thesis_data/trials/trial_$(printf '%03d' "$n")" ]; do
        n=$((n + 1))
    done
    TRIAL_NAME="trial_$(printf '%03d' "$n")"
fi

# Forward-camera worlds (fwd-camera workstream): any world named *_fwd (textured walls)
# or *_fwdplain (plain walls), and their ceiling versions *_fwdc / *_fwdplainc
# (METHODOLOGY "Design — ceiling worlds"; the no-ceiling ones are superseded), carries the
# iris_fwd model's forward camera. Opt-in and name-driven: for every other world
# both arrays stay EMPTY, so the bridge and recorder argument lists are exactly the
# pre-fwd ones (METHODOLOGY, "Forward camera — harness").
declare -a FWD_BRIDGE_ARGS=()
declare -a FWD_RECORD_TOPICS=()
FWD_CAMERA=false
if [[ "$WORLD" == *_fwd || "$WORLD" == *_fwdplain || "$WORLD" == *_fwdc || "$WORLD" == *_fwdplainc ]]; then
    FWD_CAMERA=true
    FWD_BRIDGE_ARGS=(
        /forward_camera/image@sensor_msgs/msg/Image@gz.msgs.Image
        /forward_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo
    )
    FWD_RECORD_TOPICS=(/forward_camera/image /forward_camera/camera_info)
    # DIAGNOSTIC ONLY (Phase 1 RTF diagnosis, METHODOLOGY): FWD_DIAG=no_record keeps
    # the bridge but drops the forward topics from the bag; FWD_DIAG=no_bridge also
    # drops them from the bridge (camera still rendered). Unset = the normal path.
    case "${FWD_DIAG:-}" in
        "") ;;
        no_record) FWD_RECORD_TOPICS=() ;;
        no_bridge) FWD_RECORD_TOPICS=(); FWD_BRIDGE_ARGS=() ;;
        *) echo "ERROR: unknown FWD_DIAG='${FWD_DIAG}'" >&2; exit 1 ;;
    esac
fi

OUTPUT_DIR="$HOME/thesis_data/trials/$TRIAL_NAME"
if [ -d "$OUTPUT_DIR" ]; then
    echo "ERROR: Trial directory already exists: $OUTPUT_DIR" >&2
    exit 1
fi
mkdir -p "$OUTPUT_DIR"

LOG_DIR="$OUTPUT_DIR/logs"
mkdir -p "$LOG_DIR"

# Everything from here on is also captured to run_trial.log.
exec > >(tee "$OUTPUT_DIR/run_trial.log") 2>&1

echo "=== Trial '$TRIAL_NAME' ==="
echo "World: $WORLD  Velocity: $VELOCITY m/s  Altitude: $ALTITUDE m  Duration: $DURATION sim-s"
echo "Output: $OUTPUT_DIR"
echo ""

# ── PID tracking + idempotent cleanup ────────────────────────────────────
declare -a BG_PIDS=()
RECORD_PID=""
CLEANED_UP=0

start_bg() {
    # start_bg <logfile> <command...> — launches detached, tracks the PID.
    local logfile="$1"; shift
    setsid nohup "$@" > "$logfile" 2>&1 < /dev/null &
    disown
    BG_PIDS+=("$!")
}

cleanup() {
    local exit_code=$?
    if [ "$CLEANED_UP" -eq 1 ]; then
        return
    fi
    CLEANED_UP=1
    echo ""
    echo "=== Cleaning up (exit code $exit_code) ==="

    if [ -n "$RECORD_PID" ] && kill -0 "$RECORD_PID" 2>/dev/null; then
        echo "Stopping bag recorder (pid $RECORD_PID)..."
        # SIGTERM, not SIGINT: once detached from a tty (setsid, stdin
        # from /dev/null), ros2 bag record explicitly ignores SIGINT
        # (confirmed via /proc/<pid>/status SigIgn) but still catches
        # SIGTERM for a clean shutdown that flushes the bag and writes
        # metadata.yaml - SIGINT here is a silent no-op, not just slow.
        kill -TERM -- "-$RECORD_PID" 2>/dev/null || true
        for _ in $(seq 1 20); do
            kill -0 "$RECORD_PID" 2>/dev/null || break
            sleep 0.5
        done
        kill -9 -- "-$RECORD_PID" 2>/dev/null || true
    fi

    # Each start_bg launch used setsid, so it's the leader of its own
    # process group - kill the whole group (negative PID), not just the
    # single tracked PID. ros2 run/ros2 bag both launch a wrapper process
    # that then execs or forks the real binary; killing only the wrapper
    # PID orphans the real one (found by testing this exact script).
    for pid in "${BG_PIDS[@]:-}"; do
        [ -n "$pid" ] && kill -9 -- "-$pid" 2>/dev/null || true
    done

    # Belt-and-braces: catch anything the PID list missed (e.g. a process
    # that forked a child we didn't track), scoped to this trial's own
    # world/port selection so we don't touch unrelated work.
    pkill -9 -f "sim/worlds/${WORLD}.sdf" 2>/dev/null || true
    pkill -9 -f "build/sitl/bin/arducopter.*sim-address=127.0.0.1 -I0" 2>/dev/null || true
    pkill -9 -f "mavproxy.py --daemon.*--out 127.0.0.1:14550" 2>/dev/null || true

    echo "Cleanup complete."
    exit "$exit_code"
}
trap cleanup EXIT INT TERM ERR

# ── Readiness polling helper ─────────────────────────────────────────────
# Polls an actual condition, not a fixed sleep. The cap here is a
# wall-clock safety net against real process-launch latency (see header
# comment #2), NOT a substitute for checking the condition.
wait_for() {
    # Each poll attempt is itself bounded (timeout 5) so a single hung
    # attempt (gz's CLI tools have been observed to occasionally hang in
    # this environment) can't block the whole retry loop forever - the
    # outer cap_s is what actually decides when to give up.
    local description="$1" check_cmd="$2" cap_s="$3"
    local t0=$SECONDS
    echo "Waiting for: $description (cap ${cap_s}s)..."
    while (( SECONDS - t0 < cap_s )); do
        if timeout 5 bash -c "$check_cmd" >/dev/null 2>&1; then
            echo "  ready after $((SECONDS - t0))s"
            return 0
        fi
        sleep 1
    done
    echo "ERROR: timed out waiting for: $description" >&2
    return 1
}

# ── Launch: Gazebo (headless) ────────────────────────────────────────────
echo ""
echo "--- Launching Gazebo (headless) ---"
cd ~/ardupilot_gazebo
# Vendored thesis sim assets (sim/models, sim/worlds) take precedence; the iris
# drone (iris_with_ardupilot/iris_with_standoffs + 22 MB meshes) and runway
# resolve from ~/ardupilot_gazebo. See sim/README.md.
export GZ_SIM_RESOURCE_PATH=$HOME/thesis_ws/sim/models:$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds:${GZ_SIM_RESOURCE_PATH:-}
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}
start_bg "$LOG_DIR/gazebo.log" gz sim -v4 -s -r "$HOME/thesis_ws/sim/worlds/${WORLD}.sdf"

wait_for "Gazebo model spawned (/downward_lidar/range on the gz bus)" \
    "gz topic -l 2>/dev/null | grep -q /downward_lidar/range" 60

# ── Launch: ArduPilot SITL ────────────────────────────────────────────────
echo ""
echo "--- Launching ArduPilot SITL ---"
set +u
source ~/venv-ardupilot/bin/activate
set -u
cd ~/ardupilot/ArduCopter
start_bg "$LOG_DIR/arducopter.log" \
    ~/ardupilot/build/sitl/bin/arducopter \
    --model JSON --speedup 1 --slave 0 \
    --defaults ../Tools/autotest/default_params/copter.parm,../Tools/autotest/default_params/gazebo-iris.parm,"$HOME/thesis_ws/lidar_rangefinder.parm","$HOME/thesis_ws/flow_ekf.parm","$HOME/thesis_ws/gnss_denied.parm","$HOME/thesis_ws/gnss_denied_nomag.parm","$HOME/thesis_ws/sim_noise.parm","$HOME/thesis_ws/consolidated_rerun.parm" \
    --serial2=udpclient:127.0.0.1:14556 \
    --sim-address=127.0.0.1 -I0

wait_for "SITL MAVLink port open (tcp 5760)" "ss -tln 2>/dev/null | grep -q ':5760 '" 60

echo ""
echo "--- Launching MAVProxy (relay for the bridge scripts' UDP ports) ---"
start_bg "$LOG_DIR/mavproxy.log" \
    mavproxy.py --daemon --retries 5 \
    --out 127.0.0.1:14550 --master tcp:127.0.0.1:5760 --sitl 127.0.0.1:5501 \
    --out 127.0.0.1:14551 --out 127.0.0.1:14552 --out 127.0.0.1:14553 --out 127.0.0.1:14554

wait_for "MAVProxy relaying (vehicle detected)" \
    "grep -q 'online system' '$LOG_DIR/mavproxy.log'" 240
# Cap is 240s, not the ~60s a normal boot needs: this stage occasionally hits
# a real (if temporary) stall in the Gazebo<->SITL JSON lockstep channel once
# a MAVLink client (MAVProxy) attaches to SERIAL0 - confirmed via `gdb` that
# SITL's main thread blocks in SITL::JSON::recv_fdm() waiting on Gazebo's next
# physics packet, and confirmed via arducopter's own log
# ("No JSON sensor message received, resending servos") that this is a stall
# ArduPilot's SITL backend already has built-in retry logic for - it
# self-heals once Gazebo's ArduPilotPlugin times out and resets
# (connectionTimeoutMaxCount) and restarts the exchange, which was observed
# taking ~90-110s wall-clock. This is NOT caused by world load time (verified:
# every corridor world and iris_textured.sdf alike finish loading in ~5-6s,
# gz sim itself only pegs one core - it produces no further log output during
# the stall, it's not "busy loading") and is NOT specific to corridor
# worlds - it reproduced identically on iris_textured.sdf in direct testing.
# See CLAUDE.md, Known Issues, for the full investigation.

# ── Launch: ROS2 bridges + nodes ─────────────────────────────────────────
echo ""
echo "--- Launching ROS2 bridge + nodes ---"
set +u
source /opt/ros/jazzy/setup.bash
source "$HOME/thesis_ws/install/setup.bash"
set -u

start_bg "$LOG_DIR/ros_gz_bridge.log" \
    ros2 run ros_gz_bridge parameter_bridge \
    /downward_camera/image@sensor_msgs/msg/Image@gz.msgs.Image \
    /downward_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo \
    /downward_lidar/range@sensor_msgs/msg/Range[gz.msgs.LaserScan \
    /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
    "/world/${WORLD}/dynamic_pose/info@geometry_msgs/msg/PoseArray[gz.msgs.Pose_V" \
    "${FWD_BRIDGE_ARGS[@]}"

start_bg "$LOG_DIR/ground_truth_pub.log" \
    python3 "$HOME/thesis_ws/ground_truth_pub.py" "$WORLD"

wait_for "/ground_truth/pose publishing" "ros2 topic list 2>/dev/null | grep -q /ground_truth/pose" 60
wait_for "/downward_lidar/range on ROS2" "ros2 topic list 2>/dev/null | grep -q /downward_lidar/range" 60

start_bg "$LOG_DIR/attitude_bridge.log" \
    python3 "$HOME/thesis_ws/attitude_bridge.py" --ros-args -p use_sim_time:=true
start_bg "$LOG_DIR/lidar_bridge.log" \
    python3 "$HOME/thesis_ws/lidar_bridge.py" --ros-args -p use_sim_time:=true

wait_for "/attitude/angular_rates publishing" "ros2 topic list 2>/dev/null | grep -q /attitude/angular_rates" 60

start_bg "$LOG_DIR/flow_tracker.log" \
    ros2 run optical_flow_node flow_tracker --ros-args -p use_sim_time:=true -p ransac_seed:="$RANSAC_SEED"

wait_for "/optical_flow/measurement publishing" "ros2 topic list 2>/dev/null | grep -q /optical_flow/measurement" 60

start_bg "$LOG_DIR/flow_bridge.log" \
    python3 "$HOME/thesis_ws/flow_bridge.py" --ros-args -p use_sim_time:=true
start_bg "$LOG_DIR/ekf_bridge.log" \
    python3 "$HOME/thesis_ws/ekf_bridge.py" --ros-args -p use_sim_time:=true

wait_for "/ekf/pose publishing" "ros2 topic list 2>/dev/null | grep -q /ekf/pose" 60

start_bg "$LOG_DIR/imu_bridge.log" \
    python3 "$HOME/thesis_ws/imu_bridge.py" --ros-args -p use_sim_time:=true

wait_for "/imu/data_raw publishing" "ros2 topic list 2>/dev/null | grep -q /imu/data_raw" 60

echo ""
echo "--- Full stack up ---"

# ── Recording ─────────────────────────────────────────────────────────────
echo ""
echo "--- Starting bag recording ---"
set +e
setsid ros2 bag record \
    --storage sqlite3 \
    --use-sim-time \
    --output "$OUTPUT_DIR/bag" \
    --topics \
    /clock \
    /ground_truth/pose \
    /ekf/pose \
    /downward_lidar/range \
    /attitude/angular_rates \
    /imu/data_raw \
    /imu/time_ref \
    /optical_flow/measurement \
    "${FWD_RECORD_TOPICS[@]}" \
    > "$LOG_DIR/ros2_bag_record.log" 2>&1 < /dev/null &
RECORD_PID=$!
disown
set -e
sleep 2
if ! kill -0 "$RECORD_PID" 2>/dev/null; then
    echo "ERROR: ros2 bag record exited immediately - see $LOG_DIR/ros2_bag_record.log" >&2
    exit 1
fi
echo "Recording (pid $RECORD_PID) -> $OUTPUT_DIR/bag"

# ── Flight (arm, climb, cruise, land — all state-gated, see fly_trial.py) ─
echo ""
echo "--- Flying trial ---"
set +u
source ~/venv-ardupilot/bin/activate
set -u
set +e
python3 "$HOME/thesis_ws/fly_trial.py" \
    --port 14550 --altitude "$ALTITUDE" --velocity "$VELOCITY" --duration "$DURATION" \
    2>&1 | tee "$LOG_DIR/fly_trial.log"
FLIGHT_STATUS=${PIPESTATUS[0]}
set -e

if [ "$FLIGHT_STATUS" -ne 0 ]; then
    echo "ERROR: fly_trial.py failed (exit $FLIGHT_STATUS) - see $LOG_DIR/fly_trial.log" >&2
    exit "$FLIGHT_STATUS"
fi

# ── Stop recording, copy ArduPilot log, write metadata ───────────────────
echo ""
echo "--- Stopping recording ---"
# SIGTERM, not SIGINT: once detached from a tty, ros2 bag record ignores
# SIGINT outright (verified via /proc/<pid>/status) but shuts down cleanly
# on SIGTERM, flushing the bag and writing metadata.yaml. Using SIGINT
# here previously left the recorder running forever until force-killed,
# which skips metadata.yaml entirely and leaves the bag unreadable.
kill -TERM -- "-$RECORD_PID" 2>/dev/null || true
for _ in $(seq 1 20); do
    kill -0 "$RECORD_PID" 2>/dev/null || break
    sleep 0.5
done
# Fallback only - kill -9 here means metadata.yaml was NOT written and the
# bag is unusable, so this should never fire in a healthy run; it exists
# purely to guarantee no orphaned process, same reasoning as cleanup().
kill -9 -- "-$RECORD_PID" 2>/dev/null || true
RECORD_PID=""

LATEST_BIN=$(find "$HOME/ardupilot/ArduCopter/logs" -maxdepth 1 -name "*.BIN" -type f \
    -printf "%T@ %p\n" 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
if [ -n "$LATEST_BIN" ]; then
    cp "$LATEST_BIN" "$OUTPUT_DIR/ardupilot.bin"
    echo "Copied ArduPilot log: $(basename "$LATEST_BIN") -> ardupilot.bin"
else
    echo "WARNING: No .BIN log found - skipping ArduPilot log copy."
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_HASH=$(git -C "$HOME/thesis_ws" rev-parse HEAD 2>/dev/null || echo "unknown")
# ardupilot_gazebo supplies the iris/runway meshes (not vendored) — record its
# live commit and the upstream base so mesh provenance is explicit (sim/README.md).
AG_COMMIT=$(git -C "$HOME/ardupilot_gazebo" rev-parse --short HEAD 2>/dev/null || echo "unknown")
AG_BASE=$(git -C "$HOME/ardupilot_gazebo" merge-base HEAD origin/main 2>/dev/null | cut -c1-7 || echo "unknown")
HOST=$(hostname)

cat > "$OUTPUT_DIR/metadata.yaml" << EOF
trial_name: $TRIAL_NAME
timestamp_utc: $TIMESTAMP
world: $WORLD
target_velocity_m_s: $VELOCITY
target_altitude_m: $ALTITUDE
target_duration_sim_s: $DURATION
gnss_denied: true
git_commit: $GIT_HASH
hostname: $HOST
harness: run_trial.sh
flow_ransac_seed: $RANSAC_SEED
ardupilot_gazebo_commit: $AG_COMMIT
ardupilot_gazebo_upstream_base: $AG_BASE
EOF
if [ "$FWD_CAMERA" = true ]; then
    echo "forward_camera: true" >> "$OUTPUT_DIR/metadata.yaml"
    if [ -n "${FWD_DIAG:-}" ]; then
        echo "fwd_diag: ${FWD_DIAG}   # DIAGNOSTIC run, not a dataset trial" >> "$OUTPUT_DIR/metadata.yaml"
    fi
fi

# Append the live SITL noise/drift params (authoritative — read from the flight
# .BIN's PARM stream) so the noise realisation is self-documented in metadata.
# Best-effort: on failure the params still live in ardupilot.bin.
if [ -f "$OUTPUT_DIR/ardupilot.bin" ]; then
    "$HOME/venv-ardupilot/bin/python3" - "$OUTPUT_DIR/ardupilot.bin" \
        >> "$OUTPUT_DIR/metadata.yaml" 2>/dev/null \
        <<'PYEOF' || echo "WARNING: SIM_* metadata dump failed (params remain in ardupilot.bin)"
import sys
from pymavlink import mavutil
m = mavutil.mavlink_connection(sys.argv[1])
sim = ["SIM_DRIFT_SPEED","SIM_DRIFT_TIME","SIM_ACC1_RND","SIM_ACC2_RND",
       "SIM_GYR1_RND","SIM_GYR2_RND","SIM_BARO_RND","SIM_SONAR_RND","SIM_FLOW_RND"]
# Yaw-source config — the exact axis on which the nomag (dsn_*) and compass-active
# (ds_*) datasets differ. Recorded so a downstream script can tell them apart from
# metadata alone, not just from the live .BIN PARM stream. EK3_SRC1_YAW=0 +
# COMPASS_USE=0 == no yaw source (nomag); EK3_SRC1_YAW=1 == compass-aided yaw.
yaw = ["EK3_SRC1_YAW","COMPASS_USE"]
want = sim + yaw
got = {}
while True:
    p = m.recv_match(type="PARM")
    if p is None: break
    if p.Name in want: got[p.Name] = p.Value
print("sim_noise:")
for k in sim:
    v = got.get(k)
    print(f"  {k}: {v if v is not None else 'null'}")
print("yaw_source:")
for k in yaw:
    v = got.get(k)
    print(f"  {k}: {v if v is not None else 'null'}")
PYEOF
fi

echo ""
echo "=== Trial '$TRIAL_NAME' complete ==="
echo "Bag:      $OUTPUT_DIR/bag"
echo "ArduPilot log: $OUTPUT_DIR/ardupilot.bin"
echo "Metadata: $OUTPUT_DIR/metadata.yaml"
echo "Per-process logs: $LOG_DIR/"
echo ""
echo "Evaluate with: ./evaluate_trial.sh $TRIAL_NAME"
