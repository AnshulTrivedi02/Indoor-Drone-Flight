# Numbers for the methodology chapter

Companion to `methodology_index.md`. Every value is copied verbatim from its source. None
has been recomputed or re-rounded.

- **Sources:** `M:L123` / `C:L123` / `P:L123` are line numbers in the snapshot
  `docs/thesis/export_2026-09-29_563a989/` (METHODOLOGY.md, CLAUDE.md, PROGRESS.md; snapshot
  commit `563a989`). `C(d89a902):L123` points into the earlier snapshot
  `docs/thesis/export_2026-09-29_d89a902/`, kept for reference, where a value no longer
  appears in the current files. `json:<file>:<key>` is a file in `eval/results/`.
  `code:<path>:<line>` is the file at `563a989` (unchanged since `d89a902`).
- **Flag resolutions:** the discrepancies flagged in the first version of this file are
  resolved in METHODOLOGY "Source-pack flag resolutions (2026-09-29, documentation only)"
  (M:L3114-L3198, §1–§6), and applied here as recorded.
- **Status:**
  - CURRENT: the standing value.
  - DIAGNOSTIC: reported but never a gate, or a descriptive record.
  - ESTIMATE: not measured.
  - CURRENT (pre-registered): a pre-registered band or setting.
- **Superseded values** appear only in the last section, each with what superseded it.
- **Receipt-stamp UKF/FGO values.** METHODOLOGY supersedes every UKF/FGO number computed on
  receipt stamps (M:L505-L511), pending one consolidated re-run. Such numbers are therefore
  in the superseded section even when the finding they support is current. EKF3 values
  are not affected by the IMU-stamp treatment.
- **Discrepancies** between sources are flagged with ⚑ in the quantity cell and collected in the second-last
  section (now split into resolved and remaining).
- **Final consolidated re-run (2026-10-10).** The UKF/FGO rows below are restated from the final re-run (UKF
  bias-corrected derotation and jitter-on-failure; FGO `biasAccOmegaInt = 0` and the variance-gated yaw cap), as
  ruled in METHODOLOGY "RULINGS (user, 2026-10-10): the final restatement" (items 2–9 and 11). EKF3 is unchanged
  (9 hard gates, 0 differences). Every replaced row is kept verbatim in "Superseded by the final consolidated re-run
  (2026-10-10)" at the end. Withdrawn claims stay in place, marked **WITHDRAWN** with the reason. Old → new for every
  row: `docs/thesis/final_restatement_draft.md` and `eval/results/final_old_vs_new.md`. **Attribution is PENDING:**
  which correction causes which change is not yet established (the attribution study is running).

---

## 1. Simulation and setup

| quantity | value | units | status | source |
|---|---|---|---|---|
| Corridor width | 20 m wide (x = −10…10 m) | m | CURRENT | C:L99 |
| Corridor length | 160 m long (y = 0…160 m) | m | CURRENT | C:L99 |
| Walls: height, thickness | 5 m tall and 0.2 m thick | m | CURRENT | C:L100 |
| Transition texture boundary | y = 80 m | m | CURRENT | C:L119 |
| Measured boundary crossing (verification trial) | ground-truth y = 80.01 m | m | CURRENT | C:L1814 |
| Spawn pose | (0, 0, 0.195), yaw 90° | m, deg | CURRENT | C:L102 |
| Downward camera mount | z = −0.25 m | m (rel. base_link) | CURRENT | C:L153 |
| Downward LiDAR mount | z = −0.12 m | m (rel. base_link) | CURRENT | C:L155 |
| LiDAR range | 0.05–40 m | m | CURRENT | C:L155 |
| LiDAR reading at rest, corridor worlds | 0.075 m at y = 0, 80 and 150 | m | CURRENT | C:L1793 |
| Flight profile (all datasets) | 0.5 m/s, 2.0 m, 300 s | m/s, m, s | CURRENT | M:L790-L791 |
| Flow RANSAC seed | 42 | — | CURRENT | M:L791 |
| True travel per trial | 151 | m | CURRENT | M:L551 |
| Cruise window on the nine `dsn_*` bags | ~30.0 → ~332.8 s | s | CURRENT | M:L42-L43 |
| Forward camera HFOV | 60° (1.047 rad) | deg | CURRENT | M:L1348 |
| Forward camera VFOV | ±23.4° | deg | CURRENT | M:L1348 |
| Forward camera focal length | f = 554.38 px | px | CURRENT | M:L1348 |
| Forward camera angular resolution | 0.094°/px | deg/px | CURRENT | M:L1348 |
| Forward camera resolution / rate | 640 × 480 / 30 Hz | px / Hz | CURRENT | M:L1349-L1350 |
| Forward camera mount | 0.15 m forward of base_link, level | m | CURRENT | M:L1352 |
| Forward camera far clip | far 200 m | m | CURRENT | M:L1353 |
| Cruise GT yaw (forward-camera design) | 90.01°, std 0.017° | deg | CURRENT | M:L1337-L1338 |
| Cruise roll | mean 0.00°, std 0.26°, max 0.53° | deg | CURRENT | M:L1342 |
| Cruise pitch | mean +0.02°, std 0.17°, max 5.2° | deg | CURRENT | M:L1343 |
| Cruise base_link height | 2.29 m | m | CURRENT | M:L1344 |
| Ceiling slab | 20.2 × 170 × 0.1 m | m | CURRENT | M:L2329 |
| Ceiling bottom face | z = 5.0 m | m | CURRENT | M:L2330 |
| Sky share of forward frame height (no-ceiling worlds) | ~46% | % | CURRENT (finding) | M:L2280 |
| Sky share near the end wall | ~29% | % | CURRENT (finding) | M:L2281 |
| RTF, old machine | 0.05 – 0.17 | — | CURRENT (historical) | C:L922 |
| RTF, new machine (pre-fix) | ≈0.86 | — | CURRENT (historical) | C:L922 |
| RTF, corridor collision root cause (as-is) | 0.0134 | — | CURRENT (finding) | C:L1728 |
| RTF, 8 tiles rendering, 1 with collision | 0.3934 | — | CURRENT (finding) | C:L1731 |
| RTF, live lockstep after fix (tex / blank / trans) | 0.917 / 0.912 / 0.927 | — | CURRENT | C:L1695 |
| RTF, live lockstep mean | 0.919 | — | CURRENT | C:L1701 |
| RTF, `dsn_*` flights (cruise method) | 0.975–0.981 | — | CURRENT | M:L1430 |
| Batch cost, 9 corridor trials | 58 minutes for 9 trials | min | CURRENT | C:L1712 |
| Phase 2 `fwd_*` batch duration | 69.0 min | min | DIAGNOSTIC | M:L1871 |
| Ceiling datasets batch duration | 140.9 min | min | DIAGNOSTIC | M:L2505 |
| Forward camera RTF cost: control / fwd | 0.954 / 0.768 | — | DIAGNOSTIC | M:L1487-L1488 |
| RTF diagnosis: control / full / norecord / nobridge | 0.957 / 0.759 / 0.761 / 0.958 | — | DIAGNOSTIC | M:L1544-L1547 |
| Cost of bridging one 640×480 30 Hz image | ~40% of a core | — | CURRENT | M:L1666-L1667 |
| RTF, Phase 2 `fwd_*` | 0.73–0.81 | — | DIAGNOSTIC | M:L1952 |
| RTF, ceiling datasets | 0.72–0.77 | — | DIAGNOSTIC | M:L2542 |
| Live parameter audit | 1379 parameters on each side … 16 value differences | — | CURRENT | C:L853-L854 |

## 2. Sensor rates and timing

| quantity | value | units | status | source |
|---|---|---|---|---|
| IMU bridge realised rate | 333.27 Hz | Hz | CURRENT | C:L564 |
| IMU rate evidence | 29665 msgs / 89.012 s; median dt 3.000 ms | — | CURRENT | C:L565 |
| IMU rate ceiling (0.8 × SCHED_LOOP_RATE) | `2500/800 = 3.125 ms` | ms | CURRENT | C:L562 |
| IMU at rest ‖a‖ | 9.81085 m/s² (std 0.00061) | m/s² | CURRENT | C:L619 |
| IMU stream late start | ~2.35 s | s | CURRENT | C:L624 |
| IMU header mean gap (every bag) | 3.0005 ms | ms | CURRENT | M:L1180 |
| IMU receipt-stamp scatter | 0–9 ms | ms | CURRENT | M:L1179 |
| IMU rate per bag, `dsn` baseline | 333.27–333.28 Hz | Hz | CURRENT | M:L1583 |
| Flow and LiDAR header rate | 30.30 Hz | Hz | CURRENT | M:L1581 |
| Flow and LiDAR median and p99 gap | 33.0 ms | ms | CURRENT | M:L1582 |
| LiDAR sim-time period (Stage 1) | 33.00 ms | ms | CURRENT | C:L155 |
| Ground-truth pose rate, `dsn` spread | 59.65–59.89 | Hz | DIAGNOSTIC | M:L166 |
| Ground-truth pose rate, verified range | 57–227 Hz | Hz | CURRENT | C:L145 |
| Normal IMU sensor-time steps | 2, 3, 5 and 6 ms | ms | CURRENT | M:L1979 |
| IMU gap threshold | 10 ms | ms | CURRENT | M:L1978 |
| Real dropouts found (`fwd_*`) | 20 and 30 ms | ms | CURRENT | M:L1982 |
| Receipt-bunch threshold | 25 ms | ms | CURRENT | M:L2475 |
| Minimum stationary data before arming after a trim | 10 s | s | CURRENT | M:L2478 |
| IMU data before arming, clean bags | 11.5–13.8 s | s | CURRENT | M:L2498 |
| Dejitter validity range, `dsn` | ±13 ms | ms | CURRENT | M:L1954 |
| Dejitter guard limit | 25 ms | ms | CURRENT | M:L1918 |
| OI-2 anchors per bag | 6722–6823 anchors, ≈ 81% | — | DIAGNOSTIC | M:L1222 |
| OI-2 sensor-time model residual | std **0.82 ms** and max 1.89 ms | ms | DIAGNOSTIC | M:L1227 |
| Receipt minus sensor time, median | 5–9 ms | ms | DIAGNOSTIC | M:L1229 |
| Sensor-time reconstruction accuracy | about ±5 ms | ms | CURRENT | M:L1267 |
| SITL `TimeUS` rate vs sim time | slow by **0.016–0.022%** | % | CURRENT | M:L1195 |
| TimeUS offset early / late | −6 to −9 ms early and −52 to −68 ms late | ms | CURRENT | M:L1194 |
| TimeUS offset drift (CLAUDE summary) ⚑ | about −7 ms to about −60 ms | ms | CURRENT | C:L810-L811 |
| EKF3 flow delay assumption | `EK3_FLOW_DELAY` (10 ms) | ms | CURRENT | M:L1591 |
| Latency tolerance (one EKF3 step) | 12.5 ms | ms | CURRENT | M:L1590 |
| `dsn` flow → EKF3 latency, textured (median / p95, linear map) | 14.5–17.6 / 23.7–24.9 | ms | CURRENT | M:L1752 |
| `dsn` latency, transition | 15.2–20.5 / 24.8–27.7 | ms | CURRENT | M:L1753 |
| `dsn` latency, blank | 16.4–18.9 / 24.9–27.0 | ms | CURRENT | M:L1753 |
| Forward camera added latency | ~5–10 ms median and ~8–13 ms p95 | ms | CURRENT | M:L1763 |
| RTF alone added latency (`p1rtf`) | ~4 ms median | ms | CURRENT | M:L1764 |
| EKF3 flow alignment error, `dsn` → `fwd` | ~5 ms … ~11–18 ms | ms | CURRENT | M:L1767 |
| Clock-shift sensitivity check | ±0.25 s and ±0.5 s | s | CURRENT | M:L87-L88 |
| Max Δ evo -a (cruise) under clock shift, textured EKF3 / UKF / FGO (re-flown `dsn_tex` r1–r3) | 0.012 / 0.009–0.013 / 0.012–0.013 | m | CURRENT (final re-run 2026-10-10); not like-for-like with the old row (pre-re-fly bags; EKF3 differs too) | json:phase0_cruise_pinned_final.json |
| Same, transition | EKF3 0.136–0.137 / UKF 4.4–5.4 † / FGO 7.7–17.8 † | m | CURRENT (final re-run 2026-10-10) († runaway magnitudes) | same |
| Same, blank | EKF3 0.000–0.015 / UKF 48–58 † / FGO 26–53 † | m | CURRENT (final re-run 2026-10-10) († runaway magnitudes) | same |
| Independently computed cruise windows agree to | 0.14–0.34 s | s | CURRENT | M:L100 |

## 3. Noise parameters and conversions

| quantity | value | units | status | source |
|---|---|---|---|---|
| `GYRO_P_NSE` | 0.015 | rad/s | CURRENT | C:L1140 |
| `ACC_P_NSE` | 0.35 | m/s² | CURRENT | C:L1141 |
| `GBIAS_P_NSE` | 0.001 | rad/s/s | CURRENT | C:L1142 |
| `ABIAS_P_NSE` | 0.02 | m/s/s/s | CURRENT | C:L1143 |
| `EK3_FLOW_M_NSE` | 0.25 rad/s | rad/s | CURRENT | C:L1121 |
| `EK3_FLOW_I_GATE` | 300 → NIS gate 9 (3σ) | — | CURRENT | C:L1122 |
| `EK3_RNG_M_NSE` | 0.5 m | m | CURRENT | C:L1123 |
| `EK3_RNG_I_GATE` | 500 → NIS gate 25 (5σ) | — | CURRENT | C:L1124 |
| `FLOW_MAX` | 2.5 rad/s hard reject | rad/s | CURRENT | C:L1125 |
| GTSAM conversion rule | `σ_c = NSE·√dt` | — | CURRENT | C:L674 |
| √dt at dt = 0.0125 s | 0.1118034 | √s | CURRENT | C:L685 |
| `accelerometerCovariance` σ / covariance | 0.03913119 / 1.53125×10⁻³ | m/s²/√Hz | CURRENT | C:L689 |
| `gyroscopeCovariance` σ / covariance | 0.001677051 / 2.8125×10⁻⁶ | rad/s/√Hz | CURRENT | C:L690 |
| `biasAccCovariance` σ / covariance | 0.002236068 / 5.0×10⁻⁶ | m/s²/√s | CURRENT | C:L691 |
| `biasOmegaCovariance` σ / covariance | 0.0001118034 / 1.25×10⁻⁸ | rad/s/√s | CURRENT | C:L692 |
| `integrationCovariance` (no EKF3 counterpart) | ~1e-8·I | — | CURRENT | C:L699 |
| EKF3 pseudo-yaw opportunity interval | every 140 ms | ms | CURRENT | M:L898 |
| EKF3 pseudo-yaw gate (quaternion trace) | 0.01 | — | CURRENT | M:L901 |
| UKF pseudo-yaw gate (Euler attitude trace) | 0.04 | rad² | CURRENT | M:L902 |
| EKF3 cruise tilt variance | `XKF4.errRP² ≈ 1×10⁻⁴ rad²` | rad² | CURRENT | M:L911 |
| EKF3 `XKV1` quaternion covariance | median 0.0093, max 0.01001 | — | CURRENT | M:L914 |
| UKF attitude-cov trace / firing rate | Euler **0.029** (quaternion-equivalent 0.0072) / ~1% | — | CURRENT | M:L922-L923 |
| EKF3 nomag flow rejection | 7.5% (236/3153 airborne) | % | CURRENT | M:L398 |
| Yaw observability from flow | `∂flow/∂yaw = v/h ≈ 0.286` rad/s per rad | rad/s/rad | CURRENT | M:L941-L942 |
| Same (framing section) | ≈ 0.29 rad/s per rad | rad/s/rad | CURRENT | M:L887 |
| `h_flow` translational sensitivity | `∂flow/∂v = 0.571` | — | CURRENT | M:L452 |
| Cruise rollspeed / pitchspeed std | 0.399 rad/s vs … 0.013 — 31× | rad/s | CURRENT | M:L455 |
| SITL gyro drift parameters | `SIM_DRIFT_SPEED=0.05` deg/s/minute … `SIM_DRIFT_TIME=5` minutes | — | CURRENT | M:L733-L734 |
| Drift triangle-wave period | `2·DRIFT_TIME = 10` min | min | CURRENT | M:L738 |
| Drift ramp slope | 3.00 deg/min per minute | deg/min/min | CURRENT | M:L739 |
| Instantaneous bias over cruise | ~1.6 to ~14.8 deg/min | deg/min | CURRENT | M:L740 |
| Physical drift (window mean) ⚑ | +9.8 deg/min | deg/min | CURRENT | M:L741 |
| Window-mean range | ≈8.9–9.8 | deg/min | CURRENT | M:L742 |
| True bias over cruise, textured bags (Ruling 1 check) ⚑ | 1.49–1.52 to 13.35–13.41 … mean of 8.87–8.90 | deg/min | CURRENT | M:L2077 |
| True bias mean (Phase 3 basis) ⚑ | 8.9 deg/min = 0.148 deg/s | deg/min | CURRENT | M:L2718 |

