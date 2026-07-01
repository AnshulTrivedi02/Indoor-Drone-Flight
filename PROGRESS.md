# Thesis Progress Log

Master's thesis: Indoor drone state estimation (EKF / UKF / online FGO) in
GNSS-denied environments, with emphasis on robustness under degraded sensing.

---

## Current Status — 2026-07-02

### Phase 1 checklist

| Task                                         | Status        | Notes |
|----------------------------------------------|---------------|-------|
| Downward camera in Gazebo                    | Done          | Publishes `/downward_camera/image` and `/downward_camera/camera_info` |
| Basic optical flow (Shi-Tomasi + LK)         | Done          | `flow_tracker.py` — pixel flow output to terminal |
| Mean → median displacement                   | Done          | `np.median` over inlier displacements |
| RANSAC outlier rejection                     | Done          | Tested — working; blank floor gives 4–10 features (too few); textured floor gives 60+ |
| Textured Gazebo world                        | Done          | `iris_textured.sdf` + `textured_ground` model (64×64 checkerboard, 20 m plane, ~0.31 m/square at ground) |
| Optical flow validated                       | Done          | Measured ~145 px/s at 0.5 m/s, 2 m alt — matches theory (expected 138 px/s). Flow_y consistent; flow_x noisy from gyro coupling |
| Simulation launch / teardown scripts         | Done          | `start_sim.sh` accepts world arg; `stop_sim.sh` uses sentinel file to close tabs cleanly |
| ROS2 timestamp sync                          | Done          | `/clock` bridged from Gazebo; all nodes run with `use_sim_time:=true`; header stamps confirmed sim-time |
| Ground truth bridging                        | Done          | Pose_V → PoseArray bridge; `ground_truth_pub.py` republishes `poses[0]` as `/ground_truth/pose` (PoseStamped); verified 57–227 Hz, sim-time stamps |
| Custom OpticalFlow message + publisher       | Done          | `optical_flow_interfaces` package; `flow_tracker.py` publishes `/optical_flow/measurement`; `flow_x_rad`/`flow_y_rad` reserved but zero |
| Data collection pipeline                     | Done          | `record_trial.sh` records self-contained trials; see Data Collection section below |
| Shadow rejection                             | Not started   | — |
| Gyro decoupling                              | Not started   | Roll/pitch rate contaminates flow_x/flow_y; correction = `flow_measured − (ω × focal_length)` |
| Pixel-to-radian (rad/s) conversion           | Not started   | Needed for `OPTICAL_FLOW_RAD`; requires altitude scaling |
| Downward LiDAR in model.sdf                  | Not started   | Inject via `DISTANCE_SENSOR` MAVLink message |
| MAVLink injection (OPTICAL_FLOW_RAD)         | Not started   | — |

---

## Work Sessions

### Session — 2026-07-02

**Data collection pipeline built and verified (Sessions 1 & 2).**

One command now records a self-contained trial:
```bash
./record_trial.sh <name> --world <w> --velocity <v> --altitude <a> --notes "<n>"
```
Produces `~/thesis_data/trials/<name>/` containing `bag/` (ROS2 bag),
`metadata.yaml` (ISO timestamp, world, velocity, altitude, git hash, hostname,
notes), and `ardupilot.bin` (dataflash log copied from
`~/ardupilot/ArduCopter/logs/`).

**Ground truth pose bridging.** Gazebo drone pose →
`/ground_truth/pose` (`geometry_msgs/PoseStamped`) via `ground_truth_pub.py`.
Verified: sim-time timestamps, 57–227 Hz, stable tracking of `iris_with_ardupilot`.

**Custom optical flow message.** New `optical_flow_interfaces` package
(ament_cmake) defines `OpticalFlow.msg` (`flow_x`, `flow_y`, `feature_count`,
`inlier_ratio`, `valid`, `flow_x_rad`, `flow_y_rad`). `flow_tracker.py` now
publishes on `/optical_flow/measurement` in addition to terminal logging.
Angular flow fields (`_rad`) reserved but not yet populated (zero).

**Lightweight recording.** Raw camera images dropped from trials by default.
A 35 s trial is now ~2.7 MiB vs ~2.4 GiB with images (~900× reduction).
Images available via `--with-images` for dedicated flow-development runs.

