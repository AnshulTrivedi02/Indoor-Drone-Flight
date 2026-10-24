# Attribution ablation: pre-registration

# DRAFT — NOT SIGNED OFF — DO NOT RUN

**EXPLORATORY.** This is not a thesis hypothesis test. All three predictions are **descriptive**: n = 3 per wall type,
and the replays are deterministic, so there is no inferential band (§6). Each prediction still carries a pass rule fixed
here, so no verdict is chosen after the data are seen.

**Rules:**
- Standing decision rules 1–8 (`docs/thesis/tier1/decisions_log.md`) apply.
- Lock: 2026-11-04 23:59 AEDT.
- Results go only into `ablation_numbers.md`; `numbers.md` is untouched.
- Every number is traced to a json key, and rounded once.
- Step 0 evidence (file:line for every code claim): `step0_report.md`.
- Decisions: decisions_log D28–D35.

## 1. Question and scope

**Question.** Which of window length, iteration count and robust loss explains the with-heading gap between the FGO and
the UKF?
- Gap = UKF − FGO, evo -a (cruise), arm `heading`, textured floor.
- **Line-textured walls (`fwdc`):** gaps 0.071 / 0.072 / 0.074 m.
- **Plain walls (`fwdplainc`):** gaps 0.038 / 0.057 / 0.028 m.
- Source: `step0_report.md` §2.2.

**Out of scope:**
- UKF vs EKF3 (no ordering is claimed there).
- Any new flight, any estimator code change, any tuning.
- Any truth input to an estimator.

**Fairness is unchanged:**
- same models and noise values;
- the shared flow model;
- the locked constants of `step0_report.md` §5, read from the code.

Only the FGO's window, LM cap and (r6/r7) heading kernel change.

## 2. Recordings

**With heading** (arm `heading`, 6 bags): `fwdc_tex_r1`, `fwdc_tex_r2`, `fwdc_tex_r3`, `fwdplainc_tex_r1`,
`fwdplainc_tex_r2`, `fwdplainc_tex_r3`.

**Control** (arm `baseline`, no forward factors): the same 6 bags.

**Inputs, read only:**
- `~/thesis_data/trials/<t>/{bag, imu_gaps.json, fwd_meas/meas_frozen.npz}`;
- `eval/results/fwd_calibration.json`.

## 3. Rungs (FGO only; every command uses existing flags)

Common prefix for every job:
```
cd ~/thesis_ws && MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 FGO_OUT_ROOT=$HOME/thesis_data/ablation/<rung> \
  timeout <min(48 h, time to lock)> python3 src/estimators/fgo_cpp/tools/heavy.py --wait-s 86400 "ablation <rung> <t> <arm>" -- \
  $HOME/venv-fgo/bin/python src/estimators/fgo/fgo_replay.py <t> <W> <cap> <arm>
```
`heavy.py` sets `OMP_NUM_THREADS = OPENBLAS_NUM_THREADS = 1` and nice 19, and takes BUILD_LOCK, so jobs run one at a
time. The arm is always given explicitly (`heading` or `baseline`, never the legacy no-arm form), so the outputs are
like-for-like with the stored `fgo_<arm>/`.

| rung | `<rung>` folder | W (s) | cap | arms | extra env | output |
|---|---|---|---|---|---|---|
| r0 (thesis config; identity gate + serial timing) | `r0_w0.25_lm2` | 0.25 | 2 | heading, baseline | — | `<root>/<t>/fgo_<arm>/` |
| r1 one keyframe × 1 iteration | `r1_kf1_lm1` | 0.01 | 1 | heading, baseline | — | same |
| r2 one keyframe × cap 2 (proposed extra; Q2) | `r2_kf1_lm2` | 0.01 | 2 | heading, baseline | — | same |
| r3 one keyframe × converged | `r3_kf1_lm100` | 0.01 | 100 | heading, baseline | — | same |
| r4 1 s | `r4_w1_lm2` | 1 | 2 | heading, baseline | — | same |
| r5 2 s | `r5_w2_lm2` | 2 | 2 | heading, baseline | — | same |
| r6 Huber, 0.25 s | `r6_w0.25_lm2_huber` | 0.25 | 2 | heading | `F_TAG=H1345 F_ROBUST=huber:1.345` | `<root>/<t>/fgo_heading_H1345/` |
| r7 Huber, one keyframe converged | `r7_kf1_lm100_huber` | 0.01 | 100 | heading | `F_TAG=H1345 F_ROBUST=huber:1.345` | same |
| r6s (zero machine cost) | — | 0.25 | 2 | heading | stored `fgo_heading_F1cauchy_2_385` (Cauchy 2.385, gate off) | scored read-only from `~/thesis_data/trials/<t>/` |

