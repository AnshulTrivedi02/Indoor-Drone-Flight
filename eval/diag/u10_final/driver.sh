#!/bin/bash
# U10 rule 2 (2026-10-12): Replay a build on the five SITL LOG_REPLAY logs (one heavy.py step per Replay), keep the
# replayed .BIN, and compare the five CSVs byte for byte with the INSTALLED Replay e82c050b's outputs of the same
# inputs and environments (stored by the xuko_u10_h10 stage in s12/xuko_inst/<L>).
# Usage: driver.sh <replay-binary> <tag>
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
BIN=$1; TAG=$2
O=$S/u10f/rep_$TAG
REF=$S/s12/xuko_inst
T=/home/makerspace/thesis_data/trials
H="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py --wait-s 3600"
RUN=/home/makerspace/thesis_ws/.claude/worktrees/agent-a5e6fd9bcc14a040c/eval/diag/xuko_fmt/run_one_keep.sh
declare -A FENV=( [dsn_tex_r1]="X=0" [fwdplainc_tex_r1]="X=0" [cl_a_tex_half]="X=0"
                  [cl_ukf_b_tex_r1_half_v2]="UKF_EXTYAW=1" [H_s2v2_r1]="UKF_EXTPOS=1 UKF_EXTYAW=1" )
md5sum $BIN
for L in cl_a_tex_half dsn_tex_r1 fwdplainc_tex_r1 cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  E=${FENV[$L]}
  cmp -s <(cat $REF/$L/env.txt) <(echo "$E") || echo "WARN $L env differs from the reference: $(cat $REF/$L/env.txt) vs $E"
  if [ ! -s $O/$L/ukf_shadow.csv ]; then
    echo -n "$L: "
    $H "U10 rule-2 Replay $TAG $L" -- bash $RUN $O/$L $BIN $T/$L/ardupilot.bin $E || echo "heavy rc=$?"
  fi
  for f in ukf_shadow.csv ukf_inputs.csv ukf_derot.csv ukf_geometry.csv ukf_stats.csv; do
    cmp -s $REF/$L/$f $O/$L/$f && echo "RESULT $L $f IDENTICAL to installed e82c050b" || echo "RESULT $L $f DIFFERS from installed e82c050b"
  done
  grep "end of run" $O/$L/replay.log || echo "RESULT $L no end-of-run line"
done
echo DRIVER_DONE
