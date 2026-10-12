# Handover, 2026-10-12: watcher bench B0–B10 RE-RUN in SITL after F6 (`wbench2_*`)

**Stage:** VERIFICATION flights only (STANDING RULE 2026-10-10: short, never result data). §7.2 of
`docs/real_flights_plan.md` requires the FULL bench to be repeated after any watcher change; F6 changed
`realflight/watcher/fc_link.py`. The watcher under test is the real-hardware watcher (`realflight/watcher/`) at the
commit that adds this pre-registration (unchanged from `fwd-camera` `140a946`: `pytest realflight/` → **91 passed** at
the start of this stage). Driver: `realflight/sitl_bench/` + `tools/run_wbench.sh`, with the harness changes in §1.1.
Not edited: METHODOLOGY.md, run_trial.sh, sim/tools/closed_loop_run.sh, fly_trial.py, `realflight/watcher/`.

## 1. RE-REGISTRATION (written and committed BEFORE any SITL session of this stage)

Base: the 2026-10-11 pre-registration (`docs/handovers/2026-10-11_watcher_sitl_bench.md` §1.1–§1.4, amendments A1–A8)
applies UNCHANGED except where this section says otherwise. Any change after this commit is added as a dated amendment
in §1.5; no criterion is edited after data are seen.

### 1.1 Set-up changes (harness only; the watcher is not changed)

