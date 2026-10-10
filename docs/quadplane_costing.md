# QuadPlane costing: what changes if the vehicle is a VTOL QuadPlane

Status: REPORT ONLY, written 2026-10-11 on `fwd-camera` at `bccbc78`, for item 2(b) of the ruling "PLAN AND BUILD
TOWARDS REAL FLIGHTS" (METHODOLOGY, 2026-10-11): "QuadPlane costing … REPORTED BEFORE BUILDING". Nothing was built,
flown or changed to produce it. The only network access was a read of six published `.apj` headers (§9).

**Sources.**
- ArduPilot `7bac20cbcc` (`~/ardupilot`). Citations are `path:line` at that commit.
- The thesis fork `~/ardupilot_ukf`:
  - branch `ukf-jitter-fix` at `abb0357d`, cited as **fork**;
  - branch `rung1-geometry` at `c25fa898`, cited as **fork-r1**.

**Labels:**
- **[V]** verified in source or in a fetched file;
- **[E]** an estimate, with its basis;
- **[U]** unverified.

**Effort:** one person; "d" is a working day; every effort figure is [E].

**Inputs.** `docs/partC_onboard_feasibility.md` §1.9 (the first Plane pass), `docs/real_flight_readiness.md` (G4: "+1–2
d if QuadPlane") and `docs/real_flight_readiness_by_rung.md`. This report supersedes those QuadPlane estimates.

---

## 0. Summary

**Verdict: a QuadPlane is NOT a configuration change. It is blocked for rung 3 by three items of new firmware code:**

| # | blocker | why |
|---|---|---|
| B1 | **No position-free landing in QuadPlane** | QLAND runs the QLOITER position controller (`ArduPlane/mode_qland.cpp:26-31`). No Q mode checks position validity. `AP_InertialNav` freezes the last horizontal velocity when the estimator stops reporting it. So the "position lost → LAND" response that `thesis_nav_check` gives on Copter has no safe Plane equivalent. |
| B2 | **The thesis backends have no origin, so Plane has no Location** | `AP_AHRS_UKF::get_origin` returns false and `location_valid=false` (fork `AP_AHRS_UKF.h:30`, `AP_AHRS_UKF.cpp:42`). Plane builds `current_loc`, home, the guided targets, take-off targets, QRTL and the altitude fence from the Location. |
| B3 | **Plane GUIDED cannot fly the experiment profile** | `SET_POSITION_TARGET_LOCAL_NED` changes **altitude only** (`ArduPlane/GCS_MAVLink_Plane.cpp:1081-1101`). There are no velocity targets. Horizontal targets need a Location (`DO_REPOSITION`), which needs B2. |

**Effort.**
- QuadPlane delta over the Copter rung-3 path: **about 11–17 d** (§11). The previous estimate was "+1–2 d".
- About 7–10.5 d of it is software that can start now, with QuadPlane SITL after the sim freeze.
- **Rung 1 on a QuadPlane (EKF3 flying) is not blocked by B1–B3.** It needs an EKF3 origin set by procedure (about
  0.25 d) for the Location-based features (§6), and pilot-flown Q modes, or a `DO_REPOSITION` script, in place of the
  Copter GUIDED profile (B3, §4).

**Flash: the premise that Plane is larger than Copter is not borne out.** The published stable builds put Plane
**3.5–7 kB smaller** than Copter on every H7 board checked (§9). The binding constraint is the board, not the vehicle:
a MatekH743-class board has only about **150 kB free**, against about 290–380 kB on the Pixhawk class.

**Recommendation (§13):**
- Choose the **cinewhoop (Copter)** if the supervisor's choice is still open.
- If the vehicle must be a QuadPlane, then:
  - fly rung 1 pilot-flown in QLOITER/QHOVER with EKF3;
  - schedule B1–B3 as new code before any rung-3 QuadPlane flight.

---

## 1. How Plane uses AHRS and the EKF

### 1.1 The thesis backends compile into ArduPlane with no vehicle-side registration [V]

- **Correction to Part C §1.9.** Part C said a UKF parameter group "must be registered in **both** vehicles". The fork
  instead registers the UKF and FGO groups **inside `AP_AHRS`**:
  - `AP_SUBGROUPINFO(ukf, "UKF_", 22, …)` and `(fgo, "FGO_", 23, …)` (fork `libraries/AP_AHRS/AP_AHRS.cpp:237-245`, the UKF line at 240);
  - `AP_NavUKF` is in `COMMON_VEHICLE_DEPENDENT_LIBRARIES` (fork `Tools/ardupilotwaf/ardupilotwaf.py:51`).
  - So `arduplane` gets `AHRS_UKF_*`, `AHRS_FGO_*` and `AHRS_EKF_TYPE 12/13` with no Plane edit.
- **The update path is vehicle-agnostic.** `AP_AHRS::update()` runs `ukf.update()` and, when type 12 is active,
  `copy_estimates_from_backend_estimates` (fork `AP_AHRS.cpp:527-547`). Plane calls `ahrs.update()` from its
  `FAST_TASK(ahrs_update)` (`ArduPlane/Plane.cpp:64`).
- **The FGO `ODOMETRY` route is in `GCS_Common.cpp`** (fork `GCS_Common.cpp:4057-4072`), so it is vehicle-agnostic too.
- **Never built:** the fork's `arduplane` target, in SITL or for a board [V: `~/ardupilot_ukf/build/` holds only
  `sitl/` builds of Copter and Replay, per `real_flight_readiness.md` G1b]. So "compiles" is [E] until a build is run.

