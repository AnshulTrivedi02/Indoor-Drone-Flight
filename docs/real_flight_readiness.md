# Real-flight readiness checklist

Status: PLANNING ONLY. Written 2026-10-10 on `fwd-camera` at `4556714`, after the ruling "REORDER, real-flight
readiness first" (METHODOLOGY, last entry). Nothing was run, built or changed to produce it. It complements
`docs/real_flights_plan.md` (the design and staging; another agent is pre-registering its §7 items now) and
`docs/real_flights_pi_readiness.md` (the ARM heading build). It does not replace either.

## Scope: the two flight types

- **(a) Open-loop logging flight.** EKF3 flies (route 3, plan §2). The UKF and FGO are not in the loop. Every sensor
  stream is logged so that the UKF and FGO can be replayed offline and scored against mocap. Offline scoring is labelled
  "not real-time" (plan §9.3).
- **(b) Closed-loop UKF/FGO flight** (route 1, plan §2). Either the onboard UKF port (`AP_NavUKF`, `AHRS_EKF_TYPE 12`)
  or the C++ FGO node on the Pi through the thin backend (`AP_NavFGO`, `AHRS_EKF_TYPE 13`) is the flying estimator.

## Status categories (applied strictly; exactly one per row)

| status | meaning here |
|---|---|
| **exists and tested in SITL** | Built and run end to end in SITL in the role it will have on the vehicle. What remains is hardware confirmation only. |
| **exists but untested on hardware** | Built and self-tested, but never exercised in its flight role. Examples: the qemu-only ARM build, `mocap_align.py`, the `real_camera` self-tests. |
| **needs adapting for real sensors** | Works in SITL, but carries simulator assumptions: UDP ports, `use_sim_time`, hard-coded sim geometry, sim-only parameters. |
| **not built** | No code, file or procedure exists yet. |

Effort is for one person. It assumes the hardware is in hand and assembled, unless a row says otherwise. "d" means a
working day. Every estimate is [E].

---

## 0. Required inputs from the user (unknown; not assumed)

These identities change several rows below. Each is listed again under "Open questions".

| # | unknown | rows it changes |
|---|---|---|
| U1 | **Flight-controller board.** Part C §5 assumed an STM32H743 (Pixhawk 6X or CubeOrange). The UKF port uses `double` state and covariance, so the board needs a hardware double FPU (H7 class). | G1a, G1b, G2, C1 |
| U2 | **Vehicle type.** Copter, or ArduPlane QuadPlane in Q modes (Part C scope)? `thesis_nav_check` exists only in `ArduCopter/`. | G1b, G4, H10 |
| U3 | **Companion computer.** Pi 4 or Pi 5? RAM? Cooling? | A4, G8 |
| U4 | **Downward camera and lens.** Interface: CSI/libcamera or USB/V4L2. Global or rolling shutter. | A3, D1, D3, D4 |
| U5 | **Forward camera and lens**, if flown. | A6, D2, D6 |
| U6 | **Rangefinder model and interface.** Serial/I²C to the FC, or read on the Pi. Minimum range. | A8, A9, C2 |
| U7 | **Mocap system.** Vicon or OptiTrack. Rate. Streaming protocol (VRPN/NatNet). Time source (PTP/NTP). Capture-volume size. | F1, I3, I4, H9 |
| U8 | **Airframe.** Frame size, prop guards, battery, RC transmitter and receiver, telemetry radio. | A1, A2, H5 |
| U9 | **UKF placement** (plan question 2): onboard the FC (the port) or on the Pi. | G1b, G10 |

---

## 1. Checklist

Columns: **ID** · **component** · **status** · **needed by** · **evidence** · **effort (assumption)** · **depends on**.

### A. Vehicle, sensor drivers and bridges

