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
   - Flight controller: NO board firmware has been built for this tree (correction 2026-10-10: only `sitl/` builds
     exist). Part C's flash budget used PUBLISHED Copter `.apj` sizes for Pixhawk 6X/CubeOrange. `AP_NAVUKF_ENABLED`
     defaults to SITL only (`AP_NavUKF.h:29`), so a board build must enable it explicitly. See
     `docs/real_flight_readiness.md`.
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
    The full bench procedure is §7.2 (B0–B10).
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
- **Flow validity: inlier ratio as well as feature count (ruling 2026-10-09; planned fix for D22).** In SITL, flow
  frames were flagged valid on the tracked-feature count alone (`flow_tracker.py:313`) while the features collapsed
  and the inlier ratio fell. This put false lateral flow into all three estimators, giving a 0.30 m/s and a
  0.25 m/s sideways burst (`cl_ukf_b_tex_r3_half`, `cl_fgo_b_tex_r3_half_v3`).
  - **Before the first real flight:** add an inlier-ratio threshold to the validity rule, IDENTICAL for EKF3, the UKF
    and the FGO (one flag, one source).
  - **Threshold calibration:** on the simulation calibration flights only (`p1c_*`; never the datasets), recorded
    and pre-registered.

  **7.1 Flow-validity rule: PRE-REGISTERED (confirmed by the user 2026-10-10, for the camera-flow path), 2026-10-10.**
  Details: `docs/handovers/2026-10-10_flow_rule_watcher_bench.md`. The calibration criterion was written down and
  committed (`b9706ce`) before any p1c number was read.
  - **Rule:** `valid = (feature_count >= N_min) AND (inlier_ratio >= r_min)`, with **N_min = 20** (today's value,
    unchanged) and **r_min = 0.85**.
    - `feature_count` is the post-RANSAC inlier count, because `tracked_count` is overwritten by the RANSAC
      survivors. `inlier_ratio` = survivors / tracked before RANSAC.
    - Today the rule is `valid = feature_count >= 20` alone (`flow_tracker.py:313`). In all six p1c bags the
      published flag equals that rule exactly (0 mismatches).
  - **Calibration data:** `p1c_fwdc_{tex,trans,blank}` and `p1c_fwdplainc_{tex,trans,blank}` only
    (`p1c_fwdplainc_blank_ABORTED` excluded; no dataset bag used). Each bag was decompressed to a scratch copy, which
    was deleted afterwards. Only `/optical_flow/measurement`, `/ground_truth/pose` and `/imu/data_raw` were read.
  - **Population:** frames valid under today's rule, airborne (GT z ≥ 0.30 m), over a textured floor. That means the
    whole flight on the `_tex` worlds, and GT y < 78 m on the `_trans` worlds. GT is interpolated to each flow stamp.
  - **Criterion (fixed before the data):** r_min is the LARGEST value on a 0.05 grid that keeps ≥ 99% of the pooled
    textured-floor frames valid (`inlier_ratio >= r_min`).
  - **Result:** 28,347 pooled textured-floor frames.

    | r_min | 0.80 | **0.85** | 0.90 | 0.95 | 1.00 |
    |---|---|---|---|---|---|
    | textured frames kept | 99.89% | **99.11%** | 94.57% | 83.29% | 78.14% |

    - The 1st percentile of the textured inlier ratio is 0.855, and the median is 1.00.
    - Per flight, the textured frames kept at 0.85 are:

      | flight | kept | rejected / frames |
      |---|---|---|
      | `fwdc_tex` | 99.05% | 90 / 9,464 |
      | `fwdc_trans` (textured half) | 98.94% | 50 / 4,731 |
      | `fwdplainc_tex` | 99.26% | 70 / 9,443 |
      | `fwdplainc_trans` (textured half) | 99.13% | 41 / 4,709 |
  - **Effect on the blank floor (reported, not used for the choice):** today's count rule already invalidates almost
    every blank-floor frame. Only 16 of about 28,400 airborne blank-floor frames are valid today, pooled over the two
    `_blank` flights and the y > 82 m part of the two `_trans` flights. The new rule rejects all 16 (inlier ratio
    0.21–0.33). **In these simulated worlds the new rule changes almost nothing on the blank floor.** It acts on
    the textured floor and in the climb.
  - **Climb (z 0.3 m up to the first z > 1.9 m), where both D22 episodes happened:**
    - 177 frames are valid today across the six flights, and the new rule rejects 39 of them;
    - the lowest inlier ratio among the climb frames valid today is 0.45, with feature counts ≥ 21.
  - **Truth-residual diagnostic (reported, not used for the choice):**
    - A per-axis linear truth model was fitted on the textured frames: flow ≈ GT body velocity / camera height, plus
      gyro terms. Residual RMS is 0.027 rad/s (x) and 0.025 rad/s (y).
    - All six flights have 23 currently valid airborne frames with a gross error (|residual| > 0.5 rad/s). The rule
      removes 19 of them, at a cost of about 0.9% of the good textured frames.
    - The rejected and accepted frames have about the same median residual (≈ 0.002–0.004 rad/s). Most rejected
      frames are therefore good frames: the rule removes most of the gross errors and about 0.9% of the good frames
      with them.
  - **Check on the D22 frames (looked at only AFTER r_min was fixed and committed):** see 7.1a below.
  - **Implementation (specified here, NOT implemented; real-flight pipeline only):**
    - **`flow_tracker.py`:**
      - add a parameter `min_inlier_ratio` (default 0.85) next to `min_valid_features` (20);
      - set `out.valid = tracked_count >= min_valid and inlier_ratio >= min_inlier`.
      - **Edge case:** if `estimateAffinePartial2D` returns no mask with ≥ 4 points, the ratio currently reads 1.0
        (no RANSAC applied). That frame is to be published INVALID, with `inlier_ratio = 0`.
      - `run_trial.sh` / the real-flight recorder writes both thresholds into `metadata.yaml`, as it does
        `flow_ransac_seed`.
    - **`flow_bridge.py`: no change in logic.** It already drops every `valid == False` message (`flow_bridge.py:123`)
      and sends `quality = round(inlier_ratio·255)`, so every sent message has quality ≥ 217.
      - EKF3 only checks `quality > 0` (`AP_NavEKF3_Measurements.cpp:203`).
      - The onboard UKF port does the same (`~/ardupilot_ukf` `AP_NavUKF.cpp:589`).
      - No second threshold is added anywhere: the one flag computed in the tracker is the only source.
    - **UKF / FGO on the Pi: no change.** They consume `msg.valid` and require `inlier_ratio > 0`
      (`ukf_core.py:291`, `fgo_cpp/src/replay_common.cpp:250`, `fgo_cpp_node.cpp:96`).
    - **Simulation pipeline unchanged before the freeze** (ruling 2026-10-09). Every thesis dataset stays under the
      count-only rule.
  - **Real-camera check (stage 0, before stage 1):**
    - On the hand-carried mocap runs over the flight floor, report the fraction of frames valid under the count rule
      that have `inlier_ratio >= 0.85`.
    - If it is < 99%, STOP and report: the real camera's inlier statistics differ from the simulation's, and the
      threshold is not silently re-tuned. Any change is a new ruling.

  **7.1a Check on the two D22 flights (read only AFTER r_min = 0.85 was committed in `eaa2011`; a check, not a
  calibration input).**
  - **Bags:** `cl_ukf_b_tex_r3_half` and `cl_fgo_b_tex_r3_half_v3`, the flow and GT topics only. The per-frame
    values below are the frames flagged VALID today.
  - **Correction to the bin means quoted in METHODOLOGY:** the "mean flow_x −1.37 / −2.27 rad/s" figures average
    every message in the 0.5 s bin. They include one INVALID frame per flight at lift-off (feature_count 3,
    flow_x −22.9 / −22.6 rad/s), which `flow_bridge` drops and the UKF and FGO ignore. The valid frames themselves
    carried:

    | phase (GT z) | UKF flight: valid frames | FGO flight: valid frames | rejected by the rule? |
    |---|---|---|---|
    | lift-off, z 0.29–0.37 m | 5 frames, flow_x +1.17…−1.25 (alternating sign), inlier ratio 0.53–0.71 | 6 frames, flow_x −4.35, −2.22, −1.29, −0.82, −0.56, −0.43; inlier ratio 0.48, 0.846, 0.92–1.00 | UKF: **all 5**. FGO: **2 of 6** (the two largest, −4.35 and −2.22); the other four (−1.29…−0.43) are KEPT |
    | climb, z 1.07–1.6 m | 12 frames, flow_x +0.65 decaying to +0.35, inlier ratio 0.86–1.00 | 14 frames, flow_x +0.24…+0.65, inlier ratio 0.64–1.00 | UKF: **0 of 12**. FGO: 3 of 14 (inlier 0.64, 0.83, 0.75); 11 are KEPT |

  - **Truth residual of the climb plateau:** the per-axis truth model (fitted on p1c) predicts ≈ 0 to +0.17 rad/s
    there, so the plateau is up to ~0.6 rad/s in excess of truth.
    - It starts before any roll: ωx = 0.00 at the first frame, and GT lateral velocity is 0.
    - The vehicle's roll rate then rises (to ωx ≈ +0.2 rad/s), and GT east velocity begins to grow 0.1–0.3 s after
      the plateau starts. The lift-off frames come about 1 s earlier.
    - **Direction agrees.** In the truth fit, flow_x rises with body-left velocity. With the vehicle heading north,
      a plateau of flow_x ≈ +0.6 therefore reads to the estimator as a WESTWARD drift, and the controller's
      correction pushes the vehicle EAST, as observed in both flights (the UKF flight's logged VE −0.083 against a
      true +0.091). The FGO flight's lift-off frames are all negative (mean −1.6 rad/s); they would have pushed it
      WEST, the opposite of what happened. The sign of the lateral coefficient is only weakly identified from p1c
      (fit coefficient 2.2, against the ≈ 1 expected).
    - **The timing and the direction therefore both point to the high-inlier climb plateau, not the lift-off frames,
      as the more likely driver of the B4 bursts.** This cannot be confirmed without a replay, which this stage did not run.
  - **Conclusion, plainly:** the pre-registered rule removes the low-inlier lift-off frames (all of the UKF
    flight's, and the two largest of the FGO flight's). **It does NOT remove the climb plateau, so on this evidence
    it is NOT a sufficient fix for D22.** r_min is not moved: the criterion was fixed before the data.
  - **Not pre-registered, offered for a user ruling:** the plateau has a high inlier ratio because RANSAC fits a
    similarity transform (`estimateAffinePartial2D`), and expansion during a fast climb is consistent with one. A
    plausible mechanism is image expansion acting on an off-centre feature set, so the MEDIAN feature displacement is
    biased. This is NOT verified (no images were inspected). Candidate fixes, all requiring a ruling:
    - (a) take the flow as the fitted transform's translation at the principal point, not the median displacement;
    - (b) reject frames whose fitted scale departs from 1 by more than a threshold (vertical motion);
    - (c) reject frames during the climb/descent phases on the rangefinder rate (|ż|/h above a threshold);
    - (d) require N consecutive valid frames after a re-detection (the plateau starts at a feature re-detection,
      feature count 30 → 52).
    - In p1c, the full-speed climbs show this plateau weakly or not at all: `p1c_fwdplainc_trans` has 2 frames
      (+0.57, +0.44), and `p1c_fwdc_tex` none.
