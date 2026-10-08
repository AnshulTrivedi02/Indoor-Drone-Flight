#!/usr/bin/env bash
# H option (i) safety tests (pre-registered 2026-10-08), one flight per argument, under the flight lock; stops at the
# first failed run. Args: ukf_a ukf_b fgo_a fgo_b. FGO runs need FGO_CPP_DELAY / FGO_CPP_IMU_STAMP set by the caller.
set -u
cd "$(dirname "$0")/.."
source tools/flight_lock.sh
B="$PWD/batches/expH"
for t in "$@"; do
  name="H_safety_$t"
  [ -e "$HOME/thesis_data/trials/$name" ] && { echo "$name exists; stopping"; exit 1; }
  flight_lock_acquire "$name" || { echo "safety: cannot take the flight lock; stopping"; exit 1; }
  case "$t" in
    ukf_a) H=1 UKF=1 HPROFILE="$B/safety_ukf_a_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far "$name";;
    ukf_b) H=1 UKF=1 WATCH_DEP_LOSS=land HPROFILE="$B/safety_ukf_b_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far "$name";;
    fgo_a) H=1 FGO=1 FGO_NODE_IMPL=cpp HPROFILE="$B/safety_fgo_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far "$name";;
    fgo_b) H=1 FGO=1 FGO_NODE_IMPL=cpp WATCH_EXTRA="fgo_cpp_node.--ros-args" WATCH_DEP_LOSS=land \
             HPROFILE="$B/safety_fgo_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far "$name";;
    # 2 m-clearance hold W(-2.6, 0) (ruling 2026-10-09 item 3)
    ekf3_ref) H=1 WATCH_DEP_LOSS=land HPROFILE="$B/safety2_ekf3_ref_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far "$name";;
    fgo_b2) H=1 FGO=1 FGO_NODE_IMPL=cpp WATCH_EXTRA="fgo_cpp_node.--ros-args" WATCH_DEP_LOSS=land \
             HPROFILE="$B/safety2_fgo_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far "$name";;
    *) echo "bad test $t"; flight_lock_release; exit 2;;
  esac
  flight_lock_release
  r="$HOME/thesis_data/closed_loop/$name"
  cat "$r/result.txt"
  if [ -f "$r/BREACH.txt" ]; then echo "safety: $name BREACHED - stopping"; exit 1; fi
  echo "safety: $name flown (scored separately)"
done
