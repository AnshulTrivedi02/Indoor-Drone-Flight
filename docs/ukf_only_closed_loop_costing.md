# UKF-only closed loop: costing the quickest rung-3 option

Status: REPORT ONLY, written 2026-10-11 on `fwd-camera` at `bccbc78`, for item 2(e) of the ruling "PLAN AND BUILD
TOWARDS REAL FLIGHTS" (METHODOLOGY, 2026-10-11). Nothing was built, flown or changed to produce it.

**The option.** The onboard UKF (`AP_NavUKF`, `AHRS_EKF_TYPE 12`) steers the vehicle, using the vehicle's **own** flow
sensor and rangefinder on the flight controller. There is no Pi, no camera pipeline and no FGO. EKF3 keeps running as a
passive shadow (it already does: fork `AP_AHRS.cpp:527-547`).

**Sources.**
- ArduPilot `7bac20cbcc` (`~/ardupilot`).
- The thesis fork `~/ardupilot_ukf`:
  - `ukf-jitter-fix` at `abb0357d`, cited as **fork**;
  - `rung1-geometry` at `c25fa898`, cited as **fork-r1**.

**Labels:**
- **[V]** verified in source or a document;
- **[E]** an estimate, with its basis;
- **[U]** unverified.

Effort is for one person; "d" is a working day; every effort figure is [E].

**Vehicle.** This report assumes **Copter** (a cinewhoop or quad), where every safety layer is already built and tested
in SITL. On a QuadPlane, add the blockers B1–B3 of `docs/quadplane_costing.md` (about 11–17 d).

---

## 0. Summary

**What it needs that does not exist yet:**
- a board build of the fork;
- the port's real-sensor geometry merged (fork-r1, on hold) and its derotation input settled (D18);
- **initialisation on the ground for a rangefinder that reads below its minimum** (a new, small port change; without it
  the vehicle may not arm);
- SITL verification flights with a SITL flow sensor;
- a live mocap feed to the watcher, which already exists;
- the bench, hand-carried and tethered steps, the forced-invalidity bench test, and a stage-3 pre-registration.

**Effort:**
- **About 12–18 d in all:**
  - software now about 4–6 d;
  - SITL after the freeze about 2–3 d;
  - hardware about 6–9 d.
- That is about half of the full rung 3 (17–27 d), which sits on top of rung 2 (24–37 d), because the UKF-only option
  **skips rung 2 entirely**: it needs no Pi, camera, FC↔Pi link, clock map, C++ FGO on ARM, or latency rehearsal.

**How it builds on rung 1.** The vehicle, sensors, parameter template, flight cards, mocap recorder, `mocap_align`,
scorer and `LOG_REPLAY` logs are the same.
- The decisive extra gate is cheap: **replay the onboard UKF port on the rung-1 real logs** (Tools/Replay with the fork)
  before it ever steers.
- The same C++ code that will fly is then shown to stay healthy and track mocap on real sensor data.

**Calendar.**
- About **8–10 working days from the hardware being in hand**, provided the software and SITL items are finished first
  and rung 1 has produced at least one real log.
- **Not reachable by 23 Oct** under the current calendar (rung 1 itself needs the vehicle by about 16 Oct).
- Realistically it is the first closed-loop work after 23 Oct.

---

## 1. What it needs, with effort

