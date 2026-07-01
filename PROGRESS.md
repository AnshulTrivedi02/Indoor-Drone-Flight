# Thesis Progress Log

Master's thesis: Indoor drone state estimation (EKF / UKF / online FGO) in
GNSS-denied environments, with emphasis on robustness under degraded sensing.

---

## Current Status — 2026-06-28

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
| Shadow rejection                             | Not started   | — |
| Gyro decoupling                              | Not started   | Roll/pitch rate contaminates flow_x/flow_y; correction = `flow_measured − (ω × focal_length)` |
| Pixel-to-radian (rad/s) conversion           | Not started   | Needed for `OPTICAL_FLOW_RAD`; requires altitude scaling |
| Downward LiDAR in model.sdf                  | Not started   | Inject via `DISTANCE_SENSOR` MAVLink message |
| MAVLink injection (OPTICAL_FLOW_RAD)         | Not started   | — |
| ROS2 timestamp sync                          | Not started   | Gazebo sim time vs ROS time vs ArduPilot unresolved |

---

## Work Sessions

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
| `src/optical_flow_node/optical_flow_node/flow_tracker.py` | Main optical flow node |
| `start_sim.sh` | Launch full simulation stack — `./start_sim.sh [world.sdf]` |
| `stop_sim.sh` | Tear down stack and close terminal tabs |
| `fly_forward.py` | Continuous MAVLink velocity commands for testing |
| `~/ardupilot_gazebo/worlds/iris_runway.sdf` | Blank floor — **degraded baseline** |
| `~/ardupilot_gazebo/worlds/iris_textured.sdf` | Checkerboard floor — **nominal baseline** |
| `~/ardupilot_gazebo/models/textured_ground/` | Checkerboard ground plane model |
| `~/ardupilot_gazebo/models/iris_with_standoffs/model.sdf` | Drone model (downward camera defined here) |

---

## Next Priorities (Phase 1 remainder)

1. **Gyro decoupling** — subscribe to IMU (`/imu` or via MAVLink), subtract
   rotational contribution (`ω × f`) from pixel flow before computing
   translational estimate. This is the dominant noise source in flow_x.
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
       │  /downward_camera/image
       ▼
  flow_tracker.py
       ├─ Shi-Tomasi corner detection
       ├─ Lucas-Kanade optical flow
       ├─ RANSAC inlier filtering (cv2.estimateAffinePartial2D) ✓ tested
       └─ Median displacement → px/s logged to terminal
```

---

## Known Issues (open)

1. Gyro decoupling absent — roll/pitch oscillation contaminates flow_x (dominant noise source)
2. Drone shadow contaminates downward flow (not yet characterised on textured floor)
3. No pixel-to-radian conversion — cannot produce `OPTICAL_FLOW_RAD` yet
4. No LiDAR — metric scale unavailable, ArduPilot EKF cannot fuse flow
5. Timestamp sync between Gazebo / ROS / ArduPilot unresolved

## Camera Parameters (confirmed)

| Parameter        | Value                        |
|------------------|------------------------------|
| Resolution       | 640 × 480 px                 |
| Horizontal FOV   | 60° (1.047 rad)              |
| Focal length     | ~554 px                      |
| Mount            | Rigid downward, no gimbal    |
