# Thesis Project: Indoor Drone State Estimation

## Overview

Master's thesis comparing **EKF**, **UKF**, and **online Factor Graph Optimisation (FGO)**
for indoor UAV state estimation in GNSS-denied environments, with emphasis on
**robustness under degraded sensing** (low-texture scenes, transitions between
feature-rich and feature-poor regions).

Estimators will be evaluated against ground truth (Gazebo first, motion capture
later) under nominal and degraded sensing conditions, and across commanded
velocity as a second experimental axis (see Experimental Design Notes).

## Software Stack

| Component     | Detail                                                         |
|---------------|----------------------------------------------------------------|
| OS            | Ubuntu 24.04                                                   |
| Simulator     | Gazebo **Harmonic** — use `gz` CLI only, never `ign`/`gazebo` |
| Autopilot     | ArduPilot SITL (ArduCopter), venv at `~/venv-ardupilot`       |
| Middleware    | ROS2 **Jazzy**                                                 |
| Bridge        | `ros_gz_bridge` (standard, no custom config file)             |
| Vision        | OpenCV (Python) — Shi-Tomasi + Lucas-Kanade in `flow_tracker.py` |
| FGO library   | GTSAM (planned, not yet integrated)                           |
| Evaluation    | `evo` for ATE / RPE, venv at `~/venv-evo`, wrapped by `evaluate_trial.sh` |
| Language      | Australian English in all comments, docs, and prose            |

## Key Paths

| Item                        | Path                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| ArduPilot SITL              | `~/ardupilot`                                                        |
| Gazebo plugin + iris/runway meshes | `~/ardupilot_gazebo` (upstream base `082a0fe`; ArduPilotPlugin + meshes) |
| **Worlds (tracked — run from here)** | `~/thesis_ws/sim/worlds/`                                       |
| **Degraded world (blank)**  | `~/thesis_ws/sim/worlds/iris_runway.sdf`                             |
| **Nominal world (textured)**| `~/thesis_ws/sim/worlds/iris_textured.sdf`                           |
| **Corridor world (nominal)**    | `~/thesis_ws/sim/worlds/corridor_textured.sdf`                   |
| **Corridor world (degraded)**   | `~/thesis_ws/sim/worlds/corridor_blank.sdf`                      |
| **Corridor world (transition)** | `~/thesis_ws/sim/worlds/corridor_transition.sdf`                 |
| **Forward-camera corridor worlds** | **USE** `sim/worlds/corridor_{textured,blank,transition}_fwdc.sdf` (line-textured walls = UPPER BOUND) and `..._fwdplainc.sdf` (plain walls = featureless case), both with a plain ceiling (`corridor_ceiling`). The no-ceiling `_fwd`/`_fwdplain` worlds and the `fwd_*` dataset are **SUPERSEDED** (sky visible; kept, not analysed). `run_trial.sh` enables forward-camera recording for all four suffixes — see METHODOLOGY |
| Custom floor/wall models (tracked) | `~/thesis_ws/sim/models/`                                        |
| Drone SDF (edit + mirror)   | `~/ardupilot_gazebo/models/iris_with_standoffs/model.sdf` → mirror to `sim/reference/` |
| ROS2 workspace              | `~/thesis_ws`                                                        |

> **Sim assets are vendored (2026-07-29).** The worlds and custom floor/wall
> models live in and **run from** `~/thesis_ws/sim/` — `run_trial.sh`/`start_sim.sh`
> prepend `sim/models` to `GZ_SIM_RESOURCE_PATH` and load worlds by absolute path
> from `sim/worlds/`, so a `thesis_ws` commit pins the environment (each trial's
> `metadata.yaml` also records the live `ardupilot_gazebo_commit` +
> `ardupilot_gazebo_upstream_base` for the un-vendored meshes). **Edit worlds and
> floor/wall models in `sim/`, not `~/ardupilot_gazebo`** — the latter's copies
> are shadowed and silently ignored. **One exception — the iris drone:** it still
> resolves from `~/ardupilot_gazebo` (22 MB meshes), so edit its sensors in
> `~/ardupilot_gazebo/models/iris_with_standoffs/model.sdf` **and** mirror to
> `sim/reference/iris_with_standoffs.model.sdf`. See `sim/README.md`.
| Optical flow package        | `~/thesis_ws/src/optical_flow_node/`                                 |
| Flow node entry point       | `~/thesis_ws/src/optical_flow_node/optical_flow_node/flow_tracker.py`|
| **Message definitions**     | `~/thesis_ws/src/optical_flow_interfaces/msg/OpticalFlow.msg`        |
| **Ground truth publisher**  | `~/thesis_ws/ground_truth_pub.py`                                    |
| **Attitude bridge**         | `~/thesis_ws/attitude_bridge.py`                                     |
| **LiDAR bridge**            | `~/thesis_ws/lidar_bridge.py`                                        |
| **LiDAR RNGFND1 params**    | `~/thesis_ws/lidar_rangefinder.parm`                                 |
| **Flow EKF bridge**         | `~/thesis_ws/flow_bridge.py`                                         |
| **Flow EKF3 params**        | `~/thesis_ws/flow_ekf.parm`                                          |
| **GNSS-denied params**      | `~/thesis_ws/gnss_denied.parm`                                       |
| **No-yaw comparison params (used by `run_trial.sh` for all `dsn_*` and forward-camera datasets)** | `~/thesis_ws/gnss_denied_nomag.parm` (+ `sim_noise.parm`) — the three-way comparison config (METHODOLOGY "Comparison dataset — nomag") |
| **EKF pose bridge**         | `~/thesis_ws/ekf_bridge.py`                                          |
| **IMU bridge**               | `~/thesis_ws/imu_bridge.py`                                          |
| **evo venv**                 | `~/venv-evo`                                                         |
| **FGO venv (GTSAM)**         | `~/venv-fgo` (gtsam 4.2.1 + rosbags; numpy 1.26 — kept separate from `venv-evo`'s numpy 2.x) |
| **Estimators (UKF + FGO)**  | `~/thesis_ws/src/estimators/` (`ukf_core.py`, `measurement_models.py`, `fgo/`) |
| **Trial recorder**          | `~/thesis_ws/record_trial.sh`                                        |
| **Trial evaluator**         | `~/thesis_ws/evaluate_trial.sh`                                      |
| **Resumable batch runner (use for datasets)** | `~/thesis_ws/run_resumable_batch.sh <conf> <batch>` — run in tmux; state in `~/thesis_data/batches/<batch>/` (`trials.log`, `STATUS`, `DONE`/`FAILED`); re-run the same command after a crash to resume (partial trial → `ABORTED.txt`, renamed aside) |
| ArduPilot dataflash logs    | `~/ardupilot/ArduCopter/logs/` (`.BIN` files, written by SITL)      |
| Trial data output           | `~/thesis_data/trials/`                                              |

## Drone Model

The world SDF includes `iris_with_ardupilot`, which itself includes
`iris_with_standoffs`. The Gazebo model name (as it appears in topics like
`dynamic_pose/info`) is **`iris_with_ardupilot`**. The gimbal joint limits are
fixed at zero — the camera is **rigidly mounted** with no active stabilisation.
No changes to the gimbal model beyond adding the downward camera to
`iris_with_standoffs/model.sdf`.

**Implication:** rotational body motion couples into pixel flow. Raw gyro
rates are therefore a required input alongside raw flow for every estimator
to derotate internally — see [Sensor Fusion Architecture](#sensor-fusion-architecture).

## Corridor Worlds — Long-Duration Degraded-Sensing Trials

*(Section rewritten 2026-09-29 to match METHODOLOGY. The original 2026-07 text, including
the investigation of the now-fixed Known Issues #11/#12, is in git history and in
`docs/thesis/export_2026-09-29_d89a902/CLAUDE.md`.)*

**All worlds live in, and run from, `~/thesis_ws/sim/worlds/`** (vendored; see the Key
Paths note). Geometry is common to all of them:
- **Corridor:** 20 m wide (x = −10…10 m) and 160 m long (y = 0…160 m), along world +Y.
- **Walls:** 5 m tall and 0.2 m thick at x = ±10 m, spanning y = −5…165 m.
- **Lighting:** the same directional sun as `iris_textured.sdf`.
- **Spawn:** `iris_with_ardupilot` at (0, 0, 0.195), yaw 90°. That is ArduPilot yaw 0,
  NED-North, and the flight direction.
- **Floor:** 9 visual-only tiles (y = −20…160 m) plus **exactly one
  `model://ground_collision`**. This is the Known Issue #11 fix: coincident infinite
  collision planes had cut RTF 30×.
- **Blank floors:** they use visual `blank_ground_visual` tiles with the same material
  minus the albedo map (the Known Issue #12 fix: `gpu_lidar` raycasts the *rendered*
  scene).
- **Floor texture is the only variable between the three floor conditions.**

| world set | floor conditions | walls / ceiling / camera | status |
|---|---|---|---|
| `corridor_{textured,blank,transition}.sdf` | textured / blank / transition (textured y < 80 m, blank y > 80 m) | plain grey walls, no ceiling, downward sensors only | **CURRENT**: `dsn_*` baseline datasets |
| `corridor_*_fwdc.sdf` | same three | **line-textured walls + plain ceiling**, `iris_fwd` forward camera | **CURRENT**: `fwdc_*` (upper bound) |
| `corridor_*_fwdplainc.sdf` | same three | **plain walls + plain ceiling**, `iris_fwd` | **CURRENT**: `fwdplainc_*` (featureless case) |
| `corridor_*_fwd.sdf`, `corridor_*_fwdplain.sdf` | same three | no ceiling, so the forward camera **sees the cloud skybox** | **SUPERSEDED** (kept, not analysed) |

- **The transition boundary is at y = 80 m.** Flow `inlier_ratio` switches in the 80–82 m
  bin in every flight.
- **Verified end to end:** all worlds fly full 300 s trials at RTF ≈ 0.74–0.92, and
  LiDAR reads the floor everywhere.
- **Launch:** `./run_trial.sh --world <name> ...` (harness), or `./start_sim.sh <world>.sdf`
  (manual).
- The ceiling is `corridor_ceiling` (visual-only, non-shadow-casting, underside at 5 m).
  The ceiling vs no-ceiling transition-flow effect size (+0.43 px/s, p = 0.31) must be
  stated in any ceiling-vs-`dsn` comparison on the transition world (METHODOLOGY standing
  rule).

## Ground Truth Bridging

Ground truth is obtained from Gazebo's `dynamic_pose/info` topic, **not** from
ArduPilot's EKF estimate.

**Bridge type:** `gz.msgs.Pose_V → geometry_msgs/msg/PoseArray` (`[gz.msgs.Pose_V`)

> **Do NOT use `tf2_msgs/TFMessage`** for this topic. In ros_gz_bridge 1.0.22,
> the `Pose_V → TFMessage` conversion zeroes all header stamps and clears all
> `child_frame_id` and `frame_id` fields, making it useless for ground truth.
> The `PoseArray` conversion preserves the outer Pose_V header (sim timestamp).

`ground_truth_pub.py` subscribes to `/world/<world>/dynamic_pose/info`
(PoseArray), selects `poses[0]` — which is always the top-level model
**`iris_with_ardupilot`** in world-frame coordinates — and republishes as
`geometry_msgs/PoseStamped` on `/ground_truth/pose`. Verified: 57–227 Hz,
sim-time stamps (`header.stamp` tracks `/clock`).

## Sensor Status

| Sensor          | Status            | Notes                                                        |
|-----------------|-------------------|--------------------------------------------------------------|
| IMU             | Working           | Via ArduPilot SITL                                           |
| Downward camera | Working           | Defined in `iris_with_standoffs/model.sdf`; mounted at **z = −0.25 m** relative to `base_link` origin; publishes `/downward_camera/image` and `/downward_camera/camera_info` |
| Optical flow    | Working — publishing, fused by EKF3 (Stage A) | Publishes `/optical_flow/measurement` (`optical_flow_interfaces/OpticalFlow`). RANSAC tested; ~145 px/s at 0.5 m/s matches theory. `flow_x_raw`/`flow_y_raw` are the **production values** — raw, un-derotated flow. `flow_x`/`flow_y` are a manual derotation (`enable_derotation` param, default on) kept for **characterisation only**, not fed to any estimator. `flow_x_rad`/`flow_y_rad` (rad/s, sensor-native camera-optical frame) are now populated (`flow_x_raw`/`FOCAL_LENGTH_PX`) and fed to ArduPilot EKF3 via `flow_bridge.py` — see "Downward Optical Flow — EKF3 Fusion (Stage A)" below. Needs shadow rejection |
| Downward LiDAR  | Stage 1 done — SDF sensor + ROS bridge, verified | Single-beam `gpu_lidar` in `iris_with_standoffs/model.sdf`, mounted at **z = −0.12 m** relative to `base_link` origin, pointing straight down. Emits `gz.msgs.LaserScan` on gz topic `/downward_lidar/range`, bridged to ROS2 as `sensor_msgs/msg/Range` on the same topic name. Range 0.05–40 m. Verified against `/ground_truth/pose` z during a 2 m hover: sub-millimetre accuracy (383/383 samples within 5 cm, mean error 0.1 mm) once settled. `min_angle`/`max_angle` **must both be exactly 0** for a 1-sample axis — Ogre2GpuRays warns and silently ignores `max_angle` otherwise, and an earlier attempt at a small nonzero FOV was a red herring; the real fix for transient short-range noise was moving the mount from −0.05 m to −0.12 m to clear the airframe's own belly mesh (a ray originating too close to the body can graze it under small attitude jitter). `update_rate` is **30 Hz**, matching the camera/flow rate (kept at 30, not raised — see below). **The sim's real-time factor (RTF) is the actual rate bottleneck, not `update_rate`**: this machine runs the model at RTF ≈ 0.05–0.17 (measured via `gz topic -e -t /stats`), even standalone/headless with no GUI or ArduPilot attached, so the *wall-clock* topic rate (what `ros2 topic hz` reports) is roughly `update_rate × RTF` — measured ~3.6–4 Hz at 30 Hz configured, which is what looked like a "slow LiDAR" but is really just RTF. The sensor's **true sim-time rate is correct**: consecutive `sensor_msgs/Range` header stamps on `/downward_lidar/range` are spaced exactly 33.00 ms apart (100-sample check), i.e. genuine 30.3 Hz in simulated time, independent of wall-clock slowdown. Bumping `update_rate` higher (tried 50 Hz) does raise the wall-clock rate roughly proportionally, but doesn't fix the underlying RTF and wasn't kept — 30 Hz matches the camera/flow cadence, which is what actually matters for fusion. When reasoning about any sensor's "Hz" in this project, use sim-time (header-stamp deltas), not wall-clock `topic hz`, unless wall-clock behaviour specifically is what's being investigated. Stage 2 (MAVLink `DISTANCE_SENSOR` injection, not `SIM_SONAR`) done and verified — see "Downward LiDAR — Stage 2" below. |
| Forward camera  | Phase 3 measurements implemented + validated (offline) | `iris_fwd`: level forward camera (60°, 640×480, 30 Hz, mono) in the ceiling worlds `corridor_*_fwdc` (textured walls = upper bound) / `corridor_*_fwdplainc` (plain walls = featureless case). `src/forward_camera/fwd_measure.py` gives **heading** from the corridor vanishing point (LSD + RANSAC, per-frame confidence, "no measurement" near the end wall) and **yaw rate** from horizontal forward flow near the VP. Validated heading: textured walls 9/9, plain walls on blank/transition floors; fails plain walls over a checker floor. Yaw rate: textured walls only. **EKF3 ruling (2026-09-29): EKF3 is the fixed no-yaw-source baseline offline; only the UKF/FGO get forward arms** (EKF3 has one downward flow sensor only; ExternalNav yaw needs a position per message and has a `VISO_YAW_M_NSE` floor; our logs have `LOG_REPLAY=0`). **Supervisor direction (2026-09-29):** UKF/FGO to run onboard as EKF3 drop-in replacements, real mocap flights in scope, forward camera flown only once verified in sim. See METHODOLOGY. |

### Downward LiDAR — Stage 2 (MAVLink injection)

`lidar_bridge.py` subscribes to `/downward_lidar/range` and injects each
reading into ArduPilot as `RNGFND1` via MAVLink `DISTANCE_SENSOR`, on its own
dedicated UDP port **14552** (`14550` is `fly_forward.py`, `14551` is
`attitude_bridge.py`) — see Terminal 8 below and Key Paths. Deliberately
**not** using ArduPilot's built-in `SIM_SONAR`/Analog rangefinder simulation,
consistent with this project's render-driven-sensing philosophy: the
distance ArduPilot sees comes from the same Gazebo raycast as everything
else, not a separate SITL physics shortcut.

**RNGFND1 parameters** (`lidar_rangefinder.parm`, appended via
`--add-param-file` so it loads *after*, and overrides, `gazebo-iris.parm`'s
`RNGFND1_TYPE 1`/Analog/SIM_SONAR block):
```
RNGFND1_TYPE 10      # MAVLink
RNGFND1_ORIENT 25    # Down / ROTATION_PITCH_270 (matches DISTANCE_SENSOR's orientation field)
RNGFND1_MIN 0.05     # metres — matches the gpu_lidar's <range><min>
RNGFND1_MAX 40       # metres — matches the gpu_lidar's <range><max>
```
Confirmed via `~/ardupilot/libraries/AP_RangeFinder/AP_RangeFinder_Params.cpp`
(this build, `ArduPilot-4.6.0-beta1-6521-g7bac20cbcc`, already has the
Dec-2024 `RNGFND1_MIN_CM`/`MAX_CM` → `RNGFND1_MIN`/`MAX` rename, so these are
**metres**, not centimetres) rather than trusted from memory.
`AP_RangeFinder_MAVLink::handle_msg` only checks
`packet.orientation == orientation()` to accept a reading — no serial port
wiring needed, since `DISTANCE_SENSOR` is handled generically for any
connected MAVLink channel in `GCS_Common.cpp`.

**Verified** (2 m hover, direct comparison against `/ground_truth/pose` via
MAVLink `RANGEFINDER` + `SYS_STATUS`):
- `SYS_STATUS` reports the rangefinder sensor bit `present=enabled=healthy=True`.
- During steady hover: mean error **0.17 mm**, max **10 mm** (6 samples,
  1 cm MAVLink quantisation) — matching Stage 1's raw-sensor accuracy.
- During the dynamic climb: **~3% transient dropout rate** (occasional single
  samples reading near-zero instead of true altitude) — same
  self-occlusion/attitude-jitter characteristic noted in Stage 1, surfacing
  here under more aggressive attitude excursions than Stage 1's gentle hover
  test covered. **Currently harmless**: `EK3_SRC1_POSZ=1` (Baro) and
  `EK3_RNG_USE_HGT=-1` (disabled) by default, so RNGFND1 isn't fused into
  the EKF's height estimate or flight control at all in this configuration —
  confirmed by param readback, not assumed. Worth revisiting (e.g. filtering
  dropouts in `lidar_bridge.py`, or characterising the self-occlusion angle
  threshold) before ever enabling `EK3_RNG_USE_HGT` or surface tracking.
- A MAVProxy stream freshly requesting `RANGEFINDER` needs periodic
  re-assertion (every ~2 s) to counter MAVProxy silently overriding a
  one-shot `SET_MESSAGE_INTERVAL` with its own low default rate — the same
  issue already fixed in `attitude_bridge.py` (see Known Issues). Only
  affects code that *requests telemetry from* the vehicle;
  `lidar_bridge.py` itself only sends, so it isn't affected.

`/downward_lidar/range` is recorded by default in `record_trial.sh` trials
(unconditionally — one float per message is lightweight, unlike the raw
camera images gated behind `--with-images`).

### Downward Optical Flow — EKF3 Fusion (Stage A)

**Stage A proves flow velocity fusion only — it is NOT a GNSS-denied
navigation config.** `EK3_SRC1_POSXY` is deliberately left at its default
(GPS) throughout; only `EK3_SRC1_VELXY` switches to flow. GPS still supplies
absolute position the whole time. Removing GPS entirely (flow + rangefinder
for full GNSS-denied position) is a separate, later step — don't conflate
the two when reading trial data from this stage.

**`OPTICAL_FLOW_RAD` is not usable — use `OPTICAL_FLOW` instead.** Traced
the full incoming-message dispatch in `GCS_Common.cpp::handle_message()`
(the same switch statement handling `DISTANCE_SENSOR`, see Stage 2 above):
there is no `case MAVLINK_MSG_ID_OPTICAL_FLOW_RAD` and no `default:` case
either, so an injected `OPTICAL_FLOW_RAD` message is silently dropped in
this ArduPilot build — never reaching any backend. What's actually wired up
for `FLOW_TYPE=5` (MAVLink) is `MAVLINK_MSG_ID_OPTICAL_FLOW` (message 100,
not 106) → `AP_OpticalFlow_MAV::handle_msg()`, which reads the message's
`flow_rate_x`/`flow_rate_y` **extension fields** (rad/s, **instantaneous
rate**, not integrated) in preference to the deprecated `flow_x`/`flow_y`
int16 fields. That backend does **not** read any gyro field from the
message — it samples `AP::ahrs().get_gyro()` internally for body-rate
compensation — so `flow_bridge.py` sends flow only, and `FLOW_OPTIONS` must
**not** have "Stabilised" set (our flow is raw/un-derotated; ArduPilot
derotates with its own AHRS gyro, which is the intended behaviour).

**`flow_rate_x`/`flow_rate_y` are MAVLink v2 extension fields** — absent
from pymavlink's default v1 dialect (confirmed empirically:
`MAVLink_optical_flow_message.fieldnames` omits them, and
`optical_flow_send()`'s signature has no `flow_rate_x`/`flow_rate_y`
parameter, unless `MAVLINK20=1` is set as an environment variable **before**
`from pymavlink import mavutil` is executed, which switches the loaded
dialect module from `dialects/v10/` to `dialects/v20/`). `flow_bridge.py`
sets this at the top of the file. `attitude_bridge.py`/`lidar_bridge.py`
don't need it — `ATTITUDE` and `DISTANCE_SENSOR` have no extension fields.

**Axis/sign mapping** (camera optical/pixel frame → MAVLink body-relative
frame): `flow_x_rad`/`flow_y_rad` are in the camera's optical/pixel frame
(X=image-right, Y=image-down; see `flow_tracker.py`). Best-derived (not
assumed) from `flow_tracker.py`'s own already-validated rotation-derotation
formula (`flow_x_rot = -FOCAL*rollspeed`, `flow_y_rot = +FOCAL*pitchspeed`)
compared against `OPTICAL_FLOW`'s field convention ("RH rotation about X
induces **positive** `flow_rate_x`"; "RH rotation about Y induces
**positive** `flow_rate_y`"): our `flow_x_rot` has the opposite sign to
what positive roll should give under the message's own convention, so
`flow_rate_x = -flow_x_rad`; `flow_y_rot` already matches, so
`flow_rate_y = +flow_y_rad` (no flip). **Empirically confirmed correct**
(see Verification below) — do not assume this transfers to a different
camera mount without re-deriving and re-verifying.

**RNGFND1/RangeFinder use:** `ground_distance` is populated from
`/downward_lidar/range` (cached, reported as `-1`/unknown if the last
reading is >0.5 s stale) but is **not read at all** by
`AP_OpticalFlow_MAV::handle_msg()` — confirmed by reading the backend
directly. It's included for completeness/other consumers, not because
EKF3's flow fusion needs it via this field (rangefinder height comes from
`RNGFND1` directly, see Stage 2).