### 1.2 Loop rate and the UKF predict step [V/E]

- With `Q_ENABLE`, Plane sets `SCHED_LOOP_RATE` to 300 (`ArduPlane/Parameters.cpp:1365-1369`, via Part C §1.9). The loop
  budget is therefore **3.33 ms**, against Copter's 2.5 ms.
- **The port follows EKF3's own trigger.** It accumulates IMU deltas until `_dt_acc >= TARGET_DT - 0.5*dta` and predicts
  on the accumulated dt (fork `AP_NavUKF.cpp:536-540`).
  - At 300 Hz that gives **4 frames = 13.3 ms (75 Hz)**, the same step EKF3 takes [derived].
  - The process noise has EKF3's per-step form, so the NSE values transfer unchanged.
- **However, the offline Python UKF and the `UKF_Equiv` harness assume 0.0125 s** (CLAUDE.md "EKF3 Prediction dt"). On a
  Plane log they must be re-run with the 13.3 ms step: an equivalence re-check, **0.5 d**.

### 1.3 The DCM fallback for FIXED_WING vehicles [V]

**Plane is always `VehicleClass::FIXED_WING`.** `_active_EKF_type()` therefore applies its fixed-wing fallback to the
UKF and FGO arms too (fork `AP_AHRS.cpp:2346-2457`; the UKF/FGO cases at 2374-2385 set `should_use_gps=false`).

- **`can_use_dcm = dcm.yaw_source_available() || fly_forward`** (2394).
  - With the nomag configuration (`COMPASS_USE*=0`) and in VTOL flight (`fly_forward` false), it is false. The fallback
    then stays on the UKF **while** attitude, vertical velocity and vertical position are valid (2395-2398).
  - With a compass in use, set `AHRS_OPTIONS` bit 1 `DisableDCMFallbackVTOL` (2405-2410). Otherwise the UKF's loss of
    `horiz_vel`/`horiz_pos_rel` (2443-2456) hands the vehicle to DCM, which has no horizontal position.
- **No option prevents the forced handover when `!can_use_ekf`** (2398-2401):
  - The UKF's option-(i) hold keeps attitude valid. It keeps vertical position and velocity valid only for
    `VERT_HOLD_MS = 15000` (fork `AP_NavUKF.h`, `vert_hold_valid()`), or while the rangefinder is fused.
  - After that, AHRS switches to DCM **whatever the options say**.
  - **On Copter this cannot happen.** The vehicle is not FIXED_WING, and the fork's Copter `thesis_nav_check` relies on
    "active = configured" (fork `ArduCopter/ekf_check.cpp:340-341`). **On Plane, active can differ from configured.**
  - `has_status()` reads the **configured** backend (fork `AP_AHRS.cpp:337-343` → `get_filter_status`, switching on
    `configured_ekf_type()` at 2747). The controllers, however, read the **active** one.
  - **A Plane landing trigger must therefore treat "active ≠ configured" as a failure in its own right.**

### 1.4 Where QuadPlane reads position, velocity and Location [V]

- **Relative NE position and velocity** reach the VTOL controllers through `QuadPlane::inertial_nav`, which is updated in
  `Plane::ahrs_update` (`ArduPlane/Plane.cpp:202-203`).
  - `AP_InertialNav::update` copies `get_relative_position_NE_origin`, `_D_origin` and `get_velocity_NED` **only when
    they succeed**. Otherwise it keeps the last values (`libraries/AP_InertialNav/AP_InertialNav.cpp:18-36`).
  - When velocity fails, the horizontal velocity is **frozen at the last good value** (37-44).
  - So the UKF's option-(i) hold, with velocity invalid, leaves the loiter controller acting on a stale velocity (B1).
- **Location.**
  - `Plane::update_current_loc`: `have_position = ahrs.get_location(current_loc)` (`ArduPlane/Plane.cpp:1059-1065`),
    which is false for types 12 and 13 (no origin, B2).
  - **This reaches far:** `quadplane.cpp` has 39 references to `current_loc`, `next_WP_loc` or an origin vector [V: grep
    count].
  - `setup_target_position` zeroes the origin if there is none (`quadplane.cpp:3108-3124`).
  - Guided take-off reads the origin (3240).
  - Guided and auto loiter re-read `current_loc` (2849).
  - `do_user_takeoff` seeds its target from `current_loc` (4027-4030).
  - QRTL targets home or a rally point (`mode_qrtl.cpp`).
