# Attribution ablation, Step 0: what can be run, at what cost (EXPLORATORY)

**Status: Step 0 only, read-only.** Nothing was replayed, simulated or re-tuned, and no estimator code was changed.
The only things executed were:
- reads of the stored outputs and logs;
- the read-only scorer identity gate (`score_ablation.py --gate`, evo on the STORED trajectories, §2.3);
- `check_step0.py`.

Everything in the ablation is **exploratory**. The design is in `preregistration_draft.md` (DRAFT, not signed off).
Results will go only into `ablation_numbers.md`; `numbers.md` is untouched.

**Conventions.**
- Code citations are `file:line` at commit **`2683ab4`** (HEAD when this was written). `check_step0.py` reads them with
  `git show 2683ab4:<path>`, so later edits cannot shift them.
- GTSAM citations refer to the 4.2.1 source tarball at `~/opt/src/gtsam-4.2.1/`, which was used for the C++ port. The
  replays use the PyPI wheel `gtsam 4.2.1` in `~/venv-fgo` (`pip show gtsam`: Version 4.2.1). This is the same release,
  but the wheel's own source was not inspected, so **library behaviour below is read from the tarball and inferred to be
  identical in the wheel.**
- Units: m for position error, ms for step time, s for wall time (`docs/thesis/units.md`).
- Each derived number is computed from unrounded stored values and rounded once.
- "Inferred" marks anything not read directly from code, a file or a log.

## 0. Which FGO produced the with-heading results

- **Script:** `src/estimators/fgo/fgo_replay.py` (the corridor FGO, Phase 4 arms). It is NOT `room_fgo_replay.py` or
  `lc_fgo_replay.py`, which are the room / loop-closure FGOs of Experiments 2–4.
- **Command of record:** `fgo_replay.py <trial> 0.25 2 <arm>`, with arm `heading` or `baseline`.
  - Committed job list: `batches/phase4_replays.jobs:2-4`.
  - The run that produced the stored values: `~/thesis_data/batches/final_rerun2/final2_phase4.fgo.jobs:1-2`, run by
    `eval/run_jobs_resumable.sh` with `parallel=6`, commit `2cc08a2`. Source: the BEGIN line of
    `~/thesis_data/batches/final2_phase4/jobs.log`.
  - Thread variables at 1: `eval/final_rerun_pipeline.sh:43`.
- **Outputs:** `~/thesis_data/trials/<trial>/fgo_<arm>/` (`fgo_replay.py:57`). They were scored by `eval/phase4_eval.py`
  through `eval/three_way_eval.py`, giving `eval/results/phase4_{fwdc,fwdplainc}_{evo,arms}.json` (2026-10-10 14:06;
  committed in `819caab`).
- **Code changes to `fgo_replay.py` since then** (`b9da351`, `4608637`, `eb629a6`, `0ac0983`) touch only the
  off-by-default events mode (`FGO_EVENTS`, `fgo_replay.py:39-47,69-88`). They should not change a bag replay. That is
  **inferred**, so the pre-registration re-runs the 0.25 s rung as a byte-identity gate (§3, decision D33).
- **Truth is not an input.** `/ground_truth/pose` is read (`fgo_replay.py:105-106`) but used only in:
  - `f_filter_forward`, which is a no-op unless `F_HDG_FROM_CRUISE` or `F_MASK` is set (`measurement_models.py:328-329`);
  - the metrics after the loop (`fgo_replay.py:253-311`).

## 1. Knobs: config/CLI versus code (Step 0 item 1)

