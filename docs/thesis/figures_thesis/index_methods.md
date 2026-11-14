# Methodology figure and tables: index (2026-10-17)

Built by `eval/figs_thesis_methods.py` at commit `0ea33f4` (run with `/home/makerspace/venv-evo/bin/python`). Drawing and tabulating only: no simulation, no estimator result recomputed, numbers.md not edited. **Not yet in the combined PDF**: integration with `eval/figs_thesis.py` and `index.md` comes later. ArduPilot trees cited: thesis fork `~/ardupilot_ukf` (f30f6ffa2f, branch ukf-jitter-fix; files read with git show at this revision); pinned `~/ardupilot` (7bac20cbcc; files read with git show at this revision).

**Source checks: 331/332 citations verified** (the needle occurs verbatim on the cited line). **Cross-checks: 43/43 EXACT** (computed string = stored string, `rd()` of `eval/figs_thesis.py`, loaded by AST).

**Proposed numbering** (vocabulary §6: by chapter; Chapter 3 = method, Chapter 8 = towards real flights). File names are descriptive and new; `M1`–`M3` are deliberately not used as ids because they are the F8 mitigation codes.

| proposed no. | files | title | checks | proposed place |
|---|---|---|---|---|
| Figure 3.1 | `methods_architecture.png`, `methods_architecture.pdf`, `methods_architecture_a.png`, `methods_architecture_a.pdf`, `methods_architecture_b.png`, `methods_architecture_b.pdf` | System architecture: sensors, bridges, the three estimators and where each one runs | 0/0 | Chapter 3 (method): the architecture the estimators, experiments and safety tables refer to |
| Table 3.1 | `methods_estimator_design.md`, `methods_estimator_design.tex`, `methods_estimator_design.png` | Estimator design: EKF3, the UKF and the FGO | 7/7 | Chapter 3 (method), estimators |
| Table 3.2 | `methods_noise_parity.md`, `methods_noise_parity.tex`, `methods_noise_parity.png` | Noise parity: measurement and process noise per sensor and estimator | 15/15 | Chapter 3 (method), fairness |
| Table 3.3 | `methods_noise_exceptions.md`, `methods_noise_exceptions.tex`, `methods_noise_exceptions_p1.png`, `methods_noise_exceptions_p2.png`, `methods_noise_exceptions_p3.png` | Documented exceptions to noise and treatment parity, with their rulings | 12/12 | Chapter 3 (method), fairness |
| Table 3.4 | `methods_experiment_matrix.md`, `methods_experiment_matrix.tex`, `methods_experiment_matrix_p1.png`, `methods_experiment_matrix_p2.png` | Experiment matrix | 4/4 | Chapter 3 (method), experiments |
| Table 8.1 | `realflight_compute.md`, `realflight_compute.tex`, `realflight_compute.png` | Compute and deployability per estimator | 4/4 | Chapter 8 (towards real flights); the offline row may also sit in Chapter 3 |
| Table 8.2 | `realflight_safety_findings.md`, `realflight_safety_findings.tex`, `realflight_safety_findings_p1.png`, `realflight_safety_findings_p2.png` | Safety findings from the SITL safety bench, with mitigations and status | 1/1 | Chapter 8 (towards real flights) |

## Captions, sources and cross-checks

### Figure 3.1: System architecture: sensors, bridges, the three estimators and where each one runs

- **Caption:** Panel (a) shows the sensors and the relays that carry their measurements to the flight controller and to the recorded data used offline. Panel (b) shows the flight controller, where each of the three estimators runs, outlined in its own colour (EKF3 blue, UKF green, FGO orange), alongside the safety watchers and the offline replay and evaluation.
- **Edges and boxes, with their sources** (every edge is derived from these lines):

| what the diagram shows | source (file:line) |
|---|---|
| IMU: HIGHRES_IMU on SITL SERIAL2 (udpclient 14556, bypassing MAVProxy) -> imu_bridge -> /imu/data_raw, /imu/time_ref | run_trial.sh:300; imu_bridge.py:102; imu_bridge.py:123; imu_bridge.py:127 |
| /imu/data_raw is for the UKF/FGO only; EKF3 (and the UKF port) use the FC's own IMU (DAL) | CLAUDE.md:963; AP_NavUKF.h:14 |
| Downward camera -> flow_tracker -> /optical_flow/measurement (uses /attitude/angular_rates) | flow_tracker.py:60; flow_tracker.py:67; flow_tracker.py:74 |
| flow_bridge: OPTICAL_FLOW (msg 100) on MAVProxy 14553 -> EKF3; fanned out to the UKF port | flow_bridge.py:80; flow_bridge.py:137; AP_AHRS.cpp:2798 |
| lidar_bridge: DISTANCE_SENSOR on MAVProxy 14552 -> RNGFND1 | lidar_bridge.py:46; lidar_bridge.py:80 |
| attitude_bridge: FC ATTITUDE on MAVProxy 14551 -> /attitude/angular_rates | attitude_bridge.py:44; attitude_bridge.py:55 |
| heading_bridge: forward camera -> vanishing-point heading -> ODOMETRY on SITL SERIAL1 (14557) -> ExtNav yaw; republishes /forward_camera/heading_sent | heading_bridge.py:2; heading_bridge.py:35; heading_bridge.py:72; heading_bridge_core.py:27 |
| ExtNav reaches EKF3 and (rulings D17 and H) the UKF port by the same call | AP_AHRS.cpp:2827; AP_AHRS.cpp:2830 |
| Tag bridges: floor tags (tag_bridge, Experiments 2/3) and the wall tag (tag_bridge_fwd, Experiment 5) -> ODOMETRY on SERIAL1 14557 (ExtNav position + yaw); /tags/sent | tag_bridge.py:11; tag_bridge_fwd.py:2; tag_bridge_fwd.py:12; run_trial.sh:142 |
| Ground truth: Gazebo dynamic_pose -> ground_truth_pub -> /ground_truth/pose (evaluation and the SITL watcher only) | ground_truth_pub.py:48; ukf_replay.py:7 |
| FGO node (Python or C++): subscriptions; ODOMETRY LOCAL_NED / ESTIMATOR_TYPE_NAIVE on SITL SERIAL3 (14558) -> AP_NavFGO | CN:4; run_trial.sh:166; run_trial.sh:448; GCS_Common.cpp:4063; AP_NavFGO.h:2 |
| AHRS_EKF_TYPE selects the flying estimator: 12 = thesis UKF, 13 = thesis FGO; 3 = EKF3; 10 = simulator truth | AP_AHRS.h:499; AP_AHRS.h:500; consolidated_rerun.parm:11; closedloop.parm:4; closedloop_ukf.parm:4; closedloop_fgo.parm:4 |
| SHADOW: EKF3 flies and the UKF port / the FGO node + output predictor run in shadow (logged only) | closed_loop_run.sh:20; closed_loop_run.sh:39; ukf_shadow.parm:2; AP_AHRS.cpp:528 |
| Camera heading to EKF3 via ExtNav only in closed loop (1C with heading: EK3_SRC1_YAW 6; UKF port AHRS_UKF_EXTYAW 1); the FGO node takes /forward_camera/heading_sent | closedloop_heading.parm:10; closedloop_ukf_heading.parm:1; run_trial.sh:449 |
| Offline 1B: EKF3 gets no heading (ruling 2026-09-29); the UKF/FGO arms read the frozen Phase 3 heading | M:2884; M:2888; MM:219 |
| Experiment 5: EKF3 flies on the wall tag (ExtNav position + yaw); UKF-flying uses AHRS_UKF_EXTPOS/EXTYAW; FGO node takes /tags/sent | h_extnav.parm:7; h_ukf_tag.parm:7; closed_loop_run.sh:72 |
| Offline replay reads the bag topics (ground truth for scoring only) | ukf_replay.py:67; fgo_replay.py:101 |
| SITL safety watcher wall_watch.py: ground truth + process liveness -> heartbeat file -> fly_trial LAND / stop | wall_watch.py:5; wall_watch.py:53; fly_trial.py:493; closed_loop_run.sh:117; run_h_safety.sh:14 |
| Real-hardware watcher realflight/watcher: mocap (MCP1) + FC telemetry + beacons -> ONE LAND + HEARTBEAT gating FS_GCS; SITL bench only | mocap_watch.py:3; mocap_watch.py:14; liveness.py:4; watcher_fc.parm:14; mcp1.py:1 |
| Companion: in SITL every process ran on the desktop; Pi timing is an ESTIMATE; closed-loop real flights are future work | M:13651; M:12954 |


