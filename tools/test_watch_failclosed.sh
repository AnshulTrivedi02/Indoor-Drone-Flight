#!/usr/bin/env bash
# Fail-closed safety-watcher tests (ruling 2026-10-08). Lock protocol: waits for BUILD_LOCK to clear, holds FLIGHT_LOCK.
#  T1 H_wtest_noarm: the watcher is deliberately NOT started -> fly_trial must refuse to arm (no take-off).
#  T2 H_wtest_kill : the watcher is SIGKILLed once the vehicle is airborne -> fly_trial must land.
set -u; cd "$(dirname "$0")/.."; source tools/flight_lock.sh
flight_lock_acquire "watcher tests" || exit 1; trap flight_lock_release EXIT
P="$PWD/batches/expH/wtest_profile.json"
echo "=== T1: watcher not started"
H=1 HPROFILE="$P" WATCHER_TEST_SKIP=1 sim/tools/closed_loop_run.sh room_wall_tag H_wtest_noarm
grep -E "REFUSING TO ARM|Armed\.|FAILED" ~/thesis_data/trials/H_wtest_noarm/logs/fly_trial.log
echo "=== T2: watcher killed in flight"
( SECONDS=0; until grep -q "WAIT_FIX ok" ~/thesis_data/trials/H_wtest_kill/logs/fly_trial.log 2>/dev/null || [ $SECONDS -gt 900 ]; do sleep 2; done
  sleep 10; W=$(pgrep -f '[w]all_watch.py.*H_wtest_kill' | head -1); echo "killing watcher pid $W at $(date +%T)"; [ -n "$W" ] && kill -9 "$W" ) &
H=1 HPROFILE="$P" sim/tools/closed_loop_run.sh room_wall_tag H_wtest_kill
wait
grep -E "watcher lost|landing|Landing|Disarmed|FAILED|confirmed before arming" ~/thesis_data/trials/H_wtest_kill/logs/fly_trial.log
