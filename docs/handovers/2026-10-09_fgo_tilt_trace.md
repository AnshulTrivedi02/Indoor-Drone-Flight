# FGO hover tilt trace (2026-10-09). STOPPED by ruling, incomplete

**Status:** this was a report-only stage. No estimator code or thesis result was changed.
- The user's ruling stopped the stage before batch 4 (take-off offset knobs) ran. Batch 4 was SIGINTed while it was
  still waiting, and no BUILD_LOCK was left behind.
- All replays below are DIAGNOSTIC. They were written to scratch only, not to any trial's `room_fgo/`.
- Scripts are in `eval/diag/fgo_tilt_trace/`:
  - `diag_replay.py` wraps the UNCHANGED `room_fgo_replay.py`, with env knobs;
  - `h_score_diag.py` is `eval/h_score.py` with a switchable FGO track path.
- One write outside scratch: `imu_gaps.json` for `H_safety_fgo_a`/`_b`, via `imu_gap_check --write` (verdict ok).

## Result in one line
**There are two causes.** The main one is confirmed: a GTSAM 4.2.1 parameter misreading makes the FGO's IMU factor
~26× too loose in rotation (it causes the roll scatter). The second is supported but not confirmed: a take-off
flow artefact, which leaves a per-flight tilt offset.

## 1. Error characterisation (offline Python FGO; reproduces the flown numbers)
Hover windows:
- `H_s1_r1`: 60–110 s.
- `H_safety_fgo_a`: t_f − 17 s … t_f (65.72 s).
- `H_safety_fgo_b`: t_f − 17 s … t_f (72.19 s).

Error = estimate − GT. Offline output is FLU, where pitch has the opposite sign to the flown ATT (FRD).

| | roll mean / sd (°) | pitch mean / sd (°) | tilt RMS (°) |
|---|---|---|---|
| `H_safety_fgo_a`, offline | +0.006 / **0.183** | +0.094 / 0.013 | 0.206 (flown: 0.205) |
| `H_safety_fgo_b`, offline | +0.043 / **0.187** | −0.224 / 0.016 | 0.295 (flown: 0.280) |
| `H_s1_r1`, offline | −0.031 / **0.185** | +0.177 / 0.036 | 0.260 |
| `H_s1_r1`, UKF | +0.022 / 0.040 | +0.184 / 0.006 | 0.189 |

The offline replay reproduces the flown signature (sign-converted), so this is the FGO model, not the C++ port.

**Structure (`H_s1_r1`).**
- The scatter is 0.5–5 Hz:
  - roll: 58% of its power at 0.5–2 Hz and 27% at 2–5 Hz;
  - lag-1 autocorrelation 0.82;
  - not at the keyframe rate.
- The FGO over-responds to the real roll:
  - regression of the estimate on GT gives a gain of **1.39** (pitch 1.64), against the UKF's 0.95;
  - the residual sd is 0.17°.
- **It is driven by the tag fixes:**
  - roll error vs the tag-fix E error: r = +0.61 (one keyframe lag);
  - pitch error vs the tag-fix N error: r = +0.61.
- The tag-fix error itself:
  - sd 7.1 mm in E and 1.2 mm in N;
  - broadband;
  - NOT coupled to the true attitude (R² 0.03).
- **During tag losses** (264–269 s, 299–319 s) the roll sd falls to **0.002°**.

## 2. Confirmed cause: `setBiasAccOmegaInit` acts as extra IMU white noise in GTSAM 4.2.1
- **Where it is set:**
  - `fgo_core.py:32` and `fgo_cpp/src/fgo_core.cpp:46` set `biasAccOmegaInit = diag(0.2², 0.043633²)`;
  - FGO_DESIGN §5 meant this as "EKF3's initial bias covariance".
- **What 4.2.1 actually does** (`~/opt/src/gtsam-4.2.1/gtsam/navigation/CombinedImuFactor.cpp:138-163`):
  - it adds `H·(bInitCov/dt)·Hᵀ` at EVERY `integrateMeasurement`, with H ≈ dt;
  - that is a continuous white-noise density of 0.0436 rad/s/√Hz on the gyro and 0.2 m/s²/√Hz on the accelerometer.
- **Against the matched values** (0.00168 and 0.039): **26× (gyro) and 5× (accel) too loose.**
- CLAUDE.md's "deprecated" note refers to later GTSAM, not the 4.2.1 that both cores use.
- The `B(0)` prior already carries these sigmas, so the term is also double-counted.
- **Measured** (`pimcov.py`, one 33 ms keyframe):

  | | rotation sd | velocity sd |
  |---|---|---|
  | as set | 0.454° | 37 mm/s |
  | `binit = 0` | 0.0175° | 7.1 mm/s |

- **Mechanism:** with attitude barely constrained by the gyro, the ungated tag factors (σ 0.02 m, 30 Hz) pull roll and
  pitch to fit their noise.

**Diagnostic replays (`H_s1_r1` to 130 s, window 60–110 s):**

