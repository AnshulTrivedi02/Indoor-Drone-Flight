# Attribution ablation: numbers (EXPLORATORY)

**EXPLORATORY: every value in this file is exploratory, not a thesis result.** No thesis claim changes on these values
without a separate ruling. `docs/thesis/numbers.md` is not touched.

**Status: COMPLETE.** Pre-registration SIGNED OFF by the user 2026-10-24 with edits (`preregistration.md`, commit
`41941cf`, committed before any run). Everything below is scored as worded there; ambiguity is read against the
hypothesis (rule 2).

**Rules for this file:**
- Every value traces to a json key: `~/thesis_data/ablation/scores/<rung>_<arm>.json` (`trials.<t>.ate_a_cruise_m`,
  `trials.<t>.step_ms`, `trials.<t>.fwd_counts`), `~/thesis_data/ablation/scores/ablation_results.json` (derived values,
  unrounded), or `eval/results/phase4_<ds>_arms.json` for the stored rows (`<t>.UKF_<arm>.evo.ate_a_cruise."+0.00"`,
  `<t>.EKF3.ate_a_cruise."+0.00"`).
- Every value is rounded once, from the unrounded value. Metric: evo -a (cruise), the pinned window (`score_ablation.py`).
- Units: m (position error), ms (step time), s / h (wall time).
- Checked by `check_ablation.py` (independent recomputation; 0 mismatches required).

## 0. Run record (EXPLORATORY)

- **Before:** guard verify IDENTICAL (13253 files, `docs/thesis/tier1/frozen_manifest_20261022T002851_verify_ablation_pre_*.json`);
  `check_numbers_frozen.py` PASS; scorer gate 24/24 EQUAL; run-code snapshot `~/thesis_data/ablation/code_pre.json`.
- **First launch failed before any estimator step (harness bug, D43):** the input bags are stored packed
  (`bag_0.db3.zst`); all 12 r0 jobs exited rc 1 at bag open. Fixed by sha256-verified decompressed copies under
  `~/thesis_data/ablation/bags/` read through the existing `FGO_BAG_ROOT` flag; no model or argument changed. That
  attempt's state is kept in `~/thesis_data/ablation/attempt0_bagmissing/`.
- **Identity gate (r0, 0.25 s, cap 2): PASS.** `fgo_traj.tum` 12/12 byte-identical to the stored trajectories
  (`ground_truth.tum`, `bgz_series.txt`, `fwd_stats.json` also identical); r0 evo -a (cruise) 12/12 equal to the stored
  values (`~/thesis_data/ablation/gate.json`, `gate.out`). Only then did the other rungs run.
- **Jobs:** 84/84 completed; 84/84 OK (rc 0, no keyframe failure, finite trajectory); retries: 0; keyframe failures: 0;
  no FAILED-ESTIMATOR, no crash, no NOT RUN. Serial via `heavy.py` (1 thread, nice 19), 11:38–19:56 AEDT.
- **After:** post-run guard verify: IDENTICAL (13253 files); `check_numbers_frozen.py` PASS; run code identical to
  `code_pre.json` (sha256 of every run-code file; no tracked change in src/eval).
- **Not run:** the full batch (`F_BATCH`), dropped by the user (Q3).

Wall time per rung (s, sum of job walls from `timing.tsv`; projection was 50198 s, an upper bound):

| rung | wall (s) |
|---|---|
| r0 | 2508 |
| r1 | 927 |
| r2 | 991 |
| r3 | 1021 |
| r4 | 7531 |
| r5 | 14787 |
| r6 | 1529 |
| r7 | 599 |

total 29893 s = 8.3 h.

## 1. Tables (EXPLORATORY)

The stored UKF / EKF3 rows are reused, not re-run. r0 equals the stored thesis FGO (identity gate). "1 kf" = one
keyframe (W = 0.01 s). r3 and r7: cap 100; convergence not confirmed (iteration counts not logged). r6 / r7 / r6s are
robust weighting replacing the heading gate (not Huber vs Gaussian). Band = max − min of the three stored thesis-FGO
values per wall type and arm (D35): `fwdc` heading 0.007, `fwdplainc` heading 0.127, `fwdc` control 2.282,
`fwdplainc` control 0.223 m.

## T1. With heading: FGO evo -a (cruise), m (EXPLORATORY)

