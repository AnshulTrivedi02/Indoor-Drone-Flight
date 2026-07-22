# Thesis Progress Log

Master's thesis: Indoor drone state estimation (EKF / UKF / online FGO) in
GNSS-denied environments, with emphasis on robustness under degraded sensing.

---

## Current Status — 2026-07-22

**Machine migration in progress.** This machine's low RTF (≈0.05–0.17,
see Known Issues) is the reason a second Ubuntu 24 workstation is being
set up as the new working environment. ROS2/Gazebo/ArduPilot SITL still
need installing there — this machine remains the active one until that's
done. Repo pushed to `origin` (`git@github.com:AnshulTrivedi02/Indoor-
Drone-Flight.git`) specifically to support the move.

### Phase 1 checklist

| Task                                         | Status        | Notes |
|----------------------------------------------|---------------|-------|
| Downward camera in Gazebo                    | Done          | Publishes `/downward_camera/image` and `/downward_camera/camera_info` |
| Basic optical flow (Shi-Tomasi + LK)         | Done          | `flow_tracker.py` — pixel flow output to terminal |
| Mean → median displacement                   | Done          | `np.median` over inlier displacements |
| RANSAC outlier rejection                     | Done          | Tested — working; blank floor gives 4–10 features (too few); textured floor gives 60+ |
| Textured Gazebo world                        | Done, too small | `iris_textured.sdf` — 20 m × 20 m; needs enlarging to ≥50 m × 50 m before nominal-condition data is trustworthy |
| Optical flow validated                       | Done          | ~145 px/s at 0.5 m/s, 2 m alt — matches theory (138 px/s) |
| Simulation launch / teardown scripts         | Done          | `start_sim.sh`/`stop_sim.sh`; now also `run_trial.sh` for fully headless, unattended trials |
| ROS2 timestamp sync                          | Done          | `/clock` bridged; `use_sim_time:=true` everywhere |
| Ground truth bridging                        | Done          | `ground_truth_pub.py` → `/ground_truth/pose`, 57–227 Hz, sim-time |
| Custom OpticalFlow message + publisher       | Done          | `flow_x_raw`/`flow_y_raw` (production), `flow_x`/`flow_y` (derotated, characterisation-only), `flow_x_rad`/`flow_y_rad` (rad/s, fed to EKF3) |
| Data collection pipeline                     | Done          | `record_trial.sh` (manual) and `run_trial.sh` (fully automated, headless) |
| Shadow rejection                             | Not started   | — |
| Attitude bridge (`/attitude/angular_rates`)  | Done          | `attitude_bridge.py`; raw gyro rates, common raw input across all estimators |
| Manual flow derotation (characterisation)    | Done, deprioritised | Characterisation tool only — see CLAUDE.md "Sensor Fusion Architecture" |
| Pixel-to-radian (rad/s) conversion           | Done          | `flow_x_rad`/`flow_y_rad`, altitude-independent (focal length only) |
| Downward LiDAR in model.sdf                  | Done          | Stage 1 (sensor + ROS bridge) and Stage 2 (`RNGFND1` MAVLink injection) both verified |
| MAVLink injection (optical flow → EKF3)      | Done          | `OPTICAL_FLOW` (message 100), **not** `OPTICAL_FLOW_RAD` — unhandled by this ArduPilot build. Fusion verified via dataflash `XKF5`/`XKF1` |
| EKF3 state estimate → ROS2 + evo evaluation  | Done          | `ekf_bridge.py` → `/ekf/pose`; `evaluate_trial.sh` wraps `evo_ape`/`evo_rpe`/`evo_traj` |
| GNSS-denied config (flow + rangefinder only) | Done          | `gnss_denied.parm` — standing baseline for EKF3/UKF/FGO comparison |
| Automated, unattended trial harness          | Done          | `fly_trial.py` + `run_trial.sh` + `run_batch_trials.sh` |
| Accelerometer bridge (`/imu/data_raw`)       | Done          | `imu_bridge.py`; specific-force confirmed empirically (+9.81 m/s² at rest), 50 Hz, sim-time aligned with the other estimator inputs |
| UKF design                                   | Confirmed, no code yet | State vector, process/measurement models, matched robustness params, Q derivation, position reference, covariance logging, validation plan all decided — see CLAUDE.md "UKF Design" |
| No-yaw / compass-denied investigation        | Done          | Found EKF3 fusing compass outside the stated sensor suite; verified fix (`gnss_denied_nomag.parm`) not yet folded into the standing baseline — see CLAUDE.md "No-Yaw / Compass-Denied Investigation" |
| Corridor worlds — actual flight-tested       | Blocked       | Both `corridor_textured.sdf` and `corridor_blank.sdf` hit unresolved issues when actually flown via `run_trial.sh` — see Known Issues below |
| FGO (GTSAM) implementation                   | Not started   | Uses `gnss_denied.parm` baseline |

