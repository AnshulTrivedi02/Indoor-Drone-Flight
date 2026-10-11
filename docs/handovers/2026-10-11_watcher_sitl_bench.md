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
| **B8a** | Hover, EKF3. Aiding loss (amendment A5): SIGKILL `flow_bridge.py` (the flow stops reaching the FC). Watcher heartbeat and deps untouched; 20 s observed, then flow restored and landed. | Report-only (§7.2). Expected from `H_safety_ekf3_ref`: EKF3 raises NO failsafe and keeps a dead-reckoned position. If the watcher or the flight script acts first, the run is VOID. |
| **B9a** | Hover, `--dep-loss land`. SIGKILL (1) the `flow_tracker` stub (in-process beacon), (2) the `flow_bridge` stub (proc sidecar). One hover each. | Watcher withdraws within **1.5 s W** of the kill and stops its heartbeat AND LAND within **2.5 s W** of the kill. |
| **B9b** | Hover, `--dep-loss stop`. SIGKILL the `flow_tracker` stub. | As B9a (stop must mean LAND, G8). |
| **B9c** | Hover. SIGSTOP (1) the `flow_tracker` stub, (2) the `flow_bridge` stub. | Detected and handled as B9a (same bounds). |
| **B9-hang** (observation) | Hover. The `flow_tracker` stub keeps beaconing but freezes its progress counter. | No pre-registered bound (§7.2 gives none); expected: withdrawal ~2 s (progress timeout) + tick, then LAND. |
| **B9d** | = B1b. | As B1b. |
| **B10a** | Hover in GUIDED. RC mode switch to ALT_HOLD; later STABILIZE briefly, then ALT_HOLD. | FC mode changes within **0.3 s W** of the RC change, AND the flight script's GUIDED setpoints have no effect afterwards (no mode change back; vehicle holds). |
| **B10b** | Hover in ALT_HOLD (pilot). In turn: (1) watcher SIGKILL; (2) a NEW watcher confirms, then dependency loss (SIGKILL `flow_tracker`); (3) aiding loss (A5: SIGKILL `flow_bridge.py`). | GCS failsafe and EKF failsafe make NO mode change; the watcher and the flight script send at most ONE LAND (latched); if that LAND is accepted, the pilot regains ALT_HOLD by one switch move within 1 s, and nothing re-commands LAND afterwards (10 s observed). The flight script used carries an H10 guard (no LAND when the FC is in a pilot mode or already in LAND), labelled an H10 PROTOTYPE; the log also states whether `fly_trial.py`'s as-is `WatcherLost` path would have commanded LAND. |
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

All five come from the SMOKE session (`wbench_smoke`, a plumbing check: arm through the gate, 15 s hover, land), before
any B-test was run. None changes a pass criterion; they change the vehicle set-up so it can hover as rung 1 would.

- **A1 — EKF origin.** EKF3 on flow had no position estimate pre-arm ("Arm: Need Position Estimate"). The operator sends
  `SET_GPS_GLOBAL_ORIGIN` once at start-up (the pre-registered fallback 1; normal for a non-GPS ArduPilot vehicle).
- **A2/A4 — rangefinder: the Gazebo LiDAR, not SITL's analog sonar.** The SITL analog rangefinder read 0.0 m on the
  ground and up to ~1.3 m, then ~1.4 m short of the truth, so EKF3 had no pre-arm position and took off to 3.7 m true
  (a box-top breach that the watcher caught: BREACH + LAND in the same millisecond, GCS failsafe 2.7 s later). Replaced by
  the thesis stack's verified rangefinder: the Gazebo `gpu_lidar` → `lidar_bridge.py` → MAVLink `DISTANCE_SENSOR`
  (`lidar_rangefinder.parm`; 0.075 m at rest, RNGFND1_MIN 0.05, as a real downward rangefinder reads at rest).
- **A3 — climb rate 0.5 m/s** (`WPNAV_SPEED_UP`, `PILOT_SPEED_UP` 50) and `PLND_ENABLED 0` (gazebo-iris.parm's
  precision landing, no IR-LOCK here). Not a criterion change.