| # | item | status today | work | effort [E] | kind |
|---|---|---|---|---|---|
| U1 | **Board firmware** with `AP_NavUKF` | `#define AP_NAVUKF_ENABLED (CONFIG_HAL_BOARD == HAL_BOARD_SITL)` (fork `libraries/AP_NavUKF/AP_NavUKF.h:28-30`); no board build exists | §2 | SW 1–2 d (shared with 2(a)); HW 1 d | SW+HW |
| U2 | **Real sensor geometry** in the port | fork-r1 `c25fa898`, on hold; **its Replay regression and `UKF_Equiv` not re-verified** (commit message) | merge after the regression | 0.5 d (needs one build slot) | SW (light build) |
| U3 | **Flow derotation input** (D18) | the port takes the driver's `rawGyroRates` (fork `AP_NavUKF.cpp:470`) | §3; decide, then (optionally) one port change | 0–1 d | SW |
| U4 | **Ground initialisation** when the rangefinder reads below its minimum | the port initialises only on a Good downward range above `RNG_MIN` (fork `AP_NavUKF.cpp:493,524`; fork-r1 607,641) | initialise from `RNGFNDn_GNDCLEAR` (plus the lever arm) while disarmed and `OutOfRangeLow`, as EKF3 does on ground | 0.5–1 d + a SITL check | SW + SIM |
| U5 | **Yaw source** | the UKF has no compass input (`use_compass()` false, fork `AP_AHRS_UKF.h:27`); it uses the variance-gated zero-innovation pseudo-yaw | §4; a decision, not code | 0 d (nomag) | — |
| U6 | **Landing trigger** | `Copter::thesis_nav_check`, a `FAST_TASK` (fork `ArduCopter/Copter.cpp:136`, `ekf_check.cpp:337-358`), SITL safety (a) PASS; **the re-run on the corrected builds is still open (H1)** | §5 | 0 d code; H1 re-run ~0.5 d (UKF only) | SIM |
| U7 | **Failsafe parameter file** (real FC) | the SITL files exist (`closedloop_ukf.parm`); the real-FC template is rung-1 R6 | `AHRS_EKF_TYPE 12`, `AHRS_UKF_ENABLE 1`, `AHRS_UKF_TFAIL 0`, `FS_EKF_ACTION 1`, the GCS failsafe, battery, RC | 0.5 d on top of R6 | SW |
| U8 | **Watcher** | G1–G11 built and merged (`realflight/watcher/`, 73 offline tests); SITL bench B0–B10 is 2(c); live mocap client F1 not built | §6 | F1 1–2 d (protocol per U7 mocap); B0–B10 in 2(c); hardware bench 1 d | SW + SIM + HW |
| U9 | **SITL verification flights** with a SITL flow sensor | none with `SIM_FLOW` | §7 | harness 0.5 d; flights 1.5–2 d | SIM (after 16 Oct) |
| U10 | **Replay gate on rung-1 logs** | the Replay UKF exists (fork Replay hooks) | §8 | 0.5–1 d after the first rung-1 log | SW |
| U11 | **Bench, hand-carried, tethered** | not built (readiness H4, H7, H8) | §9 | 2.5–3.5 d | HW |
| U12 | **Safety tests on the vehicle** | the SITL analogues exist | §10 | in U11 + 0.5 d | HW |
| U13 | **CPU and flash on the H743** | estimates only | §11 | in U1/U11 | HW |
| U14 | **Stage-3 pre-registration** (profile, n, window, abort rules) | not written | | 1–1.5 d | SW |
| U15 | **Flights and scoring** | | | 1 d flights + 0.5–1 d scoring | HW + SW |

**Totals [E]:**

| kind | items | effort |
|---|---|---|
| Software that can start now | U1 (SW), U2, U3, U4 (code), U7, U8 (F1), U14 | about 4–6 d |
| SITL after 16 Oct | U4 (check), U6 (H1 UKF part), U9 | about 2–3 d |
| After rung 1's first log | U10 | 0.5–1 d |
| Hardware | U1 (HW), U8 (bench), U11, U12, U15 | about 6–9 d |
| **Total** | | **about 12–18 d** |

---

## 2. Board firmware with `AP_NavUKF` (U1)

**What has to change in the fork:**
1. **The guard.** Make `AP_NAVUKF_ENABLED` a build option:
   - default off;
   - on for SITL, and for the chosen board through a hwdef `define AP_NAVUKF_ENABLED 1` or a waf
     `--enable-thesis-ukf` flag (an entry in `Tools/scripts/build_options.py`).
   - Optionally put `AP_NavFGO` and the `ODOMETRY` hook (fork `GCS_Common.cpp:4057-4072`) under their own flag, so that a
     UKF-only build drops them.
2. **Replay-only file I/O.** The port calls `fopen`/`fprintf` with `FILE *` casts for its CSV and input dump (fork
   `AP_NavUKF.cpp:255-705`). They are never opened on a vehicle, but they must not be compiled into flight code.
   - On ChibiOS, `fopen`/`fprintf` are macros onto `apfs_*` (`libraries/AP_Filesystem/posix_compat.h:94-95`), and the
     `FILE *` casts may not compile against `APFS_FILE` [U].
   - Guard them with `#if CONFIG_HAL_BOARD == HAL_BOARD_SITL`.