### Table 3.1: Estimator design: EKF3, the UKF and the FGO

- **Caption:** Design of the three estimators as built (offline and in the flight software). Each cell gives its source in brackets.
- **Sources:** in the table's source column (`docs/thesis/tables/methods_estimator_design.md`).

| check | computed | expected | source | match |
|---|---|---|---|---|
| EKF3 prediction period = 5 frames × 1/400 s (s), printed in ms in Table 3.1 | `0.0125` | `0.0125` | N:183 | yes |
| UKF port predict period printed in Table 3.1 (ms) = EKF3's | `12.5` | `12.5` | N:186 | yes |
| UKF port TARGET_DT equals EKF3's EKF_TARGET_DT (s) | `0.012` | `0.012` | AP_NavUKF.cpp:38; AP_NavEKF3_core.h:59 | yes |
| flow NIS gate = (0.01 × EK3_FLOW_I_GATE)² | `9` | `9` | AP_NavEKF3.cpp:42; N:147 | yes |
| range NIS gate = (0.01 × EK3_RNG_I_GATE)² | `25` | `25` | UC:45; N:149 | yes |
| EKF3 range-height NIS gate = (0.01 × EK3_HGT_I_GATE)² (range as the height source) | `25` | `25` | AP_NavEKF3.cpp:36; N:149 | yes |
| heading χ² gate of the UKF/FGO = (0.01 × 300)² | `9.0` | `9.0` | MM:186 | yes |

### Table 3.2: Noise parity: measurement and process noise per sensor and estimator

- **Caption:** The measurement noise each estimator applies, offline and in flight. Values come from the parameter files, the code constants and METHODOLOGY; the source column gives each. Where the estimators differ the difference is listed, with its ruling, in Table 3.3.
- **Sources:** in the table's source column (`docs/thesis/tables/methods_noise_parity.md`).

| check | computed | expected | source | match |
|---|---|---|---|---|
| √dt at dt = 0.0125 s | `0.1118034` | `0.1118034` | N:152 | yes |
| EKF3 GYRO_P_NSE default equals the value used here | `0.015` | `0.015` | AP_NavEKF3.cpp:28 | yes |
| EKF3 ACC_P_NSE default equals the value used here | `0.350` | `0.350` | AP_NavEKF3.cpp:29 | yes |
| EKF3 GBIAS_P_NSE default equals the value used here | `0.001` | `0.001` | AP_NavEKF3.cpp:30 | yes |
| EKF3 ABIAS_P_NSE default equals the value used here | `0.020` | `0.020` | AP_NavEKF3.cpp:31 | yes |
| accelerometerCovariance: σ_c = NSE·√dt / covariance = NSE²·dt | `0.03913119 / 1.53125×10⁻³` | `0.03913119 / 1.53125×10⁻³` | N:153 | yes |
| accelerometerCovariance in fgo_core.py equals NSE²·dt (printed in Table 3.2) | `1.53125e-3` | `1.53125e-3` | FC:27 | yes |
| gyroscopeCovariance: σ_c = NSE·√dt / covariance = NSE²·dt | `0.001677051 / 2.8125×10⁻⁶` | `0.001677051 / 2.8125×10⁻⁶` | N:154 | yes |
| gyroscopeCovariance in fgo_core.py equals NSE²·dt (printed in Table 3.2) | `2.8125e-6` | `2.8125e-6` | FC:28 | yes |
| biasAccCovariance: σ_c = NSE·√dt / covariance = NSE²·dt | `0.002236068 / 5.0×10⁻⁶` | `0.002236068 / 5.0×10⁻⁶` | N:155 | yes |
| biasAccCovariance in fgo_core.py equals NSE²·dt (printed in Table 3.2) | `5.0e-6` | `5.0e-6` | FC:29 | yes |
| biasOmegaCovariance: σ_c = NSE·√dt / covariance = NSE²·dt | `0.0001118034 / 1.25×10⁻⁸` | `0.0001118034 / 1.25×10⁻⁸` | N:156 | yes |
| biasOmegaCovariance in fgo_core.py equals NSE²·dt (printed in Table 3.2) | `1.25e-8` | `1.25e-8` | FC:30 | yes |
| EKF3 effective ExtNav yaw σ at the default VISO_YAW_M_NSE 0.2 rad (deg) | `11.46` | `11.46` | M:4756 | yes |
| VISO_YAW_M_NSE at which EKF3's 5° floor binds (rad) | `0.0873` | `0.0873` | M:4757 | yes |