## 4. EKF3 prediction dt

| quantity | value | units | status | source |
|---|---|---|---|---|
| `EKF_TARGET_DT` | 0.012f | s | CURRENT | C:L529 |
| Frames per prediction | 5 frames = **0.0125 s** | — | CURRENT | C:L532 |
| Actual prediction dt | 0.0125 s (80 Hz) (derived, not logged) | s | CURRENT | C:L537 |
| `SCHED_LOOP_RATE` | 400 | Hz | CURRENT | C:L537 |
| UKF predict dt | port 12.5 ms (DAL frames); offline 15.00 ms (actual accumulated IMU interval, correction (ii)) | s | CURRENT (D27) | M: "D27 RULED" |
| UKF process noise vs EKF3 / FGO | identical per-second densities (EKF3's at DT_REF 12.5 ms; offline per-step forms scaled by DT_REF/dt) | — | CURRENT (D27) | M: "D27 RULED"; ukf_core.make_params |

## 5. Evaluation window and metric parameters

| quantity | value | units | status | source |
|---|---|---|---|---|
| Speed threshold | > 0.30 m/s | m/s | CURRENT | M:L41 |
| Boxcar (centred moving average) | 0.42 s | s | CURRENT | M:L38 |
| Boxcar historical equivalent | 25-sample boxcar at the ~59 Hz GT rate | — | CURRENT | M:L38-L39 |
| Window rule | largest contiguous run | — | CURRENT | M:L41-L42 |
| Alignment | `evo_ape -a` (Umeyama SE3, no scale) | — | CURRENT | M:L47 |
| Change vs historical per-clock windows | ≤ 0.051 m (EKF3 only) | m | CURRENT | M:L53 |
| Pre-cruise horizontal speed | ≤ 0.001 m/s | m/s | CURRENT | M:L57 |
| In-cruise smoothed speed | median 0.500 m/s and 1st percentile 0.497 m/s | m/s | CURRENT | M:L58 |
| Raw speed std | 0.005 m/s | m/s | CURRENT | M:L59 |
| Acceleration ramp 0.1 → 0.45 m/s | ~0.56 s | s | CURRENT | M:L60 |
| Sensitivity thresholds tested | 0.20 and 0.40 m/s | m/s | CURRENT | M:L71 |
| 0.20 m/s: max Δ evo -a (cruise), textured EKF3 / UKF / FGO (re-flown `dsn_tex` r1–r3) | 0.009 / 0.009 / 0.008 | m | CURRENT (final re-run 2026-10-10); not like-for-like with the old row | json:threshold_0.20_final.json |
| 0.40 m/s: same | 0.009 / 0.010 / 0.008 | m | CURRENT (final re-run 2026-10-10) | json:threshold_0.40_final.json |
| Divergence onset threshold | > 15 m | m | CURRENT | M:L552 |
| Failure metrics vs window (full vs cruise) | ratio by ≤ 0.05 and the onset by ≤ 1 m | — | CURRENT | M:L557-L558 |
| n=3 exceedance probability | 2/(n+1) = 50% | — | CURRENT | M:L132 |
| FGO deployability budget | 33 ms | ms | CURRENT | M:L698 |

## 6. Baseline results — RESTATED after the consolidated re-run (2026-09-29)

All values below come from the re-flown bags (sign fix, `FLOW_POS_Z 0.25`, UKF dt, roll gains,
time sync, replay logging). Sources are files in `eval/results/` and METHODOLOGY sections ("M:").
The former values are in the superseded section ("Former sections 6–9").

### 6.1 Textured `dsn`, evo -a (cruise)

| quantity | value | units | status | source |
|---|---|---|---|---|
| EKF3 r1 / r2 / r3 | 4.03 / 3.86 / 4.10 | m | CURRENT | json:rerun_dsn_evo.json |
| EKF3 mean / range | 4.00 / 0.24 | m | CURRENT | same |
| FGO (0.25 s) r1 / r2 / r3 | 4.07 / 1.93 / 4.47 | m | CURRENT (final re-run 2026-10-10) | json:rerun_dsn_evo.json |
| FGO mean / range | 3.49 / 2.54 (bimodal: r2 low, as the UKF) | m | CURRENT (final re-run 2026-10-10) | same |
| UKF r1 / r2 / r3 | 3.98 / 1.61 / 5.17 | m | CURRENT (final re-run 2026-10-10) | same |
| EKF3 vs FGO (claim wording) | **WITHDRAWN (ruling 2, 2026-10-10): "EKF3 beats / is lower than the FGO on standard sensors (textured floor)".** Reason: the confirmatory test that confirmed it used the FGO with the mis-specified noise model; with the corrected FGO the same test, same rule, gives "no ordering claimed" (row below). Was: "now CONFIRMED by the pre-registered test; the earlier interim wording 'EKF3 lower on all three repeats' is superseded" | — | WITHDRAWN | M: "RULINGS (user, 2026-10-10)" item 2 |
| **Confirmatory test, EKF3 vs FGO** (r4–r10, pre-registered; r10 unusable for FGO; d = EKF3 − FGO) | **no ordering claimed** (REPLACES the old verdict, ruling 2): d < 0 on 5/7 (one positive: r6 +1.68; r10 counts against both), mean d −0.040 m, 95% CI [−0.934, +0.853]; one-sided sign-test p 0.227 (EKF3 lower) / 0.992 (FGO lower). (a) and (b) both fail; df 5 or 6 does not change it | m | CURRENT (final re-run 2026-10-10) | json:dsn_paired_test.json |
| Confirmatory test, OLD verdict | "EKF3 lower" (d < 0 on 6/7, mean d −0.69 m, 95% CI [−1.16, −0.21]): **computed with the mis-specified FGO noise model** (`biasAccOmegaInt` ≠ 0). Not cited as a result | m | WITHDRAWN (ruling 2) | results_pre_final/dsn_paired_test.json |
| Noise floor SD (re-flown `dsn_tex`): EKF3 (n = 10) / FGO (n = 9) / d (n = 9) | 0.31 [0.22, 0.57] / **1.23 [0.83, 2.36]** / 0.96 [0.65, 1.83] (the FGO is no longer the "tight" estimator) | m | CURRENT (final re-run 2026-10-10) | json:dsn_paired_test.json |
| **Claim wording (D15, supersedes "the UKF is poor in most textured flights")** | with EKF3's ground-proximity flow rule the UKF is stable on all 9 usable `dsn_tex` flights (1.17–5.85 m, median 5.13; above EKF3 4.10 and FGO 4.45 by median, descriptive) and ≤ 5.85 m on 14 of 17 textured flights overall; 3 of 17 (p1c_fwdc 7.34, fwdplainc r2 11.19, r3 10.82) are 7.3–11.2 m with a residual post-detection take-off kick that EKF3 does not show (a UKF flow→yaw property; the kick magnitudes −1.4 … −4.4° were not recomputed in the final re-run) | m | CURRENT (final re-run 2026-10-10) (wording) | json:rerun_dsn_evo.json, dsn_extra_evo.json, rerun_fwdc/fwdplainc/p1c_evo.json |
| EKF3's flow timestamp against our flow (28 re-flown trials with flow fused) | EKF3 fuses flow 31–44 ms before capture (median 36), i.e. 15–27 ms before the frame's mid-time (median 19): its hard-coded 100 ms flow interval against our 30 Hz flow | ms | CURRENT (finding; D8) | json:input_timing_rerun_all.json |
| UKF r1–r9 (usable): median / range / SD | 5.13 / 1.17–5.85 / 1.70 (instability rule > 3× median: 0/9) | m | CURRENT (final re-run 2026-10-10) | json:rerun_dsn_evo.json, dsn_extra_evo.json, dsn_paired_test.json |
| UKF cruise yaw drift, `dsn_tex` r1–r9 / transition (ENU; all westward) | −7.6, −2.3, −10.0, −10.1, −9.9, −0.7, −10.1, −11.4, −9.8 / −10.3, −12.9, −10.2 | deg/min | CURRENT (final re-run 2026-10-10) | json:d15_drift.json |
| UKF take-off yaw change, `dsn_tex` r1–r9 | **\|Δ\| ≤ 0.82°** (r8 −0.82; ruling 9: the former "≤ 0.79°" bound is exceeded by 0.03°) (was −17.0 … +5.4° before D15) | deg | CURRENT (final re-run 2026-10-10) | json:d15_kick.json |
| FGO cruise yaw drift, `dsn_tex` r1–r9 / take-off yaw change | −8.0, −3.6, −8.9, −8.8, −9.1, −2.5, −9.1, −9.0, −8.4 (now bias-tracks on r2/r6 too; was −9.1 … −9.4 on all) / \|Δ\| ≤ 0.09° | deg/min / deg | CURRENT (final re-run 2026-10-10) | json:d15_drift.json, d15_kick.json |
| **Textured `dsn` standing of the UKF (descriptive; no ordering is claimed, no test)** | **mean of r1–r3: FGO 3.49 < UKF 3.59 < EKF3 4.00 (the UKF is NOT last; old: UKF 3.91 < EKF3 4.00 < FGO 4.64)**. Median of r1–r9: UKF 5.13 > FGO 4.45 > EKF3 4.10 (UKF highest by median); UKF highest on 6/9 flights, lowest on 3/9 (r1, r2, r6). n = 3 means are driven by the bimodal r2 (and r6) flights | m | DESCRIPTIVE (final re-run) | json:rerun_dsn_evo.json, dsn_extra_evo.json |
| Compass-active `ds_*` EKF3, textured r1 / r2 / r3 | 0.66 / 0.69 / 0.07 | m | CURRENT (reference; EKF3 with an absolute heading) | json:rerun_ds_evo.json |

### 6.2 Transition and blank: behaviour under total loss of flow aiding (not accuracy)

| quantity | value | units | status | source |
|---|---|---|---|---|
| Valid airborne flow frames in cruise, blank (all 14 blank bags) | 0 | — | CURRENT | M: "Loss-of-flow analysis — flow-loss point defined" |
| Flow-loss cases | transition 14/14 B (y ≈ 80.5 m); blank 13 A + 1 C (`ds_blank_r2`) | — | CURRENT | same |
| EKF3 position flagged invalid | transition +0.9…+1.1 s after loss, for 139–141 s of cruise; blank from take-off (all 14), for 301–310 s | s | CURRENT | json:blank_behaviour.json |
| EKF3 output while invalid | exactly the origin (0, 0); not scored (evaluation rule) | — | CURRENT | M: "Rulings on the early pipeline results" |
| Compass-active `ds_blank` EKF3 evo -a (cruise), r1 / r2 / r3 | 43.68 / NaN / NaN: in all three the cruise output is a single point (the origin; 2,950 rows, xy std 0). evo's SE(3) alignment of a constant trajectory is undefined (NaN), and r1 is finite only from moving samples at the window edge. None is scored (invalid-output rule). | m | RECORDED (artefact) | json:rerun_ds_evo.json |
| UKF baseline position error magnitude at +10 / +30 / +60 s after loss, blank (n = 11: `dsn`, `fwdc`, `fwdplainc`, `p1c`) | 6.4–8.2 / 27.3–36.5 / 60–108 | m | CURRENT (final re-run 2026-10-10) | json:blank_behaviour.json |
| FGO baseline, same | 6.4–8.2 / 28.0–37.0 / 155–204 | m | CURRENT (final re-run 2026-10-10) | same |
| UKF / FGO baseline error at the end of cruise, blank †| 29–40 / 19–41 | km | CURRENT (final re-run 2026-10-10) | same |
| UKF / FGO baseline error at +60 s after loss, transition (n = 11) †| 129–139 / 223–231 | m | CURRENT (final re-run 2026-10-10) | json:blank_behaviour.json |
| Heading arms (n = 6, `fwdc`/`fwdplainc`), blank, +60 s: UKF / FGO †| 40–89 / 132–193 | m | CURRENT (final re-run 2026-10-10) (the heading still does not bound position without flow) | json:blank_behaviour.json |
| `dsn` transition displacement ratio, UKF / FGO (mean of 3) †| 6.8 / 26.8 (was 45.9 / 50.0); still divergence, not accuracy. Transition and blank are NOT ranked by evo (EKF3's output there is the invalid origin, not scored) | — | CURRENT (final re-run 2026-10-10) | json:rerun_dsn_evo.json |

### 6.3 Other current estimator results

| quantity | value | units | status | source |
|---|---|---|---|---|
| Heading share of EKF3 lateral drift (pinned window), `dsn_tex_r3` / r1 / r2 | 0.906 / 0.904 / 0.899 | — | CURRENT (correction (iii)) | json:heading_share_restated.json |
| EKF3 lateral errV, `dsn_tex_r3` | 0.133 m/s (cross-track 40.2 m) | m/s | CURRENT | same |
| EKF3 lateral flow innovation, airborne mean \|FIX\| (textured, check flight) | 7 (321 before; ~300–450 in every old dataset) | ×1000 rad/s | CURRENT | M: "Check flight `rgs_check_tex` — result" |
| Rows of the former 6.3 not recomputed (FINDING 1 residual slopes, EKF3 bias-correction share, filter-consistency %, flow-residual partition, gyro-z ramp tracking) | pre-re-run values (in the superseded section); **must be recomputed before being cited** (sign fix and roll gains) | — | NOT RESTATED | — |

### 6.4 Forward-camera datasets, textured, evo -a (cruise)

| quantity | value | units | status | source |
|---|---|---|---|---|
| `fwdc` textured EKF3 r1 / r2 / r3 | 4.09 / 3.60 / 4.08 | m | CURRENT | json:rerun_fwdc_evo.json |
| `fwdc` textured FGO r1 / r2 / r3 | 4.46 / 2.39 / 4.53 (mean 3.79; EKF3 3.92) | m | CURRENT (final re-run 2026-10-10) | json:rerun_fwdc_evo.json |
| `fwdc` textured UKF r1 / r2 / r3 | 4.96 / 1.78 / 4.96 (mean 3.90) | m | DIAGNOSTIC (final re-run) | same |
| `fwdplainc` textured EKF3 r1 / r2 / r3 | 4.08 / 4.06 / 4.08 | m | CURRENT | json:rerun_fwdplainc_evo.json |
| `fwdplainc` textured FGO r1 / r2 / r3 | 4.52 / 4.51 / 4.72 | m | CURRENT (final re-run 2026-10-10) | json:rerun_fwdplainc_evo.json |
| `fwdplainc` textured UKF r1 / r2 / r3 | 5.02 / 11.19 / 10.82 | m | DIAGNOSTIC (final re-run; r2, r3 residual take-off kick remains) | same |
| `p1c` textured EKF3 / FGO (`fwdc`, `fwdplainc`) | 4.14 / **5.20**; 4.11 / 4.59 (p1c_fwdc FGO 5.20 lies outside the old FGO band [4.189, 5.117] and passes only because the band widened, §7) | m | CURRENT (final re-run 2026-10-10) | json:rerun_p1c_evo.json |

### 6.5 Distance scale (textured `fwdc`, n = 3)

| quantity | value | units | status | source |
|---|---|---|---|---|
| Flow sensor scale (`flow_y` slope) | 0.987 (was 1.009); the steadier camera, **not tuned** | — | CURRENT | json:scale_check.json |
| EKF3 speed ratio / along-track ratio | 0.996–0.997 / 0.972–0.979 | — | CURRENT (correction (i)) | same |
| FGO baseline / +heading speed ratio | 0.998–0.999 / 0.998–0.999 | — | CURRENT (final re-run 2026-10-10) | json:scale_check.json |
| UKF +heading speed / along-track ratio | 0.996–0.997 / 0.996–0.997 (the residual 1% under-scale is gone; now matches the FGO) | — | CURRENT (final re-run 2026-10-10) | same |
| EKF3 speed ratio: tsx 1.02 vs "0.935" | different quantities; 0.935 WITHDRAWN (heading-dependent North projection) | — | CURRENT (note) | M: "EKF3 speed ratio: tsx 1.02 against rgs 0.935" |

### 6.6 Phase 4 (offline forward-camera fusion), textured, evo -a (cruise)

| quantity | value | units | status | source |
|---|---|---|---|---|
| `fwdc` UKF +heading r1 / r2 / r3 | 0.13 / 0.13 / 0.14 (0.127 / 0.134 / 0.137; about 5× better than before) | m | CURRENT (final re-run 2026-10-10) | json:phase4_fwdc_arms.json |
| `fwdc` FGO +heading r1 / r2 / r3 | 0.06 / 0.06 / 0.06 | m | CURRENT (final re-run 2026-10-10) | same |
| `fwdc` +heading+yaw rate (UKF / FGO) | equal to +heading to 0.01 m | m | CURRENT | same |
| `fwdplainc` UKF +heading r1 / r2 / r3 | 0.19 / 0.15 / 0.25 | m | CURRENT (final re-run 2026-10-10) | json:phase4_fwdplainc_arms.json |
| `fwdplainc` FGO +heading r1 / r2 / r3 | **43.5 / 42.7 / 43.1** (yaw divergence of the hard-gated FGO on plain walls, row below) | m | CURRENT (final re-run 2026-10-10) | same |
| **Plain-wall FGO yaw divergence (hard, EKF3-style gate), `fwdplainc` textured and transition** | gyro-z bias runs away (−267 … −480 / +447 deg/min against a true +8.9); 19–28 of 6,197–8,431 valid headings fused; median heading NIS 1,740–13,121; yaw-error RMS 838–1,497°. Not on blank (8.6 k headings fused), not on `fwdc`, not in the FGO baseline. Reported as a property of the corrected FGO WITH THE HARD GATE (ruling 1); the robust FGO is the best arm there. **Mechanism: TRACE PENDING** (bounded offline trace running; gate lockout vs model inconsistency not yet decided) | — | CURRENT (final re-run 2026-10-10) (trace pending) | json:phase4_fwdplainc_arms.json; final_restatement_draft.md §2.1 |
| Heading-arm yaw error rms, `fwdc` (UKF / FGO) | 0.07–0.08 / 0.07–0.08: **with heading on `fwdc` the UKF ≈ the FGO** (ruling 9; the former "UKF about 2× lower yaw error than the FGO" no longer holds on `fwdc`) | deg | CURRENT (final re-run 2026-10-10) | same |
| Heading-arm yaw error rms, `fwdplainc` textured (UKF / FGO) | 3.08–3.39 / 838–1,014 (the FGO divergence above) | deg | CURRENT (final re-run 2026-10-10) (trace pending for the FGO) | json:phase4_fwdplainc_arms.json |
| **C0 (FGO vs UKF with heading, textured)** | FGO lower on 3/3 `fwdc` (0.06 vs 0.13 m); **UKF lower on 3/3 `fwdplainc`** (0.15–0.25 vs 43 m). Was "FGO lower on all 6". The reversal is the plain-wall divergence (trace pending) | m | CURRENT (final re-run 2026-10-10) | json:phase4_*_arms.json |
| FGO vs UKF with heading (claim wording) | implementation result: FGO lower on textured walls (`fwdc`), UKF lower on plain walls (`fwdplainc`, hard-gated FGO divergence, trace pending); the UKF's residual take-off kick (D15) and plain-wall over-confidence (NEES 13.41) stated alongside | — | CURRENT (final re-run 2026-10-10) (wording) | M: "D15 RESULTS"; final re-run |
| UKF +heading vs EKF3 without heading | **not a fair comparison; never stated as the UKF being better** | — | CURRENT (wording) | same |
| `fwdplainc` textured UKF +heading mean position NEES, mean of r1–r3 | 13.41 (14.39 / 12.75 / 13.10) (was 6.11; more over-confident on plain walls) | — | DIAGNOSTIC (final re-run) | json:phase5b_consistency.json |
| FGO baseline cross-track mean NEES, `fwdc` textured (mean of r1–r3) | 1.67 (2.3 / 0.2 / 2.5; was 57.1: the FGO's covariance is no longer ~57× over-confident; predicted yaw σ 0.476° → 0.057°) | — | DIAGNOSTIC (final re-run) | json:phase5b_consistency.json |
| FGO +heading NEES, `fwdplainc` (P5b); end-wall yaw-prediction NEES `fwdplainc/FGO` | 0.05 → 24.8; 4.15 → 3.7 × 10⁶ (both from the plain-wall divergence) | — | DIAGNOSTIC (final re-run; trace pending) | same |

## 7. Pre-registered bands — P4 recomputed from the re-flown `dsn` (same formula)

| quantity | value | units | status | source |
|---|---|---|---|---|
| P1 flow/LiDAR/IMU timing | unchanged: 30.30 Hz ± 0.1%, ≤ 0.5% late; IMU gap 3.0005 ± 0.003 ms, p99 ≤ 10 ms | — | CURRENT (pre-registered) | M: Phase 1/2 |
| P2 latency | same-world `dsn` mean + 12.5 ms; **undefined on blank (no flow fused)** | ms | DIAGNOSTIC | json:rerun_latency_check.json |
| P3 references (textured `dsn`): inlier / % < 0.5 / features / `flow_y_raw` | 0.9839 / 0.0036% / 52.40 / 134.49 px/s | — | CURRENT | json:flow_quality_dsn.json |
| P3 references (transition) | 0.6341 / 46.48% / 30.54 / 66.54 px/s | — | CURRENT | same |
| P3 references (blank) | 0.2360 / 99.66% / 5.84 / −11.47 px/s | — | CURRENT | same |
| P4 EKF3 textured | [3.613, 4.340] m (n = 3 range 3.86–4.10 widened by one range-width) | m | CURRENT (recomputed) | json:rerun_p4_bands.json |
| P4 FGO textured | **[−0.614, 7.017] m** (registered formula on the corrected r1–r3, range 1.93–4.47 ± one range-width). **CAVEAT (ruling 3): too wide to be informative**: its lower bound is negative and it cannot fail any plausible textured value. Kept as computed by the registered formula | m | CURRENT (final re-run 2026-10-10) (recomputed; uninformative) | json:rerun_p4_bands.json |
| P4 transition/blank bands | computed by formula, but they measure EKF3 invalid output / UKF-FGO runaway size, not sensing. FGO now: transition ratio [1.406, 49.073], onset [88.25, 98.315] m; blank ratio [18.009, 342.823], onset [12.099, 23.679] m † | — | RECORDED (context: rulings 1 and 3; final re-run) | same |

## 8. Dataset pass/fail counts (re-flown)

| quantity | value | units | status | source |
|---|---|---|---|---|
| Re-fly batch | 42 trials complete (33 main + 9 `ds`); one harness abort, re-flown | — | CURRENT | M: "Consolidated re-fly — aborted attempt" |
| IMU gap rule on the 42 bags | 39 `ok`, 3 `trim`, 0 `unusable` | — | CURRENT | `<trial>/imu_gaps.json` |
| `p1c` primary | 6/6 pass | — | CURRENT | json:rerun_p1c_score.json |
| `fwdc` primary †| **8/9 pass** (was 6/9; miss: `fwdc_tex_r2` EKF3 0.01 m outside its band, unchanged). `fwdc_blank_r1`, `r2` now pass their FGO ratio/onset bands, partly because the FGO bands moved with the FGO itself, not only from better estimates; `fwdc_tex_r2` FGO 2.39 would fail the old textured band | — | CURRENT (final re-run 2026-10-10) (misses as worded) | json:rerun_fwdc_score.json |
| `fwdplainc` primary †| **9/9 pass** (was 8/9; `fwdplainc_blank_r2` FGO ratio now inside the moved band) | — | CURRENT (final re-run 2026-10-10) | json:rerun_fwdplainc_score.json |
| Phase 3 heading validation | `fwdc` 9/9, `fwdplainc` 6/9 (checkerboard fails) | — | CURRENT (unchanged) | json:fwd_validation.json |
| Phase 3 yaw-rate validation | `fwdc` 9/9; `fwdplainc` 3/9 (textured 3/3 now; transition/blank fail on availability 67–69%) | — | CURRENT | same |
| Phase 3 second validation on the re-flown `p1c` | heading 5/6 (fails `p1c_fwdplainc_tex`); yaw rate 4/6 | — | CURRENT | json:fwd_validation_p1c.json |

## 9. Forward-camera measurement results — RESTATED (frozen parameters unchanged)

| quantity | value | units | status | source |
|---|---|---|---|---|
| Frozen parameters | unchanged: inlier 0.5°, S_MIN 200 px, box 80 px, N_MIN 5; OpenCV 4.6.0 / numpy 1.26 pinned | — | CURRENT | json:fwd_calibration.json; M: "Rulings (user, 2026-09-29) on Parts 1 and 2" |
| Validation heading `fwdc` tex / trans / blank (avail / sd / outliers) | 96.6% / 0.199° / 0.08%; 96.6% / 0.131° / 0.01%; 96.6% / 0.106° / 0.00% | — | CURRENT | json:fwd_validation.json |
| Validation heading `fwdplainc` tex / trans / blank | 60.5% / 0.648° / 13.62%; 87.3% / 0.377° / 3.25%; 95.5% / 0.150° / 0.08% | — | CURRENT | same |
| Validation yaw rate `fwdc` (avail / sd) | 97.3–99.9% / 0.031–0.035 deg/s (was 0.13–0.21) | — | CURRENT | same |
| Validation yaw rate `fwdplainc` tex / trans / blank (avail / sd / outliers) | 88.5% / 0.288 / 0.42%; 66.9% / 0.278 / 0.58%; 68.6% / 0.331 / 0.31% | — | CURRENT | same |
| Static sweep results | not re-rendered (a static render tool, unaffected by flight corrections) | — | CURRENT (unchanged) | json:fwd_yaw_sweep.json |

### Rows elsewhere in this file affected by the corrections but NOT recomputed

- **§1:** cruise roll / pitch statistics (the roll limit cycle is removed), and the RTF of the
  forward-camera datasets.
- **§2:** P2 latencies (the re-flown values are in `rerun_latency_check.json`).
- **§11:** the ceiling effect size. It was computed on pre-correction `fwd*`/`fwdc` bags;
  transition `flow_y_raw` has since moved from ~71.5 to ~66.3 px/s.
- **§14:** timing figures (see the Phase 4 timing in `phase4_*_arms.json`, which is DIAGNOSTIC).
- **These must be recomputed on the re-flown bags before being cited.**

## 10. Phase 4 (pre-registered only; results still running)

**No Phase 4 results exist in the snapshot.** The replay batch was running when this pack
was prepared. Only pre-registered values are listed.

| quantity | value | units | status | source |
|---|---|---|---|---|
| Arms, `fwdc_*` | baseline / +heading / +heading+yaw rate | — | CURRENT (pre-registered) | M:L2949 |
| Arms, `fwdplainc_*` | baseline / +heading | — | CURRENT (pre-registered) | M:L2950 |
| Replay runs | 90 replay runs | — | CURRENT (pre-registered) | M:L2952 |
| Heading validity | support ≥ S_MIN = 200 px | px | CURRENT (pre-registered) | M:L2960 |
| Yaw-rate validity | ≥ N_MIN = 5 tracked corners | — | CURRENT (pre-registered) | M:L2960 |
| σ_ψ `fwdc` / `fwdplainc` (static sweep) | **`fwdc` 0.148°**, **`fwdplainc` 0.126°** | deg | CURRENT (pre-registered) | M:L2980 |
| σ_ω `fwdc` (derived) | 0.106 × (0.148/0.097) = 0.162 deg/s | deg/s | CURRENT (pre-registered) | M:L2986 |
| χ² gate | ν²/S ≤ 9 | — | CURRENT (pre-registered) | M:L2990 |
| Implemented gate (code) | `FWD_CHI2_GATE = 9.0` | — | CURRENT (matches the pre-registration) | code:src/estimators/measurement_models.py:L146 |
| Implemented σ (code) | `np.radians(0.148)`, `np.radians(0.162)`; `np.radians(0.126)`, `None` | rad | CURRENT (matches the pre-registration) | code:src/estimators/measurement_models.py:L151-L152 |
| FGO gate-recursion information matrix | 30-dimensional | — | CURRENT (pre-registered) | M:L2997 |
| Timing periods: UKF predict / FGO keyframe | 80 Hz, period 12.5 ms / 30 Hz, period 33.3 ms | ms | DIAGNOSTIC (pre-registered) | M:L3005-L3006 |

## 11. Ceiling effect size (transition `flow_y_raw`, ceiling n = 8 vs no-ceiling n = 8)

| quantity | value | units | status | source |
|---|---|---|---|---|
| Whole cruise: ceiling / no-ceiling mean (sd) | 71.87 (1.00) / 71.44 (0.58) | px/s | CURRENT | M:L2591 |
| Whole cruise: difference, Welch t (df), p | **+0.43 px/s (+0.6%)**, 1.06 (11.2), 0.31 | px/s | CURRENT | M:L2591 |
| Textured half: difference, t (df), p | +0.10 px/s (+0.07%), 0.39 (13.0), 0.70 | px/s | CURRENT | M:L2592 |
| Blank half: ceiling / no-ceiling mean (sd) | −2.08 (2.43) / −2.39 (0.85) | px/s | CURRENT | M:L2593 |
| Blank half: difference, t (df), p | +0.31 px/s, 0.34 (8.7), 0.74 | px/s | CURRENT | M:L2593 |
| Blank-half variance ratio (Levene p) | 8.1 (Levene p = 0.17 | — | CURRENT | M:L2599 |
| Cross-check (JSON) difference | 0.4331935635006232 | px/s | CURRENT | json:ceiling_flow_effect.json:groups.all.difference |
| Over-band flights' blank-half means | +0.87 … +1.30, against −6.40 to −1.34 | px/s | CURRENT | M:L2601 |

p-values and the Levene test appear only in METHODOLOGY; the JSON stores means, sd, the
difference, Welch t and df.

## 12. ArduPilot limits and source facts

| quantity | value | units | status | source |
|---|---|---|---|---|
| ExternalNav yaw floor inside EKF3 | `yawAngErr = MAX(angErr, radians(5))` | deg | CURRENT | M:L3106 |
| `VISO_YAW_M_NSE` default | 0.2 rad | rad | CURRENT | M:L2912 |
| `VISO_YAW_M_NSE` documented range | 0.05–1.0 rad | rad | CURRENT | M:L2912 |
| `VISO_YAW_M_NSE` floor (ruling wording) | ≥ 0.05 rad | rad | CURRENT | M:L2874 |
| UKF/FGO heading noise quoted against the floor | 0.13–0.15° | deg | CURRENT | M:L3111 |
| `AHRS_EKF_TYPE` default injection | `SIM_JSON.cpp:410-413` … `set_default_by_name("AHRS_EKF_TYPE", 10)` | — | CURRENT | M:L3098-L3099 |
| Model flag | `<no_time_sync>1</no_time_sync>` (`model.sdf:789`) | — | CURRENT | M:L3100 |
| Recorded logs | `LOG_REPLAY=0` and `LOG_DISARMED=0` | — | CURRENT | M:L2923 |
| Future flights | `LOG_REPLAY=1` and `LOG_DISARMED=1` | — | CURRENT | M:L2863 |
| ArduPilot pinned commit | `7bac20cbcc` | — | CURRENT | M:L2890 |

## 13. Part C (onboard feasibility) — estimates

| quantity | value | units | status | source |
|---|---|---|---|---|
| Target flight controller | STM32H743 flight controller** (2 MB flash, ~1 MB RAM) | — | CURRENT (supervisor) | M:L3034 |
| UKF onboard flash | ~25–50 kB flash | kB | ESTIMATE | M:L3063 |
| UKF onboard RAM | < 16 kB RAM | kB | ESTIMATE | M:L3063 |
| UKF onboard CPU | ~2–8% CPU | % | ESTIMATE | M:L3063 |
| Free flash on current builds | About 270–325 kB | kB | ESTIMATE (from published `.apj`) | M:L3063-L3064 |
| `EKF3.*` call sites in `AP_AHRS` | 86 | — | CURRENT (source count) | M:L3067 |
| `EKFType` switch arms needed | about 52 | — | ESTIMATE | M:L3070 |
| Shadow-run evidence, `dsn_tex_r1` | 6654 `XKF1` rows, 2 lanes | — | CURRENT | M:L3072 |
| QuadPlane loop rate | 300 Hz | Hz | CURRENT | M:L3073 |
| FGO Python step (Part C, textured) | 29 ms/step | ms | DIAGNOSTIC (workstation; measured BEFORE the thread-limit fix, may be inflated; not current) | M:L3081 |
| Camera pipeline (Python, i7, under load) | ≤ 61 ms/frame | ms | DIAGNOSTIC (workstation; measured BEFORE the thread-limit fix, may be inflated; not current) | M:L3082 |
| Wall contact from GT | \|x\| ≥ 9.58 m | m | CURRENT | M:L3088 |
| Distance scale, EKF3 vs FGO (n = 9; Part C summary, rounded) | EKF3 +6–10% against the FGO's ~+1% | % | CURRENT (candidate; exact values in §6.5) | M:L3091 |
| Effort | ~18–30 person-weeks (estimate), plus 4–6 if route (b) is built | person-weeks | ESTIMATE | M:L3094 |

## 14. Timing figures

All timing figures are **DIAGNOSTIC (workstation)**: measured in Python on the workstation,
with parallel jobs and load not recorded; they say nothing directly about onboard feasibility
(M:L3137-L3139). The FGO step time is world-dependent and must state its world (M:L3131-L3132).

| quantity | value | units | status | source |
|---|---|---|---|---|
| FGO step time, 0.25 s window, textured (pre-fix figure) | ~29 ms median on textured bags | ms | DIAGNOSTIC (workstation; measured BEFORE the thread-limit fix, may be inflated; not current) | M:L3121 |
| FGO stored medians, textured (`dsn`/`fwdc`/`fwdplainc`), n = 9 | 26.9–29.2 | ms | DIAGNOSTIC (workstation; measured BEFORE the thread-limit fix, may be inflated; not current) | M:L3126 |
| FGO stored medians, transition, n = 9 | 15.1–15.7 | ms | DIAGNOSTIC (workstation; measured BEFORE the thread-limit fix, may be inflated; not current) | M:L3127 |
| FGO stored medians, blank, n = 9 | 4.0–4.3 | ms | DIAGNOSTIC (workstation; measured BEFORE the thread-limit fix, may be inflated; not current) | M:L3128 |
| FGO window sweep step time at 1.0 / 0.5 / 0.25 s (`dsn_tex_r1`, 2026-08-01, `04426d2`) | 96 / 48 / 27 ms | ms | DIAGNOSTIC (workstation; measured BEFORE the thread-limit fix, may be inflated; not current) | M:L710 |
| FGO step, post-fix, baseline textured (6 jobs parallel, 1 thread) | 32.7–32.9 median / 37–38 p95 | ms | DIAGNOSTIC (workstation; CURRENT, post-fix) | M: "RULINGS (user, 2026-09-29) after Phase 4" §3; eval/results/phase4_*_arms.json |
| FGO step, post-fix, baseline `fwdc_tex_r2` (identity check, 3 parallel) | 27.6 | ms | DIAGNOSTIC (workstation; CURRENT, post-fix) | M: "Phase 4 run note" |
| FGO step, post-fix, +heading / +heading+yaw rate, textured | 37–40 / 42 median | ms | DIAGNOSTIC (CURRENT, post-fix) | M: Phase 4 result, timing |
| FGO step, post-fix, transition baseline / +heading | 17–18 / 23–35 median | ms | DIAGNOSTIC (CURRENT, post-fix) | M: Phase 4 result, timing |
| FGO step, post-fix, blank baseline / +heading | 4.5 / 11–12.5 median | ms | DIAGNOSTIC (CURRENT, post-fix) | M: Phase 4 result, timing |
| UKF predict / forward update, post-fix | 1.5–1.6 / 0.25–0.49 median | ms | DIAGNOSTIC (CURRENT, post-fix) | M: Phase 4 result, timing |
| LM iterations cap | capped at 2 (warm-started) | — | CURRENT | M:L714 |
| Capped vs full LM | max position difference 0.11 m, **RMS 0.029 m** | m | CURRENT | M:L715 |
| Keyframes, `dsn_tex_r1` | 10047 | — | CURRENT | M:L717 |
| iSAM2 step time / cascade point | 0.2 ms/step … after ~590 keyframes | ms | DIAGNOSTIC (workstation) | M:L1125-L1126 |
| 9-bag FGO run time at 0.25 s vs 1.0 s | ~40 min (was 2.4 h at 1.0 s) | — | DIAGNOSTIC (workstation) | P:L258 |

The window-sweep ATEs (M:L701), which are the evidence that ATE does not depend on the window,
are pre-correction, receipt-stamp values and are listed in the superseded section.

---

## 15. Closed loop (the estimator flies the vehicle) — CURRENT after D28 (2026-10-02)

Textured corridor, 0.5 m/s, 300 s cruise. Full speed = `corridor_textured_fwdc`; half speed = `corridor_textured_half_fwdc` (loopback-pinned, `VISO_DELAY_MS` 25). No cross-speed comparison is claimed (D21). n = 1 per no-heading cell; closed-loop run-to-run variability is unmeasured.

| Quantity | Value | Unit | Status | Source |
|---|---|---|---|---|
| No heading, west-wall contact (cruise +): EKF3 full / half | +186.2 (PASS, window [+155, +215]) / +242.1 (MISS, D21) | s | CURRENT | json:closed_loop_cl_a_tex.json, closed_loop_cl_a_tex_half.json |
| No heading, contact: UKF full / half | +163.0 (PASS, [+146, +218]) / +198.0 (PASS, [+146, +218]) | s | CURRENT | M: "cl_ukf_a_tex"; json:closed_loop_cl_ukf_a_tex_half.json |
| No heading, contact: FGO (half only) | +165.8 (PASS, [+145, +196]; open-loop prediction +169.6) | s | CURRENT | json:closed_loop_cl_fgo_a_tex_half.json |
| No heading, contact: final corrected FGO re-flight `cl_fgo_a_tex_half_v3` | +169.9 west (U3 PASS, inside the registered [+145, +196]; U1/U2 PASS). The registered prediction and its band stand | s | CURRENT | M: "FGO re-flight `cl_fgo_a_tex_half_v3`" |
| **Contact-prediction consistency check (POST-HOC, corrected FGO replayed open loop; not a prediction)** | n = 8 of the original 10 realisations: 4 west (+154 … +198 s), 3 east, 1 no contact; median of the 7 contacts +162.9 s. The corrected FGO no longer drifts consistently west, so the method would not have given a tight west cluster. **Two cases missing: `fgo_shadow_half_a` (offline, not recomputed) and the live `XFGO` (no live XFGO recomputation exists)** | s | DESCRIPTIVE (post hoc; ruling 11) | json:fgo_contact_prediction_half_final.json |
| No heading, yaw drift over first 150 s of cruise: EKF3 full / half; UKF full / half; FGO half | 4.31 / 2.13; 5.45 / 3.89; 5.48 | deg/min | DESCRIPTIVE (n = 1 each) | M: D21; "cl_fgo_a_tex_half" |
| With heading, flights passing B1–B5 (+S2 UKF/FGO): EKF3 full (Python / C++) / half | 3/3, 3/3 / 3/3 | — | CURRENT | json:closed_loop_cl_b*_tex*.json |
| With heading: UKF full / half | 3/3 / 2/3 (r3 B4, D22 flow validity) | — | CURRENT | json:closed_loop_cl_ukf_b_tex*.json |
| With heading: FGO hard-gated / robust (half) | **3/3 / 3/3** (D28; first scored 2/3 each, B5 window artefact) | — | CURRENT (D28) | json:closed_loop_cl_fgo_b*_tex_r*_half.json |
| With heading, B2 max cross-track (EKF3 full C++, EKF3 half, UKF full, UKF half, FGO hard, FGO robust) | 0.23–0.34, 0.24–0.33, 0.16–0.29, 0.13–0.53, 0.06–0.25, 0.05–0.14 | m | CURRENT | same |
| With heading, B3 yaw error p95 / max (same order) | 0.28–0.31/0.40–0.42, 0.28–0.32/0.33–0.39, 0.17–0.21/0.26–0.31, 0.18–0.21/0.28–1.32, 0.26–0.38/1.28–1.88, 0.26–0.30/0.86–1.15 | deg | CURRENT | same |
| FGO climb-top true overshoot (no heading / with heading r1–r3 / robust) | +0.94 / 0, +0.11, +0.24 / descriptive | m | DESCRIPTIVE (D23 artefact; scales with short LiDAR returns 7 / 0, 1, 3) | json:climb_top_response_cl_fgo_*.json |
| FGO heading timing: applied after capture (median / max) | 17 / 33 | ms | CLOSED as negligible (≈0.015°) | json:fgo_heading_timing.json |
| Per-heading weight at equal sensor noise: FGO / UKF (closed loop, 5° R) | FGO **≈ 1.3–1.4 %** on the `_v3` re-flights (window-median predicted σ 0.57–0.59°; R = 5° confirmed from the logged NIS) (was 15.9 %, σ 2.17°); **UKF: OPEN** (the 2.9 % is the old UKF on a different flight). **No FGO/UKF ratio is stated** | % | FGO CURRENT (final re-run 2026-10-10); UKF OPEN | final_restatement_draft.md §7; batches/final_rerun/d26gate_*_v3.txt |
| Fast yaw jitter (cruise): FGO hard / robust / EKF3 / UKF | 0.031–0.041 / 0.030–0.037 / 0.006–0.007 / 0.007–0.009 | deg | DESCRIPTIVE (EXPLORATORY) | json:d26_jitter_control.json, p2b_jitter_control.json |
| Coupling corr(true yaw rate, −de/dt): FGO hard / robust / EKF3 / UKF / passive shadow | +0.68…+0.74 / +0.67…+0.70 / +0.09…+0.13 / +0.24…+0.28 / ≈0 | — | DESCRIPTIVE (EXPLORATORY) | same |

### 15.1 Robust heading weighting (plan step 2)

| Quantity | Value | Unit | Status | Source |
|---|---|---|---|---|
| 2(a) fresh open-loop flights: P1 robust < hard-gated FGO yaw max | 7/12 (≥ 10 needed): **FAIL** (was 9/12; on `fwdc` the two arms are now equal, Δ ≤ 0.05°) | — | CURRENT (final re-run 2026-10-10) (2 IMU-gap exclusions counted against) | json:f4_test.json |
| 2(a) S1 fewer wrong headings accepted, plain walls | 5/6: **PASS** (13–26 vs 49–91 accepted) | — | CURRENT | same |
| 2(a) S2 max cross-track ≤ hard-gated | 5/12 (≥ 8 needed): **FAIL** (was 6/12) | — | CURRENT (final re-run 2026-10-10) | same |
| 2(a) against the UKF (descriptive) | **robust FGO lower yaw max on 8/10** (ruling 9: the former "UKF lower yaw max 10/10" reverses), yaw rms 9/10, cross-track 10/10. Lockout totals UKF_hard / FGO_hard / FGO_robust 6 / 23 / 6 (was 7 / 3 / 5; the FGO_hard rise is the plain-wall divergence) | — | DESCRIPTIVE (final re-run) | same |
| 2(a) conclusion | F1's exploratory benefit over the hard-gated FGO still largely did not replicate (P1 and S2 FAIL); replicated: fewer wrong headings accepted (S1 5/6). Against the UKF the robust FGO now has the lower yaw max (8/10). On plain walls the hard-gated FGO now diverges (§6.6, trace pending), so robust vs hard there compares against a divergent arm | — | CURRENT (wording, ruled D28; restated 2026-10-10) | M: "D28 RULED"; final re-run |
| 2(b) robust closed-loop set, end-wall FGO yaw-error range (r1–r3) vs hard-gated | 1.14 / 1.20 / 2.04 vs 2.36 / 1.07 / 2.48 | deg | DESCRIPTIVE | M: "Plan step 2(b) RESULT" |
| 2(b) cruise yaw-gyro std, robust vs hard-gated | 0.144–0.159 vs 0.196–0.208 (~25% lower; jitter unchanged; cause untested) | deg/s | DESCRIPTIVE | json:p2b_jitter_control.json |

### 15.2 F tests (offline, re-scored in the final re-run; added 2026-10-10)

| Quantity | Value | Unit | Status | Source |
|---|---|---|---|---|
| F1 (k = 2.385): robust FGO better than the hard-gated UKF | **NOT met (lockout tie)** (ruling 8): robust lower yaw max on 6/6 (was 0/6), but lockouts FGO_robust 3 = UKF_hard 3 (was 4 < 6). FGO_hard on the plain-wall bags: yaw max 179.9–180.0° (the divergence, trace pending) | — | CURRENT (final re-run 2026-10-10) | json:f1_test.json |
| F2 hindsight correction (FGO batch vs live) | **MET** (was NOT met): batch off-interval yaw RMS 0.063–0.066° against live 0.32–0.36° on all 3 bags | — | CURRENT (final re-run 2026-10-10) (verdict flip, ruling 4) | json:f2_test.json |
| F3 FGO advantage grows with Δ | **NOT met**, reason changed: the FGO's Δ30 prior-induced lockout is gone (convergence 176–182 s → 0.0–0.1 s); ratio decreasing on 1/3 bags (2/3 needed); at Δ60 both lock out | — | CURRENT (final re-run 2026-10-10) | json:f3_test.json |
| F3b (a) FGO at least as fast / (b) advantage grows | TRUE / FALSE (unchanged); the UKF still diverges numerically at every Δ | — | CURRENT (final re-run 2026-10-10) | json:f3b_test.json |
| F3c (a) / (b) | FALSE / **FALSE** ((b) was TRUE; ratio decreasing on 1/3 bags, was 3/3) | — | CURRENT (final re-run 2026-10-10) (verdict flip, ruling 4) | json:f3c_test.json |

## 16. Experiments T, O, L (2026-10-08) — CURRENT

Pre-registrations and full records: METHODOLOGY "Experiments T, L, O". Figures: `plots/supervisor_2026-10-08/` (fig11–fig15).
All absolute-frame metrics are world frame (T, O) or the first tag's frame (L), with **no alignment**.

### 16.1 T — AprilTag fixes at known positions (`room_tags`, 5 laps of a 6 m square, 3 repeats per condition)

Horizontal RMSE over the lap window, mean of 3 repeats (repeats agree within 8 mm). Source: `eval/results/expT/t_aggregate.json`.

| condition (tags sent; median gap) | EKF3 live | UKF live | FGO live | RTS-UKF (hindsight) | FGO batch (hindsight) |
|---|---|---|---|---|---|
| A: all 8 (4.3 s) | 0.039 m | 0.037 m | **0.020 m** | 0.014 m | **0.011 m** |
| B: corners (10.1 s) | 0.055 m | 0.061 m | **0.026 m** | 0.031 m | **0.015 m** |
| C: 2 diagonal (22.0 s) | 0.074 m | 0.076 m | **0.053 m** | 0.039 m | **0.019 m** |
| D: 1 tag (46.3 s) | 0.096 m | 0.131 m | **0.082 m** (descriptive, n = 3; ruling 7) | 0.109 m | **0.028 m** |

- **(Final re-run 2026-10-10; old table and bullets in the superseded block.) Condition D:** FGO live 0.082 against
  EKF3 live 0.096 is **descriptive only (n = 3)** (ruling 7); no live ordering is claimed.
- **H-T1 (primary) PASS.** The FGO hindsight gain per gap (median) is 0.010 / 0.011 / 0.023 / 0.052 m for A–D,
  strictly increasing. Spearman ρ = +0.30, p = 6e-6, n = 213 gaps.
- **P-T2 FAIL.** The RTS-UKF gain is +0.020 / +0.032 / +0.037 / +0.029 m (all positive now, not increasing; ρ +0.11, p 0.11).
- **P-T3 FAIL.** The live max/min ratio is 1.97 / 2.36 / 1.43 / 1.59 (C now inside the band).
- **P-T4 FAIL.** The batch-FGO vs RTS-UKF ratio is 1.31 / 2.14 / 2.07 / 3.89.
- **EKF3 timeout:** `horiz_pos_abs` inside the gaps is A 1.00, B–D 0.05. EKF3 times out (> 10 s) and fuses the next
  fix ungated from B on.
- **Tag module** (2.26 m): detection 100% of the fully visible tags; central-third position p95 40 mm, yaw p95 0.10°;
  5.6 ms/frame.
- **`VISO_DELAY_MS 15`** (ruled; D2 deviation): the per-fix bound is ≤ 6 mm nominal, ≤ 22 mm at the measured 1.80 m/s
  corner maximum, ≤ 0.06° in yaw.
- **Flow in the post-corner catch-up:** 97.3% of frames valid against 98.7% on the straights; 54 vs 53 features.

### 16.2 O — outdoor → indoor (123 s, GNSS off) → outdoor, 3 flights

Indoor horizontal RMSE across O_r1 / O_r2 / O_r3b. Source: `eval/results/expO/O_*.json`.

| track | indoor RMSE | error at GNSS return | largest step in 10 s after return |
|---|---|---|---|
| EKF3 live | 1.42–1.43 m | 3.53–3.54 m | **4.10 m (reset jump, every flight)** |
| UKF live | 0.77–0.84 m | 2.37–2.51 m | 2.30–2.44 m |
| FGO live | 0.83–0.89 m | 2.50–2.66 m | 2.14–2.27 m |
| RTS-UKF (hindsight) | 0.58–0.60 m (cap-free variant 0.60–0.62 m) | 0.02 m | — |
| **FGO batch (hindsight)** | **0.59 m** (was 0.33 m: WORSENED; attribution PENDING) | 0.02 m | — |

- **H-O1 (primary) PASS 3/3.**
- **H-O2 FAIL:** the live ratio is 1.72–1.84× (was about 2.2×).
- **P-O3 PASS (was FAIL; flip accepted, ruling 5):** batch FGO vs RTS-UKF ratio 1.01–1.02 (capped), 1.02–1.05 (cap-free).
- **WITHDRAWN (ruling 5): "the FGO batch is about 1.9–2× better than the better RTS-UKF".** Reason: the corrected FGO batch
  worsened 0.33 → 0.59 m and now equals the RTS-UKF within 1–5 %. Also no longer holding: "the cap-free RTS-UKF is worse
  (0.97–0.98)" (now 0.60–0.62) and "live ordering UKF < FGO" on O_r1 (now a tie). **The batch worsening is to be explained
  by the attribution study: PENDING.**
- EKF3 switched source set at OFF + 4.3 s and ON + 4.4 s; `posTimeout` was set for 92% of the indoor segment.

### 16.3 L — tags at UNKNOWN positions; keyframe FGO with loop closure (T_A_r1–r3)

Horizontal RMSE in the first tag's frame. Source: `eval/results/expL/T_A_r*_t245.json`.

| mode | live (overall) | hindsight (overall) | live lap 5 ÷ lap 1 |
|---|---|---|---|
| with loop closure | **0.049–0.076 m** | **0.017–0.027 m** | 0.16–0.43 |
| without loop closure | 0.281–0.362 m | 0.221–0.271 m | 3.0–5.0 |

- **V-L: NOT re-scorable** (ruling 6, 2026-10-09: its labels were never recorded and none are made after the fact). The old result (keyframe FGO 4.63 m vs thesis FGO 4.59 m on `dsn_tex_r1`, PASS) was on the old FGO and is not restated.
- **H-L1 (primary), H-L2, H-L3 and P-L4: PASS 3/3** (unchanged in the final re-run; L's result HOLDS, magnitudes moved).
- **Computational cost (DIAGNOSTIC, workstation Python):**
  - LC: median 36–41 ms per update (final re-run).
  - no-LC: median 47–54 ms, p99 1.3–1.7 s (final re-run; graph size identical). Wall time per no-LC job rose from
    1,044–2,996 s to 9,868–11,175 s, from rare steps beyond p99 from about keyframe 3,000–4,000. Cause untraced; results
    unaffected.
  - Cause: the 30 Hz whole-history graph, plus a landmark per pass without loop closure.
  - Deviations: the replays are cut at anchor + 245 s, and hindsight uses iSAM2's full estimate.

## 17. Experiment H (marker-relative holding), S0 + S1 (2026-10-08) — CURRENT

Source: `eval/results/expH/` (`s0a_char.json`, `s0b_check.json`, `s1_r1..3.json`). Full record: METHODOLOGY
"Experiment H".

**S0a (wall tag, forward camera):**
- detection 95.8% of in-view frames, 0 wrong ids;
- horizontal p95: 18 mm at 1.25–1.75 m, 15 mm at 1.75–2.25 m, 24 mm at 2.25–2.8 m;
- yaw p95 0.4–0.7°;
- whole image valid; σ_pos 0.02 m.

**S0b:** `VISO_DELAY_MS` 31 (receipt 31.2 ms, node 31.0 ms).

| S1, EKF3 flying (3 flights) | value |
|---|---|
| hold error mean / max | 8 mm / 16–25 mm (H-H1 PASS) |
| lateral tracking RMSE / max (0.2 m/s setpoint) | 78–90 / 235–251 mm |
| gyro activity in the holds | 0.008 rad/s |

| tag-loss drift (effective, post hoc) | EKF3 (flying) | UKF (shadow) | FGO (shadow) |
|---|---|---|---|
| 5 s hover | 13–27 mm | 11–19 mm | 9–18 mm |
| 15 s hover | 6–25 mm | 5–22 mm | 4–20 mm |
| 30 s hover | 3–11 mm | 4–9 mm | 1–8 mm |
| ~7 s during a move | 7–31 mm | 8–19 mm | 0.5–8 mm |
| re-lock after the first returning fix (effective) | 28–44 ms | 0 ms | 0 ms |
| re-lock as pre-registered (OFF → fused) | 0.16–1.06 s (occluder render lag; P-H6 FAIL as worded) | same | same |

No lockout in any loss (P-H7 PASS). P-H5 PASS (20/20 each estimator; new-only `s1far_r3b` 4/4).

**Final re-run (2026-10-10), ruling 6:** the UKF/FGO shadow columns are restated; EKF3 (flying) is unchanged. The shadows
now drift at EKF3's scale, so the statement is **"there is no gap between the shadow and the flying estimators"**
(it replaces "the S1 → S2/S3 gap closes"). The old shadow values are in the superseded block.

## † Diverging (unaided) FGO results: evidence of divergence, not precise values (ruling 2026-10-08)

Rows marked **†** carry magnitudes from the Python FGO's **runaway** on blank or transition floors (end-of-cruise km
errors, +60 s errors, displacement ratios, onsets, runaway-size bands).
- These are **not bit-reproducible across BLAS builds**. One last-bit rounding difference in `R.T @ v` (OpenBLAS
  `dgemv` vs Eigen) is amplified without bound once the estimate diverges: the C++ port differs by up to 1.97 km on
  `dsn_blank_r1`, yet is bit-identical under NumPy-rounding emulation.
- They are reproducible on this workstation; fresh runs match the stored results.
- **Cite them as evidence that the FGO diverges, with the order of magnitude, not as precise values.**
- Aided (textured) FGO results are bit-reproducible across builds (agreement to 4e-4 mm).
- See METHODOLOGY "RULING (user, 2026-10-08): FGO C++ port". The UKF's diverging values are untested in this respect
  (same caution by analogy).


## Flags: resolved and remaining

**Resolved** (METHODOLOGY "Source-pack flag resolutions", M:L3114-L3198; applied above):
1. **FGO step time (§1):** current ~29 ms median on textured bags; stored medians are
   world-dependent (textured 26.9–29.2, transition 15.1–15.7, blank 4.0–4.3 ms, n = 9 each);
   27 ms is the 2026-08-01 window-sweep result; 101 ms/step is superseded (1.0 s window,
   pre-LM-cap). All DIAGNOSTIC (workstation). CLAUDE item 12 (C:L1861) now agrees.
2. **EKF3 yaw drift with no compass (§2):** current +6.6…+11.1 deg/min, mean ~8.1, n = 9
   `dsn_*`; the window is not stated in the record. "~5 deg/min" is superseded (single-trial
   +5.32 residual).
3. **UKF overshoot (§3):** two definitions, A (% of the constant 9.8) and B (% of the window
   mean of the true bias, ≈ 8.88). Stored values A 222.4% / 336.0%, B 245.3% / ≈ 370.7%. The
   thesis uses B. The "245% → 336%" pair mixes the two and is superseded.
4. **Distance scale (§4):** current n = 9 values EKF3 +5.7…+9.6%, FGO +0.9…+1.1%; the n = 1
   +12.6% / +4.7% are superseded. The scale-cause check ("bounded check 5a") is PENDING and not
   yet defined in the record.
5. **OI-2 commit (§5):** cite `9b0f5d9` (on `master` and `fwd-camera`); `cc588df` is the first
   recording (fwd-camera only), same opening text.

- **`dsn` noise floor — CLOSED (ruling 2026-09-30); values restated 2026-10-10.** Established from the re-flown `dsn_tex` (n = 10 / 9):
  EKF3 SD 0.31 m, FGO SD **1.23 m** [0.83, 2.36] (final re-run; was 0.13, itself already stale after D15's 0.05). It replaces
  textured bands; the existing P4 bands are not re-scored retrospectively.

**Remaining:**
1. **Physical drift denominator ⚑:** 9.8 deg/min (M:L741) against 8.9 deg/min (M:L2718) and
   8.87–8.90 (M:L2077). M:L741-L742 explains the value is a window mean, ≈8.9–9.8 depending
   on the window; §3 records ≈ 8.88 as the true-bias window mean. A window difference, not a
   contradiction.
2. **EKF3 velocity scale on other samples:** "~+6.5% scale" (M:L960) and ~5% on
   `iris_textured` (C:L884) are different samples/quantities, not addressed by §4.
3. **Clock offset drift ⚑:** M:L1194 "−6 to −9 ms early and −52 to −68 ms late" against
   C:L810-L811 "about −7 ms to about −60 ms". Summary rounding, not a conflict.
4. **Static sweep slope ⚑:** the JSON's pooled slope (e.g. `textured_fwdc` 0.624, all y
   positions) is a different quantity from METHODOLOGY's descriptive "slope 1.00–1.01" at y =
   20 and 100 m only (M:L2820-L2822). Do not present them as the same number.
5. **Transition segment breakdown:** NOT IN METHODOLOGY. Present only in
   `eval/results/fwd_transition_segments.json` (commit `938fdb6`).
6. **Phase 4 regression result:** the byte-identical baseline claim is only in the `938fdb6`
   commit message; the snapshot records no regression result. Phase 4 has no results yet.
7. **Phase 1 flow → EKF3 latency baseline:** "median 10.9 ms and p95 42.7 ms" (M:L1594) used
   the single-offset clock; superseded by the linear-map `dsn` values (M:L1752-L1753).

---

## Superseded values (do not cite as current)

| quantity | value | units | status | source | superseded by |
|---|---|---|---|---|---|
| Stage B ATE / RPE (`/ekf/pose`) | RMSE **6.4 mm** / RMSE **4.6 mm** | mm | SUPERSEDED (VOID) | C:L403, C:L405 | `/ekf/pose` was simulator truth (`AHRS_EKF_TYPE=10`), C:L345-L356 |
| Stage C ATE textured / blank | 7.7 mm / 10.0 mm | mm | SUPERSEDED (VOID) | C:L347 | Same reason (C:L486-L491) |
| Stage C RPE textured / blank | 5.4 mm vs blank RMSE 6.5 mm | mm | SUPERSEDED (VOID) | C:L492 | Same reason (C:L493) |
| No-yaw 320 s yaw drift | ±0.03° / ≈0.000 deg/min | deg, deg/min | SUPERSEDED (VOID) | C:L1264 | Truth vs truth (C:L1262-L1279); nomag EKF3 drift re-measured from `XKF1` at M:L884 |
| Textured receipt-stamp table, FGO r1/r2/r3; mean; range | 4.96 / 4.91 / 4.57; 4.81; 0.39 | m | SUPERSEDED | M:L518 | Dejittered baseline, M:L484 |
| Textured receipt-stamp table, UKF r1/r2/r3; mean; range | 18.57 / 10.11 / 22.53; 17.07; 12.42 | m | SUPERSEDED | M:L519 | Dejittered baseline, M:L485 |
| Textured full-window (historical) means EKF3 / FGO / UKF | 4.97 · 5.46 · 19.96 | m | SUPERSEDED | M:L520 | evo -a (cruise), M:L483-L485 |
| Mixed-window table (EKF3 / FGO / UKF means) | (mean 4.97) … (5.46) … (19.96) | m | SUPERSEDED | M:L530-L531 | Pinned cruise window (M:L529-L548) |
| First FGO vs EKF3 (full window) | EKF3 4.79 m vs FGO 5.10 m | m | SUPERSEDED | M:L1097 | evo -a (cruise), EKF3 4.58 vs FGO 4.47 (M:L1099), itself receipt-stamp and pre-correction |
| FGO fixed-anchor ATE | 0.49 m | m | SUPERSEDED (VOID) | M:L1034 | Artefact (M:L1031-L1044); fair anchor (M:L1056-L1131) |
| FGO window sweep ATE at 1.0 / 0.5 / 0.25 s, evo -a (cruise), `dsn_tex_r1` | 4.47 / 4.44 / 3.72 m | m | SUPERSEDED (pre-correction, receipt stamps) | M:L701 | Correction and dejitter; kept only as the evidence that ATE does not depend on the window (M:L699-L704) |
| Pre-correction textured (cruise) UKF / FGO | UKF **14.09 → 17.07**, FGO **4.32 → 4.81** | m | SUPERSEDED | M:L260-L261 | `h_flow` correction, then the dejittered baseline |
| UKF / FGO transition ratio; onset | 0.83 / 0.74; 78 m / 95 m | —; m | SUPERSEDED (pending restatement) | M:L563-L564 | Receipt-stamp; consolidated re-run (M:L505-L511, L1171-L1173) |
| UKF / FGO blank ratio; onset | **1.30** / **1.60**; 50 m / 24 m | —; m | SUPERSEDED (pending restatement) | M:L565-L566 | Same |
| Pre-correction FGO blank ratio (OI-1 evidence) | 0.06 / 0.18 / 0.04 | — | SUPERSEDED (retained as OI-1 evidence) | M:L577 | `h_flow` correction |
| FINDING 2 table, UKF ATE cruise instantaneous / interval-avg | 10.49 / 18.57 | m | SUPERSEDED (pending restatement) | M:L320 | Receipt-stamp; consolidated re-run |
| FINDING 4 `dsn` A / B / C (evo -a cruise) | 10.49 / 16.23 / 18.57 | m | SUPERSEDED (pending restatement) | M:L363-L365 | Same |
| FINDING 4 `ds` A / B / C | 17.43 / 27.13 / **7.88** | m | SUPERSEDED (pending restatement) | M:L380-L382 | Same |
| UKF ramp-tracking | +1.5…+2.1 tex, **−0.5…−0.7 blank** | deg/min/min | SUPERSEDED (pending restatement) | M:L661 | Same |
| UKF consistency Pos E / Pos N / yaw | Pos E 91%, Pos N 65% … yaw 58% | % | SUPERSEDED (pending restatement) | M:L189-L190 | Same |
| Four-estimator yaw clustering (UKF values) | UKF-uncond 9.52 / UKF-gated 12.7 | deg/min | SUPERSEDED | M:L645 | No longer holds for the corrected UKF (M:L644-L648) |
| Smoke test FGO / UKF (receipt stamps) | FGO 4.81 / UKF 19.36 | m | SUPERSEDED | M:L170, M:L172 | Receipt-stamp; the gate verdict (PASS) stands |
| OI-2 receipt → sensor, FGO mean | **4.81 → 4.52** | m | SUPERSEDED (evidence for the dejitter ruling) | M:L1239 | Dejitter only adopted (M:L476-L503) |
| OI-2 decomposition, FGO sensor (dejitter + shift) mean | 4.52 | m | SUPERSEDED (evidence for the dejitter ruling) | M:L1280 | Shift not adopted |
| 400 Hz / 50 Hz Q scaling | ×0.3536, ×0.0442; 0.0053, 0.124, 4.42×10⁻⁵, 8.84×10⁻⁴ | — | SUPERSEDED | C:L1171-L1174 | Predict at 0.0125 s, NSE unchanged (C:L521-L554) |
| IMU bridge rate (old) | 20.00 ms → 50.0 Hz achieved | ms, Hz | SUPERSEDED | C(d89a902):L1095 | 333.27 Hz (C:L564); CLAUDE rewritten, C:L1022-L1026 |
| 50 Hz aliasing artefact peak | "14.84 Hz peak" | Hz | SUPERSEDED | C:L581 | Real tone 34.99 Hz (C:L578) |
| 50 Hz aliased energy | 0.154 m/s² | m/s² | SUPERSEDED | C:L591 | 333 Hz: 0.018 m/s² (C:L592) |
| VIBE-based aliasing magnitude | 0.25 m/s² RMS above Nyquist | m/s² | SUPERSEDED | C:L599 | Direct 25–50 Hz figure (C:L597-L612) |
| Phase 1 single-offset latency, `dsn_tex` baseline | median 10.9 ms and p95 42.7 ms | ms | SUPERSEDED | M:L1594 | Linear clock map (M:L1752-L1753) |
| Phase 1 single-offset limits | ≤ 23.4 / ≤ 55.2 ms | ms | SUPERSEDED | M:L1774 | ≤ 28.1 / ≤ 36.7 (M:L1776) |
| Phase 1 single-offset `p1_fwd_tex` latency | median 19.8, p95 51.5 | ms | SUPERSEDED | M:L1598 | 20.7 / 31.5 (M:L1757) |
| Transition medians (single offset) | up to 32.0 ms | ms | SUPERSEDED | M:L1599 | Linear map (M:L1207-L1211) |
| IMU ">1.5× gap" band | 18.4–18.7% | % | SUPERSEDED | M:L1587 | Mean-gap check plus p99 gap (M:L1657-L1663) |
| RTF gate | RTF ≥ 0.92 | — | SUPERSEDED | M:L1432 | Revised Phase 1 criterion (M:L1672-L1713) |
| Phase 1 `_fwd` worlds (revised criterion) | ALL THREE fwd worlds PASS | — | SUPERSEDED (recorded) | M:L1715 | Ceiling worlds; sky visible (M:L2342-L2349) |
| Phase 1 `_fwd` P4 (tex / trans / blank), EKF3 | 4.07; ratio 0.56, onset 101 m; ratio 0.21, onset 20 m | m; —, m | SUPERSEDED (recorded) | M:L1731 | Same |
| Phase 1 `_fwd` P4, FGO | 4.55; ratio 0.71, onset 94 m; ratio 1.58, onset 24 m | m; —, m | SUPERSEDED (recorded) | M:L1732 | Same |
| `fwd_*` flown | All nine … completed first time | — | SUPERSEDED (recorded) | M:L1869 | Same |
| `fwd_*` primary: P1 and P3 / P4 | P1 and P3 pass in all nine. P4 passes in eight. | — | SUPERSEDED (recorded) | M:L2133 | Same |
| Phase 2 `fwd_*` P4 textured EKF3 / FGO | 4.37 / **5.158 (> 5.14)**; 4.15 / 4.71; 4.41 / 4.53 | m | SUPERSEDED (recorded; `fwd_tex_r1` miss kept) | M:L1886-L1888 | Same |
| Phase 2 `fwd_*` UKF textured (diagnostic) | 42.73 / 7.67 / 9.31 | m | SUPERSEDED (recorded) | M:L1956 | Same |
| Plain-wall Phase 1 | 3/3 complete; all primary pass | — | SUPERSEDED (recorded) | M:L2250 | Same |
| Plain-wall Phase 1 P4 EKF3 / FGO | 4.46 … 4.69 | m | SUPERSEDED (recorded) | M:L2265-L2266 | Same |
| FGO batch timing (1.0 s window, pre-LM-cap) | **101 ms/step median, p99 167 ms** | ms | SUPERSEDED | M:L1124 | Post-fix 0.25 s figures (M: "RULINGS … after Phase 4" §3) |
| PHYS_DRIFT as a constant | the constant 9.8 (a window mean) | deg/min | SUPERSEDED | M:L267 | Triangle-wave `sitl_gyro_drift(t)` (M:L737-L746) |
| Old corridor-world feature counts (Gazebo-level check) | ~126-183 … ~15-24 | — | SUPERSEDED | C(d89a902):L164 | Fixed worlds' verification (C:L1802-L1806) |
| EKF3 yaw drift with no compass, early figure | ~5 deg/min | deg/min | SUPERSEDED | M:L871 | n = 9 `dsn_*` value +6.6…+11.1, mean ~8.1 (M:L3142); origin is the single-trial residual +5.32 on `nomag_corridor_baseline` (M:L3146-L3148) |
| UKF overshoot pair in the sign-flip paragraphs | 245% → 336% | % | SUPERSEDED (mixed denominators) | M:L228 | 245 is definition B, 336 is A; consistent pairs A 222% → 336%, B 245% → ~371% (M:L3163-L3164) |
| EKF3 / FGO velocity scale, `dsn_tex_r1` (n = 1) | `0.556 m/s` (+12.6 %) … +4.7 % | % | SUPERSEDED | M:L1105-L1106 | n = 9 distance scale EKF3 +5.7…+9.6%, FGO +0.9…+1.1% (M:L3170-L3177); the n = 1 figure was speed-magnitude based and pre-correction |
| Heading-driven share (old window, aiding onset to end of log) | ~74% | % | SUPERSEDED | M:L1012 | 69% on the pinned cruise window (M: "Heading share restated (2026-09-29)") |
| Residual share (old window) | ~26% (~0.05 m/s, ~16 m) | % | SUPERSEDED | M:L1014-L1015 | 31% on the pinned cruise window |

### Former sections 6–9 (SUPERSEDED by the consolidated re-run, 2026-09-29; kept verbatim, not edited)

## 6. Baseline results

##### 6.1 Textured, evo -a (cruise), current (dejittered) baseline

| quantity | value | units | status | source |
|---|---|---|---|---|
| EKF3 r1 / r2 / r3 | 4.58 / 3.55 / 5.84 | m | CURRENT | M:L483 |
| EKF3 mean / range | 4.66 / 2.29 | m | CURRENT | M:L483 |
| FGO (0.25 s) r1 / r2 / r3 | 4.63 / 4.74 / 4.57 | m | CURRENT | M:L484 |
| FGO mean / range | 4.65 / 0.17 | m | CURRENT | M:L484 |
| UKF (gated) r1 / r2 / r3 | 16.98 / 9.96 / 20.71 | m | CURRENT | M:L485 |
| UKF mean / range | 15.88 / 10.75 | m | CURRENT | M:L485 |
| Cross-check (JSON), EKF3 r1 | 4.575016 | m | CURRENT | json:dsn_dejitter_baseline.json:trials.dsn_tex_r1.est.EKF3.ate_a_cruise.+0.00 |
| Cross-check (JSON), UKF r1 | 16.977329 | m | CURRENT | json:dsn_dejitter_baseline.json:trials.dsn_tex_r1.est.UKF.ate_a_cruise.+0.00 |
| UKF vs EKF3/FGO factor | ~3.4× worse | — | CURRENT | M:L490 |

##### 6.2 Transition and blank failure metrics (cruise), EKF3 (current)

| quantity | value | units | status | source |
|---|---|---|---|---|
| EKF3 transition \|disp\|/true | 0.57 | — | CURRENT | M:L563 |
| EKF3 transition onset (true y) | 102 m | m | CURRENT | M:L564 |
| EKF3 blank \|disp\|/true | 0.20 | — | CURRENT | M:L565 |
| EKF3 blank onset (true y) | 18 m | m | CURRENT | M:L566 |
| EKF3 blank stop distance | ~30 m | m | CURRENT | M:L570 |
| EKF3 textured displacement ratio (smoke test and `dsn_tex`) | 1.06 | — | CURRENT | M:L175 |

UKF/FGO failure metrics on transition and blank are receipt-stamp values, pending the
consolidated re-run. They are in the superseded section. The dejittered values exist in
`json:dsn_dejitter_baseline.json` but are not interpreted in METHODOLOGY (M:L510-L511).
The Phase 2 FGO bands (section 7) were derived from them.

##### 6.3 Other current estimator results (EKF3 or estimator-independent)

| quantity | value | units | status | source |
|---|---|---|---|---|
| EKF3 `XKF1.Yaw` drift, n = 9 `dsn_*` (window not stated in the record) | +6.6…+11.1 deg/min, mean ~8.1 | deg/min | CURRENT | M:L3142-L3145 |
| EKF3 share of bias corrected | 14–33% | % | CURRENT | M:L884 |
| EKF3 east-velocity bias, `dsn_tex_r3` | +0.194 m/s | m/s | CURRENT | M:L995 |
| Heading-driven share (pinned cruise window, `dsn_tex_r3`) | **68.9%** (0.150 of 0.218 m/s) | % | CURRENT (EKF3; restate after correction (i)) | eval/results/heading_share_restated.json; M: "Heading share restated (2026-09-29)" |
| Heading share, `dsn_tex_r1` / `r2` (context) | 54.9% / 60.7% | % | CURRENT (context, n=3 span 55–69%) | same |
| Geometric slope `errVE vs spd·sin(yawErr)` | +1.10 | — | CURRENT | M:L1007 |
| Residual share (pinned cruise window, `dsn_tex_r3`) | 31.1% (0.068 m/s, 20.5 m) | % | CURRENT (restate after (i)) | same |
| FINDING 1 lateral residual, EKF3: roll-rate corr / slope / std | −0.09 / −0.15 / 0.48 | — | CURRENT | M:L293 |
| FINDING 1, `h_flow` (instantaneous ω) | −0.95 / −2.09 / 0.60 | — | CURRENT | M:L294 |
| Interval-averaged ω residual slope / std | −2.09 → −1.24 (std 0.60 → 0.40) | — | CURRENT | M:L315 |
| Flow residual partition (single update) | velocity 69% / yaw 31% | % | CURRENT | M:L974-L975 |
| Gyro-z ramp-tracking, EKF3 | 0.1–0.3 | deg/min/min | CURRENT | M:L659 |
| Filter consistency, EKF3 Pos E outside ±3σ | 39% | % | CURRENT | M:L185 |
| Filter consistency, EKF3 Vel E / yaw | 16% / 10% | % | CURRENT | M:L187 |
| Noise floor `ds_*` (compass-active, apparatus): within-condition ATE range | 2.81–10.90 m | m | CURRENT (`ds_*` only) | M:L800 |
| Same: textured vs blank mean ATE | 17.8 m vs … 85.8 m | m | CURRENT (`ds_*` only) | M:L802 |
| Same: yaw reproducibility at 300 s | 0.263° | deg | CURRENT (`ds_*` only) | M:L807 |
| Same: transition PN stop | y = 81.7 m (range 0.2 m) | m | CURRENT (`ds_*` only) | M:L814 |
| Vendor verify flight along-track PN | 154.04 m | m | DIAGNOSTIC | M:L846 |
| Flow velocity-axis error growth | ~+7.8% at 0.25 m/s to ~+12.5% at 1.0 m/s | % | CURRENT | C:L1871 |
| Flow validation vs theory | 137.13 px/s vs 137.1 px/s predicted | px/s | CURRENT | P:L440-L441 |

##### 6.4 Smoke test `p0_smoke_tex` (EKF3) and forward-camera datasets (current)

| quantity | value | units | status | source |
|---|---|---|---|---|
| Smoke test EKF3 evo -a (cruise) | 5.74 | m | DIAGNOSTIC (gate record) | M:L171 |
| Ceiling `fwdc` textured EKF3 r1 / r2 / r3 | 3.44 / 3.98 / 3.99 | m | CURRENT | M:L2533 |
| Ceiling `fwdc` textured FGO r1 / r2 / r3 | 4.68 / 4.42 / 4.97 | m | CURRENT | M:L2533 |
| Ceiling `fwdplainc` textured EKF3 r1 / r2 / r3 | 3.88 / 4.26 / 4.15 | m | CURRENT | M:L2534 |
| Ceiling `fwdplainc` textured FGO r1 / r2 / r3 | 4.67 / 4.82 / 4.64 | m | CURRENT | M:L2534 |
| Ceiling transition EKF3 ratio / onset | 0.547–0.564, onset 100–101 m | —, m | CURRENT | M:L2536 |
| Ceiling transition FGO ratio / onset †| 0.691–0.725, onset 94.5–95.2 m | —, m | CURRENT | M:L2536-L2537 |
| Ceiling blank EKF3 ratio / onset | 0.181–0.223, onset 17–20 m | —, m | CURRENT | M:L2538 |
| Ceiling blank FGO ratio / onset †| 1.506–1.529, onset 34–38 m | —, m | CURRENT | M:L2538-L2539 |
| Ceiling UKF textured (`fwdc` / `fwdplainc`) | `fwdc` 14.6 / 20.9 / 7.3, `fwdplainc` 15.8 / 10.0 / 8.7 | m | DIAGNOSTIC | M:L2543 |
| Ceiling P2 latency p95 max | at most 36.4 ms | ms | DIAGNOSTIC | M:L2541 |
| Phase 1c P4 EKF3 (fwdc tex / fwdplainc tex) | 3.92 / 4.49 | m | CURRENT | M:L2413 |
| Phase 1c P4 FGO (fwdc tex / fwdplainc tex) | 4.60 / 4.53 | m | CURRENT | M:L2414 |
| `p1c_fwdc_trans` after the extended rule: FGO ratio / onset †| 0.700 … 94.9 m | —, m | CURRENT | M:L2488-L2489 |

##### 6.5 Resolved definitions and scale (flag resolutions §3, §4)

| quantity | value | units | status | source |
|---|---|---|---|---|
| UKF gyro-z overshoot, definition A ("% of 9.8": \|mean bias\| ÷ constant 9.8 deg/min), `dsn_tex_r1` baseline / sign-flip | **222.4%** … **336.0%** | % | DIAGNOSTIC (definition record; pre-correction runs) | M:L3152-L3157 |
| UKF gyro-z overshoot, definition B (÷ window mean of the true bias ≈ 8.88 deg/min), baseline / sign-flip | **245.3%** … **≈ 370.7%** | % | DIAGNOSTIC (definition record; pre-correction runs) | M:L3158-L3162 |
| Definition used by the thesis | definition B | — | CURRENT | M:L3165 |
| Consistent pairs | A: 222% → 336% … B: 245% → ~371% | % | CURRENT | M:L3164 |
| Distance scale, EKF3 (n = 9, derived, Part C item 9 row A) | +5.7…+9.6% | % | CURRENT | M:L3170-L3171 |
| Distance scale, FGO (n = 9, same basis) | +0.9…+1.1% | % | CURRENT | M:L3172 |
| Scale basis | path-length ratio … 20 s resampling | — | CURRENT | M:L3173 |
| Corroborating `disp_ratio`, 12 textured bags | EKF3 1.04–1.06, FGO 0.98–0.99 | — | CURRENT | M:L3175 |
| Scale-cause check ("bounded check 5a") | PENDING; not yet defined in the record | — | CURRENT (open) | M:L3178-L3179 |

#### 7. Pre-registered bands

| quantity | value | units | status | source |
|---|---|---|---|---|
| Smoke test band FGO / EKF3 / UKF | [4.18, 5.35] / [1.26, 8.13] / [0, 34.95] | m | CURRENT (pre-registered) | M:L145-L147 |
| P1 flow/LiDAR timing | 30.30 Hz ± 0.1%; ≤ 0.5% of gaps above 1.5 periods | — | CURRENT (pre-registered) | M:L1693 |
| P1 IMU timing | mean gap 3.0005 ± 0.003 ms … p99 gap ≤ 10 ms | ms | CURRENT (pre-registered) | M:L1694 |
| P2 latency | ≤ same-world `dsn` mean + **12.5 ms** | ms | DIAGNOSTIC (pre-registered; diagnostic from Phase 2) | M:L1695 |
| P3 inlier mean | ±0.01 of the `dsn` mean | — | CURRENT (pre-registered) | M:L1696 |
| P3 % below 0.5 / features / `flow_y_raw` | within ±3 pp; features ±5%; `flow_y_raw` ±2% … or ±5 px/s (blank) | — | CURRENT (pre-registered) | M:L1696 |
| P3 GT lateral | \|x\| ≤ 0.05 m | m | CURRENT (pre-registered) | M:L1696 |
| P4 EKF3 textured | [1.26, 8.13] | m | CURRENT (pre-registered) | M:L1850 |
| P4 EKF3 transition ratio / onset | [0.51, 0.63], onset [96, 108] m | —, m | CURRENT (pre-registered) | M:L1850 |
| P4 EKF3 blank ratio / onset | [0.12, 0.27], onset [13, 24] m | —, m | CURRENT (pre-registered) | M:L1850 |
| P4 FGO textured (dejittered) | [4.17, 5.14] | m | CURRENT (pre-registered) | M:L1851 |
| P4 FGO textured band basis | 4.57–4.74 ± max(range 0.17, **0.40 m**) | m | CURRENT (pre-registered) | M:L1851 |
| P4 FGO transition †| ratio 0.72–0.73 ± 0.05 → [0.67, 0.78]; onset 95–96 ± 5 → [90, 101] m | —, m | CURRENT (pre-registered) | M:L1851 |
| P4 FGO blank †| ratio 1.50–1.55 ± 0.05 → [1.45, 1.60]; onset 33–37 ± 5 → [28, 42] m | —, m | CURRENT (pre-registered) | M:L1851 |
| `dsn` P3 baseline, textured inlier | 0.9729–0.9741 | — | CURRENT | M:L1445 |
| `dsn` P3 baseline, blank inlier | 0.3130–0.3153 | — | CURRENT | M:L1446 |
| `dsn` `flow_y_raw` mean, textured | 136.45 | px/s | CURRENT | M:L1516 |
| `dsn` `flow_y_raw` mean, transition (band) | 71.43 ± 2% (≤ 72.86) | px/s | CURRENT | M:L2412 |
| Transition `flow_y_raw` historical spread | 70.52–72.29 | px/s | CURRENT | M:L2464 |
| Ruling 1 decision rule (`fwdplainc_trans`) | 2 or more of the 3 | — | CURRENT (pre-registered) | M:L2456 |

#### 8. Dataset pass/fail counts

| quantity | value | units | status | source |
|---|---|---|---|---|
| `dsn_*` comparison batch | 3 corridor worlds × 3 repeats | — | CURRENT | M:L856 |
| Phase 1c ceiling checks | five of six pass every primary criterion | — | CURRENT | M:L2492 |
| Render check R (checks: pre-flight / in flight) | 18 frames … 42 frames | — | CURRENT | M:L2418-L2419 |
| Ceiling datasets flown | 18/18 trials completed first time | — | CURRENT | M:L2504 |
| Extended IMU rule on 18 bags | 15 bags are `ok` and 3 are `trim` | — | CURRENT | M:L2513 |
| `fwdplainc_*` primary | 9/9 pass | — | CURRENT | M:L2526 |
| `fwdc_*` primary | 8/9 pass | — | CURRENT | M:L2527 |
| Render check R on datasets | PASS on all 18 | — | CURRENT | M:L2522 |
| Ceiling transition flights above `flow_y_raw` band | 2 of 8 … 0 of 8 without a ceiling | — | CURRENT | M:L2567-L2568 |
| Phase 3 calibration heading / yaw rate | Heading: 5/6 / Yaw rate: 3/6 | — | CURRENT | M:L2756-L2758 |
| Phase 3 validation heading | 15/18 | — | CURRENT | M:L2825 |
| Phase 3 validation yaw rate `fwdc` / `fwdplainc` | 9/9 / 0/9 | — | CURRENT | M:L2789-L2790 |
| Static heading response bar | 1/6 worlds pass | — | CURRENT | M:L2816 |

#### 9. Forward-camera measurement: frozen parameters and results

| quantity | value | units | status | source |
|---|---|---|---|---|
| LSD minimum segment length | 15 px | px | CURRENT | M:L2634 |
| Segment angle exclusion | within 5° of horizontal or vertical | deg | CURRENT | M:L2635 |
| RANSAC iterations | 300 | — | CURRENT | M:L2636 |
| Prior (i) | \|ψ\| < 30° | deg | CURRENT | M:L2642 |
| Prior (ii) | within ±5° of the horizon row | deg | CURRENT | M:L2644 |
| Yaw-rate corners | up to 100 | — | CURRENT | M:L2662 |
| Frozen inlier tolerance | 0.5° | deg | CURRENT | M:L2737 |
| Frozen S_MIN | 200 px | px | CURRENT | M:L2737 |
| Frozen yaw-rate box half-size | 80 px | px | CURRENT | M:L2737 |
| Frozen N_MIN | 5 | — | CURRENT | M:L2738 |
| Cross-check (JSON) frozen set | inlier_deg 0.5, s_min 200, box_half_px 80, n_min 5 | — | CURRENT | json:fwd_calibration.json:frozen |
| Calibration σ_ψ `fwdc` / `fwdplainc` | 0.097° / 0.026° | deg | CURRENT | M:L2742-L2743 |
| Calibration σ_ω `fwdc` | 0.106 deg/s | deg/s | CURRENT | M:L2742 |
| Calibration σ_ω `fwdplainc` (not used: failed validation) | 2.07 deg/s | deg/s | DIAGNOSTIC | M:L2743 |
| Accuracy bar, heading | ≥ 70% / ≤ 0.5° / ≤ 1.0° / ≤ 5% (\|error\| > 3°) | — | CURRENT (pre-registered) | M:L2711 |
| Accuracy bar, yaw rate | ≥ 70% / ≤ 0.05 deg/s / ≤ 1.0 deg/s / ≤ 5% (\|error\| > 3 deg/s) | — | CURRENT (pre-registered) | M:L2712 |
| Static sweep bar | slope 1 ± 0.05, and every \|residual\| ≤ 0.5° | — | CURRENT (pre-registered) | M:L2703-L2704 |
| Static sweep offsets | {−10, −5, −2, 0, +2, +5, +10}° | deg | CURRENT (pre-registered) | M:L2703 |
| Validation heading `fwdc` tex (avail / bias / sd / robust σ / outliers) | 96.8% / −0.006° / 0.20° / 0.13° / 0.09% | — | CURRENT | M:L2778 |
| Validation heading `fwdc` trans | 96.8% / −0.014° / 0.13° / 0.09° / 0.00% | — | CURRENT | M:L2779 |
| Validation heading `fwdc` blank | 96.8% / −0.018° / 0.11° / 0.08° / 0.00% | — | CURRENT | M:L2780 |
| Validation heading `fwdplainc` tex | 60.0% / +0.206° / 0.68° / 0.33° / 11.9% | — | CURRENT | M:L2781 |
| Validation heading `fwdplainc` trans | 87.6% / +0.035° / 0.39° / 0.02° / 3.0% | — | CURRENT | M:L2782 |
| Validation heading `fwdplainc` blank | 95.5% / −0.027° / 0.12° / 0.01° / 0.14% | — | CURRENT | M:L2783 |
| Validation yaw rate `fwdc` (avail) | 99.9 / 97.4 / 97.4% | % | CURRENT | M:L2789 |
| Validation yaw rate `fwdc` (bias) | +0.006 / +0.009 / +0.002 deg/s | deg/s | CURRENT | M:L2789 |
| Validation yaw rate `fwdc` (noise sd) | 0.19 / 0.21 / 0.13 deg/s | deg/s | CURRENT | M:L2789 |
| Validation yaw rate `fwdplainc` (avail) | 89.7 / 86.1 / 87.5% | % | CURRENT | M:L2790 |
| Validation yaw rate `fwdplainc` (noise sd / outliers) | 1.48 / 1.43 / 1.36 deg/s … 15.4 / 15.7 / 23.7% | — | CURRENT | M:L2790 |
| End-wall heading availability (GT y > 145 m) | `fwdc`: 14–20%; `fwdplainc`: 0–10% | % | CURRENT | M:L2796-L2797 |
| Static sweep, near end wall example | a true +10° is reported as −17.2° | deg | CURRENT | M:L2818 |
| Static sweep descriptive, y = 20 and 100 m | slope 1.00–1.01 and max \|residual\| ≤ 0.32° | — | DIAGNOSTIC | M:L2821-L2822 |
| Static sweep, pooled slope `textured_fwdc` (all y, JSON) ⚑ | 0.6240513705473866 | — | DIAGNOSTIC | json:fwd_yaw_sweep.json:textured_fwdc.slope |
| Static sweep, pooled slope `blank_fwdc` (JSON) | 1.0071911784543726 | — | DIAGNOSTIC | json:fwd_yaw_sweep.json:blank_fwdc.slope |
| Transition segment breakdown, `fwdc_trans_r{1,2,3}` | ψ and ω `pass` true in both halves | — | DIAGNOSTIC | json:fwd_transition_segments.json:fwdc_trans_r*/{checker_y<80,blank_y>80}.{psi,omega}.pass |
| Transition segment breakdown, `fwdplainc_trans_r{1,2,3}` | ψ pass false (checker y<80), true (blank y>80); ω pass false in both | — | DIAGNOSTIC | json:fwd_transition_segments.json:fwdplainc_trans_r*/…pass |

### Superseded by D10 (2026-09-30): Phase 4 / 5b FGO yaw values computed from typo'd FGO TUM quaternions
- `eval/results_pre_d10/phase4_{fwdc,fwdplainc}_arms.json` and `phase5b_consistency.json` are SUPERSEDED by
  the restated `eval/results/` files. Every changed value, old → new, is in `eval/results/d10_restatement.json`.
  The largest change is 0.17° (≤ 0.57%). No row of this file changes at its printed precision.


### Superseded by D27 (2026-10-01): offline-UKF values with 1.2× per-second IMU process noise (correction (ii) to D27); kept verbatim (cell separators shown as ¦)

| row (verbatim) |
|---|
|  UKF predict dt ¦ 0.0125 s ¦ s ¦ CURRENT ¦ C:L546  |
|  NSE scale factor UKF vs EKF3 ¦ exactly 1 ¦ — ¦ CURRENT ¦ C:L548  |
|  UKF r1 / r2 / r3 ¦ 4.31 / 2.29 / 5.93 ¦ m ¦ CURRENT (D15; the r1 instability was the take-off kick) ¦ same  |
|  UKF r1–r9 (usable): median / range / SD ¦ 5.39 / 1.87–5.93 / 1.51 ¦ m ¦ CURRENT (D15) ¦ json:rerun_dsn_evo.json, dsn_extra_evo.json  |
|  UKF cruise yaw drift, `dsn_tex` r1–r9 / transition (ENU; all westward) ¦ −7.8, −3.1, −11.1, −10.2, −9.8, −1.9, −10.0, −10.4, −10.1 / −10.4, −13.3, −10.3 ¦ deg/min ¦ CURRENT (D15) ¦ json:d15_drift.json  |
|  UKF take-off yaw change, `dsn_tex` r1–r9 ¦ \¦Δ\¦ ≤ 0.76° (was −17.0 … +5.4°) ¦ deg ¦ CURRENT (D15) ¦ json:d15_kick.json  |
|  UKF baseline position error magnitude at +10 / +30 / +60 s after loss, blank (n = 11: `dsn`, `fwdc`, `fwdplainc`, `p1c`) ¦ 6.4–9.2 / 20.5–34.1 / 96–313 ¦ m ¦ CURRENT ¦ json:blank_behaviour.json  |
|  UKF / FGO baseline error at the end of cruise, blank ¦ 10–63 / 22–31 ¦ km ¦ CURRENT (D15) ¦ same  |
|  UKF / FGO baseline error at +60 s after loss, transition (n = 11) ¦ 83–315 / 939–1,049 ¦ m ¦ CURRENT (D15) ¦ json:blank_behaviour.json  |
|  Heading arms (n = 6, `fwdc`/`fwdplainc`), blank, +60 s: UKF / FGO ¦ 61–176 / 299–904 ¦ m ¦ CURRENT (D15; the heading does not bound position without flow) ¦ json:blank_behaviour.json  |
|  `fwdc` textured UKF r1 / r2 / r3 ¦ 5.18 / 2.47 / 5.18 ¦ m ¦ DIAGNOSTIC (D15) ¦ same  |
|  `fwdplainc` textured UKF r1 / r2 / r3 ¦ 5.22 / 11.89 / 11.54 ¦ m ¦ DIAGNOSTIC (D15; r2, r3 residual take-off kick) ¦ same  |
|  `fwdc` UKF +heading r1 / r2 / r3 ¦ 0.61 / 0.62 / 0.62 ¦ m ¦ CURRENT ¦ json:phase4_fwdc_arms.json  |
|  `fwdplainc` UKF +heading r1 / r2 / r3 ¦ 0.65 / 1.01 / 0.95 ¦ m ¦ CURRENT ¦ json:phase4_fwdplainc_arms.json  |
|  `fwdplainc` textured UKF +heading mean position NEES, mean of r1–r3 ¦ 5.10 (0.36 / 5.50 / 9.45) (D15; was 5.08) ¦ — ¦ DIAGNOSTIC ¦ json:phase5b_consistency.json  |

### Superseded by D15 (2026-09-30): UKF/FGO values before EKF3's ground-proximity flow rule
- All pre-D15 result files are kept in `eval/results_pre_d15/`, and every trial's pre-D15 UKF/FGO outputs in
  `~/thesis_data/pre_d15_trials/`. Old → new for each restated row is in METHODOLOGY "D15 RESULTS".

| quantity | value | units | status | source | superseded by |
|---|---|---|---|---|---|
| FGO `dsn_tex` r1 / r2 / r3; mean / range | 4.62 / 4.30 / 4.64; 4.52 / 0.34 | m | SUPERSEDED | results_pre_d15/rerun_dsn_evo.json | D15 rule |
| UKF `dsn_tex` r1 / r2 / r3 | 17.45 / 2.28 / 4.30 | m | SUPERSEDED | same | D15 rule (the r1 instability was the take-off kick) |
| Confirmatory test CI; noise floor FGO / d | [−1.20, −0.19]; 0.13 [0.09, 0.24] / 0.39 [0.26, 0.75] | m | SUPERSEDED (verdict unchanged) | results_pre_d15/dsn_paired_test.json | D15 rule |
| "UKF poor in most textured flights": ≤ 4.3 m on 3 of 9, 13–36 m on 6 of 9; median 17.5, range 2.3–35.9 | — | m | SUPERSEDED (wording) | same | D15: a take-off artefact |
| UKF take-off yaw change, `dsn_tex` r1–r9 | −9.2, +0.4, +5.1, −17.0, +5.4, −10.7, −11.5, −5.4, −9.3 | deg | SUPERSEDED | METHODOLOGY P2 table | D15 |
| Blank behaviour: UKF / FGO transition +60 s; end-of-cruise blank; FGO blank +60 s; FGO heading blank +60 s | 67–378 / 895–1,080; 9–63 / 23–32 km; 171–574; 299–898 | m | SUPERSEDED | results_pre_d15/blank_behaviour.json | D15 |
| `fwdc` UKF r1 / r2 / r3; `fwdplainc` UKF; `fwdplainc` FGO r2 / r3; `p1c_fwdc` FGO | 9.88 / 2.47 / 20.46; 14.23 / 3.40 / 24.93; 4.47 / 4.63; 4.60 | m | SUPERSEDED | results_pre_d15/rerun_*_evo.json | D15 |
| `fwdplainc` UKF +heading NEES mean | 5.08 (0.38 / 5.43 / 9.44) | — | SUPERSEDED | results_pre_d15/phase5b_consistency.json | D15 (5.10) |
| P4 FGO textured band | [3.898, 5.042] | m | SUPERSEDED | results_pre_d15/rerun_p4_bands.json | D15 |
| `fwdc` primary | 5/9 | — | SUPERSEDED | results_pre_d15/rerun_fwdc_score.json | D15 (6/9) |

### Superseded by the final consolidated re-run (2026-10-10): rows replaced under rulings 2–9 and 11; kept verbatim (cell separators shown as ¦)

Old UKF/FGO values computed with the pre-correction UKF (no bias-corrected derotation; jitter always on) and the FGO
with the mis-specified noise model (`biasAccOmegaInt` ≠ 0, no variance-gated yaw cap). Old → new for every row:
`docs/thesis/final_restatement_draft.md`.

| section | row (verbatim) |
|---|---|
| §2 | ¦ Max Δ evo -a (cruise) under clock shift, textured EKF3 / UKF / FGO ¦ 0.002–0.009 / 0.007–0.009 / 0.014–0.015 ¦ m ¦ CURRENT ¦ M:L93 ¦ |
| §2 | ¦ Same, transition ¦ 0.085–0.103 / 0.004–0.016 / 0.006–0.007 ¦ m ¦ CURRENT ¦ M:L94 ¦ |
| §2 | ¦ Same, blank ¦ 0.001–0.013 / 0.002–0.009 / 0.005–0.006 ¦ m ¦ CURRENT ¦ M:L95 ¦ |
| §5 | ¦ 0.20 m/s: max Δ evo -a (cruise), textured EKF3 / UKF / FGO ¦ 0.005 / 0.038 / 0.009 ¦ m ¦ CURRENT ¦ M:L76 ¦ |
| §5 | ¦ 0.40 m/s: same ¦ 0.008 / 0.043 / 0.011 ¦ m ¦ CURRENT ¦ M:L77 ¦ |
| §6.1 | ¦ FGO (0.25 s) r1 / r2 / r3 ¦ 4.59 / 4.72 / 4.60 ¦ m ¦ CURRENT (D15) ¦ same ¦ |
| §6.1 | ¦ FGO mean / range ¦ 4.64 / 0.13 ¦ m ¦ CURRENT (D15) ¦ same ¦ |
| §6.1 | ¦ UKF r1 / r2 / r3 ¦ 4.23 / 2.14 / 5.38 ¦ m ¦ CURRENT (D15 + D27) ¦ same ¦ |
| §6.1 | ¦ EKF3 vs FGO (claim wording) ¦ now CONFIRMED by the pre-registered test (row below); the earlier interim wording "EKF3 lower on all three repeats" is superseded ¦ — ¦ CURRENT (wording) ¦ M: "Rulings (user, 2026-09-29) on the re-run results" ¦ |
| §6.1 | ¦ **Confirmatory test, EKF3 vs FGO** (r4–r10, pre-registered; r10 unusable for FGO) ¦ **EKF3 lower** (holds after D15): d < 0 on 6/7, mean d −0.69 m, 95% CI [−1.16, −0.21] ¦ m ¦ CURRENT (D15) ¦ json:dsn_paired_test.json ¦ |
| §6.1 | ¦ Noise floor SD (re-flown `dsn_tex`): EKF3 (n = 10) / FGO (n = 9) / d (n = 9) ¦ 0.31 [0.22, 0.57] / 0.05 [0.03, 0.10] / 0.37 [0.25, 0.71] ¦ m ¦ CURRENT (D15) ¦ same ¦ |
| §6.1 | ¦ **Claim wording (D15, supersedes "the UKF is poor in most textured flights")** ¦ with EKF3's ground-proximity flow rule the UKF is stable on all 9 usable `dsn_tex` flights (1.71–5.96 m, median 5.34 after D27; above EKF3 4.10 and FGO 4.61, descriptive) and ≤ 5.93 m on 14 of 17 textured flights overall; 3 of 17 (p1c_fwdc, fwdplainc r2, r3) are 7.7–11.9 m with a residual post-detection take-off kick (−1.4 … −4.4°) that EKF3 does not show (a UKF flow→yaw property) ¦ m ¦ CURRENT (wording) ¦ M: "D15 RESULTS" ¦ |
| §6.1 | ¦ UKF r1–r9 (usable): median / range / SD ¦ 5.34 / 1.71–5.96 / 1.55 ¦ m ¦ CURRENT (D15 + D27) ¦ json:rerun_dsn_evo.json, dsn_extra_evo.json ¦ |
| §6.1 | ¦ UKF cruise yaw drift, `dsn_tex` r1–r9 / transition (ENU; all westward) ¦ −7.6, −2.7, −10.0, −10.1, −9.7, −1.3, −9.9, −11.2, −10.0 / −10.3, −13.0, −10.2 ¦ deg/min ¦ CURRENT (D15 + D27) ¦ json:d15_drift.json ¦ |
| §6.1 | ¦ UKF take-off yaw change, `dsn_tex` r1–r9 ¦ \¦Δ\¦ ≤ 0.79° (was −17.0 … +5.4° before D15) ¦ deg ¦ CURRENT (D15 + D27) ¦ json:d15_kick.json ¦ |
| §6.2 | ¦ UKF baseline position error magnitude at +10 / +30 / +60 s after loss, blank (n = 11: `dsn`, `fwdc`, `fwdplainc`, `p1c`) ¦ 6.4–9.0 / 20.5–33.0 / 112–288 ¦ m ¦ CURRENT (D27) ¦ json:blank_behaviour.json ¦ |
| §6.2 | ¦ FGO baseline, same ¦ 4.2–18.3 / 27–142 / 172–574 ¦ m ¦ CURRENT (D15) ¦ same ¦ |
| §6.2 | ¦ UKF / FGO baseline error at the end of cruise, blank †¦ 13–58 / 22–31 ¦ km ¦ CURRENT (D15 + D27) ¦ same ¦ |
| §6.2 | ¦ UKF / FGO baseline error at +60 s after loss, transition (n = 11) †¦ 31–307 / 939–1,049 ¦ m ¦ CURRENT (D15 + D27) ¦ json:blank_behaviour.json ¦ |
| §6.2 | ¦ Heading arms (n = 6, `fwdc`/`fwdplainc`), blank, +60 s: UKF / FGO †¦ 88–323 / 299–904 ¦ m ¦ CURRENT (D15 + D27; the heading does not bound position without flow) ¦ json:blank_behaviour.json ¦ |
| §6.4 | ¦ `fwdc` textured FGO r1 / r2 / r3 ¦ 4.58 / 4.68 / 4.58 ¦ m ¦ CURRENT ¦ same ¦ |
| §6.4 | ¦ `fwdc` textured UKF r1 / r2 / r3 ¦ 5.13 / 2.27 / 5.13 ¦ m ¦ DIAGNOSTIC (D15 + D27) ¦ same ¦ |
| §6.4 | ¦ `fwdplainc` textured FGO r1 / r2 / r3 ¦ 4.57 / 4.54 / 4.56 ¦ m ¦ CURRENT (D15) ¦ same ¦ |
| §6.4 | ¦ `fwdplainc` textured UKF r1 / r2 / r3 ¦ 5.17 / 11.51 / 11.09 ¦ m ¦ DIAGNOSTIC (D15 + D27; r2, r3 residual take-off kick) ¦ same ¦ |
| §6.4 | ¦ `p1c` textured EKF3 / FGO (`fwdc`, `fwdplainc`) ¦ 4.14 / 4.57; 4.11 / 4.60 ¦ m ¦ CURRENT (D15) ¦ json:rerun_p1c_evo.json ¦ |
| §6.5 | ¦ FGO baseline / +heading speed ratio ¦ 0.997 / 0.998 ¦ — ¦ CURRENT ¦ same ¦ |
| §6.5 | ¦ UKF +heading speed / along-track ratio ¦ 0.987–0.990 / 0.987–0.990 ¦ — ¦ CURRENT (correction (ii)) ¦ same ¦ |
| §6.6 | ¦ `fwdc` UKF +heading r1 / r2 / r3 ¦ 0.61 / 0.62 / 0.62 (0.611 / 0.617 / 0.621) ¦ m ¦ CURRENT (D27: −0.002 m each) ¦ json:phase4_fwdc_arms.json ¦ |
| §6.6 | ¦ `fwdc` FGO +heading r1 / r2 / r3 ¦ 0.08 / 0.09 / 0.09 ¦ m ¦ CURRENT ¦ same ¦ |
| §6.6 | ¦ `fwdplainc` UKF +heading r1 / r2 / r3 ¦ 0.88 / 0.94 / 0.73 ¦ m ¦ CURRENT (D27) ¦ json:phase4_fwdplainc_arms.json ¦ |
| §6.6 | ¦ `fwdplainc` FGO +heading r1 / r2 / r3 ¦ 0.20 / 0.61 / 0.22 ¦ m ¦ CURRENT ¦ same ¦ |
| §6.6 | ¦ Heading-arm yaw error rms, `fwdc` (UKF / FGO) ¦ 0.08 / 0.18–0.19 ¦ deg ¦ CURRENT ¦ same ¦ |
| §6.6 | ¦ FGO vs UKF with heading (claim wording) ¦ implementation result; the UKF's residual take-off kick (D15) and plain-wall over-confidence (NEES 6.11 after D27) stated alongside ¦ — ¦ CURRENT (wording, D15) ¦ M: "D15 RESULTS" ¦ |
| §6.6 | ¦ `fwdplainc` textured UKF +heading mean position NEES, mean of r1–r3 ¦ 6.11 (10.42 / 6.79 / 1.12) (D27; was 5.10) ¦ — ¦ DIAGNOSTIC ¦ json:phase5b_consistency.json ¦ |
| §7 | ¦ P4 FGO textured ¦ [4.189, 5.117] m (range 4.59–4.72 ± max(range, 0.40)) ¦ m ¦ CURRENT (recomputed, D15) ¦ same ¦ |
| §7 | ¦ P4 transition/blank bands ¦ computed by formula, but they measure EKF3 invalid output / UKF-FGO runaway size, not sensing ¦ — ¦ RECORDED (context: rulings 1 and 3) ¦ same ¦ |
| §8 | ¦ `fwdc` primary †¦ 6/9 pass (D15; misses: `fwdc_tex_r2` EKF3 0.01 m better than the band; `fwdc_blank_r1..r2` FGO runaway-size bands; `fwdc_blank_r3` now passes because its FGO ratio moved 212.53 → 203.52) ¦ — ¦ CURRENT (misses as worded) ¦ json:rerun_fwdc_score.json ¦ |
| §8 | ¦ `fwdplainc` primary †¦ 8/9 pass (miss: `fwdplainc_blank_r2` FGO ratio) ¦ — ¦ CURRENT (miss as worded) ¦ json:rerun_fwdplainc_score.json ¦ |
| §15 | ¦ Per-heading weight at equal sensor noise: FGO / UKF (closed loop, 5° R) ¦ 15.9 / 2.9 (gate σ 2.17 / 0.86°) ¦ % ¦ STRUCTURAL (mechanism untested) ¦ M: "D26 (b)", "D27 item 3" ¦ |
| §15.1 | ¦ 2(a) fresh open-loop flights: P1 robust < hard-gated FGO yaw max ¦ 9/12 (≥ 10 needed): **FAIL** ¦ — ¦ CURRENT (2 IMU-gap exclusions counted against) ¦ json:f4_test.json ¦ |
| §15.1 | ¦ 2(a) S2 max cross-track ≤ hard-gated ¦ 6/12 (≥ 8 needed): **FAIL** ¦ — ¦ CURRENT ¦ same ¦ |
| §15.1 | ¦ 2(a) against the UKF (descriptive) ¦ UKF lower yaw max 10/10; robust FGO lower cross-track 10/10 ¦ — ¦ DESCRIPTIVE ¦ same ¦ |
| §15.1 | ¦ 2(a) conclusion ¦ F1's exploratory benefit largely did not replicate; replicated: fewer wrong headings accepted ¦ — ¦ CURRENT (wording, ruled) ¦ M: "D28 RULED" ¦ |
| §16.1 | ¦ A: all 8 (4.3 s) ¦ 0.039 m ¦ 0.037 m ¦ **0.018 m** ¦ 0.014 m ¦ **0.011 m** ¦ |
| §16.1 | ¦ B: corners (10.1 s) ¦ 0.055 m ¦ 0.064 m ¦ **0.028 m** ¦ 0.031 m ¦ **0.013 m** ¦ |
| §16.1 | ¦ C: 2 diagonal (22.0 s) ¦ 0.074 m ¦ 0.104 m ¦ **0.058 m** ¦ 0.091 m ¦ **0.021 m** ¦ |
| §16.1 | ¦ D: 1 tag (46.3 s) ¦ **0.096 m** ¦ 0.189 m ¦ 0.121 m ¦ 0.258 m ¦ **0.033 m** ¦ |
| §16.1 | - **H-T1 (primary) PASS.** The FGO hindsight gain per gap (median) is 0.005 / 0.015 / 0.025 / 0.050 m for A–D, |
| §16.1 |   strictly increasing. Spearman ρ = +0.47, p = 3e-13, n = 213 gaps. |
| §16.1 | - **P-T2 FAIL.** The RTS-UKF gain is +0.021 / +0.036 / −0.007 / −0.126 m (single-pass smoother). |
| §16.1 | - **P-T3 FAIL.** The live max/min ratio is 2.15 / 2.33 / 1.80 / 1.97. |
| §16.1 | - **P-T4 FAIL.** The batch-FGO vs RTS-UKF ratio is 1.23 / 2.34 / 4.26 / 7.78. |
| §16.2 | ¦ UKF live ¦ 0.63–0.64 m ¦ 1.69–1.75 m ¦ 1.66–1.71 m ¦ |
| §16.2 | ¦ FGO live ¦ 0.97–1.17 m ¦ 2.83–3.31 m ¦ 2.47–2.88 m ¦ |
| §16.2 | ¦ RTS-UKF (hindsight) ¦ 0.60–0.64 m (cap-free variant 0.97–0.98 m) ¦ 0.02 m ¦ — ¦ |
| §16.2 | ¦ **FGO batch (hindsight)** ¦ **0.33 m** ¦ 0.00–0.01 m ¦ — ¦ |
| §16.2 | - **H-O2 FAIL:** the live ratio is about 2.2×. |
| §16.2 | - **P-O3 FAIL:** the batch FGO is about 1.9× better than the better RTS-UKF. |
| §16.3 | ¦ with loop closure ¦ **0.041–0.047 m** ¦ **0.020–0.029 m** ¦ 0.27–0.57 ¦ |
| §16.3 | ¦ without loop closure ¦ 0.200–0.312 m ¦ 0.236–0.298 m ¦ 4.5–5.5 ¦ |
| §16.3 | - **V-L PASS:** keyframe FGO 4.63 m against thesis FGO 4.59 m on `dsn_tex_r1` (evo -a cruise, +0.9%). |
| §16.3 | - **H-L1 (primary), H-L2, H-L3 and P-L4: PASS 3/3.** |
| §16.3 |   - no-LC: median 36–55 ms, p99 1.3–2.2 s, worst 1000-keyframe mean 1.41 s. |
| §16.3 |   - LC: median 33–43 ms per update. |
| §17 | ¦ 5 s hover ¦ 13–27 mm ¦ 32–49 mm ¦ 14–25 mm ¦ |
| §17 | ¦ 15 s hover ¦ 6–25 mm ¦ 120–145 mm ¦ 50–63 mm ¦ |
| §17 | ¦ 30 s hover ¦ 3–11 mm ¦ 282–292 mm ¦ 107–114 mm ¦ |
| §17 | ¦ ~7 s during a move ¦ 7–31 mm ¦ 40–57 mm ¦ 1–7 mm ¦ |
| §17 | No lockout in any loss (P-H7 PASS). P-H5 PASS. |
| Flags | - **`dsn` noise floor — CLOSED (ruling 2026-09-30).** Established from the re-flown `dsn_tex` (n = 10 / 9): |
| Flags |   EKF3 SD 0.31 m, FGO SD 0.13 m. It replaces "n = 3 range ± one range-width" as the basis for future |