- **A5 — flow: the thesis camera-flow path, world `iris_textured`.** SITL's own flow sensor (`FLOW_TYPE 10`) drifted
  ~0.25 m/s in the hover (3 m in 12 s; SITL's height above ground is offset with this JSON model, see A4, and SIM_FLOW
  scales by it). Replaced by the verified camera path (downward camera → `flow_tracker` → `flow_bridge.py` →
  `OPTICAL_FLOW`, `flow_ekf.parm`, `FLOW_POS_Z 0.25`) over the 20 × 20 m textured mat of **`iris_textured`** (no walls;
  the ±3 m box lies inside the mat). Hover drift in the smoke run: x −0.06…+0.08 m, y −0.00…+0.04 m.
  - Consequence for B8a: the aiding loss is now "stop the flow bridge" (`flow_bridge.py`, SIGKILL), exactly as §7.2 B8(a)
    words it, instead of `SIM_FLOW_ENABLE 0`. `flow_bridge.py` is NOT a watched dependency (the stubs are), so B8's
    isolation holds. For B10b(3) the same.
  - The takeoff overshoots to ~2.4 m true before the 1.5 m hold (box top 3.0 m).

**Amendments made DURING the runs** (each after a run had stopped; no criterion changed):
- **A6 — B5b-noflag set-up.** With `tracked = −1` from the start, the vehicle at rest gives bit-identical Gazebo poses,
  so the frozen fallback never let the watcher confirm (`wbench_hoverB_…125723`, session stopped; fail-closed, see
  finding F3). The source now switches to "no tracking flag" once airborne, holds 3 s (moving poses), then freezes.
- **A7 — harness only.** (a) Before each hover the landed, DISARMED vehicle is put back at the spawn point with Gazebo
  `set_pose` (the bench analogue of carrying it back). Needed because after B4b_side it had landed at y = 3.34 m,
  outside the box, and the watcher (correctly) stayed latched; and after B9b it tipped over (finding F2). (b) If the
  vehicle sits on the ground in LAND, still armed, the operator disarms it (as the safety pilot would): first after
  15 s, then after 4 s (finding F2). Every such disarm is logged ("OPERATOR DISARM") and is AFTER the criterion's event.
- **Harness fix while a session ran (disclosed against the standing "no edits during a batch" rule):** the flight
  script's mode-name mapping (finding F4) was fixed in `flight_script.py` at ~12:50:30 while `hoverA2` was starting; the
  first flight-script process of that session was spawned after the edit (12:50:35), so every hoverA2 flight used the
  fixed script. hoverA (B2a–B3b) used the old one; there, its only effect was a mis-mapped "GUIDED" re-assert (mode 15,
  refused) while the FC was already in GUIDED; its LAND mapped correctly (B3a, mode 9 at the WatcherLost instant).

## 2. Results

**Sessions** (all under `~/thesis_data/wbench/`; verification data only, never result data). Every number below is
produced by `python3 -m realflight.sitl_bench.results <session>` (intervals) and `analyse` (merged per-test timelines in
`<session>/analysis/`). W = wall clock, F = FC clock (SITL sim time; RTF ≈ 0.93–0.99 here). The F↔W map residual is a
few tens of ms (one operator mode command was mapped 33 ms before its own send), so W/F intervals are good to ±0.04 s.

| session | content |
|---|---|
| `wbench_smoke_20261011_122220` | plumbing (amendments A1–A5) |
| `wbench_ground_20261011_122619` | B1a, B1c(i–iv), B0, B1b, B5c, B6a, B1-native, B7b, B10c, B1c-Lua (confounded, see below) |
| `wbench_lua_20261011_123502` | B1c-Lua re-run (45 s settle after each reboot) |
| `wbench_hoverA_20261011_123756` | B2a, B2b, B3a, B3b; B4b_side attempt 1 (stopped: finding F2) |
| `wbench_hoverA2_20261011_125023` | B4b_side (then stopped: landed outside the box) |
| `wbench_hoverA3_20261011_125342` | B4b_top, B5a, B5b, observations (latency, frame reset, wrong ID) |
| `wbench_hoverB_20261011_125723` | B5b-noflag attempt 1 (never confirmed at rest; A6) |
| `wbench_hoverB_20261011_125941` | B5b-noflag, B6b ×2, B8a, B9a ×2, B9b (then stopped: tip-over, F2) |
| `wbench_hoverB2_20261011_130644` | B9c ×2, B9-hang |
| `wbench_hoverC_20261011_130923` | B10a, B10b |

### 2.1 Per test (result as worded against §1.2)