**Params** (`flow_ekf.parm`, `--add-param-file`, alongside
`lidar_rangefinder.parm`):
```
FLOW_TYPE 5          # MAVLink — selects AP_OpticalFlow_MAV
EK3_SRC1_VELXY 5      # OpticalFlow — required by NavEKF3_core::readyToUseOptFlow()
EK3_FLOW_USE 1        # Navigation (not Terrain-only) — readyToUseOptFlow() hard-fails on FLOW_USE=2
```
Confirmed `NavEKF3_core::readyToUseOptFlow()`'s exact preconditions by
reading `AP_NavEKF3_Control.cpp` directly: `EK3_FLOW_USE==1`,
`EK3_SRCx_VELXY==OpticalFlow` for the active source set, flow data younger
than 200 ms, `tiltAlignComplete`, and `delAngBiasLearned` (gyro bias
converged) — all satisfied in verification.

**Gotcha: SITL's persisted `eeprom.bin` can silently defeat `--add-param-file`.**
`FLOW_TYPE` initially read back as `10` (SITL) instead of the `5` in
`flow_ekf.parm`, despite `EK3_SRC1_VELXY`/`EK3_FLOW_USE` from the *same*
file applying correctly. Root cause: `AP_Param::configured_in_storage()` —
once a param has *any* explicitly-stored value in the SITL vehicle's
persisted `eeprom.bin` (`~/ardupilot/ArduCopter/eeprom.bin`, gitignored,
carries over across SITL sessions in the same working directory),
`--defaults`/`--add-param-file` no longer override it; defaults only apply
to still-untouched params. Fixed **without deleting the eeprom** (that's
destructive local state, not something to reset without asking) by a live
`PARAM_SET FLOW_TYPE=5` over MAVLink followed by
`MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN` (a soft in-process SITL reboot, same
`arducopter` PID, no relaunch needed) — `FLOW_TYPE` is `AP_PARAM_FLAG_ENABLE`
and backends are only constructed once at boot, so the reboot is required
either way. **If a new param ever silently doesn't take effect from a
`.parm` file despite the file being correct, suspect this before anything
else.**

**Gotcha: flight test scripts must gate on measured state, not wall-clock
sleep, given this machine's low RTF** (see the RTF diagnostic entry in
Known Issues — RTF ≈ 0.05–0.17). A first verification attempt used
`time.sleep(25)`-style wall-clock delays for climb/cruise phases; at
RTF≈0.1 that bought only ~2.5 s of *sim* time, producing a near-empty
7–12 s flight (dataflash log confirmed `HAGL` never left ~0.1 m). Fixed by
polling `LOCAL_POSITION_NED` and gating each phase on the actual measured
altitude/distance reached, with a generous wall-clock timeout as a safety
cap rather than the primary control. Apply this to any future scripted
flight test on this machine.

**Verification** (state-gated flight: climb to ~2 m, fly pure-forward at
0.4 m/s for ~3 m, stop, land; `ardupilot.bin` parsed via pymavlink's
`DFReader` for the `XKF5` dataflash message — `FIX`/`FIY` are the flow
innovations ×1000, `NI` is the normalised innovation test ratio, ≥100 means
rejected by the gate, confirmed by reading `AP_NavEKF3_Logging.cpp`):
- **Fusion is active, not rejected**: 251/251 airborne (`HAGL`>1.0 m) `XKF5`
  rows show live, nonzero `FIX`/`FIY`; **0/251 rejected** (`NI` stayed
  below 100 throughout, peak 82, mean 15).
- **The fused state is quantitatively correct** — the cleanest possible
  confirmation, cross-checked via `XKF1`'s `VN`/`VE`/`PN` (EKF velocity/
  position state, from the *same* `ardupilot.bin`, since `EK3_SRC1_VELXY=5`
  means this velocity comes from flow alone — GPS does not contribute
  velocity in this config): during the known pure-forward segment, `VN`
  (North velocity, ≈ body-forward since yaw stayed ≈0°) rises smoothly to a
  stable **0.395–0.40 m/s** — matching the commanded 0.4 m/s almost
  exactly — while `VE` (East/lateral) stayed near zero throughout. `PN`
  correspondingly tracked 0 → +3.14 m, matching the known ~3 m forward
  distance. This confirms the axis/sign mapping above is correct as
  derived, not just plausible.
- Raw per-sample `XKF5` innovations are noisier than the converged state
  estimate (large swings on one axis, small on the other, not simply
  attributable to "wrong axis" — the Kalman-filtered `VN`/`VE` state above
  is the trustworthy signal, not the raw innovation magnitude alone).

State extraction / `evo` comparison against ground truth — done, see
"EKF State Estimate — Stage B" below.

(`record_trial.sh` not sourcing the workspace overlay, and so silently
dropping `/optical_flow/measurement` from bags, was found during this
work — since fixed, see Known Issues.)

### EKF State Estimate — Stage B (evo evaluation)

> ## ⚠️ THE ATE/RPE NUMBERS BELOW ARE NOT EKF3 ACCURACY
>
> **Do not quote Stage B's 6.4 mm ATE, or Stage C's 7.7 mm / 10.0 mm ATEs, as a
> measurement of EKF3.** They are pipeline validation only.
>
> `AHRS_EKF_TYPE=10` ("Sim") means `/ekf/pose` carries **simulator ground
> truth**, not the EKF3 estimate — so every `evo_ape`/`evo_rpe` result computed
> from it compared ground truth against ground truth. See "Hidden Configuration
> Audit — Machine Migration (2026-07-22)" below for the source trace and the
> measured evidence. These numbers remain valid as confirmation that the
> recording, frame transform, bag extraction and `evo` tooling all work
> end-to-end — which is all this section ever actually established.

`ekf_bridge.py` reads ArduPilot's EKF3 state estimate via MAVLink
(`LOCAL_POSITION_NED` + `ATTITUDE_QUATERNION`, port **14554** — dedicated,
separate from `fly_forward.py` (14550), `attitude_bridge.py` (14551),
`lidar_bridge.py` (14552) and `flow_bridge.py` (14553)) and republishes as
`/ekf/pose` (`geometry_msgs/PoseStamped`), transformed into the same
ENU/FLU frame as `/ground_truth/pose` so the two are directly comparable.
Recorded by default in `record_trial.sh` trials.

**Frame transform** (ArduPilot NED/FRD → Gazebo/ROS ENU/FLU), reported and
verified before finalising, per your instruction:

- **Position** (NED → ENU) — purely definitional axis relabelling, no
  ambiguity: `enu.x = ned.y` (East), `enu.y = ned.x` (North),
  `enu.z = -ned.z` (Up = −Down).
