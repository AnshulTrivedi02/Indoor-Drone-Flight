# Model audit of effective behaviour: EKF3, UKF and FGO (2026-10-09)

Stage agent, worktree branch from `fwd-camera` 14c8d66. The FGO is audited as corrected (`setBiasAccOmegaInit = 0`,
merged 252fc46). Ruling: METHODOLOGY "RULING (user, 2026-10-09): bounded MODEL AUDIT of effective behaviour".

**REPORT ONLY.** No estimator code and no thesis result was changed. No simulator was run. Nothing was written to a trial
directory: bags were unpacked to the scratch area and replay outputs went to scratch. Every CPU-heavy step ran through
`heavy.py`.

Scripts are in `eval/diag/model_audit/`, and the raw outputs are in `eval/diag/model_audit/results/`.

## Verdict in one paragraph

**The FGO (corrected) and EKF3 match the analytic free-inertial growth** from the stated densities to within 1–6% on
every state, at 10 s and at 60 s.

**The UKF (offline and port) does not.** Its process noise is correct, but its sigma-point regularisation is not
harmless:
- `_sigma_points` adds 1e-12·I to P before the Cholesky (the port adds the same c·1e-12).
- The unscented transform carries that jitter straight into the predicted covariance at **every predict step**.
- On the delta-form gyro-bias states, whose per-step random walk is only (dt²·GBIAS_P_NSE)² ≈ 2–5e-14, this jitter is
  **the dominant process noise**. The effective gyro-bias random walk is **24.7× (offline) and 42× (port) the stated
  density**, in variance.
- It then inflates the attitude, velocity and position growth: at 10 s, tilt variance is 4.1× / 6.3×.
- Removing the jitter (diagnostic copy) brings both UKFs onto the analytic curve to within 1%. **This is a genuine
  inconsistency and a D18 model-correction candidate.**

Two smaller findings, for ruling:
1. **The FGO's per-keyframe yaw cap is not variance-gated.** EKF3's and the UKF's are gated. In free inertial over 60 s
   it holds the FGO's yaw variance at **0.37×** the others'. Its stated design intent (§9.4) was to match EKF3's gated
   `fuseEulerYaw(PREDICTED)`.
2. **Flow and range fusion rates differ.** EKF3 fuses flow at **15.1 Hz** and range at **16 Hz**. The UKF and the FGO
   fuse both at **30 Hz**, with the same per-sample σ. That is ~2.0× and ~1.9× the information per second. EKF3's
   50 ms sensor interval is an EKF3 rule.

Everything else is either consistent or a documented EKF3 rule. The details follow.

## Inputs

- **IMU:** `dsn_tex_r1` `/imu/data_raw`, cruise.
  - It was dejittered exactly as the replays do (`imu_timing.dejitter_imu` after the IMU-gap rule; period 3.00057 ms).
  - Window [120.0, 130.0] s for the 10 s numbers, and [120, 180] s for the 60 s numbers. The first 10 s are identical.
  - GT net horizontal speed 0.500 m/s, height 2.31 m, mean specific force (−0.004, 0.001, 9.811) m/s² FLU.
- **All three estimators propagate the SAME samples.** Each uses its own cadence and its own code:
  - **EKF3:** `ekf3_cov_harness.cpp`. `build.sh` copies EKF3's generated `CovariancePrediction` block **verbatim** from
    the pinned source (`AP_NavEKF3_core.cpp:1196-1748`, 7bac20cbcc) and `#include`s it. Around it the harness
    reproduces the following from the same source:
    - the noise set-up (`:1036, 1045-1058, 1159-1163`);
    - the bias process-noise addition, the 1e4 position-variance hold and the symmetric copy (`:1750-1794`);
    - `ConstrainVariances` (`:1884-1984`, states 0–15; bias states active, as in flight, `Control.cpp:159-179`);
    - the strapdown quaternion before the covariance, as `UpdateFilter` does.
    - Configuration: `stateIndexLim` = 15 (no mag, no wind). The IMU is re-binned to EKF3's **12.5 ms** prediction
      period (FRD).
  - **UKF offline:** `ukf_core.make_params(dt=DT_STEP)` + `ukf_core.predict`, accumulated exactly as `ukf_replay.py`
    does (5 samples = 15.003 ms, D27 scaling).
  - **UKF port:** the same Python core at the port's 12.5 ms cadence.
    - The port's Q is `sq(d·NSE)` with d = the actual ~12.5 ms step (`AP_NavUKF.cpp:167-169`), i.e. make_params at
      dt = 0.0125.
    - Its Cholesky adds the same c·1e-12 jitter (`AP_NavUKF.cpp:116-121`).
    - The port and the Python core were shown equivalent earlier (validation step 2).
    - **Not re-run in C++ here.**
  - **FGO:** `fgo_core.make_pim_params()` (corrected).
    - A chain of `CombinedImuFactor` at the replay's 1/30 s IMU-clock keyframes, from priors on X(0), V(0) and B(0).
    - Marginals from `gtsam.Marginals` at each checkpoint, with the rotation and translation tangents rotated into the
      world frame.
    - With no measurement factors, marginalising the fixed-lag window is exact, so the chain marginal is the
      smoother's.