| knob | how it is set | without a code change? | evidence |
|---|---|---|---|
| Window length (fixed lag, s) | `argv[2]`. **The CLI default is 1.0 s, not 0.25 s**, so every command must pass the value | **yes** | `fgo_replay.py:125`; passed to `BatchFixedLagSmoother(window, lm)` at `fgo_core.py:87-90` |
| LM iteration cap | `argv[3]`, default 2 → `LevenbergMarquardtParams.setMaxIterations` | **yes** | `fgo_replay.py:126`, `fgo_core.py:88-89` |
| LM tolerances (relative / absolute / error) | not set: GTSAM defaults 1e-5 / 1e-5 / 0 | **no** (needs code) | `fgo_core.py:88-89` sets only the cap; defaults at `NonlinearOptimizerParams.h:42-44` |
| Iteration count actually used | not logged: `smoother.update(...)` returns a `Result` that is discarded | **no** (needs code to log) | `fgo_core.py:193` |
| Keyframe rate | `kf_dt = 1/30` s (30 Hz), hard-coded | **no** (needs code) | `fgo_replay.py:128` (and the cadence `t_kf_next += fgo.kf_dt`, `:216`) |
| One-keyframe window | any window < 1/30 s, via `argv[2]` | **yes**, and it behaves as intended (§1.2) | `FixedLagSmoother.cpp:104-111`, `BatchFixedLagSmoother.cpp:82-106` |
| Robust loss | env `F_ROBUST=huber:k` or `cauchy:k`, with `F_TAG` required | **partly**: heading factor only, and it also REMOVES the heading χ² gate (§1.1) | `fgo_replay.py:129`, `fgo_core.py:100-106`, `measurement_models.py:317-323` |
| Whole-flight batch | env `F_BATCH=1`, with `F_TAG` required | **yes**, with caveats (§3.3) | `fgo_replay.py:132,314-334` |
| Output location | env `FGO_OUT_ROOT` → `<root>/<trial>/fgo_<arm>[_<F_TAG>]/`. Window and cap are NOT in the folder name | **yes**: one root per rung | `fgo_replay.py:57` |

### 1.1 Robust (Huber) loss, by factor type

| factor type | where its noise model is built | robust model switchable without code? |
|---|---|---|
| Forward-camera **heading** | `fgo_core.py:101`; robust wrap at `:102-106` when `fwd_robust` is set | **Yes, but coupled:** `F_ROBUST` sets `fwd_gate = inf` (`fgo_replay.py:129`), so the runnable variant is "robust kernel *replacing* the χ² gate", not "Huber vs Gaussian with the gate kept". This is the F1/F4 design (`batches/f4_replays.jobs:4`, Cauchy 2.385). The gate-kept variant needs code. |
| Forward-camera yaw rate | `fgo_core.py:107-108` (fwdc only; `heading_yawrate` arm) | no; also not on the `heading` arm |
| Downward flow | `fgo_core.py:97` (σ 0.25, Gaussian) | **no** (needs code). FGO_DESIGN planned Huber k = 1.345 on the flow factor (`FGO_DESIGN.md:476-478`); it was never implemented |
| Range | `fgo_core.py:98` (σ 0.5) | **no** (needs code) |
| Yaw cap (zero-innovation pseudo-yaw) | `fgo_core.py:99` (σ 0.5) | **no** (needs code) |
| IMU (`CombinedImuFactor`) | preintegration covariance `fgo_core.py:25-36` | **no** (needs code; a robust IMU factor is not part of any design) |

- On the control (`baseline` arm) there are no heading factors, so the `F_ROBUST` switch is **inert** there. The Huber
  rungs therefore run on the 6 heading bags only.
- `F_ROBUST` requires `F_TAG` (`measurement_models.py:321-322`). The output folder then becomes
  `fgo_heading_<F_TAG>` (`fgo_replay.py:57`).
- Huber k: 1.345 is proposed, the standard 95%-efficiency constant on whitened residuals (`FGO_DESIGN.md:476-478`).
  It is stated, not tuned.
- Stored prior evidence (context only, no evo -a stored): `fgo_heading_F1cauchy_2_385` exists on all 6 bags
  (2026-10-10 14:36). It is a robust (Cauchy 2.385, gate off) 0.25 s run. Its yaw metrics in
  `eval/results/f1_test.json` (key `<trial>.FGO_robust`) differ strongly from the hard-gated FGO on plain walls: yaw
  RMS 0.28–0.42° against 3.07–3.41°. So P3 "within the band" may well fail on plain walls (open question Q4).

### 1.2 One-keyframe window: it behaves as intended, as a two-keyframe iterated filter

**Read from source:**
- `BatchFixedLagSmoother::update` (`BatchFixedLagSmoother.cpp:53-108`) works in this order:
  1. inserts the new factors and values;
  2. takes `current_timestamp = getCurrentTimestamp()`, the newest key time (`FixedLagSmoother.cpp:95-101`);
  3. takes `marginalizableKeys = findKeysBefore(current_timestamp - smootherLag_)` (`:82-86`);
  4. **optimises** (`:93-99`);
  5. **then marginalises** (`:101-106`).