- **Orientation** — composed from two fixed quaternions (Hamilton product,
  `q_enu_flu = q_ned2enu ⊗ q_attitude ⊗ q_frd2flu`):
  - `q_ned2enu = (w=0, x=√2/2, y=√2/2, z=0)` — 180° about the NED axis
    (1,1,0)/√2. Verified by explicit rotation-matrix conversion (all 9
    matrix entries checked by hand), not assumed.
  - `q_frd2flu = (w=0, x=1, y=0, z=0)` — 180° about body X (forward).
    **Exactly matches** `flow_tracker.py`'s own already-empirically-validated
    FRD↔FLU relationship (`(wx, -wy, -wz)` for angular rates, confirmed
    against the `imu_link`'s 180° roll SDF pose) — same transform, applied
    to a static orientation instead of a rate.
  - This matches the standard ArduPilot/PX4↔ROS frame-conversion structure
    (same form as mavros's `NED_ENU_Q` / `AIRCRAFT_BASELINK_Q`
    composition), derived and verified independently rather than trusted
    from that recollection.

**`evo` reads ROS2 bags directly** (`evo_ape`/`evo_rpe`/`evo_traj bag2 <bag>
<ref_topic> <est_topic>`, via the pure-Python `rosbags` library — no ROS
install needed for this step) rather than requiring a manual TUM-file
conversion. Since `/ground_truth/pose` and `/ekf/pose` are both plain
`geometry_msgs/PoseStamped`, this is used directly instead of the manual
TUM conversion — same ATE/RPE output, one less place for a conversion bug
to hide. `evo` lives in its own venv (`~/venv-evo`), independent of the ROS
Python environment (evaluation doesn't need ROS bindings at all).
`evaluate_trial.sh <trial_name>` wraps `evo_ape`, `evo_rpe`, and `evo_traj`
into one command, writing to `~/thesis_data/trials/<trial_name>/evo/`.
Needs `--no_warnings` — `evo` otherwise prompts interactively to confirm
overwriting existing plot files, which hangs a non-interactive script.

**Verification** (`stage_b_verify` trial: state-gated climb to ~2 m, pure
forward flight at 0.4 m/s for ~3 m, stop, land — same RTF-aware
methodology as Stage A, see Known Issues):
- **ATE** (`evo_ape`, SE(3)-aligned): RMSE **6.4 mm**, mean 5.4 mm, max
  18.4 mm.
- **RPE** (`evo_rpe`, consecutive-pair): RMSE **4.6 mm**, mean 2.4 mm.
- Sub-centimetre accuracy is expected and **not yet a meaningful test of
  flow's contribution alone** — `EK3_SRC1_POSXY` is still GPS (unchanged
  since Stage A), and SITL's simulated GPS is near-noise-free by default.
  This result mainly validates the pipeline end-to-end (frame transform,
  bag extraction, `evo` tooling) rather than flow-only positioning
  accuracy — that requires the GNSS-denied config Stage A explicitly
  deferred.
- `evo_traj`'s per-axis time-series plot shows `/ekf/pose` tracking
  `/ground_truth/pose` closely on all of x/y/z, confirming the position
  transform. Yaw reads **~90°**, not 0°, for *both* curves at rest —
  this is not a bug: ENU's "yaw measured from East/X-axis" convention
  means ArduPilot's yaw=0 (facing NED-North = ENU +Y) is correctly ~90°
  in this representation. Both curves agreeing on this (offset <0.1°,
  same noise pattern throughout the flight) is itself confirmation the
  orientation transform is correct — a transform bug would show the two
  diverging, not agreeing on an unexpected number.
- At rest, `/ekf/pose` z ≈ 0.190 m vs `/ground_truth/pose` z = 0.195 m —
  consistent with Stage 1/2's already-established ground-rest geometry.

### GNSS-Denied Configuration — Stage C

**This is the config the thesis actually studies**, and the standing
baseline for UKF and FGO to also use for a fair comparison — Stage B's
sub-cm ATE reflected GPS (`EK3_SRC1_POSXY` was still GPS), not flow.
`gnss_denied.parm` (loaded by default in `start_sim.sh`/CLAUDE.md's
`--add-param-file` chain, after `flow_ekf.parm`) removes GPS entirely:

```
EK3_SRC1_POSXY 0   # None — see below, there is no "OpticalFlow" POSXY value
EK3_SRC1_POSZ 2    # RangeFinder — height from the downward LiDAR, not Baro (the default) or GPS
EK3_SRC1_VELZ 0    # None — VELZ defaults to GPS(3); this closes that gap so GPS can't contribute vertical velocity either
SIM_GPS1_ENABLE 0  # physically disables the simulated GPS sensor, belt-and-braces beyond the EK3_SRC selections above
```

**There is no "OpticalFlow" value for `EK3_SRC1_POSXY`** (`@Values: 0:None,
3:GPS, 4:Beacon, 6:ExternalNav` in `AP_NavEKF_Source.cpp` — only VELXY has
`5:OpticalFlow`). Flow-based position isn't a direct POSXY source at all —
it's **dead reckoning**. Confirmed by reading `NavEKF3_core::readyToUseGPS()`
in `AP_NavEKF3_Control.cpp` directly: it returns `false` immediately once
`EK3_SRC1_POSXY != GPS`, *regardless of actual GPS signal health* — this
alone is enough to make `PV_AidingMode` fall through to `AID_RELATIVE`
(flow dead-reckoning) once `readyToUseOptFlow()` is satisfied (already
working since Stage A). `EK3_SRC1_VELZ` defaulting to GPS(3) was a gap
that would have been easy to miss — confirmed by reading the same file.

**Arming still works with GPS fully disabled** — tested directly (armed
cleanly, "Arming motors", no GPS-related arming-check failure) before
committing to the full flight tests.

**Same `eeprom.bin` persistence gotcha as Stage A recurred** — `EK3_SRC1_POSXY`
read back as `3` (GPS) instead of the `0` in `gnss_denied.parm` on first
boot with this file, exactly like Stage A's `FLOW_TYPE`. `EK3_SRC1_POSZ`,
`EK3_SRC1_VELZ` and `SIM_GPS1_ENABLE` all applied correctly from the same
file — only the param whose *value happened to already match what was in
storage from an earlier boot* got stuck. Same fix: live `PARAM_SET
EK3_SRC1_POSXY=0` + `MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN`. **If a value from
a `.parm` file doesn't take, check this before assuming the file is wrong.**

**Verification** (`stage_c_textured` and `stage_c_blank` trials, same
state-gated flight profile as Stage A/B — climb to ~2 m, forward 3 m at
0.4 m/s, stop, land — flown once over `iris_textured.sdf`, once over
`iris_runway.sdf`, the blank/degraded world):

- **Genuinely GPS-free, confirmed from the flight's own log, not just
  param readback**: decoded the `nav_filter_status` bitfield (`XKF4.SS` in
  the dataflash log; bit layout from `AP_Nav_Common.h`) for every sample
  of the textured-floor flight — `using_gps` was `False` for all 1024
  samples (100%), `horiz_pos_abs` (an absolute fix) `False` throughout,
  `horiz_pos_rel` (relative/flow-aided position) `True` for 71% of
  samples once airborne (the rest is the pre-takeoff/ground period, before
  `readyToUseOptFlow()`'s preconditions are met).
- **Both flights landed safely, no crash, no divergence** — final ground
  truth altitude matched the known rest height (0.195 m) in both cases,
  and `XKF5`'s innovation gate (`NI`) never once hit the ≥100 rejection
  threshold in either flight (textured: mean 15, peak 82, 0/251 rejected;
  blank: mean 1.3, peak 18, 0/244 rejected).
- **ATE (evo_ape, SE(3)-aligned)**: **textured RMSE 7.7 mm** (mean 6.3 mm,
  max 28.0 mm) vs **blank RMSE 10.0 mm** (mean 8.7 mm, max 30.7 mm) — worse
  on blank, but only ~30%, not the dramatic collapse a first guess might
  expect.
  **⚠️ VOID as an EKF3 measurement** — computed from `/ekf/pose`, which is
  simulator ground truth under `AHRS_EKF_TYPE=10`, not the EKF3 estimate.
  This is ground truth vs ground truth. See the Hidden Configuration Audit
  section. **The "modest ~30% gap" puzzle below is fully explained by this**:
  the metric could not respond to sensor degradation because it never
  contained an estimator.
- **RPE**: textured RMSE 5.4 mm vs blank RMSE 6.5 mm — same modest-not-dramatic pattern.
  **⚠️ VOID as an EKF3 measurement, same reason as the ATE above.**
- **The sensor-level story is much starker than the ATE numbers alone
  suggest — this is the real thesis signal.** Extracted `inlier_ratio` and
  `feature_count` directly from `/optical_flow/measurement` in each bag:
  textured floor `inlier_ratio` mean **0.94** (median 1.0, only 4% of
  samples below 0.5); blank floor mean **0.47** (median 0.28, **62%** of
  samples below 0.5), `feature_count` mean dropping from 85 to 54 (min 0 —
  some frames find *zero* trackable points). Flow quality collapses on the
  blank floor exactly as expected; the downstream position estimate is
  comparatively resilient over this short (~40 s) flight.
- **Read this nuance carefully before quoting a number**: the modest ATE
  gap does **not** mean texture doesn't matter — the `inlier_ratio`
  collapse is unambiguous evidence it does, at the sensor level. The EKF's
  own innovation gating and short flight duration appear to be limiting
  how much that sensor-level degradation has propagated into position
  error *yet*. A longer flight, or one with more aggressive dynamics,
  would very likely show substantially more accumulated drift on the blank
  floor as the (still-noisier, still-degraded) flow measurements integrate
  error over more time — this hasn't been tested and is a natural
  next experiment, not assumed.
- One flight-to-flight difference worth noting honestly, not over-reading:
  the blank-floor flight's climb showed a real altitude overshoot (to
  ~3.2 m before settling at ~2.05 m) and a brief 1.3 m/s ground-truth speed
  spike, both absent from the textured-floor climb. Altitude comes from
  the rangefinder (`EK3_SRC1_POSZ=2`), independent of floor texture, so
  this reads as ordinary flight-to-flight controller/physics variance, not
  a flow-driven effect — flagged for transparency, not concluded from.

## EKF3 Prediction dt — 80 Hz, not 400 Hz (2026-07-23)

**EKF3 accumulates IMU frames to a target period and predicts on the total.
`SCHED_LOOP_RATE` sets the IMU *frame* rate, not the prediction rate.**
Traced at pinned commit `7bac20cbcc`:

| Step | Location | Fact |
|---|---|---|
| Target period | `AP_NavEKF3_core.h:58-59` | `EKF_TARGET_DT 0.012f`, `EKF_TARGET_DT_MS 12` |
| Init | `AP_NavEKF3_core.cpp:35-36` | `dtEkfAvg = MAX(1/loop_rate, EKF_TARGET_DT)` → at 400 Hz, `MAX(0.0025, 0.012)` = **0.012** |
| Accumulate | `AP_NavEKF3_Measurements.cpp:453-454,475` | frames summed into `imuDataDownSampledNew.delAngDT/delVelDT` |
| Trigger | `AP_NavEKF3_Measurements.cpp:483-484` | fires at `delAngDT >= EKF_TARGET_DT - dtIMUavg*0.5` = 0.01075 s → 5 frames = **0.0125 s** |
| Frame count | `AP_NavEKF3.cpp:778` | `_framesPerPrediction = round(0.012/0.0025)` = **5** (independent confirmation) |
| dt used | `AP_NavEKF3_core.cpp:1036` | `dt = constrain(0.5*(delAngDT+delVelDT), 0.5*dtEkfAvg, 2*dtEkfAvg)` — the accumulated period |
| Q consumption | `AP_NavEKF3_core.cpp:1049,1056` | `sq(sq(dt) * _gyroBiasProcessNoise)` — confirms the `dt²` (k=2) bias form |

**Actual prediction dt = 0.0125 s (80 Hz).** Verified live: `SCHED_LOOP_RATE=400`,
`INS_FAST_SAMPLE=1`, and all four `_NSE` params at defaults.

**Caveat:** 0.0125 s is *derived* (400 Hz frames × 5), not measured — EKF3 does
not log its `dt`. `dtEkfAvg` is a low-pass average
(`AP_NavEKF3_Measurements.cpp:497`) with constrain bounds `[0.5×, 2×]`, so
jitter stays well inside. Treat as solid, but state the derivation rather than
claiming a measurement.

**Consequence (CORRECTED 2026-09-29, see METHODOLOGY "Distance-scale check"):** the UKF was intended to predict at this same 0.0125 s,
accumulating by elapsed time as EKF3 does; **in practice each step spans 15.00 ms (five 3.0 ms IMU samples) but position and gravity were integrated with the fixed 0.0125 s**, a ~15% position under-scale. It is queued as a baseline correction. Originally: so **EKF3's `*_NSE` values transfer
unchanged** (scale factor exactly 1). This is a stronger position than any
correct rescaling — there is nothing to defend.

**This also exposes that ArduPilot's `_P_NSE` values are not true continuous
noise densities** — they are rate-dependent, sitting inside discrete
`(dt·NSE)²` expressions. That is precisely why the 400 Hz assumption bit, and
why the GTSAM conversion below cannot be a copy-paste.

## IMU Bridge — rate, aliasing, and the MAVProxy bypass (2026-07-23)

### Rate raised 50 Hz → 333 Hz

**333 Hz is the ceiling ArduPilot permits, not a preference.**
`GCS_Common.cpp:268-277`'s `cap_message_interval()` enforces "no greater than
0.8 × SCHED_LOOP_RATE"; at 400 Hz the floor is `2500/800 = 3.125 ms`, and
`set_message_interval()` (`GCS_Common.cpp:3225`) truncates µs to integer ms, so
a 2 ms request is rejected outright. **Measured realised rate: 333.27 Hz**
(29665 msgs / 89.012 s; median dt 3.000 ms) — it hits the ceiling exactly.

**Raising `SCHED_LOOP_RATE` to lift the ceiling is NOT an option** — it changes
EKF3's own frame rate and INS sampling, i.e. the baseline being compared
against.

### Why: 50 Hz was aliasing, confirmed by direct observation

At 333 Hz the cruise spectrum resolves what 50 Hz could not:

| Axis | true peak | band holding the energy |
|---|---|---|
| `acc_y` | **17.41 Hz** | 99.3% in 5–25 Hz |
| `acc_z` | **34.99 Hz** | **90.9% in 25–50 Hz** |

**`acc_z`'s real tone is 35 Hz.** At 50 Hz sampling it folded to
`50 − 34.99 = 15.01 Hz`, which is exactly the "14.84 Hz peak" the 50 Hz
analysis reported as real. **That peak was the artefact.** 34.99 ≈ 2 × 17.41,
so `acc_z` carries the second harmonic of `acc_y`'s fundamental — consistent
with rotor/blade-pass content from the Gazebo model's own dynamics (ArduPilot
synthesises none: `SIM_ACC*_RND = 0`, `SIM_VIB_* = 0`).

**Aliased energy in the stream we actually receive:**

| | RMS folding in | share of `acc_z` power |
|---|---|---|
| at 50 Hz (25–50 Hz content) | **0.154 m/s²** | 90.9% |
| at 333 Hz (>166.6 Hz content) | **0.018 m/s²** | 1.2% |

**An 8.7× reduction in aliased energy.** Residual is small but non-zero — a
documented limitation, not an eliminated one.

### Correction: `VIBE` measures a different signal

The earlier "0.25 m/s² RMS above Nyquist" figure, inferred by comparing `VIBE`
against the observable band, **conflated filtering with aliasing.**
`AP_InertialSensor_Backend.cpp:592` passes the **pre-filter** accel to
`calc_vibration_and_clipping`, while line 611 applies `_accel_filter`
afterwards into `_accel_filtered` — which is what `get_accel()` and therefore
`HIGHRES_IMU` return. **`VIBE` measures the raw 1000 Hz signal; the bridge
receives a 20 Hz-low-passed one** (`INS_ACCEL_FILTER = INS_GYRO_FILTER = 20`).
The large VIBE-vs-observable gap is that filter, not aliasing. The conclusion
(raise the rate) was right; the magnitude was measured wrongly and is
superseded by the direct 25–50 Hz figure above.

The 20 Hz INS filter is only 2-pole, so 35 Hz passes at roughly −10 dB —
attenuated but far from removed, which is why it still dominated `acc_z` and
still aliased at 50 Hz.

### Verification at the new rate (trial `imu_rate_verify`)

| Check | Result |
|---|---|
| Achieved rate | **333.27 Hz** (29665 / 89.012 s) |
| `‖a‖` at rest | 9.81085 m/s² (std 0.00061) |
| `a_z` sign | **+9.81085** — positive, correct FLU specific force |
| Structure through velocity change | ground std 0.0006 → climb 0.463 → cruise 0.162 |
| Stamp range vs `/attitude/angular_rates` | end delta **30 ms**; **start delta 2348 ms** — see below |

**Regression to be aware of:** `/imu/data_raw` now starts ~2.35 s *later* than
the other streams (previously all four agreed within ~20 ms). Cause: SITL's
`udpclient` only begins streaming after our `SET_MESSAGE_INTERVAL` lands — the
bridge log shows heartbeat at +0.04 s but first `HIGHRES_IMU` at +1.75 s. There
is **no systematic timestamp offset** (the streams end together, 30 ms apart);
it is purely a later start, absorbed by `run_trial.sh`'s readiness wait and
well before arming. Harmless for trials, but do not assume all four topics
share a start instant.

### MAVProxy bypass — a deliberate architectural divergence

`imu_bridge.py` runs on **port 14556, fed by a dedicated SITL serial output**
(`arducopter --serial2=udpclient:127.0.0.1:14556`), **not** a MAVProxy `--out`
port. `run_trial.sh` no longer passes `--out 127.0.0.1:14555`.

**This departs from the architecture brief's "every bridge owns a MAVLink UDP
port via MAVProxy `--out`" pattern**, which `fly_forward.py` (14550),
`attitude_bridge.py` (14551), `lidar_bridge.py` (14552), `flow_bridge.py`
(14553) and `ekf_bridge.py` (14554) all still follow. Recorded here so the
divergence is not rediscovered as a bug.

**Rationale — headroom, not a demonstrated failure.** At 333 Hz MAVProxy would
relay ~2000 msg/s of *sim-time* traffic to six outputs in single-threaded
Python. **That figure is sim-time; at RTF ≈ 0.39 it is ~780 msg/s wall-clock,
which MAVProxy may well have coped with.** The bypass was taken for margin and
because it removes MAVProxy's documented stream-rate clobbering from this path
entirely. It was not forced by a measured failure.

## GTSAM IMU Preintegration — noise conversion (2026-07-23)

**Derived, not deferred, because the fairness principle requires the FGO's
process noise to be *equivalent* to EKF3's, not merely reasonable.**

