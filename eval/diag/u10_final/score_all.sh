#!/bin/bash
# U10 rule 2: replay_gate.py and the rung-1 scorer (SIM truth standing in for mocap; plumbing only) on the Replay
# outputs of a build (tag). Usage: score_all.sh <tag>
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
W=/home/makerspace/thesis_ws/.claude/worktrees/agent-a5e6fd9bcc14a040c
TAG=$1; O=$S/u10f/rep_$TAG; R=$W/eval/results/u10_final
PY=~/venv-ardupilot/bin/python
for L in cl_a_tex_half cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  echo "== $L"
  $PY $W/eval/replay_gate.py $O/$L/logs/00000001.BIN --json $R/replay_gate_${L}_$TAG.json | python3 -c "import json,sys;d=json.load(sys.stdin);print('replay_gate', 'PASS' if d['pass'] else 'FAIL', d['n'], d['max_horizontal_m'], d['max_height_m'], d['max_yaw_deg'], d['reader'])" || echo "replay_gate FAILED to run"
  X=""; [ "$L" != cl_a_tex_half ] && X=--onboard
  $PY $W/eval/diag/u10_final/score_rukx.py $O/$L/logs/00000001.BIN $S/u10f/score_${L}_$TAG $R/score_${L}_sim_truth_$TAG.json $X 2>&1 | tail -14
done
