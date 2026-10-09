#!/bin/sh
set -e
J=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
D=/home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4/eval/diag/ukf_jitter_fix
R=$D/results
cd $J
cp s2/equiv_dsn_tex_r2.json s2/equiv_dsn_tex_r2_d27.json $R/
cp s2/export.log $R/step2_dsn_tex_r2_export.log
cp ua/tierA.json $R/tierA_H_s1_r1.json
cp ua/tierA_d27.json $R/tierA_H_s1_r1_diagD27q.json
cp ua/export.log $R/tierA_H_s1_r1_export.log
cp equiv.log $R/equiv_run.log
cp build_port.log $R/port_build.log
cp equiv.sh s2_d27.sh s2_qdiag.py rts.sh build_port.sh stat_live.sh fi_wrap.py score_cfi.sh $D/
rm -f $R/fi_wrap.py
sh stat_live.sh > after_stat.txt 2>&1
cp before_stat.txt after_stat.txt $R/
diff before_stat.txt after_stat.txt && echo LIVE_UNCHANGED
ls $R
