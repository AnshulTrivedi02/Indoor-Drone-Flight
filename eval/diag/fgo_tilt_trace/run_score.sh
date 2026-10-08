#!/bin/bash
# FGO tilt trace: score H_s1_r1 tag losses with a scratch copy of eval/h_score.py (only the FGO track path is switchable).
cd "$(dirname "$0")"
SIG=$(python3 -c "import json;print(json.load(open('/home/makerspace/thesis_ws/eval/results/expH/s1_r1.json'))['sigma_pos'])")
cd /home/makerspace/thesis_ws
~/venv-tags/bin/python "$OLDPWD/h_score_diag.py" H_s1_r1 --profile batches/expH/s1_profile.json --sigma $SIG --json "$OLDPWD/score_s1_stored.json" > /dev/null
DIAG_FGO_TUM="$OLDPWD/out/s1full_binit0/H_s1_r1/room_fgo/fgo_live.tum" ~/venv-tags/bin/python "$OLDPWD/h_score_diag.py" H_s1_r1 --profile batches/expH/s1_profile.json --sigma $SIG --json "$OLDPWD/score_s1_binit0.json" > /dev/null
echo done