Notes on the rungs:
- **W = 0.01 s means "one keyframe".** Any W < 1/30 s keeps only keyframe k after the step. The solve itself covers k−1
  and k (`step0_report.md` §1.2). 0.01 avoids a float-equality edge at 1/30 (D29).
- **cap 100 means "converged".** It is the GTSAM default `maxIterations`, and the default 1e-5 tolerances stop the loop.
  Iteration counts are not logged, so whether 100 ever binds is not confirmed (D30).
- **r6 and r7 are "robust kernel replacing the χ² gate".** `F_ROBUST` sets the heading gate to infinity
  (`fgo_replay.py:129`). They are NOT a pure Huber-vs-Gaussian swap; that needs code (§11). They run on heading bags
  only, because on the control the switch is inert.
- **Full batch (`F_BATCH`) is not in the ladder** (D34, Q3). If the user adds it, it is descriptive only, serial, with the
  `step0_report.md` §3.3 caveats.

**Order (serial):**
1. r0 on all 12, then the identity gate (§9).
2. Then r3 → r2 → r1 → r7 → r6 → r4 → r5. The key rung comes first and the longest rungs last.

Within each rung the order is: heading `fwdc_tex_r1..r3`, `fwdplainc_tex_r1..r3`, then baseline in the same order.

**Projected wall:** 50198 s = 13.9 h serial, an upper bound (`step0_report.md` §3.2), against the ~1 day cap.

## 4. Outputs: nothing stored is overwritten

- Every replay writes only to `~/thesis_data/ablation/<rung>/<t>/fgo_<arm>[_H1345]/`: `FGO_OUT_ROOT`,
  `fgo_replay.py:57`. Nothing is written under `~/thesis_data/trials`.
- A job refuses to start if its output folder exists and is non-empty.
- On a retry, the partial folder is moved to `<dir>.CRASHED_try1.<epoch>`, never deleted.
- **Driver and state:** a stage2f-style serial driver (`~/thesis_data/tier1/stage2f/driver.sh` is the model). Its job
  scripts, `timing.tsv` (job, start, end, wall, rc, try, load average at start and end, outcome) and logs all live under
  `~/thesis_data/ablation/`.
  - **NOT `eval/run_jobs_resumable.sh`.** It writes its state to `~/thesis_data/batches/<name>/` (`:17`), which the
    checksum guard covers, so a verify would then fail.
  - The driver is written after sign-off. It is analysis tooling, not estimator code.
- **Scores:** `~/thesis_data/ablation/scores/<rung>_<arm>.json`, written by `docs/thesis/ablation/score_ablation.py`.
  Tables go to `docs/thesis/ablation/ablation_numbers.md`.

## 5. Metrics

1. **Position: evo -a (cruise), m.** The thesis metric, computed by `score_ablation.py`:
   - it reuses `eval/three_way_eval.py`'s `cruise_window` / `crop` / `evo_ape_a`;
   - the window is the pinned cruise window, from the stored `~/thesis_data/trials/<t>/ukf/ground_truth.tum`:
     ground-truth horizontal speed, 0.42 s centred boxcar, > 0.30 m/s, largest contiguous run (`eval/cruise_window.py`);
   - the estimate and its own `ground_truth.tum` are cropped to `[t0, t1]`;
   - then `evo_ape tum ref est --t_max_diff 0.05 -a` (Umeyama SE(3), no scale), RMSE.

   The scorer reproduced all 24 stored FGO/UKF values exactly (`scorer_gate.json`). The value is read at full precision
   and rounded once, to 3 dp, in `ablation_numbers.md`.
