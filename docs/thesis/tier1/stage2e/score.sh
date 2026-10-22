#!/bin/bash
# Stage 2e: score every E3 run once with eval/l_score.py (preregistration §2.2), into docs/thesis/tier1/scores/.
set -u
cd /home/makerspace/thesis_ws
SC=docs/thesis/tier1/scores; B=_t245_tags0-1-2-3-4-5-6-7; RB=_robcauchy2.385
sc(){ echo "== $1 $2"; ~/venv-tags/bin/python eval/l_score.py $1 --in-root ~/thesis_data/tier1 --suffix "$2" --json $SC/$3 || exit 1; }
for r in 1 2 3; do for p in 0.01 0.05; do for s in 0 1 2; do
  sc T_A_r$r "${B}_mis${p}_s$s" E3a_T_A_r${r}_${p}_s$s.json; done; done; done
for r in 1 2 3; do sc T_A_r$r "${B}${RB}" E3b_T_A_r${r}_0.json; done
for r in 1 2 3; do for p in 0.01 0.05; do for s in 0 1 2; do
  sc T_A_r$r "${B}_mis${p}_s$s${RB}" E3b_T_A_r${r}_${p}_s$s.json; done; done; done
echo SCORED_ALL
