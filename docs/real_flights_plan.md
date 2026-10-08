# Real flights: design plan (no hardware yet)

Status: PLAN. Written 2026-10-02, after the simulation work and before the 16 Oct simulation freeze. Nothing here
changes a thesis result. Facts verified in source or in the logs are marked [V], estimates [E], and unknowns that need
hardware or a decision [U]. Part C (`docs/partC_onboard_feasibility.md`) holds the source traces for the routes and the
compute budget. This plan updates it with what has been built and measured since: the thin FGO backend, the C++ heading
program, the D25 clock map and the node step times.

**Supervisor direction (2026-09-29):** all estimators on the Raspberry Pi; real mocap flights in scope; the forward
camera flown only once verified.

**Supervisor decisions (2026-10-08), §9:** BOTH approved.
- **Open loop:** EKF3 flies; the UKF and FGO run alongside on the Pi with identical data, scored against mocap.
- **Closed loop:** each estimator flies its own flights.
- **Flight profiles:** the wall-tag holding task (`docs/tag_hold_design.md`) and laps (as experiment T).
- Questions 1 and 9 below are resolved by §9.

---

## Open questions for the supervisor (decisions needed before hardware work)

1. **Steering route.** *(RESOLVED 2026-10-08: route 3 (open loop) and route 1 (closed loop), staged as §9.4.)* Which
   estimator may fly the vehicle, and how?
   - (1) The thin external-estimator backend, already built and SITL-validated for the FGO: the Pi estimate flies through
     an on-FC output predictor.
   - (2) EKF3 fusing the Pi estimate as ExternalNav, a cascade.
   - (3) Shadow only: EKF3 flies, and the UKF and FGO run on the Pi and are scored open-loop against mocap.
   - Recommendation: (3) for the first campaign, then (1) for the UKF and FGO once (3) is clean. Route (2) is not a fair
     estimator comparison (§2).
2. **UKF placement.** The UKF already exists as an ArduPilot port (`AP_NavUKF`) that can fly onboard the FC. "All
   estimators on the Pi" means running the UKF on the Pi as well, behind the same thin backend as the FGO.
   - Which applies? Pi placement makes the UKF and FGO share the same link latency (fairer between them), but adds a
     latency EKF3 does not have.
3. **Hardware.**
   - Flight controller: the Pixhawk 6X and CubeOrange firmware for this tree has been built, and the flash budget checked
     in Part C.
   - Pi 4 or Pi 5? The FGO needs a Pi 5 or the D11 speed-up (§6).
   - Downward camera and lens; forward camera and lens.
   - Rangefinder model.
   - Frame size and propeller guards.
4. **Optical-flow source.**
   - In simulation, flow is computed from the downward camera by our tracker, sent to EKF3 as `OPTICAL_FLOW`, and given
     to the UKF and FGO directly. Keep the same on the real vehicle (same algorithm, same input for all three; my
     recommendation)?
   - Or use an FC-native flow sensor (e.g. PMW3901 or HereFlow) whose output the Pi would then receive second-hand?
5. **Mocap facility.**
   - Which system (Vicon or OptiTrack)? Capture-volume size? Time source (PTP or NTP)? Can the mocap host join the same
     network as the Pi?
   - The simulated corridor is 160 m. A lab volume is roughly 5–15 m, so the experiment changes. Is the degraded-sensing
     axis to be reproduced with floor mats (textured and blank) inside the volume?
6. **Forward camera in the lab.** The heading program needs corridor-like line structure (Phase 3: it fails on plain
   walls over a checkerboard). Does the lab offer it, or are textured wall panels to be added?
   - The frozen calibration is simulation-specific (60°, 640×480, ideal pinhole). A real lens needs distortion
     calibration and re-validation, which is a new pre-registration.
7. **Safety ownership.**
   - Safety pilot.
   - Tether or net.
   - Minimum height.
   - RC override policy (a mode switch to a mode that needs no estimator position).
   - Whether flying a non-EKF3 estimator needs an extra lab or safety review.
