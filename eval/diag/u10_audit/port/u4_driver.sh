#!/bin/bash
# Byte-identity of the rebased u4-gndclr Replay against the INSTALLED Replay 3c3b62bb on the 5 SITL LOG_REPLAY logs:
# the five CSVs per log (25 files) against the stored installed outputs (u10f/rep_inst/<L>), each log in its stored
# environment. One heavy.py step per Replay. The replayed .BINs are not compared (FMTU process-clock stamps differ).
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
BIN=$S/g5a/u4wt/build/sitl/tool/Replay
REF=$S/u10f/rep_inst
O=$S/g5a/u4rep
T=/home/makerspace/thesis_data/trials
H="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py --wait-s 14400"
md5sum $BIN
for L in cl_a_tex_half dsn_tex_r1 fwdplainc_tex_r1 cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  E=$(cat $REF/$L/env.txt)
  if [ ! -s $O/$L/ukf_stats.csv ]; then
    echo -n "$L ($E): "
    $H "U4 rebased Replay byte-identity $L" -- bash $S/r1ukf/run_one.sh $O/$L $BIN $T/$L/ardupilot.bin $E || echo "heavy rc=$?"
  fi
  for f in ukf_shadow.csv ukf_inputs.csv ukf_derot.csv ukf_geometry.csv ukf_stats.csv; do
    cmp -s $REF/$L/$f $O/$L/$f && echo "RESULT $L $f IDENTICAL" || echo "RESULT $L $f DIFFERS"
  done
  grep "end of run" $O/$L/replay.log || echo "RESULT $L no end-of-run line"
done
echo DRIVER_DONE
