#!/usr/bin/env bash
# render_check.sh WORLD Y OUT_DIR [Z]
# Render check without SITL: launch WORLD headless, pause, teleport the drone to
# (0, Y, Z) facing +Y (the flight heading), step, save one forward and one downward
# frame to OUT_DIR, then tear down only the processes this script started.
set -euo pipefail
WORLD="$1"; Y="$2"; OUT="$3"; Z="${4:-2.3}"
mkdir -p "$OUT"
export GZ_SIM_RESOURCE_PATH=$HOME/thesis_ws/sim/models:$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build
set +u; source /opt/ros/jazzy/setup.bash; set -u
PIDS=()
cleanup() { for p in "${PIDS[@]}"; do kill -- -"$p" 2>/dev/null || true; done; }
trap cleanup EXIT
setsid gz sim -v2 -s -r "$HOME/thesis_ws/sim/worlds/${WORLD}.sdf" > "$OUT/gz.log" 2>&1 < /dev/null & PIDS+=("$!")
setsid ros2 run ros_gz_bridge parameter_bridge \
    /forward_camera/image@sensor_msgs/msg/Image@gz.msgs.Image \
    /downward_camera/image@sensor_msgs/msg/Image@gz.msgs.Image > "$OUT/bridge.log" 2>&1 < /dev/null & PIDS+=("$!")
svc() { gz service -s "/world/${WORLD}/$1" --reqtype "$2" --reptype gz.msgs.Boolean --timeout 5000 --req "$3" > /dev/null; }
for _ in $(seq 60); do svc control gz.msgs.WorldControl 'pause: true' && break; sleep 1; done
svc set_pose gz.msgs.Pose "name: \"iris_with_ardupilot\", position: {x: 0, y: ${Y}, z: ${Z}}, orientation: {x: 0, y: 0, z: 0.7071068, w: 0.7071068}"
timeout 90 python3 "$HOME/thesis_ws/sim/tools/grab_frames.py" "$OUT" /forward_camera/image /downward_camera/image & GRAB=$!
sleep 3
for _ in $(seq 8); do svc control gz.msgs.WorldControl 'multi_step: 40'; done
wait "$GRAB"
