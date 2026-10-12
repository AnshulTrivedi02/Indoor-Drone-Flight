#!/bin/bash
# XUKO FMT (2026-10-12): byte-identity of the four CSVs of a Replay build against the INSTALLED Replay be7c4d18's
# outputs (stored s12/inst/<L>/new, made 2026-10-12 with the same per-log environment), on the five SITL LOG_REPLAY
# logs. One heavy.py step per Replay. The replayed .BIN is kept (the FMT checks read it).
# Usage: driver.sh <replay-binary> <tag>
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
BIN=$1; TAG=$2
O=$S/s12/xuko_$TAG
REF=$S/s12/inst
T=/home/makerspace/thesis_data/trials
H="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py --wait-s 3600"
RUN=/home/makerspace/thesis_ws/.claude/worktrees/agent-a60b4a326e4fb1d35/eval/diag/xuko_fmt/run_one_keep.sh
declare -A FENV=( [dsn_tex_r1]="X=0" [fwdplainc_tex_r1]="X=0" [cl_a_tex_half]="X=0"
                  [cl_ukf_b_tex_r1_half_v2]="UKF_EXTYAW=1" [H_s2v2_r1]="UKF_EXTPOS=1 UKF_EXTYAW=1" )
md5sum $BIN
for L in cl_a_tex_half dsn_tex_r1 fwdplainc_tex_r1 cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  E=${FENV[$L]}
  if [ ! -s $O/$L/ukf_shadow.csv ]; then
    echo -n "$L: "
    $H "xuko-fmt Replay byte-identity $TAG $L" -- bash $RUN $O/$L $BIN $T/$L/ardupilot.bin $E || echo "heavy rc=$?"
  fi
  for f in ukf_shadow.csv ukf_inputs.csv ukf_derot.csv ukf_geometry.csv; do
    cmp -s $REF/$L/new/$f $O/$L/$f && echo "RESULT $L $f IDENTICAL to installed be7c4d18" || echo "RESULT $L $f DIFFERS from installed be7c4d18"
  done
  grep "end of run" $O/$L/replay.log || echo "RESULT $L no end-of-run line"
  cat $O/$L/ukf_stats.csv 2>/dev/null | tr '\n' ' '; echo
done
echo DRIVER_DONE