- **FGO initial yaw σ (ruling 2026-10-10):** every SITL FGO flight so far (S3, the half-speed `_v3` corridor set, the
  FGO safety tests) flew the C++ node with an initial yaw σ of 1e-3 rad. **Before any real FGO flight:** the corrected
  node (initial yaw σ 1°, the same as the UKF) must pass its C++ equivalence checks and the SITL safety tests (a)/(b).
- **Estimator-loss trigger timing on the REAL FC (ruling 2026-10-11).** A bench test on the flight controller. With
  props off, stop the estimator's aiding input (flow) and time from the LAST flow message the FC received to the
  "position lost" trigger and the LAND mode change, from the FC's own log.
  - Pass: S-A2b ≤ 5.5 s (the supplementary criterion pre-registered 2026-10-11; S-A2 as worded stays for SITL).
  - In SITL the MAVProxy relay drain added 0.69–0.71 s after a kill; the real path has no MAVProxy relay. The bench
    measures this directly.
- **Companion computer: a Pi 5 is recommended** (2f, estimated). A Pi 4 would miss a 33 ms keyframe on the worst FGO
  solve spikes (~58–67 ms).
- **Attitude-only landing drifts (ruling 2026-10-09).** On estimator position loss, LAND flies the estimated level.
  A few tenths of a degree of attitude error drifts the vehicle > 1 m over the 4 s LAND pause plus the descent
  (SITL: 0.37–1.4 m). **Every hold point needs ≥ 2 m clearance to the watcher box in every direction.** The mocap
  watcher and the safety pilot (RC override) are the PRIMARY protection; the FC's own estimator-loss landing is a
  secondary layer.
