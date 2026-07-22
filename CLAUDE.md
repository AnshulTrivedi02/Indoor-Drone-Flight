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
| Gazebo plugin / models      | `~/ardupilot_gazebo`                                                 |
| Worlds                      | `~/ardupilot_gazebo/worlds/`                                         |
| **Degraded world (blank)**  | `~/ardupilot_gazebo/worlds/iris_runway.sdf`                          |
| **Nominal world (textured)**| `~/ardupilot_gazebo/worlds/iris_textured.sdf`                        |
| **Corridor world (nominal)**    | `~/ardupilot_gazebo/worlds/corridor_textured.sdf`                 |
| **Corridor world (degraded)**   | `~/ardupilot_gazebo/worlds/corridor_blank.sdf`                    |
| **Corridor world (transition)** | `~/ardupilot_gazebo/worlds/corridor_transition.sdf`               |
| Drone SDF (primary edit)    | `~/ardupilot_gazebo/models/iris_with_standoffs/model.sdf`            |
| ROS2 workspace              | `~/thesis_ws`                                                        |
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
| **No-yaw test params (throwaway, not the baseline)** | `~/thesis_ws/gnss_denied_nomag.parm`               |
| **EKF pose bridge**         | `~/thesis_ws/ekf_bridge.py`                                          |
| **IMU bridge**               | `~/thesis_ws/imu_bridge.py`                                          |
| **evo venv**                 | `~/venv-evo`                                                         |
| **Trial recorder**          | `~/thesis_ws/record_trial.sh`                                        |
| **Trial evaluator**         | `~/thesis_ws/evaluate_trial.sh`                                      |
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

`iris_textured.sdf`'s 20 m x 20 m checkerboard is too small for a full
60-120 s forward-flight trial — the drone exits the mat mid-flight,
contaminating "nominal" recordings with feature-poor segments (see Known
Issues). It's also too short for dead-reckoning drift to accumulate: Stage
C's ~40 s flights showed only a modest ATE gap between textured and blank
floors despite a stark `inlier_ratio` collapse at the sensor level —
position error hadn't yet caught up to the sensor degradation over that
short a flight.

Three corridor worlds in `~/ardupilot_gazebo/worlds/` address both
problems, built from one shared template so **floor texture is the only
variable** — dimensions, walls, lighting, and spawn are identical:

- **Corridor geometry**: 20 m wide (x: −10..10 m), **160 m long**
  (y: 0..160 m) — comfortably over the ≥100 m minimum needed for a
  60-120 s cruise at 0.5-1.0 m/s (30-120 m) plus climb/stop margin.
  Corridor runs along world **+Y** — the drone's spawn yaw (90°, see
  below) points +Y, matching ArduPilot's internal yaw=0 (NED-North), which
  is the direction `fly_forward.py`/`fly_trial.py` fly.
- **Walls**: two static boxes at x=±10 m (model `corridor_wall`,
  `~/ardupilot_gazebo/models/corridor_wall/`), 5 m tall, 0.2 m thick,
  spanning y:−5..165 m. Plain grey, identical in all three worlds — the
  downward camera only looks straight down, so the walls never enter its
  FOV and can't confound the floor comparison.
- **Lighting**: the same directional sun as `iris_textured.sdf`, copied
  verbatim. A directional light has no falloff, so it's uniform along the
  whole corridor by construction — no illumination gradient to confound
  with the texture variable.
- **Spawn**: `iris_with_ardupilot` at `(0, 0, 0.195)`, yaw 90°, identical
  across all three and identical to `iris_textured.sdf`/`iris_runway.sdf`.

**`corridor_textured.sdf`** (nominal): 8x unmodified `textured_ground`
tiles (the same 20x20 m checker model `iris_textured.sdf` already uses)
tiled along Y, giving a seamless 20x160 m checkerboard for the full
corridor. Reusing the existing tile unmodified avoids a UV-scaling trap —
Gazebo/Ogre2 stretches one texture image across a plane's *whole* extent
rather than repeating it per metre, so a single 20x160 m plane with
`checker.png` stretched over it would wash out into a handful of huge
squares, losing exactly the fine-grained features needed. Tiling the
already-validated 20x20 m tile sidesteps that entirely.

**`corridor_blank.sdf`** (degraded): a single flat 20x160 m plane,
`blank_floor`, using the *exact same* ambient/diffuse/specular/roughness/
metalness values as `textured_ground`'s material but with no
`albedo_map` — flat grey, featureless. This isolates texture as the only
difference from `corridor_textured.sdf`, not colour or reflectance.