- **R1 — A1 FIXED (the B8a harness fault, handover 2026-10-12 §4).** The EKF origin (`SET_GPS_GLOBAL_ORIGIN`, the same
  CMAC coordinates as before: −35.3632610, 149.1652300, 584 m) is sent only AFTER every EKF3 core in `EK3_IMU_MASK` has
  reported "EKF3 IMUn initialised" in that boot (STATUSTEXT on the operator link, or in MAVProxy's console log), and is
  then VERIFIED: a `GPS_GLOBAL_ORIGIN` from the FC received after the send (also requested with
  `MAV_CMD_REQUEST_MESSAGE` 49), with the lat/lon sent. Retried at ~1 Hz, up to 30 tries; **without a verified origin
  the session aborts before any test.** The same gate and verification run after every reboot (the Lua block). After
  each session the dataflash `ORGN` record is checked (`results.py` prints it). (`bench.py establish_origin`.)
- **R2 — consequence: the stock EKF failsafe is now LIVE in every session** (`ekf_check.cpp:35-39` no longer returns at
  once). Any GUIDED hover in which `HORIZ_POS_REL` is false for ≥ 1 s now produces an EKF-failsafe LAND
  (`FS_EKF_ACTION 1`). If that happens in a test other than B8a BEFORE that test's own criterion event, the test is
  VOID and repeated once (recorded as an amendment).
- **R3 — sessions.** `ground` (B1a, B1c(i–iv), B0, B1b/B9d, B5c, B6a, B1-native, B7b, **F6c**, B10c, B4a/B4c (A8),
  B1c-Lua with the 45 s post-reboot settle that the 2026-10-11 Lua re-run needed), `hoverA` (B2a, B2b, B3a, B3b,
  B4b side, B4b top, B5a, B5b, observations), `hoverB` (B5b-noflag, B6b ×2, **B8a**, B9a ×2, B9b, B9c ×2, B9-hang),
  `hoverC` (B10a, B10b, **F6a**, **F6b**). One simulation at a time, each under FLIGHT_LOCK, nothing heavy in
  parallel. `bench.py --from TEST` is used ONLY to resume an aborted session (each use recorded in §1.5).
- **R4 — relay (the watcher's simulated telemetry link, `udp_link.py`).** It now parses every MAVLink frame (v1/v2; SITL
  can pack several per datagram) and can (a) strip COMMAND_ACK frames FC → watcher (`ack_strip on|off`), (b) hold FC
  HEARTBEAT frames FC → watcher for S s after the next watcher DO_SET_MODE(LAND) frame (`hb_hold S`), (c) drop the next
  watcher DO_SET_MODE(LAND) frame once (`drop_land_once`). Every removed frame is logged; every FC heartbeat arrival on
  the watcher link is logged (`relay_fc_hb.csv`), which measures whether the watcher's 5 Hz HEARTBEAT request works.
- **R5 — provenance.** Every session's `bench.log` records the repository HEAD and any uncommitted change under
  `realflight/`. Output directories: `~/thesis_data/wbench/wbench2_<session>_<stamp>`.

### 1.2 Pass criteria

**Unchanged from 2026-10-11 §1.2, verbatim:** B0, B1a, B1b, B1c (i)–(iv) (same predictions), B1-native, B1c-Lua,
B2a, B2b, B3a, B3b, B4a (A8), B4b side, B4b top, B4c (A8), B5b (2), B5c, B6a, B6b, B7a, B9a, B9b, B9c, B9-hang
(observation), B9d, B10a, B10b (1)–(2), B10c, and the observations (frame-counter reset; wrong body ID mid-hover).

**Changed or new rows:**

| test | set-up | PASS (registered here, before any run) |
|---|---|---|
| **B5a** (re-worded, §7.2 B5 ruling 4) | as 2026-10-11 | Stale declared within **0.525 s W** of the last frame (0.5 s limit + one 0.025 s loop period), AND LAND within **1.0 s W** of the last frame; MAVLink heartbeat stopped; confirmation withdrawn. |
| **B5b-noflag** (re-worded) | as 2026-10-11 (A6) | Frozen declared within **0.525 s W** of the first frozen frame AND LAND within **1.0 s W** of it. States the case: the frozen fallback. |
| **B7b** (warm-up stated) | Ground, disarmed, watcher stopped; 12 LAND commands from the watcher's own `FcLink` (system ID 213) on the watcher's link, each after a GUIDED reset. **Warm-up, before command 0:** the link must have received ≥ 1 FC HEARTBEAT (a `udpin` link cannot send before it knows its peer); then `request_streams()` is called; then ≥ 3 FC heartbeats must arrive within 1 s (the 5 Hz request took effect); the warm-up time is recorded. **During the 12 commands** the link is polled continuously and `request_streams()` is re-called every 2 s, exactly as the watcher's own loop does (`mocap_watch.py`); command i is sent only after a heartbeat received after its GUIDED reset shows GUIDED (so M0 = GUIDED, as in real operation, where a LAND always follows a confirmation that needs FC heartbeats). Timing starts at the send. | Command send → FC MODE LAND: **p99 ≤ 0.3 s W** over the 12 commands (as 2026-10-11). Plus every in-flight watcher LAND (B4b, B5, B9, F6a/b) reported. If the warm-up fails, B7b is NOT RUN (reported). |
| **B8a** (REPEATED, harness fault; expected outcome RE-REGISTERED) | As the first run: `hoverB`, `iris_textured`, the same ±3 m box, hover profile take-off 1.5 m / hold 10 s / hold 35 s / land, GUIDED; `flow_bridge.py` (not a watched dependency) SIGKILLed 1 s after the hold start; watcher heartbeat and dependencies untouched; flow restored after 20 s. **With the origin set and verified (R1).** | **Preconditions** (otherwise NOT VALID, repeated once): (p1) a verified `GPS_GLOBAL_ORIGIN` at set-up AND an `ORGN` record in this boot's dataflash before the kill; (p2) `HORIZ_POS_REL` (XKF4 core 0) true throughout the 3 s before the kill (`has_ever_passed`). **Reference R** = the last dataflash `OF` row (F clock). **Expected from source:** `HORIZ_POS_REL` lost ~1.0 s after R (`flowDataValid` 1 s timeout, `AP_NavEKF3_OptFlowFusion.cpp:40`, `AP_NavEKF3_Control.cpp:783,803`); `ekf_check` then fails 10 iterations at 10 Hz → **≈ +2.0–2.1 s after R**: ERR FAILSAFE_EKFINAV, "EKF Failsafe: changed to LAND Mode", MODE LAND reason **EKF_FAILSAFE** (`set_mode_land_with_pause`: a 4 s altitude hold, then an attitude-only (no-position) descent). **PASS requires all of:** (a) MODE LAND with reason EKF_FAILSAFE within **3.0 s F of R** (expected 2.0–2.1 s; 0.9 s margin for the 10 Hz check phase and the flow-timeout evaluation); (b) it is the FIRST protective action: before it there is no watcher BREACH or LAND command, no flight-script LAND or WatcherLost, and no FAILSAFE_GCS (if any of these comes first, the run is VOID, as the isolation rule says); (c) **excursion:** the true horizontal distance (Gazebo ground truth) from the vehicle's position at the kill stays **≤ 2.0 m until the disarm**, and the watcher logs NO box BREACH before the disarm. Arithmetic for (c): ≈ 2.1 s to the trigger + 4.0 s pause + ≈ 3 s descent from 1.5 m at `LAND_SPD_MS` (default 0.5 m/s) + ≈ 1 s land detection ≈ 10 s after the kill; at the first run's measured true drift before the runaway (0.05–0.13 m/s) that is 0.5–1.3 m; 2.0 m leaves ~50 % margin. **Observations (not pass items):** no reported-position jump at "stopped aiding" (XKF1 core 0, consecutive rows > 0.3 m apart) — expected none, since with an origin `getPosNE` returns the last known position (`AP_NavEKF3_Outputs.cpp:282-285`); whether "stopped aiding" occurs before touchdown at all. |
| **B10b (3)** (expectation re-registered) | as 2026-10-11 (ALT_HOLD, `flow_bridge.py` SIGKILL, 15 s) | Now non-vacuous (an origin exists). PASS: ERR FAILSAFE_EKFINAV (or "EKF Failsafe") **appears** AND NO mode change follows (`FS_EKF_ACTION 1`; ALT_HOLD does not require a position, `ekf_check.cpp:190`). If no EKF failsafe is logged, (3) is reported "not exercised", not PASS. |
| **F6a** (NEW, in flight, LAND ACKed) | Standard hover in GUIDED. The flight script is SIGKILLed 2.0 s before the injection (as B2b), so the watcher is the ONLY process that can command LAND (`fly_trial.py`'s as-is WatcherLost LAND in GUIDED is the open H10 item, not F6). Throttle stick centred (1500). Injection: SIGKILL of the `flow_tracker` stub (dependency loss, `--dep-loss land`) → the watcher's ONE LAND. The pilot (SITL RC input on UDP 5501, the bench's transmitter model; not MAVLink RC override, which MAV_GCS_SYSID 211 would ignore) moves the mode switch to ALT_HOLD **0.33 s after the watcher's send** (B10b's measured toggle), observes 10 s, then lands with the LAND switch position. | (1) exactly **ONE** watcher LAND send from the injection to the disarm; (2) FC MODE LAND (GCS_COMMAND) within 1.0 s W of the send; (3) FC MODE ALT_HOLD (RC_COMMAND) within 0.3 s W of the switch move; (4) **NO FC mode change** in the 10 s after ALT_HOLD (until the pilot's LAND switch). Recorded: the watcher's stop reason (expected S1, ACK). |
| **F6b** (NEW, in flight, LAND UNACKNOWLEDGED) | As F6a, plus: the relay strips every COMMAND_ACK FC → watcher (`ack_strip on`) and holds FC HEARTBEATs to the watcher for **0.6 s** after the watcher's LAND frame (`hb_hold 0.6`), so the pilot's ALT_HOLD (at +0.33 s) reaches the FC before any heartbeat showing LAND reaches the watcher: exactly F6's scenario (under the OLD rule the watcher would have re-sent LAND blind at +0.3 s and +0.6 s, the second after the pilot's switch). | (1)–(4) as F6a. **Validity** (otherwise VOID, repeated once): the relay logged ≥ 1 stripped COMMAND_ACK for command 176 after the send, the watcher logged NO "LAND ACK", and the relay held ≥ 1 FC heartbeat. Recorded: the stop reason (expected S3, pilot mode ALT_HOLD). |
| **F6c** (NEW, ground, lost command → re-send) | Ground, disarmed, GUIDED, watcher confirmed. The relay drops the watcher's FIRST DO_SET_MODE(LAND) frame (`drop_land_once`); FC heartbeats keep flowing. Injection: SIGKILL of the `flow_tracker` stub. | Exactly **2** sends; send 2 at **0.30–0.60 s W** after send 1 (rule R: ≥ 0.3 s and an evidence heartbeat ≥ 0.2 s after the send; at 5 Hz the evidence arrives by ~0.4 s); NO FC MODE LAND between send 1 and send 2; FC MODE LAND within **0.3 s W** of send 2; re-sending then stops (S1 or S2) with no third send. Validity: the relay logged exactly one dropped DO_SET_MODE(LAND). |

**Observation (all sessions):** the FC heartbeat rate on the watcher's link (`relay_fc_hb.csv`) while a watcher runs:
expected ≈ 5 Hz (the F6 request), not the 1 Hz default.

### 1.3 Why each profile's length suffices (STANDING RULE 2026-10-10)

- Repeated tests use the 2026-10-11 profiles and justifications (§1.1 there and §2 "Why each non-standard profile's
  length suffices"): the standard hover (take-off 1.5 m, 10 s hold, inject, observe to the disarm; ~40–60 s sim) covers
  every bound (≤ 4 s after the injection) plus the landing.
- **B8a:** the first run's profile, unchanged, because ruling 4 repeats it as the first run (only the origin differs).
  The EKF failsafe is expected at ~+2 s; the 20 s flow-loss window only bounds the wait and covers EKF3's 5 s aiding
  timeout ("stopped aiding") as an observation.
- **F6a/F6b:** the standard hover; the watcher's LAND comes ~1 s after the injection, the pilot's switch 0.33 s after
  it; the 10 s observation is the B10b "nothing re-commands LAND" window; the pilot then lands (~10 s).
- **F6c:** ground only; the re-send rule acts within 0.6 s of the first send; 6 s observed.

### 1.4 Hardware only

Unchanged from 2026-10-11 §3: B4d, the B6 hand procedure, B7a true latency, B7c, B8b/B8c, the real B10c receiver
failsafe, the Lua script on the real board, beacons inside the Pi processes, the audible alert.

### 1.5 Amendments (dated, after this commit)

- **A9 (2026-10-12, ~11:45, after `wbench2_hoverB_20261012_112751` was stopped; before any further run). Harness
  only; no criterion changes.**
  - **What happened.** After B6b's 90° yaw manoeuvre the landed vehicle was "carried home" by Gazebo `set_pose`, which
    ALSO rotated it back to the spawn heading. The FC's gyros never saw that rotation. From the dataflash (ATT vs SIM):
    EKF3's yaw was 77° off the truth after the teleport, and the compass corrected it at ~1.4°/s. The FC armed (the
    "Check mag field" pre-arm passed below 100) at a 22° yaw error. On take-off the vehicle flew away west at ~6 m/s.
    The watcher's box caught it at x = −3.02 m (BREACH and LAND in the same millisecond, ACKed on the first send).
    Every later hover in that session then started with a large yaw error, and the vehicle crashed (roll ~180°). B8a
    and B9a never reached their injection ("NOT_RUN"). The session was stopped with SIGINT, which runs the driver's
    teardown.
  - **Why it did not show on 2026-10-11:** not established. The only set-up difference is the origin (R1). With an
    origin, EKF3 and the arming checks use the earth-field table at the location.
  - **Fix (A9).** `Stack.carry_home` now keeps the vehicle's CURRENT heading (levelled, yaw read from Gazebo), so the
    carry contains no rotation the FC cannot sense. A real carry is sensed by the gyros, so this matches the hardware
    better.
  - **New validity check (all hover tests, A9):** EKF yaw minus true yaw at the ARM event (dataflash ATT − SIM). A
    hover with |diff| > 5° at arming is VOID.
    - Already flown, from `results.py`: hoverA, all 9 hovers within ±1.5° (valid).
    - The aborted hoverB: B5b-noflag −0.0° and B6b right body −0.1° (valid, but superseded by the full re-run).
  - **hoverB is re-run IN FULL** (all 10 hovers) with A9. The stopped session is kept on disk and is not used for any
    criterion.
  - **A finding for the safety case, not a watcher issue (F7).** Stock EKF3 on flow can pass its arming checks with
    a ~22° yaw error, and then fly away on take-off. Here the box caught it.

## 2. Results

(to be filled after the runs)