---

## Work Sessions

### Session — 2026-07-22 — IMU bridge, UKF design, no-yaw investigation, corridor-world bugs, machine migration

**Accelerometer bridge (`imu_bridge.py`).** The one raw sensor no prior
bridge provided — needed because a gyro-only process model can't observe
roll/pitch at all (only integrate them, open-loop). Bridges MAVLink
`HIGHRES_IMU` (chosen over `RAW_IMU`/`SCALED_IMU` after reading
`GCS_MAVLINK::send_highres_imu` directly — float32 SI units, no lossy
milli-g int16 encoding) to `/imu/data_raw` (`sensor_msgs/Imu`), FRD→FLU,
50 Hz. Verified empirically, not just asserted: 50.0 Hz achieved (message
count ÷ span from `ros2 bag info`), specific force confirmed
(`+9.811 m/s²` at rest, matching standard gravity; `+9.670 m/s²`
mid-cruise, consistent with a small forward pitch), sim-time alignment
against the other three estimator inputs confirmed to within ~20 ms.
`angular_velocity` is deliberately re-sourced from this same message
(not `/attitude/angular_rates`) so accel and gyro share one timestamped
sample — matters for a UKF predict step and GTSAM's IMU preintegration.
2 commits.

**UKF design report — confirmed, no filter code written.** Full design
pass before any implementation, per instruction. State vector: 9-state
scaffold (position/velocity ENU, Euler FLU) → 15-state IMU-driven
deliverable (+3-axis `gyro_bias`/`accel_bias`, matching EKF3's own state
structure exactly). Measurement models mirror EKF3's own formulation
(confirmed from `AP_NavEKF3_OptFlowFusion.cpp`/`PosVelFusion.cpp`
directly, not assumed). Robustness parameters (flow/range noise, gates,
quality handling) matched to EKF3's actual live values rather than
self-derived — the point being to isolate filter formulation from tuning
in the eventual comparison. One real correction found mid-review: process
noise parameters can't be copied from EKF3 unchanged, because EKF3's own
predict step runs at 400 Hz (`SCHED_LOOP_RATE`, read from a dataflash
`PARM` dump) while the UKF's is capped at 50 Hz — derived the correct
dt-rescaling from EKF3's own confirmed formulas rather than assuming
"same parameter = same behaviour." Full detail in CLAUDE.md, "UKF Design."

**No-yaw / compass-denied investigation.** Audit of every sensor EKF3
consumes under `gnss_denied.parm` vs what the UKF/FGO receive found a real
confound: `EK3_SRC1_YAW` is untouched, so EKF3 still fuses the compass for
yaw — a sensor outside the thesis's stated IMU+flow+LiDAR suite, and the
same category of unfair advantage the accelerometer gap was. Traced
ArduPilot's arming logic to find a working fix (counter-intuitively,
`COMPASS_ENABLE` must stay `1` — a separate, unconditional Copter arming
gate requires the compass to report healthy even though `EK3_SRC1_YAW=0`
+ `COMPASS_USE*=0` keep it out of actual fusion) — first attempt failed
exactly as source analysis predicted (`"Compass 1 not healthy"`), second
attempt (with the corrected param set) armed and flew cleanly. Verified
compass genuinely not fusing via dataflash (`XKFS.MAG_FUSION=0`, frozen
mag states) — not just assumed from the config. A 320 s flight
(`iris_textured.sdf`, since corridor worlds weren't usable yet — see
below) showed essentially zero yaw drift (±0.03° over the whole flight) —
**not evidence yaw drift is a non-issue generally**: EKF3 still estimates
gyro bias even without yaw fusion, the simulated gyro is very clean, and
the flight was pure straight-line with minimal actual yaw rotation. Fix
lives only in the throwaway `gnss_denied_nomag.parm` — **not folded into
the standing `gnss_denied.parm` baseline**, pending a decision. Full
detail in CLAUDE.md, "No-Yaw / Compass-Denied Investigation."