2. **Compute per step, ms (DIAGNOSTIC):** median and p95 of `t_keyframe_ns` (`timing_and_fwd.npz`, `fgo_replay.py:191-199,230`).
   - It covers everything inside `fgo.keyframe()`: the smoother update, the estimate, and the window-independent
     gate-only recursion.
   - Measured serially (D28): workstation Python, 1 thread, nice 19.
   - It says nothing direct about the flight controller. There is no timing prediction.
3. **Descriptive context:**
   - headings valid / fused (`fwd_stats.json`);
   - keyframe failures (`[warn] keyframe` lines in the job log);
   - finite trajectory;
   - run wall time.

**References, stored, never re-run:**
- UKF and EKF3 rows: `eval/results/phase4_<ds>_arms.json`
  (`<t>.UKF_<arm>.evo.ate_a_cruise."+0.00"`, `<t>.EKF3.ate_a_cruise."+0.00"`).
- FGO thesis row: `<t>.FGO_<arm>.evo.ate_a_cruise."+0.00"`. It equals r0 by the identity gate.

## 6. Noise band (method and its meaning at n = 3)

- **Method:** for each wall type and arm, band = max − min of the three stored thesis-FGO values (0.25 s, cap 2) over
  r1–r3. Unrounded, from `phase4_<ds>_arms.json`; shown rounded to 3 dp.

| wall type | arm | band (m) |
|---|---|---|
| fwdc | heading | 0.007 (0.063294 − 0.056585) |
| fwdplainc | heading | 0.127 (0.221451 − 0.094237) |
| fwdc | baseline | 2.282 (4.544273 − 2.262089) |
| fwdplainc | baseline | 0.223 (4.740214 − 4.517620) |

- **What it is:**
  - The band is the **between-flight** spread. The comparisons are **paired per bag**, and a bag replays
    deterministically (r0 must be byte-identical), so the within-bag "noise" is about zero.
  - The band is therefore a scale for "a change as large as the flight-to-flight spread", **not** a confidence band.
  - It is not meaningful as a noise band at n = 3. As the user specified, the gap predictions are **descriptive** (D35).
- **What it means per wall type:**
  - **fwdc heading:** 0.007 m, about a tenth of the 0.071–0.074 m gap. The band is usable as a scale.
  - **fwdplainc heading:** 0.127 m, larger than every gap (0.028–0.057 m). Those comparisons are uninformative against
    the band, and are reported as raw paired differences.
  - **fwdc baseline:** 2.282 m. P1 is nearly vacuous on `fwdc`, so the paired Δ is always printed beside the verdict.

## 7. Predictions (exploratory, descriptive; scored on unrounded values)

Notation:
- F_ρ,i is the FGO evo -a (cruise) of rung ρ on bag i.
- U_i is the stored UKF value.
- F_0,i is the stored thesis FGO, equal to r0.
- w(i) is the bag's wall type.

**P1 (control, no heading).**
- For each of r1, r2, r3, r4, r5: |F_ρ,i − F_0,i| ≤ band(w(i), baseline) on **6/6** control bags.
- Also reported:
  - the paired Δ;
  - whether the sign of U_i − F_ρ,i differs from U_i − F_0,i. This is descriptive; the control has no consistent
    ordering on `fwdc`.

**P2 (with heading): the one-keyframe converged FGO retains at least half the FGO–UKF gap.**
- gap_i = U_i − F_0,i, which is > 0 on all 6.
- R_i(ρ) = (U_i − F_ρ,i) / gap_i. R = 1 means the gap is unchanged; R ≤ 0 means the FGO is no better than the UKF.
- **Pass iff R_i(r3) ≥ 0.5 on all 3 `fwdc` bags.** Per bag, not pooled; ambiguity is read against the hypothesis
  (rule 2).