**GTSAM's convention, verified from library source** (not assumed):
- `PreintegrationParams.h:27-29` — `accelerometerCovariance`, with the explicit
  comment *"Continuous-time 'Covariance' of accelerometer. The units for stddev
  are σ = m/s²/√Hz"*.
- `PreintegrationCombinedParams.h:38-41` — `biasAccCovariance` /
  `biasOmegaCovariance`, *"continuous-time 'Covariance' describing … bias
  random walk"*.
- `CombinedImuFactor.cpp:136-155` — the discrete propagation:
  `D_v_v = vel_H_acc·(aCov/dt)·vel_H_accᵀ`, `D_R_R = theta_H_omega·(wCov/dt)·…`,
  `D_a_a = dt·biasAccCovariance`, `D_g_g = dt·biasOmegaCovariance`. Since
  `vel_H_acc` carries a `dt`, the velocity contribution is `dt·aCov`.

**Derivation.** Per prediction step:
- GTSAM adds `dt·σ_c²` (all four terms, from the propagation above).
- EKF3 adds `(dt·NSE)² = dt²·NSE²` to velocity/attitude
  (`AP_NavEKF3_core.cpp`, auto-generated covariance prediction).
- Equating: `dt·σ_c² = dt²·NSE²` → **`σ_c = NSE·√dt`**.

**The bias terms need one extra step, and it does *not* follow the k=2 form.**
EKF3's bias states are in **delta** units (rad, m/s — `state_elements`), adding
`(dt²·NSE)² = dt⁴·NSE²` per step. GTSAM's bias states are **rates** (rad/s,
m/s²), related by `b_delta = b_rate·dt`, so `Var(b_delta) = dt²·Var(b_rate)`.
Converting: EKF3 adds `dt⁴·NSE²/dt² = dt²·NSE²` to the *rate*-bias variance.
Equating with GTSAM's `dt·σ_c²` gives **`σ_c = NSE·√dt` again**. All four
collapse to the same form once the delta-vs-rate unit difference is handled —
the k=2 exponent applies to *rate changes within EKF3's own delta-form
parameterisation*, not to this conversion.

**Values at dt = 0.0125 s** (`√dt = 0.1118034`), i.e. `covariance = NSE²·dt`:

| GTSAM parameter | from | σ (continuous) | units | covariance |
|---|---|---|---|---|
| `accelerometerCovariance` | `ACC_P_NSE` 0.35 | 0.03913119 | m/s²/√Hz | 1.53125×10⁻³ |
| `gyroscopeCovariance` | `GYRO_P_NSE` 0.015 | 0.001677051 | rad/s/√Hz | 2.8125×10⁻⁶ |
| `biasAccCovariance` | `ABIAS_P_NSE` 0.02 | 0.002236068 | m/s²/√s | 5.0×10⁻⁶ |
| `biasOmegaCovariance` | `GBIAS_P_NSE` 0.001 | 0.0001118034 | rad/s/√s | 1.25×10⁻⁸ |

Units check: `ACC_P_NSE` [m/s²]·√s = m/s²/√Hz ✓; `GBIAS_P_NSE` [rad/s²]·√s =
rad/s/√s ✓ — the standard bias-random-walk unit.

**Notes:**
- `integrationCovariance` has **no EKF3 counterpart** (GTSAM-specific position
  integration uncertainty). Set small (~1e-8·I) and document the asymmetry
  rather than pretending it is matched.
- `biasAccOmegaInt` is **deprecated** in current GTSAM
  (`PreintegrationCombinedParams.h:92`: *"no longer used. Use a prior on first
  bias instead"*).
- Gravity: `imu_bridge.py` publishes FLU with **+9.81 at rest**, so
  `PreintegrationCombinedParams::MakeSharedU(9.81)` (Z-up) is the matching
  constructor.
- **Feed every 333 Hz sample to `integrateMeasurement()`; never decimate to
  keyframe rate.** At ~10 Hz keyframes that is ~33 samples per factor. At the
  old 50 Hz it would have been 5 — marginal, and it would have made the FGO
  look worse for reasons unrelated to the estimator.

**Standing caveat for all three estimators:** `HIGHRES_IMU` carries
*instantaneous* samples, whereas EKF3 receives true delta-angles/delta-velocities
integrated by the INS driver at 1000 Hz. Summing `a·dt` over bridged samples is
**rectangular integration** and does not anti-alias. Good at 333 Hz, far better
than 50 Hz, but state it in the methodology as an approximation rather than an
exact match. No standard MAVLink message carries ArduPilot's true delta
quantities, so this is an interface limitation, not a choice.

## Hidden Configuration Audit — Machine Migration (2026-07-22)

Migrating from the ThinkPad X1 Carbon (i5-10210U, 15 W mobile) to a desktop
(i7-8700, 65 W, + Quadro P620 discrete GPU) surfaced **three separate
configuration values that the working setup depended on but that existed in
no committed file**. All three lived only in `~/ardupilot/ArduCopter/eeprom.bin`,
which is gitignored and machine-local. This is Known Issue #10's persistence
gotcha operating in reverse: instead of *blocking* a param you set, the eeprom
was silently *supplying* one you never recorded.

**Three such discoveries in two days is a pattern, not bad luck.** The
mitigations are `preflight_check.sh` (see below) and the standing rule that
any live `PARAM_SET` must be written into a `.parm` file in the same session.

### 1. `AHRS_EKF_TYPE=10` — `/ekf/pose` is ground truth, not EKF3

> **Correction (2026-09-29, verified in source):** the value is also **injected as a
> default by SITL itself**. `SIM_JSON.cpp:410-413` calls
> `set_default_by_name("AHRS_EKF_TYPE", 10)` whenever the model sends `no_time_sync`,
> and our iris model does (`iris_with_ardupilot/model.sdf:789`: `<no_time_sync>1</no_time_sync>`).
> ArduPilot warns that without time sync the "EKF is likely to diverge".
> **Before any closed-loop flight:** set `AHRS_EKF_TYPE` explicitly in a `.parm` file,
> confirm it from the log's PARM dump, and settle the time-sync question. See
> METHODOLOGY "Part C" and `docs/partC_onboard_feasibility.md`.

**This is the most consequential finding in this document.** `AHRS_EKF_TYPE`
selects which estimator ArduPilot *reports* as the vehicle's position. `10` is
`EKFType::SIM` — the simulator's own perfect state. EKF3 is `3`.

Source path, traced at pinned commit `7bac20cbcc`:

```
ekf_bridge.py                  reads MAVLink LOCAL_POSITION_NED
GCS_Common.cpp:3042            send_local_position()
  -> AP_AHRS.cpp:1826          get_relative_position_NED_origin_float()
  -> AP_AHRS.cpp:1777          get_relative_position_NED_origin()
  -> switch (active_EKF_type())
  -> case EKFType::SIM:        return sim.get_relative_position_NED_origin(vec)
```

`case EKFType::THREE` (which reads `EKF3.getPosNE()`/`getPosD()`) sits directly
above and **is never taken**. So `/ekf/pose` republishes simulator truth.

**Measured evidence** (`smoke_test`, 2026-07-22, `iris_textured`, 0.4 m/s
forward, compass active — `run_trial.sh`'s chain ends at `gnss_denied.parm`,
so `EK3_SRC1_YAW` was at its default of 1/Compass):

| Source | East | North |
|---|---|---|
| `/ground_truth/pose` | −0.010 … 0.004 m | 0 … **4.784 m** |
| `/ekf/pose` | −0.009 … 0.000 m | 0 … **4.787 m** |
| `XKF1` (EKF3's own logged state) | −0.274 … **1.025 m** | −0.118 … 0.023 m |

`/ekf/pose` tracks ground truth to **3 mm over a 4.78 m flight**. EKF3's own
solution is unrelated to both — see "EKF3 Solution Diagnosis" below.

**Unaffected by this finding** (all sourced from EKF3's own logging or from the
sensor topics, never from `/ekf/pose`): `XKF5` innovation analysis, `XKF4.SS`
`nav_filter_status` decoding (`using_gps=False`), and every `inlier_ratio` /
`feature_count` result.

**Decision (2026-07-22): keep `AHRS_EKF_TYPE=10`; evaluate EKF3 offline from
`XKF1`.** Not merely because EKF3's current solution is too poor to fly on, but
for a stronger methodological reason: with EKF3 in the loop, *the estimator
under test determines the trajectory it is tested on*. The controller flies to
make the estimate hit the setpoint, so EKF3 physically wanders by its own error
— different flow content, different ground truth, and over a 160 m corridor
possibly into a wall. The UKF and FGO are passive and perturb nothing. That
asymmetry would sit directly on top of the degradation variable. Flying on
simulator truth gives one fixed trajectory across all conditions with floor
texture as the only variable — the controlled comparison the sensor-fairness
argument has been building toward.

Two costs, documented rather than discovered later:
- **No closed-loop stability claim is possible** from this data. State this in
  the methodology chapter. Term 3's real flights are necessarily in-loop, which
  makes that a natural extension rather than a gap.
- **Sourcing EKF3 from dataflash reintroduces clock alignment.** `XKF1`'s
  `TimeUS` is microseconds since boot; the bags are sim-time. This must be
  *proven* on an existing bag — cross-correlate `XKF1` height against
  `/ground_truth/pose` z, report the residual, and overlay the aligned
  trajectory — before `evaluate_trial.sh` is rewired. Do not assume a constant
  offset holds.
  **CLOSED 2026-09-24 as "bounded, not proven".** No formal alignment proof was
  done. Instead, a sensitivity check shifts the pinned cruise window by ±0.25 s and
  ±0.5 s on all nine `dsn_*` bags. The largest change in EKF3's evo -a (cruise) is
  0.103 m (transition) and at most 0.015 m on textured, far below the
  between-estimator gaps. See METHODOLOGY "Cruise window — pinned definition and clock
  sensitivity".
  **Update, same day: the clocks also differ in RATE.** SITL's `TimeUS` runs about
  0.02% slow against Gazebo sim time, so the offset drifts from about −7 ms to about
  −60 ms over a flight. That is still well inside the ±0.5 s bound, so the item stays
  "bounded, not proven". Any TimeUS-vs-bag comparison must use `eval/input_timing.py`
  `clock_map()` (offset and rate). See METHODOLOGY "FINDING — the SITL dataflash clock
  runs ~0.02% slow".

### 2. `GPS1_TYPE` — arming failure on a clean machine

`SIM_GPS1_ENABLE=0` disables the *simulated GPS sensor*. `GPS1_TYPE` is a
separate question: whether a GPS is **fitted at all**. With `GPS1_TYPE` at its
SITL default, arming fails with `Arm: GPS 1: Bad fix`.

`AP_Arming::gps_checks()` runs whenever the GPS bit (`1<<3`, i.e. 8) is set in
`ARMING_CHECK`, **independently of the `EK3_SRC` selections**, and rejects any
configured instance below `FIX_3D`. With `GPS1_TYPE=0` the check takes its
`continue` branch and skips the instance entirely (`AP_Arming.cpp`, ~line 714).

`ARMING_CHECK` was **not** modified on the old machine — it does not appear in
`stage_c_textured`'s PARM dump at all. The GPS check was never disabled;
ArduPilot was simply told no GPS is fitted. Now pinned in `gnss_denied.parm`
and added to `fly_trial.py`'s `EXPECTED_PARAMS` (it carries
`AP_PARAM_FLAG_ENABLE`, so it is squarely subject to the eeprom gotcha).

### 3. Compass configuration — why it looks like a bug and is not

`gnss_denied_nomag.parm` sets `COMPASS_ENABLE=1` alongside `COMPASS_USE*=0` and
`EK3_SRC1_YAW=0`. **This is deliberate; do not "fix" it to `COMPASS_ENABLE=0`.**
`AP_Arming_Copter::arm_checks()` (`AP_Arming_Copter.cpp:575`, `#ifndef
ALLOW_ARM_NO_COMPASS`, not defined for this SITL build) has its own
compass-health gate, separate from the generic `AP_Arming::compass_checks()`.
It is unconditional — not gated behind `ARMING_CHECK`, and it runs before
`should_skip_all_checks()` — so no bitmask can bypass it. It only skips when
`ahrs.using_noncompass_for_yaw()` is true, which requires a recent (<5 s)
non-compass yaw fusion event that cannot occur in this no-GPS config. The
compass driver must therefore exist and report healthy. EKF3 still receives
zero yaw information: `EK3_SRC1_YAW=0` means `setYawSource()` never selects
COMPASS, and `COMPASS_USE*=0` keeps it out of `AP_Compass::use_for_yaw()`.
The full reasoning is inline in `gnss_denied_nomag.parm`.

### 4. Full live parameter diff

`param_audit_migration_2026-07-22.txt` records a complete old-vs-new comparison,
dumped from each flight's dataflash `PARM` stream (the *live* values, not what
the `.parm` files claim). **1379 parameters on each side, none present on one
machine and absent on the other, 16 value differences.** Fifteen are
calibration state (`INS_GYR*OFFS_*`, `INS_GYR*_CALTEMP`), learned values
(`MOT_THST_HOVER`), environmental (`BARO2_GND_PRESS`) or cumulative counters
(`STAT_*`).

The sixteenth, **`SIM_FLOW_ENABLE` (old=1, new=0)**, is proven **inert**:
`AP_OpticalFlow::init()` instantiates exactly one backend via `switch(FLOW_TYPE)`,
and `FLOW_TYPE=5` selects `AP_OpticalFlow_MAV` only — `AP_OpticalFlow_SITL` is
never constructed, so SITL's simulated flow has no consumer. It is a leftover
from when `FLOW_TYPE` was stuck at 10 (see the Stage A eeprom gotcha).

**Conclusion: the old configuration is fully enumerable. Nothing is
unrecoverable.**

### EKF3 Solution Diagnosis (2026-07-22) — not misconfigured

Once `/ekf/pose` was known to be ground truth, EKF3's *actual* solution was
read from `XKF1` for the first time. The initial reading looked alarming — 1.0 m
East against 4.78 m North actual — but that figure is **invalid** and must not
be quoted. It came from a 10 s cruise that never escaped EKF3's startup
transient.

**Measured properly (`ekf3_diag_60s`, `iris_textured`, 0.4 m/s, compass active),
over the window where flow aiding was actually engaged:**

| t (s) | GT north travelled | EKF3 `PN` | Error |
|---|---|---|---|
| 41.85 (aiding engages) | 0 (ref) | 0.000 | — |
| 46.05 | 1.682 m | 1.755 m | +0.073 m |
| 51.55 | 3.880 m | 4.085 m | +0.205 m |
| 57.05 | 6.085 m | 6.392 m | **+0.307 m (≈5%)** |

**That is honest flow dead reckoning** — a smooth ~5% scale over-estimate, no
divergence, no axis error. Yaw stayed within 0.65° of North throughout
(`XKF1.Yaw` 359.99°→0.65°; GT yaw 90.0° in ENU, the documented ENU/NED
correspondence). Flow was never gated out: **0/183 rejections**, mean `NI` 1.97
against the 100 threshold.

**Two artefacts bound the usable measurement window, and both are properties of
the test world rather than of EKF3:**

1. **Startup transient.** `const_pos_mode` held position at *exactly* 0.000
   until t=41.85 s — ~16 s after takeoff — because `readyToUseOptFlow()`
   requires `delAngBiasLearned` (gyro-bias convergence). `horiz_vel` was true
   the whole time, so velocity was estimated correctly (`VN` ≈ 0.41 m/s against
   0.40 commanded) while position was pinned by design. **Any cruise shorter
   than ~20 s of sim time measures nothing.** Stage C's ~40 s flights cleared
   it (71% `horiz_pos_rel`); the 10 s smoke test did not (39.9%).
2. **Rangefinder loss at the mat edge** — see Known Issue #6 above. Aiding
   dropped at t=56.55 s and never returned.