**Corridor worlds don't actually work yet — found by trying to fly a real
trial in them, which hadn't been done before.** `corridor_textured.sdf`
and `corridor_blank.sdf` were both previously "verified" only at the
Gazebo level (spawn pose, rendering, feature counts) — a real
`run_trial.sh` flight surfaced two separate, unresolved bugs:
- A Gazebo↔SITL JSON lockstep stall (confirmed via `gdb`: SITL blocks in
  `SITL::JSON::recv_fdm()`) that can take ~90–110 s to self-heal once a
  MAVLink client attaches. Initially misdiagnosed as corridor-specific
  slow world-loading (more floor tiles) — that theory is wrong, it
  reproduces on `iris_textured.sdf` too, and all worlds load in ~5-6s
  regardless. Mitigated (not fixed) by raising `run_trial.sh`'s relevant
  timeout 60s→240s.
- `corridor_blank.sdf` fails to arm outright — the downward LiDAR never
  returns a valid reading at the spawn point (`range: 41.0`, out of
  sensor range), so `RNGFND1` never gets data. Root cause not found; this
  world cannot currently fly a trial at all.
- Separately, an intermittent loss of the `PARAM_REQUEST_READ`/
  `PARAM_VALUE` round trip in `fly_trial.py`'s param-verification step was
  found (3/3 in one session) and partially mitigated (5x retry), but the
  root cause wasn't pinned down — reproduction attempts with `strace`
  wrapping the network syscalls of every relevant process succeeded
  cleanly 2/2, so this remains a genuinely open, intermittent issue.

Given these, the planned long-duration GNSS-denied flight (Next Priorities
#2, below) still hasn't been run on an actual corridor world — the no-yaw
320 s flight above used `iris_textured.sdf` instead as a substitute.

**Machine migration.** This machine's RTF (0.05–0.17) makes iteration
slow enough that a second Ubuntu 24 PC is being set up as the new
workstation. Repo brought up to date and pushed to GitHub to support the
move — ROS2/Gazebo/ArduPilot SITL setup on the new machine is a separate,
outstanding task.

---

### Session — 2026-07-14 — LiDAR, EKF3 flow fusion, GNSS-denied baseline, automated trial harness

This was a large session covering the rest of the sensing pipeline and closing
out Phase 1's remaining infrastructure work. Full technical detail (params,
frame transforms, verification numbers) is in `CLAUDE.md` — this is the
condensed log.

