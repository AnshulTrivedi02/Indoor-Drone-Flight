#!/usr/bin/env bash
# H far-spawn sequence (pre-registered 2026-10-08/09), one flight per argument, under the flight lock; stops at the first
# breach or failed run_trial. Args: gt_ukf gt_fgo ifa_ekf3 ifa_ukf ifa_fgo s1r1 s1r2 s1r3
set -u; cd "$(dirname "$0")/.."; source tools/flight_lock.sh
B="$PWD/batches/expH"
for t in "$@"; do
  case "$t" in
    gt_ukf) name=H_gt_ukf_far; cmd=(env H=1 UKF=1 HPROFILE="$B/wtest_far_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    gt_fgo) name=H_gt_fgo_far; cmd=(env H=1 FGO=1 FGO_NODE_IMPL=cpp HPROFILE="$B/wtest_far_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    ifa_ekf3) name=H_ifa_ekf3; cmd=(env H=1 HPROFILE="$B/ifanchor_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far_occ);;
    ifa_ukf) name=H_ifa_ukf; cmd=(env H=1 UKF=1 HPROFILE="$B/ifanchor_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far_occ);;
    ifa_fgo) name=H_ifa_fgo; cmd=(env H=1 FGO=1 FGO_NODE_IMPL=cpp HPROFILE="$B/ifanchor_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far_occ);;
    s1r[123]) name="H_s1far_r${t:3}"; cmd=(env H=1 HPROFILE="$B/s1_far_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    s2r[123]) name="H_s2_r${t:3}"; cmd=(env H=1 UKF=1 HPROFILE="$B/s1_far_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    *) echo "bad arg $t"; exit 2;;
  esac
  [ -e "$HOME/thesis_data/trials/$name" ] && { echo "$name exists; stopping"; exit 1; }
  flight_lock_acquire "$name" || { echo "no flight lock; stopping"; exit 1; }
  "${cmd[@]}" "$name"
  flight_lock_release
  r="$HOME/thesis_data/closed_loop/$name"; cat "$r/result.txt"
  [ -f "$r/BREACH.txt" ] && { echo "far: $name BREACHED - stopping"; exit 1; }
  grep -q "run_trial exit 0" "$r/result.txt" || { echo "far: $name run_trial failed - stopping"; exit 1; }
  echo "far: $name flown"
done