| bag | r0 | r1 | r2 | r3 | r4 | r5 | UKF (stored) | EKF3 (stored) |
|---|---|---|---|---|---|---|---|---|
| fwdc_tex_r1 | 0.057 | 0.056 | 0.056 | 0.056 | 0.054 | 0.056 | 0.127 | 4.093 |
| fwdc_tex_r2 | 0.063 | 0.065 | 0.065 | 0.065 | 0.064 | 0.063 | 0.134 | 3.603 |
| fwdc_tex_r3 | 0.063 | 0.065 | 0.065 | 0.065 | 0.062 | 0.063 | 0.137 | 4.076 |
| fwdplainc_tex_r1 | 0.150 | 0.150 | 0.150 | 0.150 | 0.150 | 0.149 | 0.188 | 4.075 |
| fwdplainc_tex_r2 | 0.094 | 0.094 | 0.094 | 0.094 | 0.094 | 0.093 | 0.151 | 4.057 |
| fwdplainc_tex_r3 | 0.221 | 0.222 | 0.222 | 0.222 | 0.221 | 0.221 | 0.250 | 4.082 |

## T2. Gap retention R_i = (U_i − F_ρ,i) / (U_i − F_0,i) (EXPLORATORY; DESCRIPTIVE)

| bag | gap (m) | 1 − band/gap | R(r1) | R(r2) | R(r3) | R(r4) | R(r5) | R(r6) | R(r7) |
|---|---|---|---|---|---|---|---|---|---|
| fwdc_tex_r1 | 0.071 | 0.91 | 1.01 | 1.01 | 1.01 | 1.03 | 1.01 | 1.02 | 1.18 |
| fwdc_tex_r2 | 0.072 | 0.91 | 0.97 | 0.97 | 0.97 | 0.98 | 0.99 | 1.05 | 1.09 |
| fwdc_tex_r3 | 0.074 | 0.91 | 0.98 | 0.98 | 0.98 | 1.02 | 1.00 | 1.00 | 0.99 |
| fwdplainc_tex_r1 | 0.038 | −2.34 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | −3.96 | −3.54 |
| fwdplainc_tex_r2 | 0.057 | −1.22 | 1.01 | 1.00 | 1.00 | 1.01 | 1.02 | −2.51 | −2.12 |
| fwdplainc_tex_r3 | 0.028 | −3.53 | 0.99 | 1.00 | 1.00 | 1.00 | 1.01 | −2.75 | −2.71 |

## T3. Control (no heading): FGO evo -a (cruise), m, and paired Δ = F_ρ − F_0, m (EXPLORATORY)

| bag | r0 | r1 (Δ) | r2 (Δ) | r3 (Δ) | r4 (Δ) | r5 (Δ) | band | UKF (stored) |
|---|---|---|---|---|---|---|---|---|
| fwdc_tex_r1 | 4.467 | 4.457 (−0.010) | 4.445 (−0.022) | 4.439 (−0.028) | 4.430 (−0.037) | 4.352 (−0.115) | 2.282 | 4.960 |
| fwdc_tex_r2 | 2.262 | 2.566 (0.304) | 2.562 (0.300) | 2.562 (0.300) | 1.504 (−0.758) | 0.979 (−1.283) | 2.282 | 1.783 |
| fwdc_tex_r3 | 4.544 | 4.520 (−0.024) | 4.510 (−0.034) | 4.495 (−0.049) | 4.497 (−0.047) | 4.378 (−0.166) | 2.282 | 4.964 |
| fwdplainc_tex_r1 | 4.536 | 4.484 (−0.052) | 4.492 (−0.045) | 4.496 (−0.040) | 4.488 (−0.048) | 4.338 (−0.198) | 0.223 | 5.023 |
| fwdplainc_tex_r2 | 4.518 | 4.525 (0.008) | 4.564 (0.046) | 4.675 (0.157) | 4.576 (0.058) | 4.620 (0.102) | 0.223 | 11.194 |
| fwdplainc_tex_r3 | 4.740 | 4.341 (−0.399) | 4.375 (−0.365) | 4.337 (−0.403) | 4.772 (0.032) | 4.798 (0.058) | 0.223 | 10.819 |

## T4. Robust weighting replacing the heading gate: evo -a (cruise), m (EXPLORATORY; DESCRIPTIVE)