3. **The test hook.** `AHRS_UKF_TFAIL` is a parameter (fork `AP_NavUKF.h`, `_tfail`), and it has persisted in eeprom
   before (readiness C8).
   - Keep it, because the bench forced-invalidity test (U12) needs a trigger.
   - **Refuse arming when it is non-zero**: one line in `AP_AHRS_UKF::pre_arm_check`.
   - Check it in `ensure_params`.
4. **Compile.** `./waf configure --board <board>` then `./waf copter`.
   - The base `Board` flags already include `-fsingle-precision-constant` and the `-Werror=…` set, and SITL inherits them
     (`Tools/ardupilotwaf/boards.py:261-470`). So **unsuffixed literals already behave the same in SITL**, and SITL
     equivalence is not undermined by that flag [V].
   - **Board and SITL results will not be bit-identical** (newlib against glibc libm, FMA contraction,
     `-fno-math-errno` on ChibiOS) [E]. Equivalence therefore transfers statistically, not byte-for-byte. Replaying a
     board log in SITL Replay (U10) is the check.
5. **Flash and RAM report and rollback.** Item 2(a) does this (stock `.apj` kept, the bootloader untouched, flashed via
   the GCS or `uploader.py`, parameter dump before and after).

**Bench (HW, 1 d):**
- boot;
- parameter readback;
- **"backends disabled reproduces EKF3"** (`AHRS_EKF_TYPE 3`, `AHRS_UKF_ENABLE 0`: the same EKF3 behaviour as stock);
- then shadow on (`AHRS_UKF_ENABLE 1`, type 3) with `XUKF` logging;
- CPU via `PM` (U13).

---

## 3. Flow input from the real flow sensor; the D18 derotation (U3)

**What the port fuses.** `writeOptFlowMeas(quality, rawFlowRates, rawGyroRates, msec)`, the same arguments EKF3 gets
(fork `AP_NavUKF.cpp:470`). The flow model adds `_flow_gyro` as the rotational term (fork `AP_NavUKF.cpp:208-211`).

**Where `rawGyroRates` comes from depends on the driver [V]:**
- **Pixart (SPI) and MAVLink sensors** take `AP::ahrs().get_gyro()`, averaged over the flow interval
  (`libraries/AP_OpticalFlow/AP_OpticalFlow_Pixart.cpp:291-303`, `AP_OpticalFlow_MAV.cpp:38-42,76`).
  - `AP::ahrs().get_gyro()` is the **active** backend's `gyro_estimate`.
  - **When the UKF is active (type 12)**, `copy_estimates_from_backend_estimates` sets it to the INS gyro minus the
    UKF's **own** bias (fork `AP_AHRS.cpp:633-648`; `AP_AHRS_UKF.cpp:32-33`: `gyro_drift = -bias`,
    `gyro_estimate = gyro + drift`).
  - **So in closed loop, D18's "its own bias-corrected gyro" is satisfied automatically** for these drivers.
  - In **shadow** (EKF3 active) and in **Replay** (`ROFH.G`) it carries **EKF3's** bias instead. That is exactly the
    rung-1 issue that the D18 ruling addresses for the Replay path.
- **HereFlow (DroneCAN)** sends its **own** gyro (`AP_OpticalFlow_HereFlow.cpp:82`), with no bias correction in any
  mode.
- **The SITL flow sensor (`FLOW_TYPE 10`)** sets `bodyRate` to the **true** simulated gyro
  (`AP_OpticalFlow_SITL.cpp:42-44,95`). **SITL therefore does not exercise this path at all.**

**Options:**
- **(a) Accept the driver's rate.**
  - 0 d.
  - Closed loop uses the UKF's own bias.
  - The shadow and Replay runs use EKF3's, so they differ from the flying UKF in this one input. State it.