### Table 3.3: Documented exceptions to noise and treatment parity, with their rulings

- **Caption:** Every documented place where the noise or the treatment differs between estimators, with the ruling that covers it. Two code differences (5, 6) have no ruling in the record and are reported, not resolved.
- **Sources:** in the table's source column (`docs/thesis/tables/methods_noise_exceptions.md`).

| check | computed | expected | source | match |
|---|---|---|---|---|
| Table 3.3 row 23: measured minimum latency (ms) | `17.5–26.6` | `17.5–26.6` | M:10512 | yes |
| Table 3.3 row 23: shortfall (ms) | `12` | `12` | M:10512 | yes |
| Table 3.3 row 23: nominal bound (mm) | `6` | `6` | N:542 | yes |
| Table 3.3 row 23: corner bound (mm) | `22` | `22` | N:542 | yes |
| Table 3.3 row 23: corner speed (m/s) | `1.80` | `1.80` | N:542 | yes |
| Table 3.3 row 23: yaw bound (deg) | `0.06` | `0.06` | N:543 | yes |
| Table 3.3 row 23: nominal speed (m/s) | `0.5` | `0.5` | M:10517 | yes |
| Table 3.3 row 5: gating count, textured joint flow-rejection rate (chi2(2)=11.83) | `0.01%` | `0.01%` | FGN:13 | yes |
| Table 3.3 row 5: gating count, textured FLOW_MAX one-sided rate | `0.00%` | `0.00%` | FGN:13 | yes |
| Table 3.3 row 5: gating count, textured FLOW_MAX two-sided rate | `0.00%` | `0.00%` | FGN:13 | yes |
| Table 3.3 row 5: gating count, FLOW_MAX one-sided == two-sided (textured) | `0.00%` | `0.00%` | FGN:13 | yes |
| Table 3.3 row 5: gating count, joint chi2(2) threshold | `11.83` | `11.83` | FGN:11 | yes |

### Table 3.4: Experiment matrix

- **Caption:** Every experiment in the thesis numbering, with its worlds, sensors, estimators and their roles, loop, number of flights (with the unit), primary metric and hypothesis labels. Real-flight readiness is not an experiment and has no row (vocabulary §1, decision 3).
- **Sources:** in the table's source column (`docs/thesis/tables/methods_experiment_matrix.md`).

| check | computed | expected | source | match |
|---|---|---|---|---|
| 1B validation bags: 2 wall conditions × 3 floors × 3 repeats | `18` | `18` | M:2706 | yes |
| 1B offline fusion replays: (9 textured-wall bags × 3 arms + 9 plain-wall bags × 2 arms) × 2 estimators | `90` | `90` | M:2970 | yes |
| 1B robust-weighting replication: 6 flights × 2 worlds | `12` | `12` | M:9706 | yes |
| Exp. 2: 4 tag conditions × 3 repeats | `12` | `12` | M:10123 | yes |

### Table 8.1: Compute and deployability per estimator

- **Caption:** Offline step time, flight-controller cost and companion-computer timing, each labelled as its source labels it: MEASURED (board build), ESTIMATED, or DIAGNOSTIC (workstation timing, which says nothing directly about onboard feasibility).
- **Sources:** in the table's source column (`docs/thesis/tables/realflight_compute.md`).

| check | computed | expected | source | match |
|---|---|---|---|---|
| MatekH743 flash added = free without − free with (kB, 1000 B) | `+24.2 kB` | `+24.2 kB` | M:13567 | yes |
| Pixhawk6X flash added (kB) | `+23.8 kB` | `+23.8 kB` | M:13568 | yes |
| wall time per keyframe at RTF 0.5 = (1/30 s)/0.5 (ms) | `66.7` | `66.7` | M:7779 | yes |
| keyframe period 1/30 s (ms) | `33.3` | `33.3` | M:7772 | yes |

### Table 8.2: Safety findings from the SITL safety bench, with mitigations and status

- **Caption:** Findings for the real-flight path: each with its evidence (the SITL watcher bench on stock SITL, or a source trace), its mitigation and its status (built, tested in SITL, or hardware only). These are not the 5S safety tests (Table 7.2).
- **Sources:** in the table's source column (`docs/thesis/tables/realflight_safety_findings.md`).

| check | computed | expected | source | match |
|---|---|---|---|---|
| number of watcher gaps listed in real_flights_plan.md (G1–G11) | `11` | `11` | real_flights_plan.md:442-452; M:13122 | yes |

## Source verification (every citation)