| bag | r0 | r6 Huber 0.25 s | r6 − r0 | r3 | r7 Huber 1 kf | r7 − r3 | r6s stored Cauchy | band (heading) |
|---|---|---|---|---|---|---|---|---|
| fwdc_tex_r1 | 0.057 | 0.055 | −0.002 | 0.056 | 0.044 | −0.012 | 0.056 | 0.007 |
| fwdc_tex_r2 | 0.063 | 0.059 | −0.003 | 0.065 | 0.056 | −0.008 | 0.062 | 0.007 |
| fwdc_tex_r3 | 0.063 | 0.064 | 0.000 | 0.065 | 0.064 | −0.001 | 0.064 | 0.007 |
| fwdplainc_tex_r1 | 0.150 | 0.339 | 0.189 | 0.150 | 0.322 | 0.173 | 0.096 | 0.127 |
| fwdplainc_tex_r2 | 0.094 | 0.295 | 0.201 | 0.094 | 0.273 | 0.178 | 0.117 | 0.127 |
| fwdplainc_tex_r3 | 0.221 | 0.327 | 0.105 | 0.222 | 0.326 | 0.104 | 0.099 | 0.127 |

## T5. Compute per step, median / p95, ms (EXPLORATORY; DIAGNOSTIC: workstation Python, serial, 1 thread, nice 19)

| bag, arm | r0 | r1 | r2 | r3 | r4 | r5 | r6 | r7 |
|---|---|---|---|---|---|---|---|---|
| fwdc_tex_r1, heading | 23.1 / 34.9 | 8.5 / 9.1 | 9.4 / 12.0 | 9.2 / 12.1 | 64.2 / 113.2 | 122.1 / 224.5 | 31.2 / 34.8 | 11.5 / 12.4 |
| fwdc_tex_r2, heading | 27.8 / 35.0 | 8.6 / 9.1 | 9.4 / 12.4 | 9.0 / 11.8 | 69.4 / 115.1 | 137.2 / 225.8 | 30.6 / 34.4 | 11.3 / 12.1 |
| fwdc_tex_r3, heading | 29.2 / 34.7 | 8.5 / 8.9 | 9.6 / 12.2 | 9.4 / 11.9 | 100.7 / 111.6 | 197.5 / 222.2 | 31.4 / 35.0 | 11.7 / 12.5 |
| fwdplainc_tex_r1, heading | 18.7 / 32.5 | 7.9 / 8.6 | 8.2 / 11.6 | 8.3 / 11.6 | 54.1 / 101.6 | 104.0 / 198.2 | 19.4 / 34.4 | 8.4 / 11.8 |
| fwdplainc_tex_r2, heading | 18.1 / 31.4 | 8.0 / 8.6 | 7.9 / 11.1 | 8.0 / 11.3 | 54.0 / 100.7 | 105.4 / 199.5 | 19.2 / 33.7 | 8.3 / 11.7 |
| fwdplainc_tex_r3, heading | 18.7 / 32.4 | 7.9 / 8.5 | 7.9 / 11.1 | 8.0 / 11.2 | 53.2 / 100.2 | 103.6 / 198.2 | 19.5 / 34.4 | 8.4 / 11.8 |
| fwdc_tex_r1, baseline | 16.4 / 18.2 | 6.2 / 6.6 | 6.2 / 7.0 | 6.2 / 6.8 | 51.9 / 55.1 | 100.6 / 106.1 | — | — |
| fwdc_tex_r2, baseline | 17.0 / 18.6 | 6.2 / 6.6 | 6.2 / 6.8 | 6.3 / 7.0 | 51.8 / 55.5 | 102.3 / 109.1 | — | — |
| fwdc_tex_r3, baseline | 17.1 / 18.5 | 6.1 / 6.5 | 6.2 / 7.0 | 6.1 / 6.8 | 51.3 / 55.3 | 100.8 / 106.2 | — | — |
| fwdplainc_tex_r1, baseline | 16.3 / 17.9 | 6.4 / 6.8 | 6.1 / 6.8 | 6.1 / 6.8 | 51.6 / 55.8 | 104.6 / 111.4 | — | — |
| fwdplainc_tex_r2, baseline | 16.4 / 17.7 | 6.2 / 6.6 | 6.1 / 6.6 | 6.1 / 6.9 | 51.3 / 54.6 | 102.3 / 109.4 | — | — |
| fwdplainc_tex_r3, baseline | 16.4 / 17.9 | 6.2 / 6.6 | 6.1 / 7.0 | 6.2 / 7.0 | 51.6 / 55.4 | 101.2 / 106.1 | — | — |

## T6. Headings fused / valid, and run status (EXPLORATORY; DESCRIPTIVE)

