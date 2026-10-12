#!/bin/bash
# U10 gate demo RE-RUN (2026-10-12, stage u10_g5_audit_rebase) with the audited eval/u10_gate.py. PLUMBING ONLY:
# SIM truth stands in for mocap, the flights are SITL corridors / closed loops, not rung-1 flights. Inputs: the stored
# Replay outputs of the INSTALLED Replay 3c3b62bb (scratchpad u10f/rep_inst, made by stage 2026-10-12_u10_final) and
# their committed SIM-truth scores (eval/results/u10_final/score_*_inst.json). Gate only (light); nothing replayed.
# D_max is the signed default (1.0 m): no --d-max is passed.
set -u
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
W=/home/makerspace/thesis_ws/.claude/worktrees/agent-a5792858aabb1c0d5
R=$W/eval/results/u10_audit; SC=$W/eval/results/u10_final; O=$S/u10f/rep_inst
PY=~/venv-ardupilot/bin/python
mkdir -p $R
for L in cl_a_tex_half cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  $PY $W/eval/u10_gate.py flight --replay-dir $O/$L --score $SC/score_${L}_sim_truth_inst.json --name $L \
      --json $R/u10_gate_demo_$L.json > /dev/null
  $PY -c "import json;d=json.load(open('$R/u10_gate_demo_$L.json'));print('$L gated:', d['verdict'], {g:(d[g]['pass'], d[g].get('why')) for g in ('preconditions','G1','G2','G3','G4','G5','G6')})"
done
# H_s2v2_r1 the way the protocol treats an H log (plumbing: no score), and as a V log (G1-G3 judged)
$PY $W/eval/u10_gate.py flight --replay-dir $O/H_s2v2_r1 --name H_s2v2_r1_plumbing --json $R/u10_gate_demo_H_s2v2_r1_plumbing.json > /dev/null
$PY -c "import json;d=json.load(open('$R/u10_gate_demo_H_s2v2_r1_plumbing.json'));print('H_s2v2_r1 plumbing:', d['verdict'])"
$PY $W/eval/u10_gate.py flight --replay-dir $O/H_s2v2_r1 --score $SC/score_H_s2v2_r1_sim_truth_inst.json --verification \
    --name H_s2v2_r1_verification --json $R/u10_gate_demo_H_s2v2_r1_verification.json > /dev/null
$PY -c "import json;d=json.load(open('$R/u10_gate_demo_H_s2v2_r1_verification.json'));print('H_s2v2_r1 verification:', d['verdict'], 'G5 reported:', d['G5'].get('why'))"
# a changed D_max is refused
$PY $W/eval/u10_gate.py flight --replay-dir $O/H_s2v2_r1 --score $SC/score_H_s2v2_r1_sim_truth_inst.json --d-max 2.0 > /dev/null 2> $R/dmax_refusal.txt
echo "d-max 2.0 rc=$? : $(cat $R/dmax_refusal.txt)"
# U10 rule 1: a run without ukf_stats.csv fails G3 (copy of cl_a_tex_half without the file)
T=$S/u10audit_nostats; rm -rf $T; mkdir -p $T/logs
cp $O/cl_a_tex_half/ukf_shadow.csv $O/cl_a_tex_half/ukf_geometry.csv $O/cl_a_tex_half/replay.log $O/cl_a_tex_half/binary.md5 $T/
cp $O/cl_a_tex_half/logs/00000001.BIN $T/logs/
$PY $W/eval/u10_gate.py flight --replay-dir $T --score $SC/score_cl_a_tex_half_sim_truth_inst.json \
    --name cl_a_tex_half_no_ukf_stats --json $R/u10_gate_demo_nostats.json > /dev/null
$PY -c "import json;d=json.load(open('$R/u10_gate_demo_nostats.json'));print('nostats:', d['verdict'], d['G3']['why'])"
rm -rf $T
# the set of the 3 gated records: NOT EVALUABLE (< 4)
$PY $W/eval/u10_gate.py set $R/u10_gate_demo_cl_a_tex_half.json $R/u10_gate_demo_cl_ukf_b_tex_r1_half_v2.json \
    $R/u10_gate_demo_H_s2v2_r1.json --json $R/u10_gate_demo_set.json | $PY -c "import json,sys;print('set:', json.load(sys.stdin)['verdict'])"
echo DEMO_DONE