- **QLOITER itself** (`mode_qloiter.cpp:34-127`) runs `loiter_nav` on relative position. It works without an origin
  **while the position is valid**. Its precision-landing override needs an origin (`get_vector_xy_from_origin_NE_cm`,
  line 58).
- **Plane's EKF failsafe is doubly silent on the thesis backends.**
  - `Plane::ekf_check` returns immediately without an origin (`ArduPlane/ekf_check.cpp:35-39`).
  - It is disabled outside `in_vtol_posvel_mode()` (44-47).
  - The UKF reports `velVar = posVar = 0` (fork `AP_AHRS_UKF.cpp:113-119`), so only the range ratio can score.
  - This mirrors Copter, which is why the fork added `thesis_nav_check`.

### 1.5 Effort

| item | effort |
|---|---|
| Build the fork's `arduplane` for SITL; confirm parameters `AHRS_UKF_*` appear; shadow run | 0.5 d |
| Equivalence re-check at the 300 Hz / 13.3 ms step (offline UKF, `UKF_Equiv`) | 0.5 d |
| **Origin support in the UKF and FGO backends** (B2): accept `SET_GPS_GLOBAL_ORIGIN` or the recorded origin (`AHRS_OPTIONS` bits 3/4); return `get_origin`; `location = origin + relative NED`; take part in the common-origin propagation. **This also changes the Copter design** ("no origin"), so Copter SITL safety (a)/(b) must be re-run. | 1.5–2.5 d (code 1–1.5, Copter re-test 0.5–1) |

---

## 2. `thesis_nav_check` on Plane

**Today.** The check exists only as `Copter::thesis_nav_check`, a `FAST_TASK` placed before the flight mode (fork
`ArduCopter/Copter.cpp:135-136`, `ekf_check.cpp:330-358`).
- It fires when the vehicle is armed, type 12/13 is configured, the backend has reported `HORIZ_POS_REL` since arming,
  and it no longer does.
- It then calls `failsafe_ekf_event()`, which applies `FS_EKF_ACTION`. The default is LAND, which on Copter lands without
  position, on attitude plus height.

**Is a Plane equivalent needed? Yes.** Plane's EKF failsafe never fires on these backends (§1.4).

**Plane has no `FS_EKF_ACTION`** [V: grep over `ArduPlane/` finds only `FS_EKF_THRESH`]. The action in
`Plane::failsafe_ekf_event` is hard-wired (`ArduPlane/ekf_check.cpp:149-176`):
- it does nothing outside `in_vtol_posvel_mode()`;
- in VTOL auto it switches to **QLAND**;
- otherwise it switches to **QHOVER**.

**Neither target is a safe response to position loss on the UKF:**
- **QLAND** runs QLOITER (`mode_qland.cpp:26-31`), which runs the position controller on a frozen velocity (§1.4).
  - It may tilt persistently to "cancel" a velocity that no longer updates.
  - No Q mode or `quadplane.cpp` path gates on position validity [V: grep for `HORIZ_POS`, `has_status`, `position_ok`
    in `mode_q*.cpp` and `quadplane.cpp` returns nothing].
- **QHOVER** holds altitude on attitude plus height, with horizontal motion left to the pilot. It does not land by itself.
  It is acceptable **only** with a pilot ready to land manually.

**What the Plane version needs:**
1. **Placement.** A new `FAST_TASK(thesis_nav_check)` directly after `ahrs_update` in `Plane::scheduler_tasks`
   (`ArduPlane/Plane.cpp:64-65`), so that it runs before `update_control_mode`.
   - The 10 Hz `ekf_check` slot (`Plane.cpp:83`) would add up to 100 ms of latency.
2. **Trigger.** As on Copter (had `HORIZ_POS_REL` since arming, now lost), **plus** "active ≠ configured" (the DCM
   handover, §1.3).
3. **Action: a position-free VTOL landing (B1).** The options are:
   - **(a)** a new "attitude-only QLAND" path. In QLAND, when the thesis backend lacks horizontal position: hold level
     roll/pitch (pilot sticks added if present), use `pos_control` D only to descend at `Q_LAND_SPEED`, and keep the
     existing landing detection. This mirrors Copter's `land_run_horiz_and_vert_control` without position.
     - It touches `mode_qland.cpp`/`mode_qloiter.cpp`/`quadplane.cpp`, which are flight-critical shared code.
     - **2–3 d** of code plus QuadPlane SITL.
   - **(b)** QHOVER plus an alert, with the pilot landing. **0.5 d.** But this makes the safety case depend on the pilot,
     which the Copter path does not.
   - **(c)** Disarm below a height threshold. Not recommended.

**Effort:** **3–4 d** for (a), including SITL. That replaces readiness G4's "+1–2 d".

---

## 3. Failsafe paths

