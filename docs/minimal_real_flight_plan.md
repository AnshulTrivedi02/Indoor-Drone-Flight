# Minimal real-flight plan (RUNG 1): costing against the 23 Oct freeze

Status: PLANNING ONLY. Written 2026-10-10 (a Saturday) on `fwd-camera` at `91e87c9`. Nothing was built, flown or
replayed to produce it. The only probes were reads of source, of the existing build trees, and one message census of an
existing SITL `.BIN` with pymavlink.

Rulings this plan implements:
- METHODOLOGY "RULINGS (user, 2026-10-10): the MINIMAL real-flight path";
- METHODOLOGY "RULINGS (user, 2026-10-10, SUPERSEDING the scope part …): real flights built as RUNGS". **This plan is
  rung 1.** Rung 2 (our Pi pipeline, open loop) and rung 3 (closed loop) are costed by rung in
  `docs/real_flight_readiness_by_rung.md`.

Companion documents: `docs/real_flight_readiness.md` (the 60-row checklist), `docs/real_flights_plan.md`, and
`docs/partC_onboard_feasibility.md` §3 (Replay).

Evidence tags:
- **[V]** verified here from source, a build tree or a log;
- **[E]** estimate;
- **[U]** unknown until the supervisor's hardware inputs arrive.

---

## 0. Rung 1 in one paragraph

A vehicle that the supervisor provides, running **stock ArduPilot**, with **its own flow sensor and rangefinder on the
flight controller** (no Pi, no camera pipeline, no forward camera). It is flown by **a safety pilot in ALT_HOLD**
(recommended), or by EKF3 in a position mode, inside the mocap volume. Logging uses `LOG_REPLAY=1` and
`LOG_DISARMED=1`, with mocap recorded throughout. Safety comes from ArduPilot's fence and the safety pilot. **Nothing of
ours steers.**

Offline afterwards, on the same real logs:
- EKF3 runs via ArduPilot Replay;
- the UKF port runs via Replay;
- the FGO runs via a dataflash-to-FGO converter.

All three are scored against mocap with the same alignment and the same window.

---

## 1. Inputs from the supervisor (on the critical path)

| # | input | what it changes here |
|---|---|---|
| S1 | **FC board.** An H7 is assumed (Pixhawk 6X/6C, CubeOrange(+), Durandal, MatekH743, KakuteH7: all have hwdefs at the pinned commit [V]). | Firmware build target. EKF precision: on H7, `HAL_HAVE_HARDWARE_DOUBLE` is 1 (`hwdef/scripts/STM32H743xx.py:76` [V]), so EKF3 runs in double as SITL/Replay do (`board/chibios.h:63-64`, `board/sitl.h:83-84` [V]). On an F7/F4 the board runs EKF3 in single precision while Replay runs it in double, so the two cannot be bit-exact. |
| S2 | **Is the vehicle already flying?** Which firmware version is on it? Is it tuned? | 0 d of airframe work if it is already flying. Otherwise assembly and tune cost 3–6 d (`A1`+`A2`), which **breaks the calendar** (§6). |
| S3 | **Flow sensor** (PMW3901-class on SPI = `FLOW_TYPE 2` Pixart; HereFlow = 6 DroneCAN; MTF-01/UPFLOW/MSP = 5/8/7 [V `AP_OpticalFlow.cpp:30`]) | `FLOW_TYPE`, `FLOW_ORIENT_YAW`, `EK3_FLOW_DELAY`, and the source of the derotation rate (§4.3: Pixart and MAV/MSP use the FC's gyro; HereFlow uses the sensor's own gyro [V]). |
| S4 | **Rangefinder** (TF-Luna/TFmini = Benewake serial; VL53L1X = I²C) | `RNGFND1_TYPE`, `MIN`/`MAX`, `GNDCLEAR`. The minimum range matters: a TF-Luna's 0.2 m minimum means it reads out of range on the ground. |
| S5 | **Mocap system** (OptiTrack/Vicon), rate, how recordings are exported, volume size, booking dates | The recorder (§4.5), the frame convention (OptiTrack streams Y-up by default), the flight profile size, and the calendar. |
| S6 | **Firmware choice:** the pinned `7bac20cbcc` built from unmodified source, or the nearest stock release (`Copter-4.7.0`) | §2. |
| S7 | **Floor:** can a plain (low-texture) sheet be laid in the volume? | Whether the degraded-sensing variable can be touched at all (§7). |

---

## 2. Firmware: pinned `7bac20cbcc` or stock `Copter-4.7.0`

**Facts [V]:**
- `7bac20cbcc` (tag `thesis-baseline`, 2026-04-22) is a **master** commit. It is not an ancestor of any Copter release.
- The nearest stable release is **`Copter-4.7.0`** (`1511f27194`, 2026-07-21), the current `ArduCopter-stable`. It
  branched from master at `ff0448a9cd` (2026-03-06).
- The pinned commit is 578 commits past that branch point; 4.7.0 is 390 past it. The whole-tree diff is 812 files.
- **EKF3/DAL commits unique to the pinned side** (patch-id, `--cherry-pick`): about 20. They include:
  - "make fusion update more consistent" refactors of FuseOptFlow, FuseVelPosNED, FuseBodyVel, FuseRngBcn,
    fuseEulerYaw, FuseMagnetometer and FuseDeclination;
  - zero-velocity fusion changes (`onGroundNotMoving`; `fusingStationaryZeroVel` capped at `NOAID_M_NSE`);
  - "inhibit accel bias learning when on ground and moving";
  - `EK3_MAG_CAL=7`;
  - `AP_GPS_FixType` plumbing;
  - position/velocity uncertainty exposure.