**B0 — PASS.** Ground. "Safety watcher confirmed before arming: watcher ok (age 0.6 s)", then "Armed." 0.8 s after the
script started (EV ARMED at W 2070.881); no pre-arm failure message before it. The watcher's MAVLink heartbeat from
system ID 211 was flowing (the FC's GCS failsafe later latched/cleared on it, e.g. "GCS Failsafe Cleared" each time it
resumed). Duration: ground only — arming acceptance needs no take-off.

**B1a — PASS.** "REFUSING TO ARM: no watcher heartbeat (fail-closed safety watcher, WATCH_HEARTBEAT)" after the 60 s cap;
no EV ARMED in the dataflash in that window (the first ARM of the boot is B1c(i), 4 s later).

**B1b (= B9d) — PASS.** `flow_tracker` stub SIGKILLed; "REFUSING TO ARM: watcher not confirming (box=0 bridge=0)". (box
is 0 too because the dependency loss latched an episode; bridge=0 as worded.) No ARM.

**B1c (G6), stock firmware, watcher never started in the boot:**
- (i) `ARMING_RUDDER 2`, stick arm in STABILIZE: **the FC ARMED** (EV ARMED W 2055.123) → **FAIL of the stock FC side,
  as predicted** (the known finding, confirmed in SITL).
- (ii) `ARMING_RUDDER 0`, same stick input: **did not arm → PASS** (mitigation (i) blocks stick arming).
- (iii) non-force MAVLink arm from system ID 255: **ARMED** (ACK 0) — as predicted: mitigation (i) is procedural only.
- (iv) force-arm (2989): **ARMED** — as predicted.

**B1-native — PASS.** Watcher confirmed, SIGKILLed while disarmed, 6 s later a non-force arm: ACK 4 (denied), the only
message "Arm: GCS failsafe on". After the restart: "GCS Failsafe Cleared" 3.4 s later, and the flight script armed.

**B1c-Lua (G6 ii) — PASS** (re-run `wbench_lua`). The draft `watcher_arming_auth.lua`, run in SITL:
- (a) watcher never seen: non-force MAVLink arm REFUSED, the only message "Arm: Watcher: never seen"; stick arm with
  `ARMING_RUDDER 2` REFUSED ("Arm: Watcher: never seen", "PreArm: Watcher: never seen");
- (b) watcher confirmed (`--lua-auth`, it read back `SCR_ENABLE 1`): the flight script ARMED — so the script does not
  simply always fail;
- (c) watcher SIGKILLed, 6 s: REFUSED ("Arm: GCS failsafe on", "Arm: Watcher: heartbeat 6.5s old");
- (d) after a reboot (never seen), force-arm: ARMED (bypass, as predicted).
- In the ground session the same sequence was confounded: (a) also showed "Gyros inconsistent" (12 s settle after the
  reboot), so it is not used; the re-run waited 45 s.

**B2a — PASS.** Hover, watcher SIGKILL → MODE LAND (reason GCS_FAILSAFE) at **+2.767 s W** (+2.755 s F) ≤ 4.0 s. Layer
first: the **FC's GCS failsafe**; the flight script's LAND followed at +3.485 s W (FC already in LAND).

**B2b (G5, G11) — PASS.** Flight script SIGKILLed 2.0 s before the watcher; watcher SIGKILL → ERR FAILSAFE_GCS and MODE
LAND (GCS_FAILSAFE) at **+2.366 s F** ≤ 3.5 s, with MAVProxy (system ID 255) sending its heartbeat throughout: nothing
else refreshed the GCS timer.

**B3a — PASS.** Relay drop (both directions) → ERR FAILSAFE_GCS at **+3.286 s F** ≤ 3.5 s. As expected, the watcher
withdrew on "FC link lost: no FC HEARTBEAT for 3.0 s" at +2.16 s W with **no LAND** (0 LAND commands); the first actor was
the flight script (WatcherLost → LAND, MODE LAND GCS_COMMAND at +2.937 s W), the FC failsafe 0.35 s later.