| bag | r0 | r1 | r2 | r3 | r4 | r5 | r6 | r7 |
|---|---|---|---|---|---|---|---|---|
| fwdc_tex_r1 | 9184 / 9539 | 9184 / 9539 | 9184 / 9539 | 9184 / 9539 | 9184 / 9539 | 9184 / 9539 | 9539 / 9539 | 9539 / 9539 |
| fwdc_tex_r2 | 9315 / 9619 | 9315 / 9619 | 9315 / 9619 | 9315 / 9619 | 9315 / 9619 | 9315 / 9619 | 9619 / 9619 | 9619 / 9619 |
| fwdc_tex_r3 | 9159 / 9521 | 9159 / 9521 | 9159 / 9521 | 9159 / 9521 | 9159 / 9521 | 9159 / 9521 | 9521 / 9521 | 9521 / 9521 |
| fwdplainc_tex_r1 | 747 / 6333 | 747 / 6333 | 747 / 6333 | 747 / 6333 | 747 / 6333 | 747 / 6333 | 6333 / 6333 | 6333 / 6333 |
| fwdplainc_tex_r2 | 647 / 6197 | 653 / 6197 | 653 / 6197 | 653 / 6197 | 647 / 6197 | 647 / 6197 | 6197 / 6197 | 6197 / 6197 |
| fwdplainc_tex_r3 | 778 / 6258 | 778 / 6258 | 778 / 6258 | 778 / 6258 | 778 / 6258 | 778 / 6258 | 6258 / 6258 | 6258 / 6258 |

## 2. Verdicts (EXPLORATORY; scored as worded in `preregistration.md` §7, on unrounded values)

| prediction | verdict | count | where it fails |
|---|---|---|---|
| P1 r1 | FAIL | 5/6 | fwdplainc_tex_r3: Δ −0.399 m vs band 0.223 m |
| P1 r2 | FAIL | 5/6 | fwdplainc_tex_r3: Δ −0.365 m vs band 0.223 m |
| P1 r3 | FAIL | 5/6 | fwdplainc_tex_r3: Δ −0.403 m vs band 0.223 m |
| P1 r4 | PASS | 6/6 | all 6 within band |
| P1 r5 | PASS | 6/6 | all 6 within band |
| P1 overall | FAIL | — | P1 needs every rung 6/6 |
| P2 | PASS | 3/3 | — (R(r3) on `fwdc`: 1.01, 0.97, 0.98; pass needs ≥ 0.5 on each) |
| P3 | FAIL | r6 4/6, r7 2/6 | r6: `fwdplainc_tex_r1`, `_r2` (+0.189, +0.201 m vs band 0.127); r7: `fwdc_tex_r1`, `_r2` (−0.012, −0.008 m vs band 0.007) and `fwdplainc_tex_r1`, `_r2` (+0.173, +0.178 m) |

- **P1 is a weak test on `fwdc`** (pre-registered): the 2.28 m band is set by one outlying repeat and admits almost any
  result. Example: r4 and r5 "pass" on `fwdc_tex_r2` with Δ −0.758 and −1.283 m, which also flip the sign of
  UKF − FGO on that control flight (the only sign flips in P1).
- **P1 fails only through `fwdplainc_tex_r3` at one keyframe** (r1, r2, r3): its no-heading error is about 0.4 m
  LOWER than r0's (4.341 / 4.375 / 4.337 against 4.740 m; Δ −0.399 / −0.365 / −0.403 m), beyond the 0.223 m band.
- **P2 passes 3/3.** `fwdplainc` R(r3) (descriptive, not scored): see T2 (1.00 / 1.00 / 1.00).

**Interpretation-table tests on `fwdc` (heading; D36, D44; unrounded values):**

| bag | R(r3) | 1 − band/gap | R(r3) ≥ 1 − band/gap | |R(r4) − 1| ≤ band/gap | |R(r5) − 1| ≤ band/gap |
|---|---|---|---|---|---|
| fwdc_tex_r1 | 1.01 | 0.91 | yes | yes | yes |
| fwdc_tex_r2 | 0.97 | 0.91 | yes | yes | yes |
| fwdc_tex_r3 | 0.98 | 0.91 | yes | yes | yes |

Iteration rungs at one keyframe, pairwise FGO differences on `fwdc` (band 0.006709 m):
- fwdc_tex_r1 r1−r2 −0.000020 m (≤ band)
- fwdc_tex_r1 r1−r3 −0.000060 m (≤ band)
- fwdc_tex_r1 r2−r3 −0.000040 m (≤ band)
- fwdc_tex_r2 r1−r2 0.000007 m (≤ band)
- fwdc_tex_r2 r1−r3 0.000008 m (≤ band)
- fwdc_tex_r2 r2−r3 0.000001 m (≤ band)
- fwdc_tex_r3 r1−r2 −0.000026 m (≤ band)
- fwdc_tex_r3 r1−r3 −0.000045 m (≤ band)
- fwdc_tex_r3 r2−r3 −0.000019 m (≤ band)