- **No arming if the flight controller has rebooted since the estimator node started (ruling 2026-10-09).** The Pi
  node's clock map is built against one FC boot. The pre-arm check compares the FC boot identity (boot counter or
  `SYSTEM_TIME` boot time / the dataflash log index) recorded at node start with the current one. On a mismatch the
  node is restarted and its clock map must settle ("first state sent") before arming. **In flight**, a backwards
  step of the FC clock (time-reference sensor time, offset tracking error > 0.1 s, or a sent state time going
  backwards) latches the node's output INVALID, so the FC's estimator-loss landing trigger applies. Verified in SITL
  (`fly_trial.require_fgo_node_current`, `live_adapter` clock-integrity latch) before any real flight.
- **No frame change after arming (ruling 2026-10-09, after `H_ifa_ekf3`).** Under GUIDED with a stored position
  target, a frame change in flight sends the vehicle towards the OLD target expressed in the NEW frame (SITL: 2.25 m,
  19.2° tilt, watcher stop). ArduCopter's GUIDED sets this, not the estimator. Enforced for every estimator: the
  marker bridge releases no first fix once armed, the onboard backends refuse a first anchor once armed, EKF3's ExtNav
  alignment must complete pre-arm, and **arming is refused unless anchored: if the marker is not visible on the
  ground, the drone does not arm.** (EKF3's position reset after a > 10 s marker loss is a same-frame correction
  equal to the accumulated drift, not a frame change, and is not covered by this rule.)
- **Frame anchoring completes before arming (ruling 2026-10-08).** Every estimator that re-anchors to the marker/mocap
  frame must have anchored on the ground before arming (the vehicle placed where the marker is in view), and the FC must
  be receiving valid fixes. No frame change in flight. Gate it in the flight script, as `wait_fix` before arming.
- **EKF origin on every real flight (ruling 1, 2026-10-12).** Without an origin Copter's EKF failsafe never runs
  (`ekf_check.cpp:35-39`), and a no-origin EKF3 reports (0, 0) after an aiding loss (the SITL B8a runaway).
  - The origin is sent (or set by AHRS from `AHRS_ORIGIN_*`) only after EVERY EKF3 core has reported initialised.
  - It is verified by a `GPS_GLOBAL_ORIGIN` from the FC, and afterwards by an `ORGN` record in the log.
  - NO ARMING without it. The procedure is `docs/rung1_flight_cards.md` §1a.
- **F7 pre-arm yaw check (ruling 2, 2026-10-12).** The stock arming checks allowed arming with a 22° EKF yaw error,
  and the vehicle flew away on take-off (SITL wbench2, amendment A9).
  - **Rule.** While the FC is disarmed, the mocap watcher withholds its confirmation unless the FC's ATTITUDE yaw
    agrees with the mocap heading plus the tie within 5°, sustained ≥ 1 s, with mocap valid. With no confirmation it
    sends no heartbeat, so the FC cannot arm.
  - **Once armed** the check is informational only: it never lands the vehicle.
  - **The tie** is captured at the FC's EKF-origin broadcast (no compass), or is a surveyed constant (compass).
  - **Code and tests:** `realflight/watcher/yawcheck.py`; bench test B11 below; SITL `wbench3_f7`
    (`docs/handovers/2026-10-12_f7_cards.md`).
  - **Rung 1** has no watcher, so it is a manual card step there.