- **EKF3 commits unique to 4.7.0:** 4.
  - "zero del vel bias states after covariance update";
  - "prevent yaw measurement time delay exceeding IMU buffer age";
  - synthetic airspeed only if fly-forward;
  - log baro offset.
- **Several of these touch flow fusion, zero-velocity fusion and accel-bias learning**, so the two EKF3s are not
  numerically the same filter. Neither has a GPS dependence that matters here.
- **The replay record format is identical**: `git diff --quiet Copter-4.7.0 7bac20cbcc -- libraries/AP_DAL/LogStructure.h`
  passes [V]. A 4.7.0 `LOG_REPLAY` log should therefore parse in a pinned-commit Replay. This is [E] until it is tried
  on the first real log.
- **The fork** (`~/ardupilot_ukf`, branch `ukf-jitter-fix`, `abb0357d`, based on `7bac20cbcc`) **has no change to
  `libraries/AP_NavEKF3`**. Its `AP_DAL` adds only 14 lines of replay hooks, which are null in vehicle builds [V].

**Recommendation: fly the pinned `7bac20cbcc`, built from a CLEAN checkout for the board.**
- **Reason 1:** EKF3 on the vehicle is then the same EKF3 as every simulated result.
- **Reason 2:** the fork's existing Replay binary (`~/ardupilot_ukf/build/sitl/tool/Replay`, built 9 Oct) then
  contains **both** that EKF3 and the UKF port (`strings` finds "thesis shadow UKF" [V]). One binary, one run per log.
- **Clean checkout:** use a fresh `git worktree` at the tag, because `~/ardupilot` has an untracked `ArduCopter/scripts/`
  [V].
- **Toolchain:** `arm-none-eabi-gcc` 10-2020-q4 (the ArduPilot-recommended version) is installed
  [V].
- **Effort:** 0.5 d to configure, build (`./waf configure --board <B>; ./waf copter`) and archive the `.apj`, plus the
  parameter dump. A further 0.5 d to flash and rehearse rollback to the vehicle's current image [E].

**If the supervisor prefers a stock release (`Copter-4.7.0`):**
- Flash the release `.apj` (0.25 d). Alternatively, if the vehicle already runs 4.7.0, change nothing.
- Build a **stock Replay at `Copter-4.7.0`** for EKF3 (clean worktree, `./waf configure --board sitl; ./waf replay`;
  0.5 d) [E].
- The UKF still runs in the fork's Replay, on the same log (same DAL format).
- **State in the thesis:** "the real EKF3 is ArduPilot 4.7.0, which differs from the simulated EKF3 (`7bac20cbcc`) by
  the commits listed above".
- Optional sensitivity check (0 d extra): the fork's Replay also replays the pinned EKF3 on the 4.7.0 log, which gives
  "pinned EKF3 on real data" as a secondary row.
- **If the vehicle runs an older release (≤ 4.5)**, check the DAL format diff against that tag before relying on it [U].

---

## 3. The flight itself

### 3.1 Who flies

- **Recommended: a pilot flying in ALT_HOLD.**
  - Height comes from EKF3 (rangefinder, `EK3_SRC1_POSZ 2`). The horizontal path does not depend on any estimator.
  - This is the same argument as the 2026-07-22 decision to fly SITL on truth: the trajectory must not be shaped by the
    estimator under test.
  - It also needs the least tuning.
- **Alternative: EKF3 flying in LOITER/GUIDED.** Possible only if EKF3's flow navigation is proven on the bench and in a
  hover first. In the no-yaw configuration EKF3 drifts in yaw (sim: about 8°/min), so a held position walks.
  Not recommended for rung 1.

### 3.2 Profile (to be pre-registered; sized to the volume, S5)

1. **Disarmed, logging:** pick the vehicle up and rotate it sharply about all axes for about 5 s (the **sync
   wiggle**), then set it down. Stand clear.
