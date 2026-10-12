#!/usr/bin/env bash
# Watcher SITL bench (item 2c; docs/handovers/2026-10-11_watcher_sitl_bench.md). VERIFICATION flights only (wbench_*),
# never result data. One session per call, under FLIGHT_LOCK (waits for BUILD_LOCK first; released on exit).
#   tools/run_wbench.sh <session> [--from TEST] [--prefix P]   sessions: smoke ground hoverA hoverB hoverC
#   (2026-10-12 re-run: output wbench2_<session>_<stamp>; --prefix wbench reproduces the 2026-10-11 naming)
# Separate driver: run_trial.sh / closed_loop_run.sh / fly_trial.py are not modified (fly_trial.py is imported read-only
# by realflight/sitl_bench/flight_script.py for its watcher gate).
set -u
cd "$(dirname "$0")/.."
source tools/flight_lock.sh
S="${1:?session}"
if pgrep -fa '[a]rducopter' >/dev/null; then echo "an arducopter process is already running; refusing" >&2; exit 1; fi
flight_lock_acquire "wbench_$S (watcher SITL bench 2c)" || exit 1
trap flight_lock_release EXIT
"$HOME/venv-ardupilot/bin/python3" -m realflight.sitl_bench.bench "$@"