**Downward LiDAR (Stages 1 & 2).** Added a single-beam `gpu_lidar` to
`iris_with_standoffs/model.sdf` (z = −0.12 m, straight down), bridged to ROS2
as `sensor_msgs/Range` on `/downward_lidar/range`. Verified sub-mm accuracy
against ground truth during a hover. Found and root-caused two gotchas along
the way: `min_angle`/`max_angle` must both be exactly `0` for a 1-sample
sensor (Ogre2GpuRays silently ignores a small nonzero FOV), and this
machine's real-time factor (RTF ≈ 0.05–0.17, confirmed via `gz topic -e -t
/stats`) means wall-clock `ros2 topic hz` numbers are misleading — always
check sim-time header-stamp spacing instead. Stage 2 (`lidar_bridge.py`)
injects each reading into ArduPilot as `RNGFND1` via MAVLink
`DISTANCE_SENSOR`, verified against ground truth (mean error 0.17 mm,
~3% transient dropout under aggressive attitude changes — currently harmless
since `EK3_RNG_USE_HGT=-1` keeps it out of the height estimate).

**Optical flow → ArduPilot EKF3 fusion (Stage A).** Traced ArduPilot's
message dispatch directly and found `OPTICAL_FLOW_RAD` is silently dropped
by this build — no handler exists for it at all. Switched to the older
`OPTICAL_FLOW` message (100) via `flow_bridge.py`, using its MAVLink v2
`flow_rate_x`/`flow_rate_y` extension fields (required setting `MAVLINK20=1`
before importing pymavlink). Derived and empirically confirmed the
camera-optical-frame → MAVLink-body-frame sign mapping
(`flow_rate_x = -flow_x_rad`, `flow_rate_y = +flow_y_rad`). Verified fusion
is genuinely active (not just arriving) by parsing the ArduPilot dataflash
log directly: 0/251 flow innovations rejected, and the EKF's own fused
velocity state matched the commanded 0.4 m/s to within 1.3%.

Also hit the **`eeprom.bin` persistence gotcha** for the first time here:
once a param has any explicitly-stored value in ArduPilot SITL's persisted
`eeprom.bin`, `--add-param-file` silently stops overriding it. Fixed with a
live `PARAM_SET` + soft in-process reboot rather than deleting the eeprom —
this recurred in Stage C and is now handled automatically by
`fly_trial.py`'s `ensure_params()`.

**EKF3 state estimate → ROS2 + evo evaluation (Stage B).** `ekf_bridge.py`
reads ArduPilot's `LOCAL_POSITION_NED` + `ATTITUDE_QUATERNION` and republishes
as `/ekf/pose`, transformed from NED/FRD into the same ENU/FLU frame as
`/ground_truth/pose` (frame transform independently derived and verified,
not assumed — see CLAUDE.md). `evaluate_trial.sh` wraps `evo_ape`/`evo_rpe`/
`evo_traj`, reading bags directly via the `rosbags` library. Verification
trial: ATE RMSE 6.4 mm, RPE RMSE 4.6 mm — validates the pipeline end-to-end,
but GPS was still the position source at this stage, so this isn't yet a
flow-only accuracy number.

**GNSS-denied baseline (Stage C) — the config the thesis actually studies.**
`gnss_denied.parm` sets `EK3_SRC1_POSXY=0` (None — flow position isn't a
direct source, it becomes AID_RELATIVE dead-reckoning once
`readyToUseOptFlow()` is satisfied), `EK3_SRC1_POSZ=2` (RangeFinder),
`EK3_SRC1_VELZ=0`, and `SIM_GPS1_ENABLE=0`. Confirmed genuinely GPS-free by
decoding the `nav_filter_status` bitfield in the dataflash log (`using_gps`
False for 100% of samples), not just param readback. Flew this config over
both worlds:
- Textured floor: ATE RMSE 7.7 mm, `inlier_ratio` mean 0.94.
- Blank floor: ATE RMSE 10.0 mm, `inlier_ratio` mean 0.47 (62% of samples
  below 0.5, feature count dropping to zero on some frames).

**The real thesis signal here is at the sensor level, not (yet) the
position-error level** — `inlier_ratio` collapses sharply on the blank floor
exactly as expected, but the ~40 s flight is short enough that EKF3's
innovation gating and dead-reckoning haven't had time to turn that
sensor-level degradation into dramatic drift yet. Flagged as the direct
motivation for the next item.

**Automated, unattended trial harness.** Built to make longer/more varied
flights (needed to actually see drift accumulate) practical to collect
without babysitting each one:
- `fly_trial.py` — MAVLink flight controller: connect, self-heal the eeprom
  gotcha, arm, climb, cruise for a specified **sim-time** duration, stop,
  land. Every phase gates on measured vehicle state, never wall-clock sleep
  (this machine's RTF makes that unreliable — a real bug hit in Stage A's
  first draft).
- `run_trial.sh` — full headless stack launch (Gazebo, SITL, MAVProxy,
  bridges, flow node) with state-polled readiness at each step, drives
  `fly_trial.py`, records the full topic set, copies the ArduPilot log,
  writes `metadata.yaml`. Idempotent cleanup trap kills whole process
  groups, not single PIDs (`ros2 run`/`ros2 bag` fork/exec a real binary
  under a wrapper). Found and fixed two real bugs during verification: a
  missing hard-kill fallback that orphaned the recorder, and — more
  seriously — `ros2 bag record` silently *ignoring* SIGINT once detached
  from a tty (confirmed via `/proc/<pid>/status`), which meant trials were
  reporting success while producing bags with no `metadata.yaml`. Fixed by
  switching recorder shutdown to SIGTERM.
- `run_batch_trials.sh` — reads a `(world, velocity, altitude, duration)`
  list from a config file and runs them back-to-back unattended, logging and
  continuing past individual trial failures rather than aborting the batch.

All three verified end-to-end (zero orphan processes, valid bags, correct
metadata, and a deliberate-failure test proving the batch continues past a
bad row) and committed as three separate commits.

---

### Session — 2026-07-02 (cont.) — Attitude bridge, derotation, and architecture reframe

**Attitude bridge and manual derotation implemented.** `attitude_bridge.py`
(new) bridges MAVLink `ATTITUDE` body rates to `/attitude/angular_rates`
(`geometry_msgs/Vector3Stamped`, raw FRD, on a dedicated MAVLink port 14551
so it doesn't collide with `fly_forward.py`'s port 14550).
`flow_tracker.py` gained a manual derotation path (`enable_derotation`
param, default on) that maps FRD body rates into the camera optical frame
and subtracts rotational pixel flow from measured flow; `OpticalFlow.msg`
gained `flow_x_raw`/`flow_y_raw`/`derotation_enabled` fields so raw and
derotated flow are both available.

Bugs found and fixed along the way:
- Sign error on the roll term in derotation (correction was adding instead
  of subtracting) — fixed, commit `cab84c1`.
- Attitude stream rate silently decaying to ~4 Hz because MAVProxy
  periodically re-issues its own low default stream-rate request, clobbering
  our one-time `SET_MESSAGE_INTERVAL` — fixed with a periodic re-assert
  timer, commit `8baa64e`.
- `ros2 bag record` silently dropped the custom `OpticalFlow` topic when
  only `/opt/ros/jazzy/setup.bash` was sourced (not the workspace overlay).
- Stale duplicate `flow_tracker`/`attitude_bridge` processes from
  incomplete prior restarts corrupted a recorded bag with mixed
  message-definition versions — fixed by always killing stale PIDs before a
  clean run.

**Isolated pure-rotation hover validation — partial, then deprioritised.**
Only the yaw test was completed (pitch/roll not attempted — an earlier
attempt to isolate pitch via `ALT_HOLD` crashed the drone; `ALT_HOLD`
interprets RC3 as a climb-rate command, not absolute throttle). Yaw result:
flow_x median |raw| 185 px/s → |derotated| 157 px/s (15% reduction), not
the clean collapse the pass/fail criterion called for. Investigation
surfaced a persistent ~0.4 rad/s (23°/s) roll-rate oscillation present even
at idle hover with zero commanded motion — real (visible camera shake,
confirmed independently), but with ArduPilot's own `VIBRATION` and
`EKF_STATUS_REPORT` reporting healthy/low levels, consistent with fast
self-cancelling motor/frame buzz rather than a control-loop problem.

**Design decision — supervisor guidance (Mitchell), 2026-07-02.** Each
estimator should consume raw sensor data and perform its own rotation
compensation on its own terms, rather than all three being fed one
identically pre-processed input:
- **ArduPilot EKF3** is the fixed baseline — native `OPTICAL_FLOW` input
  (raw flow only; see the 2026-07-14 session above for why `OPTICAL_FLOW_RAD`
  isn't usable), derotates internally using its own AHRS gyro. No shortcuts.
- **FGO** will do rotation compensation inside its own flow factor
  (referencing IMU/attitude state from within the graph), not by consuming
  a separately pre-derotated flow topic.
- **UKF** (if implemented) follows the same principle for its own
  measurement model.
- Fairness comes from each estimator being correctly implemented on its own
  terms, not identical preprocessing.

**Practical consequence:** the manual derotation path built this session
is **not a production data path** for any estimator — `flow_x_raw`/
`flow_y_raw` (plus `/attitude/angular_rates`) are the production values.
`flow_x`/`flow_y` (derotated) and `enable_derotation` are retained as a
**characterisation tool** — useful for the methodology write-up and for
informing the FGO's flow-factor design — not deleted. Chasing the
background-vibration confound to get a clean collapse-to-zero is
**deprioritised/deferred indefinitely**; it was only relevant to validating
a production path that no longer exists. `analyse_derotation.py` and the
sign-fix work remain valid characterisation tooling. See CLAUDE.md,
"Sensor Fusion Architecture", for the full write-up.

**Velocity-dependent flow error reframed as an experimental axis, not a
bug.** `analyse_flow_sweep.py` (new this session) measured optical flow
error growing from roughly +7.8% at 0.25 m/s to +12.5% at 1.0 m/s.
Supervisor guidance: "filters will start to break down at higher speeds,
that's kinda expected and okay — can be a test case for you." Commanded
velocity is now a planned second experimental axis alongside sensing
degradation (see CLAUDE.md, "Experimental Design Notes") — not an open
defect to fix.

**Still open / deferred (not blocking):**
- Pitch-only and roll-only isolated hover tests — not attempted; low
  priority now that manual derotation is characterisation-only.
- Background sim vibration source — deferred indefinitely, no longer
  blocking anything.

---

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
  nominal-condition data. **Still not actioned as of 2026-07-14.**
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
| `src/optical_flow_node/optical_flow_node/flow_tracker.py` | Main optical flow node — publishes `/optical_flow/measurement` (`flow_x_raw`/`flow_y_raw` are production; `flow_x_rad`/`flow_y_rad` fed to EKF3; `flow_x`/`flow_y` derotated, characterisation-only) |
| `src/optical_flow_interfaces/msg/OpticalFlow.msg` | Custom flow message definition |
| `ground_truth_pub.py` | Republishes Gazebo drone pose as `/ground_truth/pose` |
| `attitude_bridge.py` | Republishes MAVLink `ATTITUDE` body rates as `/attitude/angular_rates` — common raw input across all estimators |
| `lidar_bridge.py` | Injects `/downward_lidar/range` into ArduPilot as `RNGFND1` via MAVLink `DISTANCE_SENSOR` |
| `flow_bridge.py` | Injects `/optical_flow/measurement` into ArduPilot EKF3 as MAVLink `OPTICAL_FLOW` |
| `ekf_bridge.py` | Republishes ArduPilot EKF3's state estimate as `/ekf/pose`, transformed NED/FRD → ENU/FLU |
| `imu_bridge.py` | Republishes MAVLink `HIGHRES_IMU` accel + a co-sampled gyro copy as `/imu/data_raw` — the UKF/FGO process model's accelerometer input |
| `evaluate_trial.sh` | Wraps `evo_ape`/`evo_rpe`/`evo_traj` to score a trial's `/ekf/pose` against `/ground_truth/pose` |
| `fly_trial.py` | State-gated flight controller (arm/climb/cruise/land) for the automated harness |
| `run_trial.sh` | One-command, headless, unattended single-trial harness (launch → fly → record → teardown) |
| `run_batch_trials.sh` | Runs a config-file list of trials back-to-back, continuing past individual failures |
| `analyse_derotation.py` | Characterisation tool — quantifies rotational coupling in raw flow (not a production pipeline component) |
| `analyse_flow_sweep.py` | Velocity-sweep flow validation — feeds the velocity experimental axis |
| `dump_flow.py` | Ad-hoc debug script — dumps raw `flow_y` + feature/inlier stats from a bag (untracked scratch tool) |
| `record_trial.sh` | Manual/interactive trial recording (bag + metadata + ArduPilot log); superseded for unattended use by `run_trial.sh` |
| `gnss_denied.parm` | GNSS-denied EK3 source config — the standing baseline for EKF3/UKF/FGO comparison |
| `gnss_denied_nomag.parm` | Throwaway — verified fix for EKF3 fusing the compass for yaw outside the stated sensor suite; not yet folded into `gnss_denied.parm` |
| `flow_ekf.parm` | `FLOW_TYPE`/EK3 params enabling optical-flow velocity fusion |
| `lidar_rangefinder.parm` | `RNGFND1` params for the MAVLink-injected downward LiDAR |
| `start_sim.sh` | Manual/interactive launch of the full simulation stack — `./start_sim.sh [world.sdf]` |
| `stop_sim.sh` | Tear down stack and close terminal tabs |
| `fly_forward.py` | Continuous MAVLink velocity commands for manual/ad-hoc testing |
| `~/ardupilot_gazebo/worlds/iris_runway.sdf` | Blank floor — **degraded baseline** |
| `~/ardupilot_gazebo/worlds/iris_textured.sdf` | Checkerboard floor — **nominal baseline**, still too small (20×20 m) |
| `~/ardupilot_gazebo/worlds/corridor_textured.sdf` / `corridor_blank.sdf` / `corridor_transition.sdf` | 20×160 m long-duration worlds — built and Gazebo-level verified, but **not yet flown end-to-end successfully** via `run_trial.sh`, see Known Issues |
| `~/ardupilot_gazebo/models/textured_ground/` | Checkerboard ground plane model |
| `~/ardupilot_gazebo/models/iris_with_standoffs/model.sdf` | Drone model (downward camera + LiDAR defined here) |

---

## Next Priorities (Phase 1 remainder → Phase 2)

0. **Set up ROS2/Gazebo/ArduPilot SITL on the new Ubuntu 24 machine** —
   migration motivated by this machine's low RTF (0.05–0.17); this
   machine remains primary until the new one is ready.
1. **Fix the two corridor-world bugs** before relying on them for real
   trials — the JSON lockstep stall (mitigated with a longer timeout, not
   fixed) and `corridor_blank.sdf`'s LiDAR-no-surface arming failure
   (unresolved). See Known Issues.
2. **Decide on the no-yaw compass fix** (`gnss_denied_nomag.parm`) — fold
   into the standing `gnss_denied.parm` baseline, or keep EKF3's compass
   active as a deliberate, documented asymmetry? Affects every future
   trial and the fairness of the eventual EKF3/UKF/FGO comparison.
3. **Enlarge textured world** — current 20 m × 20 m mat is still too small
   for forward-flight trials; need ≥50 m × 50 m before nominal-condition
   data collection is fully trustworthy. Not yet actioned. (Corridor
   worlds address the length problem for GNSS-denied trials specifically,
   but not this one for nominal-condition data.)
4. **Shadow rejection** — detect and mask the drone's shadow in the downward
   camera frame before feature detection.
5. **Longer / more aggressive GNSS-denied flights on an actual corridor
   world** — Stage C's ~40 s flights showed a sharp sensor-level
   texture-quality gap (`inlier_ratio` 0.94 vs 0.47) but only a modest ATE
   gap (7.7 mm vs 10.0 mm); the working hypothesis is that drift
   accumulates more starkly over longer flights. A 320 s no-yaw flight was
   run on `iris_textured.sdf` as a substitute (yaw drift ~0°, see the
   2026-07-22 session) but the actual textured-vs-blank corridor
   comparison is still blocked on priority #1 above.
6. **UKF implementation** — design confirmed (see CLAUDE.md "UKF Design"),
   no code written yet. Build the constant-velocity scaffold first
   (plumbing only, not a thesis result), then the IMU-driven deliverable.
7. **FGO (GTSAM) implementation** — flow-factor rotation compensation done
   inside the graph itself, not via pre-derotated flow. Same baseline config.

---

## Architecture (current)

```
Gazebo (iris_textured.sdf — checkerboard floor, nominal)
  OR   (iris_runway.sdf   — blank floor, degraded baseline)
  └─ iris_with_ardupilot → iris_with_standoffs → downward camera + downward LiDAR
       │  gz transport
       ▼
  ros_gz_bridge
       ├─ /downward_camera/image + /downward_camera/camera_info
       ├─ /downward_lidar/range   (sensor_msgs/Range)
       ├─ /clock  (sim time)
       └─ /world/<world>/dynamic_pose/info  (PoseArray — NOT TFMessage)
                │
         ground_truth_pub.py  [poses[0] = iris_with_ardupilot]
                │
         /ground_truth/pose  (PoseStamped, sim-time stamps)
       │
       ├─ flow_tracker.py
       │    ├─ Shi-Tomasi + Lucas-Kanade + RANSAC
       │    └─ /optical_flow/measurement  (flow_x_raw/rad, sim-time stamps)
       ├─ attitude_bridge.py  →  /attitude/angular_rates  (raw gyro, MAVLink)
       │
       ▼ (flow_bridge.py, lidar_bridge.py inject into ArduPilot via MAVLink)
  ArduPilot SITL — EKF3 (gnss_denied.parm: no GPS, flow VELXY, RangeFinder POSZ)
       │
       ▼ (ekf_bridge.py, MAVLink → ROS2, NED/FRD → ENU/FLU)
  /ekf/pose  (PoseStamped, sim-time stamps)
       │
       ▼
  run_trial.sh  (headless, unattended: launch stack → fly_trial.py → record → teardown)
       └─ ~/thesis_data/trials/<name>/
               ├─ bag/           (ROS2 bag: clock, ground_truth, ekf pose,
               │                  lidar, attitude, flow)
               ├─ metadata.yaml
               ├─ ardupilot.bin  (dataflash log)
               └─ logs/          (per-process stdout/stderr)
                        │
                 evaluate_trial.sh  (evo ATE/RPE/traj vs ground truth)
