# Result: input-path diagnostic (brief `2026-10-08_input_path_diagnostic.md`) — REPORT ONLY

No thesis number, result file or figure is changed by this stage. All new outputs are in new directories.

## 0. Comparison stated BEFORE running (b) (committed before any (b) run)

**Variants of the offline UKF** (same code, same noise form, same 15.0 ms predict step, same range, tags, gap rule and
D15 rule; only the inputs named change; env `UKF_APIN`, OFF by default):

| label | IMU (predict + flow-derotation average + take-off detector) | flow (values, time, derotation gyro) |
|---|---|---|
| (a) | bag `/imu/data_raw` (HIGHRES_IMU, 20 Hz-filtered instantaneous samples, OI-2 dejittered) | bag `/optical_flow/measurement` at capture stamp, frame-averaged bag gyro |
| (b) `UKF_APIN=both` | FC INS deltas (`RISI` instance 0, per FC frame, DADT), on the FC clock | `ROFH` values, at EKF3's / the UKF port's time (arrival − 60 ms), EKF3's `bodyRate` gyro |
| (b-imu) `UKF_APIN=imu` | as (b) | as (a) |
| (b-flow) `UKF_APIN=flow` | as (a) | as (b) |

(b-imu) and (b-flow) are a diagnostic decomposition (the "swap one input" method), reported alongside.

**Metrics.**
- `H_s1_r1` (`room_ukf_replay.py`, `ROOM_TAG_SIGMA_POS=0.02`): `eval/h_score.py H_s1_r1 --profile
  batches/expH/s1_profile.json --sigma 0.02`, per loss (hover 5 / 15 / 30 s, move ~7 s): the **effective drift**
  (|estimate − GT| just before the first returning fix) and the as-worded drift (at OCCLUDER OFF). Reference points:
  EKF3 (same flight) and the UKF port on Replay (tier B: 12 / 8 / 11 / 13 mm effective).
- `dsn_tex_r2` (`ukf_replay.py`, standard config): **evo -a (cruise)** via `eval/three_way_eval.py --est`, window
  pinned from the stored `ukf/ground_truth.tum` (unchanged), plus the replay's own along-track and yaw-drift lines.
- **Share of the gap closed** per loss: (a − b) / (a − port). ≥ 0.7 = the input path accounts for most of the
  offline-vs-port gap; 0.3–0.7 = part; < 0.3 = little.

**Regression (default path byte-identical):** the modified scripts with `UKF_APIN` unset, run into a scratch HOME,
must give output files byte-identical to the unmodified scripts (HEAD `b918455`) on `dsn_tex_r2` and `H_s1_r1`, and
are also compared with the stored thesis outputs.

### 0.1 Added after the first (a)/(b) results, stated before running them

The first results put the whole `H_s1_r1` effect in the flow path ((b-flow) = (b); (b-imu) = (a)). Three more
OFF-by-default variants split it (same metrics as §0):
- `flowgyro`: bag flow and capture stamps, but EKF3's derotation gyro (ROFH `bodyRate`, paired by frame).
- `flowtime`: ROFH flow at EKF3's time (arrival − 60 ms), with the bag-IMU frame-average gyro.
- `biascorr`: bag inputs; `h_flow` derotates with the frame-average gyro minus the UKF's own gyro-bias estimate
  (EKF3 derotates with bias-corrected rates; the FGO too). A formulation variant, not an input substitution.
Expectation stated beforehand: if `flowgyro` and `biascorr` each close most of the H gap and `flowtime` does not,
the mechanism is the gyro bias left in the offline UKF's derotation, not the input path. The default path is
re-checked byte-identical after this change.

## 1. What each estimator receives (source at `~/ardupilot` 7bac20cbcc; port at `~/ardupilot_ukf` `ukf-port-tag` eb86bada)