8. **Pre-registration of the real-flight criteria.** The simulation criteria (U1–U3, B1–B5) assume a 160 m corridor
   (B2 band 6 m, wall-contact timing). New criteria must be fitted to the capture volume.
   - Should they be pre-registered with the supervisor before the first flight?
9. **Compute compromise for the FGO** *(options and recommendation now in §9.3)*, if the Pi cannot run it at 30 Hz
   keyframes (§6):
   - (a) the D11 speed-up (C++/analytic Jacobians), or
   - (b) a lower keyframe rate (e.g. 10–15 Hz), which changes the estimator relative to simulation and needs a new
     simulation check before the freeze.
   - Which is acceptable?

---

## 1. Architecture

```
            ┌──────────────── flight controller (ArduPilot, this tree) ─────────────────┐
 IMU ──────►│ INS 1 kHz → EKF3 (baseline, always running; flies in route 3)             │
 rangefinder►│ RNGFND1 (serial)                                                          │
            │ AP_AHRS: EKF3 | thin backend (UKF/FGO state from the Pi, output predictor) │
            └─────▲──────────────┬───────────────────────────────▲──────────────────────┘
       OPTICAL_FLOW, ODOMETRY    │ HIGHRES_IMU 333 Hz,            │ (route 1 only) ODOMETRY state
       (heading, as ExtNav yaw)  │ DISTANCE_SENSOR, SYSTEM_TIME   │
            ┌─────┴──────────────▼───────────────────────────────┴──────────────────────┐
            │ Raspberry Pi: flow tracker (downward cam) · heading program (forward cam) │
            │               UKF · FGO · clock map · logging (bags)                      │
            └───────────────────────────────▲──────────────────────────────────────────┘
                                            │ mocap pose (LAN, PTP/NTP-synced) — EVALUATION + SAFETY only
                                     mocap host / ground station: watcher, logging
```

- **The same physical sensors feed every estimator**, as in simulation:
  - the FC IMU (EKF3 directly; UKF and FGO via `HIGHRES_IMU`);
  - the rangefinder on the FC (EKF3 directly; UKF and FGO via `DISTANCE_SENSOR`);
  - flow computed on the Pi (EKF3 via `OPTICAL_FLOW`; UKF and FGO directly);
  - heading computed on the Pi (EKF3 via ExtNav yaw `ODOMETRY`; UKF and FGO directly).
- **Mocap is never an estimator input.** It is ground truth for scoring and the input to the safety watcher.

## 2. Steering routes and fairness

**Route 1: thin external-estimator backend** (`AHRS_EKF_TYPE 13` for the FGO; the same pattern for a Pi UKF) [V in SITL].
- The Pi sends each state as `ODOMETRY`. The FC backend (`AP_NavFGO`) validates it (flag, arrival ≤ 250 ms, age ≤ 250 ms)
  and propagates it to current time with the FC's own IMU (the output predictor, FG3/FG3b), so the controllers see a
  current state.
- Validated in SITL:
  - FG1 (received = offline);
  - FG2 (`OV` 100%);
  - FG3b (output age ≤ 183 ms);
  - D25 (no start-up invalidity);
  - closed-loop flights (`cl_fgo_*`).
- **Fairness:** the Pi estimators pay a link latency (in SITL, state age 130–180 ms at half speed) that EKF3 does not.
  The output predictor removes most of it (FG3 position p95 ≤ 0.003 m away from the climb top), but the asymmetry is
  stated with every closed-loop result. With the UKF also on the Pi (question 2), the UKF and FGO share it exactly.

**Route 2: EKF3 fuses the Pi estimate as ExternalNav** [V, Part C §2.5].
- What flies is EKF3 re-filtering a time-correlated estimate that already contains the same IMU, flow and range. That
  double-counts the information, and EKF3's floors reshape it. Flow cannot remain in the same EKF3 source set.
- It is a cascade, not "FGO vs EKF3". **Use ExtNav only for information unique to the Pi** (the forward-camera heading,
  as already done in simulation set (b)).