**B3b — PASS.** SIGSTOP → MODE LAND (GCS_FAILSAFE) at **+2.848 s W** ≤ 4.0 s. SIGCONT 1.0 s after LAND was seen (still
airborne): the watcher logged "watcher stalled: own loop gap 3.87 s … no LAND sent, heartbeat stays withdrawn", sent 0
LAND commands, and re-confirmed (heartbeat resumed) only 2.6 s after the disarm (the 2 s episode clear). No mode change other than the
landing and no re-arm in the 10 s observed after the disarm (the next MODE GUIDED is the operator's, after the window).

**B4b side face (y = 3 m) — PASS** (`hoverA2`). First pose outside (0.481, 3.007, 1.602): watcher BREACH at **+0.000 s**
(same sample) ≤ 0.1 s; LAND command +0.001 s; FC MODE LAND at **+0.038 s W** ≤ 1.0 s; exactly ONE LAND decision and one
send (ACKed). (Attempt 1 in `hoverA`: identical behaviour, BREACH and MODE LAND in the same millisecond; that session then
stopped on finding F2.)

**B4b top face (z = 3.0 m, G10) — PASS** (`hoverA3`). First pose outside (0.053, 0.048, 3.005): BREACH +0.000 s, MODE
LAND **+0.004 s W**; one LAND.

**B5a — FAIL as worded (stale declaration 8 ms late); LAND part PASS.** Last frame sent 0.011 s before the stop
command. Watcher "mocap pose stale (0.51 s > 0.5 s)" at **+0.508 s** after the last frame: the criterion "within 0.5 s"
is missed by 8 ms. LAND command at +0.508 s, FC MODE LAND at **+0.559 s W** ≤ 1.0 s (PASS); confirmation withdrawn at
+0.508 s; MAVLink heartbeat: the last one at +0.14 s (pose still fresh), the next only after the disarm + 2 s.
- **Why:** the watcher's rule is "stale when older than `stale_s` = 0.5 s", evaluated each ~20 ms loop, so detection is
  necessarily a little AFTER 0.5 s; the pre-registered bound equals the limit itself and leaves no room for the loop
  period. This is a criterion/limit mismatch, not a malfunction; the watcher was NOT changed. **A ruling is needed**
  (e.g. bound = stale limit + one loop period, or `--stale-s 0.45`). Per the instructions this line stopped here.

**B5b — PASS** (as worded for the untracked case). (1) Frozen poses WITH a tracking flag (tracked = 1) for 3 s: no
watcher event, no mode change (observation, by design). (2) tracked = 0: BREACH "reported NOT TRACKED" on the first
untracked frame (+0.000 s), MODE LAND **+0.052 s W** ≤ 1.0 s; heartbeat stopped (none after).

**B5b-noflag — FAIL as worded (10 ms late); LAND part PASS; case: the frozen fallback.** (A6.) Freeze in a hover with no
tracking flag: "mocap pose frozen (bit-identical for 0.51 s, no tracked flag)" at **+0.510 s** after the first frozen
frame (bound 0.5 s: missed by 10 ms, same cause as B5a); MODE LAND **+0.562 s W** ≤ 1.0 s.

**B5c — PASS.** Ground. Stream stopped 3 s (the stale breach sent its one LAND to the landed FC), restored: first fresh
frame W 2142.131, confirmation W 2144.144 = **2.013 s** ≥ 2.0 s; no LAND or mode command after the restore.

**B6a (stream level) — PASS.** Body `other_body`/ID 2 only: never confirmed (stale, as the samples are ignored),
"REFUSING TO ARM: watcher not confirming (box=0 bridge=0)".

**B6b (motion identity, D1) — PASS (both runs).** Observer watcher (system ID 212, SERIAL3, ATTITUDE 24.7 Hz), manoeuvre
roll 12° for 0.8 s then yaw 90°:
- right body: `identity=confirmed (proven (roll/pitch and yaw change agree))`, max roll/pitch difference 1.05°;
- static other body under the right name: `identity=failed (FAILED: roll/pitch disagree by 12.2 deg > 5.0 for 0.5 s
  (mocap r/p 0.0/0.0, FC 12.2/-4.7))`; it never confirmed (0 heartbeats sent).

**B7a — PASS on the forwarder → watcher path only** (n = 93,903 poses, all hover sessions, the injected-latency window
excluded): median **0.10 ms**, p99 **0.50 ms** (localhost). The maximum, 3.85 s, is the B3b SIGSTOP backlog. The true
exposure → watcher latency is hardware-only. **Observation:** +150 ms added latency was logged (median 0.152 s in the
track's latency column) and not acted on, as designed.

**B7b — PASS.** 12 LAND commands from the watcher's own `FcLink` (system ID 213) on the watcher's link, disarmed:
send → MODE LAND median **0.008 s**, **p99 0.248 s** ≤ 0.3 s, max 0.274 s (the first command: a `udpin` link cannot send
until it has received a packet, so the first send was lost and the 0.3 s retry delivered it). 4/12 needed a retry before
the ACK arrived although the mode had already changed (the ACK of the first send was not received). In flight, every
watcher LAND reached MODE LAND in 0.003–0.05 s.

**B8a — VOID (report-only test; the watcher acted first).** Hover; `flow_bridge.py` SIGKILLed. EKF3 raised **no
failsafe** (no EKFCHECK / FAILSAFE_EKFINAV / EKF_FAILSAFE mode change). At +5.06 s "EKF3 IMU0/IMU1 stopped aiding";
the vehicle then accelerated east (GT x 1.77 → 9.3 m in 2.6 s, ~3.6 m/s) and the watcher's box breach (x = 3.047) sent
LAND at +6.35 s. Under the pre-registered isolation rule the run is VOID; it was not repeated, because the same
excursion would breach any box that fits the mat (finding F1).

**B9a — PASS.** `--dep-loss land`.
- `flow_tracker` stub (in-process beacon) SIGKILL: withdrawal **+1.004 s** ≤ 1.5 s, MODE LAND **+1.034 s W** ≤ 2.5 s.
- `flow_bridge` stub (`proc` sidecar) SIGKILL: withdrawal **+0.820 s**, MODE LAND **+0.867 s W**.
- In both, the MAVLink heartbeat stopped at detection (any heartbeat after the injection was before detection, within
  the 1.0 s beacon timeout) and resumed only after the disarm + 2 s.

**B9b — PASS.** `--dep-loss stop`, `flow_tracker` SIGKILL: "…(--dep-loss stop has no hardware meaning: mapped to LAND +
alert, G8)", withdrawal **+0.922 s**, MODE LAND **+0.952 s W**.

**B9c — PASS.** SIGSTOP of the `flow_tracker` stub: withdrawal **+0.895 s**, MODE LAND **+0.942 s W**; SIGSTOP of the
`flow_bridge` stub (sidecar sees state T): **+0.860 s**, MODE LAND **+0.917 s W**.

**B9-hang (observation).** Beacon alive, progress frozen: "no progress for 2.00 s (hung)" at +1.813 s, MODE LAND +1.822 s.

**B10a — PASS.** RC mode switch: ALT_HOLD **+0.225 s**, STABILIZE **+0.218 s**, ALT_HOLD **+0.221 s**, LAND **+0.242 s**
(all W, ≤ 0.3 s; reason RC_COMMAND). Between ALT_HOLD and the LAND switch the only MODE events are the three RC ones,
although the flight script kept sending GUIDED position targets at 2 Hz.

**B10b — PASS, with the H10 caveat.** In ALT_HOLD:
- (1) watcher SIGKILL: "GCS Failsafe - Continuing Pilot Control", no mode change; the flight script (H10 PROTOTYPE guard)
  logged "H10 guard: FC in ALT_HOLD -> NOT commanding LAND (fly_trial.py as-is WOULD command LAND here)";
- (2) a new watcher confirmed mid-air ("GCS Failsafe Cleared"); dependency loss → its ONE LAND (MODE LAND +19.385 s);
  the pilot's switch move at +19.712 s → ALT_HOLD at **+19.934 s** (0.22 s after the toggle, ≤ 1 s); nothing
  re-commanded LAND until the pilot's own LAND switch at +49.98 s; the GCS failsafe that followed again said
  "Continuing Pilot Control";
- (3) aiding loss (`flow_bridge.py` SIGKILL, 15 s): no mode change and no EKF failsafe.
- **Caveat: `fly_trial.py` as-is would FAIL B10b** — its `WatcherLost` path commands LAND regardless of mode. The pass
  depends on the H10 guard, which exists only in this bench driver.

**B10c (model only) — PASS.** Armed on the ground, `SIM_RC_FAIL 1`: "Radio Failsafe - Disarming" 1.1 s W later
(`FS_THR_ENABLE 3`).

**Observations:** frame-counter reset mid-hover — no watcher event, no mode change; wrong body ID mid-hover — the
samples are ignored, stale at +0.489 s after the first wrong-ID frame (0.51 s after the last good one), MODE LAND
+0.507 s W.

### 2.2 Findings (not watcher bugs)

- **F1 (B8a): flow loss in GUIDED on EKF3 gives no EKF failsafe, then a fast lateral excursion.** About 5 s after the
  flow stopped reaching the FC, EKF3 "stopped aiding" and the vehicle accelerated to ~3.6 m/s sideways; only the
  watcher's box stopped it, and the LAND then drifted ~10 m further before touchdown. For rung 1 (EKF3 flying on flow):
  the mocap box is the protection; `FS_EKF_ACTION` will not act. Consistent with §7.2 B8(a)'s "report-only" expectation
  but more violent than `H_safety_ekf3_ref` (ExtNav) suggested.
- **F2: after a LAND that began with lateral motion, ArduCopter's land detector sometimes did not trip on flow-only
  EKF3** (B4b_side attempt 1: >3 min on the ground in LAND, throttle 0, still armed; B5b and the obs hover: operator
  disarm after 15 s / 4 s). Once (after B9b) the vehicle rocked and **tipped over** ("Crash: Disarming: AngErr=34>30"),
  ~9 s after touchdown. For real flights: the safety pilot must be ready to disarm after any automatic LAND.
- **F3 (B5b-noflag set-up): a source with no tracking flag and a perfectly still vehicle never confirms** (bit-identical
  poses = frozen). Fail-closed and correct; on hardware, mocap noise normally breaks bit-identity, but a VRPN-type source
  that repeats the last pose exactly would keep the watcher from confirming at rest.
- **F4: `fly_trial.connect()` takes the FIRST heartbeat it sees.** With other MAVLink senders on the link (MAVProxy, and
  the watcher's heartbeat that the FC routes to its other links) it pinned "system 0" and pymavlink mapped "GUIDED" to
  15 ("Mode change to Autotune failed"). It is harmless when the FC is already in GUIDED, but the real flight script (H10)
  must pin the FC's system ID and take the mode mapping from the FC's own heartbeat. Fixed in the bench driver only;
  `fly_trial.py` was not touched.
- **F5: B5a / B5b-noflag bound.** "Stale within 0.5 s" with a 0.5 s stale limit cannot be met (detection is 8–10 ms
  after the limit); ruling needed (see B5a).
- **The SITL analog rangefinder and SITL optical flow** are unusable with this JSON/Gazebo model (A4/A5): relevant to
  the SITL plan for the UKF-only closed loop (`docs/ukf_only_closed_loop_costing.md` assumes `SIM_FLOW`).

### 2.3 Bugs found in the watcher

**None.** No file under `realflight/watcher/`, `realflight/mcp1.py` or `realflight/params/` was changed (git diff empty),
so the 83 offline tests were not re-run after the bench (they passed at the start of this stage: 83 passed in 84 s).

## 3. Hardware-only tests (as §1.3), confirmed

B4a (carry through each face, disarmed), B4c (60° hand tilt), B4d (box geometry), the B6 hand procedure (D1), B7a true
exposure latency, B7c (mocap ↔ FC alignment with hand sync wiggles), B8b/B8c (UKF/FGO ports; item 2d), the real B10c
receiver failsafe, the Lua script on the real board, beacons inside the Pi processes, the audible alert.

## 4. Files

- Driver (new, SITL only): `realflight/sitl_bench/` — `bench.py` (sessions), `stack.py` (launch, operator link, RC
  model), `flight_script.py` (flight-script layer using `fly_trial.py`'s gate), `mocap_forwarder.py`, `udp_link.py`,
  `dep_stub.py`, `analyse.py`, `results.py`, `arm_events.py`, `params/`; `tools/run_wbench.sh <session>` (FLIGHT_LOCK).
- Not modified: `run_trial.sh`, `sim/tools/closed_loop_run.sh`, `fly_trial.py`, `realflight/watcher/`,
  METHODOLOGY.md, numbers.md. SITL ran in its own working directory (`~/thesis_data/wbench/sitl_cwd`), so the shared
  `~/ardupilot/ArduCopter/eeprom.bin` was never written.

## 5. For the next stage

- Rulings needed: the B5a/B5b-noflag bound (F5); G6 — SITL shows the Lua aux-auth works (B1c-Lua) on stock 4.6 SITL;
  the board must still be bench-tested.
- H10 requirements for the real flight script: the B10b guard; pin the FC system ID and mode mapping (F4).
- Safety procedure: the pilot disarms after any automatic LAND if the FC does not (F2); the box is the only protection
  on EKF3 flow loss (F1).
