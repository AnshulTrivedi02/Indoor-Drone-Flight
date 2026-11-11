#!/usr/bin/env bash
# Closed-loop EXTRAS launcher (pre-registration docs/thesis/closed_loop_extras/preregistration.md, commit 7bf0bff;
# D133, D136). Flies the n = 3 no-heading EKF3/UKF cells, one argument per flight, serially, under the flight lock.
# Modelled on tools/run_fgo_refly.sh / tools/run_ukf_refly.sh.
#
# Every flight here is set (a) (no heading), where the registered criteria themselves expect the vehicle to reach
# the west wall inside a window (EKF3 [+155,+215] s; UKF [+146,+218] s) after a 300 s cruise -- see
# sim/tools/wall_watch.py and the flight-1 results (e.g. eval/results/closed_loop_cl_a_tex.json: "run_trial exit
# 143; watcher exit 0" + a BREACH.txt starting "wall contact"). A "wall contact" BREACH is therefore the EXPECTED
# end and does NOT stop this launcher (same exp_contact=1 pattern as run_ukf_refly.sh's case "a", applied to every
# case here). The launcher DOES stop at: a missing result.txt, a BREACH.txt whose first line is not "wall contact"
# (crash, box, or dependency-loss breach), or a nonzero watcher exit.
#
#   cl_ukf_a_tex_v2_r1..r3        corridor_textured_fwdc,       UKF=1  (full real time)
#   cl_a_tex_r2, cl_a_tex_r3      corridor_textured_fwdc,       EKF3   (full real time)
#   cl_a_tex_half_r2, _r3         corridor_textured_half_fwdc,  EKF3   (half real time)
#   cl_ukf_a_tex_half_v2_r2, _r3  corridor_textured_half_fwdc,  UKF=1  (half real time)
#
# Re-flies (IMU-gap rule "unusable", pre-registration section 1): add a <name>b case here -- committed while
# nothing is running -- before flying it. The superseded directory is kept.
#
# Launch: EKF3 = sim/tools/closed_loop_run.sh <world> <name>; UKF = env UKF=1 sim/tools/closed_loop_run.sh <world> <name>.
set -u; cd "$(dirname "$0")/.."; source tools/flight_lock.sh
for t in "$@"; do
  case "$t" in
    cl_ukf_a_tex_v2_r1) name=cl_ukf_a_tex_v2_r1; cmd=(env UKF=1 sim/tools/closed_loop_run.sh corridor_textured_fwdc);;
    cl_ukf_a_tex_v2_r2) name=cl_ukf_a_tex_v2_r2; cmd=(env UKF=1 sim/tools/closed_loop_run.sh corridor_textured_fwdc);;
    cl_ukf_a_tex_v2_r3) name=cl_ukf_a_tex_v2_r3; cmd=(env UKF=1 sim/tools/closed_loop_run.sh corridor_textured_fwdc);;
    cl_a_tex_r2) name=cl_a_tex_r2; cmd=(sim/tools/closed_loop_run.sh corridor_textured_fwdc);;
    cl_a_tex_r3) name=cl_a_tex_r3; cmd=(sim/tools/closed_loop_run.sh corridor_textured_fwdc);;
    cl_a_tex_half_r2) name=cl_a_tex_half_r2; cmd=(sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    cl_a_tex_half_r3) name=cl_a_tex_half_r3; cmd=(sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    cl_ukf_a_tex_half_v2_r2) name=cl_ukf_a_tex_half_v2_r2; cmd=(env UKF=1 sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    cl_ukf_a_tex_half_v2_r3) name=cl_ukf_a_tex_half_v2_r3; cmd=(env UKF=1 sim/tools/closed_loop_run.sh corridor_textured_half_fwdc);;
    *) echo "bad arg $t"; exit 2;;
  esac
  [ -e "$HOME/thesis_data/trials/$name" ] && { echo "$name exists; stopping"; exit 1; }
  flight_lock_acquire "$name" 7200 || { echo "no flight lock; stopping"; exit 1; }
  "${cmd[@]}" "$name"
  flight_lock_release
  r="$HOME/thesis_data/closed_loop/$name"
  if [ ! -f "$r/result.txt" ]; then echo "cl_extras: $name NO result.txt - stopping"; exit 1; fi
  cat "$r/result.txt"
  if [ -f "$r/BREACH.txt" ] && ! head -1 "$r/BREACH.txt" | grep -q "^wall contact"; then
    echo "cl_extras: $name BREACHED (not wall contact) - stopping"; exit 1
  fi
  if ! grep -q "watcher exit 0" "$r/result.txt"; then
    echo "cl_extras: $name watcher exit nonzero - stopping"; exit 1
  fi
  echo "cl_extras: $name flown"
done
