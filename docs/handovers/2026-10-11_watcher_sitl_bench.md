# Handover, 2026-10-11: mocap watcher bench B0–B10 in SITL with a simulated mocap feed (item 2c)

**Stage:** VERIFICATION flights only (STANDING RULE 2026-10-10). They are never result data. Trials are named
`wbench_*`. The watcher under test is the REAL-HARDWARE watcher (`realflight/watcher/`), not `sim/tools/wall_watch.py`.
Not edited: METHODOLOGY.md, numbers.md, run_trial.sh, sim/tools/closed_loop_run.sh, fly_trial.py (it is imported,
read-only, for its watcher gate functions).

## 1. PRE-REGISTRATION (written and committed BEFORE any SITL session, including the smoke session)

Source: `docs/real_flights_plan.md` §7.2 (B0–B10, pre-registered 2026-10-10). The bench in §7.2 is props-off and
landed; here the vehicle hovers in SITL, so "LAND or disarm" is read as "the FC enters LAND (or disarms)". Any change
after this commit is added as a dated AMENDMENT below; no criterion is edited after data are seen.

### 1.1 Setup (fixed before running)

- **Simulator:** stock `~/ardupilot` `7bac20cbcc` SITL (ArduCopter), Gazebo Harmonic, `iris_with_ardupilot` (vendored
  `sim/models`, time sync on), world **`iris_runway`**. Why: flat and open with no walls, so a deliberate box breach or a
  dead-reckoning drift cannot hit geometry; the room worlds have walls 4.4 m from the centre and an AprilTag ExtNav
  stack that rung 1 does not fly.
- **Estimator, as rung 1 flies:** EKF3 (`AHRS_EKF_TYPE 3`), no GPS (`GPS1_TYPE 0`, `SIM_GPS1_ENABLE 0`), horizontal
  velocity from SITL's own optical-flow sensor (`FLOW_TYPE 10`, `SIM_FLOW_ENABLE 1`, `EK3_SRC1_VELXY 5`,
  `EK3_SRC1_POSXY 0`), height from the SITL rangefinder (`EK3_SRC1_POSZ 2`), compass yaw. Fallback if this stack
  cannot arm in GUIDED or hover in the smoke session: an EKF origin via `SET_GPS_GLOBAL_ORIGIN`; failing that GPS-EKF3
  for the watcher-path tests and the flow stack only for B8 (recorded as an amendment).
- **FC failsafe parameters:** `realflight/params/watcher_fc.parm` loaded UNCHANGED as an extra `--defaults` file
  (`FS_GCS_ENABLE 5`, `FS_GCS_TIMEOUT 3`, `MAV_GCS_SYSID 211`, `MAV_GCS_SYSID_HI 0`, `FS_OPTIONS 16`, `MAV_OPTIONS 0`,
  `ARMING_RUDDER 0`, `ARMING_SKIPCHK 0`), plus a bench file: `FS_EKF_ACTION 1`, `FS_THR_ENABLE 3` (rung-1 template),
  `LOG_DISARMED 1`, `LOG_REPLAY 1`, mode switch on channel 5 (GUIDED / ALT_HOLD / STABILIZE / LAND positions), and
  `DISARM_DELAY 0` for the GROUND session only (as §7.2). SITL runs in its OWN working directory
  (`~/thesis_data/wbench/sitl_cwd`), with its eeprom wiped at every session start, so no bench parameter can leak into
  the shared `~/ardupilot/ArduCopter/eeprom.bin` of the thesis flights.
