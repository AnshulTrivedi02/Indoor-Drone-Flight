# Handover, 2026-10-12: watcher F6 (LAND re-send), real-FC failsafe parameters, B5 re-wording, B8a determination

**Stage:** coding and analysis only (RULINGS 2026-10-12, items 1 and 4). Nothing was flown, run in SITL or re-run.
Stored data were only read (`~/thesis_data/wbench/`). Not edited: METHODOLOGY.md, the 2026-10-11 bench handover.
Branch: the worktree branch, based on `fwd-camera` `4449869`. Not merged.

## 1. F6: the LAND re-send rule (`realflight/watcher/fc_link.py`)

**The old rule** re-sent an un-ACKed LAND every 0.3 s, up to 5 times. Reproduced on the old code: the FC accepts the
LAND, the ACK is lost, and the pilot switches to ALT_HOLD 0.33 s later (B10b's measured toggle). The FC heartbeat runs
at its 1 Hz default. The old watcher sent **5 LANDs and left the FC in LAND**, overriding the pilot. The new watcher
sends **1**.

**The new rule** (in the module docstring). M0 is the FC custom mode in the last HEARTBEAT before the first send.
- **Stop for good** (latched for the episode) when any of these holds:
  - **S1:** a DO_SET_MODE ACK arrives;
  - **S2:** an FC heartbeat after the first send shows LAND;
  - **S3:** a heartbeat shows a **pilot mode** (ArduCopter `is_autopilot() == false`: STABILIZE, ACRO, ALT_HOLD, LOITER,
    DRIFT, SPORT, FLIP, AUTOTUNE, POSHOLD, THROW, FLOWHOLD, SYSTEMID, TURTLE). This applies even when M0 was already that
    mode;
  - **S4:** a heartbeat shows a mode other than LAND and other than M0 (a change the watcher did not command);
  - **S5:** 5 sends have been made.
- **Re-send (R)** only with positive evidence that the last send had no effect. All of these must hold:
  - ≥ `land_retry_s` (0.3 s) since the last send;
  - an FC heartbeat received ≥ `land_evidence_s` (0.2 s, new `--land-evidence-s`) after that send;
  - that heartbeat still shows M0, which must be an autopilot mode (if M0 is unknown: any autopilot mode except LAND).
- **Heartbeat rate:** `request_streams` now also asks for the FC HEARTBEAT at 5 Hz on the watcher's link
  (SET_MESSAGE_INTERVAL; HEARTBEAT is in the FC's interval table, `GCS_Common.cpp:1045`). The evidence therefore
  arrives within about 0.2 s.
- **Residual, stated in the code:**
  - a pre-LAND heartbeat that arrives more than 0.2 s late (link latency) allows one extra re-send. It could re-command
    LAND only if the pilot switched to an AUTOPILOT mode in that window;
  - with no FC heartbeat at all, nothing is re-sent (the FC's GCS failsafe covers that case, B3a).
- **Unchanged:** one LAND decision per episode; the first send; the heartbeat withdrawal; every log line. A LAND
  decided while the pilot is already in ALT_HOLD is still sent once (B10b(2)); it is just never re-sent.

**Tests** (`realflight/watcher/tests/test_fc_link.py`, fake FC on loopback). `FakeFC` gained `hb_period`.
- New tests:
  - `test_f6_pilot_takes_alt_hold_after_an_accepted_land_whose_ack_is_lost_no_further_land` (1 Hz heartbeat): 1 LAND;
  - `test_f6_land_lost_then_pilot_takes_alt_hold_no_further_land`: 1 LAND, stopped by S3;
  - `test_f6_pilot_mode_before_the_breach_still_gets_one_land_but_no_resend`;
  - `test_f6_unacked_land_with_no_mode_change_is_resent_as_before`: 3 sends ≥ 0.29 s apart, then ACK;
  - `test_f6_land_in_heartbeat_without_ack_stops_resending` (S2);
  - `test_f6_other_mode_change_not_commanded_by_the_watcher_stops_resending` (S4, BRAKE);
  - `test_f6_no_resend_without_a_post_send_heartbeat`;
  - `test_f6_heartbeat_rate_is_requested`.
- **One existing test's set-up changed:** `test_g4_land_gives_up_after_max_tries_without_ack`.
  - It used `FakeFC(ack=False)`, where the fake FC still switched to LAND. Under F6 that case now correctly stops after
    one send (it is now its own S2 test).
  - The test now uses an FC that ignores every command, so it still proves the 5-send cap (S5). Its assertion is
    unchanged.
- **Result: `pytest realflight/` → 91 passed** (the 83 earlier tests and the 8 new ones).
- The eight F6 tests fail on the old `fc_link.py`. That is partly API-related (the new attributes). The behavioural
  check is the scripted reproduction above: 5 LANDs on the old code, 1 on the new.
- **Not done: no SITL re-run.** §7.2 requires the watcher bench to be repeated IN FULL "after any change to the
  watcher". The 2026-10-11 SITL results therefore no longer describe the current code.
  - **B7b consequence to expect:** in that bench, the first command's loss on a not-yet-warm `udpin` link was rescued
    by the blind 0.3 s retry. It now waits for an FC heartbeat ≥ 0.2 s after the send. That heartbeat may still come at
    1 Hz if `request_streams` has not run yet. With 12 commands, p99 is effectively the maximum, so one slow retry can
    fail B7b's 0.3 s bound.
  - In real operation this cannot happen: a LAND only follows a confirmation, and confirmation needs FC heartbeats. The
    bench driver should warm the link and call `request_streams` before its first B7b command.
  - A B10b re-run with an injected ACK loss is the natural F6 verification flight.

## 2. Real-FC failsafe parameters

Files, all in `realflight/params/`:
- **`rung1_failsafe_fc.parm`** (new). Every failsafe, fence and landing parameter of rung 1, each with a comment. The
  comments give the @Param file:line and the value range checked in `~/ardupilot` at `7bac20cbcc`, and how the line
  relates to the watcher and the bench tests:
  - EKF origin (see the FLAG below);
  - the GCS failsafe (identical to `watcher_fc.parm`);
  - `FS_EKF_ACTION 1` and `FS_EKF_THRESH 0.8`;
  - `FS_THR_ENABLE 3`, `FS_THR_VALUE 975` and `RC_FS_TIMEOUT 1.0`;
  - the battery failsafes;
  - the altitude-only fence, with `FENCE_OPTIONS 0` so the pilot can retake control;
  - `LAND_SPD_MS 0.5` (the name at this commit; "LAND_SPEED" does not exist), `LAND_ALT_LOW_M 10`,
    `LAND_REPOSITION 1`, `DISARM_DELAY 10` (restoring the bench's 0), `FS_CRASH_CHECK 1` and `ARMING_RUDDER 0`.
- **`ukfonly_failsafe_fc.parm`** (new, fork only). It is loaded after the rung-1 set. It sets:
  - `AHRS_EKF_TYPE 12`, `AHRS_UKF_ENABLE 1`, `AHRS_UKF_TFAIL 0`;
  - EXTYAW/EXTPOS 0 and `AHRS_FGO_ENABLE 0`;
  - `AHRS_OPTIONS 0` (no recorded origin under type 12, which keeps the SITL-tested configuration; the fork's
    `thesis_nav_check` is origin-independent);
  - `FS_EKF_ACTION 1`.
  - The names were verified against the @Param tags on `~/ardupilot_ukf` `board-h743` `0156bfc34e`.
- **`rung1_template.parm`:** its GEOFENCE and FAILSAFES sections were MOVED to the failsafe file with their values
  unchanged. The load order in the header now names four files.
- **`check_parm.py`:**
  - new `--stage3`. It accepts AHRS_EKF_TYPE 12 only in this mode, requires `AHRS_UKF_ENABLE 1` and `AHRS_UKF_TFAIL 0`,
    and adds the five fork names;
  - `AHRS_UKF_TFAIL ≠ 0` is always refused;
  - new FAILSAFE_RULES (FS_GCS_ENABLE 5; FS_OPTIONS bit 4 set and bits 0–2 clear; MAV_GCS_SYSID 1–254;
    MAV_GCS_SYSID_HI 0; MAV_OPTIONS bit 0 clear; FS_EKF_ACTION 1; FS_EKF_THRESH > 0; FS_THR_ENABLE 3; FENCE_TYPE 1;
    FENCE_ACTION 2; FENCE_OPTIONS bit 0 clear; ARMING_RUDDER 0; LAND_REPOSITION 1);
  - the self-test also checks that the failsafe file agrees with `watcher_fc.parm` on the 7 shared names.
- **Results:**
  - `--selftest`: **SELFTEST PASS** (18 checks);
  - rung-1 set (template + nomag + failsafe): **OK (draft; 30 TODO_SUPERVISOR left)**;
  - `--stage3` set: **OK (draft; 30 left)**;
  - `--final` on the rung-1 set: REFUSED, on the placeholders only (as intended).
- **New TODO_SUPERVISOR values:** `AHRS_ORIGIN_LAT/LON/ALT`, `BATT_LOW/CRT_VOLT`, `FENCE_ALT_MAX`, `FENCE_MARGIN`.
- **`FENCE_ALT_MAX`:** its @Range is 10–1000 m, but that range is GCS documentation only. The code accepts any value
  ≥ 0 if ALT_MAX − ALT_MIN > 2·MARGIN (`AC_Fence.cpp:464-476, 568-571`). A GCS may warn when it is written.
- **Docs updated:**
  - `docs/rung1_flight_cards.md`: the `check_parm` line, B1 readback, and B6 (now "fence and EKF origin");
  - `docs/realflight_plan_copter.md`: U-a, U-e and U-j status.
- **FLAG (user/supervisor): the EKF origin** (`AHRS_OPTIONS 16` + `AHRS_ORIGIN_*`). Without an origin, stock
  `Copter::ekf_check()` returns at its first line (`ekf_check.cpp:35-39`). FS_EKF_ACTION is then INERT on a no-GPS
  vehicle (§4).
  - Effects of the recorded origin:
    - it makes the EKF failsafe live;
    - it stops EKF3's reported position from jumping to (0, 0) when aiding is lost (`AP_NavEKF3_Outputs.cpp:287-290`),
      the jump that drove B8a's runaway in GUIDED;
    - home is set at arming;
    - the earth-field table is read at the lab location (compass variant only).
  - No SITL run so far had an origin.
  - In ALT_HOLD it changes nothing (FS_EKF_ACTION 1 makes no mode change there).
  - Rule on adopting it; if it is declined, delete those four lines and accept that B8/EKF-failsafe protection does not
    exist on rung 1.

## 3. B5 re-worded (`docs/real_flights_plan.md` §7.2 B5; ruling 4)

- **New wording:** stale declared within the stale limit plus one watcher loop period, **0.5 s + 0.025 s = 0.525 s**, of
  the last frame; LAND/disarm within **1.0 s** (unchanged). The frozen (no-flag) case gets the same 0.525 s from the first
  frozen frame, plus LAND within 1.0 s.
- **The loop period, stated:** 0.025 s. That is the 0.02 s `select()` timeout plus 5 ms of processing. The bench measured
  `max_loop_gap_s` 0.020–0.024 s in every summary, excluding the deliberate B3b SIGSTOP.
- **The old wording is recorded verbatim** next to the new one, with the reason. The old bound equalled the limit, and
  the rule is "older than", checked once per loop, so it could not be met. No real bench run has happened, so nothing on
  hardware is re-scored.
- The SITL values (0.508 / 0.510 s) meet the new bound. That is a **post hoc** observation; they remain verification
  data only.

## 4. B8a determination: a HARNESS FAULT (test-setup error), with a real mechanism behind the excursion

**Data used:** `wbench_hoverB_20261011_125941`: `dataflash/00000018.BIN`, `mav.tlog`, `bench.log`, `fs04.log`,
`analysis/06_B8a.txt`. The scripts used are in the session scratchpad, not committed.

**Timeline.** F is FC sim time; W−F ≈ 1791683989.36 near the event. Offsets are measured from the SIGKILL of the real
`flow_bridge.py` (process `flow_bridge_real`, not a watched dependency; the correct process) at W 1791684128.686,
≈ F 139.33.

| offset | event |
|---|---|
| +0.06 s | last `OF` row (F 139.383): the flow stops reaching the FC |
| +1.11 s | XKF4 (both cores): **HORIZ_POS_REL lost** (F 140.443). From here `Copter::ekf_has_relative_position()` is false |
| +1.1…+5.0 s | EKF3 dead-reckons inertially; its velocity is ~0, while the true velocity drifts 0.05→0.13 m/s east |
| +5.06 s | "EKF3 IMU0/1 stopped aiding" (F 144.391). AID_NONE, `const_pos_mode` set. **The REPORTED horizontal position jumps from (N 0.47, E 2.99) to (0, 0)** in both cores (XKF1 144.343 → 144.443). Traced cause: `NavEKF3_core::getPosNE` (`AP_NavEKF3_Outputs.cpp:257-291`) in AID_NONE returns the last known position only `if (validOrigin)`; **with no origin it returns `posNE.zero()`** (:287-290). XKF1 (`AP_NavEKF3_Logging.cpp:27`) and the AHRS position the controller uses (`AP_AHRS.cpp:1868-1870`) both read `getPosNE`. EKF3's own state is kept at the last known position (`lastKnownPositionNE`, `AP_NavEKF3_Control.cpp:424-425`); only the no-origin output is zero |
| +5.1…+6.3 s | the position controller absorbs the jump (target 2.99 → 0.00). The flight script then re-sends its GUIDED hold target (N 0.47, E 2.99, in the frame before the jump) at 2 Hz. The reported position stays (0, 0) for as long as AID_NONE lasts, so the error never closes |
| | → the target velocity ramps to 3.29 m/s (TVN/TVE = 0.157 = 0.47/2.99, the direction of the hold point); pitch reaches −19.7° |
| | → true speed 3.58 m/s east (SIM2 E 1.69 → 7.81 m by F 147) |
| +6.32 s | **watcher** BREACH (x = 3.047 > 3.0) → LAND sent; FC MODE LAND (GCS_COMMAND) at +6.35 s. The flight script's WatcherLost LAND follows at +6.55 s (FC already in LAND) |
| +9.5 s | FC GCS failsafe (the watcher's heartbeat had been withdrawn at the breach) |
| +11.7 / +12.2 s | land complete / disarmed, ~10 m from the box after an attitude-only LAND drift |

**Which layer acted:** the watcher's box breach, first, at +6.32 s. The EKF failsafe never acted, and the log has no
EKFCHECK or FAILSAFE_EKFINAV ERR.

**Why no EKF failsafe: the harness fault.**
- The bench's declared set-up (amendment A1) includes an EKF origin via `SET_GPS_GLOBAL_ORIGIN`.
- The operator sent it 3× in the first ~1.5 s after the FC's first heartbeat. That was before "EKF3 IMU0 initialised"
  (log 4.85 s), and EKF3 refuses an origin until `statesInitialised` (`AP_NavEKF3_Control.cpp:692`).
- It was never re-sent, and the harness never checked that it took effect:
  - this boot's dataflash has **no `ORGN` record**;
  - `mav.tlog` has **no `GPS_GLOBAL_ORIGIN`**;
  - `wbench_hoverC` (B10b) also has no `ORGN`.
- Without an origin, `Copter::ekf_check()` returns at its first statement (`ekf_check.cpp:35-39`). The EKF failsafe, the
  path B8 exists to test, was therefore **disabled for the whole session**.

**Would the estimator-invalid path have triggered?** Yes, inferred from source and the logged status; it was not
observed.
- With an origin, `checks_passed` is false once HORIZ_POS_REL is lost (`ekf_check.cpp:51-53`; the variances stayed
  small, so over_threshold played no part). After 10 iterations at 10 Hz (`EKF_CHECK_ITERATIONS_MAX`), about F 141.4,
  i.e. **≈ +2.1 s**, `failsafe_ekf_event()` → GUIDED requires a position → **LAND (EKF_FAILSAFE)**.
- That is about 3 s before the runaway began (+5.06 s) and about 4 s before the breach. The vehicle was then still
  hovering, about 0.1 m/s inside the box.
- So the missing origin changed which layer acted first. By the pre-registered isolation rule ("if the watcher acts
  first, the run is void"), the run was voided by the set-up, not by the system as it would be configured.

**The missing origin ALSO caused the runaway itself:**
- Without an origin, EKF3's `getPosNE` reports (0, 0) in AID_NONE (traced above). The GUIDED hold target, re-sent at
  2 Hz by the flight script, then sat 3.03 m away from a reported position that could not move. The controller flew
  towards it at the navigation speed limit.
- With an origin, `getPosNE` reports the last known position (`AP_NavEKF3_Outputs.cpp:282-285`, no GPS). There is no
  jump, the target error stays near zero, and the vehicle would have hovered on attitude while dead-reckoning drifted.
  This is inferred from source and was not observed.
- The 3.03 m size is simply where the hold point sat in EKF3's frame when the reported position zeroed. EKF3's frame had
  accumulated that offset over the session's earlier hovers, because the harness carried the vehicle back with
  `set_pose` (A7) without resetting EKF3. Any non-zero hold point would run away by its own distance.
- So both halves of B8a, the absent EKF failsafe and the excursion, trace to one set-up fault: no EKF origin.
- **Hardware risk:** a no-GPS vehicle WITHOUT an origin, in a scripted GUIDED hold, losing flow, would do the same. With
  the origin of `rung1_failsafe_fc.parm` it would not jump, and the EKF failsafe would land it. Rung 1 is pilot-flown
  in ALT_HOLD, which does not use the horizontal position. A pilot LOITER or GUIDED profile without an origin is exposed.

**Also affected:**
- **B10b(3)** ("no EKF failsafe in ALT_HOLD") is consistent but vacuous: the EKF failsafe never ran.
- The B8a pre-registered expectation ("EKF3 raises NO failsafe", from SITL `H_safety_ekf3_ref`) encodes the same
  artefact: **`~/thesis_data/trials/H_safety_ekf3_ref/ardupilot.bin` has no `ORGN` record either** (checked). Its "no
  failsafe" result is what stock ArduCopter does WITHOUT an origin.

**Recommendation (the user decides; nothing re-run):**
- Ruling 4 allows a repeat because this is a harness fault. Repeat B8a once, as a short SITL verification flight, with:
  - (1) the origin established and **verified** before arming (`ORGN` in the log / a `GPS_GLOBAL_ORIGIN` received), set
    either by sending it after EKF3 initialises or, better, with `AHRS_OPTIONS 16` + `AHRS_ORIGIN_*` as in
    `rung1_failsafe_fc.parm`, which tests the real-FC configuration;
  - (2) everything else as the first run (`iris_textured`, the same box, the same hover profile).
- Expected with the origin (from source):
  - no position jump at "stopped aiding";
  - an EKF failsafe LAND (reason EKF_FAILSAFE) about 1 s after HORIZ_POS_REL is lost, i.e. about +2 s after the kill,
    well before any breach.
- First re-register B8a's expected outcome, since the old one came from a no-origin run (it is report-only).
- Consider re-running `H_safety_ekf3_ref` with an origin too.

## 5. Open items for the next stage

- Rulings:
  - the EKF origin FLAG (§2);
  - the B8a repeat and its expected outcome (§4);
  - whether the F6 rule needs a SITL B10b re-run with an injected ACK loss before the board bench;
  - the watcher system ID (U-k; 211 is a placeholder in both files).
- The real flight script (H10/U-f) needs the same pilot-mode guard as the bench driver. F6 covers only the watcher.
- The TODO_SUPERVISOR values in `rung1_failsafe_fc.parm`.

## 6. Files

- Changed: `realflight/watcher/fc_link.py`, `realflight/watcher/mocap_watch.py`, `realflight/watcher/tests/fakes.py`,
  `realflight/watcher/tests/test_fc_link.py`, `realflight/params/check_parm.py`, `realflight/params/rung1_template.parm`,
  `docs/real_flights_plan.md` (§7.2 B5), `docs/rung1_flight_cards.md`, `docs/realflight_plan_copter.md`.
- New: `realflight/params/rung1_failsafe_fc.parm`, `realflight/params/ukfonly_failsafe_fc.parm`, this handover.