| ID | component | status | needed by | evidence | effort (assumption) | depends on |
|---|---|---|---|---|---|---|
| A1 | Airframe, FC, Pi and sensors assembled and wired: FC↔Pi UART, cameras, LiDAR | not built | a, b | Plan question 3 is still open. No hardware is described anywhere in the repo. | 2–4 d (parts in hand). Procurement time is unknown. | U1–U8 |
| A2 | Baseline vehicle tune on the stock image: manual hover, `MOT_THST_HOVER` learned, harmonic notch, rate gains (Autotune in ALT_HOLD) | not built | a, b | The SITL values do not transfer: `h_extnav.parm` `MOT_THST_HOVER 0.310` (SITL iris), `roll_rate_gains.parm` (SITL). METHODOLOGY "`MOT_THST_HOVER` pinned". | 1–2 d of flying (safety pilot, net) | A1, G1a, H5 |
| A3 | Downward-camera capture on the Pi, publishing `/downward_camera/image` and `camera_info` with **sensor capture stamps** at 30 Hz | not built | a, b | `flow_tracker.py` subscribes to `/downward_camera/image`, which is today the Gazebo bridge. `real_flights_pi_readiness.md` §2.3 lists capture as [U]. | 1–2 d (assumes a ROS 2 Jazzy camera driver exists for the chosen camera on arm64) | A1, U4 |
| A4 | `flow_tracker.py` (Shi-Tomasi + LK + RANSAC) on the Pi CPU: rate, latency, `use_sim_time` off | needs adapting for real sensors | a, b | `FOCAL_LENGTH_PX = 554.0` is hard-coded (`flow_tracker.py:16`). Validity uses the feature count only (`:313`). Pi timing is unmeasured (plan §6, "must be timed"). | 1–2 d. **+3–5 d** if 640×480 Python misses 33 ms on the Pi (C++ port, or 320×240, which changes the measurement and must be stated) | A3, D1, E1 |
| A5 | `flow_bridge.py` → `OPTICAL_FLOW` to EKF3 over the real link | needs adapting for real sensors | a, b | UDP port 14553 via MAVProxy (`flow_bridge.py:80`). The sign is now `flow_rate_x = +flow_x_rad` (`:27-31`, 2026-09-29 finding); it must be re-verified on the real mount (D5). | 0.5 d | B1, D5 |
| A6 | Forward camera: capture plus the C++ heading program on the Pi | exists but untested on hardware | b (heading arms); a only if the forward camera is flown | ARM64 build checked under qemu only: 205/205 integer outputs identical, \|Δψ\| ≤ 1.25e-5° (`real_flights_pi_readiness.md` §1). Native run and capture are [U]. **The supervisor rule is that the forward camera flies only once verified.** | 1 d native check and timing, plus capture (shared with A3) | A3, D2, D6, U5 |
| A7 | Wall-tag detector (`tag_bridge.py`, pupil_apriltags) on real images; `ODOMETRY` to EKF3 ExtNav; the same fixes to the UKF/FGO | needs adapting for real sensors | a, b if P-HOLD is the profile | Uses UDP 14557, i.e. SITL SERIAL1 (`tag_bridge.py:35,68`). `tag_hold_design.md` "Transfer to the real mocap room" requires S0 (validity rule and σ) to be repeated on real images. | 1 d port/link, plus D7 | A6 capture, B1, D7 |
| A8 | Rangefinder on the vehicle: a native FC driver (`RNGFND1_TYPE` per model), or read on the Pi and injected as `DISTANCE_SENSOR` (the SITL pattern) | not built | a, b | `lidar_rangefinder.parm` is `TYPE 10` (MAVLink), `MIN 0.05`, `MAX 40` (gpu_lidar values). The sim LiDAR rests at 0.075 m, below many real LiDAR minimums. The D23 short-return artefact must be characterised on the real airframe (plan §3). | 0.5–1 d | A1, U6 |
| A9 | Range to the Pi for the UKF/FGO: FC `DISTANCE_SENSOR` telemetry → `/downward_lidar/range` republisher (if the LiDAR is on the FC) | not built | b live; a can instead use dataflash `RFND` offline | Today `lidar_bridge.py` goes the other way (ROS → FC). | 0.5 d | A8, B1 |
| A10 | IMU stream: `HIGHRES_IMU` 333 Hz from a real FC serial port → `imu_bridge.py` → `/imu/data_raw` + `/imu/time_ref` | needs adapting for real sensors | a (offline replay inputs), b | 333 Hz is the 0.8 × `SCHED_LOOP_RATE` cap, verified in SITL (CLAUDE.md "IMU Bridge"). SITL feeds it on `--serial2` UDP 14556. Bandwidth at 921 600 baud ≈ 25 of 92 kB/s [E] (plan §3). Drops on a real UART are [U]. Keep `SCHED_LOOP_RATE 400`. | 1 d bench: rate, drops, `time_usec` monotonicity | B1 |

### B. MAVLink link, port layout and clocks

| ID | component | status | needed by | evidence | effort (assumption) | depends on |
|---|---|---|---|---|---|---|
| B1 | FC↔Pi physical link and port layout replacing the SITL UDP ports. **SITL layout today:** 14550 `fly_trial`; 14551 attitude; 14552 LiDAR; 14553 flow; 14554 EKF pose (all MAVProxy `--out`); 14556 IMU (SERIAL2); 14557 heading/tag (SERIAL1); 14558 FGO node (SERIAL3; `run_trial.sh:144-300`). **Proposal:** one or two FC TELEM ports at 921 600 baud (`SERIALn_PROTOCOL 2`), with a router on the Pi re-exposing the same UDP ports so that the bridges stay unchanged. | not built | a, b | No serial endpoint exists in any bridge or node. Every bridge uses pymavlink `udp:`. The C++ node uses `UdpEndpoint` only (`fgo_cpp_node.cpp:9-10,80`). | 1 d, assuming a router; plus 0.5 d per bridge that has to talk serial directly instead | A1 |
| B2 | FC↔Pi clock map: D25 robust low-percentile envelope on `/imu/time_ref`; boot-identity pre-arm check; in-flight clock-integrity latch | exists and tested in SITL | a (offline alignment), b (live) | D25; `docs/handovers/2026-10-08_fgo_cpp_timeref_fix.md` (live check `fgo_cpp_shadow_ii_fix` ALL PASS); ruling 2026-10-09 "FC soft-reboot" (`require_fgo_node_current`, `live_adapter` latch). Real crystal drift is [U] (SITL ran 0.02% slow). | 0.5 d bench: settle time, drift, `TIMESYNC` cross-check | B1, A10 |
| B3 | Measured link latency distribution (one-way, jitter) for every Pi→FC stream | not built | b (feeds H2); a (report) | Plan §9.2 starts at 5–15 ± 3 ms [E], "to be replaced by the bench-measured distribution". | 0.5 d | B1 |
| B4 | Pi time base: `use_sim_time:=false` and wall-clock ROS time on every node; no `/clock` | needs adapting for real sensors | a, b | Every launch line uses `use_sim_time:=true` (CLAUDE.md "Launch Sequence"; `run_trial.sh`). | 0.5 d | A3, A10 |

### C. Parameter files with real sensor values