- `findKeysBefore` returns the keys with timestamp strictly less than its argument (`lower_bound`,
  `FixedLagSmoother.cpp:104-111`).
- Keyframe k has timestamp t_k (`fgo_core.py:192`). Keyframes are at least 1/30 s apart (`fgo_replay.py:189-216`; a
  skipped keyframe, `fgo_core.py:154-155`, only widens the gap).

**Consequence:**
- For any window W in [0, 1/30) s, step k optimises over keyframes k−1 and k together (`CombinedImuFactor` links them,
  `fgo_core.py:161`).
- It then marginalises k−1, leaving one keyframe. Every W in that interval gives the same key sets, so the
  pre-registration uses W = 0.01 s (decision D29).
- This is not a degenerate case. It is the shortest lag the solver supports: an iterated, two-keyframe filter with
  re-linearisation of k−1. A strict single-state filter (no k−1 in the solve) is not available, because the IMU factor
  always spans two keyframes.
- **Not tested** (Step 0 runs nothing).

**Window-independent parts.** The heading χ² gate and the yaw-cap variance gate use a separate "gate-only" two-keyframe
covariance recursion (`fgo_core.py:271-342`). Its prior is the previous keyframe's filtering covariance, not the
smoother's window. The gates therefore see the same structure at every window. They differ only through the
linearisation point, which the window and iterations do change.

### 1.3 "Iteration count" and "converged"

- The cap is `argv[3]`. The LM loop runs while `iterations < maxIterations` and `checkConvergence(...)` with the default
  tolerances fails (`BatchFixedLagSmoother.cpp:301-304`).
- One "iteration" can contain several damped solves: the lambda search at `:224-297`, inside the do-while at `:214-304`, with error-decrease acceptance at
  `:259` and the upper-bound exit at `:283`.
- Each step is warm-started from the previous window solution (`fgo_core.py:84-86`).
- **"Converged" is defined operationally (decision D30): cap 100, the GTSAM default `maxIterations`
  (`NonlinearOptimizerParams.h:41`), so the default 1e-5 tolerances stop the loop.**
  - Whether 100 ever binds cannot be confirmed without code, because the iteration count is discarded
    (`fgo_core.py:193`).
  - Prior evidence that 2 is near-converged at 0.25 s: METHODOLOGY:722-726 (corridor, no heading, pre-correction code:
    cap 2 vs full LM, RMS 0.029 m) and E4 (§4).
- "1 iteration" (cap 1) means one accepted (or given-up) LM step, possibly after several damped solves.

## 2. Marginalisation and verified gap values

### 2.1 What happens to states leaving the window (Step 0 item 2)

**A marginal prior IS carried forward, as linear container factors.**
- `marginalize()` (`BatchFixedLagSmoother.cpp:310-345`) does the following:
  1. collects every factor touching a marginalised key (`:318-331`);
  2. computes `CalculateMarginalFactors(removedFactors, theta_, keys, ...)` (`:334-335`): it linearises those factors at
     the current `theta_` and partially eliminates the old keys (`:423-437`, `:410-421`);
  3. wraps the result in `LinearContainerFactor`s (`LinearContainerFactor::ConvertLinearGraph`,
     `LinearContainerFactor.cpp:210-218`);
  4. removes the old factors and keys (`:338-341`);
  5. inserts the marginal factors (`:344`).
- When a key carried by an earlier marginal factor is itself later marginalised, that factor is again among the
  `removedFactors`. The information therefore chains forward; nothing is dropped. This is read from the code; the chain
  over a flight is inferred.
- **The marginal's linearisation point is frozen** at the `theta_` of the step that created it.
  `LinearContainerFactor::error` evaluates the stored linear factor at `localCoordinates` from that point
  (`LinearContainerFactor.cpp:77-89`).
- **Inferred (read, not tested):** the "enforce consistency" branch (first-estimates Jacobians) is inert in 4.2.1.
  - `enforceConsistency_` defaults to true (`BatchFixedLagSmoother.h:37-38`), but `linearValues_` is never inserted
    anywhere in `BatchFixedLagSmoother.{h,cpp}`. It is only declared (`.h:140`), read (`.cpp:189-190,268-270`) or erased
    (`.cpp:164-165`).
  - So the keys attached to a marginal factor re-linearise freely in later steps, while the marginal itself stays
    linear about its creation point.