**Route 3: shadow only** [V in SITL: `fgo_shadow_*`, `ukf_shadow_*`].
- EKF3 flies; the UKF and FGO run live on the Pi on the same flight, and are scored against mocap.
- The comparison is on one trajectory for all three: the strongest like-for-like design. It gives no closed-loop
  stability claim for the UKF or FGO.

## 3. Pi inputs: messages, rates, timestamps

| Input | Message, path | Rate achievable | Timestamp | Notes |
|---|---|---|---|---|
| IMU (accel + gyro, co-sampled) | `HIGHRES_IMU` via `SET_MESSAGE_INTERVAL` on a dedicated serial port to the Pi (the SITL `--serial2` pattern) | 333 Hz: the cap is 0.8 × `SCHED_LOOP_RATE` and the interval is truncated to whole ms [V in SITL]. At 921 600 baud, ~75 B × 333 Hz ≈ 25 kB/s of ~92 kB/s [E] | `time_usec`, the FC clock | Filtered instantaneous samples, not EKF3's delta-angles: the rectangular-integration caveat of the simulation applies unchanged [V]. `SCHED_LOOP_RATE` stays 400 (raising it changes EKF3) |
| Range | `DISTANCE_SENSOR` relayed from the FC (`RNGFND1` serial), or the sensor read directly on the Pi and injected (the SITL pattern) | sensor rate, typically 20–100 Hz [U] | FC time, or Pi time if read on the Pi | One physical sensor for all three. Its short-return artefact (D23) must be characterised on the real airframe |
| Flow | computed on the Pi (`flow_tracker.py`, downward camera); `OPTICAL_FLOW` to the FC | camera rate, 30 Hz in simulation | capture stamp (Pi) | EKF3 stamps on receipt minus `EK3_FLOW_DELAY`, which must be measured on hardware (D8 showed misdating costs EKF3 little in simulation) |
| Heading | C++ heading program on the Pi (forward camera); `ODOMETRY` yaw to the FC for EKF3 | 7.5 Hz in simulation (`every_n` 4) | capture stamp | `VISO_DELAY_MS` is measured on hardware with the D2/D20 ground-test procedure |
| State out (route 1) | `ODOMETRY` (LOCAL_NED, NAIVE) to the backend | keyframe rate, 30 Hz | keyframe time mapped to FC time | The thin backend's validity rules apply |
| Clock | `SYSTEM_TIME` (FC `AP_HAL::millis`), `TIMESYNC` | 4 Hz plus on demand | — | Used as the D24 fallback clock |

**Time sync:**
- **FC ↔ Pi:** the clock map already used by the FGO node (D25): the low percentile of (Pi receipt − `time_usec`) over a
  settled 10 s window, outlier-robust. It needs no FC change.
  - On hardware the offset drifts with the FC crystal (simulation: SITL ran 0.02% slow). The window tracks it.
  - Add `TIMESYNC` round trips as a cross-check [E].
- **Pi ↔ mocap host:** chrony (NTP) or PTP on the lab LAN. Mocap poses are stamped by the mocap host and logged with
  both host and Pi receipt times. The offline alignment (tooling item 4) estimates any residual offset from the data
  itself.

## 4. Camera and heading program on the Pi

- **Heading:** the C++ port (`src/forward_camera/cpp/heading.cpp`), bit-equivalent to the frozen Python measurement in
  simulation. It runs at 15.3 ms/frame median on the i7 (single thread); on a Pi, see §6.
  - It is cross-compiled for ARM64 by tooling item 2.
  - It needs the OpenCV 4.6 LSD, because the LSD implementation changed across OpenCV versions and the frozen
    calibration used 4.6.
- **Calibration:**
  - The real lens needs intrinsics and distortion (tooling item 3: chessboard calibration, then undistortion before the
    heading program).
  - The frozen parameters (inlier tolerance 0.5°, `S_MIN` 200 px) were calibrated on ideal simulated images. They are
    **re-validated on real recordings before any flight**, under a new pre-registration (question 6).
- **Flow:** `flow_tracker.py` (Shi-Tomasi + LK + RANSAC) on the downward camera. Its focal length and camera mount must
  be measured, and the gyro derotation sign re-verified (the lateral-sign finding of 2026-09-29).

