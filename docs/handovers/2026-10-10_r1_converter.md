# Handover: rung 1, item R1, the dataflash-to-FGO converter (2026-10-10)

Stage: coding and light tests only. No simulator, no flights, no dataset replays. Branch: the agent worktree
branch based on `fwd-camera` `3a2c3a8`. METHODOLOGY.md and numbers.md were not edited.

Plan being implemented: `docs/minimal_real_flight_plan.md` §4.3 (R1). Rulings applied: METHODOLOGY "RULINGS (user,
2026-10-10): freeze scope; real-log flow timestamps; rung-1 software starts".

## 1. What was built

| file | what it does |
|---|---|
| `eval/bin2fgo.py` | **The converter.** Takes a `.BIN` with `LOG_REPLAY=1` and writes `<out>.npz` (IMU, flow and range events on the FC clock, plus optional SITL truth) and `<out>.json` (geometry, delays, measured rates, every relevant PARM value, checks, the BIN sha256 and the code commit). The flow and range delays are **required arguments**, so there is no silent default. |
| `src/estimators/fgo/fgo_replay.py` | **Events mode, OFF by default.** It is switched on by `FGO_EVENTS=<out.npz>` and needs `FGO_OUT_ROOT`; output goes to `<root>/<trial>/fgo_bin/`. It bypasses the bag, the gap rule, `dejitter_imu`, `imu_gaps.json`, the forward camera and the `f_filter_forward` ground-truth dependency. Geometry, arming time and initial range come from the log. The IMU is integrated over the INS's own `DVDT`. With no truth, it writes the TUM and skips the apparatus metrics. **With `FGO_EVENTS` unset, every line of the bag path runs as before.** The bag-reading block is only re-indented under an `else:`. |
| `src/estimators/measurement_models.py` | `make_geometry(flow_pos_frd, range_pos_frd, h_min, rng_min, rng_max)`. `h_flow_pose(..., geom=None)` and `h_range(x, geom=None)` take it. `GroundProximityFlow(t_arm, rng_min=0.05, rng_max=40.0)`. `geom=None` keeps the module constants on the **identical** code path. The lever arm in FLU is (px, −py, −pz) from the FRD parameters. |
| `src/estimators/fgo/factors.py`, `fgo_core.py` | `flow_factor(..., geom=None)`, `range_factor(..., geom=None)` and `FGO(..., geom=None)`. These cover the init lever (the old hard-coded `+ 0.12`) and the range window (the old hard-coded `0.05/40`). |
| `eval/sensor_timing_from_log.py` | **The measurement script** for the rate and delay of each sensor, to be pre-registered. See §4. |
| `eval/bin2fgo_sitl_check.py` | The hardware-free acceptance checks against the same flight's bag. See §5. |
| `eval/bin2fgo_default_check.py` | Default-unchanged proof, level (a). See §6. |
| `eval/r1_followup_replays.sh` | The two light replays that could not run here (lock busy). See §6. |
| `eval/results/r1_converter/*.json` | Outputs of the three checks on `cl_a_tex_half`. |

Usage:

```
~/venv-fgo/bin/python eval/sensor_timing_from_log.py <log.BIN> [--truth-tum mocap_FC.tum] [--window T0 T1] --json t.json
~/venv-fgo/bin/python eval/bin2fgo.py <log.BIN> -o <x.npz> --flow-delay-ms <D_flow> --range-delay-ms <D_rng>
FGO_EVENTS=<x.npz> FGO_OUT_ROOT=<dir> ~/venv-fgo/bin/python src/estimators/fgo/fgo_replay.py <name> 0.25 2
```

## 2. Flow-sensor conventions (from the pinned `~/ardupilot` source)

- **`OF.flowX/flowY` are RAW, not body-rate compensated** (`AP_OpticalFlow.h:100,114`).
  - Units are rad/s, after `FLOW_ORIENT_YAW` (`_applyYaw`) and the `FXSCALER`/`FYSCALER` scalers, which the backends apply.
  - Convention: a right-handed body rotation about a sensor axis gives a **positive** rate.
  - EKF3 negates the rates (`AP_NavEKF3_Measurements.cpp:221`) and adds `bodyRate` (`:227-228`).
- **That convention is already the FGO's `h_flow_pose`, so the mapping is the IDENTITY:** `flow_x_rad := flowX`, `flow_y_rad := flowY`.
  - From EKF3's line-of-sight prediction (`AP_NavEKF3_OptFlowFusion.cpp:334-335`): raw_x = +ω_x − v_y(FRD)/h = +ω_x + v_left/h, and raw_y = +ω_y(FRD) + v_x/h = −ω_y(FLU) + v_fwd/h.
  - Those are exactly `h_flow_pose`'s rows.
  - On the SITL log, all 7 900 matchable OF records are **float32-identical** to the bag's `flow_x_rad`/`flow_y_rad`.
