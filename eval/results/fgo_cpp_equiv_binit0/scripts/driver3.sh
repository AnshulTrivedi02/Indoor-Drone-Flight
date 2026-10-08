#!/bin/bash
# post-hoc emulate-gemv diagnostic; waits for driver.sh and driver2.sh to finish first
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
B=$S/binit0
HEAVY="python3 $HOME/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
DEADLINE=$(date -d "2026-10-09 05:50" +%s)
while pgrep -f "binit0/driver.sh|binit0/driver2.sh" >/dev/null; do
  [ $(date +%s) -ge $DEADLINE ] && { echo "[driver3] time box, not run"; exit 75; }
  sleep 30
done
run() {
  local name=$1; shift
  local left=$(( DEADLINE - $(date +%s) ))
  if [ $left -le 60 ]; then echo "[driver3] $(date +%T) SKIP $name"; return 75; fi
  echo "[driver3] $(date +%T) START $name"
  $HEAVY --wait-s $left "binit0 $name" -- bash $B/step_emu.sh "$@" > $B/logs/$name.log 2>&1
  local rc=$?; echo "[driver3] $(date +%T) END $name rc=$rc"; return $rc
}
run emu_build build && for t in dsn_blank_r1 dsn_trans_r1 dsn_tex_r1; do run emu_$t replay ${t}_baseline; done
echo "[driver3] $(date +%T) ALL DONE"