| variant | roll mean / sd | pitch mean / sd | gain (roll) | tilt RMS |
|---|---|---|---|---|
| thesis config (reproduces the stored output's stats) | −0.031 / 0.185 | +0.177 / 0.036 | 1.38 | 0.260 |
| **binit = 0 (both)** | +0.052 / **0.026** | +0.090 / 0.004 | 0.95 | **0.108** |
| binit gyro = 0 only | +0.140 / 0.020 | −0.008 / 0.019 | 1.01 | 0.143 |
| binit accel = 0 only | −0.029 / 0.263 | +0.140 / 0.050 | 1.78 | 0.304 |

**The gyro term carries the scatter.**

**Full-length `H_s1_r1` with binit = 0** (60–385 s):
- roll sd 0.042, pitch +0.099;
- tilt RMS **0.118°** (stored: roll sd 0.17, pitch +0.13).

**The safety flights:**

| flight | variant | roll sd | tilt RMS |
|---|---|---|---|
| `H_safety_fgo_a` | thesis config | 0.183 | 0.206 |
| `H_safety_fgo_a` | binit = 0 | **0.044** | **0.089** (EKF3 ref flight: 0.114) |
| `H_safety_fgo_b` | thesis config | 0.187 | 0.295 |
| `H_safety_fgo_b` | binit = 0 | **0.043** | 0.264 |

In `H_safety_fgo_b` the pitch offset stays at −0.226 (§3).

## 3. Second component (not confirmed): a take-off tilt offset from flow during the fast low climb
- In `H_safety_fgo_b`, even with binit = 0, the pitch error jumps to ~−0.4° during the climb (37–40 s, z 0.2 →
  2.1 m, overshoot) and stays at ~−0.22° in hover.
- **It is NOT the UKF's take-off-fix mechanism.** The D18 rule held: there were no tag fixes from 35 to 44 s.
- **What the climb shows:** the flow residual against the shared `h_flow_pose` evaluated on GT is large and systematic
  on flow_y (the forward axis, i.e. pitch) while vz is large:
  - `H_safety_fgo_b`: +0.88 rad/s (sd 1.26) at z 0.5 m; −0.15 and −0.09 in the descent from the overshoot;
  - `H_safety_fgo_a`: −0.53 and +0.14 at z 0.7–1.3 m;
  - in hover: ≤ 0.005.
- **Knob tests on `H_safety_fgo_b` with binit = 0** (pitch mean over 45–60 s):

  | variant | pitch mean |
  |---|---|
  | as is | −0.21 |
  | no flow in 34–44 s | **−0.01** |
  | window 1.0 s | +0.07 |
  | LM 10 iterations | **+0.27** (sign flips) |

- **Reading:** a per-flight, poorly determined split of tilt and accelerometer bias, set by the climb's flow artefact
  and then frozen. In hover the two are unobservable apart, and the 0.25 s window marginalises it early.
- **Not done (batch 4, stopped):** the window/flow knobs through the full hover window, on both flights.

## 4. Proposed fix (for a ruling; nothing changed)
1. **`setBiasAccOmegaInit(0)`** in both cores (`fgo_core.py:32`, `fgo_core.cpp:46`).
   - The initial bias uncertainty stays in the `B(0)` prior, where it already is.
   - This makes the IMU noise EKF3-equivalent, as FGO_DESIGN §5 intended.
   - **Shown effect:** hover tilt RMS 0.26 → 0.11–0.12 (`H_s1_r1`) and 0.206 → 0.089 (`H_safety_fgo_a`).
2. **Take-off offset.** Candidates, each still to be tested:
   - a shared flow-validity rule for fast vertical motion at low height (it would apply to all three estimators,
     D18-style);
   - a longer window, but its CPU cost must be checked against the live 33 ms budget.

## 5. Implications for earlier thesis results (important)
- **Every FGO result ran with the inflated IMU noise.** That covers corridor `dsn_*`, fwdc/fwdplainc, T, O and H,
  both offline and flown (the C++ node uses the same setting).
- **The "FGO process noise equivalent to EKF3" fairness claim (CLAUDE.md "GTSAM IMU Preintegration", FGO_DESIGN §5)
  is therefore not true as implemented.** This is an FGO-only asymmetry against the EKF3-matched UKF.
- **The H S1 tag-loss drift changes a lot** (`h_score_diag.py`, `H_s1_r1`, effective drift, FGO):

  | loss | stored | binit = 0 | EKF3 (committed) | UKF |
  |---|---|---|---|---|
  | hover 5 s | 13.9 mm | 9.3 mm | | |
  | hover 15 s | 49.8 mm | **4.2 mm** | 6–25 mm | 120 mm |
  | hover 30 s | 111.6 mm | **6.5 mm** | 3–11 mm | 292 mm |
  | during the move | 0.7 mm | 0.5 mm | | |

  The S1 conclusion "the FGO drifts ~0.4 cm/s with the tag lost" is largely this parameter.
- The corridor headline numbers (evo -a (cruise), the distance scale) may move. **Not tested.**

## 6. Open items
1. **Re-run one corridor bag with binit = 0** and compare evo -a (cruise) and the distance scale:
   `FGO_OUT_ROOT=<scratch> DIAG_BINIT_ACC=0 DIAG_BINIT_GYR=0` around `fgo_replay.py`. The wrapper targets
   `room_fgo_replay.py`; switch the runpy target.
2. Batch 4 (`run_4.sh`): the take-off offset knobs through the hover window, on both safety flights.
3. Characterise the vertical-motion flow_y artefact (flow_tracker, low height, divergence) and check EKF3's/the UKF's
   exposure to it.
4. The C++ port has the same line. Any fix must change both cores and re-run the equivalence checks.