**Trial metadata** includes git commit hash for reproducibility, plus
ArduPilot dataflash log retrieval (newest `.BIN` by mtime from
`~/ardupilot/ArduCopter/logs/`).

**Bugs found and fixed during verification (lessons):**

- `gz.msgs.Pose_V → tf2_msgs/TFMessage` bridge in ros_gz_bridge 1.0.22 strips
  all frame names and timestamps (all `child_frame_id` empty, all stamps zero).
  Switched to `Pose_V → geometry_msgs/PoseArray`, selecting `poses[0]` (the
  top-level model, always `iris_with_ardupilot`). **Do not use TFMessage for
  ground truth.**
- Raw image recording made trials multi-gigabyte and contributed to sim
  instability on the laptop. Estimators consume flow measurements, not pixels,
  so images are excluded from evaluation trials by default.

**Flagged for later (not yet actioned):**

- The 20 m × 20 m textured checkerboard is too small — the drone flies off it
  during normal forward flight, contaminating "nominal" trials with off-mat
  (feature-poor) segments. Need a larger textured plane (e.g. 50 m × 50 m) or
  flight paths constrained to stay within the mat before collecting real
  nominal-condition data.
- Feature count is a deceptive quality metric: the camera reported ~100
  "features" even on featureless off-mat texture. Use `inlier_ratio` (RANSAC
  survivors) as the real flow-quality signal, not raw feature count.
- `flow_x` gyro coupling still present (unchanged Phase 1 task): rigid camera
  mount means drone attitude oscillation swamps translational flow; needs gyro
  decoupling before `flow_x_rad` can be populated.

---

### Session — 2026-06-28

- **Tested RANSAC** in simulation on blank floor (`iris_runway.sdf`). Confirmed
  working but blank floor yields only 4–10 features — insufficient for reliable
  RANSAC. Flow values ±300–900 px/s while hovering: pure noise.
- **Created textured Gazebo world** (`iris_textured.sdf`) with a custom
  `textured_ground` model: 20 m × 20 m plane, 64×64 checkerboard PNG texture
  (~0.31 m per square). Camera FOV 60°, altitude 2 m → ~7.5 squares visible
  across frame.
- **Validated optical flow** on textured floor at 0.5 m/s forward:
  - 60–66 features tracked per frame (vs 4–10 on blank floor)
  - flow_y ≈ +145 px/s — consistent signal, matches kinematic prediction
    (v/h × f = 0.5/2 × 554 = 138 px/s)
  - flow_x oscillates ±250 px/s around zero — gyro coupling from drone
    attitude oscillation, not a flow algorithm bug
- **Fixed `stop_sim.sh`**: removed `pkill gnome-terminal` (was killing Claude
  terminal). Now uses sentinel file `/tmp/thesis_sim_stop` — tabs poll for the
  file and exit naturally when it appears, closing gnome-terminal tabs cleanly.
- **Updated `start_sim.sh`**: accepts optional world argument
  (`./start_sim.sh iris_textured.sdf`); defaults to `iris_runway.sdf`.
- **Added `fly_forward.py`**: pymavlink script that sends continuous velocity
  commands every 100 ms — works around ArduPilot GUIDED mode timeout.
  Usage: `python3 ~/thesis_ws/fly_forward.py [vx] [vy] [vz]`

### Session — ~2026-06-18 (lost, reconstructed from code)

- Added **RANSAC outlier rejection** to `flow_tracker.py` using
  `cv2.estimateAffinePartial2D`. Inlier mask applied before median computation.
- Added **simulation launch script** (`start_sim.sh`): 5 gnome-terminal tabs
  with staggered sleep delays.
- Added **simulation teardown script** (`stop_sim.sh`).
- Last colcon build: 2026-06-18.

---

## Key Files