## 5. Logging

- **FC:** `LOG_REPLAY=1`, `LOG_DISARMED=1` (Replay of every flight, and pre-arm data), `LOG_BITMASK` with IMU at full
  rate.
  - The thin backend logs `XFGI`/`XFGO`; the UKF port logs `XUK*`; EKF3 logs `XKF*`.
- **Pi:** a ROS 2 bag with every input topic, the estimator outputs, `/imu/time_ref`, the heading-bridge CSV, and the
  node stats with clock-map diagnostics (`fgo_node_stats_clockmap.npz`).
- **Mocap:** poses with host stamps plus Pi receipt stamps, recorded on the Pi or the ground station.
- **Metadata:** per trial, as `run_trial.sh` writes: the commits of every repo, the FC firmware hash, the parameters, and
  the hardware IDs.

## 6. Compute budget on the Pi

| Workload (period) | i7-8700 measured | Pi 4 [E: 3–5× slower] | Pi 5 [E: 1.5–2.5× slower] |
|---|---|---|---|
| Heading, C++ (133 ms at 7.5 Hz) | 15.3 ms median, p99 20.4 [V] | 46–77 ms: fits at 7.5 Hz, not at 30 Hz | 23–38 ms: fits |
| Flow tracker, Python (33 ms) | measured in simulation at 30 Hz [U on Pi] | must be timed; 640×480 LK may need C++ or 320×240 | likely fits |
| UKF, Python (12.5 ms predict) | predict 1.5–1.6 ms; plus updates [V] | 4.5–8 ms: 36–64% of one core | 2.3–4 ms |
| FGO node, Python GTSAM, 0.25 s window (33 ms) | median 28.4, p95 53.1, p99 58.7 ms with heading (`cl_fgo_b_tex_r1_half`) [V] | 85–140 ms median: **does not fit 30 Hz** | 43–71 ms median: **does not fit 30 Hz** |

**What the FGO needs:**
- **(a) The D11 speed-up:** C++ GTSAM with analytic Jacobians. Expected 5–15× faster than the Python `CustomFactor`
  path [E, Part C §5.4], giving ~2–6 ms on the i7 and ~6–30 ms on a Pi 4. It fits.
- **(b) A lower keyframe rate:** 10 Hz keyframes give a 100 ms budget, which fits a Pi 5 at the measured per-step cost.
  But it changes the estimator relative to every simulation result.
- **Recommendation:** (a), if the FGO is to run live. Shadow mode (route 3) could instead log its inputs and run the FGO
  offline after the flight, which needs no speed-up. In that case the FGO is not "running on the Pi" in real time, which
  must be stated.
- **Cores:** a Pi has 4. The heading program, flow, UKF and FGO can be pinned one per core. Active cooling is needed
  (Part C §6.5).

## 7. Safety

- **Watcher equivalent:** a mocap-based geofence process on the ground station, as `wall_watch.py` in simulation. It
  monitors the mocap pose and commands LAND (or BRAKE then LAND) over MAVLink, and alerts the safety pilot, when the
  vehicle breaches a box inside the capture volume or the mocap stream stops.
  - **It must not depend on the estimator under test.** ArduPilot's own fence uses the AHRS position, i.e. the estimator
    being tested, so it is a secondary layer only.
- **FAIL-CLOSED (ruling 2026-10-08), every closed-loop flight:**
  - **No arming** unless the mocap watcher has started and sends a confirmed heartbeat with both checks active: the
    capture-volume box (from mocap) and the liveness of the input processes the flight depends on (tag/heading bridge,
    flow tracker, the Pi estimator for route 1).
  - **Mid-flight, the flight lands** if that heartbeat stops (> 3 s) or a check is withdrawn.
  - On the vehicle this is enforced on two sides:
    - the flight script refuses to arm and lands, as in SITL (`fly_trial.py`, `WATCH_HEARTBEAT`);
    - the ground station watcher's heartbeat goes to the FC as a MAVLink message, with a Lua or companion-side
      "no heartbeat → LAND" failsafe as the second layer.
  - Tested before the first flight of each stage, by not starting the watcher (must refuse to arm) and by killing it
    in a tethered hover (must land).
  - Verified in SITL on 2026-10-08 (METHODOLOGY "fail-closed safety watcher").