- **Processes (ground station roles):**
  - the watcher, `python3 -m realflight.watcher.mocap_watch`, `--sysid 211`, on SITL SERIAL1 through a UDP relay
    (the "telemetry link", which can be cut), `--box=-3,3,-3,3,-0.5,3.0` (watch frame = Gazebo ENU, origin at the
    spawn), `--body-name thesis_quad`, two dependencies, `--dep-loss land` unless stated;
  - MAVProxy on SERIAL0 as the ordinary GCS (system ID 255, sends its own 1 Hz HEARTBEAT; NOT started with `--sitl`);
  - the flight script: a separate process that uses `fly_trial.py`'s own `watch_ok` / `require_watcher_before_arming`
    / `check_watcher_in_flight` / `WatcherLost` with `WATCH_HEARTBEAT` = the watcher's file (`WATCH_STALE_S` 3 s),
    connected through MAVProxy like `fly_trial.py`;
  - the bench operator (injector and recorder) on SITL SERIAL2, and the RC "transmitter" = raw PWM packets to SITL's
    RC UDP port 5501;
  - the simulated mocap forwarder: `/ground_truth/pose` → MCP1 UDP packets (body `thesis_quad`, ID 1, tracked flag,
    frame counter, `t_mocap` = the ground-station wall clock at receipt of the pose), with injectable faults: stop,
    freeze (tracked 1 or −1), untracked (0), wrong body name/ID, a static other body under the right name, frame-counter
    reset, added latency;
  - dependencies: `flow_tracker` = a stub with an in-process `LivenessBeacon` and a progress counter; `flow_bridge` = a
    stub process watched by the real `proc` sidecar (`realflight/watcher/sidecars.py`).
- **Deviation D1 (identity):** the G3 identity proof is a HAND motion before arming. SITL has no hand, and arming
  through the stock gap just to prove it would defeat the test. The PRIMARY watcher therefore runs `--identity off`
  for every test. The motion-identity logic is exercised in B6b by a SECOND watcher instance (system ID 212, its own
  SITL serial port, a large box, `--fc-params off`), observing while the vehicle hovers under the primary.
- **Hover profile (every hover test):** arm via the flight-script gate, take off to 1.5 m at (0, 0), hold ≥ 10 s sim,
  inject, observe until disarmed. **Why this length suffices:** the 10 s hold gives a settled hover and a confirmed
  watcher with a steady heartbeat; every bound tested is ≤ 4 s after the injection; the landing from 1.5 m takes about
  10 s. About 40–60 s sim per hover. Ground tests need no take-off at all (arming refusal / acceptance only).
- **Clocks:** W = the ground-station wall clock (the watcher, the flight script and every injection). F = the FC clock
  (SITL sim time: dataflash `TimeUS`, `SYSTEM_TIME.time_boot_ms`; it runs at the RTF, ~0.9). Map: the operator logs
  `SYSTEM_TIME` (requested at 10 Hz) with its W receipt time; around each event, a linear fit over ±10 s of the lower
  envelope of (W − F) per 1 s bin gives W ↔ F. FC events (MODE, ARM/DISARM, ERR) are taken from the dataflash and
  mapped to W.
  - **FC-timer bounds** (B2b, B3a: the GCS-failsafe 3.5 s) are evaluated on **F** (the injection instant mapped to F).
  - **Watcher / flight-script bounds** (B2a, B3b, B4b, B5a, B5b, B9a–c, B10a, B7b) are evaluated on **W**.
  - Every interval is reported on both clocks.

### 1.2 Tests and pass criteria (as worded in §7.2, adapted to a hover where stated)