- **`OF.bodyX/bodyY` are the body rates the backend averaged over the flow interval:**
  - MAV and Pixart use `AP::ahrs().get_gyro()` (`AP_OpticalFlow_MAV.cpp:39,76`; `AP_OpticalFlow_Pixart.cpp:291,356`).
  - That is the INS-**filtered** gyro **minus the active EKF's gyro bias** (`AP_AHRS.cpp:777-780` under `AHRS_EKF_TYPE 3`).
  - HereFlow sends its own gyro instead.
  - **Verified on the SITL log** (`AHRS_EKF_TYPE 3`, `FLOW_TYPE 5`): over 25 blocks of 10 s, (bodyRate − raw RISI average over the same interval) tracks −(EKF3 `XKF1` GX/GY bias).
    - Correlation is 0.83 (x) and 0.96 (y).
    - RMS falls from 2.0/2.4 to 0.6/0.4 mrad/s once the bias is added back.
- **`ROFH`** carries the identical values; `rofh_equals_of` is true. `ROFH.posOffset` equals `FLOW_POS_*`.
- **Validity rule (stated): `valid := Qual > 0`; `inlier := Qual/255` as a pass-through.**
  - The FGO's gate (valid, inlier > 0, |rate| < 4.2) then equals EKF3's (`:203`).
  - EKF3 also requires |bodyRate| < 4.2, which the FGO does not use.
  - The camera-path rule (inlier ≥ 0.85, features ≥ 20) does not apply to rung 1.

### Derotation the FGO must do: its OWN raw gyro, NOT `ROFH.G`/`OF.body*` — NEEDS A RULING

- **Plan §4.3 item 7 says to use `ROFH.GX/GY`. This stage did NOT follow it.**
  - For MAV and Pixart sensors those rates contain **EKF3's gyro-bias estimate** (verified above).
  - Feeding them to the FGO would hand it EKF3's state. Its flow factor already subtracts its own bias B(k), so the bias would be corrected **twice**.
  - That breaks the CLAUDE.md rule that each estimator derotates its own raw gyro.
- **Implemented instead, unchanged from the simulation:** `FlowFrameGyroAverager` over the converter's raw RISI gyro, averaged over (previous flow, this flow], minus the FGO's own bias.
  - With the per-sensor delay applied to both window ends, the window is the sensor's integration interval.
  - `OF.body*` is kept in the npz as a diagnostic only.
- **This is a D18 model-input change relative to the simulation, to be ruled on.** In the sim all three estimators
  derotated with the 20 Hz-filtered gyro, so the roll-tone residual was common-mode (METHODOLOGY 4440-4481). On real
  logs this implementation gives the FGO the PRE-filter RISI gyro, while EKF3 keeps the filtered AHRS gyro.
  - Option A (implemented): the FGO's own raw RISI gyro, averaged over the flow interval, minus its own bias.
  - Option B (plan §4.3 item 7): `ROFH.G`. It carries EKF3's bias estimate (above) and the INS filter lag.
  - Option C (not implemented): the FGO's own RISI gyro passed through the INS filter, to keep the sim's
    common-mode condition without importing EKF3's state.
  - Whether option A reduces the roll-tone residual on real data is UNTESTED.
- **Same exposure in the UKF port.** Its Replay flow hook passes `rawGyroRates` = `ROFH.G` (`AP_NavUKF.cpp`, plan §4.2).
  - On a real log with `AHRS_EKF_TYPE 3` the port therefore also derotates with EKF3's bias.
  - Flag this for the UKF-port stage. The ruling should cover both estimators.
- **HereFlow (`FLOW_TYPE 6`)** gives its own gyro in `bodyRate`, which is not EKF3-contaminated. The rule above (FC raw gyro) still applies, for uniformity.

## 3. IMU, range, arming, geometry

- **IMU.**
  - Source: `RISI` instance 0. `EK3_IMU_MASK` is checked; core 0 uses IMU 0.
  - acc = DV/DVDT and gyro = DA/DADT in FRD, converted to FLU as (x, −y, −z).
  - Each sample is stamped at its RFRH frame. dt = DVDT is carried in the payload.
  - Samples with flags ≠ 15 are dropped (0 on SITL).
  - Gaps come from RFRH continuity and `DSF.Dp` (0/0 on SITL).
  - SITL frames alternate 2/3 ms (mean 400.0 Hz). DVDT equals the frame spacing to < 1 µs at p99, and DVDT = DADT throughout.
- **Range.**
  - `RRNI` (what EKF3 reads) is written only on change. The held value is emitted at the backend update period measured from the change spacing: 49.98 ms on SITL, Copter's 20 Hz rangefinder task.
  - Each emission is phase-anchored at its change.
  - A range is valid only at `Status == 4` and within `RNGFND_MIN/MAX`. Status 1 and 2 occur in this log.
  - `RFND` is not used: it is logged at 20 Hz by the logger, not at reading arrival.
