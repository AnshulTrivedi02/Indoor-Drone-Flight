#!/usr/bin/env bash
# FGO closed-loop RE-FLIGHTS with the corrected FGO (ruling 2026-10-09). v3 = noise fix + gated yaw cap (node f642cd37); v2 = noise fix only (kept, ablation), one per argument, under the flight lock; stop at the
# first breach or failed run. Same settings and criteria as the originals (kept recorded against the old FGO).
#   a      cl_fgo_a_tex_half_v2   (no heading; Python node, as the original)
#   b1..b3 cl_fgo_b_tex_rN_half_v2 (heading: C++ heading node, sigma 0.148 deg, every_n 4, closedloop_heading_half.parm)
#   sa sb  H_safety_fgo_{a,b}_v2  (2 m-clearance hold W(-2.6,0); C++ FGO node 0.10 s time_ref)
#   sa4 sb4 H_safety_fgo_{a,b}_v4 (2d, 2026-10-11: as sa/sb, D18-corrected node)
set -u; cd "$(dirname "$0")/.."; source tools/flight_lock.sh
B="$PWD/batches/expH"
for t in "$@"; do
  case "$t" in
    a) name=cl_fgo_a_tex_half_v3; cmd=(env FGO=1 sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    b[123]) name="cl_fgo_b_tex_r${t:1}_half_v3"; cmd=(env FGO=1 HEADING=1 HEADING_PARM="$PWD/closedloop_heading_half.parm" HEADING_SIGMA_DEG=0.148 HEADING_EVERY_N=4 sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    sa) name=H_safety_fgo_a_v3; cmd=(env H=1 FGO=1 FGO_NODE_IMPL=cpp HPROFILE="$B/safety2_fgo_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    sb) name=H_safety_fgo_b_v3; cmd=(env H=1 FGO=1 FGO_NODE_IMPL=cpp WATCH_EXTRA="fgo_cpp_node.--ros-args" WATCH_DEP_LOSS=land HPROFILE="$B/safety2_fgo_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    # 2d (ruling 2026-10-11): the same safety re-tests on the D18-corrected node (initial yaw 1 deg, roll/pitch 5 deg); settings as sa/sb
    sa4) name=H_safety_fgo_a_v4; cmd=(env H=1 FGO=1 FGO_NODE_IMPL=cpp HPROFILE="$B/safety2_fgo_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    sb4) name=H_safety_fgo_b_v4; cmd=(env H=1 FGO=1 FGO_NODE_IMPL=cpp WATCH_EXTRA="fgo_cpp_node.--ros-args" WATCH_DEP_LOSS=land HPROFILE="$B/safety2_fgo_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    *) echo "bad arg $t"; exit 2;;
  esac
  [ -e "$HOME/thesis_data/trials/$name" ] && { echo "$name exists; stopping"; exit 1; }
  flight_lock_acquire "$name" 7200 || { echo "no flight lock; stopping"; exit 1; }
  "${cmd[@]}" "$name"
  flight_lock_release
  r="$HOME/thesis_data/closed_loop/$name"; cat "$r/result.txt"
  [ -f "$r/BREACH.txt" ] && { echo "refly: $name BREACHED - stopping"; exit 1; }
  echo "refly: $name flown"
done
