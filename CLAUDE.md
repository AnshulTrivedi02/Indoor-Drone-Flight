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
| Evaluation    | `evo` (planned) for ATE / RPE                                  |
| Language      | Australian English in all comments, docs, and prose            |

## Key Paths

| Item                        | Path                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| ArduPilot SITL              | `~/ardupilot`                                                        |
| Gazebo plugin / models      | `~/ardupilot_gazebo`                                                 |
| Worlds                      | `~/ardupilot_gazebo/worlds/`                                         |
| **Degraded world (blank)**  | `~/ardupilot_gazebo/worlds/iris_runway.sdf`                          |
| **Nominal world (textured)**| `~/ardupilot_gazebo/worlds/iris_textured.sdf`                        |
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
| **Trial recorder**          | `~/thesis_ws/record_trial.sh`                                        |
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

**Not yet done / follow-ups found during this work, not fixed (flagged for
you to decide on):**
- `record_trial.sh` doesn't source `~/thesis_ws/install/setup.bash`, so
  `ros2 bag record` can't resolve the custom `optical_flow_interfaces`
  package and silently **drops `/optical_flow/measurement` from the
  bag** (`rosbag2_recorder` logs a `WARN` but still records everything
  else). Not fixed as part of Stage A — flagging for a decision.
- State extraction / `evo` comparison against ground truth — explicitly
  out of scope until you confirm this fusion result.

## Sensor Fusion Architecture

Design decision (per supervisor guidance, 2026-07-02): **each estimator
consumes raw sensor data and performs its own rotation compensation
internally**, rather than all three being fed an identically pre-processed
input.

- **Common raw inputs across all estimators:** raw optical flow
  (`flow_x_raw`/`flow_y_raw`), raw gyro/IMU angular rates
  (`/attitude/angular_rates`, and IMU generally), and downward-rangefinder
  distance (`/downward_lidar/range`, injected into ArduPilot as `RNGFND1`
  via MAVLink `DISTANCE_SENSOR` by `lidar_bridge.py`; the FGO will consume
  the same ROS topic directly).
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

## Launch Sequence

Run each terminal in order. Source commands are mandatory before ROS2 tools.

### Preferred: use launch scripts

```bash
# Degraded baseline (blank floor)
./start_sim.sh

# Nominal baseline (textured checkerboard floor)
./start_sim.sh iris_textured.sdf

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
  --add-param-file $HOME/thesis_ws/lidar_rangefinder.parm \
  --add-param-file $HOME/thesis_ws/flow_ekf.parm \
  --no-rebuild
```

The extra `--out 127.0.0.1:14551` gives `attitude_bridge.py` (Terminal 7) its
own dedicated MAVLink output, `--out 127.0.0.1:14552` gives `lidar_bridge.py`
(Terminal 8) its own, and `--out 127.0.0.1:14553` gives `flow_bridge.py`
(Terminal 9) its own — separate from the default `14550` that
`fly_forward.py` connects to — pymavlink's plain `udp:` scheme binds and
listens, so no two processes can share one port. `--add-param-file` (passed
twice, `action="append"` in `sim_vehicle.py`) appends `lidar_rangefinder.parm`
then `flow_ekf.parm` after the frame's own defaults
(`copter.parm,gazebo-iris.parm`), so their values win over `gazebo-iris.parm`'s
Analog/SIM_SONAR-based RNGFND1 block (`--add-param-file` appends to the end of
the `--defaults` comma list, and later files override earlier ones for
duplicate params).

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

### Terminal 10 — Bag Recording (one trial)