- **Project side:** the FGO never adds or removes marginal priors itself. Each keyframe calls `smoother.update(g, vals,
  timestamps)` and `calculateEstimate()` (`fgo_core.py:192-194`). The only explicit restart is `reanchor()`
  (`fgo_core.py:229-269`), used by the room/tag experiments, not by `fgo_replay.py`.

### 2.2 The user's gap values against numbers.md (verified; no numerical discrepancy)

Metric: evo -a (cruise), arm `heading` (with heading), textured floor. Stored source:
`eval/results/phase4_<ds>_arms.json`, key `<trial>.<EST>_heading.evo.ate_a_cruise."+0.00"` (identical in
`phase4_<ds>_evo.json`). Values are given as stored (6 dp, no further rounding).

| bag | FGO (m) | UKF (m) | UKF − FGO (m, 3 dp) | numbers.md |
|---|---|---|---|---|
| fwdc_tex_r1 | 0.056585 | 0.127393 | 0.071 | `numbers.md:291` (UKF 0.13 / 0.13 / 0.14; 0.127 / 0.134 / 0.137), `:292` (FGO 0.06 / 0.06 / 0.06) |
| fwdc_tex_r2 | 0.062506 | 0.134225 | 0.072 | same |
| fwdc_tex_r3 | 0.063294 | 0.137458 | 0.074 | same |
| fwdplainc_tex_r1 | 0.149586 | 0.187642 | 0.038 | `numbers.md:294` (UKF 0.19 / 0.15 / 0.25), `:295` (FGO 0.15 / 0.09 / 0.22; 0.150 / 0.094 / 0.221) |
| fwdplainc_tex_r2 | 0.094237 | 0.151479 | 0.057 | same |
| fwdplainc_tex_r3 | 0.221451 | 0.249505 | 0.028 | same |

- **Line-textured walls (`fwdc`):** the user's "FGO 0.06 m vs UKF 0.13–0.14 m" matches exactly.
- **Plain walls (`fwdplainc`):** the user's "0.09–0.22 vs 0.15–0.25 m" matches exactly. The C0 row
  (`numbers.md:299`) gives the same values and the plain-wall margin 0.03–0.06 m.
- **No numerical discrepancy.** Three points of scope belong with the numbers:
  1. All six are **checkerboard-floor (`_tex_`) bags**, which the user's text does not say.
  2. On plain walls over the checkerboard floor, the heading measurement **failed Phase 3 validation (0/3)**. The heading
     benefit there is conditional and not claimed (`numbers.md:301`).
  3. At a 0.1 rad initial-yaw σ, the plain-wall FGO–UKF margin shrinks to 0.01–0.03 m (`numbers.md:299`).

  The plain-wall half of the gap is therefore a fragile quantity.

**Control (no heading, arm `baseline`):** key `<trial>.<EST>_baseline.evo.ate_a_cruise."+0.00"`, identical to
`rerun_<ds>_evo.json` `trials.<trial>.est.{FGO,UKF}`.

| bag | FGO (m) | UKF (m) | UKF − FGO (m, 3 dp) | numbers.md |
|---|---|---|---|---|
| fwdc_tex_r1 | 4.467123 | 4.959532 | 0.492 | `:270` (FGO 4.47 / 2.26 / 4.54), `:271` (UKF 4.96 / 1.78 / 4.96, DIAGNOSTIC) |
| fwdc_tex_r2 | 2.262089 | 1.783411 | −0.479 | same |
| fwdc_tex_r3 | 4.544273 | 4.963794 | 0.420 | same |
| fwdplainc_tex_r1 | 4.536324 | 5.023202 | 0.487 | `:273` (FGO 4.54 / 4.52 / 4.74), `:274` (UKF 5.02 / 11.19 / 10.82; r2, r3 take-off kick) |
| fwdplainc_tex_r2 | 4.517620 | 11.194393 | 6.677 | same |
| fwdplainc_tex_r3 | 4.740214 | 10.818971 | 6.079 | same |

- The control has no consistent FGO–UKF ordering on `fwdc`.
- The large `fwdplainc` r2 and r3 UKF values are the UKF's residual take-off kick (`numbers.md:230`, `:274`).
- EKF3 (stored, not in scope): `phase4_<ds>_arms.json` `<trial>.EKF3.ate_a_cruise."+0.00"`, `numbers.md:269,272`.

### 2.3 Scorer identity gate (done, read-only)