| | EKF3 (and the UKF port, via DAL) | offline UKF/FGO (bags) |
|---|---|---|
| IMU quantity | delta angle / delta velocity per FC frame (`AP_InertialSensor::get_delta_angle/velocity`, EKF3 `AP_NavEKF3_Measurements.cpp:546,763`; port `AP_NavUKF.cpp:460-467` `update()`, first usable IMU; flow input `writeOptFlowMeas` :442-457, `e.fg` used as given :543,574) | HIGHRES_IMU instantaneous `get_gyro()/get_accel()` (`GCS_Common.cpp:2294-2302`), summed rectangularly |
| filtering | **unfiltered**: delta angle from the raw sample, trapezoidal + coning (`AP_InertialSensor_Backend.cpp:333-365`, in `_notify_new_gyro_raw_sample` :281); delta velocity from the raw accel (:608) | **20 Hz 2-pole low-pass** (`_gyro_filter` :251, `_accel_filter` :611; `INS_*_FILTER 20`) |
| rate / timing | 1 kHz sensor integrated into FC frames (RFRH median 3.00 ms, 2–4 ms), on the FC clock; EKF3 predicts on ~12 ms sums, the port on the same 12 ms trigger | one sample per FC frame (333 Hz), receipt-stamped, OI-2 dejittered to a regular 3.0006 ms grid; 15.0 ms predict step (D27 noise form) |
| flow values | ROFH FX/FY = the MAVLink `flow_rate_x/y` exactly (`FLOW_*SCALER 0`, `ORIENT_YAW 0`); matched to the bag `flow_x_rad/flow_y_rad` frame by frame (|Δ| < 1e-5 rad/s; signs +,+ on both flights) | same values |
| flow time | `imuSampleTime − EK3_FLOW_DELAY(10) − flowTimeDeltaAvg/2(50) − localFilterTimeStep/2(6)`, clamped to the 60 ms horizon (`AP_NavEKF3_Measurements.cpp:232-236`, `AP_NavEKF3.h:511`, `AP_NavEKF3_core.cpp:42-46`); port identical (`AP_NavUKF.cpp:37`, `:540-542`) = arrival − 60 ms | capture stamp |
| flow rate limit | EKF3 only: ≥ 50 ms between accepted flows (`AP_NavEKF3_Measurements.cpp:178-180`, `AP_NavEKF3.h:516`) → **50.1 % (H) / 50.4 % (dsn) of frames fused**; the port does not limit | every frame |
| derotation gyro | `bodyRate` = `AP::ahrs().get_gyro()` averaged between flow messages (`AP_OpticalFlow_MAV.cpp:38-42,76`); EKF3 then subtracts `flowGyroBias` (:193-194,206-207) | frame-averaged bag gyro (`FlowFrameGyroAverager`), **raw** (no bias correction) in the UKF; bias-corrected in the FGO |
| AHRS gyro | `AHRS_EKF_TYPE 3` (**H**): `ins.get_gyro() + EKF3 gyro drift` (`AP_AHRS.cpp:776-780`) = **EKF3-bias-corrected**; `AHRS_EKF_TYPE 10` (**dsn**): `ins.get_gyro()` (`AP_AHRS_SIM.cpp:215`). Port flying (S2): `ins.get_gyro() + UKF drift` (`AP_AHRS_UKF.cpp:30`) | — |

