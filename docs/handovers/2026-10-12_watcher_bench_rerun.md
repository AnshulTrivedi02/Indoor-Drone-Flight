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
- **A10 (2026-10-12, ~11:58, after the hoverB re-run `wbench2_hoverB_20261012_114206` and hoverC; before the run it
  governs). The incomplete-stimulus rule (general, applies to every test of this stage). LABELLED POST HOC: it was
  written after the incomplete B6b attempt had been seen.**
  - **Rule:** a test whose stimulus is never applied, because an event outside the test's own mechanism happened
    first, is NOT COMPLETED. It is repeated ONCE, and both attempts are reported. If the repeat is also cut short,
    the test is reported "not completed" and nothing more is run.
  - **Where it applies:** B6b run 1 (right body) in the hoverB re-run.
    - A 1.9 m take-off excursion east happened first. Before arming, EKF3's velocity on the ground had diverged
      (VE 1.0–1.8 m/s while the vehicle sat still); see F8 below.
    - The 12° roll then crossed the east face at x = 3.007 m. The primary watcher's BREACH and LAND followed.
    - So the 90° yaw half of the manoeuvre was never flown. The observer's verdict was "unproven (roll/pitch proven,
      yaw not proven)".
    - It is reported as worded (criterion "identity CONFIRMED" not met, manoeuvre incomplete) and repeated.
  - **Where it does not apply:** no other wbench2 test meets the definition. Every other injection was applied as
    registered.
  - **How the repeat runs:** `tools/run_wbench.sh hoverB --only B6b_right_body` (new driver option `--only`). This
    gives a fresh SITL boot, so the repeat is the FIRST hover after boot, whereas the first attempt followed
    B5b-noflag and a carry. That difference is stated, not corrected for.

## 2. Results

**Sessions** (all under `~/thesis_data/wbench/`; verification data only, never result data). The numbers come from
`python3 -m realflight.sitl_bench.results <session>` (saved as `<session>/analysis/results.txt`) and from `analyse`
(merged per-test timelines in `<session>/analysis/`).
- W is the wall clock; F is the FC clock.
- The F↔W map residual is a few tens of ms, so mapped FC events are good to about ±0.04 s.

Every session logs the HEAD of the code it ran in `bench.log` (R5): e4fc256 (ground, hoverA, the aborted hoverB),
ac5fada (the hoverB re-run, hoverC) and 8d384fc (the B6b repeat). None had uncommitted changes under `realflight/`.
`realflight/watcher/` is identical in all three to `fwd-camera` `140a946`.

| session | content |
|---|---|
| `wbench2_ground_20261012_111140` | B1a, B1c (i)–(iv), B0, B1b/B9d, B5c, B6a, B1-native, B7b, F6c, B10c, B4a (5 faces), B4c, B1c-Lua (2 reboots) |
| `wbench2_hoverA_20261012_112139` | B2a, B2b, B3a, B3b, B4b side, B4b top, B5a, B5b, observations |
| `wbench2_hoverB_20261012_112751` | **ABORTED (A9)**, not used for any criterion: B5b-noflag and B6b run 1 flew; B6b run 2 flew away on take-off; B8a and B9a never reached their injections. Stopped with SIGINT, which ran the teardown |
| `wbench2_hoverB_20261012_114206` | the re-run in full (A9): B5b-noflag, B6b ×2, **B8a**, B9a ×2, B9b, B9c ×2, B9-hang |
| `wbench2_hoverC_20261012_114843` | B10a, B10b, **F6a**, **F6b** |
| `wbench2_hoverB_20261012_115531` | the B6b run 1 repeat (A10, `--only B6b_right_body`) |

**Origin (R1), every boot:**
- The gate opened when both cores (IMU0, IMU1) reported initialised.
- A `GPS_GLOBAL_ORIGIN` with the coordinates sent came back 4–7 ms after the first send. One try in every boot: 6 initial
  boots and the 2 Lua reboots.
- Every session's dataflash has `ORGN` records from F ≈ 4.8 s, before any test.

**A9 check (EKF yaw minus true yaw at arming), every counted hover:** −0.9° … +3.2°, so all are within ±5° and valid.

