#!/bin/bash
# U4 (2026-10-12): regression + positive test of the u4-gndclr scratch Replay. One heavy.py step per Replay.
#  reg  (default): all four CSVs must equal the INSTALLED Replay's outputs (s12/inst/<L>/new; range always valid on these logs)
#  low  (UKF_TEST_RNG_LOW=0.15, the test hook): the resting reading (0.075-0.08 m) counts as OutOfRangeLow inside the
#       UKF only; expected: initialisation from GNDCLR (0.10 m) before arming, then the normal path once airborne
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
R=$S/r1ukf
I=$S/s12/inst
O=$S/s12/u4
BIN=$S/apu4/build/sitl/tool/Replay
T=/home/makerspace/thesis_data/trials
H="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
declare -A FENV=( [dsn_tex_r1]="X=0" [fwdplainc_tex_r1]="X=0" [cl_a_tex_half]="X=0"
                  [cl_ukf_b_tex_r1_half_v2]="UKF_EXTYAW=1" [H_s2v2_r1]="UKF_EXTPOS=1 UKF_EXTYAW=1" )
for L in dsn_tex_r1 fwdplainc_tex_r1 cl_a_tex_half cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  E=${FENV[$L]}
  if [ ! -s $O/$L/reg/ukf_shadow.csv ]; then
    echo -n "$L reg: "
    $H "U4 regression replay $L" -- bash $R/run_one.sh $O/$L/reg $BIN $T/$L/ardupilot.bin $E || echo "heavy rc=$?"
  fi
  for f in ukf_shadow.csv ukf_inputs.csv ukf_derot.csv ukf_geometry.csv; do
    cmp -s $I/$L/new/$f $O/$L/reg/$f && echo "RESULT $L reg $f IDENTICAL to installed Replay" || echo "RESULT $L reg $f DIFFERS from installed Replay"
  done
done
for L in dsn_tex_r1 cl_ukf_b_tex_r1_half_v2; do
  E=${FENV[$L]}
  if [ ! -s $O/$L/low/ukf_shadow.csv ]; then
    echo -n "$L low: "
    $H "U4 positive test replay $L" -- bash $R/run_one.sh $O/$L/low $BIN $T/$L/ardupilot.bin $E UKF_TEST_RNG_LOW=0.15 || echo "heavy rc=$?"
  fi
  grep -E "u4_|resolved_at" $O/$L/low/ukf_geometry.csv
  grep -E "TOGCS: UKF" $O/$L/low/replay.log | head -5
done
echo DRIVER_DONE