- **Safety pilot:** RC override to a mode that needs no estimator position (STABILIZE or ALT_HOLD; ALT_HOLD needs only
  height and attitude), on a dedicated switch. Rehearsed before every session.
- **Estimator failsafes:**
  - **EKF3 flying:** the standard EKF failsafe (`FS_EKF_ACTION`, `FS_EKF_THRESH`).
  - **Thin backend flying:** the backend reports zero innovation variances (`AP_AHRS_FGO::get_variances`) [V], so
    `ekf_check` can only trip on "no relative position" when the Pi state goes invalid (`ekf_check.cpp`, `has_position`).
    The output goes invalid 130 ms after the last state (FG2 node-stop) [V].
    - **CORRECTED 2026-10-08 (`H_gt_fgo` crash, METHODOLOGY "H SITL GROUND TESTS"): it does NOT trigger.**
      `Copter::ekf_check` returns at its first line when AHRS has no origin, and the port backends have none, so
      `FS_EKF_ACTION` can never fire on the UKF/FGO port. Worse, on invalid output the port froze the AHRS attitude
      (stale estimates copied, no DCM fallback), and `AC_PosControl` zero-filled the position. **Before any flight on
      a thin backend:** DCM attitude fallback on invalid output, an origin-independent "backend invalid → LAND"
      trigger, both verified by forcing invalidity in a hover.
    - **RULING 2026-10-08 (option (i)): a GATE.** On stale external state, attitude stays valid (FC-IMU-propagated
      every loop), only position/velocity time out, position loss → land on height + attitude, and an
      origin-independent landing trigger is added. **This behaviour must pass on the bench AND in SITL** (kill the
      estimator in a hover, with and without the watcher) **before any real closed-loop flight.**
  - The flight script must use the estimator-independent clock (`SYSTEM_TIME`, D24) and land on failure.
- **No arming if the flight controller has rebooted since the estimator node started (ruling 2026-10-09).** The Pi
  node's clock map is built against one FC boot. The pre-arm check compares the FC boot identity (boot counter or
  `SYSTEM_TIME` boot time / the dataflash log index) recorded at node start with the current one. On a mismatch the
  node is restarted and its clock map must settle ("first state sent") before arming. **In flight**, a backwards
  step of the FC clock (time-reference sensor time, offset tracking error > 0.1 s, or a sent state time going
  backwards) latches the node's output INVALID, so the FC's estimator-loss landing trigger applies. Verified in SITL
  (`fly_trial.require_fgo_node_current`, `live_adapter` clock-integrity latch) before any real flight.
- **Frame anchoring completes before arming (ruling 2026-10-08).** Every estimator that re-anchors to the marker/mocap
  frame must have anchored on the ground before arming (the vehicle placed where the marker is in view), and the FC must
  be receiving valid fixes. No frame change in flight. Gate it in the flight script, as `wait_fix` before arming.
- **Physical:** prop guards, tether or net (question 7), conservative speed (0.25–0.5 m/s), the lowest workable
  height (≥ 1 m for the flow and range geometry), and a battery failsafe.
- **Staged bring-up:**
  1. Bench, with props off: all streams, rates, clock map, logging.
  2. Hand-carried, with motors off: the estimators against mocap.
  3. Tethered hover with EKF3.
  4. Shadow flights.
  5. Only then any route-1 flight.

## 8. Tooling built now (no hardware), with self-test results

- **Item 2: ARM64 cross-build of the heading program and Pi checklist** (`docs/real_flights_pi_readiness.md`).
  - OpenCV 4.6.0 cross-built.
  - Under qemu-aarch64, every integer output (VP, counts, validity, quality) is identical to x86 on 205 real frames;
    |Δψ| ≤ 1.25 × 10⁻⁵°.
  - Native Pi timing and equivalence are still to be run.
