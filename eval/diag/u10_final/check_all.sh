#!/bin/bash
# U10 rule 2: check_rukx.py on the five Replay outputs of a build (tag), against the installed e82c050b outputs.
# Usage: check_all.sh <tag>   (outputs in scratchpad/u10f/rep_<tag>; JSON to eval/results/u10_final/)
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
W=/home/makerspace/thesis_ws/.claude/worktrees/agent-a5e6fd9bcc14a040c
TAG=$1; O=$S/u10f/rep_$TAG; REF=$S/s12/xuko_inst; T=/home/makerspace/thesis_data/trials
mkdir -p $W/eval/results/u10_final
for L in cl_a_tex_half dsn_tex_r1 fwdplainc_tex_r1; do
  ~/venv-ardupilot/bin/python $W/eval/diag/u10_final/check_rukx.py --new $O/$L/logs/00000001.BIN \
    --ref $REF/$L/logs/00000001.BIN --json $W/eval/results/u10_final/check_${L}_$TAG.json > /dev/null
  echo "$L: $(python3 -c "import json;d=json.load(open('$W/eval/results/u10_final/check_${L}_$TAG.json'));print('PASS' if d['PASS'] else 'FAIL', d['counts'], d['bytecmp_vs_ref']['differing'])")"
done
for L in cl_ukf_b_tex_r1_half_v2 H_s2v2_r1; do
  ~/venv-ardupilot/bin/python $W/eval/diag/u10_final/check_rukx.py --new $O/$L/logs/00000001.BIN \
    --ref $REF/$L/logs/00000001.BIN --input $T/$L/ardupilot.bin --shadow $O/$L/ukf_shadow.csv \
    --stored-b $W/eval/results/r1_ukf_port/b_$L.json --json $W/eval/results/u10_final/check_${L}_$TAG.json > /dev/null
  echo "$L: $(python3 -c "import json;d=json.load(open('$W/eval/results/u10_final/check_${L}_$TAG.json'));f=d['fork'];print('PASS' if d['PASS'] else 'FAIL', d['counts'], f['XUK_equals_input'], f['bands_RUKF_vs_onboard_XUKF'], f.get('stored_from_csv'))")"
done
