#!/bin/bash
# resume after the scheduled pause: fi60, the emulate-gemv diagnostic, the forced-gate diagnostics (each via heavy.py)
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
Y=$S/yawgate
HEAVY="python3 $HOME/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
run() {   # run <name> <script> <args>
  local name=$1 sc=$2; shift 2
  echo "[driver3] $(date +%T) START $name"
  $HEAVY --wait-s 3600 "yawgate $name" -- bash $Y/$sc "$@" > $Y/logs/$name.log 2>&1
  local rc=$?; echo "[driver3] $(date +%T) END $name rc=$rc"; return $rc
}
run fi60 step2.sh fi60
run emu_build step.sh emu_build && for t in dsn_tex_r1 dsn_blank_r1 dsn_trans_r1; do run emu_$t step.sh emu ${t}_baseline; done
run forced_dsn_tex step2.sh forced dsn_tex_r1_baseline fgo_replay.py dsn_tex_r1 0.25 2 baseline
run forced_dsn_trans step2.sh forced dsn_trans_r1_baseline fgo_replay.py dsn_trans_r1 0.25 2 baseline
run forced_dsn_blank step2.sh forced dsn_blank_r1_baseline fgo_replay.py dsn_blank_r1 0.25 2 baseline
echo "[driver3] $(date +%T) ALL DONE"