- **Arming:** from the `ARM` record (24.149 s on SITL).
- **Initial height:** the Good range at the end of levelling (0.08 m on SITL). If there is none: the first Good range before arming, then `RRNH.GCl` (= `GNDCLEAR`), for a sensor that reads out of range on the ground.
- **Geometry:** from PARM (`FLOW_POS_*`, `RNGFND<n>_POS_*`, `MIN`/`MAX`). It is cross-checked against `ROFH.posOffset` and `RRNI.pos_offset`; both match on SITL.
- **Limits that stay:**
  - only the vertical rangefinder offset enters `h_range` (flat floor, small tilt, as today);
  - the lateral flow lever enters through ω × r.

## 4. Timestamps (ruling 2026-10-10, item 2) and the measurement script

- **Rule implemented:** capture time = FC arrival − d_sensor. Each d is a command-line value, recorded in the json, to be pre-registered from real data.
- **Flow d is defined to the END of the integration interval**, as the simulation's flow stamp is (the newer camera frame). The derotation window (previous flow, this flow] then keeps its meaning.
- **Rates are measured from the log and recorded:** IMU frame rate, flow inter-arrival, range update period.
- **`eval/sensor_timing_from_log.py`: flow delay.**
  - It cross-correlates `OF.flowX/Y` with the raw RISI gyro averaged over each flow interval shifted by L, after a ~1 s high-pass.
  - It reports the delay per axis, the correlation, the gain and the sign.
  - Rule: if the two axes agree within 5 ms, the correlation-weighted mean; otherwise the axis with the higher peak correlation, flagged.
- **`eval/sensor_timing_from_log.py`: range delay.** Range against truth height minus the lever, over the climbs and descents. Truth is a mocap TUM on the FC clock, or SIM2 on SITL.
- **Validation (`cl_a_tex_half`):**

| quantity | script | SITL truth (bag capture stamp vs FC arrival) |
|---|---|---|
| flow delay | **16.06 ms** (x axis, corr 0.80, gain +1.37); the per-axis rule was written AFTER seeing this, so it is consistency, not independent validation | **16.0 ms** median (p5 11.3, p95 22.5, mean 16.4) |
| flow delay, y axis alone | −4.2 ms (corr 0.51): **biased** | — |
| flow delay, synthetic (flow := 1.2 x exact RISI window average + noise, known d): the independent test | 16.0 ms (d=16, no jitter); 39.7 ms (d=40, no jitter); 37.5 ms (d=40, 4 ms capture jitter: −2.5 ms bias); d=16 with jitter NOT run (the harness made non-monotonic stamps) | 16, 40 ms |
| flow rate | 28.6 Hz median (inter-arrival 25 / 35 / 40 ms) | 30 Hz camera |
| range update | 49.98 ms (20 Hz task) | sensor 33 ms (30 Hz) |
| range delay vs SIM2 | 90 ms (rms 3.6 cm on one 3 s climb) | 40 ms vs the lidar's capture stamp |

- **Why the y axis is biased.** In flight, pitching accelerates the vehicle, so v_fwd/h tracks the integrated pitch rate and contaminates the high-passed y flow. Hence the per-axis rule. **Pre-register from the sync wiggles (rotation in place, `--window`).**
- **Range on SITL.** The lidar's own capture stamp lags SIM2 by ~42 ms (Gazebo render lag; compare the occluder render-lag finding). So 90 ≈ 42 + 40 + residual. The truth-height method measures the TOTAL delay against true geometry, which is what a real flight needs (mocap).
- **The method is coarse on a single climb** (rms 3.6 cm). The p1c-style climb cycles and the rung-1 profile's climbs are needed before the range delay is pre-registered.

## 5. SITL test results (`cl_a_tex_half`, `ardupilot.bin` with full replay records; `eval/results/r1_converter/`)

- **Converter runs.** It finishes in 13 s and writes 107 360 IMU, 7 955 flow and 5 488 range events, plus 107 760 truth rows.
- **IMU matches the bag's `/imu/data_raw`.**
  - Pairing goes through `/imu/time_ref`, which is on the same FC clock.
  - **Rest means:**

    | | bag | converter |
    |---|---|---|
    | acc (FLU, m/s²) | (−0.00101, 0.00094, 9.81083) | (−0.00100, 0.00092, 9.81085) |
    | gyro (rad/s) | equal to 1e-6 | equal to 1e-6 |

    This confirms the frame (FRD → FLU) and the units.
  - **Rate:** bag 333.4 Hz, converter 400.0 Hz.
  - **0.1 s block means:** correlation 0.96–0.999. Gyro RMS difference is 2–6 mrad/s and acc 0.005–0.046 m/s².
  - **Lag:** the bag gyro lags the converter's by **12.5 ms**. That is the expected 20 Hz 2-pole INS filter group delay: HIGHRES_IMU is post-filter, RISI pre-filter. Matching RMS drops 0.0213 → 0.0060 rad/s at that lag.