| test | SITL setup | PASS (pre-registered) |
|---|---|---|
| **B0** | Ground. Watcher running (D1), deps alive. Flight script requests arming in GUIDED. | Script logs "Safety watcher confirmed before arming" AND the FC arms within 60 s; no other pre-arm failure. Recorded: the watcher's MAVLink heartbeat count from system ID 211. |
| **B1a** | Ground. Watcher NOT started. Flight script requests arming. | Script logs "REFUSING TO ARM: no watcher heartbeat" AND no ARM event in the dataflash. |
| **B1b** | Ground. Watcher running, `flow_tracker` stub stopped. Flight script requests arming. | "REFUSING TO ARM: watcher not confirming (… bridge=0)" AND no ARM event. |
| **B1c** (G6) | Ground, watcher never started in this boot. (i) `ARMING_RUDDER` 2 (stock default): stick arm in STABILIZE via the RC model (throttle low, yaw right, 3 s). (ii) `ARMING_RUDDER` 0: same stick arm. (iii) a NON-force MAVLink arm from system ID 255. (iv) force-arm (param2 2989). | As §7.2: the FC REFUSES. The known finding predicts (i) ARMS → recorded as a FAIL of the stock FC side (expected); (ii) must NOT arm (PASS of mitigation (i)); (iii) predicted to ARM (recorded: mitigation (i) is procedural only); (iv) predicted to ARM (recorded). |
| **B1-native** | Ground. Watcher started, confirmed, then SIGKILLed while disarmed; wait ≥ 4 s F; non-force MAVLink arm. Then restart the watcher. | The arm is refused with a GCS-failsafe pre-arm message; after the restart and re-confirmation, "GCS Failsafe Cleared" and the flight script can arm. |
| **B1c-Lua** (G6 ii) | Ground. `watcher_arming_auth.lua` in SITL's `scripts/`, `SCR_ENABLE` 1, reboot; watcher with `--lua-auth`. (a) watcher never started: non-force MAVLink arm, and a stick arm with `ARMING_RUDDER` 2; (b) watcher confirmed: flight-script arm; (c) watcher SIGKILLed, wait ≥ 4 s F: non-force arm; (d) watcher never seen (after a reboot): force-arm. | (a) both REFUSED with the script's "Watcher: never seen"; (b) ARMS; (c) REFUSED; (d) predicted to ARM (bypass, recorded). (a) and (b) together are required for a PASS: a script that always fails would pass (a) alone. |
| **B2a** | Hover. SIGKILL the watcher (flight script alive). | LAND (or disarm) within **4.0 s W** of the kill. The layer that acted first is reported. |
| **B2b** (G5, G11) | Hover. SIGKILL the flight script (vehicle stays armed and holds), then SIGKILL the watcher; MAVProxy (255) keeps running. | FC GCS failsafe (ERR FAILSAFE_GCS, mode LAND) within **3.5 s F** of the watcher kill. |
| **B3a** | Hover. Drop all traffic on the watcher's link (both directions) at the relay; watcher running. | FC GCS failsafe within **3.5 s F** of the cut. (Expected also: the watcher withdraws on "FC link lost" without a LAND.) |
| **B3b** | Hover. SIGSTOP the watcher; SIGCONT 1 s after LAND is seen. | LAND/disarm within **4.0 s W** of the SIGSTOP, AND after SIGCONT: no LAND or mode command from the watcher, no mode change other than the landing, no re-arm (10 s observed after disarm). |
| **B4b** (side face) | Hover. Flight script moves the hold point north at 0.5 m/s across y = 3 m. | Watcher logs BREACH within **0.1 s W** of the first mocap pose outside (its own track) AND LAND within **1.0 s W** of that pose; exactly ONE LAND decision. |
| **B4b-top** (G10) | Hover. Flight script climbs at 0.5 m/s through z = 3.0 m. | As B4b. |
| **B5a** | Hover. Forwarder stops sending. | Stale declared within **0.5 s W** of the last frame (watcher log) AND LAND within **1.0 s W** of the last frame; heartbeat stopped; confirmation withdrawn. |
| **B5b** | Hover. (1) freeze with tracked = 1 for 3 s; (2) tracked = 0 (untracked) from then on. | (1) no action (frozen with a tracking flag stays fresh, by design: an OBSERVATION, not a pass item); (2) treated as stale: LAND within **1.0 s W** of the first untracked frame. |
| **B5b-noflag** | Hover with the forwarder in "no tracking flag" mode (tracked = −1) throughout; freeze (bit-identical poses) in the hover. | Stale (frozen) declared within 0.5 s of the freeze start AND LAND within **1.0 s W** of the freeze start. States which case applies: the frozen fallback. |
| **B5c** | Ground, disarmed. Confirmed watcher; stop the stream 3 s; restore. | Confirmation returns only after ≥ **2.0 s** of continuous fresh poses; no automatic action follows the restore. |
| **B6a** (stream level) | Ground. Forwarder sends body `other_body` (ID 2) only; flight script requests arming. | No confirmation (wrong_bodies counted), so arming refused. |
| **B6b** (motion identity, D1) | Hover under the primary watcher. Observer watcher (system ID 212, `--identity require`). Manoeuvre: a commanded roll of 12° held 0.8 s, then a 90° yaw. Run 1: the observer gets the right body. Run 2: the observer gets a STATIC other body under the right name. | Run 1: observer identity CONFIRMED. Run 2: observer identity FAILED and never confirmed. |
| **B7a** | All hover sessions: the watcher track's `t_rx_wall − t_mocap`. | median ≤ 50 ms, p99 ≤ 100 ms — on the FORWARDER → WATCHER path only (the true exposure latency is hardware-only). Plus an OBSERVATION: 150 ms added latency is logged and NOT acted on (staleness uses receipt time). |
| **B7b** | Ground, disarmed: ≥ 10 LAND commands with the watcher's own `FcLink` (system ID 213), each followed by a GUIDED reset; plus every in-flight LAND of B4/B5/B9. | Command send → FC MODE event: **p99 ≤ 0.3 s W** over ≥ 10 commands. |
| **B8a** | Hover, EKF3. Aiding loss: `SIM_FLOW_ENABLE 0` (the flow sensor stops). Watcher heartbeat and deps untouched; 20 s observed, then flow restored and landed. | Report-only (§7.2). Expected from `H_safety_ekf3_ref`: EKF3 raises NO failsafe and keeps a dead-reckoned position. If the watcher or the flight script acts first, the run is VOID. |
| **B9a** | Hover, `--dep-loss land`. SIGKILL (1) the `flow_tracker` stub (in-process beacon), (2) the `flow_bridge` stub (proc sidecar). One hover each. | Watcher withdraws within **1.5 s W** of the kill and stops its heartbeat AND LAND within **2.5 s W** of the kill. |
| **B9b** | Hover, `--dep-loss stop`. SIGKILL the `flow_tracker` stub. | As B9a (stop must mean LAND, G8). |
| **B9c** | Hover. SIGSTOP (1) the `flow_tracker` stub, (2) the `flow_bridge` stub. | Detected and handled as B9a (same bounds). |
| **B9-hang** (observation) | Hover. The `flow_tracker` stub keeps beaconing but freezes its progress counter. | No pre-registered bound (§7.2 gives none); expected: withdrawal ~2 s (progress timeout) + tick, then LAND. |
| **B9d** | = B1b. | As B1b. |
| **B10a** | Hover in GUIDED. RC mode switch to ALT_HOLD; later STABILIZE briefly, then ALT_HOLD. | FC mode changes within **0.3 s W** of the RC change, AND the flight script's GUIDED setpoints have no effect afterwards (no mode change back; vehicle holds). |
| **B10b** | Hover in ALT_HOLD (pilot). In turn: (1) watcher SIGKILL; (2) a NEW watcher confirms, then dependency loss (SIGKILL `flow_tracker`); (3) aiding loss (`SIM_FLOW_ENABLE 0`). | GCS failsafe and EKF failsafe make NO mode change; the watcher and the flight script send at most ONE LAND (latched); if that LAND is accepted, the pilot regains ALT_HOLD by one switch move within 1 s, and nothing re-commands LAND afterwards (10 s observed). The flight script used carries an H10 guard (no LAND when the FC is in a pilot mode or already in LAND), labelled an H10 PROTOTYPE; the log also states whether `fly_trial.py`'s as-is `WatcherLost` path would have commanded LAND. |
| **B10c** | Ground, armed (GUIDED, `DISARM_DELAY` 0). `SIM_RC_FAIL 1` (no pulses). | The configured `FS_THR_ENABLE` 3 action: disarm on the ground (a MODEL of a receiver failsafe only). |
| obs. | Frame-counter reset (in a hover); wrong body ID mid-hover. | Observations: reset → no effect expected; wrong ID mid-hover → the samples are ignored, so stale → LAND within 1.0 s W expected. |

### 1.3 Hardware only (not exercisable meaningfully in SITL), with the reason

- **B4a** (carrying through each face, disarmed) and **B4c** (a 60° hand tilt): SITL can only fake these by injecting
  poses into the forwarder; the in-flight B4b side and top faces exercise the same code path with real motion.
- **B4d** box geometry against real hold points and the capture volume.
- **B6 hand procedure** (hand roll/pitch 10°, hand yaw 90° before arming), see D1.
- **B7a true latency** (mocap exposure → watcher, chrony/PTP); in SITL `t_mocap` is the forwarder's wall clock.
- **B7c** mocap ↔ FC alignment: needs a real mocap clock and hand-rotation sync wiggles before arming and after
  disarming.
- **B8b/B8c** (UKF / FGO ports): rung 1 flies EKF3; the port paths are item 2d (`H_safety_*` re-tests).
- **B10c real receiver failsafe** semantics; SITL's `SIM_RC_FAIL` is a model only.
- The audible alert, the Lua script on the real board, beacons wired into the Pi processes, and the real telemetry
  radio's failure modes.

### 1.4 Amendments

(none yet)

## 2. Results

(to be filled in after the runs)