`eval/three_way_eval.py` cannot score a new output root:
- `TRIALS_DIR` is hard-coded (`three_way_eval.py:45`);
- `--est` is `subdir/file` under the trial folder (`:170-171`).

`docs/thesis/ablation/score_ablation.py` is a read-only analysis wrapper. It is not estimator code.
- It reuses `three_way_eval`'s own `cruise_window`, `crop`, `evo_ape_a` and `write_tum`.
- It never calls `ekf3_tums` (`:71-100`), which can write into a trial folder.
- **Gate result: 24/24 EQUAL.** Scoring the stored `{fgo,ukf}_{heading,baseline}` outputs of the 6 bags reproduces every
  stored value exactly (`scorer_gate.json`, `n_equal`).

## 3. Cost (Step 0 item 3)

### 3.1 Stored step and wall times at 0.25 s, cap 2 (DIAGNOSTIC: workstation Python, parallel = 6)

- Per-keyframe step times are from `t_keyframe_ns` in `~/thesis_data/trials/<t>/fgo_<arm>/timing_and_fwd.npz`.
  Medians equal `phase4_<ds>_arms.json` `<t>.FGO_<arm>.timing.fgo_keyframe.median_ms`.
- Wall times are from `~/thesis_data/batches/final2_phase4/jobs.log` DONE lines.

| bag | arm | keyframes | median / p95 step (ms) | sum of steps (s) | job wall (s) |
|---|---|---|---|---|---|
| fwdc_tex_r1 | heading | 10118 | 34.23 / 43.20 | 324.5 | 330 |
| fwdc_tex_r2 | heading | 10160 | 35.28 / 47.34 | 338.1 | 344 |
| fwdc_tex_r3 | heading | 10083 | 35.66 / 43.57 | 323.8 | 331 |
| fwdplainc_tex_r1 | heading | 10097 | 21.51 / 37.35 | 224.0 | 230 |
| fwdplainc_tex_r2 | heading | 10045 | 21.84 / 37.83 | 226.5 | 233 |
| fwdplainc_tex_r3 | heading | 10079 | 20.03 / 34.13 | 208.7 | 214 |
| fwdc_tex_r1 | baseline | 10118 | 19.37 / 21.96 | 197.9 | 203 |
| fwdc_tex_r2 | baseline | 10160 | 20.32 / 32.09 | 222.2 | 231 |
| fwdc_tex_r3 | baseline | 10083 | 20.01 / 24.82 | 209.1 | 216 |
| fwdplainc_tex_r1 | baseline | 10097 | 19.92 / 22.66 | 205.3 | 211 |
| fwdplainc_tex_r2 | baseline | 10045 | 19.40 / 23.26 | 200.3 | 206 |
| fwdplainc_tex_r3 | baseline | 10079 | 19.74 / 22.92 | 199.8 | 208 |

- Sum of job walls: 6 heading bags **1682 s**; 6 baseline bags **1275 s**; one 0.25 s rung on all 12 bags **2957 s**.
- The step time is dominated by the per-keyframe solve, not by bag reading: the sum of steps is 96–98% of the job wall.
- The heading step is about 15 ms longer than the baseline step on `fwdc`. Part of that is the window-independent heading
  gate: an inverse of the 30×30 information matrix per heading (`fgo_core.py:310`).
- These were measured **under parallel = 6** load. `numbers.md:447` (37–40 ms, an earlier post-fix measurement) is a
  different run. The table above is the stored final re-run.

### 3.2 Projection per rung (planning figures, not results)

**Window scaling.** E4 driver wall means (room, serial) are 141.3 / 486.3 / 964.8 s at 0.25 / 1 / 2 s
(`e4_results.md:55,57,58`). That gives ratios ×3.44 (1 s) and ×6.83 (2 s). FGO_DESIGN's corridor step times give the
same shape: 96 / 48 / ~29 ms at 1.0 / 0.5 / 0.25 s (`FGO_DESIGN.md:580-581`).

**The projection is an upper bound (inferred), for three reasons:**
- the whole job wall is scaled, including the window-independent gate cost;
- the stored walls were measured under 6-way load;
- the one-keyframe rungs are budgeted at the 0.25 s wall, although their solve is smaller.

The converged rungs are budgeted at ×2, an assumption: E4 measured cap 10 ≈ ×1.03 cap 2 (146.2 vs 141.3 s,
`e4_results.md:55,60`).

