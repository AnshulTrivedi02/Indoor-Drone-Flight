#!/bin/bash
# board-h743 (2a): SITL byte-identity of the board-h743 build (6280a35745 source) against
#   (i)  the rung1-geometry 16535f9a29 build's stored Replay outputs (scratchpad/r1ukf/a2/<log>/new, Replay a1f67e7d);
#   (ii) the INSTALLED Replay (~/ardupilot_ukf/build/sitl/tool/Replay, e8e9feac, abb0357d0f) stored outputs
#        (r1ukf/a/<log>/old) on the type-12 log only, where installed == rung1 (2026-10-11 handover table);
#   (iii) UKF_Equiv on the 2026-10-09 tapes: new vs installed (537e0dcd) vs the stored port outputs.
# Each Replay is one heavy.py step. The input logs are only read.
H=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
R=$H/r1ukf; O=$H/h7/ident
NEW=$H/aph7/build/sitl/tool/Replay
T=/home/makerspace/thesis_data/trials
HV="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
mkdir -p $O
declare -A FENV=( [cl_a_tex_half]="X=0" [cl_ukf_b_tex_r1_half_v2]="UKF_EXTYAW=1" )
for L in cl_a_tex_half cl_ukf_b_tex_r1_half_v2; do
  if [ ! -s $O/$L/ukf_shadow.csv ]; then
    $HV "board-h743 SITL identity replay $L" -- bash $R/run_one.sh $O/$L $NEW $T/$L/ardupilot.bin ${FENV[$L]} || echo "heavy rc=$?"
  fi
  for f in ukf_shadow.csv ukf_inputs.csv ukf_derot.csv ukf_geometry.csv; do
    cmp -s $R/a2/$L/new/$f $O/$L/$f && echo "$L $f IDENTICAL to rung1-geometry 16535f9a29 (a1f67e7d)" || echo "$L $f DIFFERS from rung1-geometry"
  done
  if [ $L = cl_ukf_b_tex_r1_half_v2 ]; then
    for f in ukf_shadow.csv ukf_inputs.csv; do
      cmp -s $R/a/$L/old/$f $O/$L/$f && echo "$L $f IDENTICAL to the INSTALLED Replay e8e9feac" || echo "$L $f DIFFERS from installed"
    done
  fi
  wc -l $O/$L/ukf_shadow.csv
done
echo REPLAY_IDENTITY_DONE
