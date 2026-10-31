#!/usr/bin/env bash
# E6 Stage 1b: gates G0-UKF, G-E4' (flag unset, byte identity) and V-E6 (flag = true map), serial, one heavy.py job at a
# time, from the e6-map-reuse worktree. Timing in timing.tsv; logs in logs/. (docs/thesis/tier1/e6_preregistration.md §7)
set -u
W=/home/makerspace/thesis_ws/.claude/worktrees/agent-afa2971452f4e8507
E=/home/makerspace/thesis_data/tier1/e6
H="python3 $W/src/estimators/fgo_cpp/tools/heavy.py --wait-s 7200"
mkdir -p $E/logs; TS=$E/timing.tsv
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TBB_NUM_THREADS=1
idle_wait() {   # the plot agent's figure jobs are not heavy-locked: wait while one runs (cap 2 h)
  local t0=$(date +%s)
  while pgrep -f '[f]igs_' >/dev/null; do
    [ $(( $(date +%s) - t0 )) -gt 7200 ] && { echo "plot job still running after 2 h; stop" >&2; exit 2; }
    echo "$(date -Is) waiting: plot job running" >> $E/logs/idle.log; sleep 60
  done
  echo "$(date -Is) idle ok before $1 (plot: none; heavy.py re-checks flights and BUILD_LOCK)" >> $E/logs/idle.log
}
run() {   # run <job name> <cmd...>
  local name=$1; shift; idle_wait "$name"
  local s=$(date +%s.%N); echo "$(date -Is) START $name" >> $E/logs/driver.log
  ( cd $W && $H "e6 stage1b $name" -- "$@" ) > $E/logs/$name.log 2>&1; local rc=$?
  local e=$(date +%s.%N); printf '%s\t%s\t%s\t%.1f\t%s\n' "$name" "$(date -d @${s%.*} -Is)" "$(date -d @${e%.*} -Is)" "$(echo "$e - $s" | bc)" "$rc" >> $TS
  echo "$(date -Is) END $name rc=$rc" >> $E/logs/driver.log
}
TR="T_A_r1 T_A_r2 T_A_r3 T_B_r1 T_B_r2 T_B_r3 T_C_r1 T_C_r2 T_C_r3 T_D_r1 T_D_r2 T_D_r3"
for t in $TR; do run g0ukf_$t env UKF_OUT_ROOT=/home/makerspace/thesis_data/tier1/e6_g0_ukf /home/makerspace/venv-evo/bin/python src/estimators/room_ukf_replay.py $t; done
for t in $TR; do run ge4_$t /home/makerspace/venv-fgo/bin/python src/estimators/fgo/room_fgo_replay.py $t --no-batch --window 0.25 --out-root /home/makerspace/thesis_data/tier1/e6_g0_fgo; done
for t in T_A_r1 T_A_r2 T_A_r3; do
  run ve6ukf_$t env UKF_OUT_ROOT=/home/makerspace/thesis_data/tier1/e6_val /home/makerspace/venv-evo/bin/python src/estimators/room_ukf_replay.py $t --tag-map $W/sim/worlds/room_tags_map.json --tag-map-name truemap
  run ve6fgo_$t /home/makerspace/venv-fgo/bin/python src/estimators/fgo/room_fgo_replay.py $t --no-batch --out-root /home/makerspace/thesis_data/tier1/e6_val --tag-map $W/sim/worlds/room_tags_map.json --tag-map-name truemap
done
echo "$(date -Is) ALL DONE" >> $E/logs/driver.log
touch $E/stage1b.done
