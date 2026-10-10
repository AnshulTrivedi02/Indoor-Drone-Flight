# Initial-uncertainty audit, the FGO initial-sigma correction, and the FGO-only pass (2026-10-10)

Stage agent, worktree branch `worktree-agent-a8899fea0326b338e`, based on `fwd-camera` `73b475b`.
Ruling: METHODOLOGY "RULINGS (user, 2026-10-10): FGO initial yaw sigma, a MODEL CORRECTION under D18", items 1–3.
Extends `docs/handovers/2026-10-09_model_audit.md` (process noise) to the INITIAL uncertainties.

**What this stage did not do:**
- It did not launch the FGO-only pass, and it changed no EKF3 code, METHODOLOGY.md or numbers.md.
- It wrote nothing into any trial directory. Every replay ran through `heavy.py`, from a frozen scratch copy of the
  source, with outputs in scratch (`FGO_OUT_ROOT` / `UKF_OUT_ROOT`) and scratch bag copies (`FGO_BAG_ROOT` / `UKF_BAG_ROOT`).
- It did not build or install the C++ core (parked post-freeze, coordinator 2026-10-10). The source change is committed.
- The UKF port (`~/ardupilot_ukf`) was read, not built or changed.

## A. Audit: every initial state sigma (1 σ, common units)

Sources (all read at the current trees):
- UKF offline: `src/estimators/ukf_core.py:307-324` (`init_state`).
  - Called by `ukf_replay.py:92` and `room_ukf_replay.py:112`, both with `dt = DT_STEP`. That is the realised predict
    step, 5 IMU samples = 15.003 ms.
  - Per-experiment overrides: F3 (`F_YAW0_DEG` / `F_YAW0_SIGMA_DEG`; `ukf_replay.py`) sets P[8,8], an experimental
    injection, kept. The T/O/H re-anchors (`room_ukf_replay.py:166-177`) RESET x, y and yaw (and the O velocity) to the
    fix noise. They are not initial priors.
