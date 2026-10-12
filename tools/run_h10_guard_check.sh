#!/usr/bin/env bash
# H10 verification flight h10_guard_check (pre-registered: docs/h10_guard_check_prereg.md). VERIFICATION only. ONE
# flight under FLIGHT_LOCK (waits for BUILD_LOCK first; released on exit). Runs THIS worktree's run_trial.sh with
# FLY_TRIAL = this worktree's fly_trial.py and the defaults file h10_guard_check.parm, and the scripted pilot
# tools/h10_pilot.py in the background (its own link, SITL SERIAL1 tcp 5762).
set -u
W="$(cd "$(dirname "$0")/.." && pwd)"
cd "$W"
source tools/flight_lock.sh
OUT="$HOME/thesis_data/trials/h10_guard_check"
if pgrep -fa '[a]rducopter' >/dev/null; then echo "an arducopter process is already running; refusing" >&2; exit 1; fi
if [ -e "$OUT" ]; then echo "$OUT exists; refusing" >&2; exit 1; fi
flight_lock_acquire "h10_guard_check (H10 guard verification flight)" || exit 1
PILOT_PID=""
finish() { [ -n "$PILOT_PID" ] && kill "$PILOT_PID" 2>/dev/null; flight_lock_release; }
trap finish EXIT
S="$HOME/thesis_data/h10_guard_check_side"; mkdir -p "$S"
md5sum "$HOME/ardupilot/ArduCopter/eeprom.bin" > "$S/eeprom_md5_before.txt" 2>&1
date -Is > "$S/t_start.txt"
timeout 1800 "$HOME/venv-ardupilot/bin/python3" tools/h10_pilot.py --hold-s 200 --cap-s 1700 > "$S/h10_pilot.log" 2>&1 &
PILOT_PID=$!
FLY_TRIAL="$W/fly_trial.py" EXTRA_PARM_FILES="$W/h10_guard_check.parm" timeout 2400 ./run_trial.sh \
    --world corridor_textured --altitude 1.5 --velocity 0.4 --duration 5 --trial-name h10_guard_check \
    > "$S/run_trial.log" 2>&1
RC=$?
echo "run_trial rc=$RC" >> "$S/run_trial.log"
# the pilot exits by itself on DISARMED (or its own caps); wait for it, bounded
for _ in $(seq 1 60); do kill -0 "$PILOT_PID" 2>/dev/null || break; sleep 2; done
md5sum "$HOME/ardupilot/ArduCopter/eeprom.bin" > "$S/eeprom_md5_after.txt" 2>&1
# run_trial copies the dataflash log only on success; copy the newest .BIN written since the start in any case
BIN=$(find "$HOME/ardupilot/ArduCopter/logs" -maxdepth 1 -name "*.BIN" -newer "$S/t_start.txt" -printf "%T@ %p\n" | sort -n | tail -1 | cut -d' ' -f2-)
[ -n "$BIN" ] && cp "$BIN" "$S/ardupilot.bin" && echo "copied $BIN" >> "$S/run_trial.log"
echo "DONE rc=$RC"
