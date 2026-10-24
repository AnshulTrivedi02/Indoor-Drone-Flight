#!/bin/bash
# Score every rung after the last replay (pre-registration §5, §10). Refuses to overwrite a score file.
set -eu
A=/home/makerspace/thesis_data/ablation; R=/home/makerspace/thesis_ws; PY=/home/makerspace/venv-ardupilot/bin/python
sc() { [ -e "$A/scores/$3.json" ] && { echo "exists: $3"; return 0; }; $PY $R/docs/thesis/ablation/score_ablation.py --root "$1" --sub "$2" --json "$A/scores/$3.json" > "$A/scores/$3.out" 2>&1; echo "scored $3"; }
for r in r1:r1_kf1_lm1 r2:r2_kf1_lm2 r3:r3_kf1_lm100 r4:r4_w1_lm2 r5:r5_w2_lm2; do
  k=${r%%:*}; f=${r#*:}
  sc $A/$f fgo_heading ${k}_heading; sc $A/$f fgo_baseline ${k}_baseline
done
sc $A/r6_w0.25_lm2_huber fgo_heading_H1345 r6_heading
sc $A/r7_kf1_lm100_huber fgo_heading_H1345 r7_heading
sc /home/makerspace/thesis_data/trials fgo_heading_F1cauchy_2_385 r6s_heading
echo SCORED_ALL $(date -Iseconds)