- **F8 mitigations M1–M3 (ruling 2026-10-12; none changes EKF3's configuration).** After a landing, EKF3's flow gate
  can lock one axis out on the ground while the other axis keeps the fall-backs off, so EKF3's velocity runs away
  while the vehicle sits still; no stock arming check sees it (F8, `docs/handovers/2026-10-12_f8_investigation.md`).
  - **M1:** power-cycle the FC before any re-arm after a landing, then the origin set and re-verified
    (`docs/rung1_flight_cards.md` §1a).
  - **M2 (watcher arming check):** while the FC is disarmed, the watcher withholds its confirmation unless the FC's
    `LOCAL_POSITION_NED` velocity (3-D norm of vx, vy, vz) stays < 0.2 m/s for 5 s continuously while the mocap shows
    the vehicle stationary (speed over a 0.5 s baseline < 0.05 m/s), with mocap valid and `LOCAL_POSITION_NED` fresh
    (≤ 0.5 s). Armed: informational only, never lands. No origin → no `LOCAL_POSITION_NED` → refused. Code:
    `realflight/watcher/velcheck.py`; bench test B12 below; SITL `wbench4_m2` (`docs/handovers/2026-10-12_m2_full_bench.md`).
    Rung 1: a manual card step.
  - **M3:** land in ALT_HOLD where safe; after any LAND-mode touchdown the safety pilot disarms within 2 s.
- **Physical:** prop guards, tether or net (question 7), conservative speed (0.25–0.5 m/s), the lowest workable
  height (≥ 1 m for the flow and range geometry), and a battery failsafe.
- **Staged bring-up:**
  1. Bench, with props off: all streams, rates, clock map, logging.
  2. Hand-carried, with motors off: the estimators against mocap.
  3. Tethered hover with EKF3.
  4. Shadow flights.
  5. Only then any route-1 flight.

### 7.2 Mocap watcher bench tests: PRE-REGISTERED (confirmed by the user 2026-10-10, for the camera-flow path), 2026-10-10

**Purpose:** prove on the real system, with the props off, that every path of the fail-closed rule (§7) acts. These
tests are part of stage 0 (§9.4). They are repeated at the start of every flight day (B0–B2, B10, and B11(a) and
B12(a) since 2026-10-12), and in full after any change to the watcher, the flight script, the FC firmware or its
failsafe parameters.

**What the bench can and cannot show:** the vehicle is on the ground, so these tests verify detection and the command
paths. On a landed, armed vehicle, ArduCopter's response to a failsafe is an immediate disarm
(`should_disarm_on_failsafe()` → `land_complete`, `events.cpp:463`), and LAND disarms on touchdown. "LAND or disarm"
is therefore the bench pass signal. The in-air landing behaviour is covered by the SITL tests (`H_safety_*`) and by
repeating B2 in the first tethered hover (§7).

#### 7.2.0 Not yet implemented for real hardware (each gates the test that needs it)

The SITL watcher (`sim/tools/wall_watch.py`) and the flight-script side (`fly_trial.py`: `watch_ok`,
`require_watcher_before_arming`, `check_watcher_in_flight`, `WatcherLost`) are verified in SITL only (METHODOLOGY
"fail-closed safety watcher"). Against the real system they lack the following:

| # | gap | needed for |
|---|---|---|
| G1 | **No mocap input.** The watcher reads Gazebo `/ground_truth/pose`. It needs the mocap rigid-body stream (e.g. VRPN or NatNet to ROS 2) in the mocap frame, aligned to the box definition. | all |
| G2 | **No stale-pose check.** The box and tilt rules are evaluated only when a pose ARRIVES, and the `box=1` flag is static, so a stopped mocap stream triggers nothing. §7 requires it to. | B5 |
| G3 | **No rigid-body identity check** (wrong body, or a swapped or renamed asset). | B6 |
| G4 | **The breach action stops the simulation** (SIGTERM to `fly_trial`/`run_trial`). On hardware it must command LAND over MAVLink (`SET_MODE`/`MAV_CMD_DO_SET_MODE` LAND), one-shot and latched, and alert the safety pilot (audible). | B4, B5, B9 |
| G5 | **No FC-side layer: the watcher sends no MAVLink HEARTBEAT, and no GCS-failsafe parameters are set.** The native mechanism needs no Lua: `FS_GCS_ENABLE` 5 (Land), `FS_GCS_TIMEOUT` 3 s (range 2–120; the default is 5), and `MAV_GCS_SYSID` set to the watcher's own system ID (`GCS.cpp:22`, `Parameters.cpp:101,838`). Verify the names on the real FC firmware. | B2b, B3 |
| G6 | **The FC will arm without a watcher.** `failsafe_gcs_check()` returns early if the GCS has never been seen (`events.cpp:133-136`). Without the flight script, nothing on the FC enforces "no watcher, no arming". Options: (i) procedure only (arm ONLY via the flight script; stick arming disabled with `ARMING_RUDDER` 0); (ii) a Lua arming-auth check that fails until the watcher's heartbeat is seen. Neither is implemented. | B1c |
| G7 | **Dependency liveness uses `pgrep`, which is local only.** The flow tracker, the bridges and the estimator node run on the Pi. A networked liveness signal is needed, such as topic rates seen over ROS 2 or a per-process MAVLink/ROS heartbeat. `pgrep` also misses a process that is alive but hung (SIGSTOP). | B9 |
| G8 | **`--dep-loss stop` has no hardware meaning.** In SITL it stops the simulation. On hardware both settings must end in LAND. Pre-registered: `stop` maps to LAND plus an alert (or the option is removed). | B9 |
| G9 | **The `watch_heartbeat` file is local.** That is valid only if the watcher and the flight script run on the same ground-station machine, which is pre-registered as a requirement. | B1, B2 |
| G10 | **The `--box` rule is x/y only.** It has no height limit (capture-volume top or ceiling). Add z_max, and z_min only for "below the floor" sanity. | B4 |
| G11 | **Heartbeat masking.** `handle_heartbeat` refreshes the GCS-failsafe timer for ANY HEARTBEAT, RC_OVERRIDE or MANUAL_CONTROL from a system ID in the GCS range (`GCS_Common.cpp:4231,4350,7671`; `sysid_is_gcs`). MAVProxy and pymavlink default to system ID 255 = the default `MAV_GCS_SYSID`. The watcher must therefore use a unique ID, and no other process may use it. Otherwise killing the watcher would not trip the FC. | B2b, B3 |

**Pre-registered settings for the tests:**
- stale-pose limit 0.5 s with no new mocap frame;
- watcher tick 1 s (as SITL);
- flight-script stale limit 3 s (`WATCH_STALE_S`, as SITL);
- `FS_GCS_TIMEOUT` 3 s;
- `FS_OPTIONS` keeps bit 4 (16, the default: "continue in pilot-controlled modes on GCS failsafe"), so the RC
  override wins (B10);
- `FS_EKF_ACTION` 1;
- for the bench session only, `DISARM_DELAY` 0, so an armed, landed vehicle in GUIDED does not auto-disarm during a
  test. It is restored and read back before any flight; the readback is recorded.

**Common setup (every test):**
- **Props physically removed,** checked by two people.
- The vehicle is on the bench inside the capture volume with mocap tracking. The ground station runs the watcher, the
  flight script and MAVProxy; the Pi runs the flow tracker, the bridges and the estimator node. The safety pilot holds
  the transmitter.
- **Logging:** dataflash with `LOG_DISARMED` 1 and `LOG_REPLAY` 1; the watcher's `STOP_LOG.txt`, track CSV and
  heartbeat log; the flight-script log; the MAVProxy tlog; the mocap recording.
- A parameter snapshot is taken before and after the session.
- All times are on the D24/D25 clocks: the FC `SYSTEM_TIME` map, and mocap ↔ FC via `eval/mocap_align.py`.

#### 7.2.1 Tests

Each test is given as setup / action / pass / recorded.

**B0. Control: everything up, so arming succeeds.**
- *Setup:* common. Watcher running with both checks active.
- *Action:* the flight script requests arming (GUIDED).
- *Pass:* the script logs "Safety watcher confirmed before arming", and the FC arms within 60 s. No other pre-arm
  failure occurs; one would invalidate B1.
- *Recorded:* the script log, the FC ARM event, and the watcher heartbeat (file and MAVLink, with its system ID).

**B1. No watcher → arming refused.**
- (a) Watcher not started; the flight script requests arming.
  - *Pass:* "REFUSING TO ARM: no watcher heartbeat", and no ARM event in the dataflash.
- (b) Watcher running, but a watched dependency is stopped (e.g. the flow tracker).
  - *Pass:* "REFUSING TO ARM: watcher not confirming (… bridge=0)".
- (c) Watcher not started; the safety pilot attempts to arm from the transmitter (with `ARMING_RUDDER` as configured
  for flight).
  - *Pass (G6):* the FC REFUSES. If it arms, the result is recorded as a FAIL of the FC side. Until G6(ii) exists, the
    rule "arm only via the flight script, with stick arming disabled" stands, and B1(c) is re-run with
    `ARMING_RUDDER` 0 to confirm that stick arming is impossible.
- *Recorded:* the script log, the dataflash ARM/ERR events, and the STATUSTEXT.

**B2. Watcher killed while armed → LAND/disarm.**
- (a) Both layers: armed (props off, GUIDED, landed); SIGKILL the watcher.
  - *Pass:* LAND or failsafe disarm within **4.0 s** of the kill (the 3 s stale limit plus the 1 s cadence; SITL
    measured ≤ 4 s). The layer that acted first is reported.
- (b) FC layer alone (G5): armed; SIGKILL the flight script first (the vehicle stays armed), then SIGKILL the watcher
  with every other process left running.
  - *Pass:* the FC's GCS failsafe acts within **3.5 s** of the kill (`FS_GCS_TIMEOUT` 3 s plus the check cadence).
  - This also proves that no other process refreshes the GCS timer (G11).
- *Recorded:* the kill time (ground-station clock), the dataflash FAILSAFE_GCS ERR and MODE/DISARM events with their
  reasons, and the STATUSTEXT.

**B3. Heartbeat loss with the watcher process alive.**
- (a) Link cut: armed; drop the watcher's MAVLink output (unplug its telemetry link, or block its UDP port), with the
  watcher still running.
  - *Pass:* FC GCS failsafe within **3.5 s**.
- (b) Watcher hung: armed; SIGSTOP the watcher (no file heartbeat and no MAVLink heartbeat), then SIGCONT after the
  test.
  - *Pass:* LAND/disarm within **4.0 s**, and no automatic re-arm or mode change after SIGCONT.
- *Recorded:* as B2.

**B4. Geofence breach, hand-carried → the configured action.**
- (a) Disarmed, props off: carry the vehicle out of the box through each side face and the top face (G10).
  - *Pass:* on each face, the watcher logs BREACH within **0.1 s** of the first mocap pose outside (on its own track).
  - It withdraws the confirmation: an arming attempt is then refused.
  - It sends ONE LAND command; the FC mode becomes LAND if accepted while disarmed, otherwise the command and its
    ACK are recorded.
- (b) Armed, props off, GUIDED: carry it out of one face.
  - *Pass:* LAND/disarm within **1.0 s** of the crossing.
- (c) Disarmed: tilt the vehicle past 60°.
  - *Pass:* BREACH ("tilt").
- (d) Box geometry check: place the vehicle at each planned hold point and laps corner.
  - *Pass:* ≥ 2 m clearance to every box face (§7 "attitude-only landing drifts").
- *Recorded:* the mocap log, the watcher track, BREACH.txt, the LAND command time, the FC MODE/DISARM events, and
  the measured box corners.

**B5. Mocap dropout / stale pose (G2).** *(RE-WORDED 2026-10-12 under ruling 4 of "RULINGS (user, 2026-10-12)",
METHODOLOGY; the old wording is kept verbatim below.)*
- **Watcher loop period, used in the bounds: 0.025 s.** The watcher evaluates staleness (and the frozen fallback) once
  per main-loop iteration. An idle iteration waits at most **0.02 s** in `select()` (`mocap_watch.py` `Watcher.run`;
  sooner when a packet arrives) and then does its own processing; the SITL bench measured maximum loop gaps of
  0.020–0.024 s (`max_loop_gap_s` in every `mocap_watch_summary*.txt` under `~/thesis_data/wbench/`,
  excluding B3b's deliberate 3.87 s SIGSTOP). The loop period is therefore taken as 0.02 s + 5 ms = 0.025 s. A
  declaration comes up to one loop period AFTER the limit is crossed.
- (a) Armed: stop the mocap stream (disable streaming, or the rigid body, in the mocap software).
  - *Pass:* the watcher declares the pose stale within the stale limit plus one loop period, **0.5 s + 0.025 s =
    0.525 s**, of the last frame, and acts (LAND command, MAVLink heartbeat stopped, confirmation withdrawn).
    LAND/disarm within **1.0 s** of the last frame.
- (b) Armed: occlude the markers until the mocap reports the body untracked.
  - Some systems keep sending the last pose, or a pose with a "not tracked" flag.
  - *Pass:* treated as stale, as in (a): with a tracking flag, LAND/disarm within **1.0 s** of the first untracked
    frame. Frozen (bit-identical) poses count as stale only if the mocap gives no tracking flag (state which applies);
    then the frozen pose is declared within the frozen limit plus one loop period, **0.5 s + 0.025 s = 0.525 s**, of
    the first frozen frame, and LAND/disarm follows within **1.0 s** of it.
- **Old wording (2026-10-10, pre-registered), kept verbatim:**
  > - (a) Armed: stop the mocap stream (disable streaming, or the rigid body, in the mocap software).
  >   - *Pass:* the watcher declares the pose stale within **0.5 s** of the last frame and acts (LAND command, MAVLink
  >     heartbeat stopped, confirmation withdrawn). LAND/disarm within **1.0 s** of the last frame.
  > - (b) Armed: occlude the markers until the mocap reports the body untracked.
  >   - Some systems keep sending the last pose, or a pose with a "not tracked" flag.
  >   - *Pass:* treated as stale, as in (a). Frozen identical poses for 0.5 s count as stale only if the mocap gives no
  >     tracking flag (state which applies).
- **Why it was re-worded:** the old bound (0.5 s) EQUALLED the watcher's stale limit (`--stale-s 0.5`) and frozen
  limit (`frozen_s` 0.5), and the rule is "stale when OLDER than the limit", checked once per loop, so a declaration
  can never come at or before 0.5 s: it could not be met by a correctly working watcher. The SITL bench
  (`docs/handovers/2026-10-11_watcher_sitl_bench.md` finding F5) declared stale at +0.508 s (B5a) and frozen at
  +0.510 s (B5b-noflag), and LAND reached the FC at +0.559 / +0.562 s. NO real (hardware) bench run had happened when
  this was re-worded, so no hardware result is re-scored. The SITL values meet the new wording; that is a POST HOC
  observation (the new bound was written after they were seen) and they stay verification data only. The watcher and
  its limits are unchanged; the 1.0 s LAND bound is unchanged.
- (c) Disarmed: restore the stream.
  - *Pass:* the confirmation returns only after ≥ 2 s of continuous fresh poses. No automatic action follows.
- *Recorded:* the mocap frame times, the watcher stale-detection log, the commands and the FC events.

**B6. Wrong body / rigid-body ID (G3).**
- *Setup:* watcher started with a different rigid body (a second tracked object, or a renamed asset), disarmed.
- *Action:* move the real vehicle by hand (roll/pitch about 10°, yaw 90°).
- *Pass:* the watcher withholds the confirmation (arming refused), because its identity check fails:
  - the mocap roll/pitch must agree with the FC `ATTITUDE` within 5°;
  - a hand yaw of 90° must appear in the mocap yaw within 10° and within 1 s;
  - with the correct body configured, the same check passes.
- *Recorded:* both runs' check values and the script log.

**B7. Clock and latency.**
- (a) mocap → watcher: the mocap frame stamp against the watcher receipt time (mocap PC and ground station synced by
  chrony/PTP; the sync offset reported).
  - *Pass:* median ≤ 50 ms, p99 ≤ 100 ms.
- (b) watcher command → FC: the LAND command send time against the FC MODE event (via the `SYSTEM_TIME` map) and
  against the received STATUSTEXT/HEARTBEAT mode.
  - *Pass:* p99 ≤ 0.3 s over ≥ 10 commands (issued disarmed, or in B4/B5).
- (c) mocap ↔ FC: hand-rotate the vehicle sharply 5 times and align with `eval/mocap_align.py` (|ω| from mocap
  against the FC gyro).
  - *Pass:* the residual offset scatter ≤ 10 ms. The fitted offset and rate are recorded and used for scoring.
- *Recorded:* the latency distributions, the sync offset, and the mocap_align output.

**B8. Estimator invalid → FS_EKF_ACTION path (the open item in §7).** Per flying estimator, armed (props off,
GUIDED).
- **Isolation from the watcher (required, or the test measures the watcher instead):** on a landed vehicle, any LAND
  disarms at once, and `thesis_nav_check` returns when disarmed. So for B8:
  - the processes killed are NOT in the watcher's `--watch-process` list;
  - the watcher's heartbeat (file and MAVLink) stays up throughout;
  - the watcher, the flight script and the GCS failsafe must therefore not act.
  - If any of them acts first, the run is void and repeated.
- **Precondition, with a fixed fallback order (not left open):**
  - EKF3 zeroes the flow before take-off below 0.5 m (`AP_NavEKF3_OptFlowFusion.cpp:45-48`), and the UKF port has
    its own ground-proximity rule (`AP_NavUKF.cpp:593`). The estimator under test may therefore not report a relative
    position (`HORIZ_POS_REL`) while landed. The thin-backend trigger needs it to have done so since arming.
  - Check `HORIZ_POS_REL` (EKF_STATUS_REPORT / the dataflash) in this order, using the first that works:
    1. on the bench, landed;
    2. hand-held, armed, props off, camera ≥ 0.6 m above the floor, marker in view;
    3. otherwise B8(b)/(c) move to the FIRST TETHERED HOVER of that estimator's stage, before any free flight, with
       the safety pilot ready.
  - The level used is recorded. On the bench a failsafe disarms rather than lands (`should_disarm_on_failsafe`).
- (a) **EKF3** (`AHRS_EKF_TYPE` 3): stop the flow bridge and the tag/ExtNav bridge.
  - *Expected from SITL `H_safety_ekf3_ref`:* EKF3 raises NO failsafe; it keeps a dead-reckoned position.
  - *Pass:* recorded as report-only. The protection is the watcher's dependency loss (B9).
- (b) **UKF port** (`AHRS_EKF_TYPE` 12): kill EVERY aiding input, as in SITL UKF (b) (`H_safety_ukf_b`: tag bridge and
  flow bridge): the Pi flow bridge, the tag bridge, and the heading bridge if it is running. Killing the flow bridge
  alone would leave the ExtNav fixes from the marker in view keeping the position alive.
  - *Pass:* "Thesis nav: UKF position lost" (`ekf_check.cpp:355`, `thesis_nav_check`) and LAND/disarm (reason
    EKF_FAILSAFE) within **5.5 s of the LAST aiding message received by the FC**. That is the later of the last `OF`
    row and the last ExtNav (`VISP`) row in the dataflash; the UKF's aiding timeout is 5 s.
  - The kill → last-received drain is reported separately (SITL: 0.08–0.71 s; METHODOLOGY UKF (b) re-test).
- (c) **FGO port** (`AHRS_EKF_TYPE` 13): kill the FGO node.
  - *Pass:* "Thesis nav: FGO position lost" and LAND/disarm within **0.75 s** of the last state received (as SITL
    `H_safety_fgo_a_v3`/`_b_v3`).
- (d) For (b) and (c), the attitude stays valid through the event: `ATT` continues with no freeze, and agrees with
  the mocap attitude within the SITL S-A1 bound.
- (e) Repeat (b)/(c) in ALT_HOLD: NO mode change is expected (`FS_EKF_ACTION` 1 acts only in modes that need a
  position, `ekf_check.cpp:190`). This is part of B10.
- *Recorded:* the HORIZ_POS_REL level used, the dataflash STATUSTEXT, ERR (EKFCHECK, FAILSAFE_EKFINAV), MODE/DISARM
  events, the `OF`/`VISP`/ODOMETRY arrival times, and `ATT` against mocap.

**B9. Dependency loss (`--dep-loss land|stop`; G7, G8).** Armed. For each watched dependency in turn (flow tracker,
flow bridge, tag/heading bridge, Pi estimator node, and the flight script, if it is added as a dependency):
- (a) SIGKILL it with `--dep-loss land`.
  - *Pass:* the watcher withdraws its confirmation within **1.5 s** (1 s tick), and stops its MAVLink heartbeat.
  - LAND/disarm within **2.5 s** of the kill. SITL measured LAND at +1.25 s (`H_safety_ekf3_ref`).
- (b) The same with `--dep-loss stop`.
  - *Pass:* the same LAND/disarm. On hardware `stop` must not mean "stop the processes" (G8).
- (c) SIGSTOP it (alive but silent).
  - *Pass:* detected by the networked liveness check (G7) and handled as (a). A `pgrep`-only watcher FAILS this case
    by design, which is why G7 is required.
- (d) Disarmed, with a dependency down.
  - *Pass:* arming refused (as B1b).
- *Recorded:* the kill time, the watcher detection time, the commands and the FC events, per dependency.

**B10. RC override takes precedence.** Armed, GUIDED:
- (a) The safety pilot switches to ALT_HOLD (and, separately, STABILIZE).
  - *Pass:* the FC mode changes within **0.3 s**, and the flight script's GUIDED commands have no effect afterwards.
- (b) In ALT_HOLD, trigger each automatic path in turn: watcher kill (B2b), estimator invalid (B8e), dependency loss
  (B9a).
  - *Pass:*
    - the GCS failsafe and the EKF failsafe make NO mode change (`FS_OPTIONS` bit 4; `FS_EKF_ACTION` 1);
    - the watcher and the flight script send at most ONE LAND (latched);
    - if that LAND is accepted, the pilot regains ALT_HOLD by toggling the mode switch within 1 s, and nothing
      re-commands LAND afterwards.
- (c) Transmitter off (RC failsafe).
  - *Pass:* the configured `FS_THR_ENABLE` action, here disarm on the ground.
- *Recorded:* the RC input (`RCIN`), the MODE events with their reasons, and the commands sent.

**B11. F7: estimator yaw disagrees with the mocap → arming refused (the watcher yaw check).** *(Added 2026-10-12 under
ruling 2 of "RULINGS (user, 2026-10-12, safety first)", METHODOLOGY. Pre-registered here before any hardware run; the
SITL version is `wbench3_f7`, `docs/handovers/2026-10-12_f7_cards.md`.)*
- *Setup:* common, disarmed, props off.
  - The watcher runs with `--yaw-check require` and the session's tie: `--yaw-tie origin` (no compass), or the surveyed
    `--yaw-tie <deg>` (compass).
  - The power-on procedure (`docs/rung1_flight_cards.md` §1a) is complete: the origin is verified and the tie
    recorded. With `origin`, the watcher must be running before the FC boots.
  - The Lua arming-auth script is installed if G6(ii) is in use (`--lua-auth`).
- **Why the stimulus is on the mocap side:** a real carry is sensed by the gyros, so F7's mechanism (a rotation the FC
  never sees) cannot be produced on hardware. A disagreement is created instead by giving the watcher a tie 10° off
  the recorded one.
- (a) **Control (also daily).** At rest, |diff| ≤ 5°: the watcher confirms, and the flight script arms as in B0.
  Disarmed again, hand-yaw the vehicle +90°, HOLD IT STILL there for ≥ 5 s, then turn it back.
  - *Pass:* |diff| ≤ 5° and the watcher confirmed at rest before the turn, **while held at +90° (for ≥ 2 s of the
    hold)**, and after the turn back. Any withdrawal while the vehicle moves is recorded (the 0.3 s FC-latency allowance
    should absorb a hand-speed turn); it must clear within 5.0 s of the vehicle coming to rest.
  - **Why the hold at +90°:** this is the first end-to-end test of the comparison's SENSE and axes under a rotation the
    FC senses. Every SITL stimulus (`wbench3_f7`) was a rotation the gyros never saw. A wrong heading sense, or a wrong
    up-axis or body offset (`frames.py` calls these hardware-dependent), would show as |diff| ≈ 180° at +90° and ≈ 0°
    again after the return. A pass on "before and after" alone would therefore miss it.
- (b) **Disagreement → refused.** Restart the watcher with `--yaw-tie <recorded tie + 10>`. (A fixed tie is used here
  even in the no-compass case: an `origin` watcher restarted within a boot never re-ties.)
  - *Pass:*
    - it never confirms, and its reason is "yaw … disagree (diff ≈ 10 deg > 5.0)";
    - after ≥ 5 s, a non-force MAVLink arm from the GCS is REFUSED. The FC refuses with "GCS failsafe on" if the
      watcher was seen earlier in this boot, otherwise with the Lua "Watcher: never seen" / "heartbeat … old";
    - the flight script logs "REFUSING TO ARM: watcher not confirming";
    - the watcher sends NO LAND and logs no BREACH.
  - Then restart it with `--yaw-tie <recorded tie>`.
  - *Pass:* it confirms within **5.0 s** of seeing the FC attitude, and the flight script arms (after the FC's "GCS
    Failsafe Cleared").
- (c) **Mocap invalid → refused.** Disarmed and confirmed: occlude the markers until the body is reported untracked,
  then restore them.
  - *Pass:* the confirmation is withdrawn, with "yaw mocap pose not valid" among the reasons, and it returns only after
    ≥ 2 s of fresh poses and ≥ 1 s of yaw agreement.
- (d) **Origin tie path** (no-compass sessions only).
  - Start an `origin` watcher AFTER the FC has booted and set its origin. *Pass:* it never confirms ("no tie yet").
  - Reboot the FC with the watcher running. *Pass:* it logs "tie … captured at the EKF-origin broadcast", and the tie
    agrees within 5° with the GS's §1a step-5 value. It confirms.
- **Armed (informational only):** the no-LAND property under a REAL disagreement is not tested on hardware. A
  disagreement cannot be created while armed without a fault injection. It is covered by the unit tests and by SITL
  `wbench3_f7` F7-d. On the bench, B0/B2 confirm only that an armed, agreeing vehicle keeps its confirmation.
- *Length:* ground only, ~5 min. Each response is expected within ~1.5 s, and a restart and its re-tie within ~10 s.
- *Recorded:* the watcher's `STOP_LOG.txt` and `mocap_watch_yaw.csv` (the FC yaw, the mocap heading, the tie and the
  difference at 25 Hz); the tie on the sheet; the FC STATUSTEXT and ARM events; the flight-script log.

**B12. M2: EKF velocity not settled, or the vehicle not still → arming refused (the watcher velocity check).** *(Added
2026-10-12 under "RULING (user, 2026-10-12): F8 mitigations M1, M2, M3 APPROVED", METHODOLOGY. Pre-registered here
before any hardware run; the SITL version, including a real EKF3 ground runaway, is `wbench4_m2`,
`docs/handovers/2026-10-12_m2_full_bench.md`.)*
- *Setup:* common, disarmed, props off. The watcher runs with `--vel-check require` (and the B11 yaw check). The
  power-on procedure (`docs/rung1_flight_cards.md` §1a) is complete, so the FC sends `LOCAL_POSITION_NED`.
- **Why the stimuli are not an EKF runaway:** F8 needs a landing (a touchdown with a velocity error, then the ground
  gate lock-out). With the props off there is no landing, so a real runaway cannot be produced on the bench. The SITL
  `wbench4_m2` test produces one. Here the refusal path is driven by the vehicle's motion and by a lowered threshold,
  as B11(b) uses an offset tie.
- (a) **Control (also daily).** At rest: the watcher confirms ≥ 5 s after the last motion; its
  `mocap_watch_vel.csv` shows |v| < 0.2 m/s throughout; the flight script arms as in B0. *Recorded:* the at-rest
  maximum |v| (expected ≪ 0.2: SITL ≤ 0.08 m/s on the ground before every first arm).
- (b) **Not still → refused.** Disarmed and confirmed: carry the vehicle by hand ~1 m at walking speed and set it down.
  - *Pass:* the confirmation is withdrawn while it moves, with "vel vehicle not stationary" (or "EKF velocity …") among
    the reasons; the watcher sends NO LAND and logs no BREACH; it re-confirms only ≥ 5.0 s after the vehicle is set
    down (mocap), and within 8.0 s of it if the EKF velocity has settled.
- (c) **Velocity over the limit → refused.** Restart the watcher with `--vel-max 0` (every velocity sample is then at
  or over the limit).
  - *Pass:* it never confirms, its reason is "vel EKF velocity |v| … >= 0.0"; after ≥ 5 s a non-force MAVLink arm from
    the GCS is REFUSED ("GCS failsafe on", or the Lua "Watcher: …" text); the flight script logs "REFUSING TO ARM:
    watcher not confirming"; NO LAND, no BREACH. Then restart it with the default `--vel-max 0.2`. *Pass:* it confirms
    within 8.0 s and the flight script arms (after the FC's "GCS Failsafe Cleared").
- (d) **No origin → refused.** Reboot the FC with the watcher running and do NOT set the origin for 20 s.
  - *Pass:* no confirmation, the reason "vel no LOCAL_POSITION_NED from the FC"; then set and verify the origin (§1a):
    it confirms.
- **Armed (informational only):** not testable with the props off (an armed vehicle on the bench has ~0 velocity).
  Covered by the unit tests (`realflight/watcher/tests/test_vel.py`) and SITL `wbench4_m2`.
- *Length:* ground only, ~4 min. Each response is expected within ~1 s; each re-confirmation needs the 5 s hold.
- *Recorded:* `STOP_LOG.txt`, `mocap_watch_vel.csv` (vx, vy, vz, |v|, the mocap speed, the hold time, the verdict at
  the `LOCAL_POSITION_NED` rate), the FC STATUSTEXT and ARM events, the flight-script log.

**Pass rule for stage 0:** every test passes as worded, or a deviation is recorded and ruled on before stage 1. B1(c)
and G6 may be closed by the procedure rule plus `ARMING_RUDDER` 0 only with an explicit ruling.

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
- the mocap watcher bench tests B0–B10 (§7.2, PRE-REGISTERED pending confirmation), with gaps G1–G11 closed first;
- the flow-validity real-camera check (§7.1: ≥ 99% of count-valid frames over the flight floor keep `inlier_ratio >= 0.85`).

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