- **(b) The port derotates from its own DAL gyro.**
  - It averages its own delta angles over the flow interval and subtracts its own bias, ignoring `rawGyroRates`.
  - The same code then behaves identically in shadow, Replay and flight, and with any driver, including HereFlow.
  - **This is the change rung 1 needs anyway** for the Replay path (ruling item 1: "derotate the flow with its OWN
    bias-corrected gyro"), so it is shared work.
  - 0.5–1 d plus a Replay regression.
  - It is a model-input change (D18), so it is recorded as one.
- **Recommendation: (b), done once for rung 1 and inherited by the flying port.**

---

## 4. Yaw: nomag or compass (U5)

**What the UKF uses: no absolute yaw.**
- The UKF has no magnetometer fusion (`use_compass()` returns false, fork `AP_AHRS_UKF.h:27`).
- Its yaw is the gyro-integrated attitude, with the **variance-gated zero-innovation pseudo-yaw** (EKF3's synthetic
  yaw, mirrored).
- External yaw is possible only via ExtNav (`AHRS_UKF_EXTYAW`, `EXTPOS`), which needs a camera or tags. That is out of
  scope here.
- **A compass therefore changes only the EKF3 shadow, never the flying UKF.**

**Consequence: path rotation.**
- Yaw drift is set by the residual gyro-z bias, which is unobservable (METHODOLOGY).
- In the sim, EKF3's no-compass drift was about 8 deg/min. That figure came from the Gazebo model's gyro and does not
  transfer to a real MEMS gyro.
- After the boot gyro calibration, a residual of about 0.01–0.05 deg/s gives **about 0.6–3 deg/min** [E].
- For a 1–2 min profile that is a few degrees of path rotation. Score it with the 4-DoF (yaw-aligned) fit, and pre-register
  the yaw-drift metric.

**Recommended configuration: nomag**, as in rung 1:
- `COMPASS_ENABLE 1`, `COMPASS_USE* 0`, `EK3_SRC1_YAW 0`.
- The compass must be **fitted and healthy**, because of Copter's unconditional compass-health arming gate
  (`ArduCopter/AP_Arming_Copter.cpp:575-585`).
- **If the vehicle has no compass** (common on cinewhoops), define `ALLOW_ARM_NO_COMPASS` in the board's hwdef. That is
  legitimate in custom firmware [V for the guard].
- A compass-on EKF3 Replay remains a labelled sensitivity row only.

---

## 5. Landing trigger, failsafes and the watcher (U6–U8)

**Landing trigger.** `Copter::thesis_nav_check` is a `FAST_TASK` running every loop before the flight mode.
- It fires when: armed, type 12 configured, `HORIZ_POS_REL` seen since arming, and now lost.
- Its action is `failsafe_ekf_event()` → `FS_EKF_ACTION`, default 1 = LAND.
- Copter's LAND without position holds level attitude and descends on height. The UKF keeps attitude valid in its
  option-(i) hold, and height for `VERT_HOLD_MS = 15 s`.
- **Why it exists:** `Copter::ekf_check` does nothing without an origin, and the UKF has none (fork comment at
  `ekf_check.cpp:330-336`). Moreover the UKF's `get_variances` reports vel = pos = 0 and only a range ratio (fork
  `AP_AHRS_UKF.cpp:113-119`). **The variance failsafe is therefore never the protection. The position-loss trigger is.**
- **When it fires on flow loss:** after the UKF's aiding timeout, 5 s without an accepted flow update, or when the
  horizontal velocity σ exceeds 0.5 m/s (validity rule, fork `AP_NavUKF.h`).
  - **During those 5 s the vehicle flies on inertial dead reckoning.**
  - That is EKF3's own timeout too. Pre-register it as the expected latency, and size the watcher box for it.

**Failsafe parameters (U7), Copter:**
- `FS_EKF_ACTION 1` (LAND);
- `FS_GCS_ENABLE 5` (LAND), `FS_GCS_TIMEOUT 3`, `MAV_GCS_SYSID` = the watcher, `FS_OPTIONS` bit 4 (as
  `realflight/watcher/fc_link.py:31-40` checks);
- RC throttle failsafe → LAND;
- battery failsafe → LAND;
- `ARMING_CHECK` default;
- `AHRS_UKF_TFAIL 0` (and refused at arming, §2).

**Fence.**
- Circle and polygon fences need an origin, which the UKF does not provide.
- An FC altitude fence relies on home [U: confirm in SITL whether it is inert under type 12].
- **The mocap watcher's box and z_max (G10) are the fence.**

**Watcher (U8).**
- Built for Copter: LAND = mode 9, heartbeat to the FC, one latched LAND per episode, stale-pose, identity and height
  checks.
- **With no Pi, it runs on the ground laptop.** It needs the mocap stream (F1, a live client; protocol per the mocap
  system, not built) and a MAVLink link to the FC (telemetry radio or Wi-Fi).
- **Link dropouts are a false-trigger risk** against `FS_GCS_TIMEOUT 3`. Measure the link's worst gap on the bench
  first. A false LAND is safe, but it aborts the flight.