**Measured differences** (`eval/apin_extract.py`; `eval/results/input_path/extract_stats_*.json`; clock: `/imu/time_ref`
lower envelope, as `h_score.py`):
- IMU lag: the bag gyro/accel lag the FC deltas by **16 ms (H) / 18 ms (dsn)** (cross-correlation; ≈ the 20 Hz
  filter's ~11 ms group delay plus receipt latency). Over 15 ms steps the integrated difference is small: delta-angle
  RMS 2–7e-5 rad, delta-velocity RMS 1.2e-5 (x, y) / 1.7–2.0e-4 (z) m/s; means ≈ 0 except dv_z −2.4…−3.3e-5 m/s
  (~2 mm/s² vertical).
- Flow time: EKF3 / the port place each flow **36 ms (H) / 45 ms (dsn) before** its capture (median; arrival is
  24 / 15 ms after capture). The offline UKF fuses at capture.
- Derotation gyro, ROFH − bag frame average: H mean **(−2.6, +2.6) mrad/s** (x, y), RMS 7.5 / 3.2 mrad/s; dsn mean
  ≈ 0 (2e-6), RMS 1.2 / 2.9 mrad/s. The H offset is EKF3's gyro-bias estimate carried in by AHRS type 3.

## 2. Results

**Regression (default path):** with `UKF_APIN` unset, the modified scripts reproduce the unmodified ones (HEAD
`b918455`) and the stored thesis outputs **byte for byte** on both flights (`.tum`, `.json`, `metrics.txt`,
`bgz_series.txt`; npz compared array by array, excluding only the wall-clock `t_*_ns` timing arrays). Checked after
both code changes (`eval/results/input_path/regression2.txt`).

**`H_s1_r1` tag-loss drift, UKF, effective / as worded (mm)** (`eval/results/input_path/h_*.json`):

| variant | hover 5 s | hover 15 s | hover 30 s | move ~7 s |
|---|---|---|---|---|
| (a) bag (= stored thesis value) | 32 / 28 | 120 / 117 | 292 / 289 | 40 / 37 |
| (b) FC IMU + FC flow | **11 / 11** | **7 / 7** | **11 / 11** | **13 / 18** |
| (b-imu) | 32 / 28 | 120 / 117 | 292 / 289 | 44 / 38 |
| (b-flow) | 11 / 11 | 7 / 7 | 11 / 11 | 16 / 21 |
| `flowgyro` (bag flow, EKF3's gyro) | 11 / 11 | 13 / 12 | 31 / 30 | 8 / 12 |
| `flowtime` (FC flow time, bag gyro) | 33 / 28 | 120 / 117 | 292 / 289 | 33 / 32 |
| **`biascorr` (bag inputs, own bias removed in h_flow)** | **13 / 13** | **2 / 2** | **6 / 6** | **16 / 9** |
| reference: UKF port on Replay (tier B) | 12 | 8 | 11 | 13 |
| reference: EKF3 / FGO (this flight) | 13 / 14 | 6 / 50 | 11 / 112 | 31 / 1 |

Share of the offline-vs-port gap closed by (b): 1.0 / 1.0 / 1.0 / 1.0 (b-imu: 0 / 0 / 0 / <0).

**`dsn_tex_r2` evo -a (cruise), m** (window 30.56–333.04 s; `eval/results/input_path/dsn_three_way.json`):
EKF3 3.86, FGO 4.72, UKF (a) **2.13**; (b) 2.04; (b-imu) 2.32; (b-flow) 1.88; `flowgyro` 2.09; `flowtime` 2.07;
`biascorr` 1.69. Displacement ratio 0.96–0.98 for all.

## 3. Findings

1. **The S1 hover-drift gap is NOT an input-path effect. It is the UKF's flow derotation using the raw gyro.**
   - Swapping the IMU path (filtered 333 Hz samples → FC unfiltered deltas, on the FC clock) changes nothing on H
     (≤ 4 mm) and moves dsn cruise by +0.19 m.
   - Swapping flow timing (capture → EKF3's arrival − 60 ms) changes nothing on H.
   - All of (b)'s effect comes from the derotation gyro. On H it carries **EKF3's gyro-bias estimate** (AHRS type 3), a
     ~2.6 mrad/s x/y offset. The offline UKF, on its own bag inputs, removes the same effect when `h_flow` uses
     (gyro − its own bias estimate) (`biascorr`: 2–16 mm, EKF3's scale).
   - **Confirmed from the log:** EKF3's logged gyro bias (`XKF1` GX, GY, core 0, airborne mean) is
     (+2.56, +2.64) mrad/s FRD (it ramps 0.35 → 4.0 mrad/s, the SITL drift model). `gyro_estimate = gyro − bias`
     predicts a ROFH − bag offset of (−2.56, +2.64) mrad/s FLU; measured (−2.56, +2.63).
   - **Mechanism (checked with a scratch state dump of the offline UKF on H, `--no-rts`, live track unchanged):**
     - The UKF's own gyro-bias estimate is right: airborne mean (+2.85, −2.85) mrad/s FLU, against EKF3's
       (+2.56, −2.64). Within each hover loss it is +3.4 / +3.8 / +4.2 mrad/s per axis (5 / 15 / 30 s losses). It
       follows the SITL drift ramp, so later losses see a larger bias.
     - In (a) that bias stays in `h_flow`'s rotational term (the raw rate). Flow therefore reads it as translation, and
       the estimated velocity at the end of each hover loss is (+13.8, −8.9) / (+8.3, −6.8) / (+5.9, −6.0) mm/s (E, N).
       With `biascorr` the same bias estimate is applied in `h_flow` too, and these fall to (+7.4, −2.5) / (+2.0, −0.7)
       / (−0.9, +0.6) mm/s.
     - b·h_cam: (bias ≈ 4.2·√2 ≈ 6 mrad/s horizontal) × (h_cam ≈ 0.9 m) ≈ 5.4 mm/s, of the order of the 8.5 mm/s
       observed at 30 s. The order of magnitude is explained. The residual (filter dynamics, the growing bias) is not
       modelled further.
2. **This reverses the tier-B attribution** ("input-path effect, not the UKF formulation",
   `docs/h_backends_tag_input.md` §3.3). The port on Replay received EKF3's bias-corrected `bodyRate` (Replay of an
   AHRS-type-3 flight), so its 7–19 mm drift reflects EKF3's bias estimate fed into the port's flow model.
   - **S2 prediction:** when the port flies, `AP_AHRS_UKF.cpp:30` supplies `ins.get_gyro() + UKF drift`, i.e. the
     UKF's *own* bias-corrected rate, which is the `biascorr` condition. The predicted EKF3-scale drift is therefore
     still expected, but for this reason. S2 tests the formulation, not the input path.
3. **Size for the main results:**
   - **EKF3 vs FGO:** the FGO already derotates with a bias-corrected rate, so finding 1 does not apply to it. The
     input path proper (the IMU/flow swaps) moved the UKF by **−0.25…+0.19 m** on dsn cruise ((b-flow) −0.25, (b)
     −0.09, `flowtime` −0.06, `flowgyro` −0.04, (b-imu) +0.19) and ≤ 4 mm on H. Estimated share of the EKF3-vs-FGO
     textured result: **≲ 0.25 m of evo -a (cruise)**, of the order of the FGO's own measured 0.40 m sensitivity to
     IMU-timestamp treatment (P4; an FGO figure, not a UKF one). Indirect: no FGO was run on FC inputs.
   - **The FGO's own H gap is NOT explained by this stage.** The FGO drifted 50 / 112 mm (15 / 30 s) against EKF3's
     6 / 11 mm, and it already derotates with a bias-corrected rate, so finding 1 does not apply. Open; one candidate
     is the post-anchor yaw wander S1 recorded (up to 2.6°).
   - **EKF3 vs UKF:** the input path is likewise small (≲ 0.25 m cruise). The raw-rate derotation is a formulation
     difference: about −0.44 m on one textured cruise (2.13 → 1.69, n = 1, not significant), and the dominant term in
     hover dead-reckoning (H: ~10× drift).
   - The dsn bags have no EKF3 bias in ROFH (AHRS type 10), so dsn (b-flow) isolates timing and the raw-vs-averaged
     AHRS gyro only.

## 4. Open questions / what would confirm
- `biascorr` on all nine `dsn_*`, `H_s1_r2/r3` and the T/O flights, to size the formulation effect with n > 1. It
  would be a thesis change to the UKF's `h_flow` rate, so it needs a ruling (it moves away from "UKF passes the raw
  rate", `measurement_models.h_flow_pose` docstring).
- The source of the ~2.6 mrad/s x/y gyro bias in SITL (`SIM_GYR*_BIAS` 0; the drift model?) is not traced.
- The EKF3-only 50 ms flow rate limit (half the frames fused) is not reproduced by the port or the offline UKF;
  unquantified.
- (b) keeps the offline 15 ms step and D27 noise form, so (b)-vs-port also contains the tier-A noise-form term
  (~3.6 mm); not separated.
- n = 1 per flight type. No FGO input-path run (the IMU swap is the relevant one for the FGO; not done).

## 5. Exact commands
Scratch: `$S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad`, with
`$S/home` a scratch HOME. It holds a decompressed COPY of `dsn_tex_r2/bag/bag_0.db3.zst` (sha256 matches
`PACKED.txt`) and links to `H_s1_r1/bag`.
- Extract: `~/venv-tags/bin/python eval/apin_extract.py <trial> --trials-dir $S/home/thesis_data/trials`
- Replays, each through `src/estimators/fgo_cpp/tools/heavy.py "<desc>" -- env HOME=$S/home OPENBLAS_NUM_THREADS=1
  [ROOM_TAG_SIGMA_POS=0.02] [UKF_APIN=both|imu|flow|flowgyro|flowtime|biascorr] ~/venv-evo/bin/python
  src/estimators/{room_ukf_replay.py H_s1_r1 | ukf_replay.py dsn_tex_r2}`
- Regression: the same with `UKF_APIN` unset, and the HEAD-`b918455` scripts under `$S/home_orig`; compared by
  `$S/regcmp.py`.
- Scoring: `eval/h_score.py H_s1_r1 --profile batches/expH/s1_profile.json --sigma 0.02` with `HOME` = one scoring
  home per variant (`room_ukf` linked to that variant). `eval/three_way_eval.py dsn_tex_r2 --est
  LABEL=ukf_apin*/ukf_traj.tum`, with `ekf3/ukf/fgo` linked to the real trial.
- Outputs: copied to NEW directories `~/thesis_data/trials/{H_s1_r1/room_ukf_apin*, dsn_tex_r2/ukf_apin*, */apin}`
  and `eval/results/input_path/`. No existing file was changed.

## 6. Process note (lock protocol)
- No simulator was used. `FLIGHT_LOCK` was never touched. Every replay ran through `heavy.py`, and no `BUILD_LOCK` of
  mine is left.
- **Found: `heavy.py` can wait on itself.** At ~21:52 another session's job was `heavy.py --wait-s 3600 "port rebuild
  for version string" -- bash -c '... ./waf copter ... strings build/sitl/bin/arducopter ...'`. Its own command line
  contains "arducopter", so `pgrep -f '[a]rducopter'` matches the waiting `heavy.py` itself (and its parent shell).
  - It therefore waits on itself until its timeout.
  - It blocks every other `heavy.py` job and the "no commit while `[a]rducopter` matches" rule.
  - I did not touch it. A fix would exclude the caller's own PID and its ancestors from the match, or match the
    process name (`pgrep -x arducopter`) rather than the full command line.