| failsafe | Copter (as built and tested) | QuadPlane at `7bac20cbcc` [V] | what to set or build |
|---|---|---|---|
| EKF / position loss | `thesis_nav_check` → `FS_EKF_ACTION` LAND (attitude-only) | `Plane::ekf_check` is silent (§1.4); the hard-wired action is QHOVER/QLAND | §2: a Plane `thesis_nav_check` plus a position-free landing (B1) |
| GCS heartbeat (the watcher) | `FS_GCS_ENABLE 5` (Land), `FS_GCS_TIMEOUT 3` | `FS_GCS_ENABL` 1 (heartbeat), timeout = the shared `FS_LONG_TIMEOUT` (`Parameters.cpp:452-466`; `system.cpp:370-392`). Action from `failsafe_long_on_event` (`events.cpp:111-240`): **Q modes → QLAND**, or QRTL/RTL if `Q_OPTIONS` bits 5/20 are set (`events.cpp:167-181`); **GUIDED → `FS_LONG_ACTN`** (Continue/RTL/Glide/…, never a VTOL land; `events.cpp:197-216`) | Clear `Q_OPTIONS` bits 5 and 20; **do not fly GUIDED unless it is made safe**; `FS_LONG_TIMEOUT 3`; watcher changes (§7) |
| RC short | Copter `FS_THR_*` | Q modes → QLAND, or QRTL/RTL by Q_OPTIONS (`events.cpp:50-64`); **GUIDED → CIRCLE/FBWA/FBWB** (fixed-wing modes) unless `FS_SHORT_ACTN 0` (`events.cpp:77-91`) | `FS_SHORT_ACTN 0`; Q_OPTIONS bits 5/20 clear |
| RTL anywhere | — | With `Q_RTL_MODE 0`, RTL is **fixed-wing** RTL. `Q_RTL_MODE 3` = QRTL always (`mode_rtl.cpp:21-24`). QRTL targets home/rally (`mode_qrtl.cpp:17-20`), which needs a Location (B2). | `Q_RTL_MODE 3`, and never select RTL indoors; arming requires one of `RTL_AUTOLAND`/`Q_RTL_MODE` unset (`AP_Arming_Plane.cpp:224-226`) |
| Fence breach | `FENCE_ACTION` Land available | **No Land action on Plane.** `ALWAYS_LAND`, `SMART_RTL*` and `BRAKE` are "invalid enumeration value for Plane" (`ArduPlane/fence.cpp:116-120`); the valid actions are RTL, Guided and AUTOLAND→RTL (`AC_Fence.cpp:72`), all needing a Location | §6 |
| Battery | Copter `BATT_FS_*` LAND | `BATT_FS_*` with Plane actions; QLAND is available as an action [U: check the Plane `@Values` list] | parameter only, 0.1 d |

**The QuadPlane-specific hazard:** any path that selects a **fixed-wing mode** (RTL with `Q_RTL_MODE 0`, CIRCLE, FBWA,
FBWB, AUTO with fixed-wing items) is a crash indoors. Every failsafe must be checked, in SITL, to end in a Q mode.

**Effort:** parameter file plus review **0.5 d**; SITL checks are in §10.

---

## 4. Flight modes for the experiment

| mode | needs | works on types 12/13 as built? | note |
|---|---|---|---|
| **QLOITER** | relative position and velocity (`loiter_nav`, `mode_qloiter.cpp:116-127`) | **Yes, while the backend is valid.** Pilot-flown. | The natural mode for a pilot-flown rung 1 and for a pilot-flown rung 3. B1 applies on loss. |
| **QHOVER** | attitude and height | Yes | Altitude hold only; horizontal is the pilot's. The failsafe target (§2). |
| **QSTABILIZE** | attitude | Yes | Manual backup. |
| **GUIDED** with `Q_GUIDED_MODE 1` (`quadplane.cpp:193-198`) | Location targets | **No (B2, B3).** `SET_POSITION_TARGET_LOCAL_NED` → altitude only (`GCS_MAVLink_Plane.cpp:1081-1101`); `SET_POSITION_TARGET_GLOBAL_INT` → altitude only (1103-1140); horizontal only via `MAV_CMD_DO_REPOSITION` (739) or scripting `set_target_location` (`Plane.cpp:903`), both Location-based | `fly_trial.py`'s velocity cruise and moving-setpoint laps (`SET_POSITION_TARGET_LOCAL_NED` position + velocity) **have no Plane equivalent** |
| Lua `set_velocity_match` | VTOL mode | Partly | `Plane.cpp:974-984`; consumed in QLOITER only inside `#if AC_PRECLAND_ENABLED`, with a 250 ms timeout (`mode_qloiter.cpp:45-72`). It needs scripting and precland compiled in (flash) and a Lua profile script. |
| QRTL, AUTO (VTOL items) | home / mission Locations | No (B2) | Out of scope indoors. |

**Options for a scripted profile on a QuadPlane** (needed only if the experiment is not pilot-flown):
- **(i)** B2 origin support, plus a Plane flight script using `DO_REPOSITION` with origin-relative lat/lon. **1.5–2 d**
  beyond B2. This gives point-to-point moves, not the moving setpoint with velocity feed-forward. The VTOL position
  controller's approach stages (`QPOS_APPROACH`/`POSITION1/2`) are designed for transitions and must be checked at
  sub-metre steps [U].