**`corridor_transition.sdf`** (the primary research gap): textured for
y:0-80 m (4x `textured_ground` tiles), blank for y:80-160 m (one
`blank_floor_half` plane, same material as `corridor_blank.sdf`).
**Boundary is exactly y = 80 m** (corridor midpoint) — record
`/ground_truth/pose` y at the point of boundary crossing when analysing
flight data from this world, to correlate estimator behaviour with the
sensing-quality transition.

**Verified** (gz sim headless, `ros_gz_bridge`, `flow_tracker`, drone
teleported to altitude via `gz service .../set_pose` + a paused
`multi_step` — the drone's rest pose sits below the floor plane at spawn
height, `z=0.195` vs. camera offset `−0.25 m`, so a frame grabbed at rest
shows sky, not floor, in every one of these worlds, same as
`iris_textured.sdf`; this is a pre-existing artefact of the spawn/camera
geometry, not something the corridor worlds introduced):
- Spawn pose and `/world/<world_name>/dynamic_pose/info` ground truth
  match exactly in all three worlds (note the topic's world-name segment
  changes with the world, e.g. `/world/corridor_textured/dynamic_pose/info`).
- Downward camera renders the intended floor in all three: full
  checkerboard in `corridor_textured`, flat uniform grey in
  `corridor_blank`, and a sharp textured/blank boundary exactly at the
  frame centre when the drone is positioned at y=80 in
  `corridor_transition`.
- `flow_tracker`'s `feature_count` confirms the sensor-level contrast
  numerically: ~126-183 over the textured floor vs. ~15-24 (collapsing to
  0 under fast motion) over the blank floor — an even starker gap than
  Stage C's original 85-vs-54 mean, as expected from a deliberately fully
  flat (no markings at all) blank floor.

**Launch**: `./start_sim.sh corridor_textured.sdf` (or `corridor_blank.sdf`
/ `corridor_transition.sdf`) — `start_sim.sh` accepts any world filename
in `~/ardupilot_gazebo/worlds/`, validates it exists first (listing valid
options on a typo), and substitutes it into both the Gazebo launch and the
ROS2 bridge's `dynamic_pose/info` topic name automatically. Manual launch
(Terminal 1/3) works the same way — just substitute the world name.