**Take-off lateral excursion (observation, F8):** 0.06–0.57 m in every counted hover, except the first B6b run 1
attempt (2.08 m).

**R2 check (an EKF failsafe before a test's own criterion event voids that test), all counted sessions.** ERR
EKFCHECK and ERR FAILSAFE_EKFINAV appear in B8a and B10b (3) (+31.5 s and +49.2 s), as registered. They also appear in
five other places, every one AFTER that test's criterion event, so **no test is voided**:
- B4b side: +4.66 s after the BREACH;
- B5b: +4.24 s after the first untracked frame;
- B5b-noflag: +4.9 s after the frozen declaration;
- B9-hang: +10.7 s after its LAND.
  In each of these four the vehicle was already descending in LAND, and `HORIZ_POS_REL` was lost near the ground. LAND
  does not need a position, so no mode change followed.
- ground: after the B4c tilt carry, disarmed (`failsafe_ekf_event` takes no action when disarmed).

The only EKF-failsafe mode change in the whole re-run is B8a's LAND.

### 2.1 Summary

- **PASS (as worded):** B0, B1a, B1b/B9d, B1c (ii), B1-native, B1c-Lua, B2a, B2b, B3a, B3b, B4a (5 faces), B4b side,
  B4b top, B4c, B5a (re-worded), B5b, B5b-noflag (re-worded), B5c, B6a, B6b run 2.
- **PASS, continued:**
  - B6b run 1: PASS on a repeat under A10, LABELLED POST HOC (the rule was written after the incomplete attempt was
    seen). The first attempt was NOT COMPLETED.
  - B7a: on the forwarder path only.
  - **B7b**, with the registered warm-up.
  - **B8a**, repeated with an origin.
  - B9a ×2, B9b, B9c ×2, B10a.
  - **B10b (1)–(3)**: (3) is now non-vacuous.
  - B10c: a model only.
  - **F6a, F6b, F6c.**
- **Recorded as predicted (stock FC side):**
  - B1c (i) ARMS by stick at `ARMING_RUDDER 2`;
  - B1c (iii) ARMS by a non-force MAVLink arm;
  - B1c (iv) ARMS by force.
- **FAIL as worded:** none.
- **Not completed:** the first attempt of B6b run 1 (A10, reported below). Its criterion was not met as worded.

### 2.2 Per test

**B0 — PASS.** "Safety watcher confirmed before arming: watcher ok (age 0.7 s)", then "Armed.". No pre-arm failure.

**B1a — PASS.** "REFUSING TO ARM: no watcher heartbeat"; no ARM.
**B1b (= B9d) — PASS.** "REFUSING TO ARM: watcher not confirming (box=0 bridge=0)"; no ARM.

**B1c**, stock firmware, watcher never started in the boot:
- (i) `ARMING_RUDDER 2` stick arm: ARMED, as predicted (a FAIL of the stock FC side);
- (ii) `ARMING_RUDDER 0`: did not arm, **PASS**;
- (iii) non-force MAVLink arm: ARMED (ACK 0), as predicted;
- (iv) force: ARMED, as predicted.

**B1-native — PASS.**
- After the watcher's SIGKILL, a non-force arm was DENIED (ACK 4), with the only message "Arm: GCS failsafe on".
- After the restart, "GCS Failsafe Cleared" came at +3.28 s, and the flight script armed.

**B1c-Lua — PASS.** 45 s settle after each reboot; each reboot's origin was re-gated and verified.
- (a) The MAVLink arm and the `ARMING_RUDDER 2` stick arm were both REFUSED with "Arm: Watcher: never seen".
- (b) The flight script ARMED.
- (c) After the SIGKILL and 6 s: REFUSED ("Arm: GCS failsafe on", "Arm: Watcher: heartbeat 5.9s old").
- (d) Force after a reboot: ARMED (bypass, as predicted).

**B2a — PASS.**
- MODE LAND (GCS_FAILSAFE) came +3.029 s W after the kill, inside the 4.0 s bound.
- The first layer to act was the FC's GCS failsafe. The flight script's LAND followed at +3.24 s.

**B2b — PASS.**
- The flight script was SIGKILLed 2.0 s before the watcher.
- ERR FAILSAFE_GCS and MODE LAND (GCS_FAILSAFE) came at **+3.044 s F**, inside the 3.5 s bound.

**B3a — PASS.**
- After the relay cut, FAILSAFE_GCS and MODE LAND came at **+2.328 s F**, inside the 3.5 s bound.
- The watcher withdrew on "FC link lost" at +2.90 s W and sent **0 LAND**.
- The flight script's WatcherLost came at +3.75 s.

**B3b — PASS.**
- After the SIGSTOP, MODE LAND (GCS_FAILSAFE) came at **+2.988 s W**, inside the 4.0 s bound.
- The SIGCONT came 1 s after LAND was seen.
- Afterwards:
  - the watcher logged "stalled: own loop gap 4.03 s … no LAND sent";
  - it sent 0 LAND;
  - there was no MODE or ARM event in the 10 s after the disarm (at +12.15 s);
  - the watcher re-confirmed 2.12 s after the disarm.

**B4a — PASS (all five faces).**
- On each face, the BREACH came on the first pose outside (+0.000/+0.001 s, inside the 0.1 s bound).
- The confirmation was withdrawn, ONE LAND was sent and ACKed on its first send, and the FC mode became LAND.
- After the north face, the flight script's arming attempt was "REFUSING TO ARM: watcher not confirming".

**B4c — PASS.** "BREACH: tilt 65.0 deg > 60.0"; one LAND, ACKed; FC LAND.

**B4b side — PASS.** First pose outside (−0.127, 3.007, 1.623).
- The BREACH came +0.000 s after it, and the FC MODE LAND at **+0.024 s W**.
- There was ONE LAND decision and one send.

**B4b top — PASS.** First pose outside (0.007, 0.060, 3.009).
- The BREACH came +0.000 s after it, and MODE LAND at **+0.007 s W**.
- There was one LAND.

**B5a (re-worded) — PASS.**
- "mocap pose stale (0.51 s > 0.5 s)" came at **+0.513 s** after the last frame, inside the 0.525 s bound.
- MODE LAND came at **+0.557 s W**, inside the 1.0 s bound.
- The confirmation was withdrawn at +0.513 s. The MAVLink heartbeat stopped and resumed only after the disarm plus 2 s.

**B5b — PASS.**
- (1) Frozen with tracked = 1 for 3 s: no watcher event and no mode change (an observation).
- (2) Untracked: the BREACH came on the first untracked frame, and MODE LAND at **+0.053 s W**, inside the 1.0 s bound.
  The heartbeat stopped.

**B5b-noflag (re-worded) — PASS.** The case is the frozen fallback.
- "mocap pose frozen (bit-identical for 0.51 s, no tracked flag)" came at **+0.510 s** after the first frozen frame,
  inside the 0.525 s bound.
- MODE LAND came at **+0.550 s W**, inside the 1.0 s bound.

**B5c — PASS.**
- The first fresh frame came 0.003 s after the restore. The watcher's "confirmation 1" came **2.011 s** after it,
  which meets the ≥ 2.0 s requirement.
- No LAND or mode command followed the restore. The next LAND in the log is B6a's.

**B6a — PASS.** With the body `other_body`/ID 2 only, there was no confirmation, and arming was refused.

**B6b (observer, system ID 212):**
- **run 2 (a static other body) — PASS:** `identity=failed (roll/pitch disagree by 11.9 deg > 5.0 for 0.5 s)`; it never
  confirmed (0 heartbeats).
- **run 1, first attempt — NOT COMPLETED (A10); criterion not met as worded:**
  - `identity=unproven (roll/pitch proven, yaw not proven)`.
  - The vehicle had drifted 1.9 m east on take-off (F8), so the 12° roll crossed the east face (x = 3.007 m).
  - The primary watcher's BREACH and LAND followed, and the yaw was never flown.
- **run 1, repeat (A10, fresh boot, the first hover after it) — PASS:**
  - `identity=confirmed (proven (roll/pitch and yaw change agree))`;
  - the maximum roll/pitch difference was 1.00°.

**B7a — PASS on the forwarder → watcher path only.**
- n = 52,156 poses across the 4 counted hover sessions. The 2026-10-11 exclusions applied: the +150 ms window and the
  B3b SIGSTOP backlog.
- Median **0.10 ms**, p99 **0.50 ms**, maximum 7 ms.
- **Observation:** +150 ms of added latency was logged (median 0.152 s) and not acted on.

**B7b — PASS.**
- **Warm-up as registered:**
  - the first FC heartbeat arrived 0.17 s after the link opened;
  - `request_streams()` was then called;
  - ≥ 3 heartbeats arrived within 1 s;
  - the warm-up took 0.99 s in total;
  - the FC heartbeat rate on the link was then 4.81 Hz.
- **The 12 commands:**
  - each was sent from GUIDED (M0 = 4), after a heartbeat showing GUIDED;
  - send → MODE LAND: median **0.008 s**, **p99 0.027 s** (bound 0.3 s), maximum 0.028 s;
  - all 12 were ACKed on the first send (S1), so none needed a re-send.
- **In-flight watcher LANDs (B4b, B5, B9, F6a/b):** send → MODE LAND took 0.002–0.065 s.

**B8a (repeated with a verified origin) — PASS.**
- **Preconditions:**
  - (p1) the origin was verified at set-up, and `ORGN` records are in this boot from F 4.83 s (the kill was at
    F 140.18);
  - (p2) `HORIZ_POS_REL` was true throughout the 3 s before the kill.
- **Reference R:** the last `OF` row was at F 140.175, 0.004 s before the kill as mapped. `HORIZ_POS_REL` was lost
  1.036 s after R.
- (a) At **+1.936 s F** after R: ERR EKFCHECK (2), ERR FAILSAFE_EKFINAV (1), and MODE LAND reason **EKF_FAILSAFE**,
  with "EKF variance: position lost" and "EKF Failsafe: changed to Land Mode". This is inside the 3.0 s bound, and
  slightly before the 2.0–2.1 s expectation (the 1 s flow timeout plus 10 checks; the bound is unchanged).
- (b) It was the FIRST protective action. Nothing else acted at all: no watcher BREACH or LAND, no flight-script LAND
  or WatcherLost, and no FAILSAFE_GCS.
- (c) **Excursion:** the maximum true horizontal distance from the position at the kill was **1.673 m**, inside the
  2.0 m bound. This is a smaller margin than the arithmetic predicted: the drift (dx +1.05, dy −1.30 m) came over the
  ~11 s to the disarm. The maximum |x| was 1.06 m and the maximum |y| 1.31 m; there was no box BREACH. The landing
  disarmed by itself (land complete at +10.4 s); no operator disarm was needed.
- **Observations:**
  - "EKF3 IMU0/IMU1 stopped aiding" occurred after the LAND;
  - XKF1 (core 0) shows **no reported-position jump** (> 0.3 m between rows), as expected with an origin;
  - the failsafe cleared (ERR 16/17 code 0) after the flow was restored.
- Compared with the void first run (no origin): there the EKF failsafe never ran, the reported position jumped to (0, 0)
  and the vehicle ran away at 3.6 m/s.

**B9a — PASS** (`--dep-loss land`).
- **`flow_tracker` stub kill:** the withdrawal came at **+0.867 s** (bound 1.5 s) and MODE LAND at **+0.931 s W**
  (bound 2.5 s).
- **`flow_bridge` stub kill (sidecar):** the withdrawal came at +0.944 s, and MODE LAND at +0.996 s.
- The heartbeat stopped at detection. Any heartbeat after the injection came before detection, within the 1 s beacon
  timeout.

**B9b — PASS.** `--dep-loss stop` was mapped to LAND (G8). The withdrawal came at +0.946 s, and MODE LAND at +0.998 s.

**B9c — PASS.**
- SIGSTOP of the `flow_tracker` stub: the withdrawal came at +0.949 s, and MODE LAND at +0.995 s.
- SIGSTOP of the `flow_bridge` stub: the withdrawal came at +0.942 s, and MODE LAND at +0.997 s.

**B9-hang (observation).** "no progress for 2.00 s (hung)" at +1.912 s; MODE LAND at +1.94 s.

**B10a — PASS.** Each RC switch move reached the FC with reason RC_COMMAND, all inside the 0.3 s bound:
- ALT_HOLD +0.219 s;
- STABILIZE +0.204 s;
- ALT_HOLD +0.211 s;
- LAND +0.281 s.

Between ALT_HOLD and the LAND switch there were only the three RC mode events, although GUIDED targets were still being
sent.

**B10b — PASS (with the H10 prototype guard), (3) now non-vacuous.** In ALT_HOLD:
- (1) Watcher SIGKILL: "GCS Failsafe - Continuing Pilot Control", with no mode change. The H10 guard logged "FC in
  ALT_HOLD → NOT commanding LAND (fly_trial.py as-is WOULD command LAND here)".
- (2) A new watcher confirmed, followed by a dependency loss:
  - its ONE LAND came at +19.234 s, ACKed on the first send (S1);
  - the pilot's switch move came at +19.566 s, and ALT_HOLD at +19.765 s, 0.199 s later (bound 1 s);
  - nothing re-commanded LAND until the pilot's own LAND switch at +49.84 s.
- (3) Aiding loss: ERR FAILSAFE_EKFINAV and "EKF Failsafe" came at +31.489 s, 1.92 s after the kill. **No mode change
  followed.**
- **Observation:** a second "EKF Failsafe" came at +49.197 s, 2.9 s after it cleared (+46.256 s) and 4.6 s after the
  flow bridge restart. There was no mode change; the pilot's LAND switch came 0.37 s later. The cause was not
  investigated.
- **Caveat, unchanged:** `fly_trial.py` as-is would command LAND in (1).

**B10c (model) — PASS.** `SIM_RC_FAIL 1`, armed on the ground: "Radio Failsafe - Disarming", with the disarm
+1.07 s W after it.

**F6a (in flight, LAND ACKed) — PASS.**
- The flight script was killed 2.2 s before the dependency kill.
- (1) There was ONE watcher LAND send from the injection to the disarm.
- (2) MODE LAND (GCS_COMMAND) came +0.002 s after it.
- (3) The switch move led to ALT_HOLD (RC_COMMAND) at +0.218 s.
- (4) There was **no FC mode change** in the 9.78 s from ALT_HOLD to the pilot's LAND switch.
- Stop reason: S1 (ACK).
- The GCS failsafe then said "Continuing Pilot Control".

**F6b (in flight, LAND UNACKNOWLEDGED) — PASS; valid.**
- **Validity:**
  - the relay stripped the COMMAND_ACK for command 176 sent 3 ms after the LAND;
  - the watcher logged no "LAND ACK";
  - the relay held 5 FC heartbeats in the 0.6 s (4 showing LAND, 1 showing ALT_HOLD).
- (1) There was ONE send.
- (2) MODE LAND came +0.006 s after it.
- (3) ALT_HOLD came +0.209 s after the switch move.
- (4) There was no FC mode change in the 9.79 s to the LAND switch.
- **Stop reason: S3.** "FC heartbeat shows the pilot mode ALT_HOLD": the first heartbeat after the hold, 0.72 s after
  the send.
- Under the old rule, the watcher would have re-sent blind at +0.3 s and +0.6 s; the second of those would have come
  after the pilot's switch.

**F6c (ground, lost command) — PASS; valid.**
- The relay dropped exactly one watcher DO_SET_MODE(LAND), the first send.
- That drop is the primary evidence that nothing from send 1 reached the FC. It is backed by the dataflash: the only
  MODE LAND is at +0.007 s after send 2, against a W↔F residual of about ±0.04 s.
- **Exactly 2 sends.** Send 2 came **0.311 s** after send 1 (window 0.30–0.60 s), on an evidence heartbeat showing
  GUIDED.
- MODE LAND (GCS_COMMAND) came within 0.3 s of send 2.
- The ACK stopped the re-sending (S1); there was no third send.

**Observation: the FC heartbeat on the watcher's link.** Intervals were 0.15–0.3 s for 78–91 % of heartbeats in each
session (≈ 5 Hz, the F6 request). The longer intervals are before the first request in a boot, and during the B3a
link cut.

### 2.3 Findings (not watcher bugs)

- **F7 (n = 1; caused by the harness, amendment A9).** A Gazebo carry that rotated the vehicle by a yaw the gyros
  never saw left EKF3's yaw 77° off the truth.
  - The compass corrected it at ~1.4°/s.
  - The FC passed its arming checks at a 22° yaw error.
  - The vehicle then flew away west at ~6 m/s on take-off. The link to the yaw error is inferred, not proven.
  - The watcher's box caught it at x = −3.02 m (BREACH, LAND, ACK in 3 ms).
  - For hardware: a real carry is sensed by the gyros, so this exact cause cannot occur. The general point stands:
    the stock pre-arm checks allowed arming with a large EKF yaw error, and on a flow-only vehicle a yaw error means a
    flyaway.
- **F8 (n = 1; cause not established).** Before the first B6b run 1 attempt, EKF3's velocity on the ground diverged
  while the vehicle sat still: VE 1.0–1.8 m/s, and PE ran from 2.9 to 10.3 m. The FC still armed.
  - At take-off the estimate reset (PE 10.3 → 4.35 m).
  - The position controller then moved the vehicle 1.9 m east to the old target.
  - It is not attributed to the origin or to A9; every other counted hover had a take-off excursion of 0.06–0.57 m.
  - For hardware: no pre-arm check looks at the EKF's velocity on the ground. The safety pilot should watch for a
    take-off lurch, and the box is the backstop.
- **F2 (as before).** The land detector did not trip after some LANDs on flow-only EKF3. There were 3 operator disarms
  in the counted sessions, each after 4 s on the ground in LAND, under amendment A7b.

### 2.4 Watcher changes

**None.** `realflight/watcher/` was not modified in this stage:
`git diff 140a946 f877884 --stat -- realflight/watcher/ realflight/mcp1.py realflight/params/` prints nothing. The
offline result from the start of the stage therefore stands: `pytest realflight/` → **91 passed**.

## 3. Harness fix (the B8a origin-timing fault)

`bench.py establish_origin`:
- it waits until every EKF3 core in `EK3_IMU_MASK` has reported "EKF3 IMUn initialised" in the current boot;
- it then sends `SET_GPS_GLOBAL_ORIGIN` and asks for `GPS_GLOBAL_ORIGIN` (MAV_CMD_REQUEST_MESSAGE 49);
- it accepts the origin only on a received `GPS_GLOBAL_ORIGIN` with the coordinates sent;
- it retries at ~1 Hz, up to 30 times, and otherwise ABORTS the session;
- it runs at set-up and after every reboot.

`results.py` prints the dataflash `ORGN` records per session. Result: verified at the first try in all 8 boots.

## 4. Files

- **Changed:** `realflight/sitl_bench/bench.py`, `stack.py`, `udp_link.py`, `results.py` and `analyse.py`;
  `tools/run_wbench.sh`.
- **New:** this handover.
- **Not modified:** `realflight/watcher/`, METHODOLOGY.md, run_trial.sh, sim/tools/closed_loop_run.sh and fly_trial.py.
- **SITL ran in its own working directory** (`~/thesis_data/wbench/sitl_cwd`, eeprom wiped per session), so the shared
  `~/ardupilot/ArduCopter/eeprom.bin` was never written.
- **Data:** `~/thesis_data/wbench/wbench2_*` and `run2_*.out`. Nothing was deleted.

## 5. Open (for the user / the next stage)

- **H10 (unchanged):** the real flight script needs the B10b pilot-mode guard. `fly_trial.py` as-is would command
  LAND in B10b (1).
  - F6a/F6b isolated the watcher by killing the flight script, because in GUIDED its WatcherLost LAND would race the
    pilot's switch.
- **The EKF-origin SAFETY decision (handover 2026-10-12 §2) is still the user's.** With an origin, B8a shows the stock
  EKF failsafe landing the vehicle 1.94 s after the flow stopped, before anything else acted.
- **F7/F8:** for the rung-1 safety procedure. The safety pilot watches for a take-off lurch, and the box is the
  backstop.
- **The second EKF failsafe after the flow restore** (B10b observation): not investigated.