- **(ii)** A Lua `set_velocity_match` script in QLOITER. **1.5–2 d** plus the flash cost of scripting and precland.
- **(iii)** Pilot-flown QLOITER against marks on the floor. **0 d** of code, but the trajectories are less repeatable.

---

## 5. Take-off and landing

- **Pilot take-off in QLOITER/QHOVER** works without a Location. `throttle_wait` holds the motors at ground idle until
  the pilot raises the throttle (`mode_qloiter.cpp:78-89`).
  - Set `Q_OPTIONS` bit 18 `ARMVTOL` (arm only in VTOL modes; `quadplane.cpp:279`), so the vehicle can never be armed in
    a fixed-wing mode.
- **Scripted take-off** is `MAV_CMD_NAV_TAKEOFF` in GUIDED, frame `LOCAL_OFFSET_NED` → `do_user_takeoff`
  (`GCS_MAVLink_Plane.cpp:895-911`, `quadplane.cpp:4013-4039`).
  - Its target is `current_loc` raised by the requested height. **Without a Location, `current_loc` is stale or zero.**
    So on types 12/13 it needs B2; with EKF3 flying, an EKF3 origin set by procedure (§6).
- **Landing** is QLAND (position-holding descent with landing detection) or a pilot landing in QHOVER.
  - On the thesis backends, QLAND is safe only while position is valid (B1).
- **The rangefinder in Plane** is read at 50 Hz (`Plane.cpp`, `read_rangefinder`). Landing use also needs
  `RNGFND_LANDING 1` [U for its effect in Q modes].
  - The UKF reads the rangefinder through `AP_DAL`, independent of that flag.

**Effort:** 0.5 d (parameters, take-off and landing procedure, SITL checks in §10).

---

## 6. Geofence

- Plane's fence actions are **RTL, Guided, GuidedThrottlePass and AUTOLAND-or-RTL**. There is **no Land**
  (`AC_Fence.cpp:72`, `ArduPlane/fence.cpp:111-130`).
- RTL becomes QRTL with `Q_RTL_MODE 3`, and QRTL needs home (B2).
- The altitude fence uses `get_relative_position_D_home` (`AC_Fence.cpp:597`), so it is **inert without home** [V for
  the call; E for "inert"].
- **Consequence: on a QuadPlane without B2, the mocap watcher is the only fence.** Set `FENCE_ENABLE 0`, or
  `FENCE_ACTION 0` (report only). With B2 and `Q_RTL_MODE 3`, a QRTL fence response could be tested in SITL, but QRTL
  indoors flies to home at `Q_RTL_ALT`, which is unsuitable inside a mocap volume.
- **Rung 1 on a QuadPlane (EKF3 flying) is a different, smaller problem.** B2 concerns the thesis backends only. With
  EKF3 active, a Location exists as soon as **EKF3** has an origin. That is a procedure or parameter step, not code:
  - a GCS `SET_GPS_GLOBAL_ORIGIN` before arming; or
  - the recorded origin, `AHRS_OPTIONS` bit 4 `UseRecordedOriginForNonGPS` with `AHRS_ORIGIN_LAT/LON/ALT`
    (`libraries/AP_AHRS/AP_AHRS.cpp:211-221` at the pin).
  - About 0.25 d, including a SITL check. Rung 1's "FC altitude fence" (readiness H6) then carries over.

**Effort:** 0.25 d (decision and parameters).

---

## 7. The GCS failsafe for the watcher

`realflight/watcher/` (G1–G11, 73 offline tests, merged `0502282`) is **Copter-specific** [V]:
- `COPTER_LAND = 9` (`realflight/watcher/fc_link.py:27`), sent as `MAV_CMD_DO_SET_MODE` (around line 115);
- the expected-parameter check names `FS_GCS_ENABLE eq(5)`, `FS_GCS_TIMEOUT`, `MAV_GCS_SYSID`, `MAV_GCS_SYSID_HI` and
  `FS_OPTIONS` bit 4 (`fc_link.py:31-40`).

**On Plane:**
- **QLAND is custom mode 20** (`ArduPlane/mode.h:59`).
- The failsafe parameters are `FS_GCS_ENABL` (values 0–3, 1 = heartbeat) and `FS_LONG_TIMEOUT` (1–300 s, default 5;
  `Parameters.cpp:452-466`).
- **The action depends on the mode:** QLAND from Q modes, and `FS_LONG_ACTN` from GUIDED (§3).
- `MAV_GCS_SYSID` exists on Plane too (`Parameters.cpp:1576`).
- The `FS_OPTIONS` "RC override wins" bit (B10) is Copter's. The Plane RC-override behaviour must be re-derived [U].
- **B1 again:** the watcher's QLAND on a breach is itself QLOITER-based. If the breach is *caused* by estimator failure,
  QLAND may not recover. The watcher's LAND on Plane therefore needs the position-free landing too, or QHOVER plus a
  pilot.

