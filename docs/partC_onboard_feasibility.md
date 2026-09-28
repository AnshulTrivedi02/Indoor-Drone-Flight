# Part C: Feasibility of running the UKF and FGO onboard as ArduPilot estimators

**Scope.** This is a read-only investigation. No files in `~/ardupilot`, `~/ardupilot_gazebo` or `~/thesis_ws` were modified and nothing was built.

**Scope (supervisor answers, 29 Sep).**
- Target hardware is an STM32H743 flight controller: ArduPlane QuadPlane in Q modes indoors, and also Copter.
- The **UKF runs onboard** as a drop-in replacement for EKF3.
- The **FGO runs GTSAM online on a companion computer** (Pi class), which also hosts the forward-camera processing.
- One firmware build per vehicle with parameter selection is preferred.

**Source pin.** ArduPilot `7bac20cbcc`, confirmed with `git -C ~/ardupilot rev-parse --short HEAD`. All `path:line` citations are at that commit unless marked `ardupilot_gazebo` or `thesis_ws`.

**Labelling.**
- **[V]** means verified in source, in a log, or in a cited document.
- **[E]** means an estimate. Its basis is stated alongside it.
- **[U]** means unverified or not confirmed.

---

## Summary table

| # | Item | Feasible? | Effort (person-weeks, [E]) | Main risk |
|---|---|---|---|---|
| 1 | UKF as an onboard drop-in: interface spec (what EKF3 gives AP_AHRS), Copter and Plane Q modes | Yes. The spec is fully enumerable: 86 `EKF3.*` call sites, about 70 methods (§1.2). Plane's QuadPlane uses the same interface (§1.9). | 0.5 (documentation) | The semantics matter more than the signatures. `get_variances()` returns normalised test ratios; resets and `nav_filter_status` flags drive failsafes and controllers. **Plane-only:** the `FIXED_WING` DCM fallback (`AP_AHRS.cpp:2104-2200`) needs `AHRS_OPTIONS` bit 1 if a compass is in use. |
| 2 | One build (per vehicle) with `AHRS_EKF_TYPE` selection and shadow running; FGO off-board routes | UKF: yes. EKF3 already runs and logs while not active: `dsn_tex_r1` has `AHRS_EKF_TYPE=10` and 6654 `XKF1` rows from 2 lanes. FGO: (a) the **ExtNav route exists today** (EKF3 flies, fusing FGO `ODOMETRY`); (b) **no MAVLink External-AHRS backend exists**, so one would have to be written. | UKF plumbing 2–3. FGO C++ port + route (a) 5–8. Route (b) 4–6 extra. | About 52 `case EKFType::` arms per new type in `AP_AHRS.cpp`. Route (a) means "EKF3 re-filtering the FGO", with double-counted IMU. Route (b) puts a companion attitude into the 400 Hz loop, and External AHRS is compiled out on 2 MB boards. |
| 3 | Tools/Replay for a new DAL-based backend | Partly. Inputs are estimator-agnostic, but the triggers, `core_slow` bits and handler signatures are hard-coded to EKF2/EKF3. **No existing trial is replayable** (`LOG_REPLAY=0`). | 2–4, plus re-flying with `LOG_REPLAY=1` | A log-format change (`FrameType` has 2 spare bits, `core_slow` has none). The backend must read sensors only through `AP_DAL`. |
| 4 | SITL + Gazebo JSON unchanged with custom firmware | Yes. The physics and sensor path does not depend on the estimator. | 0.5 | **Correction to CLAUDE.md:** `AHRS_EKF_TYPE=10` is injected as a default by `SIM_JSON.cpp:410-413` because the iris model sends `<no_time_sync>1</no_time_sync>`. ArduPilot's comment warns the "EKF is likely to diverge" in that mode. Resolve this before any closed-loop run. |
| 5 | Compute, memory and flash on H743 (Copter and Plane) | UKF: yes, about 2–8 % CPU (float to double), under 16 kB RAM, about 25–50 kB flash [E]. **About 270–325 kB flash is free** on CubeOrange/Pixhawk6X for current Copter and Plane builds [V, published `.apj`]. FGO: companion only (GTSAM cannot be linked into ArduPilot). | See item 7 | EKF3 runs in **double** on H7 (`HAL_WITH_EKF_DOUBLE=1`), so the UKF should use `ftype`. Our own commit's size was not measured. |
| 6 | Forward camera and FGO together on a Pi companion | Yes, **only with C++**. Measured on the i7: FGO Python 29 ms/step; camera Python **61 ms/frame** (already over 33 ms on the i7). A Pi 4/5 needs C++ GTSAM and a C++ RANSAC, and possibly half resolution or a 10 Hz heading rate [E]. Heading can reach EKF3 through ExtNav yaw; yaw rate has no EKF3 input. | 2–4 camera port, +1–2 yaw-rate handler (the FGO port is counted in row 2) | The 5° ExtNav yaw floor (`Measurements.cpp:1118`). A NaN position drops the whole sample. Changing resolution or rate breaks the frozen Phase 3 calibration. Thermal throttling. |
| 7 | Effort and risks | UKF onboard 4–8 pw. Companion FGO (C++ GTSAM + route a) 5–8 pw. Route b adds 4–6. | Total about 18–30 pw [E] (see the §7 table) | UKF: delayed-horizon and output predictor, PD loss. FGO: companion latency and timestamps, real-time jitter on Linux, the fairness of cascaded estimation. |
| 8 | Closed-loop test design | Feasible, but current blank-floor behaviour is **not survivable** in a 20 m corridor. | 2–3 (harness and metrics) | Under SIM the failsafes are silent (`AP_AHRS_SIM.cpp:117-131,183-193`). `crash_check` will not detect a wall scrape. Displacement ratio 0.2 implies about 5× the commanded ground speed. |
| 9 | Fair "clear case" for the FGO over EKF3 (existing results) | **Nothing on disk shows the FGO beating EKF3 on ATE.** EKF3 is lower on textured (11/12) and transition (12/12). The best candidates are **distance scale** (EKF3 +6–10 % vs FGO about +1 %, n = 9) and **consistency/NEES** (EKF3 cross-track ±3σ violated 39 %; the FGO covariance has not been logged). | 1–2 (analysis plus logging) | Heading/yaw-rate gains are an information asymmetry unless EKF3 gets ExtNav heading too. The scale mechanism is unexplained. |

---

## 1. Drop-in replacement: the interface EKF3 presents to AP_AHRS

### 1.1 Architecture at this commit [V]

- **EKF2 and EKF3 are not `AP_AHRS_Backend` subclasses.** They are concrete members, `NavEKF2 EKF2; NavEKF3 EKF3;` (`AP_AHRS.h:500-505`). AP_AHRS calls into them directly from `switch (active/configured EKFType)` blocks.
- **DCM, SIM and External are `AP_AHRS_Backend` subclasses.** The abstract interface is at `AP_AHRS_Backend.h:112-289`. The result struct is `AP_AHRS_Backend::Estimates` (`AP_AHRS_Backend.h:53-108`): attitude (Euler/quat/DCM), gyro estimate and drift, `accel_ef`, accel bias, `velocity_NED`, `vert_pos_rate_D`, location. AP_AHRS copies a backend's results into its state only when that backend is active (`copy_estimates_from_backend_estimates`, `AP_AHRS.cpp:591`; SIM example at `AP_AHRS.cpp:627-635`).
- **So there are two shapes a new estimator can take.**
  - (a) EKF-style: a concrete member with direct calls. This mirrors EKF3 and gives the most complete feature set.
  - (b) `AP_AHRS_Backend` subclass: a cleaner virtual interface, but it still needs a `case` in every AP_AHRS switch (see §2).
  - Option (b) is recommended. Its virtuals already cover the controller-relevant surface: resets, innovations, variances, filter status, pre-arm, origin, and relative position NED/NE/D.

### 1.2 Every call AP_AHRS makes into NavEKF3 [V]

`grep` over `AP_AHRS.cpp` finds 86 `EKF3.` call sites. They are grouped by role below, with the enclosing AP_AHRS function and line.

**Lifecycle and update**
- `set_enable`/`get_enable` in `init` (275, 287).
- `InitialiseFilter` in `update_EKF3` and `reset` (750, 865).
- `UpdateFilter` in `update_EKF3` (754). This is called every AHRS update once started, **whether or not EKF3 is active**.
- `resetGyroBias` (388).
- `Log_Write` (3525).

**Attitude and IMU state, pulled only when active** (`update_EKF3`, 755-793)
- `getRotationBodyToNED`, `getEulerAngles`, `getPrimaryCoreIMUIndex`, `getGyroBias(-1)`, `getAccelBias(-1)`, `getFilterStatus`, which feeds `update_notify_from_filter_status`.
- `getQuaternion` (1285), `getQuaternionBodyToNED` (2745, consistency check).

**Navigation outputs**
- `getLLH` (888, 1410), `getVelNED` (1451, 1609), `getPosNE` (1801, 1869), `getPosD` (1935).
- `getPosDownDerivative` (1723), `getHAGL` (1755), `getWind` (954, 1084), `getAirSpdVec` (1171), `getAirSpdHealthData` (1203), `getActiveAirspeed` (3337).
- `getMagNED`/`getMagXYZ`/`getMagOffsets` (1644, 1676, 2639).
- `getEkfControlLimits` (2589). This gives the ground-speed limit and nav-gain scaler, which matter for optical flow.
- `getHeightControlLimit` (3123).

**Health, status and quality**
- `healthy` (2085, 2326), `getFilterFaults` (2081), `getFilterStatus` (2122, 2477).
- `pre_arm_check` (2418).
- `getVariances` (3256), `getInnovations` (3189), `getVelInnovationsAndVariancesForSource` (3307), `getPosVelUncertainty` (3280).
- `isVibrationAffected` (3212).
- `using_gps` (3605), `configuredToUseGPSForPos/PosXY` (3631, 2123), `using_noncompass_for_yaw` (2784, 3549), `using_extnav_for_yaw` (3576), `use_compass` (1234).
- `send_status_report` (2982, the MAVLink `EKF_STATUS_REPORT`).
- `get_yawEstimator` (3670, 3677; the GSF).

**Origin**
- `getOriginLLH` (800, 3004), `setOriginLLH` (719, 835, 1484), `setLatLng` (1577, from `handle_external_position_estimate`).
- A common-origin mechanism propagates the first origin obtained by any backend to all the others (`AP_AHRS.cpp:794-808` for EKF3, 820-837 for External).
- A state change to "origin ok" is logged, sent as `MSG_ORIGIN` and recorded (`update_state`, `AP_AHRS.cpp:427-445`).

**Lanes and cores**
- `activeCores` (2743, 2763), `getPrimaryCoreIndex` (3415), `getPrimaryCoreIMUIndex` (769, 2674, 3370), `checkLaneSwitch` (3463).

**Resets consumed by controllers**
- `getLastYawResetAngle` (2819), `getLastPosNorthEastReset` (2852), `getLastVelNorthEastReset` (2885), `getLastPosDownReset` (2918).
- `resetHeightDatum` (2942), `requestYawReset` (3495).

**Source switching and tunables**
- `setPosVelYawSourceSet` (3505), `get_active_source_set` (3513), `set_baro_alt_noise` (3655), `setTerrainHgtStable` (3165).

