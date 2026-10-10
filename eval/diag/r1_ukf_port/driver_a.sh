#!/bin/bash
# (a) old vs new Replay regression: 5 logs x {old, new, new+GEOM_SITL, new+DEROT_ROFH, new+both}. Each Replay is one
# heavy.py step (lock protocol). The flight's own UKF options are passed for the closed-loop UKF logs.
R=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/r1ukf
OLD=/home/makerspace/ardupilot_ukf/build/sitl/tool/Replay          # abb0357d0f, md5 e8e9feac (read-only use)
NEW=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apukf/build/sitl/tool/Replay
T=/home/makerspace/thesis_data/trials
H="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
declare -A FENV=( [dsn_tex_r1]="X=0" [fwdplainc_tex_r1]="X=0" [cl_a_tex_half]="X=0"
                  [cl_ukf_b_tex_r1_half_v2]="UKF_EXTYAW=1" [H_s2v2_r1]="UKF_EXTPOS=1 UKF_EXTYAW=1" )
for L in dsn_tex_r1 fwdplainc_tex_r1 cl_a_tex_half cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  E=${FENV[$L]}
  for V in old new geomsitl derotrofh both; do
    case $V in
      old) B=$OLD; X="";;
      new) B=$NEW; X="";;
      geomsitl) B=$NEW; X="UKF_GEOM_SITL=1";;
      derotrofh) B=$NEW; X="UKF_DEROT_ROFH=1";;
      both) B=$NEW; X="UKF_GEOM_SITL=1 UKF_DEROT_ROFH=1";;
    esac
    [ -s $R/a/$L/$V/ukf_shadow.csv ] && { echo "$L $V done"; continue; }
    echo -n "$L $V: "
    $H "r1 UKF port regression replay $L $V" -- bash $R/run_one.sh $R/a/$L/$V $B $T/$L/ardupilot.bin $E $X || echo "heavy rc=$?"
  done
done
echo DRIVER_DONE
