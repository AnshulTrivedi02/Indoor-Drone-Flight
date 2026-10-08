#!/usr/bin/env bash
# FGO C++ stage 5 (docs/handovers/2026-10-08_fgo_cpp_stage5_sitl_flights.md): the three SITL shadow flights, flown on
# simulator truth (recorded deviation), one at a time under the flight lock. Usage: tools/run_fgo_cpp_stage5.sh i [ii iii]
set -u
cd "$(dirname "$0")/.."
source tools/flight_lock.sh
for v in "$@"; do
  case "$v" in i) D=0.20; S=time_ref;; ii) D=0.10; S=time_ref;; iii) D=0.10; S=causal;; *) echo "bad variant $v"; exit 2;; esac
  name="fgo_cpp_shadow_$v"
  [ -e "$HOME/thesis_data/trials/$name" ] && { echo "$name exists; not overwriting - stopping"; exit 1; }
  flight_lock_acquire "$name" || { echo "stage5: cannot take the flight lock; stopping"; exit 1; }
  env FGO_NODE=1 FGO_NODE_IMPL=cpp FGO_CPP_DELAY=$D FGO_CPP_IMU_STAMP=$S FGO_CPP_ARM_SOURCE=heartbeat \
    LOOPBACK_ONLY=1 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ARDUPILOT_TREE=$HOME/ardupilot_ukf \
    EXTRA_PARM_FILES=$HOME/thesis_ws/fgo_shadow.parm EXPECT_OVERRIDE=AHRS_FGO_ENABLE=1,SERIAL3_PROTOCOL=2 \
    ./run_trial.sh --world corridor_textured_half_fwdc --velocity 0.5 --altitude 2.0 --duration 300 --trial-name "$name"
  rc=$?
  flight_lock_release
  echo "stage5: $name run_trial exit $rc"
  [ "$rc" -eq 0 ] || { echo "stage5: $name FAILED - stopping"; exit 1; }
done
echo "stage5: done"