Headings fused / valid are identical across r0–r5 on all three `fwdc` bags (T6), so no part of the window/iteration
result acts through a different set of fused headings there.

## 3. Plain-language reading (EXPLORATORY; tied to `preregistration.md` §8)

- **Row matched: "gap persists at one keyframe".** On all three line-textured-wall flights the one-keyframe FGO
  (r3) keeps the FGO–UKF gap essentially whole (R = 1.01, 0.97, 0.98, each above its ≈ 0.91 threshold), and so do the
  1 s and 2 s windows (R within the band of 1). In the user's wording: gap persists at one keyframe -> not window or
  retained history; residual attributable to the remaining differences (attitude representation, IMU preintegration,
  Jacobians vs sigma points, heading-factor handling), which this ablation cannot separate. The pre-registered list
  also names the FGO's missing flow/range gates and flow limit, measurement-to-keyframe holding and the UKF's
  take-off kick; this ablation does not say which of these matters.
- **Iterations do not matter at one keyframe here:** cap 1, 2 and 100 differ by at most 0.000060 m on `fwdc`, far
  inside the 0.007 m band (iteration counts were not logged, so "converged" stays operational).
- **The P2 reading is qualified by P1's failure** (pre-registered row "P1 fails"): the one-keyframe variant also
  changes the no-heading FGO on one plain-wall flight (`fwdplainc_tex_r3`, about 0.4 m lower error), so the variant is
  not inert outside heading handling. On the line-textured control the Δ values sit inside a band too wide to test.
- **Robust weighting replacing the heading gate (P3 FAIL):** on plain walls it makes the FGO worse on `_r1`/`_r2`
  (r6 0.339 / 0.295 m, r7 0.322 / 0.273 m, against r0 0.150 / 0.094 m): the gate had fused only 647–778 of the
  6197–6333 valid plain-wall headings, and Huber weights all of them in. On line-textured walls it changes little at 0.25 s and lowers the one-keyframe error by
  0.008–0.012 m on two flights. Confounded with gate removal, so nothing is concluded about Huber vs Gaussian. The
  stored Cauchy (r6s) is shown alongside, not scored.
- **Step time (DIAGNOSTIC):** median per step: one keyframe 6.1–11.7 ms (r1–r3, r7), 0.25 s 16.3–31.4 ms (r0, r6), 1 s 51.3–100.7 ms,
  2 s 100.6–197.5 ms
  (workstation Python, serial). Not a flight-controller figure; no timing prediction was registered.
- **Strength of the claim (rule 8):** exploratory, simulation, n = 3 per wall type, deterministic replays; the result
  is that window length / retained history and the iteration cap do not account for the with-heading gap on these three
  line-textured flights. It does not identify the cause.

## 4. Limitations (EXPLORATORY)

- Simulation only; n = 3 flights per wall type; deterministic replays (no within-bag noise; the band is the
  between-flight spread, a descriptive scale, not a confidence band).
- All six bags are checkerboard-floor (`_tex_`) recordings.
- The plain-wall heading failed its Phase 3 validation on this floor (`numbers.md:301`), and the plain-wall margin is
  fragile to the initial yaw σ (`numbers.md:299`); plain-wall rows are descriptive.
- P1 on `fwdc` is a weak test: the line-textured control band (2.28 m) is set by one outlying repeat and admits almost
  any result.
- Convergence not confirmed: cap 100; iteration counts not logged.
- The robust rungs change the gate as well as the kernel (`fgo_replay.py:129`).
- The stored UKF/EKF3 rows are reused, not re-run. Step times are workstation Python, not the flight controller.
- The one-keyframe rung is a two-keyframe iterated filter (the IMU factor spans k−1 and k; `step0_report.md` §1.2), not
  a strict single-state filter.
- Exploratory: no thesis claim changes on these results without a separate ruling.

## 5. Open questions (for the user)

- **Q8.** P1 fails only via `fwdplainc_tex_r3` at one keyframe (the no-heading FGO ~0.4 m better). Accept the
  pre-registered qualification as is, or would you like it looked into? Rule 5 does not trigger (not > 10× off, not a
  thesis claim), so nothing was diagnosed.
- **Q9.** The result says the gap is not the window or history. Separating the remaining differences (attitude
  representation, IMU preintegration, Jacobians vs sigma points, heading-factor handling) needs code changes
  (`step0_report.md` §6 lists the cheap ones). Stop here, or scope a follow-up?
- **Q10.** Should any of this enter thesis text (e.g. a sentence in the FGO-vs-UKF discussion), and in what words?
  Nothing has been applied.
