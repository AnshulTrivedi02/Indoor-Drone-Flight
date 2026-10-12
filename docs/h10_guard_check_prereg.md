# H10 guard verification flight `h10_guard_check`: PRE-REGISTRATION (2026-10-12)

**Status: PRE-REGISTERED.** Committed BEFORE the flight and before FLIGHT_LOCK is taken. VERIFICATION only (SITL), not
data. Implements METHODOLOGY "RULINGS (user, 2026-10-12, safety first)" item 8 (H10).

## What is tested

`fly_trial.py`'s H10 pilot-takeover guard (this branch), ported from the watcher bench's flight-script layer
(`realflight/sitl_bench/flight_script.py --h10-guard`):
- the script does NOT command LAND when the FC is in a pilot mode (STABILIZE 0, ALT_HOLD 2) or already in LAND (9),
  the FC mode read passively from the FC's own latest HEARTBEAT;
- once the pilot has taken a pilot mode after a LAND (the script's or the watcher's), the script sends no further LAND
  or mode change for the rest of the run (latched) and only watches for the disarm.

**The hazard it removes** (`fly_trial.py` before this change): `land()` sends LAND, then waits 180 s wall-clock for
the disarm. If the pilot has taken ALT_HOLD, the disarm does not come, `land()` raises `TrialFailure`, and the D24
failure path in `main()` calls `land()` again, which re-commands LAND under the pilot. The offline mock test
(`tools/test_fly_trial_h10.py`, `eval/results/h10/mock_test_2026-10-12.json`) shows the old file doing exactly this
(one LAND 180 s after the first) and the new file sending nothing.

## The flight (ONE flight)

- **Harness:** this worktree's `run_trial.sh` with `FLY_TRIAL=<this worktree>/fly_trial.py` (the new one-line override;
  unset = unchanged) and `EXTRA_PARM_FILES=<this worktree>/h10_guard_check.parm` (a DEFAULTS file: FLTMODE_CH 5,
  FLTMODE5 = ALT_HOLD, FLTMODE2 = LAND; never PARAM_SET, so the shared eeprom is not written).
- `--world corridor_textured --altitude 1.5 --velocity 0.4 --duration 5 --trial-name h10_guard_check`. The standard
  dataset configuration otherwise (AHRS_EKF_TYPE 10, the vehicle flies on simulator truth).
- **The pilot** (`tools/h10_pilot.py`, a separate process on SITL SERIAL1 `tcp:127.0.0.1:5762`, system 255 =
  MAV_GCS_SYSID, so RC override is accepted). It never sends a mode command:
  1. waits until the FC has been armed in GUIDED and then shows LAND (the script's LAND after the cruise and stop);
  2. **0.33 s later** (B10b's measured toggle): mode switch (channel 5) to 1685 us (ALT_HOLD), throttle centred
     (1500 us); RC override re-sent at 10 Hz;
  3. holds ALT_HOLD for **200 s** (wall) from the switch move: longer than `land()`'s 180 s wall cap, so the old
     code's re-LAND would fall inside the hold;
  4. mode switch to 1295 us (LAND): the pilot lands; on DISARMED the override is released.
- Run by `tools/run_h10_guard_check.sh` under FLIGHT_LOCK (`tools/flight_lock.sh`); refuses if an arducopter runs.

## Pass criteria (as worded; evidence = the flight's dataflash MODE records, with `Rsn` 1 = RC_COMMAND,
## 2 = GCS_COMMAND, `ModeReason.h`; plus `fly_trial.log` and the pilot log)

1. **The script's LAND:** exactly ONE MODE record LAND with Rsn GCS_COMMAND in the flight, after the cruise.
2. **The takeover:** a MODE record ALT_HOLD with Rsn RC_COMMAND within 1.0 s (wall, pilot log) of the switch move.
3. **No further script command:** from the ALT_HOLD entry until the pilot's LAND switch (at least 180 s later),
   - NO MODE record of any kind;
   - `fly_trial.log` shows NO "Landing" line and no mode command after the takeover, and it DOES show the latch
     ("H10: the pilot took ALT_HOLD after LAND …") and, after `land()`'s cap, the guarded failure path ("H10 guard: the
     pilot took ALT_HOLD -> NOT commanding LAND …").
4. **The pilot's landing:** the next MODE record is LAND with Rsn RC_COMMAND, then DISARMED. No other MODE record
   after the takeover.

PASS = 1–4 all hold. `fly_trial.py` is expected to exit 1 (its `land()` cap expired under pilot control; the trial is
not "complete"). That exit code is not a criterion.

**VOID (reported, not a failure; not re-flown without saying so):** FLTMODE5 ≠ 2 in the flight's PARM dump; the pilot
link never connects or the FC never shows LAND/ALT_HOLD for a reason outside the script (e.g. arming failure, SITL
crash); the vehicle does not take off. If VOID, the cause is reported.

## Reported (no pass/fail)
- the switch-to-ALT_HOLD latency; the hold altitude drift (ALT_HOLD on simulator truth); the total LAND commands the
  script sent; the eeprom md5 before and after (expected to change for unrelated stored counters; reported only).