**Not yet flown end-to-end via `run_trial.sh`/`fly_trial.py` reliably for
either `corridor_textured.sdf` or `corridor_blank.sdf` as of this writing**
— the "Verified" checks above are all Gazebo-level (spawn pose, rendering,
`flow_tracker` feature counts), not a full arm/climb/cruise/land trial.
Attempting one surfaced two real, unresolved problems — see Known Issues
#11 and #12 below:
- `corridor_textured.sdf` hits a Gazebo↔SITL JSON lockstep stall (Known
  Issue #11), traced to `gz sim server` saturating a full CPU core trying
  to simulate this world's heavier geometry (2 walls + 8 floor tiles) on
  this machine — confirmed in both headless (`run_trial.sh`) and GUI-mode
  (`start_sim.sh`) launches, so it isn't a headless-vs-GUI difference. This
  is very plausibly this machine-specific (see Known Issue #9's RTF
  problems) rather than a bug in the world file itself — worth re-testing
  once the machine migration is done, watching `gz sim server`'s CPU% and
  whether MAVProxy's link stays stable through an arm attempt.
- `corridor_blank.sdf` additionally fails to arm outright — a separate,
  unrelated bug: the downward LiDAR never returns a valid reading at the
  spawn point (Known Issue #12). **Not usable for a real trial until this
  is fixed**, independent of the CPU/performance question above.
- `corridor_textured.sdf` has completed a full short trial successfully at
  least once with `run_trial.sh`'s 240 s cap in place, but has not been
  reliably reproducible — expect intermittent hard failures on this
  machine until the CPU-saturation root cause is addressed (i.e. likely
  not until the migration).

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
| Forward camera  | Deferred          | Pending supervisor discussion                                |

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
- **RPE**: textured RMSE 5.4 mm vs blank RMSE 6.5 mm — same modest-not-dramatic pattern.
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
`sensor_msgs/Imu` on `/imu/data_raw`, on its own dedicated MAVLink port
(`14555`, after `ekf_bridge.py`'s `14554`). This is the raw sensor no prior
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

**Rate: 50 Hz**, requested via `MAV_CMD_SET_MESSAGE_INTERVAL`, matching
`attitude_bridge.py`'s `ATTITUDE` rate — with the same periodic-reassert
timer (every 2 s) to counter MAVProxy silently overriding it with its own
low default (see Known Issues). Verified against a recorded bag: mean/median
inter-message gap **20.00 ms → 50.0 Hz achieved**, not just requested.

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

## UKF Design (confirmed, not yet implemented)

Design-first pass completed and confirmed before any filter code was
written — this section records the confirmed decisions so implementation
can resume without re-deriving them. **No UKF code exists yet** — the next
step is a constant-velocity scaffold (plumbing only, not a thesis result)
to validate multi-rate handling/gating/frames/publishing against existing
recorded bags, then the real IMU-driven deliverable.

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
EKF3's own predict step runs at `SCHED_LOOP_RATE` — confirmed **400 Hz**
by reading it directly from a trial's own dataflash `PARM` dump, not
assumed — while the UKF's predict step is capped at `/imu/data_raw`'s
50 Hz. Copying these parameter values unchanged silently assumes equal
`dt`, which is off by 8×. The dt-invariant quantity that should actually
match is accumulated variance *per second* (`dt^(2k-1) · NSE²` for a
`(dt^k · NSE)²` per-step term), giving `NSE_UKF = NSE_EKF3 ·
(dt_EKF3/dt_UKF)^(k−0.5)`:

| Param | EKF3 value | k | Scale factor | Value at 50 Hz |
|---|---|---|---|---|
| `GYRO_P_NSE` | 0.015 rad/s | 1 | ×0.3536 | 0.0053 rad/s |
| `ACC_P_NSE` | 0.35 m/s² | 1 | ×0.3536 | 0.124 m/s² |
| `GBIAS_P_NSE` | 0.001 rad/s/s | 2 | ×0.0442 | 4.42×10⁻⁵ rad/s/s |
| `ABIAS_P_NSE` | 0.02 m/s/s/s | 2 | ×0.0442 | 8.84×10⁻⁴ m/s/s/s |

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

**Fix found and verified working — NOT applied to `gnss_denied.parm`,
lives only in the throwaway `gnss_denied_nomag.parm` pending a decision**:
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

**Long-flight result (320 s, `iris_textured.sdf`, 0.4 m/s cruise —
corridor worlds weren't usable yet, see Known Issues #11/#12): yaw error
vs `/ground_truth/pose` stayed essentially zero the whole flight** (±0.03°
max, linear-fit drift rate ≈0.000 deg/min, R²≈0). **This is not evidence
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
  --out 127.0.0.1:14555 \
  --add-param-file $HOME/thesis_ws/lidar_rangefinder.parm \
  --add-param-file $HOME/thesis_ws/flow_ekf.parm \
  --add-param-file $HOME/thesis_ws/gnss_denied.parm \
  --no-rebuild
```

The extra `--out 127.0.0.1:14551` gives `attitude_bridge.py` (Terminal 7) its
own dedicated MAVLink output, `--out 127.0.0.1:14552` gives `lidar_bridge.py`
(Terminal 8) its own, `--out 127.0.0.1:14553` gives `flow_bridge.py`
(Terminal 9) its own, `--out 127.0.0.1:14554` gives `ekf_bridge.py`
(Terminal 10) its own, and `--out 127.0.0.1:14555` gives `imu_bridge.py`
(Terminal 11) its own — separate from the default `14550` that
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
ROS2 as `/imu/data_raw` (`sensor_msgs/Imu`, FLU — see "IMU Bridge" above),
on its own dedicated port (`14555`). Run after SITL (Terminal 2) is up and
streaming on `14555`.

```bash
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/imu_bridge.py --ros-args -p use_sim_time:=true
```

Verify:
```bash
ros2 topic hz /imu/data_raw           # expect ~50 Hz sim-time
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
6. **Textured world too small** — 20 m × 20 m checkerboard; drone exits the mat during forward-flight trials, contaminating "nominal" recordings with feature-poor segments. Need ≥50 m × 50 m plane before collecting valid nominal-condition data.
7. **Feature count is a deceptive quality metric** — ~100 features reported even on featureless off-mat texture. Use `inlier_ratio` (RANSAC survivors / pre-RANSAC tracked) as the real flow-quality indicator.
8. **TFMessage bridge broken** — `gz.msgs.Pose_V → tf2_msgs/TFMessage` in ros_gz_bridge 1.0.22 zeroes all stamps and clears all frame IDs. **Do not use it for ground truth** — see Ground Truth Bridging section above.
9. **Real-time factor is low on this machine** — measured RTF ≈ 0.05–0.17 (`gz topic -e -t /stats`), even headless with no GUI/ArduPilot attached. All sensor `update_rate` values are sim-time periods, so the wall-clock publish rate seen by `ros2 topic hz` is roughly `update_rate × RTF` — e.g. the downward LiDAR's configured 30 Hz currently yields only ~3.6–4 Hz wall-clock, even though its true sim-time rate (header-stamp deltas) is a correct 30.3 Hz. This affects every sensor topic, not just the LiDAR; when checking whether a sensor is "running at the right rate," check sim-time stamp spacing, not `ros2 topic hz`, which conflates the two. **Also affects scripted flight tests directly** — a `time.sleep(N)`-based flight script only buys ~N×RTF seconds of sim time; gate test phases on measured state (altitude, position) instead, see "Downward Optical Flow — EKF3 Fusion (Stage A)" above. Also relevant when planning trial durations (wall-clock trial time will be much longer than the simulated flight time it captures). **This is the reason the workstation is being migrated to a second Ubuntu 24 machine** — ROS2/Gazebo/ArduPilot still need setting up there; until that's done, this machine remains the working environment.
10. **SITL's persisted `eeprom.bin` can silently defeat `--add-param-file`** — once a param has any explicitly-stored value in `~/ardupilot/ArduCopter/eeprom.bin` (gitignored, persists across SITL sessions), `AP_Param::configured_in_storage()` means `--defaults`/`--add-param-file` no longer override it. Fix with a live `PARAM_SET` + `MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN` (soft in-process reboot, no relaunch needed) rather than deleting the eeprom file. See "Downward Optical Flow — EKF3 Fusion (Stage A)" above for how this was found (`FLOW_TYPE` silently stuck at `10` instead of the `5` in `flow_ekf.parm`).
11. **Gazebo↔SITL JSON lockstep stalls on `corridor_textured.sdf` — root cause found: Gazebo's server process can't keep up with the world's simulation load on this machine.** Chain of evidence, each link independently confirmed rather than assumed:
    - `gdb` attached to `arducopter` showed SITL's main thread blocking in `SITL::JSON::recv_fdm()`, waiting on Gazebo's next physics packet; `arducopter.log` shows "No JSON sensor message received, resending servos" during the stall; it self-heals once Gazebo's `ArduPilotPlugin` hits its own timeout (`connectionTimeoutMaxCount`) and resets ("ArduPilot controller has reset" in `gazebo.log`).
    - Initially misdiagnosed as slow **loading** (more `textured_ground` tiles taking longer to load) — wrong: all worlds finish *loading* in ~5–6 s regardless.
    - Ruled out headless-vs-GUI as the cause: reproduced the identical `"no link"`/`"link 1 down"`/`"link 1 OK"` flapping in MAVProxy's console, plus a *new*, more basic prearm rejection (`"AP: Arm: System not initialised"`, alongside the previously-seen `"Accels inconsistent"`), running `corridor_textured.sdf` manually via `start_sim.sh` **with the Gazebo GUI**, not just headless via `run_trial.sh`.
    - **The actual cause**: `ps aux` during that manual GUI run showed the `gz sim server` process pegged at **102% CPU** — saturating a full core — confirmed in both headless and GUI-mode runs. `corridor_textured.sdf` (20×160 m, 2 wall boxes + 8 floor tiles) is a genuinely heavier world to simulate *every tick*, not just to load, than `iris_textured.sdf` (single small 20×20 m plane). On a machine already known to struggle holding real-time factor even on the light world (see Known Issue #9), the heavier corridor world's steady-state CPU cost appears to push Gazebo below the responsiveness the JSON lockstep interface needs — explaining the blocking, the resets, the link flapping, and the cascading param-read/arm failures as one unified mechanism, not several unrelated bugs.
    - The ~100% figure is on essentially **one core**, not spread across several — the bottleneck looks single-thread/single-core-bound, not something "more cores" alone would fix.
    - `--default-modules` (excluding MAVProxy's own `param` module, which auto-downloads the full parameter set on connect and was found flooding the same link) measurably reduces failure severity — confirmed via `strace`: traffic dropped ~72% (1692 → 461 `sendto` calls), and it changed hard first-attempt failures into recoverable-with-retries — but it is **not a fix**, since it doesn't address the underlying CPU bottleneck. A run with it applied still stalled indefinitely at arming with the same `"Accels inconsistent"`/link-flapping pattern.
    - **Prediction for the machine migration**: this should improve on a faster machine, but specifically needs better *single-core* performance, not just a newer/multi-core CPU — re-test `corridor_textured.sdf` directly (watch `gz sim server`'s CPU% and whether "no link" recurs) as an early validation once the new machine is set up, rather than assuming it's resolved.
    - **Open tension, not fully reconciled**: an earlier report (from a separate investigation session) claimed this stall "reproduces identically on `iris_textured.sdf`" too — that was never independently re-confirmed under a live CPU-saturation check the way the corridor-world case now has been, and doesn't sit easily next to `iris_textured.sdf`'s otherwise consistent reliability across dozens of trials this project. Possibly that observation was a different, more transient phenomenon (a single early connection-reset event, which can happen briefly on any world and normally self-heals in seconds) rather than the same sustained, CPU-bound flapping documented here for the corridor world. Not resolved — flagging honestly rather than forcing a tidy story.
12. **`corridor_blank.sdf` fails to arm — downward LiDAR ray doesn't hit any surface at the drone's spawn point.** `/downward_lidar/range` reads `range: 41.0` (just outside the sensor's valid 0.05–40 m range), so `lidar_bridge.py` correctly drops it as invalid (mirroring a real driver's no-return handling) and `RNGFND1` never receives a single valid sample — arming fails with `"Rangefinder 1: No Data"`. Root cause not yet found; suspect a floor-geometry or spawn-pose mismatch specific to this world (its ground-plane structure differs from `corridor_textured.sdf`'s tiled floor — see "Corridor Worlds" above). **Not fixed — this world cannot currently fly a trial.**
13. **Intermittent loss of the `PARAM_REQUEST_READ`/`PARAM_VALUE` round trip in `fly_trial.py`'s `ensure_params()`** — reproduced 3/3 in one investigation session (`iris_textured.sdf`, not corridor-specific), 0/2 in a follow-up reproduction attempt with `strace -e trace=network` wrapped around `arducopter`, `mavproxy.py`, and `fly_trial.py` (both follow-up attempts succeeded cleanly, round trip <400 ms, no retries needed) — genuinely racy, not yet pinned down. **Ruled out via MAVProxy source, not assumed**: `mavfwd` (gates client→master forwarding) defaults to `True` (`MAVProxy/mavproxy.py`), and `no_fwd_types` (message types MAVProxy won't relay master→outputs) only contains `"BAD_DATA"` (`MAVProxy/modules/mavproxy_link.py`) — neither blocks this message pair by default, so it isn't a static MAVProxy configuration gate. `read_param()` now retries 5× (5 s each) as a mitigation, not a fix — if `ensure_params()` still fails outright after this, the underlying race hasn't been found yet. Worth checking whether this reproduces on the new machine too.

## Conventions

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
9. GNSS-denied config (flow + rangefinder only, no GPS for position) — done, verified (Stage C); `gnss_denied.parm`, the standing baseline for UKF/FGO too. Textured floor ATE RMSE 7.7 mm vs blank floor 10.0 mm — a modest gap, but `inlier_ratio` (0.94 vs 0.47 mean) confirms the expected sharp sensor-level texture-quality difference; EKF stayed stable in both, no rejection, no divergence. **Revisit**: `gnss_denied.parm` still lets EKF3 fuse the compass for yaw — outside the thesis's stated sensor suite and a confound vs UKF/FGO's no-yaw setup; a verified fix exists (`gnss_denied_nomag.parm`) but hasn't been folded into the standing baseline — see "No-Yaw / Compass-Denied Investigation" above
10. Longer-duration / more aggressive GNSS-denied flight test, to see whether blank-floor drift accumulates more starkly over time than the ~40 s Stage C flights showed — corridor worlds built for this but not yet usable end-to-end (`corridor_textured.sdf`/`corridor_blank.sdf` both hit unresolved issues when actually flown, see Known Issues #11/#12). A 320 s no-yaw flight was run on `iris_textured.sdf` instead (see "No-Yaw / Compass-Denied Investigation" above) — real corridor data still pending
11. UKF implementation — **design confirmed** (state vector, process/measurement models, matched robustness params, Q derivation, position reference, covariance logging, validation plan — see "UKF Design" above), **no code written yet**. Next step: constant-velocity scaffold (plumbing only) against existing bags
12. FGO (GTSAM) implementation, using the `gnss_denied.parm` baseline config — not started

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
- ArduPilot EKF fusion of custom flow + range
- `evo` evaluation harness
- GTSAM / FGO implementation
- Forward-facing camera / visual odometry
- Loop closure detection
- Motion capture (Term 3)
- Real hardware flight

## Reference Documents

- `Thesis_A_Literature_Review1.pdf` — literature review and project plan (research
  question, robustness metrics, timeline)
- `PROGRESS.md` — running progress log; update at the end of every work session
  before closing the terminal. Paste into claude.ai Project for planning sessions.
  
  A trial is: drone takes off from origin in a specified world, flies forward at a specified velocity for a specified duration, lands. We record ground truth pose, all sensor outputs, and ArduPilot EKF state throughout. Outputs: one self-contained directory per trial.