**Effort:** a vehicle switch in `fc_link.py`, Plane expected parameters, Plane `watcher_fc.parm`, and the offline tests
re-targeted: **1–1.5 d**. SITL bench B0–B10 on Plane: **+0.5–1 d** on top of 2(c).

---

## 8. Arming checks

| check | Plane behaviour [V] | consequence |
|---|---|---|
| AHRS | `AP_Arming_Plane::ins_checks` always calls `ahrs.pre_arm_check(true, …)` (`AP_Arming_Plane.cpp:233-247`) | The UKF backend ignores `requires_position` and needs only initialised and healthy (fork `AP_AHRS_UKF.cpp:92-103`). |
| Configured type | `"not using configured AHRS type"` unless compass-less (fork `AP_AHRS.cpp:2648-2653`) | Under nomag, a DCM handover would not block arming. A Plane `thesis_nav_check` must catch it in flight (§2). |
| Healthy | For EKF3 on FIXED_WING, `healthy()` is false unless EKF3 is the active type (fork `AP_AHRS.cpp:2590-2596`); the UKF/FGO arms return the backend's health (2609-2616) | No Plane-specific block for 12/13. |
| Compass | **No Copter-style unconditional compass-health gate** in `AP_Arming_Plane.cpp` [V: grep for `compass`/`ALLOW_ARM_NO_COMPASS` returns nothing] | On Plane the compass may be absent (`COMPASS_ENABLE 0`) [U: confirm with the generic `AP_Arming::compass_checks` in SITL]. |
| Quadplane | `Q_ASSIST_SPEED` must be non-zero (`AP_Arming_Plane.cpp:208-213`; set **−1** indoors, which disables assistance, `quadplane.cpp:97-101`); `SCHED_LOOP_RATE ≥ 100`; motor and `Q_P`/`Q_A` parameter checks (157-203) | Parameters only. |
| Home | Set at arming from `current_loc` (`AP_Arming_Plane.cpp:290-296`) | Without a Location, home stays unset [E]. That disables the altitude fence and QRTL, and makes `relative_altitude` undefined (`Plane.cpp:1064`). B2 fixes it. |
| Forward motor | Not an arming check | Set `Q_FWD_THR_USE 0` and `Q_VFWD_GAIN 0` (`quadplane.cpp:163-167, 527-532`) so that no Q mode uses the forward motor indoors. |

**Effort:** 0.5 d (parameter template plus SITL arming checks).

---

## 9. Flash budget

**Published stable `.apj` headers** (`git_identity dbe79216`, fetched 2026-10-11 from
`firmware.ardupilot.org/{Copter,Plane}/stable/<board>/{arducopter,arduplane}.apj`) [V]:

| board | flash_total (B) | Copter image / free | Plane image / free | Plane − Copter |
|---|---|---|---|---|
| CubeOrange | 1,966,080 | 1,644,436 / **321,644** | 1,640,968 / **325,112** | −3,468 |
| Pixhawk6X | 1,966,080 | 1,679,428 / **286,652** | 1,674,616 / **291,464** | −4,812 |
| Pixhawk6C | 1,966,080 | 1,590,348 / **375,732** | 1,586,568 / **379,512** | −3,780 |
| KakuteH7 | 1,703,936 | 1,436,028 / **267,908** | 1,428,760 / **275,176** | −7,268 |
| MatekH743 | 1,703,936 | 1,549,916 / **154,020** | 1,545,256 / **158,680** | −4,660 |
| MatekH743-bdshot | 1,703,936 | 1,553,764 / **150,172** | 1,549,408 / **154,528** | −4,356 |

**Findings:**
- **Plane is not larger than Copter.** It is 3.5–7.3 kB **smaller** on every H7 board checked. The ruling's premise
  should be corrected.
- **"2 MB" does not mean the same usable space on every H743.**
  - Pixhawk-class boards have 1,966,080 B (2048 KB less the 128 KB bootloader).
  - Boards that keep parameters in flash (Matek, Kakute) have 1,703,936 B.
  - **The MatekH743 class has about 150–160 kB free.**
- **The fork's size is not yet measured** (item 2(a)). Part C §5.5 estimated 25–50 kB for the UKF port plus plumbing.
  The FGO thin backend and `ODOMETRY` hook add a few kB [E]. That fits every board above.
- **What does not fit a Matek-class board:** the fork plus scripting (for a Lua watcher layer or `set_velocity_match`)
  plus precland [E]. Features would have to be compiled out there (Part C §5.5 list).
- **These are stable `dbe79216` sizes, not our `7bac20cbcc`.** Item 2(a) measures the real figure.
- **A QuadPlane adds nothing to the flash question** beyond B1 (a few kB) and B2 (under 1 kB) [E].

**Effort:** 0 d beyond 2(a).

---

## 10. QuadPlane SITL re-testing

