#!/usr/bin/env bash
# E6 Stage 2a/2b: test replays on T_A_r1..r3 with the supplied maps (pairing D85/D94: r1b->r1, r2->r2, r3->r3).
# 2a: UKF (live + RTS), 6 runs; 2b: FGO live + whole-flight batch, 6 runs (order r1 fgomap, r1 ukfmap, r2 ..., §8).
# Serial under heavy.py, threads 1, from the worktree. Idle check (plot jobs) before each run, liveness-timed.
set -u
W=/home/makerspace/thesis_ws/.claude/worktrees/agent-afa2971452f4e8507
E=/home/makerspace/thesis_data/tier1/e6; T1=/home/makerspace/thesis_data/tier1
H="python3 $W/src/estimators/fgo_cpp/tools/heavy.py --wait-s 7200"
TS=$W/docs/thesis/tier1/e6/stage2_timing.tsv; mkdir -p $E/logs
export UKF_OUT_ROOT=$T1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TBB_NUM_THREADS=1
STAGE=${1:-all}
idle_wait() { local t0=$(date +%s)
  while pgrep -f '[f]igs_' >/dev/null; do [ $(( $(date +%s) - t0 )) -gt 7200 ] && { echo "$(date -Is) idle timeout before $1" >> $E/logs/idle.log; exit 2; }
    echo "$(date -Is) waiting: plot job" >> $E/logs/idle.log; sleep 60; done
  echo "$(date -Is) idle ok before $1" >> $E/logs/idle.log; }
run() { local name=$1; shift; idle_wait "$name"; local s=$(date +%s.%N)
  echo "$(date -Is) START $name" >> $E/logs/driver_2.log
  ( cd $W && $H "e6 stage2 $name" -- "$@" ) > $E/logs/$name.log 2>&1; local rc=$?; local e=$(date +%s.%N)
  printf '%s\t%s\t%.1f\t%s\n' "$name" "$(date -d @${s%.*} -Is)" "$(echo "$e - $s" | bc)" "$rc" >> $TS
  echo "$(date -Is) END $name rc=$rc" >> $E/logs/driver_2.log; }
declare -A M=([1]=E6M_fig8_r1b [2]=E6M_fig8_r2 [3]=E6M_fig8_r3)
if [ "$STAGE" = all ] || [ "$STAGE" = 2a ]; then
  for k in 1 2 3; do m=${M[$k]}; for src in fgo ukf; do
    run 2a_ukf_T_A_r${k}_${src}map /home/makerspace/venv-evo/bin/python src/estimators/room_ukf_replay.py T_A_r$k \
      --tag-map $E/maps/$m/map_$src.json --tag-map-name ${src}map_$m
  done; done
  touch $E/stage2a.done
fi
if [ "$STAGE" = all ] || [ "$STAGE" = 2b ]; then
  for k in 1 2 3; do m=${M[$k]}; for src in fgo ukf; do
    run 2b_fgo_T_A_r${k}_${src}map /home/makerspace/venv-fgo/bin/python src/estimators/fgo/room_fgo_replay.py T_A_r$k \
      --out-root $T1 --tag-map $E/maps/$m/map_$src.json --tag-map-name ${src}map_$m
  done; done
  touch $E/stage2b.done
fi
echo "$(date -Is) DONE $STAGE" >> $E/logs/driver_2.log
