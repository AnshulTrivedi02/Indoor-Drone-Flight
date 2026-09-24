#!/usr/bin/env bash
# yaw_sweep.sh WORLD OUT_DIR "Y1 Y2 ..." "YAW1 YAW2 ..." [Z]
# Static heading-response check for Phase 3 (METHODOLOGY, pre-registered supplementary
# check): launch WORLD headless once, pause, and for each (y, yaw offset) teleport the
# drone to (0, y, Z) with ENU yaw = 90 deg + offset (i.e. offset from the corridor
# axis; positive = nose left), step, and save one forward frame to
# OUT_DIR/y<Y>_yaw<OFFSET>/forward_camera_image.png. Tears down only what it started.
set -euo pipefail
WORLD="$1"; OUT="$2"; YS="$3"; YAWS="$4"; Z="${5:-2.3}"
mkdir -p "$OUT"
export GZ_SIM_RESOURCE_PATH=$HOME/thesis_ws/sim/models:$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build
set +u; source /opt/ros/jazzy/setup.bash; set -u
PIDS=()
cleanup() { for p in "${PIDS[@]}"; do kill -- -"$p" 2>/dev/null || true; done; }
trap cleanup EXIT
setsid gz sim -v2 -s -r "$HOME/thesis_ws/sim/worlds/${WORLD}.sdf" > "$OUT/gz.log" 2>&1 < /dev/null & PIDS+=("$!")
setsid ros2 run ros_gz_bridge parameter_bridge \
    /forward_camera/image@sensor_msgs/msg/Image@gz.msgs.Image > "$OUT/bridge.log" 2>&1 < /dev/null & PIDS+=("$!")
svc() { gz service -s "/world/${WORLD}/$1" --reqtype "$2" --reptype gz.msgs.Boolean --timeout 5000 --req "$3" > /dev/null; }
for _ in $(seq 60); do svc control gz.msgs.WorldControl 'pause: true' && break; sleep 1; done
for Y in $YS; do for OFF in $YAWS; do
    read -r QZ QW < <(python3 -c "import math; a=math.radians(90+float('$OFF'))/2; print(math.sin(a), math.cos(a))")
    D="$OUT/y${Y}_yaw${OFF}"; mkdir -p "$D"
    svc set_pose gz.msgs.Pose "name: \"iris_with_ardupilot\", position: {x: 0, y: ${Y}, z: ${Z}}, orientation: {x: 0, y: 0, z: ${QZ}, w: ${QW}}"
    timeout 60 python3 "$HOME/thesis_ws/sim/tools/grab_frames.py" "$D" /forward_camera/image & GRAB=$!
    sleep 2
    for _ in $(seq 8); do svc control gz.msgs.WorldControl 'multi_step: 40'; done
    wait "$GRAB" || echo "grab failed: $D"
done; done