---

## 6. SITL verification flights with a SITL flow sensor (U9)

**Standing rule.** These are short verification flights, not results. They come after the 16 Oct freeze, one at a time,
with nothing heavy during flights.

**Model, option A (preferred): the existing Gazebo iris harness.**
- Keep the harness, but disable `flow_bridge` (our camera flow).
- Set `FLOW_TYPE 10`, `SIM_FLOW_ENABLE 1`, `SIM_FLOW_RATE` = the real sensor's rate, and `SIM_FLOW_DELAY`
  (`libraries/SITL/SITL.cpp:183-250`).
- Keep the Gazebo LiDAR via `lidar_bridge` as `RNGFND1`.
- **Check first** that `AP_OpticalFlow_SITL` gets a sane `height_agl` from the JSON backend [U]. It computes range from
  `state.height_agl` (`AP_OpticalFlow_SITL.cpp:67-69`).

**Model, option B: built-in physics** (`sim_vehicle.py -v ArduCopter -f quad`) with `SIM_FLOW`, an analog SITL
rangefinder (the autotest `set_analog_rangefinder_parameters`) and `SIM_GPS1_ENABLE 0`.
- No Gazebo, and no `no_time_sync` default injection (`SIM_JSON.cpp:406-414`).
- It is the lightest option.

**Either way:**
- The flow is synthesised from **true** velocity and gyro, so it is texture-independent and the derotation path is not
  exercised (§3).
- These flights test plumbing and safety, never accuracy.

**Flights (each short, 1–3 min sim):**

| # | flight | pass |
|---|---|---|
| V1 | UKF shadow, EKF3 flying, hover + small box | UKF initialises on the ground (also with the rangefinder min raised above the ground clearance, after U4); `XUKF` tracks truth |
| V2 | UKF flying (type 12), hover 60 s + box (`fly_trial.py` GUIDED local NED) | `HORIZ_POS_REL` throughout; no `thesis_nav_check` event |
| V3 | Safety (a): `AHRS_UKF_TFAIL` forced invalidity in hover | `thesis_nav_check` → LAND; touchdown drift within the pre-registered bound (earlier SITL: attitude-only drift 0.37–1.4 m) |
| V4 | Flow loss: `SIM_FLOW_ENABLE 0` mid-hover | LAND after the 5 s aiding timeout; drift recorded |
| V5 | Rangefinder loss | Vertical hold for 15 s then … **pre-register the expected outcome** (LAND on hold height; behaviour after `VERT_HOLD_MS` [U]) |
| V6 | Watcher heartbeat loss | `FS_GCS_ENABLE 5` → LAND within `FS_GCS_TIMEOUT` (already passed for the Copter watcher in SITL as T1/T2; repeat once on the UKF build) |
| V7 | Arming: `TFAIL ≠ 0` refused; rangefinder below its minimum on the ground | refusal / initialisation as designed (U4) |

**Effort:**
- harness 0.5 d (parameter file and toggling `flow_bridge`);
- flights and scoring 1.5–2 d (scorer `eval/h_safety_score.py` reused).

---

## 7. The Replay gate on rung-1 logs (U10)

- Rung 1 flies with `LOG_REPLAY 1` and `LOG_DISARMED 1`.
- Replay the **fork's** Tools/Replay (UKF hooks: fork `AP_DAL.cpp:471-512`) on each real log, with the fork-r1 geometry
  read from the log's PARM.
- **Pass, pre-registered:**
  - the UKF initialises;
  - it stays `HORIZ_POS_REL` through each flight's hover and moves;
  - no Cholesky failures (`_n_chol_fail` = 0);
  - its trajectory against mocap is within a band set before looking.
- It costs 0.5–1 d. It is the strongest pre-flight evidence available without flying the UKF: the identical C++ code,
  on the real sensor data and the real IMU.
- **Caveat:** in Replay the flow rate's gyro comes from `ROFH.G`, i.e. EKF3's bias, unless option (b) of §3 is adopted.

---

## 8. Bench, hand-carried and tethered steps (U11)