**Consequence: EKF3 cannot be characterised on `iris_textured.sdf` at all.**
The usable window is bounded below by the ~16 s aiding transient and above by
the 10 m mat edge, leaving ~6 m of valid travel. A real characterisation needs
the corridor world (Known Issue #11's fix), which is also why the §2 no-yaw
yaw-drift re-measurement must be flown there rather than on `iris_textured`.

**No tuning was performed** to produce these numbers.

### Environment differences (documented, not defects)

| | Old (ThinkPad X1 Carbon 7th) | New (desktop) |
|---|---|---|
| CPU | i5-10210U, 15 W mobile, 4C/8T | i7-8700, 65 W desktop, 6C/12T |
| GPU | Intel integrated (shared 15 W budget) | **NVIDIA Quadro P620**, driver 535 |
| Gazebo Sim | 8.11.0 | **8.14.0** (8.11.0 no longer in the OSRF repo) |
| ArduPilot | `7bac20cbcc` | `7bac20cbcc` (pinned, tag `thesis-baseline`) |
| ros_gz_bridge | 1.0.22 | 1.0.22 |
| **Measured RTF** | **0.05 – 0.17** | **≈0.86** (10.3 s sim in 12.0 s wall-clock) |

Gazebo 8.11.0 → 8.14.0 is unavoidable: the OSRF `ubuntu-stable` repo carries
only the current point release. These are patch releases within one LTS ABI;
`libgz-rendering8` is 8.2.3 and `libgz-sensors8` is 8.2.2. Worth re-flying a
Stage C equivalent and checking sensor-level `inlier_ratio` lands near the
recorded 0.94/0.47 as a cheap empirical check that the version step is a
non-issue.

**Known Issue #9 (low RTF) is effectively resolved** — ≈0.86 vs 0.05–0.17, a
5–17× improvement. The RTF-aware discipline in `fly_trial.py`/`run_trial.sh`
(gate on measured state, never wall-clock sleep) should nonetheless be kept:
it is correct regardless, and `MIN_ASSUMED_RTF` remains a safety net.

## Sensor Fusion Architecture

Design decision (per supervisor guidance, 2026-07-02): **each estimator
consumes raw sensor data and performs its own rotation compensation
internally**, rather than all three being fed an identically pre-processed
input.

- **Common raw inputs across all estimators:** raw optical flow
  (`flow_x_raw`/`flow_y_raw`), raw gyro/IMU angular rates
  (`/attitude/angular_rates`, and IMU generally), downward-rangefinder
  distance (`/downward_lidar/range`, injected into ArduPilot as `RNGFND1`
  via MAVLink `DISTANCE_SENSOR` by `lidar_bridge.py`; the FGO will consume
  the same ROS topic directly), and full IMU — accelerometer plus a second,
  co-sampled gyro copy — on `/imu/data_raw` (`imu_bridge.py`, see "IMU
  Bridge" below). ArduPilot EKF3 doesn't need `/imu/data_raw` itself (it
  already has its own onboard IMU access via AHRS); this topic exists for
  the UKF and FGO, whose process models need sensed specific force — without
  it, roll/pitch are not observable at all (only gyro-integrable, open-loop),
  which is not a difference EKF3 also has, so it isn't optional for a fair
  comparison.
- **ArduPilot EKF3 is the fixed baseline.** It is set up exactly as
  ArduPilot intends — native `OPTICAL_FLOW` input (**not** `OPTICAL_FLOW_RAD`,
  which this ArduPilot build doesn't handle at all — see "Downward Optical
  Flow — EKF3 Fusion (Stage A)" below), sending raw flow only — and
  derotates internally using its own AHRS gyro, not gyro data we send. No
  shortcuts, no pre-processing on our side.
- **The FGO** (GTSAM, planned) will handle rotation compensation as part of
  its own flow-factor formulation — e.g. a factor that references
  IMU/attitude state from within the graph — rather than consuming flow
  that has already been pre-derotated by a separate preprocessing step.
  This is a different mechanism to EKF3's internal derotation, and that is
  fine: it only needs to be correctly implemented for its own architecture.
- **UKF** (if implemented separately) follows the same principle: correct
  for its own measurement model, not required to match EKF3's input format.

**Fairness comes from each estimator being correctly implemented on its own
terms, not from identical preprocessing.** Forcing all three onto a common
pre-derotated flow stream would bias the comparison towards whichever
estimator that preprocessing choice happens to suit.

**Practical consequence:** the manual derotation logic in `flow_tracker.py`
(`flow_x`/`flow_y`, `enable_derotation` param) is **not a production data
path** for any estimator. It exists purely as a characterisation tool — to
quantify how much rotational coupling is present in the raw signal, useful
for the methodology write-up and for informing the FGO's factor design
later. The values actually fed to EKF3 (and later the FGO) are
`flow_x_raw`/`flow_y_raw` plus the raw rates on `/attitude/angular_rates`.

### IMU Bridge — accelerometer input for the UKF/FGO process model

`imu_bridge.py` bridges ArduPilot SITL's accelerometer + gyro onto ROS2 as
`sensor_msgs/Imu` on `/imu/data_raw`, on its own MAVLink link **port 14556, fed by a
dedicated SITL serial output** (`--serial2=udpclient:127.0.0.1:14556`, bypassing MAVProxy;
see "IMU Bridge — rate, aliasing, and the MAVProxy bypass"). It was originally 14555 via
MAVProxy. This is the raw sensor no prior
bridge provided — needed because a constant-velocity/gyro-only process
model cannot observe roll or pitch at all (only integrate them, open-loop),
which would silently corrupt the flow measurement model's world→body
velocity rotation over exactly the long GNSS-denied flights the trial
harness (`run_trial.sh`) exists to fly.

**Message choice: `HIGHRES_IMU` (100), not `RAW_IMU`/`SCALED_IMU`.** Read
`GCS_MAVLINK::send_highres_imu` directly
(`libraries/GCS_MAVLink/GCS_Common.cpp`) rather than assumed: it populates
`xacc`/`yacc`/`zacc` and `xgyro`/`ygyro`/`zgyro` straight from
`AP_InertialSensor`'s calibrated `get_accel()`/`get_gyro()` as float32 SI
units (m/s², rad/s) — no scale factor, no int16 round-trip. `RAW_IMU` and
`SCALED_IMU` both encode accel as milli-g int16 (`RAW_IMU`:
`accel.x * 1000.0f / GRAVITY_MSS`, `GCS_Common.cpp`), needlessly lossier.
Confirmed compiled into this SITL build: `AP_MAVLINK_MSG_HIGHRES_IMU_ENABLED
= (HAL_PROGRAM_SIZE_LIMIT_KB > 1024) && AP_INERTIALSENSOR_ENABLED`
(`GCS_MAVLink/GCS_config.h`) — trivially true for SITL/Copter.

**Specific force, not gravity-subtracted acceleration — confirmed
empirically, not just asserted from the source.** `AP_InertialSensor::get_accel()`
is the calibrated raw accelerometer reading; gravity compensation only
happens later, inside an EKF's own state propagation. Verified against a
recorded trial (`imu_verify`, deleted after verification — see git log for
the commit that added this bridge): at rest (pre-arm and post-land),
`linear_acceleration.z` (FLU, up positive) read **+9.811 m/s²** — matching
standard gravity almost exactly, the classic "accelerometer reads +1g
sitting on a table" result. Mid-cruise at 0.4 m/s it dropped slightly to
**+9.670 m/s²**, consistent with the small forward pitch needed to sustain
cruise tilting the sensed vertical component — a second, independent
confirmation the values are physically sensible, not just non-zero.

**Rate: 333 Hz** (the ceiling ArduPilot permits at `SCHED_LOOP_RATE=400`), requested via
`MAV_CMD_SET_MESSAGE_INTERVAL`. Measured 333.27 Hz. See "IMU Bridge — rate, aliasing, and the
MAVProxy bypass" above, including why 50 Hz aliased. **The original 50 Hz rate is
superseded.** The bridge also publishes `/imu/time_ref` (HIGHRES_IMU `time_usec`, the SITL
clock) for all bags recorded after `cb4c845`.

**Frame: FRD → FLU via `(x, -y, -z)`** for both `linear_acceleration` and
`angular_velocity` — the same already-empirically-validated
180°-about-body-X convention `flow_tracker.py` uses for gyro rates, reused
verbatim since it's a proper rotation and applies identically to any
body-frame vector.

**`angular_velocity` is a second, deliberately re-sourced gyro copy** —
read from this same `HIGHRES_IMU` message (not `/attitude/angular_rates`,
which comes from a separately-polled `ATTITUDE` message), so accel and gyro
share the exact same underlying IMU sample and timestamp. Important for a
UKF predict step and for GTSAM's preintegrated IMU factor, both of which
want co-sampled accel/gyro pairs. `flow_tracker.py`'s derotation is
unaffected and keeps using `/attitude/angular_rates` as before.

No orientation estimate is provided (`orientation_covariance[0] = -1`, per
REP-145); `angular_velocity_covariance`/`linear_acceleration_covariance`
are left at all-zero (valid data, unknown covariance, also per REP-145).

**Sim-time alignment verified** against the other three estimator inputs in
the same bag — all four topics' header-stamp spans agreed to within ~20 ms
(`/imu/data_raw` [10.190, 56.160], `/attitude/angular_rates` [10.180,
56.160], `/optical_flow/measurement` [10.198, 56.134], `/ground_truth/pose`
[10.182, 56.168]) — no clock-source mismatch between MAVLink-sourced and
Gazebo-sourced topics.

Recorded by default in both `record_trial.sh` and `run_trial.sh` trials
(`/imu/data_raw`, alongside the existing topic set).

## UKF Design (design record; the UKF is IMPLEMENTED)

*(Status 2026-09-29: the UKF is implemented as the 15-state IMU-driven filter: `src/estimators/ukf_core.py`
and `ukf_replay.py`, shared `measurement_models.py`, predicting at 0.0125 s with EKF3's
`*_NSE` values unchanged, the OI-2 dejitter and the IMU-gap rule. The Phase 4 forward-camera
heading and yaw-rate updates are in `ukf_core.py`. The design notes below were written
before implementation. The 9-state constant-velocity scaffold and the 400/50 Hz Q scaling
are superseded; see METHODOLOGY.)*

**State vector.** 9-state scaffold: `[p_E, p_N, p_U, v_E, v_N, v_U, roll,
pitch, yaw]`, ENU/FLU, Euler (not quaternion — `filterpy`'s vanilla
additive-noise UKF needs a proper manifold mean for a quaternion state,
which is real extra complexity for little benefit at this flight envelope;
Euler's gimbal-lock risk at pitch=±90° is a non-issue for gentle
hover/cruise flights). The IMU-driven deliverable extends this to 15
states by adding 3-axis `gyro_bias` (rad, delta-angle-per-predict-step) and
`accel_bias` (m/s, delta-velocity-per-predict-step) — matching EKF3's own
`state_elements` struct (`AP_NavEKF3_core.h:574-586`) exactly, both in
which physical states are estimated and in their units (delta/increment
form, not a rate — see the Q derivation below for why this matters).
`filterpy`'s `UnscentedKalmanFilter` is the recommended implementation
(sigma-point machinery only — the process/measurement models stay fully
owned code) but isn't installed yet; confirm it imports cleanly against
this machine's numpy version before relying on it (it's an old,
unmaintained package).

**Position reference point.** `p_U` is base_link height above ground —
the same physical point `/ground_truth/pose` and `/ekf/pose` already use —
**not** LiDAR or camera height directly. Mount offsets go into the
measurement models as lever arms instead: `h_range(x) = p_U − 0.12`
(LiDAR), `h_cam(x) = p_U − 0.25` (camera, used inside the flow model's
height scaling). `p_U` is initialised from the first valid LiDAR range
sample `+ 0.12`, not `(0,0,0)` — starting from an assumed-zero height would
eat a real transient. `roll0`/`pitch0` come from static gravity-vector
levelling on the first few accelerometer samples (`atan2` against sensed
`g`), not assumed level — more correct and it's exactly the sensor already
verified for this project (see IMU Bridge above). `yaw0` is arbitrary
(unobservable without a compass) — `evo`'s `-a` alignment absorbs a fixed
yaw offset for ATE/RPE, but not yaw *drift*, so this only matters for the
position metric, not for judging attitude quality directly.

**Measurement models — both directly mirror EKF3's own formulation**,
confirmed by reading `AP_NavEKF3_OptFlowFusion.cpp`/`PosVelFusion.cpp`
rather than assumed:
- Range: `h_range(x) = p_U − 0.12` (identity once the lever arm is
  applied — matches EKF3's own flat-terrain assumption under
  `EK3_SRC1_POSZ=RangeFinder`).
- Flow: rotate world-frame velocity into the body frame via the state's
  own attitude, exactly mirroring EKF3's `relVelSensor = prevTnb *
  stateStruct.velocity` (`AP_NavEKF3_OptFlowFusion.cpp:331`), height-scaled
  by `h_cam`, plus the same rotational-flow correction term
  `flow_tracker.py`'s derotation formula already uses
  (`rollspeed`/`pitchspeed` coefficients) — EKF3 does the structurally
  identical thing (`flowRadXYcomp = flowRadXY + bodyRadXYZ`,
  `AP_NavEKF3_Measurements.cpp:222-223`). Exact axis sign (`f_x`/`f_y`)
  deliberately left to be pinned down empirically at implementation time
  against the already-validated Stage A result ("vx → flow_y only"),
  not re-derived from scratch.

**Robustness — matched to EKF3's actual live values, confirmed from
source, not guessed or self-derived**, so the comparison isolates filter
formulation rather than tuning:

| Param | Value (Copter default, confirmed unset in our `.parm` files) | Source |
|---|---|---|
| `EK3_FLOW_M_NSE` | 0.25 rad/s | `AP_NavEKF3.cpp:41,321` |
| `EK3_FLOW_I_GATE` | 300 → NIS gate 9 (3σ) | `AP_NavEKF3.cpp:42,329` |
| `EK3_RNG_M_NSE` | 0.5 m | `AP_NavEKF3.cpp:293` |
| `EK3_RNG_I_GATE` | 500 → NIS gate 25 (5σ) | `AP_NavEKF3.cpp:301` |
| `FLOW_MAX` | 2.5 rad/s hard reject | `AP_NavEKF3.cpp` (~line 305) |

Gate formula confirmed exact: `testRatio = ν² / ((0.01·GATE)² · S)`,
rejected if `> 1.0` (`AP_NavEKF3_OptFlowFusion.cpp:218,253,665`). **Quality
(`inlier_ratio`) is a binary accept/reject gate, not continuous R-scaling**
— traced `AP_OpticalFlow_MAV::update()`/`writeOptFlowMeas()` directly:
EKF3 only checks `rawFlowQuality > 0`, then fuses with the fixed
`FLOW_M_NSE` regardless of the exact quality value above zero
(`AP_NavEKF3_Measurements.cpp:203`). Matching this (not continuous
scaling) avoids an unmatched extra defence that would bias the comparison.

**Process noise (Q) — the one place a naive "copy EKF3's parameter"
approach is wrong, and why.** EKF3's own formulas
(`AP_NavEKF3_core.cpp:1048,1054,1161-1163`):
```
Q_att_dt = (dt · GYRO_P_NSE)²      GYRO_P_NSE  = 0.015 rad/s
Q_v_dt   = (dt · ACC_P_NSE)²       ACC_P_NSE   = 0.35 m/s²
Q_bg_dt  = (dt² · GBIAS_P_NSE)²    GBIAS_P_NSE = 0.001 rad/s/s
Q_ba_dt  = (dt² · ABIAS_P_NSE)²    ABIAS_P_NSE = 0.02 m/s/s/s
```
> ## ⚠️ THE 400 Hz / 50 Hz SCALING BELOW IS SUPERSEDED — DO NOT USE IT
>
> **EKF3 does not predict at `SCHED_LOOP_RATE`.** It accumulates five 400 Hz
> IMU frames and predicts on the accumulated total: **actual dt = 0.0125 s
> (80 Hz)**. See "EKF3 Prediction dt" below for the source trace. The table
> that followed assumed a 8× rate gap where the real gap to a 50 Hz predict
> would be 1.6×, making its bias terms **11.18× too small**.
>
> **The whole table is now moot** because the resolution was to change the
> *rate*, not rescale the constants: the UKF predicts at EKF3's own
> **0.0125 s**, so the scale factor is exactly 1 and **EKF3's `*_NSE` values
> are used unchanged**. Nothing to derive, nothing to defend. See "IMU
> Bridge — rate and aliasing" for why the 50 Hz assumption was abandoned
> independently.

~~EKF3's own predict step runs at `SCHED_LOOP_RATE` — confirmed **400 Hz**
by reading it directly from a trial's own dataflash `PARM` dump, not
assumed~~ — **wrong, see the warning above** — while the UKF's predict step
was assumed capped at `/imu/data_raw`'s then-50 Hz. The dt-invariant
quantity that should match is accumulated variance *per second*
(`dt^(2k-1) · NSE²` for a `(dt^k · NSE)²` per-step term), giving
`NSE_UKF = NSE_EKF3 · (dt_EKF3/dt_UKF)^(k−0.5)`. **Superseded table, kept
only to show what the error was:**

| Param | EKF3 value | k | ~~Scale (400 Hz assumed)~~ | ~~Value at 50 Hz~~ | Correct scale if ever needed |
|---|---|---|---|---|---|
| `GYRO_P_NSE` | 0.015 rad/s | 1 | ~~×0.3536~~ | ~~0.0053~~ | ×0.7906 |
| `ACC_P_NSE` | 0.35 m/s² | 1 | ~~×0.3536~~ | ~~0.124~~ | ×0.7906 |
| `GBIAS_P_NSE` | 0.001 rad/s/s | 2 | ~~×0.0442~~ | ~~4.42×10⁻⁵~~ | ×0.4941 |
| `ABIAS_P_NSE` | 0.02 m/s/s/s | 2 | ~~×0.0442~~ | ~~8.84×10⁻⁴~~ | ×0.4941 |

**Use neither column. Predict at 0.0125 s and take EKF3's values as-is.**

The CV scaffold's velocity process noise has **no EKF3 counterpart at
all** (EKF3 has no undriven "velocity random walk" state) — use the
standard discrete white-noise-acceleration form,
`Q = σ_a² · [[dt⁴/4, dt³/2],[dt³/2, dt²]]` per axis, `σ_a ≈ 0.3–0.5 m/s²`
as a starting point, tuned empirically (unmatched by construction, unlike
everything above).

**Covariance logging.** `/ukf/pose` should publish as
`geometry_msgs/PoseWithCovarianceStamped`, not `PoseStamped` — confirmed
`evo` natively supports this type (`evo/tools/file_interface.py:48-52`),
so this is a drop-in replacement for the existing `evo_ape`/`evo_rpe`
workflow (`/ekf/pose` stays plain `PoseStamped`; each bag topic is handled
by its own declared type) while also carrying the 6×6 position/orientation
covariance needed for a NEES consistency check against `/ground_truth/pose`.

**Multi-rate handling.** Live, asynchronous — no fixed-rate loop.
`/attitude/angular_rates`-equivalent (in practice, `/imu/data_raw`'s own
co-sampled gyro, not a second poll of `/attitude/angular_rates` — see IMU
Bridge above) drives PREDICT on arrival; `/optical_flow/measurement` and
`/downward_lidar/range` each trigger a catch-up predict (last-known gyro
rate, zero-order hold, `dt ≥ 0` guarded) then their own UPDATE. Publish
after every update from any source, stamped from that message's own
header — matches how this would run unchanged on real hardware.

**Validation plan** (mirrors Stages A/B/C): scaffold plumbing check
(replay an existing bag, confirm no divergence/crashes, not a thesis
result) → flow-only sanity check (commanded 0.4 m/s should converge
`v_body_x ≈ 0.4`, mirrors Stage A's own validation method) → nominal ATE
baseline (`evo_ape`/`evo_rpe` vs `/ground_truth/pose`, compare against
Stage B's numbers, expect worse absolute accuracy — that's fine) →
GNSS-denied textured-vs-blank comparison with innovation/rejection stats
(mirrors Stage C) → NEES consistency check from the logged covariance.

## No-Yaw / Compass-Denied Investigation

**Finding: EKF3 fuses the compass for yaw under `gnss_denied.parm`,
outside the thesis's stated IMU+flow+LiDAR sensor suite.**
`gnss_denied.parm` never touches `EK3_SRC1_YAW`, so it stays at its
Copter default (`COMPASS`, confirmed via dataflash `PARM` readback:
`EK3_SRC1_YAW = 1.0`). This is the identical category of confound as the
accelerometer gap that motivated the IMU bridge — EKF3 gets an absolute
yaw reference the UKF/FGO don't have at all.

**Fix found and verified working.** It lives in `gnss_denied_nomag.parm`, which **is now the
three-way comparison configuration**: `run_trial.sh` loads it for every `dsn_*` and
forward-camera trial (METHODOLOGY "Comparison dataset — nomag"). `gnss_denied.parm` itself is
unchanged, and the compass-active `ds_*` trials are retained as a reference:
```
EK3_SRC1_YAW 0        # None
COMPASS_ENABLE 1      # counter-intuitive - see below
COMPASS_USE 0
COMPASS_USE2 0
COMPASS_USE3 0
EK3_GSF_RUN_MASK 3    # = EK3_IMU_MASK default, self-documenting only
EK3_GSF_USE_MASK 3    # (GSF is unconditionally unavailable here anyway)
```
`COMPASS_ENABLE=1` is required, not a mistake — `AP_Arming_Copter.cpp`'s
`arm_checks()` has its own unconditional compass-health gate (line ~575,
`#ifndef ALLOW_ARM_NO_COMPASS`, not defined for this SITL build) separate
from the generic `AP_Arming::compass_checks()`. It only skips if
`ahrs.using_noncompass_for_yaw()` is true, which (`AP_NavEKF3_Control.cpp:
642`) requires a *recent* non-compass yaw-fusion timestamp — impossible
with no GPS, and GSF is unconditionally gated off too
(`runYawEstimatorPrediction()`/`Correction()`,
`AP_NavEKF3_Control.cpp:827,850`, require `EK3_SRC1_POSXY`/`VELXY` to be
GPS, which `gnss_denied.parm` already sets to None/OpticalFlow). With
`COMPASS_ENABLE=0` this arming check fails outright
(`"AP: Arm: Compass 1 not healthy"`, reproduced then fixed). Keeping the
compass "present and healthy" while `COMPASS_USE*=0` + `EK3_SRC1_YAW=0`
keep it out of actual fusion satisfies the arming gate without giving
EKF3 any real yaw information.

**Verified genuinely not fusing, same evidence standard as everything
else in this project** — not just assumed from the param values: with
this config, `XKFS.MAG_FUSION=0` for the entire flight (vs `1` in the
compass-active baseline) and `XKF2`'s mag field states stay frozen at
`(0,0,0)` (vs actively-evolving nonzero values normally). `XKF3.IYAW` is
*not* all-zero — traced this to EKF3's own internal "synthetic yaw"
mechanism (`AP_NavEKF3_MagFusion.cpp`), which fuses a zero-innovation or
last-known-static pseudo-observation every 140 ms purely to stop yaw
covariance from numerically blowing up (source comment: "prevent
uncontrolled yaw variance growth... by fusing a zero innovation") — not
real yaw information.

> ## ⚠️ THE YAW-DRIFT RESULT BELOW IS VOID — DO NOT QUOTE IT
>
> The ±0.03° / ≈0.000 deg/min figure was measured as "EKF3 estimate vs
> `/ground_truth/pose`, compared directly in the bag" — but the EKF3 side came
> from `/ekf/pose`, which is **simulator ground truth** under
> `AHRS_EKF_TYPE=10` (see Hidden Configuration Audit §1). It therefore compared
> truth against truth and would have returned ≈zero **with or without a
> compass**. The pass criterion "yaw drift stays bounded enough for corridor
> experiments" was never actually tested.
>
> *(Status 2026-09-29: re-measured, and the parameter file adopted.)* EKF3's own no-compass
> yaw drift from `XKF1.Yaw` is **+6.6…+11.1 deg/min (mean ~8.1), n = 9 `dsn_*` bags**
> (METHODOLOGY, source-pack flag resolutions §2). `gnss_denied_nomag.parm` is now the
> comparison configuration for all three estimators. The original caveat was: "must NOT be
> folded into the standing baseline until re-measured from `XKF1`'s own yaw". The elaborate mechanism discussion below (synthetic yaw,
> gyro-bias coupling) remains valid — only the *number* is void.

**Long-flight result (320 s, `iris_textured.sdf`, 0.4 m/s cruise —
corridor worlds weren't usable yet, see Known Issues #11/#12): yaw error
vs `/ground_truth/pose` stayed essentially zero the whole flight** (±0.03°
max, linear-fit drift rate ≈0.000 deg/min, R²≈0) — **VOID, see the warning
above; this measured truth against truth.** **This is not evidence
that yaw drift is a non-issue in general** — three things specific to
this test explain it: EKF3 still estimates a full 3-axis `gyro_bias` state
even with `EK3_SRC1_YAW=0` (its accelerometer-aided roll/pitch corrections
constrain the joint covariance including the bias vector's yaw component);
SITL's simulated gyro is very clean/low-bias; the flight itself is pure
straight-line cruise with almost no actual commanded yaw rotation. A
constant-velocity UKF scaffold with no bias estimation should be expected
to drift measurably more than this — the IMU-driven UKF (which already
matches EKF3's own `gyro_bias`/`accel_bias` state structure, see UKF
Design above) is the one that should plausibly get close to this result.
Lateral deviation from the commanded straight path stayed small (+0.28 m
at 160 s, +0.55 m at 320 s) — fully consistent with the near-zero yaw
error. Flow/range fusion was undisturbed by removing yaw (0/3267 rejected,
mean NI=7.7, actually better than Stage C's mean 15); `inlier_ratio`
stayed ~0.98 throughout, including well past the point the drone left the
20×20 m mat — contrary to the expected confound, worth noting honestly
rather than forcing the expected result.

## Launch Sequence

Run each terminal in order. Source commands are mandatory before ROS2 tools.

### Preferred: use launch scripts

```bash
# Degraded baseline (blank floor)
./start_sim.sh

# Nominal baseline (textured checkerboard floor)
./start_sim.sh iris_textured.sdf

# Long-duration corridor worlds (see "Corridor Worlds" below) — nominal,
# degraded, and mid-flight transition, all 20 m x 160 m
./start_sim.sh corridor_textured.sdf
./start_sim.sh corridor_blank.sdf
./start_sim.sh corridor_transition.sdf

# Tear down and close all tabs
./stop_sim.sh
```

### Manual launch (if needed)

#### Terminal 1 — Gazebo

```bash
cd ~/ardupilot_gazebo
export GZ_SIM_RESOURCE_PATH=$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds:$GZ_SIM_RESOURCE_PATH
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build:$GZ_SIM_SYSTEM_PLUGIN_PATH
gz sim -v4 -r worlds/iris_textured.sdf
```

### Terminal 2 — ArduPilot SITL

```bash
source ~/venv-ardupilot/bin/activate
cd ~/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py \
  -v ArduCopter \
  -f gazebo-iris \
  --model JSON \
  --console \
  --map \
  --out 127.0.0.1:14551 \
  --out 127.0.0.1:14552 \
  --out 127.0.0.1:14553 \
  --out 127.0.0.1:14554 \
  -A "--serial2=udpclient:127.0.0.1:14556" \
  --add-param-file $HOME/thesis_ws/lidar_rangefinder.parm \
  --add-param-file $HOME/thesis_ws/flow_ekf.parm \
  --add-param-file $HOME/thesis_ws/gnss_denied.parm \
  --add-param-file $HOME/thesis_ws/gnss_denied_nomag.parm \
  --add-param-file $HOME/thesis_ws/sim_noise.parm \
  --no-rebuild
```

The extra `--out 127.0.0.1:14551` gives `attitude_bridge.py` (Terminal 7) its
own dedicated MAVLink output, `--out 127.0.0.1:14552` gives `lidar_bridge.py`
(Terminal 8) its own, `--out 127.0.0.1:14553` gives `flow_bridge.py`
(Terminal 9) its own, `--out 127.0.0.1:14554` gives `ekf_bridge.py`
(Terminal 10) its own, and `imu_bridge.py` (Terminal 11) is fed directly by SITL serial 2 on
`14556` (`-A` passes `--serial2=udpclient:127.0.0.1:14556` to the SITL binary, as
`run_trial.sh` does), bypassing MAVProxy — all separate from the default `14550` that
`fly_forward.py` connects to — pymavlink's plain `udp:` scheme binds and
listens, so no two processes can share one port. `--add-param-file` (passed
three times, `action="append"` in `sim_vehicle.py`) appends
`lidar_rangefinder.parm`, then `flow_ekf.parm`, then `gnss_denied.parm` after
the frame's own defaults (`copter.parm,gazebo-iris.parm`), so their values
win over `gazebo-iris.parm`'s Analog/SIM_SONAR-based RNGFND1 block
(`--add-param-file` appends to the end of the `--defaults` comma list, and
later files override earlier ones for duplicate params). **`gnss_denied.parm`
is loaded by default** — this is the standing GNSS-denied baseline config as
of Stage C (see "GNSS-Denied Configuration — Stage C" below), not an
opt-in extra.

Once MAVProxy starts:

```
mode GUIDED
arm throttle
takeoff 2
```

Typical movement commands:

```
velocity 0.5 0 0   # forward (one-shot, times out after ~3 s)
velocity 0 0.5 0   # strafe
velocity 0 0 0     # stop
mode LAND
```

For continuous flight (bypasses GUIDED timeout):

```bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/fly_forward.py        # 0.5 m/s forward
python3 ~/thesis_ws/fly_forward.py 1.0   # 1.0 m/s forward
# Ctrl+C sends zero velocity and stops
```

### Terminal 3 — ROS2 Bridge

Replace `iris_textured` with `iris_runway` if running the degraded world.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  /downward_camera/image@sensor_msgs/msg/Image@gz.msgs.Image \
  /downward_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo \
  /downward_lidar/range@sensor_msgs/msg/Range[gz.msgs.LaserScan \
  /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
  /world/iris_textured/dynamic_pose/info@geometry_msgs/msg/PoseArray[gz.msgs.Pose_V
```

`start_sim.sh` fills in the world name automatically from its argument.

### Terminal 4 — Image Viewer (optional debug)

```bash
source /opt/ros/jazzy/setup.bash
ros2 run rqt_image_view rqt_image_view
# Select /downward_camera/image
```

### Terminal 5 — Optical Flow Node

```bash
source /opt/ros/jazzy/setup.bash
source ~/thesis_ws/install/setup.bash
ros2 run optical_flow_node flow_tracker --ros-args -p use_sim_time:=true
```

### Terminal 6 — Ground Truth Publisher

Republishes Gazebo pose of `iris_with_ardupilot` as `/ground_truth/pose`.
Run after the bridge (Terminal 3) is up.

```bash
source /opt/ros/jazzy/setup.bash
python3 ~/thesis_ws/ground_truth_pub.py iris_textured
# For degraded world: python3 ~/thesis_ws/ground_truth_pub.py iris_runway
```

Verify:
```bash
ros2 topic hz /ground_truth/pose      # expect 50–250 Hz
ros2 topic echo /ground_truth/pose    # confirm position changes during flight
```

### Terminal 7 — Attitude Bridge

Republishes ArduPilot body angular rates (MAVLink ATTITUDE) as
`/attitude/angular_rates` (`geometry_msgs/Vector3Stamped`, raw FRD rates —
x=roll rate, y=pitch rate, z=yaw rate, rad/s). Consumed by `flow_tracker.py`
for gyro decoupling. Run after SITL (Terminal 2) is up and streaming on
`14551`.

```bash
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/attitude_bridge.py --ros-args -p use_sim_time:=true
```

Verify:
```bash
ros2 topic hz /attitude/angular_rates   # expect ~50 Hz
```

### Terminal 8 — LiDAR Bridge

Forwards `/downward_lidar/range` (`sensor_msgs/Range`) to ArduPilot as
`RNGFND1` via MAVLink `DISTANCE_SENSOR`, on its own dedicated port (`14552`)
— see [Sensor Fusion Architecture](#sensor-fusion-architecture). Run after
SITL (Terminal 2) is up and streaming on `14552`, and after the ROS2 Bridge
(Terminal 3) so `/downward_lidar/range` exists.

```bash
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/lidar_bridge.py --ros-args -p use_sim_time:=true
```

Verify: MAVProxy console should show `RNGFND1: healthy` (or similar) once
readings start arriving; `rangefinder` in the MAVProxy console prints the
current distance. Cross-check against `/ground_truth/pose` z during a hover.

### Terminal 9 — Flow EKF Bridge

Forwards `/optical_flow/measurement` to ArduPilot's EKF3 as MAVLink
`OPTICAL_FLOW` (message 100 — **not** `OPTICAL_FLOW_RAD`, which this
ArduPilot build does not handle), on its own dedicated port (`14553`) — see
"Downward Optical Flow — EKF3 Fusion (Stage A)" below. Run after SITL
(Terminal 2) is up and streaming on `14553`, and after the Optical Flow node
(Terminal 5) so `/optical_flow/measurement` exists. Also subscribes
`/downward_lidar/range` for the message's `ground_distance` field, so
Terminal 8 should be up too (not required for it to start, but
`ground_distance` reports as unknown, `-1`, until it is).

```bash
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/flow_bridge.py --ros-args -p use_sim_time:=true
```

Verify: see "Downward Optical Flow — EKF3 Fusion (Stage A)" below for the
definitive (dataflash-log-based) verification method — a message merely
arriving does not confirm EKF3 is fusing it.

### Terminal 10 — EKF Pose Bridge

Forwards ArduPilot EKF3's state estimate (MAVLink `LOCAL_POSITION_NED` +
`ATTITUDE_QUATERNION`) to ROS2 as `/ekf/pose` (`geometry_msgs/PoseStamped`,
ENU/FLU — transformed from ArduPilot's native NED/FRD, see "EKF State
Estimate — Stage B" below), on its own dedicated port (`14554`). Run after
SITL (Terminal 2) is up and streaming on `14554`.

```bash
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/ekf_bridge.py --ros-args -p use_sim_time:=true
```

Verify:
```bash
ros2 topic hz /ekf/pose               # expect ~30 Hz sim-time (see RTF note in Known Issues)
ros2 topic echo /ekf/pose --once      # confirm position/orientation look sane
```

### Terminal 11 — IMU Bridge

Forwards ArduPilot SITL's accelerometer + gyro (MAVLink `HIGHRES_IMU`) to
ROS2 as `/imu/data_raw` (`sensor_msgs/Imu`, FLU — see "IMU Bridge" above) and
`/imu/time_ref`, on port `14556`, fed directly by SITL serial 2 (see Terminal 2). Run after SITL
(Terminal 2) is up.

```bash
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/imu_bridge.py --ros-args -p use_sim_time:=true
```

Verify:
```bash
ros2 topic hz /imu/data_raw           # expect ~333 Hz sim-time (wall-clock = 333 x RTF)
ros2 topic echo /imu/data_raw --once  # confirm linear_acceleration.z ~= +9.8 at rest
```

### Terminal 12 — Bag Recording (one trial)

```bash
cd ~/thesis_ws
./record_trial.sh test_001 --world iris_textured --velocity 0.5 --altitude 2.0 --notes "first clean trial"
# Ctrl+C to stop recording; script then copies the ArduPilot .BIN log automatically.

# Inspect the result:
ros2 bag info ~/thesis_data/trials/test_001/bag/
cat ~/thesis_data/trials/test_001/metadata.yaml

# Evaluate the EKF estimate against ground truth (see "EKF State Estimate — Stage B"):
./evaluate_trial.sh test_001
```

## Build Commands

```bash
source /opt/ros/jazzy/setup.bash
cd ~/thesis_ws
# Build message definitions first (ament_cmake), then the node (ament_python).
colcon build --packages-select optical_flow_interfaces optical_flow_node --symlink-install
source install/setup.bash
```

## Current System Architecture

```
Gazebo World (iris_textured.sdf / iris_runway.sdf)
  └─ iris_with_ardupilot model
       └─ Downward camera sensor (iris_with_standoffs/model.sdf)
            │  gz transport
            ▼
       ros_gz_bridge
            ├─ /downward_camera/image      (sensor_msgs/Image)
            ├─ /downward_camera/camera_info (sensor_msgs/CameraInfo)
            ├─ /clock                      (rosgraph_msgs/Clock)  ← sim time
            └─ /world/<world>/dynamic_pose/info (geometry_msgs/PoseArray)
                                                      │
                                               ground_truth_pub.py
                                                      │
                                               /ground_truth/pose (PoseStamped)
                                                      │
            │                                         │
            ▼                                         │
       flow_tracker.py                                │
            │  Shi-Tomasi + Lucas-Kanade + RANSAC     │
            ▼                                         │
       /optical_flow/measurement                      │
       (optical_flow_interfaces/OpticalFlow)          │
            │                                         │
            └──────────────┬───────────────────────────┘
                           ▼
                    record_trial.sh
                           │
                    ~/thesis_data/trials/<name>/
                           ├─ bag/           (ROS2 bag: clock, ground_truth, flow)
                           ├─ metadata.yaml
                           └─ ardupilot.bin
```

## Data Collection

### Trial directory layout

```
~/thesis_data/trials/<trial_name>/
    bag/            ← ROS2 bag (created by ros2 bag record)
    metadata.yaml   ← written before recording starts
    ardupilot.bin   ← newest .BIN from ~/ardupilot/ArduCopter/logs/
```

### record_trial.sh interface

```bash
./record_trial.sh <trial_name> [OPTIONS]

Options:
  --world NAME              Gazebo world name (default: iris_textured)
  --velocity M/S            Target forward velocity
  --altitude M              Target hover altitude
  --notes TEXT              Free-form notes
  --ardupilot-log-dir DIR   Override ArduPilot log directory
                            (default: ~/ardupilot/ArduCopter/logs)
  --with-images             Also record /downward_camera/image and
                            /downward_camera/camera_info
                            (default: off — raw images ~0.9 MB/frame)
```

Topics recorded by default: `/clock`, `/ground_truth/pose`, `/ekf/pose`,
`/downward_lidar/range`, `/attitude/angular_rates`, `/imu/data_raw`,
`/optical_flow/measurement` (plus any topic matching `^/(flow|optical_flow)`
found on the bus at startup).

### metadata.yaml schema

```yaml
trial_name: <name>
timestamp_utc: 2026-07-02T04:31:17Z   # ISO 8601 UTC, wall clock
world: iris_textured
target_velocity_m_s: 0.5
target_altitude_m: 2.0
with_images: false
git_commit: <SHA of thesis_ws HEAD>
hostname: <machine name>
notes: "free text"
```

### Signal trap behaviour

Ctrl+C sends SIGINT to the whole process group. A `trap '...' INT` in
`record_trial.sh` intercepts the signal in the shell, allowing `ros2 bag record`
to flush and exit cleanly before the script continues to copy the ArduPilot log.

## Known Issues (to resolve in Phase 1)

1. **Manual derotation is a characterisation tool, not a blocker** — `attitude_bridge.py` publishes body rates on `/attitude/angular_rates`; `flow_tracker.py` subtracts rotational flow (`enable_derotation` param, default on) and publishes both `flow_x`/`flow_y` (derotated, characterisation-only) and `flow_x_raw`/`flow_y_raw` (raw, the production values) in `OpticalFlow.msg` — see [Sensor Fusion Architecture](#sensor-fusion-architecture). Isolated pure-rotation hover testing (yaw done, pitch/roll not) found only a partial 5–15% collapse, confounded by a persistent ~0.4 rad/s background sim vibration present even at idle hover. **This is deprioritised/deferred indefinitely** — it was only relevant to validating a production derotation path that is no longer needed; ArduPilot EKF3 derotates internally from raw flow + gyro, and the FGO will do its own rotation compensation in its flow factor.
2. **Drone shadow** contaminates downward optical flow (biases toward zero)
3. **Timestamp sync** between Gazebo sim time, ROS time, and ArduPilot: sim time resolved via `/clock` bridge + `use_sim_time:=true`; ArduPilot-to-ROS sync not yet done
4. ~~`record_trial.sh` silently dropped `/optical_flow/measurement` from bags~~ — **fixed**: it wasn't sourcing `~/thesis_ws/install/setup.bash`, so `ros2 bag record` couldn't resolve the custom `optical_flow_interfaces` package for that topic (found during EKF3 flow fusion Stage A verification).
5. **Downward LiDAR RNGFND1 dropouts under aggressive attitude changes** — ~3% of readings during a dynamic climb briefly read near-zero instead of true altitude (steady hover is sub-cm accurate). Currently harmless since `EK3_RNG_USE_HGT=-1` keeps RNGFND1 out of the EKF's height estimate by default — see "Downward LiDAR — Stage 2" above. Revisit before ever enabling range-based height switching or surface tracking.
6. **Textured world too small — and the consequence is far worse than "feature-poor segments".** 20 m × 20 m checkerboard (spans y = −10…+10 m); drone exits the mat during forward-flight trials. **Measured 2026-07-22: the `textured_ground` plane is the ONLY ground geometry in `iris_textured.sdf`, so past the mat edge the downward LiDAR returns the 41.0 no-return sentinel on 100% of samples** (606/606 and 636/636 in two consecutive windows). `lidar_bridge.py` correctly drops them, `RNGFND1` is starved, and since `EK3_SRC1_POSZ=2` is the height source, **EKF3 loses HAGL and flow fusion stops outright** — it cannot scale pixel rates into velocity without height. `horiz_pos_rel` goes false, `const_pos_mode` returns, and the position estimate freezes. Confirmed in `ekf3_diag_60s`: aiding dropped at t=56.55 s (y≈10 m, the mat edge) and never recovered; `PN` froze at 6.5 m while the drone flew on to 24.2 m. **Flow quality is NOT the mechanism** — `inlier_ratio` stayed 0.93–0.99 off the mat and `feature_count` actually rose to 120, matching the no-yaw flight's observation. This makes `iris_textured.sdf` unusable for any trial travelling more than ~10 m, which is why the 160 m corridor worlds exist.
7. **Feature count is a deceptive quality metric** — ~100 features reported even on featureless off-mat texture. Use `inlier_ratio` (RANSAC survivors / pre-RANSAC tracked) as the real flow-quality indicator.
8. **TFMessage bridge broken** — `gz.msgs.Pose_V → tf2_msgs/TFMessage` in ros_gz_bridge 1.0.22 zeroes all stamps and clears all frame IDs. **Do not use it for ground truth** — see Ground Truth Bridging section above.
9. **~~Real-time factor is low on this machine~~ — RESOLVED by the 2026-07-22 migration.** On the new desktop (i7-8700, 65 W, + Quadro P620) a full `run_trial.sh` flight measured **RTF ≈ 0.86** (10.3 s sim in 12.0 s wall-clock), against 0.05–0.17 on the ThinkPad — a 5–17× improvement. The old machine's ceiling was a 15 W throttled mobile CPU with integrated graphics sharing the same power budget; the discrete GPU also removes render contention. **The RTF-aware discipline below remains correct and must be kept** — gate on measured state, never wall-clock sleep — and `MIN_ASSUMED_RTF` stays as a safety net. Note this did NOT fix Known Issue #11, which is algorithmic, not throughput-bound. Original entry follows. — measured RTF ≈ 0.05–0.17 (`gz topic -e -t /stats`), even headless with no GUI/ArduPilot attached. All sensor `update_rate` values are sim-time periods, so the wall-clock publish rate seen by `ros2 topic hz` is roughly `update_rate × RTF` — e.g. the downward LiDAR's configured 30 Hz currently yields only ~3.6–4 Hz wall-clock, even though its true sim-time rate (header-stamp deltas) is a correct 30.3 Hz. This affects every sensor topic, not just the LiDAR; when checking whether a sensor is "running at the right rate," check sim-time stamp spacing, not `ros2 topic hz`, which conflates the two. **Also affects scripted flight tests directly** — a `time.sleep(N)`-based flight script only buys ~N×RTF seconds of sim time; gate test phases on measured state (altitude, position) instead, see "Downward Optical Flow — EKF3 Fusion (Stage A)" above. Also relevant when planning trial durations (wall-clock trial time will be much longer than the simulated flight time it captures). **This is the reason the workstation is being migrated to a second Ubuntu 24 machine** — ROS2/Gazebo/ArduPilot still need setting up there; until that's done, this machine remains the working environment.
10. **SITL's persisted `eeprom.bin` can silently defeat `--add-param-file`** — once a param has any explicitly-stored value in `~/ardupilot/ArduCopter/eeprom.bin` (gitignored, persists across SITL sessions), `AP_Param::configured_in_storage()` means `--defaults`/`--add-param-file` no longer override it. Fix with a live `PARAM_SET` + `MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN` (soft in-process reboot, no relaunch needed) rather than deleting the eeprom file. See "Downward Optical Flow — EKF3 Fusion (Stage A)" above for how this was found (`FLOW_TYPE` silently stuck at `10` instead of the `5` in `flow_ekf.parm`).
11. **~~Gazebo↔SITL JSON lockstep stalls on `corridor_textured.sdf`~~ — FIXED AND VERIFIED 2026-07-23.**

    **Fix applied:** all floor tiles are now visual-only
    (`model://textured_ground_visual`, `model://blank_ground_visual`) and each
    corridor world includes exactly one `model://ground_collision`. The
    `spawn_margin` patch was removed — it carried its own `<plane>` collision
    and existed in only two of the three worlds — and is replaced by a full
    tile at y=−10 (covering y=−20…0) applied identically to all three, which
    preserves the knife-edge protection it provided. All three worlds now have
    **0 inline `<collision>` blocks, 1 `ground_collision`, and 9 tiles at
    identical poses**.

    **Verified end-to-end (2026-07-23), 0.5 m/s, 300 s cruise, 151 m travelled:**

    | | textured | blank | transition |
    |---|---|---|---|
    | trial completed | ✅ | ✅ | ✅ |
    | RTF (live lockstep) | **0.917** | 0.912 | 0.927 |
    | `no link` / flapping events | **0** (was 37) | 0 | 0 |
    | JSON stalls | 0 | 0 | 0 |
    | MAVProxy vehicle detect | **1 s** (was 71 s) | 1 s | 1 s |

    **`corridor_textured` has now flown a full trial end-to-end** — previously
    "not reliably reproducible". **Live-lockstep RTF is 0.919 mean**, higher
    than the 0.40–0.44 standalone figures (standalone has no SITL, so
    `ArduPilotPlugin` blocks on connection timeouts).

    **The heartbeat/link failures were a *consequence* of RTF, not a separate
    bug.** MAVProxy waits for a 1 Hz **sim-time** heartbeat; at RTF 0.0134 that
    arrived every ~75 s wall-clock, which is why detection took 71 s and
    `PARAM_REQUEST_READ` round trips timed out. At RTF 0.919 it arrives every
    ~1.09 s. **No timeout value was changed** — the 240 s cap is untouched.

    **Batch cost, 320 s cruise @ 0.5 m/s, 3 worlds × 3 repeats:** 386 s/trial →
    **58 minutes for 9 trials**. At the pre-fix RTF of 0.0134 the same batch
    would have taken **~66 hours**.

    Original investigation and the root-cause measurements follow.

    **Root cause (2026-07-22): eight coincident infinite collision planes, NOT a hardware/CPU limit.**

    **`textured_ground` uses `<plane>` collision geometry, which is an infinite
    half-space — `<size>` constrains only the visual.** `corridor_textured.sdf`
    includes 8 copies of that model, so the physics solver resolves 8
    overlapping unbounded contact manifolds every tick. Measured standalone
    (headless `gz sim`, no SITL attached, identical conditions, RTF from
    `/clock` sim-time advance over a 25–40 s window):

    | Configuration | RTF | `gz sim` CPU |
    |---|---|---|
    | `corridor_textured` as-is | **0.0134** | 99.5% |
    | shadows disabled (`cast_shadows` false) | 0.0135 | 99.4% |
    | 1 floor tile + both walls | 0.3928 | 66.0% |
    | **all 8 tiles rendering, only 1 with collision** | **0.3934** | 65.5% |
    | `iris_textured` (reference) | 0.3965 | 65.0% |

    **A 29× speedup with the full 160 m checkerboard still rendering.** Shadows
    ruled out. The two walls cost nothing. The tile *visuals* cost nothing. The
    entire penalty was collision geometry.

    **The fix is scientifically free**: keep all 8 tile visuals (optical flow
    sees an identical checkerboard) and give only one tile collision. The
    remaining plane is infinite, so ground collision still spans the whole
    corridor. `gpu_lidar` raycasts against the *rendering* scene, not collision
    — verified: 0.076 m at rest in a collision-stripped world, exactly matching
    the base_link 0.195 m − LiDAR offset 0.12 m geometry, not the 41.0
    no-return sentinel.

    **The 2026-07-22 machine migration did NOT fix this** — re-tested on the
    new desktop (i7-8700, Quadro P620) and `corridor_textured` still failed a
    trial, with 37 `no link`/`link 1 down` flapping events and an `ArduPilot
    controller has reset`. That is expected in hindsight: this is an
    algorithmic blow-up in a single-threaded solver, and no realistic CPU
    upgrade closes a 30× gap. The original "needs better single-core
    performance" prediction was directionally right but the magnitude made a
    hardware fix impossible.

    **Caveat on the measurements**: taken standalone with no SITL attached, so
    absolute RTF differs under a live JSON lockstep. The relative comparison is
    sound (identical conditions throughout); a full `run_trial.sh` on a fixed
    world is the confirming test and has not yet been run.

    **Worth re-examining Known Issue #12 in this light** — now that `gpu_lidar`
    is confirmed to use the rendering scene rather than collision,
    `corridor_blank.sdf`'s 41.0 no-return points at its floor *visual*, not its
    collision geometry.

    The original investigation is preserved below. Its evidence chain was
    sound; only the final attribution (machine speed) was wrong — the CPU was
    pegged because of the redundant collision work, not because the machine was
    too slow.
    - `gdb` attached to `arducopter` showed SITL's main thread blocking in `SITL::JSON::recv_fdm()`, waiting on Gazebo's next physics packet; `arducopter.log` shows "No JSON sensor message received, resending servos" during the stall; it self-heals once Gazebo's `ArduPilotPlugin` hits its own timeout (`connectionTimeoutMaxCount`) and resets ("ArduPilot controller has reset" in `gazebo.log`).
    - Initially misdiagnosed as slow **loading** (more `textured_ground` tiles taking longer to load) — wrong: all worlds finish *loading* in ~5–6 s regardless.
    - Ruled out headless-vs-GUI as the cause: reproduced the identical `"no link"`/`"link 1 down"`/`"link 1 OK"` flapping in MAVProxy's console, plus a *new*, more basic prearm rejection (`"AP: Arm: System not initialised"`, alongside the previously-seen `"Accels inconsistent"`), running `corridor_textured.sdf` manually via `start_sim.sh` **with the Gazebo GUI**, not just headless via `run_trial.sh`.
    - **The actual cause**: `ps aux` during that manual GUI run showed the `gz sim server` process pegged at **102% CPU** — saturating a full core — confirmed in both headless and GUI-mode runs. `corridor_textured.sdf` (20×160 m, 2 wall boxes + 8 floor tiles) is a genuinely heavier world to simulate *every tick*, not just to load, than `iris_textured.sdf` (single small 20×20 m plane). On a machine already known to struggle holding real-time factor even on the light world (see Known Issue #9), the heavier corridor world's steady-state CPU cost appears to push Gazebo below the responsiveness the JSON lockstep interface needs — explaining the blocking, the resets, the link flapping, and the cascading param-read/arm failures as one unified mechanism, not several unrelated bugs.
    - The ~100% figure is on essentially **one core**, not spread across several — the bottleneck looks single-thread/single-core-bound, not something "more cores" alone would fix.
    - `--default-modules` (excluding MAVProxy's own `param` module, which auto-downloads the full parameter set on connect and was found flooding the same link) measurably reduces failure severity — confirmed via `strace`: traffic dropped ~72% (1692 → 461 `sendto` calls), and it changed hard first-attempt failures into recoverable-with-retries — but it is **not a fix**, since it doesn't address the underlying CPU bottleneck. A run with it applied still stalled indefinitely at arming with the same `"Accels inconsistent"`/link-flapping pattern.
    - **Prediction for the machine migration**: this should improve on a faster machine, but specifically needs better *single-core* performance, not just a newer/multi-core CPU — re-test `corridor_textured.sdf` directly (watch `gz sim server`'s CPU% and whether "no link" recurs) as an early validation once the new machine is set up, rather than assuming it's resolved.
    - **Open tension, not fully reconciled**: an earlier report (from a separate investigation session) claimed this stall "reproduces identically on `iris_textured.sdf`" too — that was never independently re-confirmed under a live CPU-saturation check the way the corridor-world case now has been, and doesn't sit easily next to `iris_textured.sdf`'s otherwise consistent reliability across dozens of trials this project. Possibly that observation was a different, more transient phenomenon (a single early connection-reset event, which can happen briefly on any world and normally self-heals in seconds) rather than the same sustained, CPU-bound flapping documented here for the corridor world. Not resolved — flagging honestly rather than forcing a tidy story.
12. **~~`corridor_blank.sdf` fails to arm~~ — FIXED AND VERIFIED 2026-07-23. Root cause: the world had no adequately rendered floor, and `gpu_lidar` raycasts the *rendering* scene.**

    `corridor_blank.sdf` previously used a single inline 20×164 m `blank_floor`
    plane. It has been replaced by **9 visual-only `blank_ground_visual` tiles
    at the same 9 poses as `corridor_textured`'s checkerboard**, differing
    **only** in material (no `albedo_map`) — same geometry, same extent, same
    ambient/diffuse/specular/roughness/metalness. Texture is therefore the only
    variable between conditions, by construction.

    **This matters scientifically, not just mechanically.** A world with
    nothing rendered beneath the drone is *not* a degraded-sensing condition —
    the downward camera would see skybox, giving static features, a
    deceptively **high** `inlier_ratio`, and flow confidently reporting ≈zero
    motion. That is absence of a scene, not low-texture degradation, and it is
    not the phenomenon this thesis studies.

    **Verified:** LiDAR reads **0.075 m at y = 0, 80 and 150 in all three
    corridor worlds** (9/9 probes, exactly `base_link 0.195 − LiDAR 0.12`),
    never the 41.0 no-return sentinel. `corridor_blank` **arms and flies a full
    151 m trial**.

    **Degradation confirmed against the `iris_runway` baseline of 0.28:**

    | | textured | blank | transition (textured half / blank half) |
    |---|---|---|---|
    | `inlier_ratio` | **0.9752** | **0.3101** | 0.9737 / 0.3138 |
    | median | 1.0000 | 0.2381 | — |
    | % below 0.5 | 0.0% | **85.0%** | — |
    | `feature_count` | 52.5 | **7.9** (min 0) | 53.1 / 8.0 |
    | `flow_y_raw` | **131.6 px/s** | **−0.71 px/s** | 136.4 / −3.19 |

    Both hold flat across all four 40 m bands, so neither is an edge effect.
    **This is the correct degraded signature — low confidence AND zero flow.**
    The skybox failure mode would show *high* confidence with zero flow.

    `corridor_transition` switches exactly at the boundary: `inlier_ratio`
    0.9611 at y 75–80, **0.3846 at y 80–85**, 0.3147 at y 85–100, with the
    crossing measured at sim t=190.3 s, **ground-truth y = 80.01 m**.

    Original diagnosis follows.

    **~~`corridor_blank.sdf` fails to arm~~ — downward LiDAR ray doesn't hit any surface at the drone's spawn point.** `/downward_lidar/range` reads `range: 41.0` (just outside the sensor's valid 0.05–40 m range), so `lidar_bridge.py` correctly drops it as invalid (mirroring a real driver's no-return handling) and `RNGFND1` never receives a single valid sample — arming fails with `"Rangefinder 1: No Data"`. Root cause not yet found; suspect a floor-geometry or spawn-pose mismatch specific to this world (its ground-plane structure differs from `corridor_textured.sdf`'s tiled floor — see "Corridor Worlds" above). **Not fixed — this world cannot currently fly a trial.**
13. **Intermittent loss of the `PARAM_REQUEST_READ`/`PARAM_VALUE` round trip in `fly_trial.py`'s `ensure_params()`** — reproduced 3/3 in one investigation session (`iris_textured.sdf`, not corridor-specific), 0/2 in a follow-up reproduction attempt with `strace -e trace=network` wrapped around `arducopter`, `mavproxy.py`, and `fly_trial.py` (both follow-up attempts succeeded cleanly, round trip <400 ms, no retries needed) — genuinely racy, not yet pinned down. **Ruled out via MAVProxy source, not assumed**: `mavfwd` (gates client→master forwarding) defaults to `True` (`MAVProxy/mavproxy.py`), and `no_fwd_types` (message types MAVProxy won't relay master→outputs) only contains `"BAD_DATA"` (`MAVProxy/modules/mavproxy_link.py`) — neither blocks this message pair by default, so it isn't a static MAVProxy configuration gate. `read_param()` now retries 5× (5 s each) as a mitigation, not a fix — if `ensure_params()` still fails outright after this, the underlying race hasn't been found yet. Worth checking whether this reproduces on the new machine too.

## Conventions

- **Branches:** `master` is the working branch, and all project history is on it.
  `main` is an unrelated root commit that GitHub auto-created (a one-line README). It
  has no common ancestor with `master`, and it is left alone. Workstreams branch from
  `master` (e.g. `fwd-camera`).
- **ATE metric:** cross-estimator results use **evo -a (cruise)**, computed by
  `eval/three_way_eval.py`, which pins the window. See METHODOLOGY's STANDING RULE.
- Use `gz` commands only — Gazebo Harmonic syntax (`gz sim`, `gz topic`)
- Commit to git before any multi-file change
- Do not trust ArduPilot parameter names from memory — check against docs
- Document all frame conventions explicitly (body / camera-optical / world / NED)
- MAVLink injection: `OPTICAL_FLOW` (not `OPTICAL_FLOW_RAD` — unhandled by this ArduPilot build) for flow, `DISTANCE_SENSOR` for LiDAR
- The render-driven optical flow approach is **scientifically load-bearing** for the
  thesis — it enables deliberate control over information degradation

## Current Focus (Phase 1)

Completed:
- Textured Gazebo world (`iris_textured.sdf`) — nominal baseline ✓
- Median + RANSAC outlier rejection — tested, validated ✓
- Optical flow validated: ~145 px/s at 0.5 m/s matches kinematic theory ✓
- ROS2 timestamp sync via `/clock` bridge + `use_sim_time:=true` ✓
- Ground truth bridging: `/ground_truth/pose` verified at 57–227 Hz, sim-time ✓
- Custom `OpticalFlow.msg` + `/optical_flow/measurement` publisher ✓
- Data collection pipeline (`record_trial.sh`) — self-contained trials ✓

Remaining:
0. ~~Enlarge textured world (≥50 m × 50 m) before nominal-condition data collection~~ — **done**: `corridor_textured.sdf`/`corridor_blank.sdf`/`corridor_transition.sdf`, 20 m × 160 m, verified (see "Corridor Worlds — Long-Duration Degraded-Sensing Trials")
1. Raw flow + gyro rate publishing — done (`attitude_bridge.py` + `flow_x_raw`/`flow_y_raw`); manual derotation (`flow_x`/`flow_y`) kept as a characterisation tool only, not gating further work (see [Sensor Fusion Architecture](#sensor-fusion-architecture))
2. Shadow rejection
3. Pixel-to-radian (rad/s) conversion — done (`flow_x_rad`/`flow_y_rad` in `flow_tracker.py`); no altitude scaling needed for this — the rad/s conversion is altitude-independent by design (focal length only)
4. Add downward point LiDAR to `iris_with_standoffs/model.sdf` — done, verified (Stage 1)
5. Inject `DISTANCE_SENSOR` (LiDAR) to ArduPilot via MAVLink — done, verified (Stage 2)
6. Add `/downward_lidar/range` to `record_trial.sh`'s recorded topics — done
7. Inject optical flow to ArduPilot EKF3 via MAVLink `OPTICAL_FLOW` (not `OPTICAL_FLOW_RAD` — unusable in this build) — done, verified (Stage A); GPS still POSXY source, not yet a GNSS-denied config
8. State extraction / `evo` comparison against ground truth — done, verified (Stage B); `ekf_bridge.py` + `evaluate_trial.sh`. ATE RMSE 6.4 mm, RPE RMSE 4.6 mm on a nominal trial — validates the pipeline (frame transform, extraction, tooling), not flow-only accuracy, since GPS is still the position source
9. GNSS-denied config (flow + rangefinder only, no GPS for position) — done, verified (Stage C); `gnss_denied.parm`. **The Stage C ATE figures (7.7 / 10.0 mm) are VOID**: `/ekf/pose` was simulator truth (`AHRS_EKF_TYPE=10`; see the Hidden Configuration Audit). The sensor-level `inlier_ratio` result (0.94 vs 0.47) stands. The compass question is resolved: `gnss_denied_nomag.parm` is the comparison config for all `dsn_*` and forward-camera datasets.
10. Longer-duration GNSS-denied flights — **done**: the 160 m corridor worlds fly full 300 s trials (Known Issues #11/#12 fixed 2026-07-23); the `dsn_*` batch (3 worlds × 3 repeats) is the three-way baseline; the forward-camera ceiling datasets `fwdc_*`/`fwdplainc_*` are recorded (see "Corridor Worlds" and METHODOLOGY).
11. UKF implementation — **built and producing numbers** (`src/estimators/ukf_core.py` + `ukf_replay.py`, Euler 15-state, shared `measurement_models.py`, gated pseudo-yaw matching EKF3's variance-gated `fuseEulerYaw`). Runs on the nomag `dsn_*` batch. See METHODOLOGY.md for the yaw-cap verification and the flow→yaw coupling finding.
12. FGO (GTSAM) implementation — **built and producing numbers** (`src/estimators/fgo/`, `BatchFixedLagSmoother`, window 0.25 s (a declared config choice), LM capped at 2 iterations, shared `h_flow`, custom flow/range/yaw-prior factors, IMU dejitter and gap rule, Phase 4 forward heading/yaw-rate factors; runs in `~/venv-fgo`). Current comparison: see METHODOLOGY (dejittered `dsn` baseline, textured evo -a (cruise) FGO 4.65 vs EKF3 4.66, indistinguishable at n=3). **Step time (DIAGNOSTIC, workstation Python): ~29 ms median on textured bags, ~15 ms transition, ~4 ms blank** (world-dependent). The old "~101 ms/step" was the 1.0 s-window configuration and is superseded. Distance scale over n=9 textured bags: EKF3 +5.7…+9.6 %, FGO +0.9…+1.1 % (the n=1 +12.6 %/+4.7 % is superseded); the scale-cause check is pending. iSAM2 is unusable (a marginalisation cascade with Python `CustomFactor`). See METHODOLOGY and FGO_DESIGN.md.

## Experimental Design Notes

Two independent experimental axes for estimator evaluation:

1. **Sensing degradation** — nominal (textured) vs degraded (blank/low-texture)
   worlds, and transitions between feature-rich and feature-poor regions.
2. **Commanded velocity** — sweep across forward speeds (e.g. 0.25–1.0 m/s).
   Velocity-dependent optical flow error was observed growing across this
   sweep (~+7.8% at 0.25 m/s to ~+12.5% at 1.0 m/s, `analyse_flow_sweep.py`).
   Per supervisor guidance: this is an **expected experimental condition, not
   a defect to fix** — "filters will start to break down at higher speeds,
   that's kinda expected and okay — can be a test case for you." Treat
   velocity as a planned robustness axis alongside texture degradation, not
   an open bug to chase down.

## Not Yet Implemented / Out of Scope

- ROS2 launch files (manual terminal launch for now)
- Startup automation script
- Camera calibration
- Ground velocity estimation
- FGO ROS2 node (`fgo_node.py`) + full validation (fair yaw-anchor, §9 gating checks, window sweep, NEES) — core built & running offline, node + validation pending
- Forward-camera fusion in the estimators (Phase 4, offline UKF/FGO; in progress) — visual odometry beyond heading/yaw rate is out of scope
- Onboard (flight-controller) UKF/FGO as EKF3 drop-in replacements — supervisor direction 2026-09-29, feasibility being investigated
- **All future flights: `LOG_REPLAY=1`, `LOG_DISARMED=1`** (not set in any dataset recorded so far)
- Loop closure detection
- Motion capture (Term 3)
- Real hardware flight

## Reference Documents

- `Thesis_A_Literature_Review1.pdf` — literature review and project plan (research
  question, robustness metrics, timeline)
- `PROGRESS.md` — running progress log; update at the end of every work session
  before closing the terminal. Paste into claude.ai Project for planning sessions.
  
  A trial is: drone takes off from origin in a specified world, flies forward at a specified velocity for a specified duration, lands. We record ground truth pose, all sensor outputs, and ArduPilot EKF state throughout. Outputs: one self-contained directory per trial.