```

---

## Known Issues (open)

1. **Manual derotation partial collapse (deprioritised, not blocking)** — isolated
   pure-rotation hover testing found only a 5–15% reduction in flow_x/flow_y
   magnitude, not a clean collapse, confounded by a persistent ~0.4 rad/s
   background sim vibration present even at idle hover. Deferred indefinitely
   — manual derotation is a characterisation tool only, not a production
   input for any estimator (see CLAUDE.md, "Sensor Fusion Architecture").
2. **Drone shadow** contaminates downward flow (not yet characterised on textured floor).
3. **Textured world too small** — 20 m × 20 m mat; drone exits mat during
   forward-flight trials, producing feature-poor segments inside nominally
   "textured" recordings.
4. **Feature count is a deceptive quality metric** — camera reports ~100
   "features" even on featureless off-mat texture; use `inlier_ratio` (RANSAC
   survivors) as the real flow-quality indicator.
5. **TFMessage bridge broken for ground truth** — `gz.msgs.Pose_V →
   tf2_msgs/TFMessage` in ros_gz_bridge 1.0.22 zeros all stamps and clears all
   frame names; use `PoseArray` instead (see `ground_truth_pub.py`).
6. **Real-time factor is low on this machine** — RTF ≈ 0.05–0.17, even
   headless. Every sim-time-dependent wait (sensor rates, flight phases) must
   be gated on measured state, never wall-clock sleep — see `fly_trial.py`
   and CLAUDE.md's Known Issues #9 for the full reasoning.
7. **SITL's `eeprom.bin` can silently defeat `--add-param-file`** — once a
   param has any explicitly-stored value in the persisted eeprom, new
   `--defaults`/`--add-param-file` values are ignored for it. Self-healed
   automatically in `fly_trial.py` (`ensure_params()`) via a live `PARAM_SET`
   + soft reboot; watch for this if any future param addition seems to not
   take effect.
8. **Downward LiDAR RNGFND1 dropouts under aggressive attitude changes** —
   ~3% of readings during a dynamic climb briefly read near-zero. Currently
   harmless (`EK3_RNG_USE_HGT=-1` keeps RNGFND1 out of the height estimate);
   revisit before ever enabling range-based height switching.
9. **GNSS-denied ATE gap is currently modest, not yet conclusive** — Stage C's
   short (~40 s) flights show a sharp sensor-level `inlier_ratio` gap between
   textured/blank floors but only a modest ATE gap; whether that gap widens
   over longer/more aggressive flights is untested — see Next Priorities #5.
10. **`gnss_denied.parm` lets EKF3 fuse the compass for yaw** — outside the
    thesis's stated IMU+flow+LiDAR sensor suite, a confound vs UKF/FGO's
    no-yaw setup. Verified fix exists (`gnss_denied_nomag.parm`) but not
    applied to the standing baseline — see CLAUDE.md "No-Yaw /
    Compass-Denied Investigation" and Next Priorities #2.
11. **Corridor worlds can't currently fly a real trial** — `corridor_textured.sdf`
    needs a 240 s (not 60 s) timeout to ride out a Gazebo↔SITL JSON
    lockstep stall (self-heals, not fixed); `corridor_blank.sdf` fails to
    arm outright (downward LiDAR never returns a valid reading at the
    spawn point — root cause not found). See CLAUDE.md Known Issues #11/#12.
12. **Intermittent loss of the `PARAM_REQUEST_READ`/`PARAM_VALUE` round trip**
    in `fly_trial.py`'s param-verification step — reproduced 3/3 in one
    session, 0/2 in strace-instrumented follow-up reproduction attempts.
    Genuinely racy, root cause not found; MAVProxy's own forwarding logic
    ruled out via source (`mavfwd` defaults `True`, `no_fwd_types` only
    excludes `BAD_DATA`). 5x retry added as a mitigation, not a fix. Watch
    for this on the new machine too.

## Camera Parameters (confirmed)

| Parameter        | Value                        |
|------------------|------------------------------|
| Resolution       | 640 × 480 px                 |
| Horizontal FOV   | 60° (1.047 rad)              |
| Focal length     | ~554 px                      |
| Mount            | Rigid downward, no gimbal    |