| step | content | effort |
|---|---|---|
| Bench 0 (props off) | U1 bench (boot, readback, backends off = EKF3, shadow on, `PM` CPU); flow sign and orientation; rangefinder; `RNGFND1_GNDCLEAR`; arming refusal with `TFAIL ≠ 0`; watcher heartbeat → FC; GCS failsafe → LAND (mode change seen); link worst-gap measurement | 1–1.5 d |
| Forced invalidity (props off, armed on the bench with motors disabled or `MOT_SAFE_DISARM`-style procedure) | `AHRS_UKF_TFAIL` > 0 → `thesis_nav_check` → LAND mode change (readiness H4(b); ruling 2026-10-08 "bench AND SITL") | 0.5 d |
| Hand-carried (motors off, in the mocap volume) | UKF shadow and **type 12 active** (disarmed: the output is computed, nothing steers); UKF vs mocap; flow sign under hand motion; watcher live on mocap | 0.5–1 d |
| Tethered hover | EKF3 flying first (the tune), then **UKF flying**; short hovers; forced invalidity once on the tether | 0.5–1 d |

---

## 9. Safety tests (U12)

**Required before free flight,** each with its SITL analogue already passed:
1. Forced backend invalidity → LAND: SITL V3, then bench, then tether.
2. Watcher killed or heartbeat withdrawn → LAND: SITL V6 or B-tests, then bench, then tether.
3. RC override wins over every autonomous mode (`FS_OPTIONS` bit 4; bench test B10).
4. Flow occluded (cover the sensor) in a tethered hover → LAND after the aiding timeout: SITL V4, then tether.
5. Battery failsafe parameters read back.

**Effort:** within U11, plus 0.5 d of write-up.

---

## 10. CPU and flash on the H743 (U13)

**CPU [E, Part C §5.3]:**
- The UKF in double on H7 costs **about 5–8 %** CPU, about **0.3–0.4 ms per predict**, against a 2.5 ms loop at 400 Hz.
- The worst loop combines a predict with the event-queue drain at the 60 ms horizon (flow X, flow Y and range updates,
  each a Cholesky plus 31 sigma points). That could reach **about 1 ms** [E].
- Measure with `PM` and `SCHED_DEBUG` on the bench.
- EKF3 still runs 2 lanes in shadow. If the loop overruns, the documented relief is `EK3_IMU_MASK 1` (one EKF3 lane).
  That changes only the shadow, which must then be stated.

**RAM [E]:**
- P 15×15, sigma 31×15 and the state copies in double come to about 10 kB.
- The event queue (`EV_MAX 64` × about 140 B) is about 9 kB.
- **Total about 20 kB**, against the H743's about 1 MB.

**Flash [V for the board margins, E for the fork]:**
- Free space in the published stable Copter builds (`docs/quadplane_costing.md` §9):
  - Pixhawk6X 287 kB, Pixhawk6C 376 kB, CubeOrange 322 kB;
  - KakuteH7 268 kB, MatekH743 150 kB.
- The fork's UKF and plumbing come to about 25–50 kB (Part C §5.5). It fits every board.
- On a Matek-class board, scripting (if a Lua watcher layer is wanted) may need features compiled out.
- Item 2(a) measures the real figure.

---

## 11. Risks