| File | Purpose |
|------|---------|
| `src/optical_flow_node/optical_flow_node/flow_tracker.py` | Main optical flow node — publishes `/optical_flow/measurement` |
| `src/optical_flow_interfaces/msg/OpticalFlow.msg` | Custom flow message definition |
| `ground_truth_pub.py` | Republishes Gazebo drone pose as `/ground_truth/pose` |
| `record_trial.sh` | Records one self-contained trial (bag + metadata + ArduPilot log) |
| `start_sim.sh` | Launch full simulation stack — `./start_sim.sh [world.sdf]` |
| `stop_sim.sh` | Tear down stack and close terminal tabs |
| `fly_forward.py` | Continuous MAVLink velocity commands for testing |
| `~/ardupilot_gazebo/worlds/iris_runway.sdf` | Blank floor — **degraded baseline** |
| `~/ardupilot_gazebo/worlds/iris_textured.sdf` | Checkerboard floor — **nominal baseline** |
| `~/ardupilot_gazebo/models/textured_ground/` | Checkerboard ground plane model |
| `~/ardupilot_gazebo/models/iris_with_standoffs/model.sdf` | Drone model (downward camera defined here) |

---

## Next Priorities (Phase 1 remainder)

0. **Enlarge textured world** — current 20 m × 20 m mat is too small for
   forward-flight trials; need ≥50 m × 50 m before nominal-condition data
   collection is meaningful.
1. **Gyro decoupling** — subscribe to IMU (MAVLink, no ROS2 IMU topic in this
   stack), subtract rotational contribution (`ω × f`) from pixel flow; populate
   `flow_x_rad` / `flow_y_rad` in `OpticalFlow.msg`. Dominant noise source.
2. **Shadow rejection** — detect and mask the drone's shadow in the downward
   camera frame before feature detection.
3. **Pixel-to-radian conversion** — convert px/s → rad/s using camera focal
   length (554 px at 640×480, 60° FOV); scale by altitude once LiDAR is available.
4. **Downward LiDAR** — add point LiDAR to `iris_with_standoffs/model.sdf`,
   inject `DISTANCE_SENSOR` MAVLink message.
5. **MAVLink injection** — send `OPTICAL_FLOW_RAD` to ArduPilot EKF.

---

## Architecture (current)

```
Gazebo (iris_textured.sdf — checkerboard floor, nominal)
  OR   (iris_runway.sdf   — blank floor, degraded baseline)
  └─ iris_with_ardupilot → iris_with_standoffs → downward camera
       │  gz transport
       ▼
  ros_gz_bridge
       ├─ /downward_camera/image + /downward_camera/camera_info
       ├─ /clock  (sim time)
       └─ /world/<world>/dynamic_pose/info  (PoseArray — NOT TFMessage)
                │
         ground_truth_pub.py  [poses[0] = iris_with_ardupilot]
                │
         /ground_truth/pose  (PoseStamped, sim-time stamps)
       │
       ▼
  flow_tracker.py
       ├─ Shi-Tomasi corner detection
       ├─ Lucas-Kanade optical flow
       ├─ RANSAC inlier filtering ✓ tested
       └─ /optical_flow/measurement  (OpticalFlow.msg, sim-time stamps)
                │
         record_trial.sh
                └─ ~/thesis_data/trials/<name>/
                        ├─ bag/           (ROS2 bag)
                        ├─ metadata.yaml
                        └─ ardupilot.bin  (dataflash log)
```

---

## Known Issues (open)

1. **Gyro decoupling absent** — roll/pitch oscillation contaminates flow_x (dominant noise source)
2. **Drone shadow** contaminates downward flow (not yet characterised on textured floor)
3. **No pixel-to-radian conversion** — cannot produce `OPTICAL_FLOW_RAD` yet
4. **No LiDAR** — metric scale unavailable, ArduPilot EKF cannot fuse flow
5. **Textured world too small** — 20 m × 20 m mat; drone exits mat during forward-flight trials, producing feature-poor segments inside nominally "textured" recordings
6. **Feature count is a deceptive quality metric** — camera reports ~100 "features" even on featureless off-mat texture; use `inlier_ratio` (RANSAC survivors) as the real flow-quality indicator
7. **TFMessage bridge broken for ground truth** — `gz.msgs.Pose_V → tf2_msgs/TFMessage` in ros_gz_bridge 1.0.22 zeros all stamps and clears all frame names; use `PoseArray` instead (see `ground_truth_pub.py`)

## Camera Parameters (confirmed)

| Parameter        | Value                        |
|------------------|------------------------------|
| Resolution       | 640 × 480 px                 |
| Horizontal FOV   | 60° (1.047 rad)              |
| Focal length     | ~554 px                      |
| Mount            | Rigid downward, no gimbal    |
