#!/bin/sh
set -e
cd /home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4
sed -i 's/if c > et\[-1\] + 1e-6:/if c > et[-1] + 0.1:/' eval/diag/ukf_jitter_fix/cpp_free_inertial.py
P=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
for c in A C; do
  ~/venv-fgo/bin/python3 eval/diag/ukf_jitter_fix/cpp_free_inertial.py score $P/cfi60_$c $P/fi60.json $c analytic_tv > $P/cfi60_$c.score.txt
  grep -A1 "case\|t= 10\|t= 60" $P/cfi60_$c.score.txt
done
~/venv-fgo/bin/python3 eval/diag/ukf_jitter_fix/cpp_free_inertial.py score $P/cfi10_B $P/fi10.json B analytic > $P/cfi10_B.score.txt
cp $P/cfi60_A.score.json $P/cfi60_C.score.json $P/cfi10_B.score.json $P/cfi60_A.score.txt $P/cfi60_C.score.txt $P/cfi10_B.score.txt eval/diag/ukf_jitter_fix/results/
