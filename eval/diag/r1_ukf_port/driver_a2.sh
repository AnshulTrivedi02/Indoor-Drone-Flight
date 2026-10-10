#!/bin/bash
# (a2) after the FLOW_TYPE gate: re-run the new build's default and UKF_GEOM_SITL=1 variants on the five logs (all
# FLOW_TYPE 5); they must be byte-identical to the first new build's outputs in a/. One heavy.py step per Replay.
R=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/r1ukf
NEW=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apukf/build/sitl/tool/Replay
T=/home/makerspace/thesis_data/trials
H="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
declare -A FENV=( [dsn_tex_r1]="X=0" [fwdplainc_tex_r1]="X=0" [cl_a_tex_half]="X=0"
                  [cl_ukf_b_tex_r1_half_v2]="UKF_EXTYAW=1" [H_s2v2_r1]="UKF_EXTPOS=1 UKF_EXTYAW=1" )
for L in dsn_tex_r1 fwdplainc_tex_r1 cl_a_tex_half cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  E=${FENV[$L]}
  for V in new geomsitl; do
    X=""; [ $V = geomsitl ] && X="UKF_GEOM_SITL=1"
    [ -s $R/a2/$L/$V/ukf_shadow.csv ] && { echo "$L $V done"; continue; }
    echo -n "$L $V: "
    $H "r1 UKF port regression replay (FLOW_TYPE gate) $L $V" -- bash $R/run_one.sh $R/a2/$L/$V $NEW $T/$L/ardupilot.bin $E $X || echo "heavy rc=$?"
    for f in ukf_shadow.csv ukf_inputs.csv ukf_derot.csv ukf_geometry.csv; do
      cmp -s $R/a/$L/$V/$f $R/a2/$L/$V/$f && echo "  $f identical to first build" || echo "  $f DIFFERS from first build"
    done
  done
done
echo DRIVER_DONE