**Push-style measurement inputs** (AP_AHRS forwards these to EKF2 and EKF3)
- `writeOptFlowMeas` (2501), called from `AP_OpticalFlow.cpp:275`.
- `writeExtNavData` (2529) and `writeExtNavVelData` (2551), from `AP_VisualOdom_MAV.cpp:51,80`.
- `writeBodyFrameOdom` (2518), `writeDefaultAirSpeed` (2540), `writeTerrainData` (2567).
- `getOptFlowSample` (2509).

### 1.3 Health and status semantics a replacement must reproduce [V]

- **`nav_filter_status`** (`AP_NavEKF/AP_Nav_Common.h:48-70`) has 19 flag bits: attitude, horiz_vel, vert_vel, horiz_pos_rel, horiz_pos_abs, vert_pos, terrain_alt, const_pos_mode, pred_horiz_pos_rel/abs, takeoff_detected, takeoff, touchdown, using_gps, gps_glitching, gps_quality_good, initalized, rejecting_airspeed, dead_reckoning.
  - Copter reads them through `ahrs.has_status()` (`AP_AHRS.cpp:327`).
  - **In our GNSS-denied, flow-only configuration**, `ekf_has_relative_position()` gates position modes. It needs `HORIZ_POS_REL` and not `CONST_POS_MODE`, or `PRED_HORIZ_POS_REL` before takeoff (`ArduCopter/system.cpp:280-296`). Altitude needs `VERT_POS`/`VERT_VEL` (`system.cpp:308-311`).
  - A backend that never raises `HORIZ_POS_REL` cannot fly Guided or Loiter.
- **`get_variances()` does not return SI variances.**
  - The AP_AHRS comment defines them as innovations normalised by innovation variance, where 1 is the maximum accepted inconsistency (`AP_AHRS.cpp:3225-3229`).
  - `Copter::ekf_over_threshold()` compares them against `FS_EKF_THRESH` (`ArduCopter/ekf_check.cpp:115-140`). The EKF failsafe (`ekf_check.cpp:29-104`) fires after 10 consecutive failing 10 Hz checks. At 8 fails it calls `request_yaw_reset()`; at 9 it calls `check_lane_switch()` (`ekf_check.cpp:67-77`).
  - A UKF or FGO must output NIS/test ratios on the same scale. Otherwise the failsafe either never fires or fires constantly.
- **`get_innovations()` and `is_vibration_affected()`** feed `Copter::check_vibration()` (`ekf_check.cpp:282-293`).
- **Pre-arm checks.**
  - `AP_Arming_Copter.cpp:452` calls `ahrs.pre_arm_check(mode_requires_position, ...)`.
  - Lines 484-495 check `get_filter_status` and `get_variances` against thresholds.
  - Line 570 checks `ahrs.healthy()`.
  - `AP_AHRS::attitudes_consistent()` (`AP_AHRS.cpp:2704`) compares each active core's quaternion with the primary.
- **Selection health.**
  - `_active_EKF_type()` (`AP_AHRS.cpp:2044-2102`) falls back when EKF3 has not started, is unhealthy, or (with `always_use_EKF()`) has non-zero `getFilterFaults`.
  - For copters the fallback is DCM only in specific cases (`fallback_active_EKF_type`, `AP_AHRS.cpp:2209`).
  - `healthy()` and `getFilterFaults()` therefore decide whether AP_AHRS will use the new estimator at all.

### 1.4 Origin handling [V]

- In GNSS-denied flight the origin comes from `set_origin()` (`AP_AHRS.cpp:1477`), from a GCS `SET_GPS_GLOBAL_ORIGIN` (`GCS_Common.cpp:4382`), or from the recorded origin (`use_recorded_origin_maybe`, `AP_AHRS.cpp:447-449`).
- `ekf_check` does nothing until an origin exists (`ekf_check.cpp:35-39`).
- A new backend must implement `get_origin`/`set_origin` and take part in the common-origin propagation.

### 1.5 Lanes and cores [V]

- **Cores.** `MAX_EKF_CORES 3` (`AP_Nav_Common.h:22`). There is one core per IMU in `EK3_IMU_MASK` (`AP_NavEKF3.cpp:411`). Our trials run `EK3_IMU_MASK=3`, i.e. 2 lanes (log `dsn_tex_r1` PARM).
- **Lane switching** (`NavEKF3::UpdateFilter`, `AP_NavEKF3.cpp:910-1025`):
  - It only happens armed, after 10 s of primary health.
  - It uses relative error scores and `EK3_ERR_THRESH` (642).
  - `EK3_PRIMARY` (721) sets the user primary. `EK3_AFFINITY` (651) binds GPS/baro/compass/airspeed instances to cores.
  - Yaw and position reset data are updated on a lane switch (`updateLaneSwitchYawResetData`, 2063).
  - Copter resets attitude targets when `get_primary_core_index()` changes (`ekf_check.cpp:259-265`).
- **CPU cooperation.** A lane skips its prediction if 1/3 of the loop budget has already been used (`AP_NavEKF3.cpp:918-929`; `AP_DAL::ekf_low_time_remaining`, `AP_DAL.cpp:323-340`).
- **For a new backend.** A single-lane UKF/FGO can report `get_primary_core_index()=0` and never switch. That is acceptable, but it gives up IMU redundancy, and this should be stated in the methodology.

### 1.6 Resets used by controllers [V]

- `AC_PosControl` shifts its targets on position resets: `getLastPosNorthEastReset` at `AC_PosControl.cpp:1686,1694`, `getLastPosDownReset` at 1729, 1737.
- `Copter::check_ekf_reset()` calls `attitude_control->inertial_frame_reset()` on a new yaw-reset timestamp (`ekf_check.cpp:249-257`).
- A UKF/FGO that re-anchors yaw or position (for example the FGO's window re-solve or marginalisation) **must report those jumps as resets**, with a timestamp and delta. Otherwise the controllers will chase a step.

### 1.7 Inputs EKF3 takes through AP_DAL [V]

EKF3 holds `AP_DAL &dal` (`AP_NavEKF3.h:387`, `AP_NavEKF3_core.h:494`). The accessors it uses (grep over `libraries/AP_NavEKF3`, accessor definitions in `AP_DAL.h`) are:

| Group | Accessors |
|---|---|
| IMU | `dal.ins()` (`AP_DAL.h:152`): `get_delta_angle`, `get_delta_velocity`, `get_gyro`/`get_accel`, `use_gyro`/`use_accel`, `get_loop_rate_hz` (`AP_DAL_InertialSensor.h:20-38`) |
| Baro | `dal.baro()` (153) |
| GPS | `dal.gps()` (154) |
| Compass | `dal.compass()` (176) |
| Rangefinder | `dal.rangefinder()` (157) |
| Airspeed | `dal.airspeed()` (162) |
| Beacon | `dal.beacon()` (166) |
| Visual odometry | `dal.visualodom()` (171) |
| Optical flow | `dal.opticalflow_enabled()` (228). The flow **samples** are pushed through `AP_AHRS::writeOptFlowMeas` → `NavEKF3::writeOptFlowMeas` → `dal.writeOptFlowMeas` (237) and logged as `ROFH`. They are not pulled. |
| Pushed data | `writeExtNavData`/`writeExtNavVelData`/`writeBodyFrameOdom`/`writeWheelOdom`/`writeTerrainData` (240-248) |
| Vehicle state | `get_armed`, `get_takeoff_expected`/`set_takeoff_expected`, `get_touchdown_expected`, `get_fly_forward`, `get_vehicle_class`, `get_trim`, `get_rotation_vehicle_body_to_autopilot_body`, `get_home`, `get_EAS2TAS`, `get_time_flying_ms`, `airspeed_sensor_enabled` |
| System | `millis`/`micros`, `available_memory`, `malloc_type`, `ekf_low_time_remaining`, `start_frame`, `log_event*`, `log_SetOriginLLH`, `log_SetLatLng`, `log_writeEulerYawAngle`, `snprintf` |

- `AP_DAL::start_frame` (`AP_DAL.cpp:25-117`) snapshots all of these once per IMU frame and writes them as replay blocks.
- A second estimator calling `start_frame` in the same IMU frame only ORs in its frame-type bit (`AP_DAL.cpp:36-39`). Several DAL consumers can therefore share one frame.

### 1.8 What AP_AHRS consumers require from the active estimator [V]

Callers found by grep over `ArduCopter`, `AC_AttitudeControl`, `AC_WPNav`, `AP_InertialNav` and `AC_PrecLand`:

- **Attitude controller.** Quaternion and rotation (`get_quat_body_to_ned`, 10 sites), roll/pitch/yaw and their trig (`sin_yaw`/`cos_yaw`, 17 sites each), `get_gyro`/`get_gyro_latest`, `getLastYawResetAngle`.
- **Position controller and inertial nav.** `get_relative_position_NED_origin`, `get_velocity_NED`, `get_accel_ef`, `getCorrectedDeltaVelocityNED`, `getLastPos*Reset`, `get_vert_pos_rate_D`.
- **Flow-specific.** `getControlLimits` (the ground-speed limit and gain scaler applied when flying on flow).
- **Failsafes.** `get_variances`, `get_innovations`, `is_vibration_affected`, `request_yaw_reset`, `check_lane_switch`, `get_primary_core_index`, `has_status(*)` (14 sites), `get_origin`.
- **Arming.** `pre_arm_check`, `healthy`, `get_filter_status`, `get_variances`, `attitudes_consistent`.
- **Modes.** Throw needs `ATTITUDE_VALID`/`HORIZ_POS_ABS`/`VERT_POS` (`mode_throw.cpp:255-261`). The GPS-glitch and dead-reckoning events read `GPS_GLITCHING`/`DEAD_RECKONING` (`events.cpp:312,334`).

**A second output requirement.** EKF3 fuses on a **delayed time horizon** and runs an output predictor to give current-time states (`storedOutput`, `AP_NavEKF3_core.cpp:160`). The offline UKF/FGO work at measurement time. An onboard drop-in needs an equivalent current-time output with low latency, because the 400 Hz attitude loop consumes these values. This is extra design work beyond porting the filter.

### 1.9 ArduPlane quadplane (Q modes) as well as Copter [V]

The target is also an ArduPlane QUADPLANE flown in Q modes indoors. What differs from Copter:

**Same interface, different vehicle binary.**
- Plane has its own `GOBJECTN(ahrs.EKF3, NavEKF3, "EK3_", NavEKF3)` (`ArduPlane/Parameters.cpp:931`, versus `ArduCopter/Parameters.cpp:475`). A UKF parameter group must therefore be registered in **both** vehicles.
- "One build with parameter selection" means **one build per vehicle** (arducopter, arduplane), each selecting the estimator with `AHRS_EKF_TYPE`. That is normal for ArduPilot.
- The quadplane's VTOL controllers are the same `AC_PosControl`/`AC_AttitudeControl` libraries. They consume yaw and position resets the same way: `quadplane.cpp:1084` (`getLastYawResetAngle`) and `quadplane.cpp:2320,2776` (`getLastPosNorthEastReset`).
- Plane gets its position from `ahrs.get_location()` (`ArduPlane/Plane.cpp:1061`), so an origin is mandatory, as in GNSS-denied Copter.
- Plane has its own EKF failsafe, `Plane::ekf_check()` (`ArduPlane/ekf_check.cpp:30ff`). It uses `get_variances()` (line 119) with the same ratio semantics (§1.3), and is armed-only (line 42).

**DCM fallback is a Plane-only hazard.**
- Plane sets `VehicleClass::FIXED_WING` for every airframe, including quadplanes (`ArduPlane/system.cpp:439-440`). `fly_forward` is false in VTOL phases (`ArduPlane/Plane.cpp:540-567`).
- For `FIXED_WING`, `_active_EKF_type()` applies an extra fallback to DCM (`AP_AHRS.cpp:2104-2200`):
  - DCM is forced if the active filter lacks attitude, vertical velocity or vertical position (2141-2146).
  - When armed and in `const_pos_mode` it falls back to DCM (2176-2184).
  - It falls back if `!horiz_vel` or neither `horiz_pos_abs` nor `horiz_pos_rel` is set (2186-2199).
- All of this is skipped only if DCM cannot supply yaw: `can_use_dcm = dcm.yaw_source_available() || fly_forward` (2140). `yaw_source_available()` is `compass().use_for_yaw()` (`AP_AHRS_DCM.cpp:1328-1331`). Alternatively it is skipped if `AHRS_OPTIONS` bit 1 `DisableDCMFallbackVTOL` is set (`AP_AHRS.h` Options enum; `AP_AHRS.cpp:2148-2153`).
- **Implication for GNSS-denied indoor Q flight:**
  - With `COMPASS_USE*=0` (the nomag configuration), DCM has no yaw source in VTOL, so the fallback is inert.
  - With a compass in use, set **`AHRS_OPTIONS` bit 1**. Otherwise EKF3's (or the UKF's) start-up `const_pos_mode` period would hand a hovering quadplane to DCM, which has no horizontal position without GPS.
  - A new UKF `EKFType` must be added to this switch (2110-2136) too, reporting `filt_state` like EKF3.