**Which model.**
- `ardupilot_gazebo` has no QuadPlane. Its plane is `zephyr`, a fixed-wing [V: `~/ardupilot_gazebo/models/`].
- So QuadPlane SITL uses ArduPilot's **built-in physics**: `sim_vehicle.py -v ArduPlane -f quadplane`
  (`Tools/autotest/default_params/quadplane.parm`).
- **Flow:** the SITL sensor, `SIM_FLOW_ENABLE 1` with `FLOW_TYPE 10` (`libraries/SITL/SITL.cpp:183-250`).
  - It synthesises flow from **true** velocity and **true** gyro, and sets `bodyRate` to the true gyro
    (`AP_OpticalFlow_SITL.cpp:42-95`).
  - It is therefore texture-independent and **does not exercise the hardware derotation path** (UKF-only report, §3).
- **Rangefinder:** a SITL rangefinder, as in the autotest `set_analog_rangefinder_parameters`.
- `SIM_GPS1_ENABLE 0`, plus the nomag parameters.
- **These are verification flights only, never results** (the sim freeze).

**Tests:**

| # | test | pass condition | needs |
|---|---|---|---|
| QP0 | Build the fork `arduplane` (SITL); parameter readback | `AHRS_UKF_*` present; `AHRS_EKF_TYPE 12` accepted | — |
| QP1 | UKF shadow, EKF3 flying, QLOITER hover and pilot-style box (RC override script) | UKF healthy; `XUKF` tracks SITL truth; no DCM handover | — |
| QP2 | UKF flying (type 12), QLOITER hover 60 s plus box | `HORIZ_POS_REL` throughout; active = configured throughout | — |
| QP3 | Safety (a): `AHRS_UKF_TFAIL` forced invalidity in hover | Plane `thesis_nav_check` fires; **position-free landing** lands within the pre-registered drift | B1 |
| QP4 | Flow loss (`SIM_FLOW_ENABLE 0` mid-hover) | Same as QP3, via the aiding timeout | B1 |
| QP5 | Rangefinder loss | Vertical-hold expiry → DCM handover detected and landed | B1, §1.3 |
| QP6 | GCS heartbeat loss (watcher killed) | `FS_GCS_ENABL 1` → QLAND (or the B1 path) within `FS_LONG_TIMEOUT` | §7 |
| QP7 | Every failsafe ends in a Q mode | No fixed-wing mode ever selected (RC short/long, GCS, battery, fence) | §3 |
| QP8 | Arming | Arms only in Q modes; the Q_ASSIST, compass and home behaviour as predicted (§8) | — |
| QP9 | FGO path (only if the FGO is to fly a QuadPlane) | The thin backend's FG1–FG3b on Plane | B2 if guided |

**Harness.**
- `sim/tools/closed_loop_run.sh`, `run_trial.sh` and `fly_trial.py` assume Copter, Gazebo JSON, GUIDED
  `SET_POSITION_TARGET_LOCAL_NED` and the Copter mode numbers.
- `tools/run_h_safety.sh` and `eval/h_safety_score.py` score Copter LAND events.
- A Plane variant is new work: a launcher for the built-in model, an RC-override profile driver for QLOITER, and the
  scorers re-targeted to QLAND/QHOVER and the Plane log events.

**Effort:**
- harness 1.5–2 d;
- flights and scoring QP0–QP8 1.5–2 d;
- QP9 +1 d (optional);
- **total 3–5 d.**
- It also needs B1 and the §7 watcher changes first.

---

## 11. Effort per item (the QuadPlane delta over the Copter rung-3 path)

| # | item | effort [E] | kind | blocks |
|---|---|---|---|---|
| 1 | Build `arduplane` from the fork; shadow smoke run | 0.5 d | SW + SIM | everything |
| 2 | 300 Hz / 13.3 ms equivalence re-check | 0.5 d | SW | results on a Plane log |
| 3 | **B2: origin and Location in the UKF/FGO backends** (+ Copter re-test) | 1.5–2.5 d | SW + SIM | scripted take-off, guided, home, fence |
| 4 | **B1: Plane `thesis_nav_check` + position-free QLAND path** | 3–4 d | SW + SIM | any rung-3 QuadPlane flight |
| 5 | Failsafe parameter file and review (no fixed-wing mode reachable) | 0.5 d | SW | flight |
| 6 | **B3: scripted profile** (i) `DO_REPOSITION` script, or (ii) Lua velocity match; (iii) pilot-flown = 0 d | 0–2 d | SW | a scripted experiment only |
| 7 | Take-off/landing procedure and parameters | 0.5 d | SW | flight |
| 8 | Geofence decision | 0.25 d | SW | — |
| 9 | Watcher Plane support (`fc_link.py`, parameters, tests) | 1–1.5 d | SW | rung 3 |
| 10 | Arming parameters and checks | 0.5 d | SW + SIM | flight |
| 11 | QuadPlane SITL harness, tests QP0–QP8 (QP9 optional) | 3–5 d | SIM (after 16 Oct) | rung 3 |
| 12 | Flash | 0 d beyond 2(a) | — | — |
| | **Total** | **about 11–17 d** | SW now about 7–10.5 d; SIM about 4–6.5 d | |

