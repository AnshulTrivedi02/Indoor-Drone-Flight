#!/usr/bin/env bash
# UKF closed-loop RE-FLIGHTS with the jitter-corrected UKF port (ruling 2026-10-09), one per argument, under the flight lock.
# Same settings and criteria as the originals (kept recorded, labelled old model). Stops at an unexpected breach.
#   s2r1..3  H_s2v2_rN            (UKF flying on the wall tag, far spawn, S1 profile)
#   a        cl_ukf_a_tex_half_v2  (no heading; wall contact is the expected end)
#   b1..b3   cl_ukf_b_tex_rN_half_v2 (heading: C++ heading node, sigma 0.148 deg, every_n 4, closedloop_heading_half.parm)
#   sa sb    H_safety_ukf_{a,b}_v2 (2 m-clearance hold W(-2.6,0))
#   sa3 sb3  H_safety_ukf_{a,b}_v3 (2d, 2026-10-11: as sa/sb, same port)
set -u; cd "$(dirname "$0")/.."; source tools/flight_lock.sh
B="$PWD/batches/expH"
for t in "$@"; do
  exp_contact=0
  case "$t" in
    s2r[123]) name="H_s2v2_r${t:3}"; cmd=(env H=1 UKF=1 HPROFILE="$B/s1_far_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    a) name=cl_ukf_a_tex_half_v2; exp_contact=1; cmd=(env UKF=1 sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    b[123]) name="cl_ukf_b_tex_r${t:1}_half_v2"; cmd=(env UKF=1 HEADING=1 HEADING_PARM="$PWD/closedloop_heading_half.parm" HEADING_SIGMA_DEG=0.148 HEADING_EVERY_N=4 sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    sa) name=H_safety_ukf_a_v2; cmd=(env H=1 UKF=1 HPROFILE="$B/safety2_ukf_a_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    sb) name=H_safety_ukf_b_v2; cmd=(env H=1 UKF=1 WATCH_DEP_LOSS=land HPROFILE="$B/safety2_ukf_b_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    # 2d (ruling 2026-10-11): the same safety re-tests again on the installed port (abb0357d), new names; settings as sa/sb
    sa3) name=H_safety_ukf_a_v3; cmd=(env H=1 UKF=1 HPROFILE="$B/safety2_ukf_a_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    sb3) name=H_safety_ukf_b_v3; cmd=(env H=1 UKF=1 WATCH_DEP_LOSS=land HPROFILE="$B/safety2_ukf_b_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    *) echo "bad arg $t"; exit 2;;
  esac
  [ -e "$HOME/thesis_data/trials/$name" ] && { echo "$name exists; stopping"; exit 1; }
  flight_lock_acquire "$name" 7200 || { echo "no flight lock; stopping"; exit 1; }
  "${cmd[@]}" "$name"
  flight_lock_release
  r="$HOME/thesis_data/closed_loop/$name"; cat "$r/result.txt"
  if [ -f "$r/BREACH.txt" ] && [ "$exp_contact" = 0 ]; then echo "ukfrefly: $name BREACHED - stopping"; exit 1; fi
  echo "ukfrefly: $name flown"
done