**Rate and loop** [V].
- `SCHEDULER_DEFAULT_LOOP_RATE` is 400 for Copter and 50 otherwise (`AP_Scheduler.cpp:43-47`). Plane raises the default to **300 Hz when `Q_ENABLE` is set** (`ArduPlane/Parameters.cpp:1365-1369`, `set_default_by_name("SCHED_LOOP_RATE", 300)`).
- EKF3 uses `dtEkfAvg = MAX(1/loop_rate, EKF_TARGET_DT)` = 0.012 s and triggers a prediction once the accumulated delta-angle time reaches `0.012 − dtIMU/2` (CLAUDE.md trace). At 300 Hz that is **4 frames = 0.0133 s (75 Hz)** [derived], against Copter's 5 × 2.5 ms = 0.0125 s (80 Hz).
- **So the UKF's "predict at EKF3's 0.0125 s, NSE unchanged" matching is Copter-specific.** On a quadplane, the UKF must accumulate IMU frames by the same rule (i.e. match `dtEkfAvg` and the trigger per vehicle) for the NSE values to transfer unchanged.

---

## 2. Selection and shadow running

### 2.1 Selection [V]

- **The enum.** `enum class EKFType : uint8_t { DCM=0, THREE=3, TWO=2, SIM=10, EXTERNAL=11 }` (`AP_AHRS.h:472-488`). Each value is individually guarded by `AP_AHRS_DCM_ENABLED`, `HAL_NAVEKF3_AVAILABLE`, `HAL_NAVEKF2_AVAILABLE`, `AP_AHRS_SIM_ENABLED` or `AP_AHRS_EXTERNAL_ENABLED`.
- **Default flags** (`AP_AHRS_config.h`):
  - EKF2 is **off** (`HAL_NAVEKF2_AVAILABLE 0`, lines 27-30).
  - EKF3 is on (33).
  - SIM is on only when `AP_SIM_ENABLED` (37).
  - External requires `AP_EXTERNAL_AHRS_ENABLED` (24), which itself needs `HAL_PROGRAM_SIZE_LIMIT_KB > 2048` (`AP_ExternalAHRS_config.h:6`).
- **The parameter.** `AHRS_EKF_TYPE` (`AP_AHRS.cpp:171-176`, `@Values: 0,2,3,10,11`, default `HAL_AHRS_EKF_TYPE_DEFAULT 3`, line 56-57).
  - `configured_ekf_type()` (1998) canonicalises it. **An unknown value falls back to EKF2 or EKF3** (2030-2041), so a new value must be added there as well.
  - An RC aux function can switch between EXTERNAL and THREE (`RC_Channel.cpp:1931`).

### 2.2 Shadow running: already the default behaviour for EKF3 [V]

