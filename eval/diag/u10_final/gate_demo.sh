#!/bin/bash
# U10 gate end-to-end on SITL (PLUMBING ONLY: SIM truth stands in for mocap, D_max = 1.0 m is the PROPOSED value used
# as a test input, the flights are 150 m corridors / SITL closed loops, not rung-1 flights). Installed Replay outputs.
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
W=/home/makerspace/thesis_ws/.claude/worktrees/agent-a5e6fd9bcc14a040c
R=$W/eval/results/u10_final; O=$S/u10f/rep_inst
PY=~/venv-ardupilot/bin/python
for L in cl_a_tex_half cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  $PY $W/eval/u10_gate.py flight --replay-dir $O/$L --score $R/score_${L}_sim_truth_inst.json --d-max 1.0 \
      --json $R/u10_gate_demo_$L.json > /dev/null
  python3 -c "import json;d=json.load(open('$R/u10_gate_demo_$L.json'));print('$L', d['verdict'], {g:(d[g]['pass'], d[g].get('why')) for g in ('preconditions','G1','G2','G3','G4','G5','G6')})"
done
# U10 rule 1: a run without ukf_stats.csv fails G3
rm -rf $S/u10f/nostats; mkdir -p $S/u10f/nostats/logs
cp $O/cl_a_tex_half/ukf_shadow.csv $O/cl_a_tex_half/ukf_geometry.csv $O/cl_a_tex_half/replay.log $O/cl_a_tex_half/binary.md5 $S/u10f/nostats/
cp $O/cl_a_tex_half/logs/00000001.BIN $S/u10f/nostats/logs/
$PY $W/eval/u10_gate.py flight --replay-dir $S/u10f/nostats --score $R/score_cl_a_tex_half_sim_truth_inst.json --d-max 1.0 \
    --name cl_a_tex_half_no_ukf_stats --json $R/u10_gate_demo_nostats.json > /dev/null
python3 -c "import json;d=json.load(open('$R/u10_gate_demo_nostats.json'));print('nostats', d['verdict'], d['G3'])"
rm -rf $S/u10f/nostats
# the set rule: 3 flights -> NOT EVALUABLE
$PY $W/eval/u10_gate.py set $R/u10_gate_demo_cl_a_tex_half.json $R/u10_gate_demo_cl_ukf_b_tex_r1_half_v2.json \
    $R/u10_gate_demo_H_s2v2_r1.json --json $R/u10_gate_demo_set.json | tail -12