- **Item 3: real-camera test pipeline** (`tools/real_camera/`): lens calibration, undistortion and resampling onto the
  frozen simulated camera, and a known-angle table test against Phase 3's bars (diagnostic).
  - Self-tests: a lossless PNG sequence of simulated frames reproduces Phase 3's frozen headings to 2.4 × 10⁻¹⁴°.
  - Synthetic distorted chessboards: fx recovered within 0.15%, k1 within 0.0012, and a 7.6 px lens-curved line
    straight to 0.024 px in the frozen frame.
- **Item 4: mocap alignment** (`eval/mocap_align.py`).
  - **Time, mocap ↔ FC:** a linear map from |ω| (mocap orientation against the FC gyro), fitted in take-off and landing
    windows. The gyro is shifted by the INS low-pass group delay, √2/(2π·`INS_GYRO_FILTER`) = 11.3 ms at 20 Hz. The
    rangefinder vertical speed is an optional cross-check only: its latency is unknown, and in the self-test it biased
    the offset by about −40 ms.
  - **Frame:** a 4-DoF fit (yaw + translation) on the initial segment for drift metrics, plus a whole-flight 4-DoF fit
    for evo -a style ATE. SE(3) is not used: a straight flight leaves rotation about its axis unobservable.
  - **Pi ↔ FC:** the D25 robust envelope, with a rate fit from `/imu/time_ref`.
  - **Self-test** (synthetic mocap from a simulated flight's SIM truth, known offset 3.457 s, +80 ppm, 37° yaw):
    offset recovered to −3.7 ms, rate to 4.9 ppm, yaw to 0.30°. It is limited by the 10 Hz SIM log and the 25 Hz
    logged gyro; real mocap at ≥ 100 Hz with full-rate IMU logging is expected to do better [E].
  - The Pi ↔ FC map on recorded bags gives 190–194 ppm, reproducing the known 0.017–0.02% SITL clock drift, with a
    start offset of 2–3 ms (as D25).
  - **For flights:** log the FC IMU at full rate (`INS_LOG_BAT_*` or a fast IMU bitmask). The mocap stream should
    include its own frame stamps and the Pi receipt stamps.

---

## 9. Supervisor decisions 2026-10-08: profiles, the real-FC backend, the real-time FGO, staging (PLAN ONLY)

### 9.1 Flight profiles

- **P-HOLD: wall-tag holding** (`docs/tag_hold_design.md`).
  - Hold 1.5 m in front of a wall tag (forward camera), with lateral ±0.5 m moves at 0.2 m/s, return, and a
    covered-tag segment (5 s and 15 s).
  - Navigation frame = the tag frame. EKF3 receives the tag fixes as ExtNav position + yaw; the UKF and FGO receive the
    same fixes directly.
  - Metrics: hold error, lateral tracking, gyro activity, drift during tag loss, re-lock time and jump. Mocap is
    ground truth.
  - This is the primary closed-loop profile: it stays inside a small volume and has a natural safe hold point.
- **P-LAPS: laps** (as experiment T).
  - A square of 4–6 m (fitted to the capture volume) at 0.3–0.5 m/s, constant yaw, with floor tags at known positions
    (absolute fixes) at a chosen density, or tags at unknown positions (L).
  - Open loop first. Closed loop only after P-HOLD has passed for that estimator.
- **Both profiles are scripted** with the `fly_trial.py` patterns: moving position setpoints, the
  estimator-independent clock (D24), land on failure. Both are SITL-rehearsed in the simulated mocap room before any
  hardware flight.

### 9.2 The thin backend on the actual flight controller

**What flies.** The thin external-estimator backend (`AP_NavFGO`, `EKFType::FGO` 13, SITL-validated: FG1–FG3b, D25,
`cl_fgo_*`) carries the FGO. The same pattern, with a UKF mode, carries a Pi-side UKF. Alternatively the UKF port
(`AP_NavUKF`, type 12) runs on the FC itself (question 2).
- The firmware is built from the port tree (`~/ardupilot_ukf`, branch `ukf-port`) for the actual board. The
  Pixhawk 6X / CubeOrange flash budget was checked in Part C.

**Flashing and rollback plan:**
1. **Baseline image** = the stock ArduPilot release the vehicle is first tuned on. Archive its `.apj` and a full
   parameter dump (`param save`) before any change.
2. **Thesis image** = the port tree at a tagged commit. Record the firmware git hash (`FWVersion`, logged) with every
   flight.
   - The thesis image must reproduce the baseline's EKF3 behaviour with the backends **disabled**
     (`AHRS_EKF_TYPE 3`, `AHRS_FGO_ENABLE 0`). This is checked by flying the baseline P-HOLD with EKF3 on both images
     and comparing hold error within the run-to-run spread.
3. **Flash** over USB with the ground-station tool. Parameters are restored from the dump plus a versioned
   `real_*.parm` file. The eeprom gotcha applies: `ensure_params`-style verification of every load-bearing parameter
   after each flash and boot.
4. **Rollback:** re-flash the archived baseline `.apj` and restore the parameter dump. This is rehearsed once on the
   bench before the first thesis-image flight, and takes about 5 min.
   - An in-flight fallback needs no re-flash: RC mode switch to ALT_HOLD/STABILIZE, plus `AHRS_EKF_TYPE 3` on the
     ground.
5. **Bootloader** untouched. No custom bootloader. A second, identical FC kept as a spare if possible.

**Tested first in SITL with Pi-like link latency:**
- The SITL rehearsal runs the Pi-side processes **with an injected link delay and jitter** matching the measured Pi
  link: a `tc netem` delay on the loopback UDP ports, or a delay stage in the bridges.
  - Starting values: one-way 5–15 ms ± 3 ms for USB/serial at 921 600 baud. To be replaced by the bench-measured
    distribution (§9.4 stage 0).
- **The pre-registered SITL gates repeat at that latency:**
  - FG1 (received = offline);
  - FG2 (validity 100%, invalid 130 ms after node stop);
  - FG3/FG3b (output age and predictor error);
  - D25 (no start-up invalidity);
  - one closed-loop P-HOLD per estimator.
- A gate failure blocks hardware closed loop for that estimator.

### 9.3 The FGO in real time on the Pi: options

The measured cost: the Python GTSAM node needs 28 ms median / 59 ms p99 per 30 Hz keyframe on the i7 (§6). Expected
3–5× slower on a Pi 4 and 1.5–2.5× on a Pi 5: it does not fit 30 Hz on either.

| option | what changes | effort (days) [E] | expected cost on a Pi 5 [E] | how it is proved equivalent |
|---|---|---|---|---|
| **A. C++ port, numerical Jacobians** (the same central differences as `factors.py`) | language only | 4–6 | 3–4× faster than Python: ~10–20 ms | Run the C++ node and the Python node on the **same recorded bags**: identical inputs, same keyframes, same factors. Require per-keyframe state differences below solver tolerance (position ≤ 1 mm, yaw ≤ 0.01°) and identical gate decisions, on the 9 `dsn_*`, 6 `fwdc`, the T and O sets. As D19's FG1 and the C++ heading port (bit-equivalence tests) were done. |
| **B. C++ port with exact Jacobians** (hand-derived, or generated with **SymForce** from the same `h_flow`/`h_range`/`h_heading`/`h_tag` models) | language + Jacobians | 6–9 (SymForce codegen + verification) | 5–15× faster than Python (Part C §5.4): ~3–8 ms | (1) **Unit level:** generated Jacobians against numerical differences of the *shared Python models* at random states (relative error ≤ 1e-6). (2) **System level:** as A, against the Python node on the same bags. Exact Jacobians move the LM steps slightly, so the band is position ≤ 1 cm and the same pre-registered outcomes. |
| **C. Lower keyframe rate** (e.g. 10 Hz; flow and range attached per keyframe or averaged) | the estimator | 1–2 (+ re-running affected simulation results) | the Python cost per keyframe at 10 Hz (100 ms budget): fits a Pi 5 | **Not** equivalent by construction: it changes the information per keyframe. Proof = a new simulation comparison against the 30 Hz FGO on the frozen datasets, with a pre-registered band (e.g. evo -a (cruise) within ±10%), stated as a different estimator configuration. |

**UPDATE (ruling 2026-10-08): option A built and accepted; SymForce (B) DROPPED.**
- The C++ port with numerical Jacobians passes the equivalence band on the aided (textured) bag, and runs at
  ~0.6–0.9 ms per keyframe (workstation, single thread) against the 33 ms budget. A Pi is expected to manage it without
  exact Jacobians; a Pi timing estimate follows.
- Accepted for real-flight use in the **aided** regime only (METHODOLOGY "RULING ... FGO C++ port").
- The recommendation below is kept for the record.

**Recommendation (superseded by the update above): B, with A as the stepping stone.**
- Build A first (fast to verify, since numerical Jacobians match by construction).
- Then switch the Jacobians to SymForce-generated exact ones (B) behind a flag, verified at both levels.
- B keeps the thesis FGO's configuration (30 Hz keyframes, 0.25 s window) and so transfers every simulation result.
  C is the fallback if A/B slip, labelled as a different configuration.
- For **open-loop** flights (route 3) the FGO may also run **offline after the flight** on the logged inputs, with no
  speed-up. This is stated as "not real-time" wherever it is used.
- L's keyframe FGO (whole-history iSAM2) is **not** a real-time candidate on the Pi. Its measured cost was 33–55 ms
  median and up to 2.2 s p99 per update in Python.

### 9.4 Staging, with safety requirements per stage

**Stage 0: bench and hand-carried (no flight).** Requirements:
- props off;
- all streams at rate: `HIGHRES_IMU` 333 Hz, flow 30 Hz, tags, heading;
- clock map settled (D25);
- link latency distribution measured, which feeds the §9.2 SITL rehearsal;
- `VISO_DELAY_MS` and `EK3_FLOW_DELAY` by the D2 procedure;
- tag validity rule and σ re-measured against mocap;
- hand-carried P-HOLD and laps paths, with every estimator scored against mocap;
- rollback rehearsed.

**Stage 1: open loop (route 3). EKF3 flies P-HOLD, then P-LAPS; the UKF and FGO run alongside on the Pi with
identical data.** Safety:
- the mocap geofence watcher (§7), independent of every estimator under test;
- safety pilot with RC override to ALT_HOLD;
- tether or net;
- ≥ 1 m height and ≥ 1 m wall clearance;
- 0.3–0.5 m/s maximum;
- `FS_EKF_ACTION` LAND;
- battery failsafe;
- the flight script lands on any script failure (D24 clock).

Entry: stage 0 complete. Exit: n flights with all logs complete and the pre-registered scoring done.

**Stage 2: UKF closed loop.**
- **Entry:**
  - stage 1 clean;
  - the UKF passes its SITL gates at Pi-like latency (§9.2);
  - its open-loop P-HOLD error in stage 1 is within the pre-registered band.
- **Additional safety:**
  - the backend-invalid → `FS_EKF_ACTION` path verified on the bench (open item in §7);
  - first flights tethered;
  - an RC switch from the UKF to EKF3 (`AHRS_EKF_TYPE` change) is **not** used in flight (an AHRS switch in flight is
    untested); the fallback is ALT_HOLD.
- **Order:** P-HOLD first; P-LAPS only after 3 clean P-HOLD flights.

**Stage 3: FGO closed loop.** Entry: stage 2 clean, the real-time FGO (§9.3 option B or A) passes its equivalence and
SITL gates, and its open-loop stage-1 results are within band. Safety as stage 2, plus:
- the per-keyframe solve time is monitored live, and the node stops itself (backend goes invalid → LAND) if p99
  exceeds the keyframe period for 2 s.

**Per stage:** a pre-registration (hypotheses, bands, n) written and reviewed before the first flight of the stage.
Every stage can be stopped by the safety pilot or the watcher without any estimator.