- `AP_AHRS::update()` (454) calls `update_SITL()` (491), `update_external()` (495) and **both** `update_EKF3()`/`update_EKF2()` (498-514) every cycle. Only their order depends on `_ekf_type`.
- `update_EKF3()` calls `EKF3.UpdateFilter()` whenever the filter has started (754). It copies results into AHRS state only `if (_active_EKF_type() == EKFType::THREE)` (755).
- The inactive estimator still logs: `Log_Write()` (3519-3525) calls `EKF3.Log_Write()`.
- **Direct evidence.** Trial `dsn_tex_r1` has PARM `AHRS_EKF_TYPE=10`, `EK3_ENABLE=1`, `EK3_IMU_MASK=3`, `EK2_ENABLE=0`, and contains **6654 `XKF1` messages** (2 lanes × 3327). EKF3 runs and logs in full while SIM flies the vehicle.
- **Which estimators run is set per estimator, not by AHRS.** `EK2_ENABLE` (`AP_NavEKF2.cpp:139`, default 0) and `EK3_ENABLE` (`AP_NavEKF3.cpp:145`, default 1) are each `AP_PARAM_FLAG_ENABLE` and need a reboot. `AHRS_EKF_TYPE` only chooses which output is used.
- The ArduPilot docs confirm EKF2 and EKF3 can run in parallel and advise reducing `IMU_MASK` if CPU is short (https://ardupilot.org/copter/docs/common-apm-navigation-extended-kalman-filter-overview.html).

### 2.3 What adding `EKFType::UKF` requires [V for the counts, E for the effort]

*Under the 29 Sep scope an onboard FGO `EKFType` is out of scope, because the FGO runs on the companion (§2.5). The counts below apply per new type, so they apply to the UKF.*


- **`AP_AHRS.cpp`** has **55 `switch` statements**. It has 53 `case EKFType::THREE`, 52 `case EKFType::SIM` and 52 `case EKFType::EXTERNAL` arms. Expect **about 52 new arms per new type** in this one file. Many can be delegated to a shared backend helper if the new estimators subclass `AP_AHRS_Backend`.
  - `AP_AHRS.h` and `AP_AHRS_Logging.cpp` contain 0 `case EKFType::` arms.
- **Other files that touch `EKFType::`:** `RC_Channel.cpp:1931`, `GCS.cpp:538` (SIM check), `AP_ExternalAHRS.cpp:304`, `APM_Control/examples/...` (test only).
- **Also required:**
  - The enum and parameter `@Values` (`AP_AHRS.h:472`, `AP_AHRS.cpp:174`).
  - `configured_ekf_type()`, `_active_EKF_type()` and `fallback_active_EKF_type()`.
  - The `update()` call site and the active-type GCS text (`AP_AHRS.cpp:536-560`).
  - A parameter group registered in the vehicle's `Parameters.cpp`, mirroring `GOBJECTN(ahrs.EKF3, NavEKF3, "EK3_", NavEKF3)` at `ArduCopter/Parameters.cpp:475`.
  - Log structures.
  - A build flag (for example `AP_AHRS_UKF_ENABLED`) plus entries in `Tools/scripts/build_options.py`/`extract_features.py`.
  - If DAL-based, the DAL changes listed in §3.
- **Shadow running comes for free once `update_<new>()` is called unconditionally,** as `update_SITL()`/`update_external()` already are. **One build with parameter selection is feasible.** The chosen type flies the vehicle and the others run as observers and log.
- **CPU caveat.** Running EKF3 (2 lanes, double), a UKF and an FGO in the same 400 Hz main thread needs the FGO in its own thread (§5, §7).

### 2.4 The External AHRS route [V]

- **Interface.** `AP_ExternalAHRS::state_t` (accel, gyro, quat NED, location, velocity, origin plus `have_*` flags; `AP_ExternalAHRS.h:99-115`). Accessors are at `AP_ExternalAHRS.h:118-133`. The backend virtuals are at `AP_ExternalAHRS_backend.h:30-52`.
- **Transport.** Device-specific **serial binary protocols only**: VectorNav, MicroStrain5/7, InertialLabs, GSOF, SBG, SensAItion (`AP_ExternalAHRS.h`, `DevType` enum). **There is no MAVLink-fed External AHRS device.** A companion-computer FGO would have to either
  - emulate one of those protocols over a UART, or
  - be given a new `AP_ExternalAHRS` backend (for example MAVLink `ODOMETRY` in, with full-state semantics).
- **Not compiled on typical 2 MB H7 boards.** `AP_EXTERNAL_AHRS_ENABLED` needs `HAL_PROGRAM_SIZE_LIMIT_KB > 2048` (`AP_ExternalAHRS_config.h:6`). `HAL_PROGRAM_SIZE_LIMIT_KB = BOARD_FLASH_SIZE` (`AP_HAL/board/chibios.h:29-30`), and Pixhawk6X has `FLASH_SIZE_KB 2048` (`hwdef/Pixhawk6X/hwdef.dat:27`), so it is off unless enabled in the hwdef.
- **SITL does model External AHRS devices** (`libraries/SITL/SIM_VectorNav.*`, `SIM_MicroStrain*.cpp`, `SIM_InertialLabs.*`). A companion-FGO-as-External design could therefore be prototyped in SITL.
- **Docs.** `AHRS_EKF_TYPE=11`, `EAHRS_TYPE` selects the device (https://ardupilot.org/copter/docs/common-external-ahrs.html).
- **Another Linux option, `AP_Module` hooks** (`AP_HAL_Boards.h:262-266`, needs `libdl`). These give **read-only** callbacks: `AHRS_update`, `gyro_sample`, `accel_sample` (`AP_Module.h:45-57`, `AP_Module_Structures.h:30-153`). They are useful for a shadow estimator on a Linux autopilot (Navio2), but cannot drive the vehicle.

### 2.5 How an off-board (companion) FGO estimate can drive flight

The scope is the FGO running GTSAM online on a companion computer (Pi). There are two routes. **Only route (a) exists at `7bac20cbcc` without new firmware code.**

#### Route (a): EKF3 fuses the FGO output as ExternalNav [V]

**Configuration**
- `VISO_TYPE=1` (MAVLink).
- `EK3_SRC1_POSXY=6`, `EK3_SRC1_VELXY=6`, `EK3_SRC1_YAW=6`. `EK3_SRC1_POSZ=6`/`VELZ=6` are optional. The ExternalNav value 6 is in each `@Values` list in `AP_NavEKF_Source.cpp:30-66`.
- Noise floors: `VISO_POS_M_NSE` (0.2 m default), `VISO_VEL_M_NSE` (0.1 m/s), `VISO_YAW_M_NSE` (0.2 rad), `VISO_QUAL_MIN` (`AP_VisualOdom.cpp:91-115`).

**Messages** (handling in §6.2)
- `ODOMETRY` (pose + velocity + covariance + quality). It must be in the `MAV_FRAME_LOCAL_FRD`/`BODY_FRD` frames (`GCS_Common.cpp:4066-4070`).
- Or `VISION_POSITION_ESTIMATE` + `VISION_SPEED_ESTIMATE`.

**What actually flies: EKF3's state.**
- EKF3 treats the FGO pose and velocity as measurements, fused at its delayed horizon with its own IMU prediction. Range height can remain if `EK3_SRC1_POSZ=2`. Flow cannot remain in the same source set (see the note below).
- The controllers read EKF3 (§1.8). The FGO never directly sets the controller state.

**Latency and compensation**
- **Note on sources.** With `EK3_SRC1_VELXY=6`, optical flow is **not** fused for velocity in that source set, because there is one source per slot (`AP_NavEKF_Source.cpp:37`). Flow only returns through a second source set (`EK3_SRC2_*`), switched by RC or Lua. In route (a) EKF3 is therefore IMU + ExtNav (+ range if `POSZ=2`), not IMU + flow + ExtNav.
- **Transport and processing:**
  - The FGO keyframe at t_k is published after its solve, about 5–25 ms on a Pi in C++ [E, §6.5].
  - Serial or UDP MAVLink adds about 1–5 ms [E].
  - Python GTSAM on a Pi would add about 80–150 ms [E].
- **Timestamping.** The companion should stamp `time_usec` with the keyframe (measurement) time. `correct_offboard_timestamp_usec_to_ms()` maps offboard time to local time using a jitter-correction filter and the UART receive time (`GCS_Common.cpp:7373-7388`).
- **`VISO_DELAY_MS`** (default 10, range 0–250, `AP_VisualOdom.cpp:77-83`) is subtracted in `writeExtNavData` (`AP_NavEKF3_Measurements.cpp:1101-1107`, together with half an EKF step). It should represent only the latency the timestamp does not already capture [E; the correct value depends on how the companion stamps, so measure it].
- **Delay bounds.** EKF3 sizes its buffers for the largest sensor delay, with the VISO delay clamped to 250 ms (`AP_NavEKF3_core.cpp:76-83`). It clamps any older sample to the oldest buffered IMU time (`Measurements.cpp:1105`). ExtNav is accepted at no more than 50 Hz (`extNavIntervalMin_ms = 20`, `AP_NavEKF3.h:518`).
- **Output.** EKF3's output predictor then propagates to current time, so the controllers see no extra latency beyond the state error.

**Fairness implications**
- In route (a), "FGO flying" means **EKF3 re-filtering the FGO output**.
- The FGO posterior is time-correlated and already contains the same IMU, flow and range information. EKF3 treats it as white and independent, which double-counts the IMU and makes EKF3 overconfident.
- The floors (0.2 m position unless reduced, 5° yaw, §6.3) further reshape it.
- Any closed-loop result is therefore a property of the **EKF3+FGO cascade**, not of the FGO alone. It is fair to report it as "does feeding EKF3 an FGO estimate help?". It is not fair to present it as "FGO vs EKF3".
- For a like-for-like comparison, the FGO should be evaluated **open-loop** (as now) on the same flown trajectory. Or ExtNav should carry **only the FGO-unique information**, for example the forward-camera heading (§6).

#### Route (b): `AP_ExternalAHRS` bypasses EKF3 [V for the facts, E for the effort]

**No MAVLink or generic companion backend exists at this commit.**
- `DevType` offers VectorNav, MicroStrain5/7, InertialLabs, GSOF, SBG and SensAItion only (`AP_ExternalAHRS.h` enum; `@Values` at `AP_ExternalAHRS.cpp:64`). All of them are UART binary protocols.
- The whole feature is compiled out on 2 MB boards (`AP_ExternalAHRS_config.h:6`), unless it is re-enabled with a hwdef define or `--enable-AHRS_EXT` (`build_options.py:46`).

**What flies:** the external state directly, with no EKF3 involvement.
- `AP_AHRS_External::get_results()` (`AP_AHRS_External.cpp`) copies the external **quaternion** into the AHRS attitude.
- It uses the external gyro and accel if provided, falling back to the local INS.
- Velocity and location come from the device. Relative NED position is computed from `location − origin`.
- **The external attitude goes straight into the 400 Hz attitude controller.** A 30 Hz keyframe-rate FGO attitude is therefore not acceptable here: rate and attitude control need fresh attitude at the loop rate.
- The companion would have to either
  - propagate FGO states forward with IMU at ≥ 200–400 Hz and stream that, which needs a fast IMU link to the companion (`HIGHRES_IMU` is capped at 0.8 × loop rate, 333 Hz, CLAUDE.md), or
  - send its estimate to a new on-FC backend that propagates attitude locally from the gyro.
- `EAHRS_RATE` defaults to 50 Hz (`AP_ExternalAHRS.cpp:73`).

**Adding a MAVLink External-AHRS backend** [E: 4–6 pw]:
- A new `AP_ExternalAHRS_backend` subclass (virtuals at `AP_ExternalAHRS_backend.h:30-52`).
- A hook from `GCS_MAVLINK::handle_message` to deliver `ODOMETRY` (or a custom message) to it. The existing backends read UARTs, not MAVLink.
- Implementations of `healthy()`, `pre_arm_check()`, `get_filter_status()` and `get_variances()` with the §1.3 semantics, plus origin handling.
- On-FC IMU propagation between companion updates, or a high-rate companion stream.
- Latency compensation is the backend's own job; there is no EKF-style delayed horizon.
- An alternative is emulating an existing device protocol (for example VectorNav binary) from the companion. It needs no firmware change, but it is fragile and still requires high-rate attitude.

**Fairness:** route (b) is the only way the FGO's own state flies the vehicle. But it adds the companion link and prediction as confounds, which EKF3 and the onboard UKF do not have. Any difference must therefore be read as "FGO + companion system" against "EKF3 onboard".

#### Recommendation [E]

- **Flying the vehicle:** fly EKF3 (the baseline) or the onboard UKF (drop-in, §2.3).
- **Evaluating the FGO:**
  - online on the companion in **shadow mode**, logging its estimate against ground truth in the same flight, or
  - via route (a) **restricted to FGO-unique information** where the FGO shows a clear case (§9).
- **Route (b)** is only worth building if the FGO clearly beats EKF3 in shadow mode.

---

## 3. Replay

### 3.1 How Replay works [V]

- `Tools/Replay/Replay.h:59-60` instantiates `NavEKF2 ekf2; NavEKF3 ekf3;` with parameter groups `EK2_`/`EK3_` (`Replay.cpp:67,75`).
- The `R*` messages (`RFRH`, `RFRF`, `RFRN`, `RISH`/`RISI` IMU, `RBRH`/`RBRI` baro, `RRNH`/`RRNI` rangefinder, `RGP*` GPS, `RMG*` compass, `RBC*` beacon, `RVOH` visual odometry, `ROFH` flow, `REPH` ext-nav, `REV2`/`REV3` events, and so on) are dispatched by `LogReader.cpp:65ff` to `LR_MsgHandler_*` (`LR_MsgHandler.h:21-256`). The handlers call `AP::dal().handle_message(...)`.
- **The filter trigger.** `AP_DAL::handle_message(const log_RFRF&, NavEKF2&, NavEKF3&)` (`AP_DAL.cpp:444-474`) calls `InitialiseFilter`/`UpdateFilter` on EKF2 or EKF3 according to the `FrameType` bits.
- `--force-ekf2`/`--force-ekf3` remap those trigger bits so that one filter can be replayed on another filter's log (`LR_MsgHandler.cpp:22-41`).
- Push-style inputs are hard-wired to both filters, for example `handle_message(const log_ROFH&, NavEKF2&, NavEKF3&)` (`AP_DAL.cpp:486-493`).
- **Checking.** `Tools/Replay/check_replay.py` compares `XKF*`/`NKF*` outputs between the original and replayed logs (lines 20-22). `check_replay_branch.py` automates this across branches.
- **Docs.** Logs must be captured with `LOG_REPLAY=1` and `LOG_DISARMED=1`. Build with `./waf replay` (https://ardupilot.org/dev/docs/testing-with-replay.html).

### 3.2 Could a new DAL-based backend be replayed? [V for the constraints, E for the effort]

**Yes in principle.** The recorded inputs are estimator-agnostic snapshots of every DAL sensor, frame by frame. A backend that **reads every sensor through `AP_DAL` and nothing else** (no `AP::ins()`, no `AP::ahrs()`) would see identical inputs on replay.

What it needs:

1. **New `AP_DAL::FrameType` bits** (`AP_DAL.h:41-48`). The type is `uint8_t` with 6 of 8 bits used. Two new backends × {Initialise, Update, LogWrite} need 6 bits, so the type must be widened. That changes the `RFRF` log format.
2. **`core_slow`.** `log_RFRF.core_slow` is `uint8_t` (`AP_DAL/LogStructure.h:59-61`). `ekf_low_time_remaining` uses `mask = 1<<(core + etype*4)` (`AP_DAL.cpp:325-326`, `static_assert(MAX_EKF_CORES<=4)`). EKF2 uses bits 0-3 and EKF3 bits 4-7, so **there is no room for a third `AP_DAL::EKFType`** (`AP_DAL.h:116-119`) without widening the field.
3. **New event and origin messages**, or reuse of `REV3`/`RSO3`, and new `LR_MsgHandler` classes.
4. **Handler signatures.** Every `handle_message(..., NavEKF2&, NavEKF3&)` signature needs the new filter objects passed through.
5. **Replay objects.** Add the new filter objects and parameter groups to `Replay.h`/`Replay.cpp`, and extend `check_replay.py` with the new log message names.

**Existing trials cannot be replayed.**
- `dsn_tex_r1`'s PARM has `LOG_REPLAY=0` and `LOG_DISARMED=0`, and its message census contains **no** `RFRH`/`RFRF`/`R*` blocks.
- Every trial intended for replay has to be re-flown with `LOG_REPLAY=1 LOG_DISARMED=1`. This increases log volume [U by how much].
- This would give a strong bit-exact regression harness between the offline Python estimators and an onboard C++ port.

**Effort** [E]: 2–4 pw for DAL/Replay plumbing, plus one re-fly batch.

---

## 4. SITL: custom firmware in the existing SITL + Gazebo JSON setup

### 4.1 The physics path does not depend on the estimator [V]

- `SIM_JSON` receives the Gazebo state (pose, velocity, IMU) and SITL synthesises sensors from it. The only AHRS reference in the SITL physics library is `AP::ahrs().get_EAS2TAS()` (`SIM_Aircraft.cpp:733`), which is an airspeed conversion and irrelevant to a multicopter.
- A firmware built with extra AHRS backends runs the same `build/sitl/bin/arducopter --model JSON` binary interface. Nothing in the ROS bridges (`flow_bridge`, `lidar_bridge`, `imu_bridge`, `attitude_bridge`) depends on the estimator: they inject `OPTICAL_FLOW`/`DISTANCE_SENSOR` or read MAVLink.

### 4.2 The estimator-specific item in the JSON path, and a correction to CLAUDE.md [V]

- **The mechanism:**
  - `SIM_JSON.cpp:406-414`: when the JSON peer reports `no_time_sync`, SITL prints `Forcing use_time_sync=0` and calls `AP_Param::set_default_by_name("AHRS_EKF_TYPE", 10)`. The source comment reads: *"if not using time sync then default EKF type to 10, as otherwise EKF is likely to diverge"*.
  - `~/ardupilot_gazebo/models/iris_with_ardupilot/model.sdf:789` sets `<no_time_sync>1</no_time_sync>`. This line came from upstream `ardupilot_gazebo` commit `65937b7` (Feb 2026), and the plugin sends it in every JSON frame (`ArduPilotPlugin.cc:2011-2012`).
  - With time sync off, `adjust_frame_time()` is skipped (`SIM_JSON.cpp:513,606`). SITL's loop timing is then not matched to the physics step.
- **Consequence 1.** `AHRS_EKF_TYPE=10` in our trials is very plausibly this **injected runtime default**, not only eeprom state. CLAUDE.md's Hidden Configuration Audit §1 attributes it to `eeprom.bin`. None of the thesis `.parm` files, `copter.parm` or `gazebo-iris.parm` set `AHRS_EKF_TYPE` (grep). CLAUDE.md was not edited because this investigation is read-only.
- **Consequence 2: overriding it.** `set_default()` changes the live value only `if (!configured())` (`AP_ParamT.cpp:35-42`). `configured()` means `configured_in_defaults_file() || configured_in_storage()` (`AP_Param.cpp:1426-1430`). So `AHRS_EKF_TYPE=3` in a `--defaults`/`--add-param-file` file, or a stored `PARAM_SET`, should win. **Verify with a PARM readback before any closed-loop run** [U until tested].
- **Consequence 3: a real risk for closed-loop tests.** ArduPilot's own comment predicts EKF divergence without time sync. EKF3 as a passive observer has behaved acceptably offline (METHODOLOGY), but that has not been tested in the loop. Options, not yet tested:
  - (a) set `<no_time_sync>0</no_time_sync>` in the Gazebo model, which is an `ardupilot_gazebo` edit, and re-check RTF and lockstep stability (Known Issue #11 history);
  - (b) keep it and demonstrate empirically that the estimators do not diverge in the loop.
- **Other SITL-only estimator paths:**
  - `SIM_ODOM_ENABLE` makes the SIM backend push body-frame odometry into EKF3 (`AP_AHRS_SIM.cpp:230-252`; `SITL.cpp:528`, default 0). Ensure it stays 0.
  - `SIM_GPS1_ENABLE=0` is already set.
  - SITL adds 10 kB to `available_memory()` (`AP_DAL.h:132-133`), so memory checks are slightly optimistic in SITL.

**Effort** [E]: 0.5 pw to build (`./waf configure --board sitl && ./waf copter`), select the type, and verify parameters, lockstep and RTF.

---

## 5. Compute and memory budget

### 5.1 Platform facts

**STM32H743/H753 (Pixhawk 6X, CubeOrange)**
- Cortex-M7 up to 480 MHz, with single- and double-precision FPU (FPv5-D16). 2 MB flash. About 1 MB RAM: 128 KB DTCM, 64 KB ITCM, 512 KB AXI, plus SRAM1-4 (`hwdef/scripts/STM32H743xx.py:30-37,73`). Datasheet: https://www.st.com/resource/en/datasheet/stm32h743bi.pdf; Pixhawk 6X: https://docs.px4.io/main/en/flight_controller/pixhawk6x [V].
- CubeOrange's clock is quoted as 400 MHz in one secondary source [U].
- Cortex-M7 is rated at 2.14 DMIPS/MHz (Arm Cortex-M comparison table) [V]. No MFLOPS figure was confirmed [U].

**EKF3 runs in double precision on H7 by default [V]**
- `STM32H743xx.py:76` sets `HAL_HAVE_HARDWARE_DOUBLE 1`.
- That becomes `HAL_WITH_EKF_DOUBLE` (`AP_HAL/board/chibios.h:63-64`), which becomes `ftype=double` (`AP_Math/ftype.h:14-15`).
- Linux boards do the same (`AP_HAL/board/linux.h:79-84`).
- **Implication:** a float-only UKF/FGO port on H7 would be *less* numerically capable than the EKF3 it is compared against. Use `ftype`.

**Scheduler [V]**
- `read_AHRS` is a `FAST_TASK` (`ArduCopter/Copter.cpp:127,916-920`), so it runs at `SCHED_LOOP_RATE=400` Hz: 2.5 ms per loop, shared by INS, AHRS, rate controllers and motor output.
- EKF3 predicts at 80 Hz (dt 0.0125 s; CLAUDE.md "EKF3 Prediction dt"). It self-throttles when 1/3 of the loop has been used (`AP_DAL.cpp:323-340`).

**Linux boards**
- Navio2 is supported (`libraries/AP_HAL_Linux/hwdef/navio2/`; https://ardupilot.org/copter/docs/common-navio2-overview.html) [V].
- A Pi 4 (Cortex-A72, 1.5 GHz, 4 cores) is roughly 3–5× slower single-threaded than the i7-8700 [E, general benchmark knowledge, U].

### 5.2 EKF3 reference cost [V for the counts, E for the timing]

- **State:** 24 states (`Matrix24`, `AP_NavEKF_core_common.h:38-41`).
- **Cores:** 2 lanes in our configuration.
- **Memory.** `P` is 24×24 ftype per core, i.e. 4.6 kB in double. There is one static `KHP` shared by all cores (`AP_NavEKF_core_common.cpp:19`). IMU and output ring buffers are sized from the maximum sensor delay (`AP_NavEKF3_core.cpp:88-104`). Cores are allocated with `dal.malloc_type(sizeof(NavEKF3_core)*num_cores, FAST)` (`AP_NavEKF3.cpp:814-822`).
  - `sizeof(NavEKF3_core)` could not be read because the SITL binary is stripped [U].
  - [E] Roughly 15–30 kB per core in double, based on P, the ring buffers (`imu_buffer_length` ≈ 260/12+1 entries of IMU and output state) and about 100 scalar and vector members.
- **Per-predict work.** The auto-generated `CovariancePrediction` (`AP_NavEKF3_core.cpp:1009-1808`) contains about **1485 multiplies, 1017 adds and 560 subtracts** (a literal operator count), so about 3k flops. Strapdown and constraint steps add a few hundred.
- **Per-scalar-fusion work** [E]: Kalman gain (24) plus a `KHP` 24×24 update over the non-zero H columns, about 3–6k flops each.
- **Total** [E]: about 8–12k flops per core per 12.5 ms step. With 2 cores at 80 Hz that is about 1.5–2 Mflop/s in double. Assuming 2–4 cycles per double flop on M7 including load/store (not confirmed), that is **about 40–100 µs per core-step**, i.e. about 1–3 % CPU. This is consistent with EKF3 running comfortably on H7 at 400 Hz [E].

### 5.3 UKF: 15 states on H7 [E]

The basis is `ukf_core.py`:
- Van der Merwe sigma points: 2n+1 = **31**.
- A fresh Cholesky of P at every predict and every scalar update (`ukf_core.py:41-56,111-121,123-141`).
- Flow is two sequential scalar updates (`ukf_core.py:205-220`). Range and a gated pseudo-yaw are scalar updates.
- Heading and yaw-rate updates are also scalar (`ukf_core.py:244-277`).

| Step | Work | Flops (approx.) | Transcendentals |
|---|---|---|---|
| Cholesky 15×15 | n³/6 FMA | 1.1k | 15 sqrt |
| Sigma generation | 30×15 | 0.5k | — |
| 31 × `_process` | Rodrigues + Euler→R + R·R + R→Euler + R·dv | 31 × ~200 = 6.2k | 31 × ~10 = 310 |
| Mean (circular for 3 angles) | | 1k | ~190 |
| Covariance: 31 outer products | | 7k (symmetric) to 14k | — |
| **Predict total** | | **~16–23k** | **~500** |
| Scalar update (flow axis, range, yaw) | Cholesky + 31 h(x) + Pxz + rank-1 P update | ~4k | ~200 |

- **Per second:** 80 predicts plus about 30 Hz × (2 flow + 1 range) plus about 7 Hz yaw, i.e. about 100 scalar updates per second. That gives about **1.6–2.3 Mflop/s + 0.4 Mflop/s**, plus about 60k transcendentals per second.
- **Float on H7:** assuming about 2 cycles per flop effective and about 60 cycles per `sinf`/`atan2f`, that is about 8–12 M cycles/s, **i.e. about 2–3 % of 480 MHz**. The worst single predict is about **0.1–0.15 ms**, well inside a 2.5 ms slot.
- **Double on H7:** assume about 2–3× that, i.e. about **5–8 % CPU and about 0.3–0.4 ms per predict**. This is still acceptable but no longer negligible.
- **Cheaper variants:** a square-root UKF with a rank-1 Cholesky update/downdate between the scalar updates, or reusing sigma points between the X and Y flow axes, would cut the update cost by about 2×.
- **Memory:** P (15×15), sigma matrix (31×15), propagated sigma (31×15), and weights. That is about 1.2k scalars, i.e. **about 5 kB float / 10 kB double**. Delayed-horizon ring buffers matching EKF3's (IMU deltas and output states over about 260 ms at 80 Hz, about 22 entries × ~20 scalars) add **about 2–4 kB**. The total is **under 16 kB**, comfortably inside the H7's RAM.
- **Numerical note:** at x ≈ 160 m, float gives about 1e-5 m position resolution, which is fine. Covariance positive-definiteness in float is the real risk, because Cholesky fails if P loses PD. Use double or a square-root form.

### 5.4 FGO

**Current Python/GTSAM implementation** (`fgo_core.py`)
- Per keyframe it keeps Pose3 (6) + Velocity (3) + imuBias (6) = **15 variables**.
- Window 0.25 s at 30 Hz is about **7–8 keyframes, i.e. about 120 variables**.
- `CombinedImuFactor` connects consecutive keyframes (preintegrating every 333 Hz sample). There are custom flow, range and yaw-prior factors, each with **central-difference numerical Jacobians** (`factors.py:118-140`).
- The solver is `BatchFixedLagSmoother` with LM capped at 2 iterations (`fgo_core.py:55-58`).
- It measures **27 ms/step** on the i7-8700 (METHODOLOGY:706). Python `CustomFactor` overhead dominates that figure.

**(a) GTSAM on a Linux controller or companion** [V for the build facts, E for the timing]
- **Build dependencies.** GTSAM 4.2 **requires Boost ≥ 1.65** and CMake. TBB and MKL are optional. Eigen is bundled (https://raw.githubusercontent.com/borglab/gtsam/4.2.0/INSTALL.md).
- **Cannot be linked into the ArduPilot process.** ArduPilot builds with `-std=gnu++11 -fno-exceptions` (`Tools/ardupilotwaf/boards.py:383-387`, generic `Board`) and `-fno-rtti` on several targets. GTSAM uses exceptions (for example indeterminate-system exceptions) and newer C++. It must run as a **separate process**, on a Navio2 Pi next to ArduPilot or on a companion computer, and talk MAVLink or UART.
- **Timing on a Pi** [E]:
  - A C++ port with analytic Jacobians (no Python) is expected to be 5–20× faster than the 27 ms Python figure, i.e. about 2–5 ms on the i7.
  - On a Pi 4 (about 3–5× slower) that is about **5–25 ms per keyframe**, so the 33 ms budget is plausible. A Pi 3 would be about 2× slower again (marginal).
  - The current Python implementation on a Pi would be about 80–150 ms and **over budget**.
  - Memory: GTSAM and Boost shared libraries are tens of MB, which is fine on a Pi's 1–8 GB.
- No published GTSAM-on-Pi timing was found [U].

**(b) Fallback only: a bespoke fixed-lag smoother on the H7.** This is a C++ Gauss–Newton smoother over about 8 keyframes × 15 states, with capped iterations and preallocated storage, running in its own thread. It is judged possible [E], but the supervisor's direction is to put the FGO on a companion computer. It is therefore not budgeted here.

**Verdict.** Under the supervisor's scope, the FGO runs online with GTSAM on a companion computer (Pi class) as a separate process. §2.5 covers how its estimate can reach the flight controller, and §6.5 covers the compute budget.

### 5.5 Flash budget on H743 boards (Copter and Plane) [V for the sizes, E for the UKF]

**Published builds** (`image_size` and `flash_free` from the `.apj` JSON at firmware.ardupilot.org, fetched 29 Sep 2026; these are not our commit, but they indicate the current default feature set):

| Build | Board | image_size (B) | flash_total | flash_free |
|---|---|---|---|---|
| Copter stable (dbe79216) | CubeOrange | 1,644,436 | 1,966,080 | **321,644** |
| Copter stable | Pixhawk6X | 1,679,428 | 1,966,080 | **286,652** |
| Plane stable (incl. QuadPlane) | CubeOrange | 1,640,968 | 1,966,080 | **325,112** |
| Plane stable | Pixhawk6X | 1,674,616 | 1,966,080 | **291,464** |
| Copter latest (e3d4be86) | CubeOrange / Pixhawk6X | 1,650,220 / 1,693,148 | 1,966,080 | 315,860 / 272,932 |
| Plane latest | CubeOrange / Pixhawk6X | 1,644,908 / 1,686,820 | 1,966,080 | 321,172 / 279,260 |

URLs: `https://firmware.ardupilot.org/{Copter,Plane}/{stable,latest}/{CubeOrange,Pixhawk6X}/{arducopter,arduplane}.apj`.

- The 1,966,080 B limit is 2048 KB minus the 128 KB bootloader reservation (`hwdef/Pixhawk6X/hwdef.dat:20,27`).
- **About 270–325 kB is free** with the standard feature set.
- The size of our own `7bac20cbcc` build for these boards was not measured, because no firmware was built.

**UKF cost in flash and RAM** [E]
- **Code:** the Python core is about 480 lines (`ukf_core.py` 277 + `measurement_models.py` 205). A C++ port plus AP_AHRS plumbing (about 52 switch arms, §2.3), parameters, logging, status, resets and the output predictor is likely **about 25–50 kB of Thumb-2** (double math shares the existing libm/EKF3 routines). That fits within the 270 kB margin.
- **RAM:** at 15 states it is **about 5 kB float / 10 kB double per lane**, plus about 2–4 kB of delayed-horizon buffers (§5.3). One lane is enough for the thesis. Two lanes to mirror `EK3_IMU_MASK=3` would be about 25–30 kB in double. EKF3 itself is estimated at about 15–30 kB per lane (§5.2, [E]).
- **Replay/DAL support** (§3) adds a few kB of log structures.

**What can be compiled out** if needed, using `./waf configure --disable-<feature>` (from `build_options.py`, wired in `wscript:97-125`) or `define X 0` in a custom hwdef:
- Already off by default: EKF2 (`HAL_NAVEKF2_AVAILABLE`, `build_options.py:45`, default 0).
- Candidates irrelevant indoors: ADSB (80-84), AIS (85), EFI (123-128), MSP/OSD families (113-120), CRSF/Spektrum/LTM telemetry (88-93), EKF3 wind/drag fusion (`EKF3_WINDEST`, 56), EKF3 SRTM flow (58), and scripting, camera/mount, terrain, parachute and gripper families (further down `build_options.py`; not individually sized here [U]).
- **Keep:** `EKF3_OPTFLOW` (57), `EKF3_EXTNAV` (55) and `VISUALODOM` (54), which the flow and ExtNav routes need.
- Size impact can be measured with `Tools/scripts/size_compare_branches.py` (elf_diff) and `Tools/scripts/build_sizes/`.
- **External AHRS (route b) would need to be enabled, costing flash,** while unused External AHRS device drivers are disabled.

---

## 6. Forward camera onboard

### 6.1 Where the image processing runs [V/E]

- The OpenCV vanishing-point and flow pipeline on 640×480 at 30 Hz is not feasible on the flight controller. ArduPilot has no image-processing framework and the H7 has no camera interface in the ArduPilot HAL [E]. It must run on:
  - a companion computer (Pi 4/5, Jetson), or
  - a smart camera. ArduPilot documents OpenMV as a MAVLink optical-flow sensor (`FLOW_TYPE=5`, `SERIALx_PROTOCOL=1`; https://ardupilot.org/copter/docs/common-openmv-optflow.html) and as a precision-landing source (`LANDING_TARGET`). Whether an OpenMV H7 can run the VP pipeline at 30 Hz is [U].
- The result should reach the autopilot as a small MAVLink message.

### 6.2 Candidate MAVLink messages and how GCS_Common handles them at this commit [V]

| Message | Handler | Path into EKF3 |
|---|---|---|
| `VISION_POSITION_ESTIMATE` | `GCS_Common.cpp:4562` → `handle_vision_position_estimate` (4023) → `handle_common_vision_position_estimate_data` (4092-4119). posErr and angErr come from covariance diagonal indices [0,6,11] and [15,18,20]. | `AP_VisualOdom_MAV::handle_pose_estimate` (`AP_VisualOdom_MAV.cpp:28-60`) → `AP::ahrs().writeExtNavData` (51) |
| `ODOMETRY` | 4574 → `handle_odometry` (4055-4087). **Only `MAV_FRAME_LOCAL_FRD`/`BODY_FRD` is accepted** (4066-4070). Velocity is rotated by the supplied quaternion. | Pose via `handle_pose_estimate`, velocity via `writeExtNavVelData` |
| `ATT_POS_MOCAP` | 4578 → `handle_att_pos_mocap` (4121-4143). No reset counter. | `handle_pose_estimate` |
| `VISION_SPEED_ESTIMATE` | 4582 → 4145 | `writeExtNavVelData` |
| `GLOBAL_VISION_POSITION_ESTIMATE`, `VICON_POSITION_ESTIMATE`, `VISION_POSITION_DELTA` | 4566, 4570, 4558 | ExtNav / body-odometry |
| `NAMED_VALUE_FLOAT` | 4645 → `handle_named_value` (3882-3900). **It only logs `NVAL`.** | None |
| `DEBUG_VECT` | **No handler in `GCS_Common.cpp`** (grep finds none), so it is dropped. | None |
| Custom message | Needs a dialect change plus a handler. Lua scripting can receive arbitrary message IDs (`mavlink:register_rx_msgid`, `AP_Scripting/.../bindings.desc:1054-1056`), but no EKF3 yaw-injection binding was found [U]. | — |

All of the vision-pose handlers are compiled only under `HAL_VISUALODOM_ENABLED` (`GCS_Common.cpp:4557-4585`).

### 6.3 The ExtNav yaw path, and its constraints [V]

- **Configuration.** `EK3_SRC1_YAW=6` (ExternalNav) with `VISO_TYPE=1` (MAVLink). The docs confirm ExtNav yaw (https://ardupilot.org/copter/docs/common-vio-tracking-camera.html).
- **Samples with a NaN position are dropped whole, yaw included.** `NavEKF3_core::writeExtNavData` returns early if `pos.is_nan() || isnan(posErr)` (`AP_NavEKF3_Measurements.cpp:1076-1078`). The camera must therefore send a finite dummy position with a large posErr.
- **Two error floors apply:**
  1. `angErr` is constrained to `[VISO_YAW_M_NSE, 1.5]` (`AP_VisualOdom_MAV.cpp:43`); posErr likewise to `[VISO_POS_M_NSE, 100]` (42).
  2. **EKF3 floors the yaw sigma again at 5°**: `MAX(angErr, radians(5.0f))` (`AP_NavEKF3_Measurements.cpp:1118`). The camera's per-frame confidence therefore cannot express sub-5° accuracy.
- **Quality gate.** Samples are consumed only if `quality >= VISO_QUAL_MIN` (`AP_VisualOdom_MAV.cpp:47-51`). `ODOMETRY` carries a `quality` field; `VISION_POSITION_ESTIMATE` passes 0.
- **Is the dummy position harmless?** It is not fused as a measurement when POSXY is not EXTNAV:
  - `readyToUseExtNav()` returns false unless `getPosXYSource()==EXTNAV` (`AP_NavEKF3_Control.cpp:613-621`).
  - Fusion is gated on `posxy_source == EXTNAV` (`AP_NavEKF3_PosVelFusion.cpp:582,634`).
  - **However, `ResetPosition()` will use ExtNav data as a "third preference" if it is less than 250 ms old and the reset source is DEFAULT** (`AP_NavEKF3_PosVelFusion.cpp:157-162`). A dummy (0,0) position could therefore be written into the state on a position reset. **Mitigations:** send a position consistent with the EKF (for example, echo the current estimate), or confirm which reset paths can occur with POSXY=None [U; needs a targeted test].
- **Yaw rate.** **There is no EKF3 input for an external yaw-rate measurement.** Body-frame odometry does accept `delAng`: `writeBodyFrameOdom` stores `bodyOdmDataNew.angRate` (`AP_NavEKF3_Measurements.cpp:133`). But grep over `libraries/AP_NavEKF3` finds no fusion use of that field; the only other `angRate` uses are IMU-derived lever-arm corrections (`AP_NavEKF3_PosVelFusion.cpp:422,479`). A camera yaw rate cannot be fused by EKF3 without code changes.
- **`writeEulerYawAngle` is an alternative heading path, but not a ready one.**
  - `NavEKF3::writeEulerYawAngle` exists (`AP_NavEKF3.h:243`, `AP_NavEKF3.cpp:1649-1656`), but **`AP_AHRS` has no forwarder and no MAVLink message reaches it**. Its only in-tree caller is the GPS-yaw path (`AP_NavEKF3_Measurements.cpp:751`).
  - Its buffer `storedYawAng` is only allocated when `sources.gps_yaw_enabled()` (`AP_NavEKF3_core.cpp:131`).
  - Using it would need a new AHRS method, a MAVLink handler and a buffer-allocation change. That is a firmware change.

### 6.4 How a drop-in backend would consume camera data [E]

- **Heading.** Reuse `AP_VisualOdom`, so the MAVLink handling is unchanged, and add the new backend to the `AP_AHRS::writeExtNavData` fan-out (`AP_AHRS.cpp:2523-2530`). For replayability, log it through a new or existing DAL write (`REPH` already records ExtNav, `AP_DAL.cpp:498-503`). The backend applies its own confidence-scaled R without the 5° floor.
- **Yaw rate.** Needs a new message route. Either
  - repurpose `ODOMETRY`'s angular-rate fields (currently ignored by `handle_odometry`), or
  - add a small dedicated handler and an `AP_AHRS::writeYawRate(...)` fan-out, plus a DAL log block.

**Effort** [E]:
- 2–4 pw for heading via ExtNav into EKF3, since the path already exists. This mainly covers the companion pipeline, timestamps, the dummy position, and testing.
- +1–2 pw for a yaw-rate path into the new backends.

### 6.5 Companion compute: FGO (GTSAM) plus the forward-camera pipeline on a Pi 4 / Pi 5

**Measured on the i7-8700, single-threaded Python:**
- **FGO:** 27 ms/step at 0.25 s window (METHODOLOGY:706). On `fwdc_tex_r1` it is **median 29.2 ms, p99 36.2 ms** per keyframe (`~/thesis_data/batches/eval_fwdc/fgo_fwdc_tex_r1.log`, `[timing]` line), at about 10,000 keyframes over 300 s, i.e. 33 Hz. This is Python `CustomFactor` with central-difference Jacobians (`factors.py:118-140`), LM capped at 2 iterations.
- **Forward camera, frozen configuration** (`fwd_measure.py`: LSD + RANSAC VP with 300 iterations + LK; frozen tolerance 0.5°, box 80 px from `eval/results/fwd_calibration.json`):
  - This was a read-only timing run of the existing measurement functions, done for this report: 300 frames (index 3000–3299) of `fwdc_tex_r1`, `cv2.setNumThreads(1)`, no outputs written, no estimator run.
  - **Caveat: it was measured under heavy concurrent load.** `uptime` load average was 28.8 on 12 threads, with several `python` processes at 300–440 % CPU (Phase 4 jobs). **Treat the figures as upper bounds, especially the p99.** The pure-Python RANSAC cost is structural, so the conclusion stands.
  - **Median 61.0 ms/frame** (LSD 14.9 ms, VP-RANSAC in Python 38.6 ms, yaw-rate LK 8.1 ms). **p99 330 ms.**
  - **So even the i7 does not run the Python camera pipeline at 30 Hz** (budget 33 ms). The RANSAC loop is the bottleneck: it is pure-Python per-hypothesis scoring (`fwd_measure.py:90-124`).

**Pi scaling** [E]
- A Pi 4 (Cortex-A72 at 1.5–1.8 GHz) is about 3–5× slower single-threaded than the i7-8700. A Pi 5 (Cortex-A76 at 2.4 GHz) is about 1.5–2.5× slower. These are typical Geekbench/SPEC-class ratios and were not measured [U].

| Workload | i7-8700 (measured) | Pi 4 [E] | Pi 5 [E] |
|---|---|---|---|
| FGO, Python GTSAM, 0.25 s window | 29 ms (batch log, load not recorded) | 90–150 ms, **fails 33 ms** | 45–75 ms, **fails** |
| FGO, **C++ GTSAM**, analytic Jacobians | about 2–6 ms [E: 5–15× less than Python CustomFactor] | 6–30 ms | 3–15 ms |
| Camera, Python (as now) | 61 ms (under load, upper bound) | 180–300 ms, **~3–5 Hz** | 90–150 ms, **~7–10 Hz** |
| Camera, C++/vectorised RANSAC (LSD dominant) | about 20–25 ms [E: LSD 15 + LK 8 + RANSAC < 2] | 60–125 ms | 30–60 ms |
| Camera at 320×240 (LSD cost scales with pixels, about 4× less) | about 6–8 ms [E] | 20–40 ms | 10–20 ms |

**Conclusions** [E]
- **The FGO fits a Pi 5 (and probably a Pi 4) only as C++ GTSAM with analytic Jacobians.** The Python implementation will not meet 30 Hz on either board.
- **The camera pipeline needs a C++ (or vectorised numpy) RANSAC, and either half resolution or a lower heading rate.** For example, heading at 10 Hz and yaw-rate LK at 30 Hz. Four cores allow the FGO and camera to run on separate cores. Total load on a Pi 5 is then about 1.5–2 cores busy at 30 Hz.
- **Changing resolution or rate changes the measurement** relative to the frozen Phase 3 calibration (tolerance 0.5°, box 80 px at 640×480). Re-validation would be required, because the calibration is pre-registered (METHODOLOGY Phase 3).
- **Memory:** GTSAM + Boost + OpenCV is roughly 100–300 MB resident [E], which is fine on a 2–8 GB Pi.
- **Thermals:** sustained two-core load on a Pi 4/5 needs active cooling to avoid throttling [E, general Pi practice].

---

## 7. Effort estimates and main risks [E]

| Work package | pw | Main risks |
|---|---|---|
| Interface spec and test plan (§1) | 0.5 | Missing a semantic (variances as ratios, reset reporting, `HORIZ_POS_REL`, control limits for flow) |
| AHRS plumbing for the UKF `EKFType` in Copter and Plane, params, logging (§2) | 2–3 | Size of the switch surface (about 52 arms per type); flash fits (about 270–325 kB free, §5.5); keeping SITL-only builds separate from flight builds |
| DAL/Replay support (§3) | 2–4 | Log-format change (`FrameType`, `core_slow`); the backend must be DAL-pure |
| SITL bring-up (§4) | 0.5 | `AHRS_EKF_TYPE` default injection; the no-time-sync divergence warning |
| **UKF C++ port** | **4–8** | Delayed-horizon fusion plus an output predictor; PD loss in float (use double or square-root form); Euler singularity (safe in this envelope); producing EKF3-compatible status, variances and resets; per-scalar Cholesky cost spikes |
| FGO on the companion: C++ GTSAM port with analytic Jacobians and a MAVLink `ODOMETRY` publisher (route a) | 5–8 | Solve jitter on Linux (use an RT-prioritised process or isolated core); timestamps (`time_usec` = keyframe time, `VISO_DELAY_MS`); cascaded-estimation fairness (§2.5) |
| (Fallback only) bespoke FGO on the H7 | not budgeted | See §5.4(b) |
| Route (b): a new MAVLink External-AHRS backend plus high-rate companion propagation | 4–6 extra | Transport latency and timestamps; no MAVLink External-AHRS device exists; External AHRS is compiled out on 2 MB boards; the companion is a single point of failure |
| Forward camera companion pipeline plus ExtNav (§6) | 2–4 (+1–2 yaw rate) | 5° floor; dummy-position reset hazard; camera latency (`VISO_DELAY_MS`) |
| Closed-loop harness and metrics (§8) | 2–3 | Wall contact, runaway speeds, overshooting the end of the corridor |
| **Total (UKF onboard + companion FGO via route a + camera + harness)** | **about 18–30** (route b adds 4–6) | |

**FGO-specific risks (companion route):**
- **Real-time behaviour on Linux.** The batch LM step time is data-dependent: p99 is 36 ms against a 29 ms median on the i7, and the p99 on `fwdc_tex_r1` already exceeds 33 ms. Mitigations:
  - cap the iterations (already 2);
  - run on an isolated core with RT priority;
  - publish a stale-flag or quality field so EKF3 (route a) rejects late samples through `VISO_QUAL_MIN`, or so the backend reports unhealthy (route b).
- **GTSAM solver choice.** iSAM2 is unusable with the Python `CustomFactor` in this project (METHODOLOGY:1112-1113, FGO_DESIGN:547-567). A C++ port with native factors should be re-tested with iSAM2 (0.2 ms/step if it works), but that is unproven [U].
- **Numerical robustness.** Double precision on the Pi, so marginalisation in float is not an issue. Indeterminate systems on sensor loss (a blank floor) raise GTSAM exceptions, which the companion process must catch and turn into "unhealthy".
- **Latency and time alignment** between companion and FC (§2.5). A wrong `VISO_DELAY_MS` biases EKF3's fusion (route a) or the controllers (route b).
- **Resets.** When the FGO re-anchors, the `ODOMETRY` `reset_counter` must be incremented so that EKF3 records a position reset (`AP_VisualOdom_MAV.cpp:51`, `get_reset_timestamp_ms`).
- **Single point of failure.** A companion crash or link loss must leave EKF3 (route a) flying on its own sources. That requires source-set switching (`EK3_SRC2_*` with `RCx_OPTION` or Lua) to fall back from ExtNav to optical flow. Route (b) needs an AHRS fallback.
- **Fairness.** In route (a) any closed-loop result is "EKF3 + FGO", not the FGO (§2.5). The FGO-alone comparison should remain open-loop or shadow on the same trajectory.
- **UKF (onboard) risks.** Delayed-horizon fusion plus an output predictor; PD loss (use double or square-root); reproducing EKF3's status, ratio and reset semantics; the Plane DCM fallback (§1.9).
---

## 8. Closed-loop test design implications (report only)

### 8.1 Geometry and contact thresholds [V]

- **Walls.** Static boxes 0.2 × 170 × 5 m at x = ±10, y centred at 80 (`sim/models/corridor_wall/model.sdf`; poses at `corridor_textured.sdf:207-213`). They span y ≈ −5 to 165 with **no end caps**.
- **Ground.** An infinite collision plane. The floor visuals (which the LiDAR sees) are tiles centred y = −10 to 150, covering y ≈ −20 to 160. **Beyond y ≈ 160 the LiDAR returns no-return (41.0)** and EKF3 loses height (Known Issue #6 mechanism).
- **The iris has collision geometry** (`ardupilot_gazebo/models/iris_with_standoffs/model.sdf`):
  - base mesh `iris_collision.stl` (22-28);
  - four leg cylinders (44-120);
  - four rotor cylinders, r = 0.1 m, at (±0.13, ±0.22/0.20) (335-343; rotor poses from the link `<pose>`).
- **Lateral half-span:** about 0.22 + 0.10 = **0.32 m** at yaw ≈ 90°, or up to about 0.36 m at arbitrary yaw.
- **Wall contact from ground truth** is |x_GT| ≥ 9.9 − 0.32 ≈ **9.58 m**, or 9.54 m conservatively. Contact is physical in Gazebo; the rotor cylinders will collide.
- **The JSON plugin has no collision handling of its own** [V: no `contact`/`collision` references in `ArduPilotPlugin.cc`]. A contact is simply physics, typically a tumble.

### 8.2 What ArduCopter detects [V]

- **`crash_check`** (`ArduCopter/crash_check.cpp:4-8,22-95`) disarms only if **lean > 15° and attitude error > 30° for 2 s with filtered acceleration < 3 m/s²**. A wall scrape at 0.5 m/s probably will not trigger it. A tumble after rotor contact probably will. Wall contact must therefore be measured from ground truth, not from ArduPilot events.
- **EKF failsafe** (`ekf_check.cpp`): variance ratios over `FS_EKF_THRESH` or loss of position → `failsafe_ekf_event()`.
  - **Under SIM (type 10) this can never fire.** `AP_AHRS_SIM::get_variances` returns zeros (`AP_AHRS_SIM.cpp:183-193`) and `get_filter_status` reports everything valid (117-131).
  - Closed-loop tests of EKF3, UKF or FGO are therefore the first time these failsafes are exercised. Log `ERR` subsystem `EKFCHECK` and `FS_EKF` events.
- **Vibration check** (`ekf_check.cpp:~270-300`), **thrust-loss/yaw-imbalance checks** (`crash_check.cpp:5-12,110-235`), and **lane changes** (`EKF_PRIMARY` error events).

### 8.3 Error budget against the corridor

- **Aligned vs unaligned error.** The cruise ATEs quoted (EKF3 ~4 m, FGO ~5 m, UKF up to ~22 m) are **`evo -a` SE(3)-aligned** and **understate unaligned drift**. In closed loop, the controller flies the *unaligned* estimate: the vehicle's true lateral offset equals minus the estimator's lateral error. A per-trial **unaligned** lateral error vs time, from the existing offline runs, is the right predictor. It was not computed here [U].
- **Lateral margin** is 9.58 m. A UKF-class error of about 20 m hits the wall. EKF3/FGO-class errors of about 4-5 m (aligned) are survivable only if the unaligned lateral component stays below about 9.5 m over 300 s.
- **Displacement ratios on blank floors.** Under velocity control the true speed is roughly commanded ÷ ratio [E, first-order]:
  - EKF3 at about 0.2 gives about **2.5 m/s true** for 0.5 m/s commanded. That covers the remaining corridor in about 60 s and **overshoots y = 160**, where height aiding is lost.
  - FGO at about 1.5 **under-flies** at about 0.33 m/s.
  - In the loop the dynamics change the flow content, so these ratios will not transfer exactly. This is precisely the in-loop asymmetry the METHODOLOGY decision (fly on SIM truth) was avoiding.

### 8.4 Metrics needed

1. **Corridor completion:** ground-truth y ≥ 160 m reached without a breach, and time to complete.
2. **Physical path deviation from truth:** ground-truth lateral |x_GT| vs time. Report max, RMS, and time above 5 m and above 9.58 m. Also report along-track progress vs commanded.
3. **Wall contact:** the first time |x_GT| ≥ 9.58 m, contact count and duration (optionally from a Gazebo contact sensor), and whether a tumble or disarm followed.
4. **Estimator error in the loop:** unaligned and aligned ATE vs ground truth, the displacement ratio, and velocity error.
5. **ArduPilot events:** EKF failsafe (`FS_EKF`), `EKFCHECK` errors, crash disarm, lane or primary changes, yaw and position resets (these also affect the controller), and mode changes.
6. **Height safety:** LiDAR no-return count, and any ground contact before landing.
7. **A safety envelope for the tests:**
   - a geofence is not possible without GPS (`FENCE` needs a position) [U];
   - use a ground-truth-based kill or land monitor on the ROS side (for example switch to LAND if |x_GT| > 8 m or y_GT > 155 m);
   - use `GUIDED` velocity commands with a speed cap.

---

## 9. Where the FGO could show a clear, fair benefit over EKF3 (existing results only; no new runs)

**Method.** Existing results were read from `METHODOLOGY.md`, `FGO_DESIGN.md` and `eval/results/*.json`, plus FGO logs and `ardupilot.bin` files under `~/thesis_data`. The only additions were read-only calculations over TUM files and JSON. A helper did the bulk of the reading; its figures are reported as it cited them. Numbers marked *(derived)* were computed during this investigation and are not in a committed results file.

**Fairness conditions that apply to every scenario below:**
- The FGO output used is causal: newest keyframe only (`fgo_core.py:137`; FGO_DESIGN §6). So the 0.25 s window gives it no future information over a filter. `/fgo/pose_smoothed` must never be used for headline numbers.
- EKF3 uses its onboard IMU with true delta integration. The UKF and FGO use the bridged 333 Hz IMU with rectangular integration (CLAUDE.md caveat).
- EKF3 runs at ArduPilot defaults. The FGO window of 0.25 s is a declared configuration choice (METHODOLOGY:690-712).

### 9.1 Headline: current three-way results (evo -a cruise, n = 3 per cell, EKF3 / FGO, metres)

| Dataset | Textured | Transition | Blank* |
|---|---|---|---|
| `dsn` | 4.66 / 4.65 | 21.32 / 25.82 | 34.80 / 26.05 |
| `fwd` | 4.31 / 4.80 | 21.88 / 26.02 | 34.59 / 25.79 |
| `fwdc` | 3.80 / 4.69 | 21.75 / 26.04 | 34.62 / 26.24 |
| `fwdplainc` | 4.10 / 4.71 | 21.76 / 26.06 | 34.94 / 25.73 |

Sources: `eval/results/dsn_dejitter_baseline.json`, `phase2_fwd_evo.json`, `fwdc_evo.json`, `fwdplainc_evo.json`.

\*Blank is a failure regime. evo -a is not a quality metric there (METHODOLOGY:465-470).

**Nothing on disk supports "the FGO beats EKF3 on ATE."**
- On textured floors, EKF3 is lower on 11 of 12 bags.
- On transition, EKF3 is lower on 12 of 12.

### 9.2 Candidate scenarios

| # | Scenario | Evidence so far | Fair? | Test that would show it | Judgement |
|---|---|---|---|---|---|
| A | **Distance / velocity scale** | Path-length ratio (estimate/GT, cruise, 20 s resampling) *(derived)*: EKF3 **+5.7 to +9.6 %** (`dsn_tex` 1.096/1.071/1.079; `fwdc_tex` 1.057/1.058/1.058; `fwdplainc_tex` 1.058/1.057/1.059). FGO **+0.9 to +1.1 %** on all 9. Corroborated by `disp_ratio` (`trials.*.est.{EKF3,FGO}.failure.disp_ratio` in the four evo JSONs): EKF3 1.04–1.06, FGO 0.98–0.99 on 12 textured bags. CLAUDE.md's +12.6 % / +4.7 % (METHODOLOGY:1098-1100) is superseded: n = 1, speed-magnitude based, pre-`h_flow`-correction. | **Largely.** Same flow and LiDAR. Live PARM shows correct lever arms (`FLOW_POS_Z` 0.13, `RNGFND1_POS_Z` 0.12) and `EK3_FLOW_DELAY` 10 ms. EKF3 HAGL is unbiased (XKF5 2.29 m vs GT 2.29 m), so height does not explain it. The mechanism is **unexplained**; candidates are EKF3's AHRS-gyro derotation or its terrain-state handling. | On existing data: Sim(3) vs SE(3) ATE (`evo -as` vs `-a`) to separate scale from shape; along-track velocity ratio per 20 s segment; the pending FGO_DESIGN:113 lever-arm acceptance test (≤ 2 %, "not yet run"). Then find the EKF3 mechanism before claiming it. | **Plausible, and the best current candidate.** It does not yet translate into lower ATE. |
| B | **Consistency (NEES, ±3σ coverage, uncertainty reporting)** | EKF3 is overconfident in the unobservable directions (`dsn_tex_r1`, n = 1, pre-correction): cross-track position outside ±3σ **39 %** of the time, cross-track velocity 16 %, yaw 10 % (METHODOLOGY:179-196). XKV1/XKV2 variances exist in every `ardupilot.bin`. **No FGO covariance is on disk**, because the Python `BatchFixedLagSmoother` exposes no marginal (`fgo_core.py:144-150`). The FGO's per-keyframe zero-innovation yaw anchor may make it *more* overconfident in yaw. | Fair only if the FGO covariance is the true smoother marginal of the newest keyframe, not the Phase 4 gate recursion (which is a filtering approximation). | Small logging change (marginal of the newest keyframe via `Marginals` on the window graph, or the C++ API). Then NEES and ±3σ coverage on 9 bags against XKV, per axis, per world. | **Untested; could go either way.** The most thesis-relevant candidate for "uncertainty reporting", and the one EKF3 is known to do badly. |
| C | **Forward-camera heading and yaw rate** (Phase 3/4) | Heading σ about 0.1–0.15° where valid. It fails on plain walls over the checker floor, and gives confident wrong vanishing points within about 25 m of the end wall (METHODOLOGY:2754-2827). Phase 4 is still running (partial outputs only), so there is no result to cite. The ruling makes EKF3 the fixed no-heading baseline (METHODOLOGY:2854-2922). | **Not fair as "FGO vs EKF3".** EKF3 *can* take heading via ExtNav yaw (§6.3), with floors of `VISO_YAW_M_NSE` ≥ 0.05 rad (default 0.2) and a hard 5° floor at `AP_NavEKF3_Measurements.cpp:1118`. Only **yaw rate** is exclusive to our estimators (§6.3). The UKF gains equally, so this is not an FGO-specific benefit. | Fair version: EKF3 + ExtNav heading. Either (i) closed-loop or shadow SITL with the companion sending `ODOMETRY` yaw, or (ii) Replay with `REPH` injected, which needs `LOG_REPLAY=1` re-flights (§3). Then attribute any residual FGO edge to heading precision below 5°, to yaw rate, or to outlier handling. | **Weak as a fair FGO-over-EKF3 claim.** Strong only as "standard EKF3 as configured vs FGO + camera", which must be labelled an information asymmetry. |
| D | **Sensor dropout / textured→blank transition at y = 80 m** | evo -a (cruise) EKF3 21.3 vs FGO 25.8 (`dsn_dejitter_baseline.json`). Divergence onset EKF3 101–103 m vs FGO 95–96 m. Same pattern in `fwd`/`fwdc`/`fwdplainc`, with EKF3 lower on 12/12. The FGO's `disp_ratio` of 0.72 vs 0.56 reflects EKF3 freezing (const_pos, FGO_DESIGN:921-957); the FGO over-travels on the blank half (path ratio 1.27 on `dsn_trans_r1` *(derived)*). | The failure modes differ by design (FGO_DESIGN §9.5), and an onset metric favours a freezer. | A world with a **short blank gap** between textured sections, one gap shorter and one longer than EKF3's 5 s flow-fusion timeout, to test **recovery**. None of the current worlds has a blank→textured recovery. | **Contradicted on existing data.** A recovery test is plausible only after the FGO over-travel issue (OI-1) is resolved. |
| E | **Delayed flow / latency** | The UKF and FGO use capture (header) stamps. EKF3 stamps flow at receipt − `EK3_FLOW_DELAY` − half a frame, leaving about 5 ms (`dsn`) to 11–18 ms (`fwd`) of misalignment (METHODOLOGY:1576-1580, 1751-1756). That asymmetry already *favours* the FGO. The FGO rejects measurements stamped at or before the last keyframe (FGO_DESIGN:754). Out-of-sequence insertion, which is where a smoother would really gain, is not implemented. | EKF3 handles a *known fixed* delay natively. A fair test uses variable or unknown delay. | Implement out-of-sequence insertion in the FGO window. Inject jitter or variable latency into flow. Compare against EKF3 with a fixed `EK3_FLOW_DELAY`. This needs new flights, or replayable ones for EKF3. | **Weak** (not built). |
| F | **Yaw drift** | EKF3 about +8.4 deg/min, FGO −9.24 deg/min; physical drift 9.8 (METHODOLOGY:640, 1067-1072). Gyro-z bias is unobservable for both (METHODOLOGY:648-666). | — | — | **Contradicted.** Drift is set by the anchor, not the estimator. |
| G | **Blank floor** | `disp_ratio` EKF3 0.17–0.22 vs FGO 1.50–1.55. evo -a EKF3 34.8 vs FGO 26.1. Onset EKF3 18 m vs FGO 33–37 m. | evo -a is not a metric in this regime. The FGO's over-travel is unexplained (the pre-correction FGO froze at 0.04–0.18). **In closed loop, inventing 1.5× motion is more dangerous than freezing** (§8.3). | — | **Contradicted as a benefit.** |
| H | **Ceiling datasets** | No effect on downward flow: +0.43 px/s, Welch t = 1.06 (`eval/results/ceiling_flow_effect.json`, `groups.all`). Three-way results match `dsn`. | — | — | **No benefit.** |
| I | **Repeatability across repeats** | The "FGO range 0.17 vs EKF3 2.29" figure is `dsn` only. On `fwd` EKF3's range is smaller (0.26 vs 0.63); on `fwdc` they are equal (0.55). | — | — | **Contradicted as a general claim.** |

### 9.3 Ranking for the supervisor's "clear case" [E]

1. **Scale (A):** cheap, uses existing data, and n = 9–12 are consistent. It becomes claimable once the EKF3 mechanism is identified and a Sim(3) vs SE(3) split shows it matters.
2. **Consistency (B):** needs a small logging change. It directly addresses "uncertainty reporting", where EKF3 is already shown to be overconfident.
3. **Heading or yaw rate (C):** only a fair claim if the EKF3-with-ExtNav-heading arm is run (Replay or SITL), and it is then about yaw rate or sub-5° heading.
4. **Recovery after a short dropout (D-variant):** needs a new world and the over-travel fix.

**Honesty note for any write-up:**
- The FGO is currently **worse** on textured ATE (11/12), on transition (12/12) and in blank-floor over-travel.
- Its compute is marginal: 27.8 ms median / 32.3 ms p99 at 0.25 s (`dsn_tex_r1/fgo/metrics.txt`), and 29.2 / 36.2 ms on `fwdc_tex_r1` (§6.5).