**Not counted:**
- the QuadPlane VTOL tune and hover learning on the real airframe (supervisor's vehicle);
- hardware bench steps identical to Copter's.

**Rung 1 on a QuadPlane** (EKF3 flying, pilot-flown QLOITER) needs only items 5, 7, 8 and 10 (about 1.75 d).
- For the FC altitude fence, or a scripted profile, it also needs an **EKF3 origin set by procedure** (about 0.25 d,
  §6), not item 3.
- A scripted rung 1 then adds item 6(i) (1.5–2 d), which works on EKF3's Location without item 3.

---

## 12. The cinewhoop alternative (Copter, as now)

**Everything built so far applies unchanged [V]:**
- the fork's Copter `thesis_nav_check` and `FS_EKF_ACTION` LAND (attitude-only);
- the watcher (`COPTER_LAND 9`, `FS_GCS_ENABLE 5`);
- `fly_trial.py`'s `SET_POSITION_TARGET_LOCAL_NED` profiles;
- the SITL safety tests (a)/(b);
- the Gazebo iris harness;
- the 0.0125 s step (400 Hz).

**No B1–B3 work is needed.** The QuadPlane delta of about 11–17 d disappears.

**Cinewhoop-specific points [E]:**
- **Board.** Small AIO H7 boards are typically flash-in-parameter types (Matek/Kakute class, about 150–270 kB free, §9),
  so 2(a)'s flash check matters more there. Without a compass fitted, Copter's unconditional compass gate
  (`ArduCopter/AP_Arming_Copter.cpp:575-585`) blocks arming unless the build defines `ALLOW_ARM_NO_COMPASS`. That is a
  hwdef define, acceptable in custom firmware.
- **Vibration.** Small props at high RPM need a notch, and the flow sensor needs vibration isolation. The 333 Hz
  aliasing analysis was for the Gazebo iris, so re-check `VIBE` on the bench.
- **Endurance.** Typically 3–6 minutes, so profiles must be short. The current rung-1 profile (hover plus short moves)
  fits.
- **Indoor safety.** The ducts help in a mocap volume. The small size makes marker placement and the rigid-body identity
  check (G3) harder.

---

## 13. Recommendation

1. **If the airframe is still a choice: the cinewhoop (Copter).** It reuses every built and SITL-tested safety layer and
   avoids about 11–17 d of new, flight-critical Plane code.
2. **If the supervisor's vehicle is a QuadPlane:**
   - **Rung 1:** EKF3 flying, **pilot-flown in QLOITER/QHOVER**, with the §3/§5/§8 parameters. About 1.75 d over the
     Copter rung-1 plan. The FC fence and any scripted profile need an EKF3 origin set by procedure (about 0.25 d, §6), not B2.
   - **Rung 3 is BLOCKED until B1 (a position-free landing and a Plane `thesis_nav_check`) exists and passes QP3–QP5 in
     SITL.**
     - Scripted closed-loop profiles additionally need B2 and B3.
     - Plan about 11–17 d, of which about 7–10.5 d of software can start now. The QuadPlane SITL can only run after
       16 Oct.
     - That puts a QuadPlane rung 3 after 23 Oct.
   - Fly only Q modes, with `Q_OPTIONS` bit 18, `Q_RTL_MODE 3`, `FS_SHORT_ACTN 0`, Q_OPTIONS bits 5/20 clear,
     `Q_ASSIST_SPEED −1` and `Q_FWD_THR_USE 0`. **Never GUIDED** until B2 and B3 exist and its failsafe action
     (`FS_LONG_ACTN`) is resolved.
3. **Correct the flash premise:** Plane is not larger than Copter, and the board class sets the margin (§9).

## 14. Questions for the supervisor

1. **Airframe:** VTOL QuadPlane or cinewhoop? If QuadPlane, which type: plain quad-plus-pusher, tiltrotor or tailsitter?
   Tailsitters and tiltrotors change the VTOL code paths and are not costed here.
2. **Board:** Pixhawk class (about 290–380 kB free) or a flash-in-parameter AIO H7 (about 150–270 kB)?
3. **On a QuadPlane, is a pilot-flown QLOITER profile acceptable** for rungs 1 and 3? That removes B3, and makes B2
   optional for rung 1.
4. **Position-loss response on a QuadPlane:** is QHOVER plus a pilot landing (option (b), 0.5 d) acceptable as the
   safety case, or is an autonomous position-free landing required (option (a), 3–4 d of flight-critical Plane code)?
5. **Origin:** may the UKF/FGO backends accept a set origin (B2)? It changes the Copter "no origin" design and needs a
   Copter safety re-test.
6. **Wingspan against the mocap volume.** Is a VTOL safe to hover inside the booked volume with the watcher's ≥ 2 m
   clearance rule?
7. **Compass:** fitted or not? It matters for the Copter arming gate, and for the Plane DCM fallback if compass yaw is
   ever used.