| risk | effect | mitigation |
|---|---|---|
| Rangefinder reads below its minimum on the ground | The UKF never initialises; no arming ("UKF not initialised") | U4 (initialise from `GNDCLEAR`); pick a sensor with a low minimum |
| **Mocap IR strobes disturbing a ToF rangefinder or flow sensor** [E, common indoor issue] | Range dropouts, then the 15 s vertical hold, then LAND; or flow quality collapse | Bench check inside the volume with the cameras running (U11 hand-carried) |
| Low-texture mocap floor | Flow quality low, then the 5 s timeout and LAND | Textured mats (as rung 1) |
| 5 s inertial dead reckoning before the trigger | Drift of the order of metres if velocity was biased | Watcher box sized for it; pre-registered |
| Yaw drift (no absolute yaw) | Path rotation of a few degrees per minute | Short profiles; 4-DoF scoring |
| Board ≠ SITL numerics | No bit-identical equivalence | Statistical check; Replay gate U10 |
| The single-lane UKF (no IMU redundancy) | One IMU fault is not caught by lane switching | Stated limitation; EKF3 shadow logged |
| SITL flow is idealised and uses the true gyro | Derotation and real flow noise untested before hardware | Hand-carried and tethered steps; U10 |
| Telemetry link dropouts | False GCS failsafe LAND | Measure the link; consider `FS_GCS_TIMEOUT` > the worst gap |
| `AHRS_UKF_TFAIL` left non-zero | A forced failure in flight | Arming refusal (§2) plus `ensure_params` |
| The eeprom gotcha (Known Issue #10) on a real FC | A parameter silently not applied | Readback after every flash (rung-1 R6) |

---

## 12. Calendar from the hardware arriving

**Preconditions, done before day 1:**
- U1 software (once the board is named);
- U2, U3, U4, U7, U14;
- F1, if the mocap protocol is known;
- the SITL flights V1–V7 (after 16 Oct).

**Day 1 is the day the rung-1 vehicle (an H7 Copter with its flow sensor and rangefinder on the FC) is available for
rung-3 work.** Ideally rung 1 has already flown, which gives the U10 logs.

| day | work |
|---|---|
| 1 | Flash the fork; bench 0: boot, readback, backends off = EKF3, shadow on, CPU (`PM`) |
| 2 | Bench: forced invalidity → LAND; arming refusals; watcher heartbeat and GCS failsafe; link gap. U10 Replay gate on the rung-1 logs (if not already done) |
| 3 | Hand-carried in the volume: UKF active (disarmed) against mocap; mocap IR check on the sensors; watcher live |
| 4 | Tethered: EKF3 hover, then UKF flying hovers; forced invalidity and flow occlusion on the tether |
| 5 | Buffer / fixes (a firmware fix means a reflash and repeating day 1's readback) |
| 6–7 | Free flights, UKF flying: first a hover, then the pre-registered profile, n = 3–5 |
| 8 | Scoring (`real_score.py`), METHODOLOGY entry |
| (9–10) | Contingency: one fix-and-reflash cycle, or mocap re-booking |

**About 8–10 working days from the hardware**, of which about 4 need mocap time (days 3, 4, 6, 7).
- If the vehicle needs assembly or tuning first, add rung 1's 3–6 d.
- If rung 1 has not flown, run its flights first: the U10 gate depends on them.

---

## 13. How it builds on rung 1

**Rung-1 items reused unchanged:**
- the vehicle and its sensors, the native flow and rangefinder drivers, and the bench orientation checks (R12);
- the parameter template (R6), with only U7 added;
- the flight cards (R11);
- the mocap recorder (R7) and `mocap_align` on `RISI` (R8);
- the scorer `real_score.py` with a pre-registered window (R9);
- the `LOG_REPLAY` logging (I1);
- the UKF port's geometry from the log (R2, fork-r1);
- the D18 own-gyro derotation (if option (b) of §3 is taken: one change serves both).

**What is new for rung 3:**
- the board build of the fork;
- U4;
- the live mocap client for the watcher;
- the forced-invalidity bench test;
- the tethered UKF hover;
- the stage-3 pre-registration.

**Option for the supervisor, not a recommendation:**
- Rung 1 could fly the **fork** with `AHRS_EKF_TYPE 3` and `AHRS_UKF_ENABLE 1`, giving an onboard UKF shadow on real
  sensors in the same flights. That is the cheapest pre-closed-loop gate, earlier than U10.
- It departs from "rung-1 firmware = `7bac20cbcc` unmodified", and it needs U1's "backends disabled reproduces EKF3"
  bench check first.

---

## 14. Open questions

1. **Board** (name and class): it decides the build target and the flash margin (150–376 kB).
2. **Flow sensor and rangefinder models**: the driver (Pixart/MAV against HereFlow decides the D18 path); the
   rangefinder's minimum range against the ground clearance (U4); the update rates for `SIM_FLOW_RATE`.
3. **D18 for the flying port:** accept the driver's rate (a) or adopt the own-gyro derotation (b) for rung 1 and rung 3
   alike?
4. **Compass:** fitted (nomag) or absent (`ALLOW_ARM_NO_COMPASS` in the build)?
5. **Rung-1 firmware:** stock `7bac20cbcc`, or the fork with the UKF in shadow (§13 option)?
6. **Mocap system and protocol** for the live watcher feed (F1); and is the watcher allowed to run on the ground laptop
   over a telemetry link?
7. **Profile for stage 3:** hover plus short GUIDED moves (scripted, as in SITL) or pilot-flown LOITER?
8. **Acceptance of the 5 s aiding-loss latency** before LAND, or a shorter UKF timeout? A shorter one would be a model
   change, not EKF3-matched.
9. **Freeze scope:** do closed-loop flights after 23 Oct still count toward the thesis?
