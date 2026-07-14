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
| Optical flow    | Working — publishing | Publishes `/optical_flow/measurement` (`optical_flow_interfaces/OpticalFlow`). RANSAC tested; ~145 px/s at 0.5 m/s matches theory. `flow_x_raw`/`flow_y_raw` are the **production values** — raw, un-derotated flow, which is what ArduPilot EKF3 and the FGO consume (see [Sensor Fusion Architecture](#sensor-fusion-architecture)). `flow_x`/`flow_y` are a manual derotation (`enable_derotation` param, default on) kept for **characterisation only**, not fed to any estimator. `flow_x_rad`/`flow_y_rad` still zero pending rad/s conversion. Needs shadow rejection |
| Downward LiDAR  | Stage 1 done — SDF sensor + ROS bridge, verified | Single-beam `gpu_lidar` in `iris_with_standoffs/model.sdf`, mounted at **z = −0.12 m** relative to `base_link` origin, pointing straight down. Emits `gz.msgs.LaserScan` on gz topic `/downward_lidar/range`, bridged to ROS2 as `sensor_msgs/msg/Range` on the same topic name. Range 0.05–40 m. Verified against `/ground_truth/pose` z during a 2 m hover: sub-millimetre accuracy (383/383 samples within 5 cm, mean error 0.1 mm) once settled. `min_angle`/`max_angle` **must both be exactly 0** for a 1-sample axis — Ogre2GpuRays warns and silently ignores `max_angle` otherwise, and an earlier attempt at a small nonzero FOV was a red herring; the real fix for transient short-range noise was moving the mount from −0.05 m to −0.12 m to clear the airframe's own belly mesh (a ray originating too close to the body can graze it under small attitude jitter). `update_rate` is **30 Hz**, matching the camera/flow rate (kept at 30, not raised — see below). **The sim's real-time factor (RTF) is the actual rate bottleneck, not `update_rate`**: this machine runs the model at RTF ≈ 0.05–0.17 (measured via `gz topic -e -t /stats`), even standalone/headless with no GUI or ArduPilot attached, so the *wall-clock* topic rate (what `ros2 topic hz` reports) is roughly `update_rate × RTF` — measured ~3.6–4 Hz at 30 Hz configured, which is what looked like a "slow LiDAR" but is really just RTF. The sensor's **true sim-time rate is correct**: consecutive `sensor_msgs/Range` header stamps on `/downward_lidar/range` are spaced exactly 33.00 ms apart (100-sample check), i.e. genuine 30.3 Hz in simulated time, independent of wall-clock slowdown. Bumping `update_rate` higher (tried 50 Hz) does raise the wall-clock rate roughly proportionally, but doesn't fix the underlying RTF and wasn't kept — 30 Hz matches the camera/flow cadence, which is what actually matters for fusion. When reasoning about any sensor's "Hz" in this project, use sim-time (header-stamp deltas), not wall-clock `topic hz`, unless wall-clock behaviour specifically is what's being investigated. Stage 2 (MAVLink `DISTANCE_SENSOR` injection, not `SIM_SONAR`) not yet started. |
| Forward camera  | Deferred          | Pending supervisor discussion                                |

## Sensor Fusion Architecture

Design decision (per supervisor guidance, 2026-07-02): **each estimator
consumes raw sensor data and performs its own rotation compensation
internally**, rather than all three being fed an identically pre-processed
input.

- **Common raw inputs across all estimators:** raw optical flow
  (`flow_x_raw`/`flow_y_raw`) and raw gyro/IMU angular rates
  (`/attitude/angular_rates`, and IMU generally).
- **ArduPilot EKF3 is the fixed baseline.** It is set up exactly as
  ArduPilot intends — native `OPTICAL_FLOW_RAD` inputs (raw flow + gyro
  integration fields) — and derotates internally. No shortcuts, no
  pre-processing on our side.
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
  --no-rebuild
```

The extra `--out 127.0.0.1:14551` gives `attitude_bridge.py` (Terminal 8) its
own dedicated MAVLink output, separate from the default `14550` that
`fly_forward.py` connects to — pymavlink's plain `udp:` scheme binds and
listens, so two processes cannot share one port.

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

### Terminal 8 — Bag Recording (one trial)

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

1. **Manual derotation is a characterisation tool, not a blocker** — `attitude_bridge.py` publishes body rates on `/attitude/angular_rates`; `flow_tracker.py` subtracts rotational flow (`enable_derotation` param, default on) and publishes both `flow_x`/`flow_y` (derotated, characterisation-only) and `flow_x_raw`/`flow_y_raw` (raw, the production values) in `OpticalFlow.msg` — see [Sensor Fusion Architecture](#sensor-fusion-architecture). Isolated pure-rotation hover testing (yaw done, pitch/roll not) found only a partial 5–15% collapse, confounded by a persistent ~0.4 rad/s background sim vibration present even at idle hover. **This is deprioritised/deferred indefinitely** — it was only relevant to validating a production derotation path that is no longer needed; ArduPilot EKF3 derotates internally from raw flow + gyro, and the FGO will do its own rotation compensation in its flow factor. `flow_x_rad`/`flow_y_rad` remain zero until pixel-to-radian conversion is implemented.
2. **Drone shadow** contaminates downward optical flow (biases toward zero)
3. **Timestamp sync** between Gazebo sim time, ROS time, and ArduPilot: sim time resolved via `/clock` bridge + `use_sim_time:=true`; ArduPilot-to-ROS sync not yet done
4. **Pixel-to-radian conversion** not implemented — needed for `OPTICAL_FLOW_RAD`; focal length confirmed 554 px
5. **Downward LiDAR MAVLink injection not yet done** — sensor + ROS bridge verified (Stage 1); still needed for metric scale and ArduPilot EKF fusion (Stage 2)
6. **Textured world too small** — 20 m × 20 m checkerboard; drone exits the mat during forward-flight trials, contaminating "nominal" recordings with feature-poor segments. Need ≥50 m × 50 m plane before collecting valid nominal-condition data.
7. **Feature count is a deceptive quality metric** — ~100 features reported even on featureless off-mat texture. Use `inlier_ratio` (RANSAC survivors / pre-RANSAC tracked) as the real flow-quality indicator.
8. **TFMessage bridge broken** — `gz.msgs.Pose_V → tf2_msgs/TFMessage` in ros_gz_bridge 1.0.22 zeroes all stamps and clears all frame IDs. **Do not use it for ground truth** — see Ground Truth Bridging section above.
9. **Real-time factor is low on this machine** — measured RTF ≈ 0.05–0.17 (`gz topic -e -t /stats`), even headless with no GUI/ArduPilot attached. All sensor `update_rate` values are sim-time periods, so the wall-clock publish rate seen by `ros2 topic hz` is roughly `update_rate × RTF` — e.g. the downward LiDAR's configured 30 Hz currently yields only ~3.6–4 Hz wall-clock, even though its true sim-time rate (header-stamp deltas) is a correct 30.3 Hz. This affects every sensor topic, not just the LiDAR; when checking whether a sensor is "running at the right rate," check sim-time stamp spacing, not `ros2 topic hz`, which conflates the two. Also relevant when planning trial durations (wall-clock trial time will be much longer than the simulated flight time it captures).

## Conventions

- Use `gz` commands only — Gazebo Harmonic syntax (`gz sim`, `gz topic`)
- Commit to git before any multi-file change
- Do not trust ArduPilot parameter names from memory — check against docs
- Document all frame conventions explicitly (body / camera-optical / world / NED)
- MAVLink injection: `OPTICAL_FLOW_RAD` for flow, `DISTANCE_SENSOR` for LiDAR
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
1. Raw flow + gyro rate publishing — done (`attitude_bridge.py` + `flow_x_raw`/`flow_y_raw`); manual derotation (`flow_x`/`flow_y`) kept as a characterisation tool only, not gating further work (see [Sensor Fusion Architecture](#sensor-fusion-architecture)); populate `flow_x_rad`/`flow_y_rad` next
2. Shadow rejection
3. Pixel-to-radian (rad/s) conversion with altitude scaling (focal length = 554 px)
4. Add downward point LiDAR to `iris_with_standoffs/model.sdf` — done, verified (Stage 1)
5. Inject `DISTANCE_SENSOR` (LiDAR, Stage 2) + `OPTICAL_FLOW_RAD` to ArduPilot via MAVLink

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
