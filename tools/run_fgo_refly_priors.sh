#!/usr/bin/env bash
# FGO re-fly with CORRECTED initial priors (yaw sigma 1 deg, roll/pitch sigma 5 deg; the UKF's values).
# Pre-registration docs/thesis/refly_priors/preregistration.md (commit 29f6719, incl. AMENDMENT 1); D127-D130, D138.
# Modelled on tools/run_fgo_refly.sh (corridor cases) and tools/run_h_far.sh (hold case). The EXACT commands are the
# pre-registration's SS2 launch lines -- only the trial name is new (the "_rp" = "re-fly, priors" suffix). The
# existing launchers (run_fgo_refly.sh, run_h_far.sh) are NOT edited.
#
# One case per registered name, one argument per flight:
#   cl_fgo_a_tex_r{1,2,3}_half_rp   corridor_textured_half_fwdc, FGO (Python node), no heading
#   cl_fgo_b_tex_r{1,2,3}_half_rp   corridor_textured_half_fwdc, FGO (Python node) + heading (C++ heading node)
#   H_s3rp_r{1,2,3}                 room_wall_tag_far, FGO (C++ node), far-spawn hold profile
#
# Breach handling (mirrors tools/run_cl_extras.sh's exp_contact=1 pattern, applied only to the no-heading cases):
# the registered criterion for the no-heading corridor cases itself expects a west-wall contact inside a window
# after the cruise, so a BREACH.txt whose FIRST LINE starts "wall contact" is the EXPECTED end for cl_fgo_a_* and
# does NOT stop this launcher. Any other breach (crash, box, dependency-loss) on those cases, and ANY breach at all
# on the with-heading or hold cases, DOES stop the launcher. A missing result.txt or a nonzero watcher exit is
# always a failed run and stops the launcher.
#
# Re-flies (IMU-gap rule "unusable", pre-registration section 1): add a <name>b case here -- committed while
# nothing is running -- before flying it. The superseded directory is kept, not deleted.
set -u; cd "$(dirname "$0")/.."; source tools/flight_lock.sh
for t in "$@"; do
  exp_contact=0
  case "$t" in
    cl_fgo_a_tex_r1_half_rp|cl_fgo_a_tex_r2_half_rp|cl_fgo_a_tex_r3_half_rp)
      name="$t"; exp_contact=1
      cmd=(env FGO=1 sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    cl_fgo_b_tex_r1_half_rp|cl_fgo_b_tex_r2_half_rp|cl_fgo_b_tex_r3_half_rp)
      name="$t"
      cmd=(env FGO=1 HEADING=1 HEADING_PARM="$PWD/closedloop_heading_half.parm" HEADING_SIGMA_DEG=0.148 HEADING_EVERY_N=4 sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    H_s3rp_r1|H_s3rp_r2|H_s3rp_r3)
      name="$t"
      cmd=(env H=1 FGO=1 FGO_NODE_IMPL=cpp HPROFILE="$PWD/batches/expH/s1_far_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;
    *) echo "bad arg $t"; exit 2;;
  esac
  [ -e "$HOME/thesis_data/trials/$name" ] && { echo "$name exists; stopping"; exit 1; }
  flight_lock_acquire "$name" 7200 || { echo "no flight lock; stopping"; exit 1; }
  "${cmd[@]}" "$name"
  flight_lock_release
  r="$HOME/thesis_data/closed_loop/$name"
  if [ ! -f "$r/result.txt" ]; then echo "refly_priors: $name NO result.txt - stopping"; exit 1; fi
  cat "$r/result.txt"
  if [ -f "$r/BREACH.txt" ]; then
    if [ "$exp_contact" = 1 ] && head -1 "$r/BREACH.txt" | grep -q "^wall contact"; then
      echo "refly_priors: $name BREACH (expected wall contact) - continuing"
    else
      echo "refly_priors: $name BREACHED - stopping"; exit 1
    fi
  fi
  if ! grep -q "watcher exit 0" "$r/result.txt"; then
    echo "refly_priors: $name watcher exit nonzero - stopping"; exit 1
  fi
  echo "refly_priors: $name flown"
done