| rung | bags | basis | projected wall (s) |
|---|---|---|---|
| r0: 0.25 s, cap 2 (identity gate + serial timing) | 12 | 1 × 2957 | 2957 |
| r1: 1 keyframe, cap 1 | 12 | ≤ 1 × 2957 | 2957 |
| r2: 1 keyframe, cap 2 (proposed extra, decision D31) | 12 | ≤ 1 × 2957 | 2957 |
| r3: 1 keyframe, cap 100 ("converged") | 12 | ≤ 2 × 2957 | 5914 |
| r4: 1 s, cap 2 | 12 | 3.44 × 2957 | 10177 |
| r5: 2 s, cap 2 | 12 | 6.83 × 2957 | 20190 |
| r6: 0.25 s, cap 2, Huber (gate off) | 6 heading | 1 × 1682 | 1682 |
| r7: 1 keyframe, cap 100, Huber (gate off) | 6 heading | ≤ 2 × 1682 | 3364 |
| **Ladder total (serial)** | | | **50198 s = 13.9 h** |
| without r2 | | | 47241 s = 13.1 h |
| without the control at 1 s and 2 s (open question Q5) | | | 37105 s = 10.3 h |
| optional full batch (`F_BATCH`, §3.3) | 12 | stored ≈ 2977 s/bag | 35724 s = 9.9 h |

**Against the ~1 day cap:**
- The ladder fits serially (13.9 h, upper bound).
- Ladder plus full batch is 23.9 h, which leaves no margin. **The full batch is not cheap** (decision D34).

**Scheduling** (decision D28):
- Rule 6 requires serial only for timing hypotheses. P1–P3 are accuracy predictions, so rule 6 would allow 4 in parallel.
- But "compute per step" is a requested metric, and E4 noted contamination under load (`e4_results.md:37-44`).
- The stored corridor medians were measured at parallel = 6.
- **Proposed: all FGO rungs serial**, through `heavy.py`. Its BUILD_LOCK makes it serial anyway
  (`src/estimators/fgo_cpp/tools/heavy.py:27-37,55`); nice 19 and thread variables at 1 (`:76-77`).
- Step times are then clean DIAGNOSTIC numbers, and the total still fits the cap.
- Scoring (evo) is minutes and may run in parallel.

**Machine** (2026-10-24 11:16, `machine_step0.txt`: `free -g`, `nproc`):
- 12 threads;
- 15 GB RAM, about 6 GB available (9 GB in use);
- swap 3 GB, 2 GB used.

A batch run's peak memory was never logged, so `F_BATCH` runs, if any, must also be serial.

### 3.3 Full batch on the corridor recordings: exists, feasible, not cheap, and not like-for-like

- **It exists:** `F_BATCH=1` (with `F_TAG`). It records every factor the live smoother received (`fgo_core.py:134-136`,
  `:195-208`), then runs one LM solve, 50 iterations max, relative tolerance 1e-6 (`fgo_replay.py:315-334`). The output
  is `fgo_batch_traj.tum`.
- **Stored cost** (`~/thesis_data/batches/final2_F/logs/f2f_fwdc_tex_r{1,2,3}.log`, `[batch]` lines, `fwdc` heading with
  `F_MASK=30/30`):
  - batch solve 2540.1–2766.5 s, 3 iterations;
  - job walls 2823–3062 s (`final2_F/jobs.log`);
  - live steps were inflated by the recording (median 22.9–24.0 ms against 19.4–20.3 ms), because the recording sits
    inside the timed region (`fgo_core.py:195-208` within `fgo_replay.py:191-199`).
- **Caveats:**
  - it is hindsight (non-causal), so it is not like-for-like with the UKF filter;
  - it contains only the heading factors that the **live** gate accepted;
  - it contains every live yaw-cap pseudo-measurement, anchored to the live predicted yaw, which is circular per
    `fgo_core.py:196-199`. `batch_drop_yawcap` exists but `fgo_replay.py` cannot set it, so a clean batch needs code.
- **Recommendation:** not run by default, and kept out of P1–P3. Listed for the user to decide (Q3).

## 4. What E4 already answered (Step 0 item 4)

E4 (`docs/thesis/tier1/e4_results.md`; `numbers_tier1.md` §E4, from line 376) covered the following:
- **Setting:** room world, 12 tag flights T_A–T_D, `room_fgo_replay.py --no-batch`, live track, **no forward heading**,
  windows 0.25 / 0.5 / 1 / 2 / 5 s.
