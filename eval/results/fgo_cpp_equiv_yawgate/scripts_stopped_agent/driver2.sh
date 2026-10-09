#!/bin/bash
# after driver.sh bands + emu: 60 s free inertial, then the post-hoc forced-gate diagnostics (every step via heavy.py)
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
Y=$S/yawgate
HEAVY="python3 $HOME/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
while pgrep -f "yawgate/driver.sh" >/dev/null; do sleep 20; done
run() {
  local name=$1; shift
  echo "[driver2] $(date +%T) START $name"
  $HEAVY --wait-s 7200 "yawgate $name" -- bash $Y/step2.sh "$@" > $Y/logs/$name.log 2>&1
  local rc=$?; echo "[driver2] $(date +%T) END $name rc=$rc"; return $rc
}
run fi60 fi60
run forced_dsn_tex forced dsn_tex_r1_baseline fgo_replay.py dsn_tex_r1 0.25 2 baseline
run forced_dsn_trans forced dsn_trans_r1_baseline fgo_replay.py dsn_trans_r1 0.25 2 baseline
run forced_dsn_blank forced dsn_blank_r1_baseline fgo_replay.py dsn_blank_r1 0.25 2 baseline
echo "[driver2] $(date +%T) ALL DONE"
