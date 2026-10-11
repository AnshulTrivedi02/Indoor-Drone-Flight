#!/bin/bash
# 2026-10-12: byte-identity re-check of the INSTALLED Replay (~/ardupilot_ukf build, ukf-jitter-fix = rung1-geometry
# 16535f9a29), on the five SITL LOG_REPLAY logs of the 2026-10-11 stage. One heavy.py step per Replay.
#  derotrofh (UKF_DEROT_ROFH=1): shadow + inputs must equal the OLD installed Replay's (e8e9feac) outputs  a/<L>/old
#  new (default): all four CSVs must equal the tested scratch build's outputs                              a2/<L>/new
#                 and, on the type-12 logs, shadow + inputs must equal the OLD Replay's                      a/<L>/old
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
R=$S/r1ukf
O=$S/s12/inst
BIN=/home/makerspace/ardupilot_ukf/build/sitl/tool/Replay
T=/home/makerspace/thesis_data/trials
H="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
declare -A FENV=( [dsn_tex_r1]="X=0" [fwdplainc_tex_r1]="X=0" [cl_a_tex_half]="X=0"
                  [cl_ukf_b_tex_r1_half_v2]="UKF_EXTYAW=1" [H_s2v2_r1]="UKF_EXTPOS=1 UKF_EXTYAW=1" )
for L in dsn_tex_r1 fwdplainc_tex_r1 cl_a_tex_half cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  E=${FENV[$L]}
  for V in derotrofh new; do
    X=""; [ $V = derotrofh ] && X="UKF_DEROT_ROFH=1"
    if [ ! -s $O/$L/$V/ukf_shadow.csv ]; then
      echo -n "$L $V: "
      $H "UKF port install re-check replay $L $V" -- bash $R/run_one.sh $O/$L/$V $BIN $T/$L/ardupilot.bin $E $X || echo "heavy rc=$?"
    fi
    if [ $V = derotrofh ]; then
      for f in ukf_shadow.csv ukf_inputs.csv; do
        cmp -s $R/a/$L/old/$f $O/$L/$V/$f && echo "RESULT $L $V $f IDENTICAL to old installed Replay" || echo "RESULT $L $V $f DIFFERS from old installed Replay"
      done
    else
      for f in ukf_shadow.csv ukf_inputs.csv ukf_derot.csv ukf_geometry.csv; do
        cmp -s $R/a2/$L/new/$f $O/$L/$V/$f && echo "RESULT $L $V $f IDENTICAL to tested scratch build" || echo "RESULT $L $V $f DIFFERS from tested scratch build"
      done
      for f in ukf_shadow.csv ukf_inputs.csv; do
        cmp -s $R/a/$L/old/$f $O/$L/$V/$f && echo "RESULT $L $V $f IDENTICAL to old installed Replay" || echo "RESULT $L $V $f differs from old installed Replay"
      done
    fi
  done
done
echo DRIVER_DONE