| file | line | needle | ok |
|---|---|---|---|
| `run_trial.sh` | 300 | `--serial2=udpclient:127.0.0.1:14556` | yes |
| `imu_bridge.py` | 102 | `MAVLINK_PORT = 14556` | yes |
| `imu_bridge.py` | 123 | `'/imu/data_raw'` | yes |
| `imu_bridge.py` | 127 | `'/imu/time_ref'` | yes |
| `CLAUDE.md` | 963 | `ArduPilot EKF3 doesn't need `/imu/data_raw` itself` | yes |
| `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.h` | 14 | `Inputs (the same ones EKF3 uses)` | yes |
| `src/optical_flow_node/optical_flow_node/flow_tracker.py` | 60 | `/downward_camera/image` | yes |
| `src/optical_flow_node/optical_flow_node/flow_tracker.py` | 67 | `/attitude/angular_rates` | yes |
| `src/optical_flow_node/optical_flow_node/flow_tracker.py` | 74 | `/optical_flow/measurement` | yes |
| `flow_bridge.py` | 80 | `MAVLINK_PORT = 14553` | yes |
| `flow_bridge.py` | 137 | `optical_flow_send(` | yes |
| `~/ardupilot_ukf/libraries/AP_AHRS/AP_AHRS.cpp` | 2798 | `ukf.writeOptFlowMeas(` | yes |
| `lidar_bridge.py` | 46 | `MAVLINK_PORT = 14552` | yes |
| `lidar_bridge.py` | 80 | `distance_sensor_send(` | yes |
| `attitude_bridge.py` | 44 | `MAVLINK_PORT = 14551` | yes |
| `attitude_bridge.py` | 55 | `'/attitude/angular_rates'` | yes |
| `heading_bridge.py` | 2 | `Live forward-camera heading -> ArduPilot EKF3 ExternalNav yaw` | yes |
| `heading_bridge.py` | 35 | `MAVLINK_PORT = 14557` | yes |
| `heading_bridge.py` | 72 | `/forward_camera/heading_sent` | yes |
| `src/forward_camera/heading_bridge_core.py` | 27 | `Message: ODOMETRY` | yes |
| `~/ardupilot_ukf/libraries/AP_AHRS/AP_AHRS.cpp` | 2827 | `EKF3.writeExtNavData(` | yes |
| `~/ardupilot_ukf/libraries/AP_AHRS/AP_AHRS.cpp` | 2830 | `ukf.writeExtNavData(` | yes |
| `tag_bridge.py` | 11 | `MAVLink ODOMETRY to SITL SERIAL1` | yes |
| `tag_bridge_fwd.py` | 2 | `Live WALL-tag bridge for experiment H` | yes |
| `tag_bridge_fwd.py` | 12 | `MAVLink ODOMETRY to SITL SERIAL1` | yes |
| `run_trial.sh` | 142 | `TAG_BRIDGE and HEADING_BRIDGE share SERIAL1` | yes |
| `ground_truth_pub.py` | 48 | `'/ground_truth/pose'` | yes |
| `src/estimators/ukf_replay.py` | 7 | `Ground truth is used ONLY for evaluation` | yes |
| `src/estimators/fgo_cpp/src/fgo_cpp_node.cpp` | 4 | `Subscriptions (as fgo_node.py)` | yes |
| `run_trial.sh` | 166 | `SERIAL3_ARG=(--serial3=udpclient:127.0.0.1:14558)` | yes |
| `run_trial.sh` | 448 | `mavlink_out:=udp:127.0.0.1:14558` | yes |
| `~/ardupilot_ukf/libraries/GCS_MAVLink/GCS_Common.cpp` | 4063 | `MAV_FRAME_LOCAL_NED && f.estimator_type == MAV_ESTIMATOR_TYPE_NAIVE` | yes |
| `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavFGO.h` | 2 | `the thesis FGO (GTSAM fixed-lag smoother, run OUTSIDE ArduPilot` | yes |
| `~/ardupilot_ukf/libraries/AP_AHRS/AP_AHRS.h` | 499 | `UKF = 12` | yes |
| `~/ardupilot_ukf/libraries/AP_AHRS/AP_AHRS.h` | 500 | `FGO = 13` | yes |
| `consolidated_rerun.parm` | 11 | `AHRS_EKF_TYPE 10` | yes |
| `closedloop.parm` | 4 | `AHRS_EKF_TYPE 3` | yes |
| `closedloop_ukf.parm` | 4 | `AHRS_EKF_TYPE 12` | yes |
| `closedloop_fgo.parm` | 4 | `AHRS_EKF_TYPE 13` | yes |
| `sim/tools/closed_loop_run.sh` | 20 | `UKF=shadow (ruling D17 V2): EKF3 flies` | yes |
| `sim/tools/closed_loop_run.sh` | 39 | `FGO=shadow: EKF3 flies` | yes |
| `ukf_shadow.parm` | 2 | `it never drives the vehicle` | yes |
| `~/ardupilot_ukf/libraries/AP_AHRS/AP_AHRS.cpp` | 528 | `SHADOW unless AHRS_EKF_TYPE = 12` | yes |
| `closedloop_heading.parm` | 10 | `EK3_SRC1_YAW 6` | yes |
| `closedloop_ukf_heading.parm` | 1 | `the UKF fuses the ExtNav` | yes |
| `run_trial.sh` | 449 | `heading:=` | yes |
| `METHODOLOGY.md` | 2884 | `RULING — EKF3 in the offline forward-camera comparison` | yes |
| `METHODOLOGY.md` | 2888 | `Only the UKF and FGO get forward-camera arms` | yes |
| `src/estimators/measurement_models.py` | 219 | `def forward_events(trial, arm)` | yes |
| `h_extnav.parm` | 7 | `EK3_SRC1_YAW 6` | yes |
| `h_ukf_tag.parm` | 7 | `AHRS_UKF_EXTPOS 1` | yes |
| `sim/tools/closed_loop_run.sh` | 72 | `TAG_BRIDGE_FWD=1` | yes |
| `src/estimators/ukf_replay.py` | 67 | `/imu/data_raw` | yes |
| `src/estimators/fgo/fgo_replay.py` | 101 | `want = [` | yes |
| `sim/tools/wall_watch.py` | 5 | `/ground_truth/pose` | yes |
| `sim/tools/wall_watch.py` | 53 | `Box and tilt breaches always stop` | yes |
| `fly_trial.py` | 493 | `safety watcher lost in flight` | yes |
| `sim/tools/closed_loop_run.sh` | 117 | `wall_watch.py` | yes |
| `tools/run_h_safety.sh` | 14 | `WATCH_DEP_LOSS=land` | yes |
| `realflight/watcher/mocap_watch.py` | 3 | `Runs on the GROUND STATION` | yes |
| `realflight/watcher/mocap_watch.py` | 14 | `sends ONE LAND` | yes |
| `realflight/watcher/liveness.py` | 4 | `represented by a BEACON` | yes |
| `realflight/params/watcher_fc.parm` | 14 | `FS_GCS_ENABLE   5` | yes |
| `realflight/mcp1.py` | 1 | `MCP1` | yes |
| `METHODOLOGY.md` | 13651 | `Pi timing, ESTIMATED` | yes |
| `METHODOLOGY.md` | 12954 | `closed-loop real flights are FUTURE WORK` | yes |
| `docs/thesis/numbers.md` | 411 | `ArduPilot pinned commit` | yes |
| `src/estimators/ukf_core.py` | 7 | `15-state IMU-driven UKF` | yes |
| `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.h` | 2 | `AP_NavUKF: 15-state unscented Kalman filter` | yes |
| `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavFGO.h` | 2 | `run OUTSIDE ArduPilot` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_core.h` | 539 | `VectorN<ftype,24> Vector24` | yes |
| `src/estimators/measurement_models.py` | 29 | `N = 15` | yes |
| `src/estimators/ukf_core.py` | 7 | `delta-form biases matching EKF3` | yes |
| `FGO_DESIGN.md` | 141 | ``X(k)` ¦ `gtsam.Pose3`` | yes |
| `FGO_DESIGN.md` | 143 | ``B(k)`` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_core.h` | 575 | `QuaternionF quat;` | yes |
| `src/estimators/ukf_core.py` | 7 | `ZYX Euler` | yes |
| `src/estimators/fgo/fgo_core.py` | 120 | `Pose3(Rot3.Ypr(` | yes |
| `METHODOLOGY.md` | 10146 | `unscented RTS smoother` | yes |
| `src/estimators/fgo/fgo_core.py` | 90 | `BatchFixedLagSmoother(window, lm)` | yes |
| `METHODOLOGY.md` | 10129 | `The FGO uses window 0.25 s, batch fixed-lag, 2 LM iterations and 30 Hz keyframes` | yes |
| `docs/thesis/numbers.md` | 451 | `LM iterations cap` | yes |
| `src/estimators/fgo_cpp/src/fgo_cpp_node.cpp` | 62 | `window_s` | yes |
| `docs/thesis/numbers.md` | 183 | `Frames per prediction` | yes |
| `docs/thesis/numbers.md` | 184 | `derived, not logged` | yes |
| `docs/thesis/numbers.md` | 186 | `UKF predict dt` | yes |
| `docs/thesis/numbers.md` | 187 | `identical per-second densities` | yes |
| `CLAUDE.md` | 719 | `Feed every 333 Hz sample` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_MagFusion.cpp` | 263 | `lastSynthYawTime_ms > 140` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_MagFusion.cpp` | 274 | `> 0.01f` | yes |
| `docs/thesis/numbers.md` | 158 | `every 140 ms` | yes |
| `METHODOLOGY.md` | 9527 | `zero-innovation yaw pseudo-measurement` | yes |
| `src/estimators/ukf_core.py` | 46 | `YAW_DT=0.14` | yes |
| `src/estimators/ukf_core.py` | 47 | `ATT_VAR_GATE=0.04` | yes |
| `docs/thesis/numbers.md` | 160 | `UKF pseudo-yaw gate` | yes |
| `src/estimators/fgo/fgo_core.py` | 51 | `YAW_DT = 0.14` | yes |
| `src/estimators/fgo/fgo_core.py` | 52 | `ATT_VAR_GATE = 0.04` | yes |
| `METHODOLOGY.md` | 12353 | `FGO yaw cap: GATED` | yes |
| `METHODOLOGY.md` | 12338 | `EKF3 fuses flow at 15.1 Hz and range at 16 Hz` | yes |
| `METHODOLOGY.md` | 12359 | `recorded as EKF3 design under D18` | yes |
| `METHODOLOGY.md` | 12338 | `Flow and range fusion rates` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3.cpp` | 42 | `FLOW_I_GATE_DEFAULT` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_OptFlowFusion.cpp` | 665 | `_flowInnovGate` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_PosVelFusion.cpp` | 1022 | `_hgtInnovGate` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3.cpp` | 312 | `FLOW_MAX` | yes |
| `FGO_DESIGN.md` | 416 | `binary accept` | yes |
| `src/estimators/ukf_core.py` | 44 | `FLOW_GATE=300, FLOW_MAX=2.5` | yes |
| `src/estimators/ukf_core.py` | 45 | `RNG_GATE=500` | yes |
| `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp` | 40 | `FLOW_GATE = 300` | yes |
| `src/estimators/fgo/fgo_core.py` | 184 | `abs(flow_xy[0]) < 4.2` | yes |
| `src/estimators/fgo_cpp/src/fgo_core.cpp` | 144 | `std::abs(flow->xy[0]) < 4.2` | yes |
| `METHODOLOGY.md` | 8659 | `no gate` | yes |
| `FGO_DESIGN.md` | 446 | `matched NIS gate at factor-insertion time` | yes |
| `docs/thesis/numbers.md` | 450 | `UKF predict / forward update` | yes |
| `docs/thesis/numbers.md` | 445 | `FGO step, post-fix, baseline textured` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3.cpp` | 41 | `FLOW_M_NSE_DEFAULT      0.25f` | yes |
| `src/estimators/ukf_core.py` | 44 | `FLOW_M_NSE=0.25` | yes |
| `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp` | 40 | `FLOW_M_NSE = D(25, 100)` | yes |
| `src/estimators/fgo/fgo_core.py` | 97 | `Sigma(2, 0.25)` | yes |
| `METHODOLOGY.md` | 9522 | `¦ flow ¦ 0.25 rad/s` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3.cpp` | 293 | `RNG_M_NSE` | yes |
| `src/estimators/ukf_core.py` | 45 | `RNG_M_NSE=0.5` | yes |
| `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp` | 41 | `RNG_M_NSE = D(5, 10)` | yes |
| `src/estimators/fgo/fgo_core.py` | 98 | `Sigma(1, 0.5)` | yes |
| `METHODOLOGY.md` | 9523 | `¦ range ¦ 0.5 m` | yes |
| `METHODOLOGY.md` | 2887 | `EKF3 is the fixed no-yaw-source baseline` | yes |
| `src/estimators/measurement_models.py` | 191 | `np.radians(0.148)` | yes |
| `src/estimators/measurement_models.py` | 192 | `np.radians(0.126)` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_Measurements.cpp` | 1118 | `MAX(angErr, radians(5.0f))` | yes |
| `closedloop_heading.parm` | 15 | `VISO_YAW_M_NSE 0.05` | yes |
| `METHODOLOGY.md` | 7555 | `The UKF applies the heading at **5°**` | yes |
| `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp` | 523 | `radians(5.0f)` | yes |
| `src/estimators/fgo_cpp/src/fgo_cpp_node.cpp` | 70 | `heading_sigma_deg` | yes |
| `METHODOLOGY.md` | 9526 | `heading σ (closed loop)` | yes |
| `tags_extnav.parm` | 8 | `VISO_POS_M_NSE` | yes |
| `src/estimators/measurement_models.py` | 356 | `TAG_SIGMA_POS = 0.05` | yes |
| `METHODOLOGY.md` | 10064 | `position σ = max(`VISO_POS_M_NSE`, posErr) = 0.05 m` | yes |
| `h_extnav.parm` | 8 | `VISO_POS_M_NSE 0.02` | yes |
| `METHODOLOGY.md` | 10730 | `ROOM_TAG_SIGMA_POS=0.02` | yes |
| `run_trial.sh` | 423 | `tag_sigma_pos:=${TAG_SIGMA_POS:-0.02}` | yes |
| `run_trial.sh` | 449 | `tag_sigma_pos_m:=${TAG_SIGMA_POS:-0.02}` | **NO** |
| `src/estimators/measurement_models.py` | 355 | `max(VISO_YAW_M_NSE 0.05 rad, angErr, 5 deg) = 5 deg` | yes |
| `h_extnav.parm` | 9 | `VISO_YAW_M_NSE 0.05` | yes |
| `src/estimators/fgo_cpp/src/fgo_cpp_node.cpp` | 66 | `tag_sigma_yaw_deg` | yes |
| `METHODOLOGY.md` | 10336 | `σ 0.5 m, 0.3 m/s` | yes |
| `METHODOLOGY.md` | 10335 | `the samples EKF3 received` | yes |
| `src/estimators/ukf_core.py` | 46 | `YAW_M_NSE=max(0.5, 0.05)` | yes |
| `src/estimators/fgo/fgo_core.py` | 99 | `Sigma(1, 0.5)` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3.cpp` | 28 | `GYRO_P_NSE_DEFAULT` | yes |
| `src/estimators/ukf_core.py` | 21 | `DT_REF = 0.0125` | yes |
| `METHODOLOGY.md` | 9567 | `D27 RULED` | yes |
| `src/estimators/fgo/fgo_core.py` | 27 | `1.53125e-3` | yes |
| `docs/thesis/numbers.md` | 151 | `GTSAM conversion rule` | yes |
| `src/estimators/fgo_cpp/src/fgo_core.cpp` | 39 | `setAccelerometerCovariance` | yes |
| `CLAUDE.md` | 724 | `Standing caveat for all three estimators` | yes |
| `METHODOLOGY.md` | 12862 | `EKF3's 0.1 rad is recorded as EKF3's design` | yes |
| `src/estimators/ukf_core.py` | 321 | `np.radians(5)**2, np.radians(5)**2, np.radians(1)**2` | yes |
| `src/estimators/fgo/fgo_core.py` | 44 | `YAW0_SIGMA = np.radians(1)` | yes |
| `src/estimators/fgo/fgo_core.py` | 48 | `ROLLPITCH0_SIGMA = np.radians(5)` | yes |
| `docs/thesis/numbers.md` | 37 | `used the OLD priors` | yes |
| `METHODOLOGY.md` | 12338 | `EKF3 fuses flow at 15.1 Hz` | yes |
| `METHODOLOGY.md` | 12359 | `15 Hz flow fusion is recorded as EKF3 design` | yes |
| `docs/thesis/tier1/decisions_log.md` | 157 | `REOPENED` | yes |
| `docs/thesis/tier1/decisions_log.md` | 158 | `REOPENED` | yes |
| `METHODOLOGY.md` | 4896 | `VISO_YAW_M_NSE = 0.05` | yes |
| `METHODOLOGY.md` | 7553 | `Ruling D17` | yes |
| `METHODOLOGY.md` | 9528 | `documented asymmetry` | yes |
| `src/estimators/fgo/fgo_core.py` | 31 | `setIntegrationCovariance` | yes |
| `src/estimators/ukf_core.py` | 295 | `p['FLOW_GATE']` | yes |
| `src/estimators/ukf_core.py` | 231 | `p['RNG_GATE']` | yes |
| `src/estimators/fgo/fgo_core.py` | 184 | `< 4.2` | yes |
| `FGO_DESIGN.md` | 446 | `matched NIS gate` | yes |
| `METHODOLOGY.md` | 14302 | `FGO gating documented` | yes |
| `docs/thesis/diagnostics/numbers_fgo_gate_count.md` | 11 | `chi2(2)=11.83` | yes |
| `docs/thesis/diagnostics/numbers_fgo_gate_count.md` | 13 | `0.01%` | yes |
| `src/estimators/ukf_core.py` | 293 | `abs(flow_xy[0]) >= p['FLOW_MAX']` | yes |
| `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp` | 874 | `fabs(e.fr.x) < FLOW_MAX` | yes |
| `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_OptFlowFusion.cpp` | 668 | `flowRadXY.x < frontend->_maxFlowRate` | yes |
| `docs/thesis/diagnostics/fgo_gate_count_results.md` | 254 | `IDENTICAL in every single group, with no exception` | yes |
| `METHODOLOGY.md` | 7038 | `Ruling D15` | yes |
| `METHODOLOGY.md` | 7060 | `This is a sensor-model` | yes |
| `METHODOLOGY.md` | 7785 | `D18: no. PRINCIPLE` | yes |
| `PROGRESS.md` | 47 | `D18 principle recorded` | yes |
| `METHODOLOGY.md` | 8871 | `Under D18 they are not copied` | yes |
| `METHODOLOGY.md` | 12857 | `FGO initial yaw sigma, a MODEL CORRECTION under D18` | yes |
| `docs/thesis/numbers.md` | 36 | `Flown FGO results` | yes |
| `docs/thesis/tier1/decisions_log.md` | 153 | `corrected priors` | yes |
| `METHODOLOGY.md` | 12046 | `setBiasAccOmegaInit` | yes |
| `METHODOLOGY.md` | 12052 | `gyro ~26×, accelerometer ~5× looser` | yes |
| `src/estimators/fgo/fgo_core.py` | 35 | `setBiasAccOmegaInit(np.zeros((6, 6)))` | yes |
| `METHODOLOGY.md` | 12329 | `Both builds add 1e-12·I to P before the Cholesky` | yes |
| `METHODOLOGY.md` | 12343 | `UKF jitter: a MODEL CORRECTION under D18` | yes |
| `src/estimators/ukf_core.py` | 57 | `CHOL_JITTER_LADDER = (0.0, 1e-12, 1e-9, 1e-6)` | yes |
| `METHODOLOGY.md` | 11366 | `bias-corrected rate is ADOPTED as a MODEL CORRECTION` | yes |
| `METHODOLOGY.md` | 4069 | `lateral optical-flow sign is wrong` | yes |
| `METHODOLOGY.md` | 4155 | `Lateral flow sign — rulings, fix and verification` | yes |
| `docs/thesis/numbers.md` | 213 | `sign fix` | yes |
| `METHODOLOGY.md` | 8936 | `flow validity uses the feature count only` | yes |
| `FGO_DESIGN.md` | 424 | `No continuous R-scaling` | yes |
| `METHODOLOGY.md` | 1985 | `RULE — IMU gaps and the replay estimators` | yes |
| `METHODOLOGY.md` | 2487 | `IMU timing rule EXTENDED` | yes |
| `METHODOLOGY.md` | 10066 | `Gates: position 5σ, yaw 3σ` | yes |
| `METHODOLOGY.md` | 10134 | `No gate` | yes |
| `METHODOLOGY.md` | 11613 | `applied IDENTICALLY to EKF3, the UKF and the FGO` | yes |
| `METHODOLOGY.md` | 10336 | `**No gate**` | yes |
| `METHODOLOGY.md` | 10337 | `No reset or variance inflation on return` | yes |
| `METHODOLOGY.md` | 8043 | `not copied, per D18` | yes |
| `METHODOLOGY.md` | 8281 | `Cauchy, k = 2.385 chosen` | yes |
| `METHODOLOGY.md` | 10691 | `UKF:** ≤ 2× those` | yes |
| `METHODOLOGY.md` | 10509 | `RULING (user, 2026-10-08): T `VISO_DELAY_MS` stays 15 ms, no re-fly` | yes |
| `METHODOLOGY.md` | 10512 | `VISP receipt − capture was **17.5–26.6 ms**, so 15 ms is up to **12 ms short**` | yes |
| `METHODOLOGY.md` | 10514 | `the ExternalNav delay applies to **both** position and yaw fusion` | yes |
| `METHODOLOGY.md` | 10528 | `The UKF and FGO replay `/tags/sent` at the capture stamp and are not affected at all` | yes |
| `docs/thesis/numbers.md` | 542 | `the per-fix bound is ≤ 6 mm nominal, ≤ 22 mm at the measured 1.80 m/s` | yes |
| `docs/thesis/numbers.md` | 543 | `≤ 0.06° in yaw` | yes |
| `docs/thesis/thesis_vocabulary.md` | 41 | `**1A**` | yes |
| `METHODOLOGY.md` | 865 | `3 corridor worlds × 3 repeats` | yes |
| `METHODOLOGY.md` | 5640 | `7 new repeats` | yes |
| `METHODOLOGY.md` | 2874 | `flown on simulator truth` | yes |
| `docs/thesis/thesis_vocabulary.md` | 148 | `H1.1` | yes |
| `METHODOLOGY.md` | 2692 | `the six `p1c_*` check flights only` | yes |
| `METHODOLOGY.md` | 2706 | `the 18 dataset bags` | yes |
| `docs/thesis/thesis_vocabulary.md` | 149 | `H1.2` | yes |
| `METHODOLOGY.md` | 2958 | `EKF3 is the fixed no-yaw-source baseline` | yes |
| `METHODOLOGY.md` | 2970 | `90 replay runs` | yes |
| `docs/thesis/thesis_vocabulary.md` | 150 | `H1.3` | yes |
| `docs/thesis/thesis_vocabulary.md` | 152 | `C1.a` | yes |
| `METHODOLOGY.md` | 7880 | `existing recordings only` | yes |
| `METHODOLOGY.md` | 7922 | `≥ 4 of 6` | yes |
| `METHODOLOGY.md` | 7956 | `only the UKF and FGO are compared` | yes |
| `docs/thesis/thesis_vocabulary.md` | 153 | `H1.4` | yes |
| `METHODOLOGY.md` | 9706 | `n = 6 per world (12 flights)` | yes |
| `batches/f4_robust.conf` | 1 | `truth flies` | yes |
| `docs/thesis/thesis_vocabulary.md` | 159 | `H1.7a` | yes |
| `docs/thesis/thesis_vocabulary.md` | 41 | `**1C**` | yes |
| `docs/thesis/numbers.md` | 464 | `n = 1 per no-heading cell` | yes |
| `METHODOLOGY.md` | 7795 | `All FGO closed-loop flights fly at half` | yes |
| `docs/thesis/thesis_vocabulary.md` | 162 | `H1.8` | yes |
| `docs/thesis/thesis_vocabulary.md` | 163 | `H1.9` | yes |
| `METHODOLOGY.md` | 10107 | `10 × 10 m room` | yes |
| `METHODOLOGY.md` | 10123 | `12 flights` | yes |
| `METHODOLOGY.md` | 10114 | `EKF3 receives it live` | yes |
| `docs/thesis/thesis_vocabulary.md` | 170 | `H2.1` | yes |
| `METHODOLOGY.md` | 10493 | `L uses T_A_r1, T_A_r2 and T_A_r3` | yes |
| `METHODOLOGY.md` | 10456 | `**FGO capability**` | yes |
| `docs/thesis/thesis_vocabulary.md` | 179 | `V3` | yes |
| `METHODOLOGY.md` | 10301 | `open loop on simulator truth` | yes |
| `METHODOLOGY.md` | 10310 | `Three repeats.` | yes |
| `o_gnss.parm` | 2 | `AHRS_EKF_TYPE 10` | yes |
| `docs/thesis/thesis_vocabulary.md` | 189 | `H4.1` | yes |
| `METHODOLOGY.md` | 10661 | `EKF3 flies` | yes |
| `docs/tag_hold_design.md` | 141 | `Repeats: 3 per stage and estimator` | yes |
| `docs/thesis/numbers.md` | 635 | `×3 each` | yes |
| `docs/thesis/numbers.md` | 649 | `are PRIMARY` | yes |
| `docs/thesis/thesis_vocabulary.md` | 197 | `H5.1` | yes |
| `METHODOLOGY.md` | 11286 | `Option (i) safety tests` | yes |
| `docs/thesis/numbers.md` | 490 | `Safety tests (H config, 2 m-clearance hold)` | yes |
| `docs/thesis/thesis_vocabulary.md` | 58 | `They therefore carry criteria (S-A1–S-A4)` | yes |
| `METHODOLOGY.md` | 3329 | `p95 ≤ 2.1 ms` | yes |
| `docs/thesis/numbers.md` | 448 | `transition baseline` | yes |
| `docs/thesis/numbers.md` | 449 | `blank baseline` | yes |
| `docs/thesis/numbers.md` | 209 | `FGO deployability budget` | yes |
| `eval/results/fgo_cpp_arm64/RESULTS.md` | 66 | `0.53 / 0.92 ms` | yes |
| `eval/results/fgo_cpp_arm64/RESULTS.md` | 67 | `0.91 / 1.68 ms` | yes |
| `METHODOLOGY.md` | 13567 | `¦ MatekH743 ¦` | yes |
| `METHODOLOGY.md` | 13568 | `¦ Pixhawk6X ¦` | yes |
| `METHODOLOGY.md` | 13570 | `UKF 13.7 kB flash` | yes |
| `docs/handovers/2026-10-11_board_firmware_h743.md` | 58 | `5.8 kB of shared plumbing` | yes |
| `METHODOLOGY.md` | 13570 | `FGO 4.6 kB / ~14.8 kB` | yes |
| `METHODOLOGY.md` | 13571 | `CPU ESTIMATED 2–6%` | yes |
| `docs/board_firmware_plan.md` | 161 | `replays up to about 100 buffered IMU steps per state` | yes |
| `METHODOLOGY.md` | 13674 | `A Pi 5 is RECOMMENDED` | yes |
| `METHODOLOGY.md` | 13655 | `43–52 MB qemu peak` | yes |
| `docs/thesis/numbers.md` | 470 | `EKF3 full / half` | yes |
| `docs/thesis/numbers.md` | 471 | `UKF full (old UKF, jitter) / half` | yes |
| `METHODOLOGY.md` | 7771 | `the FGO step is 42–49 ms` | yes |
| `METHODOLOGY.md` | 7803 | `given sufficient compute` | yes |
| `sim/worlds/corridor_textured_half_fwdc.sdf` | 44 | `<real_time_factor>0.5</real_time_factor>` | yes |
| `METHODOLOGY.md` | 13609 | `tipped over` | yes |
| `docs/handovers/2026-10-12_f8_investigation.md` | 21 | `It follows from F8` | yes |
| `METHODOLOGY.md` | 14014 | `the pilot disarms within 2 s` | yes |
| `METHODOLOGY.md` | 13607 | `LAND retry (every 0.3 s` | yes |
| `METHODOLOGY.md` | 13820 | `LAND is re-sent only while` | yes |
| `METHODOLOGY.md` | 13876 | `each sent exactly ONE LAND` | yes |
| `METHODOLOGY.md` | 13886 | `arming is allowed with a 22` | yes |
| `METHODOLOGY.md` | 13893 | `F7:` | yes |
| `METHODOLOGY.md` | 13936 | `SITL-bench PASSED` | yes |
| `METHODOLOGY.md` | 13938 | `must agree with the mocap heading` | yes |
| `METHODOLOGY.md` | 14102 | `F7-a:` | yes |
| `METHODOLOGY.md` | 13909 | `CONFIRMED, stock EKF3 logic` | yes |
| `METHODOLOGY.md` | 13919 | `5/46 arms` | yes |
| `METHODOLOGY.md` | 13927 | `LOW on the first arm` | yes |
| `METHODOLOGY.md` | 13834 | `B8a verdict` | yes |
| `METHODOLOGY.md` | 13841 | `Without an origin, the stock EKF failsafe never runs` | yes |
| `METHODOLOGY.md` | 13874 | `LAND (EKF_FAILSAFE) 1.94 s` | yes |
| `METHODOLOGY.md` | 13892 | `EKF origin` | yes |
| `METHODOLOGY.md` | 14116 | `the FC refuses only ~3.3 s` | yes |
| `METHODOLOGY.md` | 14161 | `SAFETY OBSERVATION (void attempt 4)` | yes |
| `METHODOLOGY.md` | 14162 | `The FC-side gap is ~3.3–3.6 s` | yes |
| `METHODOLOGY.md` | 14134 | `NO RE-ARM WITHIN 10 s` | yes |
| `METHODOLOGY.md` | 13593 | `B10b passed ONLY because` | yes |
| `METHODOLOGY.md` | 13987 | `H10 guard MERGED` | yes |
| `METHODOLOGY.md` | 13997 | `The guard is ACCEPTED` | yes |
| `METHODOLOGY.md` | 14010 | `M1 (procedural)` | yes |
| `METHODOLOGY.md` | 14153 | `after M1, the origin is re-verified` | yes |
| `METHODOLOGY.md` | 14011 | `M2 (detection)` | yes |
| `METHODOLOGY.md` | 14155 | `M2-R PASSES AS WORDED` | yes |
| `METHODOLOGY.md` | 14158 | `withdrew at the first` | yes |
| `METHODOLOGY.md` | 14014 | `M3 (procedural)` | yes |
| `docs/handovers/2026-10-12_m2_full_bench.md` | 79 | `M3 in the harness` | yes |
| `METHODOLOGY.md` | 13133 | `stock ArduCopter refuses to arm only AFTER` | yes |
| `METHODOLOGY.md` | 13601 | `Stock-firmware arming, CONFIRMED in SITL` | yes |
| `METHODOLOGY.md` | 13750 | `B5/B8a/G6 rulings` | yes |
| `docs/real_flights_plan.md` | 442 | `¦ G1 ¦` | yes |
| `METHODOLOGY.md` | 13122 | `Real-hardware mocap watcher BUILT (G1–G11)` | yes |
| `docs/handovers/2026-10-10_mocap_watcher_build.md` | 52 | `The FC-side` | yes |
| `METHODOLOGY.md` | 13615 | `B4d, the B6 hand procedure` | yes |

## Not buildable from existing sources (reported, not filled)

- EKF3 offline step time: none exists (EKF3 runs only inside ArduPilot).
- EKF3 flight-controller CPU, flash and RAM: not measured (part of stock firmware).
- The FGO interface's flight-controller CPU: not estimated.
- A ruling for the FGO's missing flow/range NIS gate and for the two-sided FLOW_MAX of the UKF (Table 3.3, rows 5–6).
- The G6 ruling (stock-firmware arming without a watcher): open (M:13750).
- Thesis names for the safety codes F2, F6, F7, F8, B8a, H10 and M1–M3: none in the vocabulary; Table 8.2 uses descriptive proposals.