- UKF port: `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp:259-274` (`NavUKF::initialise`). Identical numbers, with
  dt = 0.0125 s (the port's step). `AP_NavFGO.cpp` is an output predictor only and has no priors.
- FGO offline: `src/estimators/fgo/fgo_core.py` `FGO.init` (the X(0)/V(0)/B(0) priors). `cov_gate` and `cov_prev` are
  initialised from the same `pose_sig` / 0.1 / `bias_sig`. The `reanchor` fallback covariance (used only if `cov_prev`
  is None) repeats the same values.
  - Every harness (`fgo_replay.py`, `room_fgo_replay.py`, `lc_fgo_replay.py`, `fgo_node_core.py`) calls `FGO.init`.
  - `lc_fgo_replay.start_isam_plain` (the V-L validation) had its own hard "thesis gauge" yaw 1e-3.
  - F3's `yaw_sigma` override is kept.
- FGO C++: `src/estimators/fgo_cpp/src/fgo_core.cpp:75-80` (X(0)/V(0)/B(0)), `:93` (gate covariance from `pose_sig`),
  `:200` (reanchor fallback). The constants are in `include/fgo_cpp/fgo_core.h`. `live_adapter` / `fgo_cpp_node` call
  `FGO::init` and have no priors of their own.
- EKF3 reference: `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_core.cpp:574-620` (`CovarianceInit`), with Copter
  defaults from `AP_NavEKF3.cpp:22-25,184,218,541`. None of these parameters is set in our `.parm` files.
  - Gyro-bias uncertainty: `AP_NavEKF3_GyroBias.cpp:20` = 2.5 °/s.
  - `ACCEL_BIAS_LIM_SCALER` = 0.2 (`AP_NavEKF3_core.h:55`), with `EK3_ACC_BIAS_LIM` at its default of 1.0.

| state | UKF offline (= port) | FGO (Python = C++), BEFORE | FGO AFTER this change | EKF3 `CovarianceInit` (reference) | class |
|---|---|---|---|---|---|
| roll, pitch | 5° (var `radians(5)²`, Euler) | **2°** (Pose3 tangent) | **5°** | 0.1 rad = 5.73° (rotation-vector var 0.01) | **GENUINE → fixed** |
| yaw | 1° | **1e-3 rad = 0.057°** | **1°** | 0.1 rad = 5.73° | **GENUINE (ruled) → fixed** |
| x, y | var 1e-3 → σ 0.0316 m | σ 0.001 m | unchanged | `POSNE_M_NSE` 0.5 m | justified: gauge |
| z | 0.5 m (`RNG_M_NSE`) | 0.5 m | unchanged | `ALT_M_NSE` 2.0 m | match |
| velocity (E, N, U) | 0.1 m/s | 0.1 m/s (isotropic) | unchanged | `VELNE_M_NSE` 0.3 / `VELD_M_NSE` 0.5 m/s | match |
| gyro bias | DELTA form 0.043633·dt rad per step (dt = 15.003 ms offline, 12.5 ms port) = **0.043633 rad/s = 2.5 °/s** as a rate | RATE 0.043633 rad/s | unchanged | DELTA `radians(2.5)·dtEkfAvg` = 2.5 °/s | justified: delta vs rate, equivalent |
| accel bias | DELTA 0.2·dt m/s per step = **0.2 m/s²** | RATE 0.2 m/s² | unchanged | DELTA 0.2·1.0·dtEkfAvg = 0.2 m/s² | justified: delta vs rate, equivalent |
| cross-covariances | none (diagonal) | none (independent priors) | unchanged | attitude block via `CovariancePrediction(&rot_vec_var)`, rest diagonal | match |

Notes on the classification:
- **Bias rows.**
  - The UKF divides its delta-form bias by the same `p['dt']` it was initialised with. Examples: `h_yawrate(gyro_z_avg,
    s[bz] / p['dt'])`, and the strapdown subtraction per step.
  - So the rate-equivalent is exactly the FGO's for both cadences: offline 15.003 ms (`make_params(dt=DT_STEP)`) and
    the port's 12.5 ms.
  - All three estimators carry EKF3's 2.5 °/s and 0.2 m/s².
- **x, y (gauge).**
  - No arm observes absolute horizontal position before a re-anchor. Checked in `room_fgo_replay.py`: `gnss_noise` is
    created and `gnss_factor` / `tag_factor` are added only after `reanchor()`. That call resets x, y (and yaw) with
    the fix noise in both estimators.
  - The O alignment yaw σ is the same in both: `asin(σv / spd)` (`room_ukf_replay.py:168`; `room_fgo_replay.py` passes
    the same expression to `reanchor`).
  - So the 1 mm against 31.6 mm difference carries no information. Unlike yaw, it is not a hidden claim waiting for a
    sensor. Left unchanged, which avoids a UKF re-run.
- **Attitude parameterisation.** Euler (UKF) against Pose3 body tangent (FGO). At level, with yaw 0, they coincide to
  first order. Not a mismatch.
- **Roll/pitch, the one new finding.**
  - FGO_DESIGN §8 planned the FGO's roll/pitch prior as "the empirical scatter of the levelling estimate, measured, not
    assumed". The code had a fixed 2°: neither that, nor the UKF's 5°, nor EKF3's 5.73°.
  - No estimator-design reason exists for the difference, so it is a D18 inconsistency. It is the same class as the
    yaw: the two compared estimators claim different prior knowledge.
  - **This one was NOT explicitly ruled.** It follows ruling item 2 ("genuine ones are fixed under D18 in the SAME
    change"), and the direction follows item 1 (the FGO takes the UKF's value).
  - Unlike yaw, it touches **every FGO arm**, not only the heading arms, through the X(0) prior, the yaw-cap gate trace
    and the T/O/H re-anchor roll/pitch sigmas (taken from `cov_prev`).
  - Effect size: verification C1b below. The trace already flagged it ("Secondary, NOT demonstrated: roll/pitch are 2°
    (FGO), 5° (UKF) and 5.7° (EKF3)").
- **The UKF is unchanged by this audit.** No genuine mismatch needed a UKF-side fix, so the UKF needs no re-run. The
  only UKF-file edits are off-by-default knobs; see B.

## B. Changes (commits `df50ad9` and the handover commit, which also adds `ukf_replay.py`'s `UKF_BAG_ROOT`)

D18 model corrections, in both cores:
- `src/estimators/fgo/fgo_core.py`:
  - `YAW0_SIGMA = np.radians(1)` (ruled) and `ROLLPITCH0_SIGMA = np.radians(5)` (audit);
  - used in the X(0) pose prior and the `reanchor` fallback covariance;
  - `cov_gate` / `cov_prev` pick them up from `pose_sig`. F3's `yaw_sigma` override is unchanged.
- `src/estimators/fgo_cpp/include/fgo_cpp/fgo_core.h`: the same two `constexpr` values (bit-identical to `np.radians`:
  `x * (pi / 180)`).
- `src/estimators/fgo_cpp/src/fgo_core.cpp`: used at `:75` (X(0)) and `:200` (the reanchor fallback). `:93` (`s0 <<
  pose_sig`) picks them up.
- `src/estimators/fgo/lc_fgo_replay.py` `start_isam_plain` (V-L): the yaw σ is now `sqrt(cov_prev[2,2])` (the thesis
  FGO's own) instead of a hard 1e-3. x, y stay at the 1e-3 gauge. **Changes the V-L / L results** (the L stage
  re-runs).
- `FGO_DESIGN.md` §8 table updated.

Checks, pipeline and knobs (all off by default; defaults unchanged):
- `eval/final_rerun_checks.py`:
  - **correction (5)** asserts both sigmas in both cores, both C++ sites, the reanchor fallback, the lc V-L start, no
    leftover 1e-3 / 2°, and that `ukf_core.init_state` still has 5/5/1°. Negative-tested: it FAILS on `73b475b`'s
    tree (10 errors) and passes on this branch.
  - New `ukf-gate`, the EKF3 gate generalised to UKF leaves.
- `src/estimators/fgo/fgo_replay.py`, `src/estimators/ukf_replay.py`:
  - `INIT_YAW_SIGMA_RAD`, the sensitivity knob: zero offset; it asserts that `*_OUT_ROOT` is set and that the F3 knob
    is not; its output-directory suffix is `_iy<value>`; it is refused in an equivalence dump.
  - `ukf_replay.py` also gets `UKF_BAG_ROOT` (parity with `FGO_BAG_ROOT`; the trace's scratch patch).
- `eval/run_set_eval.sh`: `SKIP_UKF=1` (FGO replays only). It also now checks exactly this run's replay logs and fails
  on a missing log. Previously a glob with no missing-log check.
- `eval/final_rerun_pipeline.sh` / `tools/launch_final_rerun.sh`: `FINAL_FGO_ONLY=1` and `FINAL_SENS_YAW0=1`; see D.
- `eval/sens_yaw0_eval.py`, `batches/final_rerun/sens_yaw0.jobs`: the labelled sensitivity check.

## C. Verification

All heavy steps ran through `heavy.py`, after the attribution study released the lock. Each ran from a frozen scratch
copy of the source (with a copy of `eval/results`, which `measurement_models` reads for `fwd_calibration.json`). The
bag was a scratch copy of `fwdplainc_tex_r1` (deleted afterwards), and the outputs went to scratch. Metrics:
`eval/diag/initial_sigma_audit/c1_metrics.{py,txt}`.

**C1a: the yaw-only correction reproduces the trace's F_YAW0 = 1° demonstration. PASS.**
- Python FGO, heading arm, hard gate (`fgo_replay.py fwdplainc_tex_r1 0.25 2 heading`), against the trace's
  `fgo_heading_y0s1` output.
- **Byte-identical:** `fgo_traj.tum`, `ground_truth.tum`, `bgz_series.txt` and `fwd_stats.json`.
- **Not identical, but only in the expected places:**
  - `metrics.txt`: only `step_median_ms` / `step_p99_ms` (wall-clock timing) differ;
  - `timing_and_fwd.npz`: `fwd_log`, `fwd_S` and `cov_log` are identical; only `t_keyframe_ns` (wall-clock) differs.
- The dumped input event stream equals the trace's.
- The trace did not keep its y0s1 per-keyframe dump, so there is no kf-level byte compare. The trajectory and every
  estimator output are byte-equal, and that is the stronger check of the two.
- Why identical: `np.radians(1)` equals `np.radians(float("1"))`, and F_YAW0_DEG = "0" injects zero offset.

**C1b: adding roll/pitch 5° (the full change, which is what the pass will run).**
- The same bag and arm give the same metrics to the printed precision:
  - evo -a (cruise) 0.150 m;
  - yaw rms 3.413° and max 5.028°;
  - bgz −8.04 deg/min;
  - 747 / 6333 headings fused.
- Against the stored output (1e-3 rad / 2°): 43.54 m, yaw max 1718°, 28 fused. The UKF stored: 0.188 m, 5.04°, 752
  fused.
- The trajectory is not byte-identical to C1a: max |Δposition| 2.7 mm and max |Δquaternion component| 6e-4. The
  roll/pitch change is real but small on this bag.
- Its effect across the whole dataset is measured by the FGO-only pass itself. The previous FGO results are the
  ablation pair.

**UKF default path unchanged by the knob edits. PASS.**
- `ukf_replay.py fwdplainc_tex_r1 heading` from the committed tree (knobs unset, `UKF_BAG_ROOT` used only to read the
  scratch bag) against the stored trial output.
- `ukf_traj.tum`, `metrics.txt`, `bgz_series.txt`, `fwd_stats.json` and `ground_truth.tum` are byte-identical.
- In `timing_and_fwd.npz`, the NIS / S arrays are identical; only the wall-clock timing arrays differ.
- `ukf_core.py`'s md5 equals the full re-run's provenance record (`483383f0…`).

**C2: C++ core. PARKED (coordinator, 2026-10-10: thesis results first).**
- The C++ source change is committed (`fgo_core.h` constants, `fgo_core.cpp` both sites).
- It was **not** built and the equivalence harness was **not** run. `~/opt/fgo_cpp` is untouched, so the installed
  binaries still carry the old 1e-3 / 2° priors.
- This is a post-freeze item. Ruled: before any REAL FGO flight, the corrected C++ node must pass its equivalence
  checks and the safety tests. See E.

**C3: `final_rerun_checks.py corrections` has the fifth check.**
- It passes on this branch and FAILS on `73b475b` (negative test on a scratch copy of HEAD's tree: 10 errors listed).
- `ukf-gate` was smoke-tested: 45 UKF leaves compared in `rerun_dsn_evo.json`.

## D. The FGO-only pass (prepared, NOT launched)

Launch, after this branch is merged into `fwd-camera` and the main checkout is on it. The job lines `cd ~/thesis_ws`, so
the pass runs the MAIN checkout's code:
```
tmux new -s final_rerun2 'FINAL_FGO_ONLY=1 FINAL_SENS_YAW0=1 bash ~/thesis_ws/tools/launch_final_rerun.sh 2>&1 | tee -a ~/thesis_data/batches/final_rerun2_console.log'
```

What `FINAL_FGO_ONLY=1` does (`eval/final_rerun_pipeline.sh` header):
- **New names.** Each one DIEs if it exists without having been started by this pipeline:
  - state `~/thesis_data/batches/final_rerun2/`;
  - snapshot `eval/results_pre_final2` (a copy of the current `eval/results`, i.e. the corrected-noise results; these
    become the ablation pair "before the initial-sigma correction");
  - archive `~/thesis_data/pre_final2_trials` (FGO output dirs only: `fgo*`, `room_fgo*`, `lc_fgo_*`; 331 dirs);
  - batches `final2_*`;
  - 5b sandbox `phase5b_final2`.
- **All FGO replays, no UKF replays.**
  - The job lists are filtered at run time: every line running `ukf_replay.py` / `room_ukf_replay.py` is dropped, and
    the stage DIEs if any kept line is not an FGO replay. Phase 4 keeps 45 of 90, F 39 of 73, f4 20 of 30, 5b 36 of 72,
    room_H 6 of 12, room_O 3 of 9, room_T 12 of 24, and L 7 of 7.
  - `run_set_eval.sh` runs with `SKIP_UKF=1`.
  - Phase 5b copies the 72 UKF instrumented outputs from `phase5b_final` (same UKF code).
- **Every scoring stage still runs**, on the trial-directory UKF outputs, which are unchanged.
- **Gates.**
  - Every EKF3 hard gate is unchanged.
  - **A hard UKF gate** (`final_rerun_checks.py ukf-gate`) next to each EKF3 gate, on the pure-metric files: the
    dsn / dsn_extra / set evo, the Phase 4 evo, and the H / O / T scores. Every UKF leaf must equal the snapshot, which
    proves the pass was FGO-only.
  - Band-scored `*_score.json` files are not UKF-gated: their UKF band/pass leaves depend on the recomputed bands.
- **Opt-in stages.** `d27item3` / `cl_pred` stay opt-in (FGO-only already).
- **Sensitivity check** (`FINAL_SENS_YAW0=1`): stage `sens_yaw0`, after ftests, while the corridor bags are still
  unpacked.
  - 30 jobs: UKF and FGO, with `INIT_YAW_SIGMA_RAD=0.1`, on the six fwdplainc tex/trans bags and fwdc_tex_r1 (baseline
    and heading arms each), and on dsn_tex_r1 (plain).
  - Outputs go to `~/thesis_data/sensitivity_yaw0_0p1/` only.
  - It is scored by `eval/sens_yaw0_eval.py` (evo -a cruise, yaw rms/max, fused headings, bgz, against this pass's own
    1° outputs) into `eval/results/sensitivity_yaw0_0p1/summary.{json,txt}`.
  - The eval script was smoke-tested on the current outputs: it reproduces the trace's stored numbers (e.g. FGO heading
    tex_r1 43.54 m, UKF 0.19 m).

Dry run (`FINAL_FGO_ONLY=1 FINAL_SENS_YAW0=1 … --dry-run`): `eval/diag/initial_sigma_audit/fgo_only_pipeline_dryrun.txt`.
- All five corrections report ok.
- The only UKF jobs in the whole dry run are the 15 labelled sensitivity jobs.

**Runtime estimate** (`eval/diag/initial_sigma_audit/runtime_estimate.{py,txt}`):
- **Method.**
  - Per-job wall times come from `~/thesis_data/batches/final_*/jobs.log`. Each job is classified by its command and
    re-scheduled FGO-only on PAR 6 (longest job first).
  - The other stages come from `final_rerun/pipeline.log`. The run_set_eval stages are scaled by the Phase 4 FGO CPU
    share (0.73).
- **The full re-run took 9.17 h.** The FGO dominates it:
  - L: 3.1 h, a single 186-min job;
  - T: 1.7 h;
  - F: 1.1 h;
  - O: 0.6 h.
- **Estimate for the FGO-only pass:**
  - **≈ 8.3 h** without the opt-in stages;
  - **≈ 8.6 h** with d27item3 / cl_pred;
  - **+ ≈ 0.2 h** for `sens_yaw0` (15 FGO jobs of ~3–6 min and 15 UKF jobs of ~1 min on 6 workers);
  - **total ≈ 8.5–8.8 h.**
  - The saving is small because the UKF was never the long pole.

## E. Open items

1. **The C++ FGO (PARKED until after the 16 Oct freeze).** Steps:
   - build the corrected core in a scratch dir: `cmake -S src/estimators/fgo_cpp -B <scratch>`, then `make
     fgo_cpp_replay`;
   - run `tools/run_equiv.py` on a fresh Python dump: `FGO_DUMP_EVENTS`, heading arm on `fwdplainc_tex_r1` plus one
     baseline bag;
   - then re-install to `~/opt/fgo_cpp`, which changes the installed-binary md5 recorded by the pipeline's provenance;
   - re-run the node's equivalence and the FGO safety tests before ANY real FGO flight (ruling item 4).
   - The installed binaries, and every flown FGO result (S3, the `_v3` set, the FGO safety tests), carry the
     1e-3 rad yaw / 2° roll-pitch priors. Record that as such; no re-fly before the freeze.
2. **Roll/pitch 2° → 5° was applied under ruling item 2 but not individually ruled.** If the user prefers the yaw-only
   change, revert `ROLLPITCH0_SIGMA` to `np.radians(2)` in both cores and loosen check (5). On the C1 bag it changed
   positions by at most 2.7 mm.
3. **The L / V-L results change.** `lc_fgo_replay` takes its pre-anchor state from `FGO.init`, and V-L's yaw σ now comes
   from `cov_prev`. The L stage re-runs in the FGO-only pass (7 jobs, the 3.1 h long pole).
4. **The pipeline runs the MAIN checkout.** Job lines `cd ~/thesis_ws`, so merge this branch into `fwd-camera` (and
   check out `fwd-camera` in `~/thesis_ws`) before launching. Preflight DIEs on a dirty tree and records the md5s.
5. **The UKF gate is the proof of FGO-only.** If it fires, something wrote UKF outputs or a scorer changed. Do not relax
   it; diagnose.
   - Not UKF-gated (by design): band-scored `*_score.json`; Phase 5b (UKF outputs copied from `phase5b_final`); F/f4
     evaluators (the UKF F-arm outputs are reused from the trial directories).
6. **Sensitivity check.**
   - It runs the baseline and heading arms on the 6 fwdplainc bags and on fwdc_tex_r1, and the plain arm on dsn_tex_r1
     (UKF and FGO each, 30 jobs).
   - With 0.1 rad, the on-ground ~+3° plain-wall heading offset is inside 1σ, so the plain-wall heading arms of both
     estimators may accept more ground headings than at 1°. That is exactly what the check is for: report whether any
     conclusion changes.
   - Not a thesis result.
7. **Not done (out of scope / parked):** a measured levelling-scatter prior (the original FGO_DESIGN §8 intent); an
   x, y gauge harmonisation (justified, no information).
8. Before the restatement: the ruling's "previous FGO results become the ablation pair" is
   `eval/results_pre_final2` + `~/thesis_data/pre_final2_trials` (FGO dirs), with
   `final_rerun2/final_old_vs_new.md` from the `compare` stage.
