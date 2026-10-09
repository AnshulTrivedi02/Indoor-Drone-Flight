#!/bin/bash
# Plain-wall divergence trace (2026-10-10): diagnostic replays, outputs to scratch only.
# FGO heading arm (window 0.25 s, LM 2) as Phase 4; UKF heading arm as Phase 4.
#   base   : unmodified FGO, tex_r1, with the equivalence dump (per-keyframe bias)
#   y0s1   : FGO with the UKF's initial yaw sigma (1 deg) via the existing off-by-default F_YAW0_* knob
#   y0t    : UKF with the FGO's initial yaw sigma (1e-3 rad = 0.0573 deg), the discriminator
SC=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/pw
W=/home/makerspace/thesis_ws/.claude/worktrees/agent-a375613081292d466
FP=/home/makerspace/venv-fgo/bin/python
UP=/home/makerspace/venv-evo/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export FGO_OUT_ROOT=$SC/out UKF_OUT_ROOT=$SC/out FGO_BAG_ROOT=$SC/bags UKF_BAG_ROOT=$SC/bags
mkdir -p $SC/out $SC/logs $SC/dump
cd $W
run() { local name=$1; shift; ( "$@" > $SC/logs/$name.log 2>&1; echo "exit $?" >> $SC/logs/$name.log ) & }

run fgo_base_tex_r1 env FGO_DUMP_EVENTS=$SC/dump/base_tex_r1 $FP src/estimators/fgo/fgo_replay.py fwdplainc_tex_r1 0.25 2 heading
run fgo_y0s1_tex_r1 env F_TAG=y0s1 F_YAW0_DEG=0 F_YAW0_SIGMA_DEG=1 FGO_DUMP_EVENTS=$SC/dump/y0s1_tex_r1 $FP src/estimators/fgo/fgo_replay.py fwdplainc_tex_r1 0.25 2 heading
run fgo_y0s1_trans_r1 env F_TAG=y0s1 F_YAW0_DEG=0 F_YAW0_SIGMA_DEG=1 $FP src/estimators/fgo/fgo_replay.py fwdplainc_trans_r1 0.25 2 heading
run ukf_y0t_tex_r1 env F_TAG=y0t F_YAW0_DEG=0 F_YAW0_SIGMA_DEG=0.0572958 $UP $SC/ukf_replay_scratch.py fwdplainc_tex_r1 heading
run ukf_y0t_trans_r1 env F_TAG=y0t F_YAW0_DEG=0 F_YAW0_SIGMA_DEG=0.0572958 $UP $SC/ukf_replay_scratch.py fwdplainc_trans_r1 heading
run fgo_y0s1_fwdc_tex_r1 env F_TAG=y0s1 F_YAW0_DEG=0 F_YAW0_SIGMA_DEG=1 $FP src/estimators/fgo/fgo_replay.py fwdc_tex_r1 0.25 2 heading
run ukf_base_tex_r1 $UP $SC/ukf_replay_scratch.py fwdplainc_tex_r1 heading
wait
for b in fwdplainc_tex_r2 fwdplainc_tex_r3 fwdplainc_trans_r2 fwdplainc_trans_r3 fwdplainc_blank_r1; do
  run fgo_y0s1_$b env F_TAG=y0s1 F_YAW0_DEG=0 F_YAW0_SIGMA_DEG=1 $FP src/estimators/fgo/fgo_replay.py $b 0.25 2 heading
done
wait
echo ALLDONE