- **Accuracy null:** H-E4.3 FAIL 7/12 (`e4_results.md:16`). Live RMSE moves by at most a few tenths of a mm on the A and
  B flights. The largest changes are on the D flights, both ways, up to 0.0043321 m (`e4_results.md:154-156,175`).
- **LM cap:** cap 2 vs cap 10 is converged at every window on T_A_r1 and T_D_r1. The largest RMS reading is 0.0009 m
  against the 0.029 m flag (`e4_results.md:20-21`). Cap 10 cost about the same as cap 2. Iteration counts were not logged
  (`e4_results.md:159-161`).
- **Step time** (serial, after the anchor): 14.35–15.13 ms at 0.25 s and 278.25–303.36 ms at 5 s (`e4_results.md:23-24`).
- **Earlier corridor evidence** (no heading, `dsn_tex_r1`, pre-correction code `08bc2eb`):
  - evo -a (cruise) 4.47 / 4.44 / 3.72 m at 1.0 / 0.5 / 0.25 s;
  - cap 2 vs full LM at 0.25 s, RMS 0.029 m (METHODOLOGY:709-726).

**What remains informative here:**
1. **With heading.** E4 had no forward heading. The heading factor is a strong absolute yaw input that a longer window
   could propagate back into bias and attitude states. The window-null result does not transfer by default. The 1 s and
   2 s rungs with heading are the gap-filling rungs.
2. **Below 0.25 s.** E4's shortest window was 0.25 s. The one-keyframe rungs (r1–r3, r7) are new.
3. **Iterations at one keyframe.** E4 compared cap 2 vs 10 only at ≥ 0.25 s, in the room, without heading. Cap 1 / 2 /
   100 at one keyframe is new.
4. **Robust kernel.** E4 used none.
5. **Least informative.** The no-heading control at 1 s and 2 s on the corridor is the setting closest to E4 and to
   METHODOLOGY:709-713. A null is expected there. It is kept as the user's P1 control; dropping it saves 3.6 h (Q5).