- **Analytic reference.**
  - The continuous linear INS error model: attitude, velocity, position, and rate-form gyro and accel bias.
  - The stated densities q = NSE²·0.0125: GYRO 2.8125e-6 rad²/s, ACC 1.53125e-3 (m/s)²/s, GBIAS 1.25e-8 (rad/s)²/s,
    ABIAS 5.0e-6 (m/s²)²/s (CLAUDE.md "noise conversion").
  - Discretised exactly (Van Loan, 12.5 ms), from the same initial covariance.
  - `analytic_tv` linearises along the free-running MEAN trajectory (attitude strapped down through the recorded gyro,
    specific force per bin). **It is the reference.**
  - A fixed-level linearisation under-predicts vertical velocity at 60 s (0.75 against 1.25 m/s). That happens because
    the mean attitude drifts with the real gyro bias and couples yaw error into velocity. All three estimators and
    `analytic_tv` agree on 1.25.
- **Ratio convention:** **variance** ratio (effective ÷ expected), as D27 did. **FLAG if > 2 or < 0.5.** The σ values
  are shown alongside.

### Initial-covariance cases
- **A (the flag case):** common, near-zero initial covariance:
  - attitude 1e-5 rad;
  - velocity and position 1e-2 (EKF3's 1e-4 variance floors);
  - gyro bias 1e-6 rad/s;
  - accel bias at **EKF3's floor**, 5e-9 (m/s)² delta = (5.657e-3 m/s²)² rate. Below that floor EKF3 *resets* the
    accel-bias covariance to (0.2 m/s²)² (`core.cpp:1943-1974`), so a smaller value is not representable in EKF3.
  - Yaw-bounding pseudo-measurements are OFF.
- **B:** as A, but with each estimator's **configured** initial bias σ:
  - EKF3: 2.5°/s and 0.2 m/s²;
  - UKF: 0.043633·dt and 0.2·dt delta;
  - FGO: B(0) prior 0.043633 and 0.2.
  - This is a unit check of the delta/rate conversions.
- **C:** as A, with the yaw-bounding mechanisms **ON**:
  - the UKF: `update_yaw_pseudo` every 140 ms, variance-gated at trace(P_att) > 0.04;
  - the FGO: `yaw_prior_factor` σ 0.5 rad at every keyframe;
  - EKF3: `fuseEulerYaw(PREDICTED)` is gated at trace(P_quat) > 0.01 (`MagFusion.cpp:274`). The harness reports its
    quaternion trace instead of simulating the fusion: it peaks at **8.0e-4 over 60 s, so EKF3's gate never opens**.

## Item 1: free-inertial growth (case A; values are σ, brackets are the variance ratio to `analytic_tv`)

#### case A, reference `analytic_tv`

| t (s) | quantity | expected | ekf3 | ukf_offline | ukf_port | fgo | ukf_offline_nojitter | ukf_port_nojitter |
|---|---|---|---|---|---|---|---|---|
| 10 | tilt σ (rad) | 0.005683 | 0.005682 (×1.00) | 0.01147 (×4.07) **FLAG** | 0.01426 (×6.30) **FLAG** | 0.005657 (×0.99) | 0.005685 (×1.00) | 0.005682 (×1.00) |
| 10 | yaw σ (rad) | 0.005683 | 0.005682 (×1.00) | 0.01147 (×4.07) **FLAG** | 0.01426 (×6.30) **FLAG** | 0.005679 (×1.00) | 0.005685 (×1.00) | 0.005682 (×1.00) |
| 10 | horiz. vel σ (m/s) | 0.3414 | 0.341 (×1.00) | 0.5095 (×2.23) **FLAG** | 0.6024 (×3.11) **FLAG** | 0.3402 (×0.99) | 0.3413 (×1.00) | 0.3411 (×1.00) |
| 10 | vert. vel σ (m/s) | 0.1425 | 0.1425 (×1.00) | 0.1431 (×1.01) | 0.1434 (×1.01) | 0.1424 (×1.00) | 0.1425 (×1.00) | 0.1425 (×1.00) |
| 10 | horiz. pos σ (m) | 1.424 | 1.42 (×0.99) | 1.776 (×1.56) | 1.991 (×1.96) | 1.42 (×1.00) | 1.421 (×1.00) | 1.42 (×0.99) |
| 10 | vert. pos σ (m) | 0.791 | 0.7902 (×1.00) | 0.792 (×1.00) | 0.7921 (×1.00) | 0.7908 (×1.00) | 0.7909 (×1.00) | 0.7902 (×1.00) |
| 10 | gyro-bias σ (rad/s) | 0.0003536 | 0.0003536 (×1.00) | 0.001757 (×24.71) **FLAG** | 0.00229 (×41.96) **FLAG** | 0.0003529 (×1.00) | 0.0003537 (×1.00) | 0.0003536 (×1.00) |
| 10 | accel-bias σ (m/s²) | 0.009055 | 0.009055 (×1.00) | 0.009219 (×1.04) | 0.009334 (×1.06) | 0.009055 (×1.00) | 0.009057 (×1.00) | 0.009055 (×1.00) |
| 60 | tilt σ (rad) | 0.03267 | 0.03265 (×1.00) | 0.1501 (×21.10) **FLAG** | 0.1953 (×35.73) **FLAG** | 0.03205 (×0.96) | 0.03277 (×1.01) | 0.03277 (×1.01) |
| 60 | yaw σ (rad) | 0.03267 | 0.03265 (×1.00) | 0.1506 (×21.26) **FLAG** | 0.196 (×36.00) **FLAG** | 0.03261 (×1.00) | 0.03288 (×1.01) | 0.03287 (×1.01) |
| 60 | horiz. vel σ (m/s) | 8.136 | 8.129 (×1.00) | 34.1 (×17.56) **FLAG** | 44.28 (×29.62) **FLAG** | 7.907 (×0.94) | 8.133 (×1.00) | 8.131 (×1.00) |
| 60 | vert. vel σ (m/s) | 1.251 | 1.25 (×1.00) | 4.422 (×12.50) **FLAG** | 5.71 (×20.84) **FLAG** | 1.229 (×0.97) | 1.25 (×1.00) | 1.249 (×1.00) |
| 60 | horiz. pos σ (m) | 155.5 | 70.75 (×0.21) **FLAG** | 581.7 (×14.00) **FLAG** | 752.9 (×23.46) **FLAG** | 150.6 (×0.94) | 155.3 (×1.00) | 155.3 (×1.00) |
| 60 | vert. pos σ (m) | 24.4 | 24.37 (×1.00) | 59.67 (×5.98) **FLAG** | 75.59 (×9.60) **FLAG** | 24.12 (×0.98) | 24.37 (×1.00) | 24.37 (×1.00) |
| 60 | gyro-bias σ (rad/s) | 0.000866 | 0.0008659 (×1.00) | 0.004303 (×24.69) **FLAG** | 0.005609 (×41.95) **FLAG** | 0.0008626 (×0.99) | 0.000866 (×1.00) | 0.0008659 (×1.00) |
| 60 | accel-bias σ (m/s²) | 0.01822 | 0.01822 (×1.00) | 0.0187 (×1.05) | 0.01904 (×1.09) | 0.01821 (×1.00) | 0.01822 (×1.00) | 0.01822 (×1.00) |

**Case B (configured initial bias σ):** every estimator is within ×0.96–×1.08 of the analytic curve, at 1 s and at 10 s,
on every quantity (full table in `results/tables.md`).
- **So the delta↔rate conversions of the initial bias σ are consistent in all three.**
- With σ_bg = 2.5°/s the jitter is negligible against the bias variance, which is why the UKF also matches here.

### Item-1 flags
| # | estimator | quantity | expected → effective (variance ratio) | classification |
|---|---|---|---|---|
| 1a | UKF offline | tilt / yaw / horiz. velocity at 10 s | ×4.07 / ×4.07 / ×2.23 (×21 / ×21 / ×17.6 at 60 s) | **GENUINE**: a consequence of 3a (the jitter's gyro-bias random walk). It vanishes when the jitter is removed (×1.00–1.01). |
| 1b | UKF port | tilt / yaw / horiz. velocity at 10 s | ×6.30 / ×6.30 / ×3.11 (×36 / ×36 / ×30 at 60 s) | **GENUINE**, same cause; larger because the port has more steps per second (80 against 66.7). |
| 1c | EKF3 | horiz. position at 60 s | ×0.21 (σ 70.7 m against 155 m) | **STRUCTURAL (EKF3 rule).** `core.cpp:1774-1783` stops position-covariance growth once P[7][7]+P[8][8] > 1e4 (100 m). Irrelevant at flight scales. |
| — | FGO | all | ×0.94–×1.00 | consistent |
| — | EKF3 | all others | ×0.99–×1.00 | consistent (the harness's `ConstrainVariances` never binds in case A: 0 accel-bias resets, 0 gyro-bias cap hits) |

## Item 3: bias random walk (from the same runs)

| estimator | gyro-bias RW (stated 1.25e-8 (rad/s)²/s) | accel-bias RW (stated 5.0e-6 (m/s²)²/s) | how |
|---|---|---|---|
| analytic | σ 3.536e-4 rad/s at 10 s, 8.66e-4 at 60 s | σ 9.055e-3 at 10 s (incl. initial 5.657e-3) | Van Loan |
| EKF3 | ×1.00 | ×1.00 | harness |
| UKF offline | **×24.7** (σ 1.757e-3 at 10 s) | ×1.04 | `ukf_core.predict` |
| UKF port cadence | **×42.0** (σ 2.29e-3 at 10 s) | ×1.06–1.09 | `ukf_core.predict` at 12.5 ms |
| UKF, jitter removed (diagnostic) | ×1.00 | ×1.00 | patched `_sigma_points` |
| FGO | ×1.00 (×0.99 at 60 s) | ×1.00 | GTSAM marginals |

**3a, the mechanism, derived and then confirmed numerically.**
- `ukf_core._sigma_points` builds the sigma set from `Psym + 1e-12·I` (`ukf_core.py:54`). The port does the same:
  `c·(P + 1e-12)` on the first attempt (`AP_NavUKF.cpp:117-121`).
- For a state that the process leaves unchanged (the biases), the unscented transform returns exactly the sigma set's
  covariance, so `predict` returns P + 1e-12 + Q.
- **Every predict step therefore adds 1e-12 to every diagonal element.**
- On the delta-form gyro bias that is 1e-12 / DT² in rate units per step:
  - offline (66.65 steps/s, DT = 15.003 ms): **2.96e-7 (rad/s)²/s**, i.e. 23.7× the stated 1.25e-8 (plus the stated
    density itself: ×24.7 total);
  - port (80 steps/s, DT = 12.5 ms): **5.12e-7**, i.e. ×41 (+1 = ×42).
  - Exactly as measured.
- On the accel bias it adds 5–10% (2.96e-7 or 5.12e-7 against 5e-6). On attitude, velocity and position it is negligible
  directly.
- **Is it relevant in aided flight?** The density ratio does not depend on P, so the effective gyro-bias random walk is
  24.7× / 42× the stated one **in flight as well**.
  - For scale: EKF3's in-flight gyro-bias variance in `dsn_tex_r1` cruise (XKV, 60–300 s, median) is 3.9e-11 rad² delta
    on x/y (σ 0.50 mrad/s) and 3.9e-10 on z (σ 1.58 mrad/s).
  - The jitter adds 6.7e-11 (offline) or 8e-11 (port) per second: more than the whole x/y variance, every second.
  - **In-flight measurement (offline UKF):** `ukf_replay.py dsn_tex_r1` was run with `UKF_DUMP`, with HOME set to a
    scratch copy, so no trial directory was written (`ukf_dump_bias.py`, `results/ukf_inflight_bias.json`). Over
    cruise 60–300 s:
    - the UKF's gyro-bias σ is **1.42 mrad/s on x/y and 4.33 mrad/s on z**, against EKF3's 0.50 / 1.58 (XKV): a
      variance of ~8× / ~7.5× EKF3's;
    - the jitter adds 1e-12 per step, i.e. **15% of the x/y gyro-bias variance per second** (1.6% on z);
    - so the jitter keeps the UKF's gyro-bias uncertainty well above EKF3's in aided flight;
    - its accel-bias σ x/y stays at 0.197 m/s² (≈ the 0.2 initial value: unobservable horizontally), and z is
      10 mm/s² (EKF3: 52.9 / 10.0).
  - The dumped delta-bias variances (4.5e-10 to 4.2e-9) are ≫ 1e-12. So the `rts_smooth` comment in `ukf_core.py`
    ("Pp spans ~1e-14 (delta-form bias states)") is loose; it does not contradict this finding.
  - The effect on yaw drift and position was **not measured**; it would need a jitter-free replay, which is a model
    change and is left to the ruling.
- **Classification: GENUINE inconsistency, D18 model-correction candidate.**
  - The stated, matched noise density is not what the filter carries.
  - A numerical regulariser enters as unmodelled process noise on the smallest-variance states.
  - Fix options for the user, none applied:
    - (i) jitter only on Cholesky failure (the port's retry ladder, but starting at 0);
    - (ii) a relative jitter (e.g. 1e-12 × diag P);
    - (iii) subtract the added jitter from the predicted covariance.
  - Both builds (offline `ukf_core.py:54` and the port `AP_NavUKF.cpp:117`) carry it.

**EKF3 bias-variance rules (structural, noted):**
- the gyro-bias variance cap is (0.175·dt)²;
- the accel-bias floor is 5e-9 delta, with the 100:1 max/min ratio and a reset to (0.2 m/s²)² below the floor
  (`core.cpp:1936-1975`).
- **None binds in cruise:**
  - `dsn_tex_r1` XKV2 (60–300 s, 480 samples): accel-bias variance V13/V14 median 4.38e-7 (σ 52.9 mm/s²) and V15
    1.57e-8 (σ 10.0 mm/s²);
  - 0% of samples at the floor; max/min ratio ≈ 28 < 100.
  - In the free-inertial harness: 0 resets and 0 cap hits.

## Item 1/3 extra: the yaw-bounding pseudo-measurements (case C)

#### case C, reference `analytic_tv`

| t (s) | quantity | expected | ekf3 | ukf_offline | ukf_port | fgo |
|---|---|---|---|---|---|---|
| 10 | tilt σ (rad) | 0.005683 | 0.005682 (×1.00) | 0.01147 (×4.07) **FLAG** | 0.01426 (×6.30) **FLAG** | 0.005661 (×0.99) |
| 10 | yaw σ (rad) | 0.005683 | 0.005682 (×1.00) | 0.01147 (×4.07) **FLAG** | 0.01426 (×6.30) **FLAG** | 0.005153 (×0.82) |
| 10 | horiz. vel σ (m/s) | 0.3414 | 0.341 (×1.00) | 0.5095 (×2.23) **FLAG** | 0.6024 (×3.11) **FLAG** | 0.3404 (×0.99) |
| 10 | vert. vel σ (m/s) | 0.1425 | 0.1425 (×1.00) | 0.1431 (×1.01) | 0.1434 (×1.01) | 0.1424 (×1.00) |
| 10 | horiz. pos σ (m) | 1.424 | 1.42 (×0.99) | 1.776 (×1.56) | 1.991 (×1.96) | 1.421 (×1.00) |
| 10 | vert. pos σ (m) | 0.791 | 0.7902 (×1.00) | 0.792 (×1.00) | 0.7921 (×1.00) | 0.7909 (×1.00) |
| 10 | gyro-bias σ (rad/s) | 0.0003536 | 0.0003536 (×1.00) | 0.001757 (×24.71) **FLAG** | 0.00229 (×41.96) **FLAG** | 0.0003365 (×0.91) |
| 10 | accel-bias σ (m/s²) | 0.009055 | 0.009055 (×1.00) | 0.009219 (×1.04) | 0.009334 (×1.06) | 0.009055 (×1.00) |
| 60 | tilt σ (rad) | 0.03267 | 0.03265 (×1.00) | 0.1496 (×20.98) **FLAG** | 0.1946 (×35.51) **FLAG** | 0.03207 (×0.96) |
| 60 | yaw σ (rad) | 0.03267 | 0.03265 (×1.00) | 0.06632 (×4.12) **FLAG** | 0.05937 (×3.30) **FLAG** | 0.01991 (×0.37) **FLAG** |
| 60 | horiz. vel σ (m/s) | 8.136 | 8.129 (×1.00) | 34.01 (×17.48) **FLAG** | 44.15 (×29.45) **FLAG** | 7.925 (×0.95) |
| 60 | vert. vel σ (m/s) | 1.251 | 1.25 (×1.00) | 4.41 (×12.44) **FLAG** | 5.698 (×20.76) **FLAG** | 1.23 (×0.97) |
| 60 | horiz. pos σ (m) | 155.5 | 70.75 (×0.21) **FLAG** | 580.6 (×13.95) **FLAG** | 751.3 (×23.36) **FLAG** | 151.1 (×0.94) |
| 60 | vert. pos σ (m) | 24.4 | 24.37 (×1.00) | 59.53 (×5.95) **FLAG** | 75.4 (×9.55) **FLAG** | 24.14 (×0.98) |
| 60 | gyro-bias σ (rad/s) | 0.000866 | 0.0008659 (×1.00) | 0.003879 (×20.06) **FLAG** | 0.004997 (×33.29) **FLAG** | 0.0008132 (×0.88) |
| 60 | accel-bias σ (m/s²) | 0.01822 | 0.01822 (×1.00) | 0.0187 (×1.05) | 0.01904 (×1.09) | 0.01821 (×1.00) |

- **EKF3:** its quaternion-trace gate (0.01) is never reached in 60 s (max 8.0e-4), so it fuses no predicted yaw.
- **UKF:**
  - its pseudo-yaw fired 59 times (offline) and 115 times (port), only because the jitter-inflated tilt variance pushed
    trace(P_att) past 0.04;
  - with the jitter removed it would not fire (the trace is 3.2e-3 at 60 s);
  - its yaw σ at 60 s (×4.1 / ×3.3) is the jitter (3a) partly capped.
- **FGO:** the per-keyframe cap (σ 0.5 rad, 30 Hz, ungated) gives yaw variance **×0.82 at 10 s and ×0.37 at 60 s**, and
  gyro-bias-z variance ×0.88.
- **Flag 4 (FGO, ×0.37 at 60 s):**
  - The cap carries 30 × 1/0.25 = 120 rad⁻²/s of yaw information that EKF3 and the UKF never fuse at these variances.
  - It is a zero-innovation constraint toward the IMU-predicted yaw, so it injects no heading. But it does lower the
    FGO's yaw variance and so its weight on any heading measurement.
  - **Classification:** an inconsistency with the FGO's OWN stated design (FGO_DESIGN §9.4 and the `yaw_prior_factor`
    docstring: "matching EKF3's fuseEulerYaw(PREDICTED)"). EKF3's mechanism is variance-gated, and the UKF matches that
    gate.
  - This is estimator design, not a sensor noise model, so whether D18 covers it is **for the user to rule**.
  - It was candidate (iii) in "D27 item 3", untested until now. It is now measured in free inertial; its size in aided
    flight is not measured.
  - Fix options for the user, none applied: add the cap factor only when the FGO's predicted yaw variance (the
    gate-only recursion already computes it) exceeds the EKF3-equivalent threshold; or drop it as the reanchored room
    runs do.
  - **Aided-flight size, existing evidence (PRE-correction FGO).** METHODOLOGY "EXPLORATORY … C0/F2 pattern",
    Hypothesis 1: on the `fwdc_tex_r1` heading arm, `F_NO_YAWCAP` changed nothing to the printed precision. "The FGO's
    0.5 rad yaw cap is negligible beside the 0.148° heading factor."
  - So the cap matters only where there is **no heading measurement**: the `dsn_*` baselines, the forward-arm
    baselines, and the closed-loop no-heading flights. Its size there is **not measured**.
  - With heading at 5° (closed loop, up to 30 Hz) the heading carries up to 30/0.0873² ≈ 3900 rad⁻²/s. The cap's
    120 rad⁻²/s is ~3% of that: probably small, but untested.

## Item 2: measurement noise

### 2.1 Per-update noise each code path applies

| measurement | stated σ | EKF3 effective R (source) | UKF (offline and port) R_eff ÷ stated | FGO σ_eff ÷ stated | flag |
|---|---|---|---|---|---|
| flow, per axis | 0.25 rad/s (`EK3_FLOW_M_NSE`) | R_LOS = max(0.25, 0.05)² (`OptFlowFusion.cpp:64`). Fusion is skipped when S ≤ R_LOS (badly conditioned, `:445-452`), with no inflation. Gate (0.01·300)² = 9. Sequential X then Y | ×1.000 (sigma spread ÷ linear HPHᵀ = 1.000); same per-axis sequential gate 9 | 0.25 / 0.25 (×1.00); one 2-D isotropic factor, **no gate** (smoother), \|flow\| < 4.2 per axis | none on σ |
| range | 0.5 m (`EK3_RNG_M_NSE`) | max(0.5, 0.1)² + (rng·`EK3_TERR_GRAD` 0.1)²·(1 − cos²tilt) (`PosVelFusion.cpp:1428-1430`). At 2.3 m and a 1° tilt the added term is 1.6e-5 m² (6e-5 of R). Gate (0.01·`HGT_I_GATE` 500)² = 25. Median of 3 | ×1.000; gate 25 | 0.5 (×1.00); no gate | none on σ |
| closed-loop heading (ExtNav yaw, D17) | `VISO_YAW_M_NSE` 0.05 rad, EKF3's 5° floor | angErr clamped to [VISO_YAW_M_NSE, 1.5] (`AP_VisualOdom_MAV.cpp:43`), then max(angErr, 5°) (`Measurements.cpp:1118`), then R = max(·, 0.05)² (`MagFusion.cpp:879`). **Effective 5°** | port: the identical expression (`AP_NavUKF.cpp:294,317`); probe ×1.000 at 5° | node default 5° (`fgo_cpp_node.cpp:70`, `fgo_node.py:126`); probe ×1.00 | none |
| offline heading (Phase 4) | camera σ 0.148° (fwdc), 0.126° (fwdplainc) | **no forward arm** (ruling 2026-09-29) | `FWD_SIGMA`; probe ×1.000 | same `FWD_SIGMA` (`fgo_replay.py:162`) | none (EKF3 has no counterpart by ruling) |
| tag position (H) | 0.02 m (`VISO_POS_M_NSE`; sent 0.02) | posErr = max(VISO_POS_M_NSE, sent) (`AP_VisualOdom_MAV.cpp:42`); R = constrain(posErr, 0.01, 10)² (`PosVelFusion.cpp:801`). **H_s1_r1 log: PErr 0.0200 on all 8670 fixes** | port: `writeExtNavData` receives the same posErr (`AP_NavUKF.cpp:289`); offline `ROOM_TAG_SIGMA_POS=0.02` | node `tag_sigma_pos` 0.02 (`closed_loop_run.sh:72`, `run_trial.sh:423,449`); probe 0.02 (×1.00) | none |
| tag position (T) | 0.05 m (`tags_extnav.parm`; sent 0.05) | 0.05 | `TAG_SIGMA_POS` 0.05; probe ×1.000 | 0.05 | none |
| tag yaw | 5° | 5° (as heading). **H_s1_r1 log: AErr 0.0873 rad on all fixes** | `TAG_SIGMA_YAW` 5°; probe ×1.000 | 5°; probe ×1.00 | none |
| yaw pseudo-measurement | `EK3_YAW_M_NSE` 0.5 rad | R = 0.5², PREDICTED, variance-gated (`MagFusion.cpp:274,874`) | 0.5 rad, gated (trace 0.04) | 0.5 rad (×1.00), **every keyframe, ungated** | see Flag 4 |

The tag-σ wiring was checked because `run_trial.sh:399` defaults `tag_bridge_fwd`'s `sigma_pos_m` to 0.05 while the
FGO node defaults to 0.02. For H, `closed_loop_run.sh:72` exports `TAG_SIGMA_POS=0.02` to both, and the dataflash
confirms 0.02. So EKF3, the port and the FGO node all ran at 0.02. No mismatch.

Validity rules that are not noise but differ (noted, not flagged under this audit):
- the FGO's flow factor has no innovation gate and uses |flow| < 4.2 per axis;
- EKF3 checks quality > 0 and |flow vector| < 4.2 at intake (`Measurements.cpp:203`), then flowRadXY < `EK3_FLOW_MAX`
  2.5, signed, at fusion (`OptFlowFusion.cpp:668`);
- the UKF uses |flow| < 2.5 per axis.

Method:
- **EKF3:** source trace at 7bac20cbcc (lines in the table). The ExtNav values were confirmed from the `H_s1_r1`
  dataflash: 8670 VISP records, all with PErr 0.0200 and AErr 0.0873 (5°); PARM VISO_POS_M_NSE 0.02, VISO_YAW_M_NSE 0.05.
- **UKF:** `meas_probe.py` computes the innovation covariance with the code's own sigma points and h at a cruise state.
  R_eff = S_code − H·P·Hᵀ (central-difference H of the same h).
- **FGO:** `meas_probe.py` linearises each factor exactly as `factors.py` builds it, with `fgo_core`'s noise models.
  σ_eff = |H_row| / |A_row| (H the unwhitened Jacobian, A the whitened one).

### 2.2 Fusion rate: per-second information density

EKF3 measured on `dsn_tex_r1`, cruise 60–300 s (`fusion_rates.py`).

| sensor | arrivals | EKF3 fused | UKF offline / port / FGO fused | per-second information, UKF·FGO ÷ EKF3 | rule |
|---|---|---|---|---|---|
| flow | 30.3 Hz (bag), 29.9 Hz (dataflash OF) | **15.11 Hz** (50.5% of OF records) | 30.3 Hz (every message; the FGO one per 30 Hz keyframe) | **×2.0** | `writeOptFlowMeas` returns if < `sensorIntervalMin_ms` = 50 ms since the last accepted (`Measurements.cpp:178`, `AP_NavEKF3.h:516`); simulated on the OF record times |
| range | 30.3 Hz | **16.0 Hz**, each the median of 3 | 30.3 Hz (the port: every `update()` at 30 Hz, D18 rule) | **×1.9** | `readRangeFinder` samples when > 50 ms has passed, called once per 12.5 ms prediction → every 62.5 ms (`Measurements.cpp:32`, `PosVelFusion.cpp:1267`) |
| ExtNav heading / tag | ≤ 30 Hz | all (interval min 20 ms) | all | ×1.0 | `extNavIntervalMin_ms` = 20 (`AP_NavEKF3.h:518`) |

**Flag 5 (flow ×2.0, range ×1.9).**
- At **identical per-sample σ**, the UKF and the FGO take ~2× the flow and range information per second that EKF3 takes.
- This is EKF3's **buffer design**, not its noise model.
- **Classification: STRUCTURAL.**
  - The range half is already ruled under D18 (METHODOLOGY "range handling": the 50 ms sampling and the median are
    "EKF3 estimator design, not sensor validity … not copied").
  - The flow half follows the same rule. It is **recorded for confirmation** because no METHODOLOGY record of it was
    found.
- **Caveat, not measured:** fusing every frame assumes independent per-frame errors. Consecutive flow frames share
  features, so per-frame errors may be correlated. A 2× rate then overstates the information more than a 2× σ²
  difference would suggest.

### 2.3 Heading: effective innovation covariance, corrected FGO against the UKF (offline arm, `fwdc_tex_r1`)

The corrected FGO was replayed to scratch:
- `FGO_OUT_ROOT`, `fgo_replay.py fwdc_tex_r1 0.25 2 heading`.
- Its metrics are in `results/fgo_heading_fwdc_tex_r1_corrected_metrics.txt`.
- The `cross_track` / `ate_apparatus` values in that file are the corridor-frame artefact of the heading arm. The
  pre-correction file shows the same 150.8 / 123.2.
- Gyro-z bias tracking is now 92.7% of the true mean, against 55% before the correction.

The UKF numbers are from the trial's D27 `ukf_heading`. Cruise is 60–300 s, and R is (0.148°)² (`heading_S.py`,
`results/heading_S.json`).

| | n | S median | predicted yaw σ (median) | heading weight (HPHᵀ/S, median) | mean NIS | median NIS | NIS > 9 |
|---|---|---|---|---|---|---|---|
| UKF (current) | 7272 | 7.59e-6 | 0.055° | 0.121 | 1.36 | 0.239 | 2.4% |
| FGO before the correction | 7200 | 7.57e-5 | 0.476° | 0.912 | 0.22 | 0.042 | 0.1% |
| **FGO corrected** | 7200 | **7.53e-6** | **0.053°** | **0.114** | **1.36** | **0.234** | **2.4%** |

**With the correction, the FGO's heading innovation covariance matches the UKF's** (S ×0.99, weight 0.114 against
0.121, identical NIS).
- Before the correction the FGO's predicted yaw σ was 8.7× the UKF's and its weight 0.91. That is the offline face of
  "D27 item 3" (closed loop: weight 15.9% FGO against 2.9% UKF).
- **Offline**, the `biasAccOmegaInt` white noise accounts for the whole difference, and the correction removed it.
- **This does not settle "D27 item 3".** That ruling concerned the closed-loop builds: heading at 5°, with the weight
  measured from the smoother's actual yaw response to an outlier.
  - Those weights were not re-measured here; that would need a node-core replay with the corrected `make_pim_params`.
  - Flag 4 (the ungated yaw cap) was one of that item's candidates and is still present in closed loop.
  - Treat the item as **open pending a closed-loop re-measurement**, not as resolved.
- Mean NIS 1.36 for both: the heading innovations are slightly larger than predicted, identically in both
  estimators. This lies within 2× and is not flagged. The median NIS of 0.23 together with 2.4% > 9 points to
  heavy-tailed camera headings, not a model difference.

## Flags (summary)

| # | estimator | what | effective ÷ expected (variance) | classification |
|---|---|---|---|---|
| 3a | UKF offline and port | gyro-bias random walk carried by the sigma-point jitter 1e-12·I per predict | ×24.7 (offline), ×42 (port) | **GENUINE: D18 model-correction candidate** |
| 1a/1b | UKF offline and port | free-inertial tilt / yaw / horizontal velocity at 10 s (consequence of 3a) | ×4.1 / ×4.1 / ×2.2 (offline); ×6.3 / ×6.3 / ×3.1 (port) | GENUINE (same fix as 3a) |
| 4 | FGO | ungated per-keyframe yaw cap (σ 0.5 rad, 30 Hz) against EKF3's variance-gated PREDICTED fusion | yaw variance ×0.82 (10 s), ×0.37 (60 s) | an inconsistency with the FGO's own stated design (§9.4); **user to rule** whether D18 applies |
| 5 | UKF, FGO vs EKF3 | flow and range fusion rate at equal σ (EKF3 50 ms sensor interval) | information per second ×2.0 (flow), ×1.9 (range) | STRUCTURAL (EKF3 buffer rule; range already ruled under D18, flow to be confirmed) |
| 1c | EKF3 | horizontal position variance held at 1e4 m² | ×0.21 at 60 s | STRUCTURAL (EKF3 rule, `core.cpp:1774`); irrelevant in flight |
| (resolved OFFLINE only) | FGO (pre-correction) | offline heading S 10× the UKF's (σ 0.148° arm) | corrected FGO: S ×0.99 of the UKF's, identical NIS | **resolved offline** by the merged correction. The closed-loop weight behind "D27 item 3" (5° heading, the smoother's response to an outlier) was **not** re-measured; re-measure it with the corrected core before revisiting that ruling (Flag 4's ungated cap is still a candidate there) |

Not flagged (consistent within ×0.94–×1.09):
- **EKF3 and the FGO** on every process-noise quantity.
- **All three** on the configured initial bias σ (case B).
- **The per-sample R:**
  - flow 0.25, range 0.5 (EKF3's terrain-gradient inflation is ~6e-5 of R at cruise tilt);
  - closed-loop heading 5° (EKF3's floor);
  - tag position 0.02 m (H) / 0.05 m (T) and tag yaw 5°.
- **The accel-bias random walk** in all three (the UKF +4–9% from the jitter).

### Re-run scope if a correction is ruled (for the consolidated re-run plan)
- **3a (UKF jitter):**
  - **Offline:** every offline UKF result (all `ukf*` replays, RTS-UKF hindsight, room/T/O/H shadows).
  - **Port:** every port result:
    - the shadow replays can be re-run through Replay;
    - the closed-loop UKF flights (`cl_ukf_*`, H S2/S3 with the UKF flying) **cannot be replayed** and would need
      re-flying, as was ruled for the FGO's closed-loop flights.
  - The fix must go into both builds (`ukf_core.py:54` and `AP_NavUKF.cpp:117-121`), with the port equivalence
    re-checked.
- **Flag 4 (FGO yaw cap):**
  - every FGO result, offline and closed-loop: the C++ core adds the same factor at every keyframe (`fgo_core.cpp:123-125`);
  - the room runs drop the cap after the anchor, so their post-anchor segment is unaffected;
  - from the existing (pre-correction) evidence, heading-arm results are expected to be insensitive.
- **Flag 5 (rates):** no re-run unless the user rules to match EKF3's 50 ms interval (it is EKF3 design under D18 for
  range).

### Scope of the evidence (what each number is)
- **Item 1/3:** free-inertial propagation through each estimator's own prediction code, on recorded IMU. No aiding.
- **Item 2, flow / range / tags:** the R each **code path** applies, computed at a synthetic cruise state (UKF sigma
  points; FGO factor whitening), plus the EKF3 source and the dataflash values. **Only heading has an in-flight S**
  (§2.3).
- **The analytic reference:** no flag depends on choosing the fixed-level reference or the mean-trajectory one.
  - At 10 s the two are identical to 4 significant figures.
  - They differ only in vertical velocity and position at 30–60 s, where all three estimators side with
    `analytic_tv`.

## Reproduce
```
# scratch: unpack ~/thesis_data/trials/dsn_tex_r1/bag (zstd) to SCR/bag
python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "imu window" -- ~/venv-fgo/bin/python3 eval/diag/model_audit/imu_window.py SCR/bag dsn_tex_r1 120 SCR/win60.npz 60
python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "ekf3 harness" -- sh eval/diag/model_audit/build.sh SCR
python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "free inertial" -- ~/venv-fgo/bin/python3 eval/diag/model_audit/free_inertial.py SCR/win60.npz SCR/ekf3_cov_harness OUT.json 60
~/venv-ardupilot/bin/python eval/diag/model_audit/fusion_rates.py ~/thesis_data/trials/dsn_tex_r1/ardupilot.bin SCR/win60.npz 60 300
~/venv-fgo/bin/python3 eval/diag/model_audit/meas_probe.py OUT_probe.json
python3 eval/diag/model_audit/tables.py OUT60.json OUT10.json
```