- **Flow matches.**
  - **7 900 / 7 900** of the bag's valid flow messages that fall inside the log are float32-identical to an OF record. Identity mapping, no sign or axis change.
  - The 50 unmatched OF records come before the bag started.
  - `Qual == round(inlier·255)` for all of them.
- **Range matches.**
  - Against the bag's range at the best lag (40 ms): rms **3.9 mm**, p99 **5.6 mm**. That is centimetre quantisation (`DISTANCE_SENSOR`).
  - Hover median difference −2.0 mm.
  - The true change-to-arrival delay is 27 ms median (2.5–57 ms, p5–p95), which includes the 20 Hz task hold.
- **Clock map FC → bag:** offset −0.02 ms, rate 215 ppm, envelope residual ≤ 6.4 ms.

**Cannot be tested without hardware:**
- a real sensor's scale and `FLOW_ORIENT_YAW`: the R12 bench and the R13 hand-carry;
- the real flow and range delays and rates;
- jitter in real RFRH frame timing and `DVDT`;
- a non-zero `DSF.Dp`;
- a multi-IMU instance choice;
- HereFlow or Pixart backends (SITL used MAV);
- a sensor that reads out of range on the ground (the `GNDCLEAR` init path);
- the real mocap clock map.

## 6. Default-unchanged proof

- **Scope of (a):** `measurement_models`, `factors` and `fgo_core` only. The `fgo_replay.py` bag-path edits (the
  `EVENTS` guards, the re-indented bag block, `d[2] if EVENTS`, `GEOM=None` into `h_flow_pose`, the events-only
  take-off filter) are verified BY INSPECTION ONLY until (b) runs.
- **(a) DONE, PASS.** `eval/bin2fgo_default_check.py` loads the base commit's (`3a2c3a8`) `measurement_models`, `factors` and `fgo_core` beside the new ones.
  - It runs **11 821 byte-identity comparisons** on random inputs, all with `.tobytes()` equality and 0 failures.
  - Covered: `h_flow_pose`, `h_flow`, `h_range`, `h_flow_rot`, the flow and range factors' unwhitened errors, Jacobians and right-hand sides, `FGO.init` plus a keyframe, and a `GroundProximityFlow` sequence.
- **(b) NOT RUN: FOLLOW-UP.** The single `heavy.py` replay (`cl_a_tex_half 0.25 2` against the stored `fgo/fgo_traj.tum`) was queued.
  - `BUILD_LOCK` was held by the attribution study: 64 replays at PAR 6, started 10:59, 25/64 done at 12:45, so about 3 h more.
  - Per the brief it is listed here instead.
  - Run `heavy.py "R1 default-unchanged replay" -- bash eval/r1_followup_replays.sh default <scratch>`.
  - It decompresses the bag to scratch, checks the sha256 against `PACKED.txt`, replays to scratch, byte-compares and deletes the scratch bag.
  - Also run the events-mode smoke: `... eval/r1_followup_replays.sh smoke <scratch>`. It covers 90 s and is plumbing only, not a result.
  - **Neither was run, so the events path in `fgo_replay.py` is untested end to end.** Its pieces (converter output, geometry dict, `GroundProximityFlow` args) are tested.

## 7. Follow-ups

1. **Ruling:** derotation source for rung 1 (§2), for the FGO **and** the UKF port.
2. The two light replays in §6(b).
3. The FGO-from-BIN against FGO-from-bag acceptance band (plan §4.3): evo -a (cruise) on the full `cl_a_tex_half`, after 16 Oct or as a light job. Use `--truth sim2` for the metrics; the delays are 16/40 ms (the SITL truth) or a stated alternative.
4. The C++ FGO (`fgo_cpp`) geometry and events input: not done. Rung 1 uses the Python FGO.
5. Pre-registration (R10): d_flow from the sync wiggles (x and y must agree within 5 ms), and d_range from the climb cycles against mocap. Record the measured rates.
6. The UKF port (plan §4.2): pass the geometry through DAL, and decide the `ROFH.G` question above.
7. Take-off detection (D15) in events mode: EKF3 uses the DAL `gyro_filtered`, the RISI rate through a 10 Hz 1-pole
   low-pass (`AP_DAL_InertialSensor.cpp:53-63`, `AP_NavEKF3_VehicleStatus.cpp:470-476`). The events path now
   reproduces that filter for `GroundProximityFlow.on_gyro` only (bag path untouched). Untested end to end (§6).