The current `.parm` files are SITL-specific. A new versioned `real_*.parm` set is needed. Parameters are restored from a
dump plus the file after every flash, with `ensure_params` readback, because the eeprom gotcha (Known Issue #10) applies
on a real FC too.

| ID | component | status | needed by | evidence | effort (assumption) | depends on |
|---|---|---|---|---|---|---|
| C1 | Core real-FC parameter file: EKF3 sources from `gnss_denied.parm` and `gnss_denied_nomag.parm` (`EK3_SRC1_POSXY 0`, `POSZ 2`, `VELZ 0`, `YAW 0`, `GPS1_TYPE 0`, compass present but unused); `FS_EKF_ACTION` LAND; battery failsafe; RC mode switch; `LOG_*` (I1) | not built | a, b | **Hazards in the current files:** (1) `consolidated_rerun.parm` carries `AHRS_EKF_TYPE 10` (SITL truth), so it must never load on a real FC; (2) `SIM_GPS1_ENABLE` (in `gnss_denied.parm`) and all of `sim_noise.parm` do not exist on hardware; (3) `COMPASS_ENABLE 1` with `USE 0` still needs a calibrated, healthy compass to arm (`AP_Arming_Copter.cpp:575`), and an indoor steel environment may fail that check. | 1 d, plus a bench readback | G1a, U1 |
| C2 | Rangefinder parameters: `RNGFND1_TYPE`, `ORIENT 25`, `MIN`, `MAX`, `POS_X/Y/Z`, `GNDCLEAR` | needs adapting for real sensors | a, b | `lidar_rangefinder.parm` (`TYPE 10`, `0.05`/`40`, `POS_Z 0.12`, all sim values). | 0.5 d | A8 |
| C3 | Flow parameters: `FLOW_TYPE 5`, `FLOW_POS_X/Y/Z`, `FLOW_ORIENT_YAW`, `EK3_FLOW_DELAY` | needs adapting for real sensors | a, b | **`FLOW_POS_Z` conflicts in SITL: 0.13 in `flow_ekf.parm`, overridden to 0.25 in `consolidated_rerun.parm`.** One measured real value replaces both. `EK3_FLOW_DELAY` is the default 10 ms (METHODOLOGY:1609, 4992). | 0.5 d, plus D4 | D3, D4 |
| C4 | ExtNav parameters for the tag and heading paths: `VISO_TYPE 1`, `EK3_SRC1_POSXY/YAW 6`, `VISO_POS_M_NSE`, `VISO_YAW_M_NSE`, `VISO_DELAY_MS`, `ARMING_SKIPCHK 262144` | needs adapting for real sensors | a, b if P-HOLD (or forward heading) is flown | `h_extnav.parm` (`VISO_DELAY_MS 31`, `POS_M_NSE 0.02` from S0), `tags_extnav.parm` (15 ms), `closedloop_heading*.parm` (38/25 ms): all measured in SITL by the D2/D20 procedure. | 0.5 d, after D4 and D7 | D4, D7 |
| C5 | `MOT_THST_HOVER` and `MOT_HOVER_LEARN`; attitude gains | needs adapting for real sensors | a, b | `h_extnav.parm` pins 0.310 with `MOT_HOVER_LEARN 1` (SITL iris). | in A2 | A2 |
| C6 | Sensor noise and filters: INS filters (`INS_GYRO_FILTER`/`INS_ACCEL_FILTER` 20 Hz in SITL), harmonic notch, vibration (`VIBE`); EKF3 `*_NSE` | needs adapting for real sensors | a, b | The UKF/FGO noise matching assumes EKF3's default `*_NSE` and dt 0.0125 s (CLAUDE.md "GTSAM IMU Preintegration"). That still holds if `SCHED_LOOP_RATE` stays 400 and the `*_NSE` stay default. Notch and filter settings change what `HIGHRES_IMU` delivers to the UKF/FGO, so they are recorded per flight. `sim_noise.parm` has no hardware meaning. | 0.5 d (record; no retuning of the `*_NSE`) | A2 |
| C7 | Estimator geometry constants, **hard-coded in three implementations**: `RANGE_LEVER 0.12` and `CAM_OFFSET 0.25` in `measurement_models.py:32-33`, `factors.h:28-29` and `AP_NavUKF.cpp:33`; a bare literal `first_range + 0.12` at `fgo_core.cpp:69`; port `RNG_MIN 0.05`, `RNG_MAX 40` (`AP_NavUKF.cpp:29`); `FOCAL_LENGTH_PX 554.0` | needs adapting for real sensors | a (offline replay), b | As listed. A change to any of them must re-pass the C++-vs-Python band (`docs/fgo_cpp_port.md`) and port tier B (`docs/h_backends_tag_input.md` §1.2) with sim values (no-op check), before the real values are set. | 1–2 d to parametrise, plus 1 d of equivalence re-runs | D3 |
| C8 | Fork parameters: `AHRS_EKF_TYPE 12/13`, `AHRS_UKF_ENABLE/EXTYAW/EXTPOS/TFAIL`, `AHRS_FGO_ENABLE`, `SERIALn_PROTOCOL` for the node | exists and tested in SITL | b | `closedloop_ukf.parm`, `closedloop_fgo.parm`, `h_ukf_tag.parm`. **`AHRS_UKF_TFAIL` (a test hook) has persisted in eeprom before** (METHODOLOGY "H safety UKF (a), attempt 3"). It must be 0 and must be in `ensure_params` on hardware. | 0.5 d | G1b |

### D. Calibration and re-validation

| ID | component | status | needed by | evidence | effort (assumption) | depends on |
|---|---|---|---|---|---|---|
| D1 | Downward-camera intrinsics and distortion: focal length for the px/s → rad/s conversion | exists but untested on hardware | a, b | `tools/real_camera/calibrate.py`. Self-test `selftest_calibration.py` passed (fx within 0.15%, k1 within 0.0012; README). Never run on a real lens. | 0.5 d | A3 |
| D2 | Forward-camera intrinsics, undistortion and resampling onto the frozen simulated camera (640×480, fx 554.38) | exists but untested on hardware | b (heading arms); a if flown | `tools/real_camera/run_heading_video.py`. A PNG round trip reproduced Phase 3's headings to 2.4e-14° (README). | 0.5–1 d | A6 |
| D3 | Camera–IMU (and LiDAR–IMU) extrinsics: lever arms; downward-camera rotation about z (sets the flow axes); forward-camera yaw offset (a heading bias) | not built | a, b | There is no tool. The simulated mounts are ideal (CLAUDE.md "Drone Model"). | 1–2 d (tape measure plus a mocap rotation and hover check) | A1, I3 |
| D4 | Camera–FC time offsets: `EK3_FLOW_DELAY`, `VISO_DELAY_MS` (D2/D20 receipt rule), the flow capture stamp | needs adapting for real sensors | a, b | The D2/D20 procedure exists and was used in SITL (D20; `tags_extnav.parm`). On hardware the capture-to-receipt latency is new (plan §9.4 stage 0). | 1 d bench | A3, B2 |
| D5 | Flow sign and axis re-verification on the real mount: the lateral-sign finding of 2026-09-29 | needs adapting for real sensors | a, b | `flow_bridge.py:27-31`. Only the SITL mount is verified, and CLAUDE.md warns against transferring it to a different mount. | 0.5 d hand-carried, against mocap | A5, D3, F1 |
| D6 | Vanishing-point heading method re-validated on real images under a **new pre-registration** (plan question 6) | not built | b (heading arms); a if the forward camera is flown | The frozen parameters (0.5° tolerance, `S_MIN` 200 px, 80 px box) were calibrated on ideal simulated images. It fails plain walls over a checker floor (Phase 3). The table-test tool exists (D2). | 2–4 d: pre-registration, recordings, table test | D2, U5 |
| D7 | Wall-tag method re-validated: S0 (validity rule and σ_pos) repeated on real images against mocap | not built | a, b if P-HOLD | `tag_hold_design.md` "Transfer"; the D18 shared tag-validity rule (METHODOLOGY "RULING 2026-10-08, shared tag-fix VALIDITY RULE"). | 1–2 d | A7, I3 |

### E. Flow-validity rule

| ID | component | status | needed by | evidence | effort (assumption) | depends on |
|---|---|---|---|---|---|---|
| E1 | Flow validity = inlier ratio **and** feature count, ONE flag from one source, identical for EKF3, the UKF and the FGO. The threshold is calibrated on `p1c_*` only. | not built | a, b (it also feeds EKF3) | **Current committed state** (plan §7, `4556714`, lines 228–235; ruling 2026-10-09 "D22 is a SHARED SENSOR-PIPELINE LIMITATION"): planned, with no threshold or code yet. Code today: `out.valid = tracked_count >= min_valid` (`flow_tracker.py:313`). **Being pre-registered now by another agent; this document does not set it.** No newer draft was visible in other worktrees at writing time. Calibration flights exist: `p1c_{fwdc,fwdplainc}_{tex,trans,blank}` (6 usable, 1 `_ABORTED`). | 0.5 d code, 0.5 d calibration on `p1c_*`, 0.5 d regression on recorded bags | pre-registration (other agent) |

### F. Mocap-based fail-closed watcher

| ID | component | status | needed by | evidence | effort (assumption) | depends on |
|---|---|---|---|---|---|---|
| F1 | Mocap client: Vicon/OptiTrack stream (VRPN/NatNet) → ROS 2 pose with host stamps and Pi/ground-station receipt stamps | not built | a, b | No mocap client exists in the repo; only `eval/mocap_align.py` (offline) and `wall_watch.py` mention mocap. | 1–2 d (assumes an existing ROS 2 driver for the system) | U7 |
| F2 | Watcher logic: capture-volume box, process liveness, tilt | needs adapting for real sensors | a, b | `sim/tools/wall_watch.py` (`--box`, `--watch-process`, `--dep-loss land`; fail-closed heartbeat contract at `:134-146`). Its input is the Gazebo `/ground_truth/pose`, and its stop actions kill SITL processes (`LEFTOVER`), which on a real vehicle must become LAND commands. Verified in SITL 2026-10-08 (`tools/test_watch_failclosed.sh`, METHODOLOGY "fail-closed safety watcher"). | 1 d | F1 |
| F3 | Heartbeat path to the FC and an FC-side "no heartbeat → LAND" second layer (Lua or companion), plus a watcher → `LAND` MAVLink command | not built | a, b | In SITL the heartbeat is a local file (`<out>/watch_heartbeat`) that `fly_trial.py` reads (`WATCH_HEARTBEAT`, `fly_trial.py:303-315`). Plan §7 requires a MAVLink heartbeat to the FC as the second layer. A Lua layer needs scripting in the board build (flash, G1). Only `sim/scripts/o_source_switch.lua` exists. | 2–3 d | F2, B1, G1a |
| F4 | Watcher bench tests: watcher not started → no arm; watcher killed in a tethered hover → land | not built | a, b | **Being pre-registered now by another agent** (ruling 2026-10-10 item 4). The SITL analogue passed (T1/T2 in `tools/test_watch_failclosed.sh`). | 0.5 d bench, plus 0.5 d in a tethered hover (H8) | F3 |

### G. Estimators and firmware

| ID | component | status | needed by | evidence | effort (assumption) | depends on |
|---|---|---|---|---|---|---|
| G1a | Baseline firmware image for (a): the pinned `7bac20cbcc` (tag `thesis-baseline`) built for the real board, or a stock release; `.apj` and parameter dump archived (plan §9.2 step 1) | not built | a | `~/ardupilot/build/` contains only `sitl/` (checked). The pinned commit is preferred over a stock release so that `LOG_REPLAY` logs replay in the fork's Replay (same DAL format) [E]. | 0.5 d build and flash, plus 0.5 d rollback rehearsal | U1 |
| G1b | Thesis firmware (fork `~/ardupilot_ukf`, branch `ukf-jitter-fix`) for the real board: `AP_NavUKF`, `AP_NavFGO`, `AP_AHRS_UKF/FGO`, `thesis_nav_check` | not built | b (and a, only if the UKF shadows onboard) | **BLOCKER: the port is compiled for SITL only.** `AP_NavUKF.h:29` reads `#define AP_NAVUKF_ENABLED (CONFIG_HAL_BOARD == HAL_BOARD_SITL)`, so every backend, the 52 AHRS switch arms and `thesis_nav_check` drop out of a board build. `~/ardupilot_ukf/build/` contains only `sitl/`. **`real_flights_plan.md:35` says the Pixhawk 6X / CubeOrange firmware "has been built"; Part C §5.5 says no firmware was built, and its flash figures (270–325 kB free) come from published STOCK `.apj` files.** Neither build directory (the fork's, or `~/ardupilot/build/`) has a board build (not edited here). | 2–4 d: guard change, ChibiOS compile fixes, flash-size check (`size_compare_branches.py`), bench boot, and the "backends disabled reproduces EKF3" check (plan §9.2 step 2). The port is assumed to compile for ChibiOS with minor fixes [U]. | U1, U2 |
| G2 | UKF CPU load on the FC MCU at 80 Hz predict plus updates; loop-time margin | not built | b (onboard UKF) | Estimate only: 5–8% CPU, 0.3–0.4 ms per predict in double on H7 (Part C §5.3). Never measured. | 0.5 d bench (scheduler `PM` / perf logging) | G1b |
| G3 | UKF port algorithm: shadow and flying, tag ExtNav input, option (i) attitude hold on invalid output, first tag anchor refused once armed, jitter fix | exists and tested in SITL | b | Installed `ukf-jitter-fix` `abb0357d` (METHODOLOGY "UKF jitter correction MERGED"). S2v2 ×3; `cl_ukf_*_v2` PASS; tier B UB1–UB5 PASS; safety (a) v2 ALL PASS; safety (b) v2 S-A2 failed as worded (relay drain; safety unaffected). **The SITL safety (a)/(b) re-run on the corrected builds is still scheduled** (ruling 2026-10-10 item 3; see H1). If the initial-uncertainty audit changes the UKF, it is re-installed and re-gated. | 0 d new code; gates in H1 | audit (ruling 2026-10-10 item 2), H1 |
| G4 | `thesis_nav_check`: origin-independent "position lost → LAND" for types 12/13 | exists and tested in SITL | b | `ArduCopter/ekf_check.cpp:330-340` in the fork. SITL safety tests (a) PASS for both estimators. **Copter only; a QuadPlane would need its own (U2).** It is compiled out of board builds today (G1b). | in G1b; +1–2 d if QuadPlane | G1b |
| G5 | `AP_NavFGO` thin backend: `ODOMETRY` validation (flag, arrival ≤ 250 ms, age ≤ 250 ms), FC-IMU output predictor, `XFGI`/`XFGO` logging | exists and tested in SITL | b | FG1–FG3b, D25, `cl_fgo_*`, `fgo_cpp_shadow_*` (`docs/fgo_cpp_port.md` Part 4; METHODOLOGY "FGO C++ stage 5 RESULT"). | 0 d new code; hardware gates in H2/H4 | G1b |
| G6 | C++ FGO node on x86 (GTSAM 4.2.1, ROS 2 / MAVLink adapter, time_ref stamping, reorder delay 0.20 s) | exists and tested in SITL | b | `src/estimators/fgo_cpp/`. Equivalence bands A/B/C/L passed; flew S3/S3v2 and the FGO safety re-tests (node `f642cd37`). Accepted for the **aided regime only** (plan §9.3 update). | — | — |
| G7 | Corrected FGO (initial yaw σ 1° in both cores, ruling 2026-10-10): C++ equivalence on the corrected build, plus SITL safety (a)/(b) | not built | b (FGO) | Ruling 2026-10-10 items 1–3 and the reorder ruling (in progress). Plan §7: "before any real FGO flight". All flown FGO results used 1e-3 rad. | already scheduled; ~1 d of equivalence plus the H1 flights | audit, H1 |
| G8 | C++ FGO on the real Pi: GTSAM 4.2.1 + Boost on arm64 (native or cross build), ROS 2 Jazzy arm64, keyframe CPU budget (33 ms), memory, core pinning and RT priority, **live solve-time self-stop** (stage 3 requirement: p99 > keyframe period for 2 s → node stops → backend invalid → LAND) | not built | b (FGO); a only if a live shadow is wanted (offline replay needs none of this) | "Neither a qemu run nor a cross-compile was done" (`fgo_cpp_port.md`, Pi estimate). Estimated p99 on a Pi 5 ~4.3 ms, on a Pi 4 ~10–11.5 ms, single spikes to ~65 ms on a Pi 4 [E]. The self-stop exists only as a plan requirement (§9.4 stage 3). | 1 d native build (Pi 5; a Pi 4 needs `-j2` plus swap, possibly 2 d), 1 d timing under the full load with thermals, 1 d self-stop | A1, U3 |
| G9 | C++ FGO node transport to a serial FC (today UDP only, learning the peer from SITL SERIAL3) | needs adapting for real sensors | b (FGO) | `fgo_cpp_node.cpp:9-10,80` (`UdpEndpoint`). With a router (B1) the change may be configuration only. | 0.5–1 d | B1 |
| G10 | UKF live on the Pi (only if U9 = Pi placement): a live UKF node plus a UKF mode in the thin backend | not built | b (only if U9 = Pi) | Only `ukf_core.py` and the replay scripts exist; there is no live Python UKF node. | 3–5 d plus its own SITL gates (FG1–FG3-type) | U9 |
| G11 | Offline replay of the UKF/FGO on real-flight logs (Python `ukf_replay.py` / `fgo_replay.py`, C++ replay, port Replay on `LOG_REPLAY` dataflash) | needs adapting for real sensors | a | It assumes bag topics, sim stamps, 333 Hz/3 ms IMU dejitter and `imu_gap_check` (memory rule: run `imu_gap_check --write` first), and the C7 constants. | 1–2 d | C7, I2 |

### H. Safety tests and staging

| ID | component | status | needed by | evidence | effort (assumption) | depends on |
|---|---|---|---|---|---|---|
| H1 | SITL safety tests (a) estimator failure in a hover and (b) node or bridge kill, on the corrected UKF and FGO builds | exists and tested in SITL | b | Procedure and scorer exist (`tools/run_h_safety.sh`, `eval/h_safety_score.py`). Earlier builds passed (METHODOLOGY "RESULT: FGO safety re-test (a)/(b) v3", "UKF safety re-test (a) v2"). **GATE STILL OPEN:** the re-run on the corrected builds is scheduled (ruling 2026-10-10 item 3). | ~1 d of flights (scheduled) | G7, G3 |
| H2 | SITL rehearsal at Pi-like link latency (`tc netem` or a bridge delay): FG1, FG2, FG3/FG3b, D25, plus one closed-loop P-HOLD per estimator | not built | b | Plan §9.2. A gate failure blocks hardware closed loop for that estimator. | 1 d harness, plus 1 d flights per estimator | B3, H1 |
| H3 | Rehearsal of P-HOLD and P-LAPS in the simulated mocap room (`fly_trial` profiles, moving setpoints, D24 clock, land on failure) | exists and tested in SITL | a, b | Experiment H S1/S2/S3 (`room_wall_tag`); experiment T (laps). | 0 d; re-run only after a script change | — |
| H4 | Bench stage 0 (props off): all streams at rate, clock map settled, logging complete, rollback rehearsed; for (b) also forced backend invalidity → `thesis_nav_check` LAND on the real FC | not built | a; b adds the forced-invalidity item | Plan §9.4 stage 0; plan §7 ("must pass on the bench AND in SITL"). | 1–2 d (a); +1 d (b) | everything in A–C, F3, G1 |
| H5 | RC override: a dedicated switch to ALT_HOLD/STABILIZE (no estimator position), rehearsed before every session | not built | a, b | Plan §7, §9.4. ALT_HOLD needs the height source (here the rangefinder) to remain healthy. | 0.5 d | A1, U8 |
| H6 | Geofence: the mocap box (primary, F2) plus the ArduPilot fence as a secondary layer only | needs adapting for real sensors | a, b | Plan §7: the FC fence uses the AHRS position, i.e. the estimator under test. Box sizes from the SITL rule "≥ 2 m clearance from every hold point" (ruling 2026-10-09, attitude-only landing drift 0.37–1.4 m). | 0.5 d | F2, U7 |
| H7 | Hand-carried stage (motors off): estimators against mocap; flow sign; heading and tag checks | not built | a, b | Plan §9.4 stage 0. | 0.5–1 d | H4, F1 |
| H8 | Tethered hover with EKF3 flying | not built | a, b | Plan §7 staged bring-up step 3. | 0.5–1 d | H7, H5, F4 |
| H9 | Per-stage pre-registration with real-flight criteria fitted to the capture volume (plan question 8); real-flight scoring scripts | not built | a, b | The SITL criteria (U1–U3, B1–B5) assume a 160 m corridor (plan question 8). | 1–2 d per stage | U7 |
| H10 | Real-vehicle flight script: `fly_trial.py` without SITL assumptions, keeping `ensure_params`, D24 `SYSTEM_TIME` clock, `WATCH_HEARTBEAT` (to be replaced by F3), `require_fgo_node_current`, `wait_fix` before arming, land on failure | needs adapting for real sensors | a, b | `fly_trial.py` (`:303-315`, `:502-509`, `:864`). It has SITL-only paths, e.g. OUTBACK toggling `SIM_GPS1_ENABLE` (`o_gnss.parm`). | 1–2 d | F3, C1 |

### I. Logging, ground truth and time sync

| ID | component | status | needed by | evidence | effort (assumption) | depends on |
|---|---|---|---|---|---|---|
| I1 | FC logging: `LOG_REPLAY=1`, `LOG_DISARMED=1` (CLAUDE.md "All future flights"), IMU at full rate (`INS_LOG_BAT_*` or a fast IMU bitmask, needed by `mocap_align`), `XUK*`/`XFG*`/`XKF*` | needs adapting for real sensors | a, b | Today these are set only in `consolidated_rerun.parm`, alongside `AHRS_EKF_TYPE 10`, so they must move to a real file (C1). SD-card throughput at full-rate IMU is [U]. | 0.5 d plus a bench check for dropped log blocks | C1, G1a |
| I2 | Pi recorder: a ROS 2 bag of every input, estimator outputs, `/imu/time_ref`, heading-bridge CSV, node clock-map stats; metadata (repo commits, firmware hash, parameters, hardware IDs) | needs adapting for real sensors | a, b | `record_trial.sh` / `run_trial.sh` assume `/clock`, `/ground_truth/pose` and Gazebo world names. | 1 d | B4, F1 |
| I3 | Mocap ground truth into the trial: poses with mocap-host stamps plus receipt stamps; `eval/mocap_align.py` (4-DoF frame fit) | exists but untested on hardware | a, b | `mocap_align.py` self-test: offset −3.7 ms, rate 4.9 ppm, yaw 0.30° on synthetic mocap (plan §8 item 4). | 0.5 d | F1, I1 |
| I4 | Time sync mocap ↔ FC (|ω| correlation against the FC gyro, with the 11.3 ms INS group delay at 20 Hz) and Pi ↔ mocap host (chrony or PTP on the lab LAN) | exists but untested on hardware | a, b | The `mocap_align.py` method is self-tested only. chrony/PTP is not configured anywhere [U7]. If the notch or filter settings differ from 20 Hz (C6), the group-delay constant changes. | 0.5–1 d | I3, C6, U7 |

---

## 2. Counts per status

| status | rows | IDs |
|---|---|---|
| exists and tested in SITL | 8 | B2, C8, G3, G4, G5, G6, H1, H3 |
| exists but untested on hardware | 5 | A6, D1, D2, I3, I4 |
| needs adapting for real sensors | 20 | A4, A5, A7, A10, B4, C2, C3, C4, C5, C6, C7, D4, D5, F2, G9, G11, H6, H10, I1, I2 |
| not built | 27 | A1, A2, A3, A8, A9, B1, B3, C1, D3, D6, D7, E1, F1, F3, F4, G1a, G1b, G2, G7, G8, G10, H2, H4, H5, H7, H8, H9 |
| **total** | **60** | |

Two "tested in SITL" rows still have an **open gate**: H1 (the safety re-run on the corrected builds, scheduled) and G3 (it
depends on H1).

---

## 3. Shortest path to (a): EKF3 flies, everything logged, UKF/FGO replayed offline

**Minimal (a)** = EKF3 on downward flow plus rangefinder, the thesis configuration (`gnss_denied_nomag`-equivalent), on
the stock-or-pinned image. The profile is a hover, then a small square inside the mocap volume. The UKF and FGO run
**offline after the flight** ("not real-time"). This path needs **none of the fork** (G1b), **no Pi GTSAM** (G8) and
**no forward camera**. P-HOLD with the wall tag is an add-on, shown in step 9.

Order (cumulative effort, one person; hardware assembled; [E]):

| step | items | effort | cumulative |
|---|---|---|---|
| 0 | Hardware identities answered (U1–U8); airframe assembled (A1) | 2–4 d | 2–4 d |
| 1 | Baseline image built and flashed, archived, rollback rehearsed (G1a); stock manual tune, hover learn, notch (A2, C5, C6) | 2.5–3.5 d | 4.5–7.5 d |
| 2 | FC↔Pi link and router; IMU stream; Pi time base; clock-map bench (B1, A10, B4, B2) | 3 d | 7.5–10.5 d |
| 3 | Rangefinder on the FC and its parameters (A8, C2); range republisher, or dataflash `RFND` for replay (A9) | 1.5–2 d | 9–12.5 d |
| 4 | Downward camera capture, calibration and flow on the Pi; flow bridge (A3, D1, A4, A5) | 3–5 d (**+3–5 d** if flow needs C++) | 12–17.5 d |
| 5 | Flow-validity rule coded and calibrated per its pre-registration (E1) | 1.5 d | 13.5–19 d |
| 6 | Real parameter file with logging (C1, C3, I1) | 2 d | 15.5–21 d |
| 7 | Mocap client, watcher, heartbeat to the FC with an FC-side LAND layer, bench tests (F1, F2, F3, F4); geofence (H6); RC override (H5) | 6–8 d | 21.5–29 d |
| 8 | Extrinsics, time offsets, flow sign (D3, D4, D5); Pi recorder (I2); flight script (H10); mocap alignment (I3, I4) | 5.5–8 d | 27–37 d |
| 9 | *(only if P-HOLD)* tag detector, S0 re-validation, ExtNav parameters (A7, D7, C4) | +2.5–3.5 d | (29.5–40.5 d) |
| 10 | Stage 0 bench (H4); hand-carried (H7); stage-1 pre-registration (H9); tethered EKF3 hover (H8); then the first (a) flight | 3–6 d | **30–43 d** (32.5–46.5 d with P-HOLD) |
| after | Offline replay adapted to real logs, with the lever-arm parametrisation and its equivalence re-runs (C7, G11). Needed to score, not to fly. | 3–5 d | — |

Each step figure is the sum of its rows' own estimates; no overlap inside a step is assumed.

**Total to the first (a) flight: about 30–43 working days** (6–9 weeks for one person). Add 3–5 d if flow needs C++,
2.5–3.5 d for P-HOLD, and the procurement time for any missing hardware.

**Critical path:** hardware identities → link and IMU stream (B1, A10) → camera and flow on the Pi (A3, A4) → flow-validity
rule (E1) → mocap client → watcher → FC heartbeat layer (F1, F2, F3, F4) → stage-0 bench → hand-carried → tethered hover.
The watcher chain (step 7, 6–8 d) and the camera/flow chain (steps 4–5, 4.5–6.5 d) can run in parallel with two
people, which shortens the path to about 24–35 d.

## 4. Then to (b): additional items

| order | items | effort | notes |
|---|---|---|---|
| 1 | **Corrected FGO gates**: initial-uncertainty audit, C++ equivalence on the corrected build, SITL safety (a)/(b) for both estimators (G7, H1; G3 re-gated if the audit touches the UKF) | already scheduled (~2–3 d) | ruling 2026-10-10 "REORDER" items 1–3 |
| 2 | **Fork for the real board**: remove the SITL-only guard, build for ChibiOS, measure flash, boot on the bench, reproduce EKF3 with the backends disabled (G1b); `thesis_nav_check` for the vehicle type (G4, U2); fork parameters with `TFAIL` 0 checked (C8) | 2–4 d (+1–2 d if QuadPlane) | **top blocker**: no board build exists, and the backends compile out today |
| 3 | UKF CPU and loop-time margin on the FC MCU (G2) | 0.5 d | only for the onboard UKF |
| 4 | Geometry constants parametrised in the Python, C++ and port code, with equivalence re-runs (C7), if not already done for (a) | 2–3 d | the same values must be in all three implementations |
| 5 | **C++ FGO on the Pi**: arm64 GTSAM build, timing under the full load, thermals, core pinning, live solve-time self-stop (G8); serial or router transport (G9) | 3.5–5 d | never built for ARM |
| 6 | Link latency measured (B3), then the SITL rehearsal at that latency: FG1–FG3b, D25, one P-HOLD per estimator (H2) | 2–3 d | a failure blocks that estimator |
| 7 | Forced backend invalidity → LAND on the real FC, on the bench (H4 item b) | 1 d | ruling 2026-10-08 option (i): "bench AND SITL" |
| 8 | P-HOLD components (A7, D7, C4), if not done for (a); forward-camera heading arms (A6, D2, D6) only once verified | 3–4 d; +3–5 d heading | the primary closed-loop profile is P-HOLD |
| 9 | UKF live on the Pi (G10), only if U9 = Pi | 3–5 d | |
| 10 | Stage-2/3 pre-registrations (H9); entry criteria from stage-1 results (plan §9.4) | 2–3 d | |

**Additional effort after (a): about 17–27 d** (excluding G10 and the heading arms).

**Top blockers for (b):**
1. `AP_NAVUKF_ENABLED` is SITL-only, so there is no board firmware with the UKF, the FGO backend or `thesis_nav_check`.
   The plan's "has been built" statement (line 35) is contradicted by Part C §5.5 and by the build directory.
2. The corrected FGO (initial yaw σ 1°) and the SITL safety (a)/(b) re-runs on the corrected builds are not yet done.
3. The C++ FGO has never been built or timed on ARM. Its transport is UDP-only, and the live solve-time self-stop does
   not exist.
4. The FC-side fail-closed layer (watcher heartbeat → LAND on the FC) does not exist. In SITL it is a local file.
5. The estimator geometry is hard-coded in three implementations (C7). Changing it re-opens the equivalence bands.

## 5. Open questions for the user

1. **Flight controller:** which board? Is it H7 with a hardware double FPU (needed by the port's `double` state)? Is a
   spare available?
2. **Vehicle type:** Copter or QuadPlane? (`thesis_nav_check` and the SITL tests are Copter only.)
3. **Companion:** Pi 4 or Pi 5? RAM? Is active cooling fitted?
4. **Downward camera:** model, lens, interface (CSI/USB), shutter type, and its mount position relative to the IMU.
5. **Forward camera:** fitted for the first campaign or not? Model and lens? Does the lab have the line structure the
   heading method needs (plan question 6)?
6. **Rangefinder:** model, interface (FC serial/I²C or the Pi), minimum range, and its mount position.
7. **Mocap:** Vicon or OptiTrack? Rate, protocol (VRPN/NatNet), time source (PTP/NTP), capture-volume size. Can the Pi
   and the ground station join the mocap LAN?
8. **Airframe and safety:** frame, prop guards, net or tether, safety pilot, RC transmitter, a lab safety review for
   non-EKF3 estimators (plan question 7).
9. **UKF placement for (b):** onboard the FC (the port; no Pi link latency) or on the Pi (G10, shared latency with the
   FGO)? (plan question 2)
10. **Firmware for (a):** the pinned `7bac20cbcc` (Replay-compatible with the fork) or a stock release?
11. **Is the open-loop FGO in (a) allowed to be offline-only** ("not real-time"), so that G8 moves entirely to (b)?
12. **Two people or one** on the software path? This sets whether the watcher and camera chains run in parallel.

## 6. Notes on this document

- It was written without running anything. Every status comes from files on disk at `4556714` and from
  `~/ardupilot_ukf` (read only).
- **Discrepancy recorded, not corrected:** `docs/real_flights_plan.md:35` ("the Pixhawk 6X and CubeOrange firmware for
  this tree has been built") against Part C §5.5 ("no firmware was built") and `~/ardupilot_ukf/build/` (SITL only).
  That file is being edited by another agent, so the correction is left to the user. What was checked: the fork's
  `build/` and `~/ardupilot/build/` (both contain only `sitl/`), and the compile guard at `AP_NavUKF.h:29`. A board
  build elsewhere on another machine cannot be ruled out from here; the guard keeps the port out of it in any case.
- E1 and F4 are deliberately left at "not built": their content is being pre-registered elsewhere. This checklist only
  tracks them.