```bash
cd ~/thesis_ws
./record_trial.sh test_001 --world iris_textured --velocity 0.5 --altitude 2.0 --notes "first clean trial"
# Ctrl+C to stop recording; script then copies the ArduPilot .BIN log automatically.

# Inspect the result:
ros2 bag info ~/thesis_data/trials/test_001/bag/
cat ~/thesis_data/trials/test_001/metadata.yaml
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

Topics recorded by default: `/clock`, `/ground_truth/pose`,
`/downward_lidar/range`, `/attitude/angular_rates`, `/optical_flow/measurement`
(plus any topic matching `^/(flow|optical_flow)` found on the bus at startup).

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
4. **`record_trial.sh` silently drops `/optical_flow/measurement` from bags** — doesn't source `~/thesis_ws/install/setup.bash`, so `ros2 bag record` can't resolve the custom `optical_flow_interfaces` package for that topic (found during EKF3 flow fusion Stage A verification; not fixed, flagged for a decision).
5. **Downward LiDAR RNGFND1 dropouts under aggressive attitude changes** — ~3% of readings during a dynamic climb briefly read near-zero instead of true altitude (steady hover is sub-cm accurate). Currently harmless since `EK3_RNG_USE_HGT=-1` keeps RNGFND1 out of the EKF's height estimate by default — see "Downward LiDAR — Stage 2" above. Revisit before ever enabling range-based height switching or surface tracking.
6. **Textured world too small** — 20 m × 20 m checkerboard; drone exits the mat during forward-flight trials, contaminating "nominal" recordings with feature-poor segments. Need ≥50 m × 50 m plane before collecting valid nominal-condition data.
7. **Feature count is a deceptive quality metric** — ~100 features reported even on featureless off-mat texture. Use `inlier_ratio` (RANSAC survivors / pre-RANSAC tracked) as the real flow-quality indicator.
8. **TFMessage bridge broken** — `gz.msgs.Pose_V → tf2_msgs/TFMessage` in ros_gz_bridge 1.0.22 zeroes all stamps and clears all frame IDs. **Do not use it for ground truth** — see Ground Truth Bridging section above.
9. **Real-time factor is low on this machine** — measured RTF ≈ 0.05–0.17 (`gz topic -e -t /stats`), even headless with no GUI/ArduPilot attached. All sensor `update_rate` values are sim-time periods, so the wall-clock publish rate seen by `ros2 topic hz` is roughly `update_rate × RTF` — e.g. the downward LiDAR's configured 30 Hz currently yields only ~3.6–4 Hz wall-clock, even though its true sim-time rate (header-stamp deltas) is a correct 30.3 Hz. This affects every sensor topic, not just the LiDAR; when checking whether a sensor is "running at the right rate," check sim-time stamp spacing, not `ros2 topic hz`, which conflates the two. **Also affects scripted flight tests directly** — a `time.sleep(N)`-based flight script only buys ~N×RTF seconds of sim time; gate test phases on measured state (altitude, position) instead, see "Downward Optical Flow — EKF3 Fusion (Stage A)" above. Also relevant when planning trial durations (wall-clock trial time will be much longer than the simulated flight time it captures).
10. **SITL's persisted `eeprom.bin` can silently defeat `--add-param-file`** — once a param has any explicitly-stored value in `~/ardupilot/ArduCopter/eeprom.bin` (gitignored, persists across SITL sessions), `AP_Param::configured_in_storage()` means `--defaults`/`--add-param-file` no longer override it. Fix with a live `PARAM_SET` + `MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN` (soft in-process reboot, no relaunch needed) rather than deleting the eeprom file. See "Downward Optical Flow — EKF3 Fusion (Stage A)" above for how this was found (`FLOW_TYPE` silently stuck at `10` instead of the `5` in `flow_ekf.parm`).

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
0. Enlarge textured world (≥50 m × 50 m) before nominal-condition data collection
1. Raw flow + gyro rate publishing — done (`attitude_bridge.py` + `flow_x_raw`/`flow_y_raw`); manual derotation (`flow_x`/`flow_y`) kept as a characterisation tool only, not gating further work (see [Sensor Fusion Architecture](#sensor-fusion-architecture))
2. Shadow rejection
3. Pixel-to-radian (rad/s) conversion — done (`flow_x_rad`/`flow_y_rad` in `flow_tracker.py`); no altitude scaling needed for this — the rad/s conversion is altitude-independent by design (focal length only)
4. Add downward point LiDAR to `iris_with_standoffs/model.sdf` — done, verified (Stage 1)
5. Inject `DISTANCE_SENSOR` (LiDAR) to ArduPilot via MAVLink — done, verified (Stage 2)
6. Add `/downward_lidar/range` to `record_trial.sh`'s recorded topics — done
7. Inject optical flow to ArduPilot EKF3 via MAVLink `OPTICAL_FLOW` (not `OPTICAL_FLOW_RAD` — unusable in this build) — done, verified (Stage A); GPS still POSXY source, not yet a GNSS-denied config
8. State extraction / `evo` comparison against ground truth — not started, out of scope until Stage A fusion result is confirmed

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