6. **Not proposed.** 5 s (E4's null is strongest there) and a keyframe-rate sweep (needs code).

## 5. Locked constants (read from the current configuration, not assumed)

| constant | value | where |
|---|---|---|
| FGO keyframe period | 1/30 s (30 Hz) | `fgo_replay.py:128` |
| FGO window / LM cap of record | 0.25 s / 2 (CLI); code defaults 1.0 / 2 | `final2_phase4.fgo.jobs:1-2`, `batches/phase4_replays.jobs:2-4`; `fgo_replay.py:125-126` |
| FGO IMU noise (continuous) | acc 1.53125e-3, gyro 2.8125e-6, bias acc 5.0e-6, bias gyro 1.25e-8, integration 1e-8, biasAccOmegaInit 0 | `fgo_core.py:27-31,35` |
| FGO measurement σ | flow 0.25 rad/s, range 0.5 m, yaw cap 0.5 rad | `fgo_core.py:97-99` |
| Forward heading σ_ψ / yaw rate σ_ω | fwdc 0.148° / 0.162°/s; fwdplainc 0.126° / none | `measurement_models.py:191-192` |
| Forward gate | χ² 9.0 | `measurement_models.py:186` |
| Yaw cap check / gate | every 0.14 s / trace > 0.04 rad² | `fgo_core.py:51-52` |
| Initial σ (both estimators) | yaw 1°, roll/pitch 5°, gyro bias 0.043633 rad/s, accel bias 0.2 m/s² | `fgo_core.py:39-48` |
| UKF prediction | `TARGET_DT 0.0125` rounded up to whole IMU periods (`DT_STEP`); EKF3 NSE values 0.015 / 0.35 / 0.001 / 0.02 | `ukf_replay.py:93-95`; `ukf_core.py:21,24-26` |
| UKF flow gate / limit | 300 per axis / two-sided 2.5 rad/s | `ukf_core.py:44,293-295` |

None of these change in any rung. Only window, cap and (r6/r7) the heading kernel change.

## 6. Needs code: stopped

The following were requested or implied, and need a code change. None was made. Each would be a separate, signed-off
change.

| item | why it needs code | minimal change |
|---|---|---|
| Huber on the heading factor **with the χ² gate kept** (a pure kernel swap) | `F_ROBUST` forces `fwd_gate = inf` (`fgo_replay.py:129`) | a separate env switch that wraps the heading noise (`fgo_core.py:102-106`) but leaves `fwd_gate = FWD_CHI2_GATE` |
| Huber on **flow / range / yaw-cap / yaw-rate** factors | noise models are fixed Gaussians (`fgo_core.py:97-99,107-108`) | env switch wrapping each in `noiseModel.Robust.Create(Huber(1.345), base)`; flow-only per `FGO_DESIGN.md:476-478` |
| **Keyframe rate** sweep | `kf_dt = 1/30` hard-coded (`fgo_replay.py:128`) | expose `kf_dt` as an argument or env |
| **LM tolerances**, and **confirming** convergence (iteration counts) | only `setMaxIterations` is set (`fgo_core.py:88-89`); the `Result` is discarded (`:193`) | keep `r = self.smoother.update(...)` and log `r.iterations`, `r.error` |
| **Clean full batch** (without the live yaw-cap anchors) | `batch_drop_yawcap` exists (`fgo_core.py:196`) but `fgo_replay.py` never sets it | env switch → `fgo.batch_drop_yawcap = True` |
| Strict single-state window (no k−1 in the solve) | the IMU factor always spans k−1 and k (`fgo_core.py:161`); the solver optimises before it marginalises (`BatchFixedLagSmoother.cpp:93-106`) | not a small change; not proposed |

The rungs that remain runnable without code are r0–r7, plus the optional `F_BATCH` (with the caveats in §3.3).

## 7. Decisions taken (logged in `docs/thesis/tier1/decisions_log.md` as "decisions_log D28"–"D36")

These numbers are the decisions_log series. They are distinct from the earlier METHODOLOGY ruling also called "D28"
(closed loop, `numbers.md:479,501`).
- D28: all FGO rungs serial.
- D29: one-keyframe lag 0.01 s.
- D30: "converged" = cap 100.
- D31: extra rung r2 proposed.
- D32: the Huber rungs = `F_ROBUST=huber:1.345`, gate off.
- D33: r0 identity gate.
- D34: full batch not by default.
- D35: noise band = per-wall-type range of the three thesis FGO values, descriptive.
- D36: in the interpretation table, "the gap persists" needs R(r3) within the band of 1, not just P2's R ≥ 0.5.

## 8. Open questions (for the user; no interactive questions were asked)

- **Q1. P2 scope.** The draft scores P2 on `fwdc` (3/3 needed). It reports `fwdplainc` descriptively: there the
  between-repeat band (0.127 m) exceeds the gaps (0.028–0.057 m), the heading failed Phase 3, and the margin is fragile
  to the initial yaw σ. Is that acceptable, or should P2 require 6/6?
- **Q2. Extra rung r2** (one keyframe, cap 2; 49 min). Without it, "0.25 s cap 2 → one keyframe converged" changes the
  window and the iteration count together, so P2 could not be attributed to the window alone. Keep it?
- **Q3. Full batch.** It is feasible (≈ 9.9 h serial), not cheap, hindsight-only, and includes circular yaw-cap anchors
  unless code changes. Drop it (default), or run it as a descriptive extra?
- **Q4. Huber rungs.** The runnable form replaces the heading gate with the kernel (`F_ROBUST`). P3 then measures
  "kernel instead of gate", not "Huber vs Gaussian". Stored F1 yaw metrics suggest a large difference on plain walls.
  Accept this form, or authorise the one-switch code change for gate-kept Huber?
- **Q5. Control at 1 s and 2 s** (3.6 h). Without heading, E4 and METHODOLOGY:709-713 already show window independence.
  Keep it as the P1 control (default), or drop it?
- **Q6. Huber k.** The draft uses 1.345 (FGO_DESIGN's stated constant). F1/F4 used Cauchy 2.385. Use one Huber value
  only (default), or also Cauchy 2.385 to match F1?
- **Q7. P2 pass vs "the gap persists".** The user's P2 passes at R ≥ 0.5. The draft's interpretation table reads "not explained by the window" only when R(r3) is within the band of 1 (R ≥ 1 − band/gap, about 0.91 on `fwdc`). A pass between 0.5 and that reads "most of the gap remains; the window accounts for (1 − R)" (D36). Accept?