2. Arm. Take off to about 1.0–1.5 m (above the rangefinder minimum, inside the flow sensor's range). **Hover for at
   least 25 s.** EKF3 needs gyro-bias convergence before flow aiding starts: about 16 s in SITL (CLAUDE.md "EKF3
   Solution Diagnosis").
3. Fly a slow rectangle or out-and-back at about 0.3–0.5 m/s for 60–120 s, then hover for 10 s.
4. Land and disarm. Do a second **sync wiggle** while still logging. Then stop the log.

- **n:** 3–5 repeats on one floor. If S7 allows, add 3 repeats over a plain sheet (§7).

### 3.3 Parameter template (`real_rung1.parm`, new; 1 d to write, plus 0.5 d bench readback)

Every name must be checked against the parameter metadata **of the commit actually flown**. Parameter names are not
trusted from memory (CLAUDE.md Conventions).

| group | settings | notes |
|---|---|---|
| EKF3 sources | `AHRS_EKF_TYPE 3`; `EK3_SRC1_POSXY 0`, `VELXY 5`, `POSZ 2`, `VELZ 0`, `YAW 0`; `EK3_FLOW_USE 1` | As `gnss_denied.parm` + `gnss_denied_nomag.parm`. **Never carry over `AHRS_EKF_TYPE 10`** from `consolidated_rerun.parm`. |
| GPS | `GPS1_TYPE 0` | As the Hidden Configuration Audit §2. There is no `SIM_*` on hardware. |
| compass | `COMPASS_ENABLE 1`, `COMPASS_USE/USE2/USE3 0`, `EK3_SRC1_YAW 0` | **FLAG: is the nomag config still wanted for real?** Recommended: YES, so that all three estimators have no absolute yaw, as in the comparison. Replay can re-run EKF3 with compass fusion from the same log, as a sensitivity row (`RMG*` records are logged). Real-hardware check: the compass must be present and **calibrated** to pass Copter's compass-health arming gate (Hidden Configuration Audit §3). Bench item. |
| flow | `FLOW_TYPE` per S3; `FLOW_ORIENT_YAW` (mount); `FLOW_POS_X/Y/Z` (measured, FRD from the IMU/body origin); `FLOW_FXSCALER`/`FYSCALER` 0 unless calibrated; `EK3_FLOW_DELAY` (the sensor's documented value) | `FLOW_OPTIONS` must **not** set "Stabilised", as in SITL. |
| rangefinder | `RNGFND1_TYPE` per S4; `RNGFND1_ORIENT 25`; `MIN`/`MAX` from the datasheet; `POS_X/Y/Z` measured; `GNDCLEAR` = the measured resting reading | `EK3_RNG_USE_HGT -1` (unchanged). |
| failsafes | `FS_EKF_ACTION 1` (LAND); battery failsafe; RC loss → LAND; a dedicated RC switch to STABILIZE as the last resort | ALT_HOLD itself is the flying mode. |
| fence | `FENCE_ENABLE 1`; `FENCE_TYPE 1` (max altitude) with the AGL/rangefinder altitude frame (parameter at `AC_Fence.cpp:170-177`; name to be checked at the flown commit); `FENCE_ALT_MAX` below the volume top; `FENCE_ACTION` LAND | **The circle/polygon fence needs an EKF origin and home.** `AC_Fence.cpp:513-535` gives "Fence requires position" [V]. With no GPS this means a `SET_GPS_GLOBAL_ORIGIN` step before arming, and it then uses EKF3's drifting relative position. It is therefore **secondary at best**. **The safety pilot, with a person watching mocap, is the primary layer.** |
| logging | `LOG_REPLAY 1`, `LOG_DISARMED 1`, `LOG_BITMASK` with IMU and OF; raise `LOG_FILE_BUFSIZE`; check `DSF` for dropped blocks after every flight | The full-rate IMU comes from `RISI` (400 Hz deltas, §4.3), so `INS_LOG_BAT_*` is optional. |
| rates | `SCHED_LOOP_RATE 400`, all EKF3 `*_NSE` at default | This keeps the UKF/FGO noise matching (dt 0.0125 s) valid. Record the INS filters and notch, with no retuning. |

After every flash: restore from the dump plus this file, then read back. The eeprom gotcha (Known Issue #10) applies to
a real FC too.

---

## 4. Offline afterwards

### 4.1 EKF3 via Replay

- **Builds and runs here [V]:**
  - `~/ardupilot_diag/build/sitl/tool/Replay` (EKF3-only diagnostic);
  - `~/ardupilot_ukf/build/sitl/tool/Replay` (EKF3 + UKF port).
  - Replay is a `sitl`-board program (`Tools/Replay/wscript`, built with the `sitl` configuration).
- **Already shown faithful on SITL logs.** D8 replayed 16 `dsn` logs flown with `LOG_REPLAY=1`. Every baseline
  reproduced the dataset's EKF3 score to ≤ 1 mm (METHODOLOGY "D8 result").
  - The brief's premise "SITL logs so far had `LOG_REPLAY=0`" holds only for the original `dsn`/`fwd` datasets.
  - From the re-fly onwards, flights carry `LOG_REPLAY 1` [V]. `cl_a_tex_half` has 107 360 `RFRH`, 214 721 `RISI`,
    7 955 `ROFH` and 227 `RRNI` records.
- **On a real-board log** the acceptance test is `Tools/Replay/check_replay.py` (compares `XKF*` original against
  replayed) on the first real log, which is the hand-carried log (§5).
  - Expected: close but not necessarily bit-exact. ARM and x86 double arithmetic can differ (FMA contraction).
  - **Pre-register a tolerance**: e.g. `XKF1` position within 1 cm and yaw within 0.1° over the flight [E].
  - If Replay does not reproduce the onboard log, the thesis must say "EKF3 (replayed)", not "the onboard EKF3".
- **Effort:**
  - 0 d of building if the pinned commit flies;
  - 0.5 d if 4.7.0 flies (a stock Replay build);
  - plus 0.5 d for the check-and-tolerance step.

### 4.2 The UKF port via Replay

- **Compiled in? Yes [V].**
  - `AP_NAVUKF_ENABLED` is `CONFIG_HAL_BOARD == HAL_BOARD_SITL` (`AP_NavUKF.h:29`), and Replay is built for the `sitl`
    board.
  - `Tools/Replay/Replay.cpp:32-38,305-321` in the fork instantiates `NavUKF replay_ukf` and wires the DAL hooks
    (`ukf_update_hook`, `ukf_flow_hook`, `ukf_extnav_hook`).
  - It needs no board build: the board's stock firmware does not need the UKF for rung 1.
- **Output:** `ukf_shadow.csv`, with `ukf_inputs.csv` as an input dump. Replay's logger does not emit FMT records for the
  UKF's dynamically named messages (METHODOLOGY "Replay logging note"), so no dataflash output is used.
  - `eval/ukf_shadow_replay_check.py` already reads this CSV.
  - A CSV → TUM-on-FC-clock step is needed: 0.25 d.
- **What must change for real sensors (a cost the port has today):**
  - `AP_NavUKF.cpp:33` hard-codes `RANGE_LEVER 0.12` and `CAM_OFFSET 0.25`, and `:29` hard-codes `RNG_MIN 0.05` and
    `RNG_MAX 40`.
  - `:38` hard-codes `FLOW_DELAY_MS 10`.
  - The Replay flow hook passes `(quality, rate, gyro, ms)` and **drops `ROFH.posOffset`**. The rangefinder's
    `RRNI.pos_offset` is also unused.
  - **Fix:** pass the flow and range body offsets through from DAL; read `EK3_FLOW_DELAY` and `RNGFND1_MIN/MAX`;
    keep the defaults.
  - **Acceptance:** on the existing SITL `LOG_REPLAY` logs (`ROFH.PZ 0.25`, `RRNI.PZ 0.12` [V]) the UKF output must
    stay **byte-identical**. Then rebuild the fork's Replay.
  - **Effort: 0.5–1 d** [E].
- **The port reads the FC's OF directly** (D18 note). Its flow model is the shared one:
  - axis 0 is `−v_y/h + g_x` and axis 1 is `v_x/h + g_y`, in FRD (`AP_NavUKF.cpp:208-211`), with `g` = the
    `bodyRate` that the OF backend delivers;
  - that is the same convention as `measurement_models.h_flow_pose`.
  - So no sign change is needed (§4.3).

### 4.3 The FGO via a dataflash → FGO-input converter

**What the FGO consumes today** (`src/estimators/fgo/fgo_replay.py:50-62`):
- `/imu/data_raw` (333 Hz HIGHRES_IMU, FLU);
- `/optical_flow/measurement` (`flow_x_rad`, `flow_y_rad`, `valid`, `inlier_ratio`);
- `/downward_lidar/range`;
- `/attitude/angular_rates`;
- (`/ground_truth/pose` for diagnostics only).

Processing:
- the gap rule (`imu_gaps.json`), `dejitter_imu`, and the flow gate `valid and inlier > 0 and |rate| < 4.2`
  (`fgo_core.py:172`);
- interval-averaged gyro derotation (`FlowFrameGyroAverager`).

The C++ FGO also accepts a raw event stream (`<P>.raw.f64` + `<P>.init.json`, `fgo_export.py` EV_COLS = 9).

**What a `LOG_REPLAY` dataflash provides [V, census of `cl_a_tex_half`]:**

| record | content | rate |
|---|---|---|
| `RFRH` | DAL frame header, `TimeUS` | 400 Hz (every IMU frame) |
| `RISI` | per IMU instance: delta velocity, delta angle, their dts, flags (FRD) | 400 Hz × instances |
| `ROFH` | exactly EKF3's flow input: `rawFlowRates` (FX, FY), `rawGyroRates` (GX, GY), `msecFlowMeas`, `posOffset`, `Qual` | per flow update |
| `RRNI` | rangefinder distance, status, orientation, `pos_offset`; **written only on change** (227 records against 5 388 `RFND`) | on change |
| `OF` | flowX/flowY/bodyX/bodyY/Qual, the same values as `ROFH` | per flow update |
| `IMU` | logged IMU | about 25 Hz only: not usable for the FGO |

**Converter specification (`eval/bin2fgo.py`, new):**
1. **Clock:** everything is on the FC's `TimeUS`. Each `R*` record takes the `TimeUS` of the preceding `RFRH`. There is
   **one clock**: rung 1 needs no Pi ↔ FC map.
2. **IMU:** from `RISI` of **the instance EKF3 core 0 uses** (the scored lane):
   - `acc = DV/DVDT`, `gyro = DA/DADT`;
   - FRD → FLU as `(x, −y, −z)` (at rest `DVZ/DVDT ≈ −9.81` FRD → +9.81 FLU [V]);
   - stamped at the frame time.
   - Check, on the first log, that `DVDT`/`DADT` match the `RFRH` spacing. SITL shows 2.0 ms deltas inside 2.5 ms
     frames.
   - `RISI` deltas are the INS-integrated deltas that EKF3 consumes. This **removes the "rectangular integration of
     instantaneous HIGHRES_IMU samples" caveat** for rung 1.
3. **IMU timing rules:** `dejitter_imu` and the gap rule were built for the 333 Hz HIGHRES stream. Parametrise the
   nominal period (2.5 ms). Gaps are detected from `RFRH` continuity, and dropped blocks from `DSF`.
4. **Flow:**
   - `flow_x_rad := ROFH.FX`, `flow_y_rad := ROFH.FY`, in the sensor-native convention after `FLOW_ORIENT_YAW` and the
     scalers.
   - The mapping is the **identity**. The SITL bridge sends `flow_rate_x = +flow_x_rad`, `flow_rate_y = +flow_y_rad`
     (`flow_bridge.py:27-31`).
   - ArduPilot requires every flow backend to deliver EKF3's convention: positive rate for a positive body rotation,
     with EKF3 negating at `AP_NavEKF3_Measurements.cpp:221`.
   - The shared `h_flow_pose` already uses that convention: `flow_x_rot = +ω_x`, `flow_y_rot = −ω_y` FLU =
     `+ω_y` FRD.
   - **So `h_flow` needs no sign change** for a correctly configured sensor. `FLOW_ORIENT_YAW` must be right, and the
     hand-carried check (§5) proves it.
5. **Flow validity:** `valid := Qual > 0` and |rate| < 4.2, which is EKF3's rule (`:203`).
   - `inlier := Qual/255` is a pass-through only, because the FGO gate uses `inlier > 0`.
   - The pre-registered camera rule (inlier ≥ 0.85, features ≥ 20) **does not apply** to rung 1 (ruling 2026-10-10).
6. **Flow time: NEEDS A RULING (proposed default below).**
   - There is no capture stamp. "Arrival" is the `TimeUS` of the `RFRH` frame preceding the `ROFH` record (= EKF3's
     `imuSampleTime_ms` at `writeOptFlowMeas`), not `ROFH.msecFlowMeas`.
   - **Proposed default: EKF3's own rule**: arrival − `EK3_FLOW_DELAY` − `flowTimeDeltaAvg_ms/2` (50) −
     `filterStep/2` (6), floored at the fusion horizon. This is exactly what the port does (`AP_NavUKF.cpp:554`).
   - **Caveat:** `flowTimeDeltaAvg_ms = 100` is a hard-coded constant (`AP_NavEKF3.h:511` [V]). It assumes a 10 Hz
     sensor, so the 50 ms term is wrong for a faster sensor (EKF3's own error, shared by all three under this rule).
   - **Alternative:** arrival − `EK3_FLOW_DELAY` only, for the UKF/FGO.
   - Either way this **changes the simulation's fairness rule**, where the UKF and FGO used capture stamps. It must be
     ruled on and stated next to any sim-to-real comparison (§9 question 9).
7. **Derotation rate:** use `ROFH.GX/GY` (the `bodyRate` EKF3 and the port use; D18) as the flow's omega, FRD → FLU,
   instead of the FGO's own interval average.
   - Where that rate comes from depends on the sensor:
     - Pixart, MAV and MSP use the FC's AHRS gyro averaged over the flow interval (`AP_OpticalFlow_Pixart.cpp:291-303`,
       `AP_OpticalFlow_MAV.cpp:38-42,76`);
     - **HereFlow uses the sensor's own gyro** (`AP_OpticalFlow_HereFlow.cpp:82`).
   - Report the FGO's interval average against `ROFH.G` as a diagnostic.
8. **Range:**
   - `RRNI` is write-on-change, so hold the last value. Emit at 30 Hz while `Status` is Good: the port's rule since its
     range bug fix (METHODOLOGY "Shadow test in ArduPilot Replay").
   - Out-of-range and no-data samples are dropped.
9. **Initialisation:**
   - Levelling over the first 0.5 s of `RISI` after logging starts, as now.
   - The initial height is taken from `RNGFND1_GNDCLEAR` (plus the lever arm), **not** "the first in-range sample". With
     a 0.2 m-minimum sensor the first in-range sample arrives mid-climb.
10. **Geometry:** make `RANGE_LEVER`, `CAM_OFFSET` (= the flow sensor's `FLOW_POS_Z`), `H_MIN`, `RNG_MIN`/`MAX` and
    `FOCAL_LENGTH_PX` (unused here) **overridable**. Values are read from the log's `PARM`/`ROFH`/`RRNI`.
    - **Defaults stay unchanged**, so every simulation result stays byte-identical. This matters during the sim
      freeze to 16 Oct.
    - Lateral `FLOW_POS_X/Y` lever arms enter `h_flow_pose` through `FLOW_LEVER_ARM_BODY` (FLU), which today is z only.
11. **Other hard dependencies of `fgo_replay.py`** that a `--bin` mode must replace:
    - **Arm time.** `imu_gaps.json` → `arm_header_s` feeds `GroundProximityFlow` (the D15 rule shared with the UKF).
      Take it from the log's `ARM`/`EV` records. This also replaces the "run `imu_gap_check --write` first" step,
      which works on bags only.
    - **The `att` stream** (omega fallback and pre-init omega): synthesise it from `RISI` gyro, or guard the path.
    - **Ground truth:** the `gt` array and `f_filter_forward(ev, gt[:,0], …)` assume `/ground_truth/pose`. Feed mocap,
      or bypass them (no forward-camera events in rung 1). An empty `gt` fails at indexing.
12. **Output:** the in-memory event list for `fgo_replay.py` (a `--bin` input mode), plus optionally `<P>.raw.f64` for the
    C++ FGO. **Rung 1 uses the Python FGO** (the corrected build, initial yaw σ 1°). The C++ FGO is optional.

**Hardware-free acceptance test (planned, not run):**
- `cl_a_tex_half` (EKF3 flew, `LOG_REPLAY 1`) has **both** the bag and the BIN.
- The converted IMU, flow and range from the BIN must match the bag's `/imu/data_raw`, `/optical_flow/measurement`
  and `/downward_lidar/range`:
  - signs;
  - units;
  - timing within the documented clock map (`eval/input_timing.clock_map`).
- FGO-from-BIN must track FGO-from-bag within a pre-registered band (e.g. evo -a (cruise) within 5 cm). Some
  difference is expected and is the test's point: 400 Hz deltas against 333 Hz samples, and EKF3 flow timing against
  capture stamps.
- This runs **after 16 Oct** or as a light job, because it is a single replay and not a batch.

**Effort:**
- converter 1.5–2 d;
- arm time, `att` stream and ground-truth dependencies (item 11) 0.25–0.5 d;
- geometry overrides plus regression 0.5–1 d;
- SITL acceptance test 0.5 d;
- **total 3–4 d** [E].

### 4.4 Is the shared `h_flow` model still right for a flow sensor? (D18)

- **Signs: yes** (§4.3 item 4).
- **Lever arms:** they must come from the real mount (item 10).
- **Scale:**
  - the camera's rad/s came from a focal length;
  - the sensor's rad/s comes from its driver scaling, plus `FLOW_FXSCALER`/`FYSCALER`;
  - any scale error is shared by all three estimators, because all read the same `ROFH` values.
- **Interval:** a dedicated sensor integrates over its own window. Using `ROFH.G` for derotation keeps the rotational
  term consistent with what EKF3 cancels. This is a **model input change, not a geometry change**, and it is recorded
  as a D18 rung-1 note.
- **No other model change is needed.**

### 4.5 Scoring against mocap

**What exists [V]:**
- `eval/mocap_align.py`:
  - time map mocap ↔ FC from |ω|, fitted in an early (take-off) and a late (landing) window;
  - 4-DoF frame fit on an initial segment, plus a whole-flight 4-DoF fit;
  - mocap TUM written on the FC clock, in the estimator frame.
  - It was self-tested only: offset −3.7 ms, rate 4.9 ppm, yaw 0.30°.
- `eval/three_way_eval.py`: evo -a on a pinned cruise window.

**What is missing:**

| item | why | effort |
|---|---|---|
| Mocap recorder | Depends on the system. OptiTrack: Motive take → CSV export. Vicon: Nexus/Tracker export or a VRPN client. A small adapter to the `mocap_align` CSV (`t_s, x, y, z, qx, qy, qz, qw`, metres, **Z-up**: OptiTrack's default is Y-up, so convert). A live ROS 2 client is NOT needed for rung 1. | 0.5–1.5 d [U S5] |
| `mocap_align` on `RISI` | It reads `IMU` at about 25 Hz. Switch the |ω| feature to `RISI` delta angles (400 Hz). `RISI` deltas are accumulated from the **raw** gyro, before `apply_gyro_filters` (`AP_InertialSensor_Backend.cpp:364-371` [V]), so the 11.3 ms group-delay shift must then be dropped. Re-run the SITL self-test against `SIM` to confirm. The sync wiggles (§3.2), done disarmed with `LOG_DISARMED 1`, give the early and late windows. | 0.5 d |
| Scorer (`eval/real_score.py`, new) | `three_way_eval`'s cruise window (truth speed > 0.30 m/s, the largest run, built for the corridor) does not fit a hover-plus-rectangle flight. The new scorer takes the replayed `XKF1` (core 0), the UKF CSV and the FGO trajectory, all on the FC clock, against the mocap TUM. **Window pre-registered before flying**, e.g. from take-off + 25 s to landing − 5 s. evo -a (4-DoF) plus the start-aligned drift (`mocap_align`'s initial-segment fit). | 1–1.5 d |
| Lever arm | The 4-DoF fit takes a constant mocap-marker ↔ IMU offset. The rotation-coupled part is small (sub-cm at these tilts) and is stated, not modelled. | 0 d |

---

## 5. Build list (rung 1)

Efforts are [E], for one person, with agents coding in parallel. "SW now" means it can start today with no hardware.

| # | item | effort | depends on | SW now? | risk |
|---|---|---|---|---|---|
| R1 | **Converter** BIN → FGO inputs (§4.3), with geometry overrides and the SITL acceptance test on `cl_a_tex_half` | 3–4 d | — | **yes** | **Medium.** Timing rules for 400 Hz deltas; `RISI` dt quirks; the SITL band may need a justified width. |
| R2 | **UKF port for real geometry** in Replay: DAL offsets, `EK3_FLOW_DELAY`, range limits; byte-identical on SITL; rebuild the fork's Replay (sitl board, light) | 0.5–1 d | — | **yes** | Low |
| R3 | UKF CSV → TUM on the FC clock | 0.25 d | R2 | yes | Low |
| R4 | **EKF3 Replay**: 0 d if pinned flies, 0.5 d stock Replay if 4.7.0 flies; `check_replay.py` acceptance with a pre-registered tolerance | 0.5–1 d | S6, first real log | partly | **Medium.** Not bit-exact on ARM; a non-H7 board makes it single against double. |
| R5 | **Firmware** for the board: pinned commit, clean worktree, build, archive, flash, rollback rehearsal (or flash stock 4.7.0) | 0.5–1 d | S1, S6 | build: once S1 is known | Low–medium. Bootloader and flashing quirks; the vehicle's existing parameters. |
| R6 | **Real-sensor parameter template** (§3.3) plus bench readback, `DSF` check and the compass arming check | 1.5 d | S1, S3, S4 | draft: yes | **Medium.** Sensor driver setup; compass calibration; the fence-origin question. |
| R7 | **Mocap recorder/adapter** plus the frame convention | 0.5–1.5 d | S5 | partly | Medium [U] |
| R8 | **`mocap_align` on `RISI`**, group-delay rule, SITL re-self-test | 0.5 d | — | **yes** | Low |
| R9 | **Scorer** `real_score.py` with the pre-registered window | 1–1.5 d | R3, R8 | **yes** | Low |
| R10 | **Pre-registration** of rung 1: profile, n, window, metrics, Replay tolerance, converter band, claims | 0.5 d | — | **yes** | Low |
| R11 | **Flight cards**: pre-flight (parameter readback, `DSF`, origin if a circle fence is used, mode switches, fence test), sync wiggles, profile, abort calls, post-flight (log download, `DSF`, pipeline run) | 1 d | R6 | **yes** | Low |
| R12 | **Bench (props off)**: sensors healthy; flow orientation (rotate the vehicle and check that `OF.bodyX/Y` and `flowX/Y` agree in sign: ArduPilot's standard flow check); rangefinder on the ground and lifted; `LOG_REPLAY` log complete | 0.5–1 d | R5, R6 | no | Medium |
| R13 | **Hand-carried check in the volume** (motors off): carry the vehicle along the profile at flight height, with sync wiggles at both ends. **The SAME DAY**, run the whole offline pipeline (R4, R2, R1, R8, R9) on that log. This is the end-to-end rehearsal and the first real Replay check. **Limit:** disarmed, EKF3 stays `onGround` and never detects take-off (`AP_NavEKF3_VehicleStatus.cpp:466-480` [V]), so the D15 ground-proximity treatment applies and flow does not drive translation. The hand-carry therefore proves plumbing, sync, flow-sensor sign and Replay reproduction of a non-aiding EKF3. **Flow navigation is first tested in the first hover** (or by carrying the vehicle armed with props off, if the lab allows it). | 0.5 d + 0.5 d pipeline | R12, R7, R1–R9 | no | **Medium–high.** First contact of every tool with real data. |
| R14 | Flight day(s): first hover, then n = 3–5 repeats (+3 over a plain sheet if S7) | 1–1.5 d | R13, mocap booking, safety pilot | no | **High.** Hardware, weather-free but lab-bound. |
| R15 | Offline runs + scoring of all flights, plus a METHODOLOGY result entry | 1 d | R14 | no | Low |
| — | *If the vehicle is not already flying:* assembly, tune, hover learn (`A1`, `A2`) | **+3–6 d** | S2 | no | **High; breaks the calendar** |

**Totals [E]:**
- software that can start now (R1–R3, R8–R11 and the R6 draft): **7.5–10 d** of work, mostly agent-coded and reviewed
  by one person;
- hardware and on-site work (R4 check, R5, R6 bench, R7, R12–R15): **5–8 d**;
- **total 12.5–18 person-days.**
- Because agents can run the software chain in parallel during the sim-priority week, the **elapsed** time is set by
  the hardware chain.

---

## 6. Calendar to the freeze (Fri 23 Oct)

There are 10 working days (Mon 12 – Fri 23), plus this weekend. Simulation work keeps priority until Fri 16 Oct
(ruling). Rung-1 software runs as coding alongside it, with no simulator and no heavy jobs.

| dates | work | gate |
|---|---|---|
| Sat 10 – Sun 11 | R10 pre-registration draft; agents start R1, R2, R8 (code only) | — |
| **Mon 12** | **Supervisor inputs S1–S7**; firmware decision S6; mocap booking | **D1: inputs received.** If there is no answer by Tue 13, rung 1 is at risk. |
| Mon 12 – Wed 14 | R1 converter, R2 port change, R8, R9 scorer, R3 (agents); R6 template draft; R11 cards | — |
| Thu 15 – Fri 16 | R5 firmware build and flash; R6 bench readback; R12 bench (flow orientation, rangefinder, log completeness); R1/R2 SITL acceptance tests (light single replays) | **D2 (Fri 16): a flying vehicle with working flow and rangefinder on the bench, logs complete.** If not, rung 1 is NOT reached by 23 Oct. |
| Mon 19 | R7 recorder test; **R13 hand-carried check + same-day pipeline** | **D3: Replay check passes on the hand-carried log (or its failure is characterised), the converter runs on real data, the scorer gives numbers.** The flow-aiding Replay check is repeated on the first hover log (Tue 20). |
| Tue 20 | fixes; first hovers (pilot, ALT_HOLD) | — |
| Wed 21 | R14 main flights: n = 3–5 (+ plain sheet if S7) | — |
| Thu 22 | R15 offline runs and scoring; spare flight slot | — |
| Fri 23 | buffer; freeze | — |

**Verdict: FITS ONLY IF all of the following hold.**
- (i) The supervisor provides, **by about Fri 16 Oct**, an H7 vehicle that **already flies** with its flow sensor and
  rangefinder on the FC, plus a safety pilot.
- (ii) Mocap time is available on about **19–21 Oct**.
- (iii) The firmware decision is made on Mon 12. Either is acceptable; the pinned build costs 1 d more.
- (iv) Agents carry the software items (R1–R3, R8–R11) during the sim-priority week.

If the vehicle needs assembly or tuning (+3–6 d), it **DOES NOT FIT**.

**A useful relaxation to ask about:** if the freeze covers *experiments* (flying) but not the offline analysis of
already-recorded logs, then R1–R4, R9 and R15 leave the critical path. Rung 1 then only needs R5–R7 and R10–R14 by
23 Oct.

---

## 7. What the thesis can claim from rung 1, and the limits

**Claim:** a **sim-to-real check of the standard-sensor comparison**. EKF3, the UKF port and the FGO run OFFLINE on the
SAME real logs (same IMU deltas, same flow records, same range, same flow timing) and are scored against mocap with one
alignment and one window. It tests whether the simulated ranking and the size of the gaps (nominal texture) carry over to
real sensors.

**Limits (state them plainly):**
1. **The flow source differs.**
   - Rung 1 uses a dedicated flow sensor (its own optics, integration window and quality metric). The thesis's camera
     pipeline (Shi-Tomasi + LK + RANSAC, inlier ratio) is not used.
   - The **degraded-sensing variable is NOT replicated** unless the floor texture is varied (S7). Even then, the
     sensor's quality metric is not our inlier ratio.
   - Without a plain-floor condition, rung 1 speaks to the nominal arm only.
2. **No closed loop.** No estimator of ours steers. The trajectory is the pilot's (or EKF3's). This gives no stability
   or closed-loop claim (as in SITL, Hidden Configuration Audit §1).
3. **EKF3 in Replay is "the onboard EKF3" only if Replay reproduces the onboard log**, within the pre-registered
   tolerance (§4.1). This holds best with an H7 (double precision on both sides) and the pinned firmware. If 4.7.0
   flies, the real EKF3 is a different EKF3 version from the simulated one (§2).
4. **Hardware n:** 3–5 flights, one vehicle, one floor (maybe two), one day. **Report the per-flight results and their
   spread. No significance claims.** This matches the simulation's n = 3 caution.
5. **Yaw/compass:**
   - **Recommended: the nomag config** (compass present, not fused), so that all three lack absolute yaw, as in the
     comparison.
   - Real indoor yaw drift may differ from the simulation's 8°/min. The 4-DoF alignment absorbs the initial yaw, not
     the drift.
   - A compass-on EKF3 Replay is possible as a labelled sensitivity row only.
6. **Flow timing:** on real logs all three estimators use EKF3's arrival-minus-delay flow time. In the simulation the
   UKF and FGO used capture stamps. This difference must be stated next to any sim-to-real comparison.
7. **The derotation rate** comes from the OF backend (`ROFH.G`) for all three. With a HereFlow it is the sensor's own
   gyro.
8. **Mocap ↔ FC time** comes from the |ω| fit. It is validated on synthetic data only until the hand-carried log.
   Report its residual.
9. **Short flights** (60–120 s in a mocap volume, against 300 s and 150 m corridors). The long-duration drift results
   are not re-tested.

---

## 8. What "closed loop is not rung 1" removes from the readiness checklist

The 2026-10-10 rungs ruling supersedes "closed-loop real flights are future work". Closed loop is **rung 3**, the target,
and it becomes future work only if it is not reached by 23 Oct. For **rung 1**, these readiness rows are NOT needed:
- **Pi, link and clocks:** A3–A7, A9, A10, B1–B4;
- **camera flow and its rule:** D1, D2, D4 (camera), D5 (camera), D6, D7, E1;
- **fork firmware and estimators onboard:** C4, C7 (C++/port-wide parametrisation, beyond R1/R2), C8, G1b, G2–G10;
- **the mocap watcher chain:** F1 (live client), F2, F3, F4, and the G1–G11 gaps of plan §7.2;
- **safety tests and staging for steering estimators:** H1, H2, H3, H4 item (b), H8 (unless the vehicle is new), H10.

Rung 1 keeps:
- **vehicle and firmware:** A1/A2 (supervisor's vehicle), A8, G1a;
- **parameters:** C1–C3, C5/C6 (record only);
- **calibration:** D3 (flow, rangefinder and marker offsets only), D4 (`EK3_FLOW_DELAY` from the datasheet), D5 (flow
  sensor orientation);
- **safety and staging:** H5, H6 (FC fence only), H7, H9 (rung-1 pre-registration);
- **logging and truth:** I1, I3, I4 (mocap ↔ FC only), G11 (via R1/R2).

The full mapping, with efforts by rung, is `docs/real_flight_readiness_by_rung.md`.

---

## 9. Open questions for the supervisor

1. **FC board** (H7?), and is the vehicle **already flying and tuned** with its flow sensor and rangefinder on the FC?
   Can it be handed over by about **16 Oct**? Which firmware is on it now?
2. **Firmware:** may we flash the pinned `7bac20cbcc` (unmodified source, built here), or should we use stock
   `Copter-4.7.0`?
3. **Flow sensor and rangefinder models**: the interface, the rangefinder's minimum range, and the mount positions.
4. **Mocap:** OptiTrack or Vicon? Rate, export path, volume size, and **booking on about 19–21 Oct**.
5. **Safety pilot and lab rules:** ALT_HOLD by a pilot as the default. Is a net or tether required?
6. **Floor:** can a plain sheet be laid, to give a degraded condition?
7. **Compass:** keep the comparison's nomag configuration for the real flights (recommended)?
8. **Freeze scope:** does the 23 Oct freeze cover the offline analysis of logs recorded before it, or only the flying?
9. **Flow timing on real logs (ruling needed):** the UKF/FGO adopt EKF3's arrival − delay − 50 − 6 ms rule (proposed),
   or arrival − `EK3_FLOW_DELAY` only? Either way it replaces the simulation's capture-stamp rule for those two.