- `fwdplainc`: R_i(r3) is reported but not scored. The band exceeds the gap there, the heading failed Phase 3
  validation on that floor (`numbers.md:301`), and the margin is fragile to the initial yaw σ (`numbers.md:299`) (Q1).
- R_i is also reported for r1, r2, r4 and r5, as the ladder (descriptive).
- A FAILED-ESTIMATOR run counts against P2 (D14 precedent): keyframe failure, non-finite trajectory, or crash after the
  one retry.

**P3 (descriptive): robust kernel vs Gaussian.**
- |F_r6,i − F_0,i| ≤ band(w(i), heading) and |F_r7,i − F_r3,i| ≤ band(w(i), heading), each on 6/6 heading bags.
- Reported as "kernel replacing the gate", not as Huber vs Gaussian (§3).
- The stored Cauchy row r6s is shown beside it.
- Prior context, not a reason to change the prediction: stored F1 yaw metrics on plain walls differ strongly between
  the robust and hard-gated FGO (`f1_test.json`).

## 8. Interpretation table (written before running)

| observation | reading | what it cannot say |
|---|---|---|
| R_i(r3) ≥ 0.5 on `fwdc` (P2 pass), and R_i(r4), R_i(r5) close to R_i(r0) = 1 (within the band) | **The gap persists at one keyframe.** It is not explained by window length or retained history. The residual is attributable to the remaining differences, and this ablation cannot separate them: attitude representation (Euler 15-state vs Pose3 manifold); IMU handling (UKF predict steps of `DT_STEP` vs preintegration of every sample with 30 Hz keyframes); numerical Jacobians vs sigma points; heading-factor handling (FGO gate-only recursion vs the UKF update); the FGO's missing flow/range innovation gates and its 4.2 vs 2.5 rad/s flow limit (METHODOLOGY:14276-14304); measurement-to-keyframe holding (FGO applies the latest flow/range/heading at the next keyframe, `fgo_replay.py:192-196,215`); the UKF's residual take-off kick (`numbers.md:230`) | which of those differences matters |
| R_i(r3) < 0.5 on `fwdc` and R rises with W (r3 < r0 ≤ r4 ≤ r5) | **Retained history contributes.** The share is the change in R, descriptive | whether the window or the marginal-prior linearisation carries it |
| R_i(r3) ≤ 0 (the gap vanishes or reverses at one keyframe) | **Check before concluding:** the marginal prior (frozen `LinearContainerFactor` linearisation, inert FEJ, `step0_report.md` §2.1); the gate-only recursion; headings fused vs r0 (`fwd_stats.json`); keyframe failures. Only then read it as "the gap needs the window" | an implementation artefact cannot be excluded without code |
| r1, r2 and r3 differ by more than the band on `fwdc` | **Iteration count matters at one keyframe.** If r2 ≈ r3, cap 2 suffices there (extending E4's cap-2 result to one keyframe with heading). If r1 differs from r2 and r3, a single LM step is not enough | the iteration counts themselves (not logged) |
| r0 → r3 changes R while r2 ≈ r3 | the change is due to the **window**, not the iterations (this is why r2 exists, Q2) | — |
| P1 fails (a control rung moves beyond its band) | the variant changes the FGO generally, not only its heading handling. The P2 reading is then qualified | — |
| P3 fails | "kernel instead of gate" changes the result. This is confounded with gate removal, so nothing is concluded about Huber vs Gaussian | the pure kernel effect (needs code) |
| headings fused differ markedly between rungs | part of any change acts through the gate's linearisation point, not through the window. Reported beside R | — |
| `fwdplainc` R values | descriptive only. Any reading carries the Phase 3 failure and the initial-yaw fragility | anything about the plain-wall heading benefit |

## 9. Checks before, during and after

**Before the first job, in order. Any failure is a STOP.**
1. Nothing is running: `pgrep -fa '[l]c_fgo_replay|[r]oom_fgo|[h]eavy.py|[a]rducopter|[f]go_replay'` is empty, and
   `~/thesis_data/FLIGHT_LOCK` is absent.
2. `python3 tools/tier1_checksum_guard.py verify docs/thesis/tier1/frozen_manifest_20261022T002851.json` → IDENTICAL,
   exit 0. This manifest covers every trial output (bags excluded), every batch folder and `eval/results`, including all
   stored `fgo_*`/`ukf_*` outputs of the 6 bags.
3. `python3 tools/check_numbers_frozen.py` → exit 0.
4. Run-code snapshot: `git rev-parse HEAD`, an empty `git status --porcelain src eval`, and sha256 of
   `src/estimators/fgo/{fgo_replay,fgo_core,factors}.py`, `src/estimators/{measurement_models,imu_timing}.py`,
   `eval/{three_way_eval,cruise_window}.py` and `docs/thesis/ablation/score_ablation.py`. Written to
   `~/thesis_data/ablation/code_pre.json`.
5. `~/thesis_data/ablation/` does not exist yet, or holds only the driver.
6. The scorer gate is re-run: `score_ablation.py --gate` → 24/24 EQUAL.

**During:**
- **Identity gate after r0:** `cmp` of `~/thesis_data/ablation/r0_w0.25_lm2/<t>/fgo_<arm>/fgo_traj.tum` against the
  stored `~/thesis_data/trials/<t>/fgo_<arm>/fgo_traj.tum` must be identical on **12/12**, and the r0 scores must equal
  the stored values.
- Any difference is a **STOP and report**, and no further rung runs (D33). The code since `2cc08a2` changed only events
  mode; this gate proves that rather than assuming it.
- Per job: rc, keyframe-failure count, finiteness and wall time go into `timing.tsv`.
- **Crash or hang (as decisions D11/D14):**
  - timeout = min(48 h, time to the lock); after the lock a job exits without running and is NOT RUN;
  - on rc ≠ 0, one identical re-run after moving the output aside; a second failure is "crashed" and the queue
    continues (the runs are independent);
  - a crashed or failed run counts against the prediction that uses it.

**After the last job, before scoring:**
- repeat steps 1–3 (verify IDENTICAL; numbers.md frozen);
- the run-code hashes must equal `code_pre.json`.

**Commit:**
- only when nothing is running (step 1);
- by explicit path (`docs/thesis/ablation/...`);
- then `tools/check_numbers_frozen.py`.

## 10. Scheduling and parallelism

- **All replays serial**, one at a time (D28; `heavy.py` BUILD_LOCK enforces it). There is no timing hypothesis, so
  rule 6 would allow 4 in parallel. Serial is chosen so that the requested "compute per step" is not contaminated by
  load (E4's note, `e4_results.md:37-44`), and it still fits the cap: 13.9 h, upper bound.
- Scoring (evo) is minutes, after the replays, and may use the scorer's internal threads.
- Machine: 12 threads, 15 GB RAM, about 6 GB available at Step 0. Serial replays are well within that.

## 11. Not runnable without a code change (listed, not dropped)

These are stopped per the user's rule (`step0_report.md` §6):
- Huber with the heading χ² gate kept (a pure kernel swap);
- Huber on flow, range, yaw-cap or yaw-rate factors;
- a keyframe-rate rung;
- LM tolerance changes, and logging iteration counts to confirm "converged";
- a clean full batch without the live yaw-cap anchors;
- a strict single-state window.

The user's ladder needs none of them, except P3's "Huber vs Gaussian" in its pure form. That prediction is run in the
gate-replacing form, and the difference is stated.

## 12. Limitations to state with the results

- Simulation only.
- n = 3 flights per wall type.
- Deterministic replays: there is no within-bag noise, and the band is the between-flight spread.
- The plain-wall heading failed Phase 3 on this floor.
- The stored UKF/EKF3 rows are reused, not re-run.
- The step times are workstation Python, not the flight controller.
- The robust rungs change the gate as well as the kernel.
- "Converged" is operational: the iteration counts are not logged.
- Exploratory: no thesis claim changes on these results without a separate ruling.
