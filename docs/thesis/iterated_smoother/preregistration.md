# Iterated UKF smoother for the Experiment 2 hindsight comparison: pre-registration (EXPLORATORY)

Written and committed BEFORE any code for the iterated smoother exists and before any run (decision D152). Status:
**EXPLORATORY, added after the Experiment 2 results.** It does not change any registered result: P-T2 and P-T4 stay
FAIL as scored (numbers.md §16.1), and nothing in numbers.md, the frozen pack, `eval/results/expT/` or any stored
`room_ukf/` output is modified.

## 1. Why

Experiment 2's registered hindsight comparison (METHODOLOGY.md:10146-10147) used the single-pass unscented RTS smoother
as the filter-side counterpart of the FGO whole-flight batch. P-T4 (within 1.5×) failed from condition B on; the
diagnosis (METHODOLOGY.md:10262-10272) is that the single pass linearises once about the filter's drifted forward
estimates and never re-linearises, and the record says "An iterated smoother (relinearising, i.e. Gauss–Newton over
the whole trajectory) would be the stronger fair comparison … Stated, not built." The results text therefore limits
the claim: "The result does not establish that factor graphs revise the past better than filter + iterated smoother
would" (METHODOLOGY.md:10283-10285). This study builds that smoother and asks the question directly.

Current values (numbers.md §16.1, horizontal RMSE over the lap window, mean of 3):

| condition (median gap) | UKF live | RTS-UKF | FGO batch |
|---|---|---|---|
| A (4.3 s) | 0.037 | 0.014 | 0.010 |
| B (10.1 s) | 0.061 | 0.031 | 0.015 |
| C (22.0 s) | 0.076 | 0.039 | 0.019 |
| D (46.3 s) | 0.131 | 0.109 | 0.028 |

## 2. Method (fixed now)

**Smoother: iterated posterior linearisation smoother (IPLS), unscented** (García-Fernández, Svensson and Särkkä,
"Iterated posterior linearization smoother", IEEE TAC 2017). Iteration j:
1. For every predict step and every measurement update of the stored UKF replay, linearise the process model and the
   measurement model by unscented statistical linear regression (SLR) about the iteration-(j−1) SMOOTHED marginal at
   that step (same sigma-point scheme and parameters as `ukf_core._sigma_points`), giving an affine model with its
   linearisation-error covariance added to Q or R.
2. Run a linear Kalman filter forward with those affine models, then a linear RTS backward pass.
3. Iteration 0 uses the forward UKF's own linearisation, so iteration 0 IS the existing single-pass RTS.

**Everything else is the UKF's, unchanged:** the same state (15-state Euler UKF), the same IMU inputs and
dejitter/gap rule, the same predict-step accumulation (15.00 ms steps, Q scaled by DT_REF/dt), the same measurement
models and noises (flow, range, tag σ_pos 0.05 m / σ_yaw 5°), the same re-anchor at the first tag fix and the same
smoothing window (from the re-anchor on, as `room_ukf_replay.py`).
- **Gates are frozen:** the accept/reject decision of every gated flow and range update is taken from the forward UKF
  pass and held fixed in every iteration (no re-gating, so the iterations cannot change which data are used). Tag fixes
  are ungated, as in the registered UKF.
- **Pseudo-yaw:** as the forward UKF (in Experiment 2 the pseudo-yaw stops at the tag re-anchor); every pseudo-yaw
  update the forward pass applied is kept, with the same noise, and none is added.
- **Angles:** Euler-angle residuals wrapped exactly as `ukf_core._state_residual`/`_wrap`.

**Stopping rule:** stop when the largest change in smoothed horizontal position between successive iterations, over
all nodes, is below 1 mm, or after 10 iterations, whichever comes first. **No damping, step control or tuning is added
after seeing results.** A run that has not met the 1 mm rule by iteration 10, or whose cost (sum of squared whitened
residuals) increases between iterations, is reported as **non-converged**, with its iteration-10 trajectory scored and
labelled; it is not re-run with other settings.

## 3. Runs

- The 12 Experiment 2 flights `T_{A,B,C,D}_r{1,2,3}` (the current, re-flown trials; IMU-gap verdicts as stored).
- Optional check, reported separately: Experiment 4 `O_r1`, `O_r2`, `O_r3b` (GNSS on both sides of the gap, where the
  single-pass RTS already matches the FGO batch, P-O3 PASS).
- Offline only, through `heavy.py`, one job at a time; outputs to a NEW directory per trial, `room_ukf_ipls/`
  (`ukf_ipls.tum`, `stats.json` with iterations, convergence flag, per-iteration max change and cost); no stored output
  is overwritten.

## 4. Gates (must pass before any result is read)

- **G1:** the forward pass reproduces the stored `room_ukf/ukf_live.tum` (max horizontal difference ≤ 1e-6 m).
- **G2:** iteration 0 reproduces the stored `room_ukf/ukf_rts.tum` (max horizontal difference ≤ 1e-6 m).
- **G3:** on a synthetic linear-Gaussian test problem, IPLS converges in one iteration to the exact RTS solution
  (difference ≤ 1e-9), and on a short nonlinear test its cost does not increase across iterations.
If any gate fails, stop and report; no result is scored.

## 5. Scoring and predictions (exploratory; rules fixed now)

Scored with the registered Experiment 2 scorer's definitions (`eval/tag_score.py`: world frame, no alignment,
horizontal RMSE over the lap window, mean of 3 per condition; per-gap gain as `eval/t_aggregate.py`), with the new
track labelled "IPLS-UKF (hindsight, exploratory)".

- **E-1 (re-linearisation helps over long gaps):** IPLS-UKF RMSE < RTS-UKF RMSE on every flight in conditions B, C and
  D (9/9).
- **E-2 (the filter-side fair comparison, P-T4's rule applied to the new track):** in every condition, the larger of
  IPLS-UKF and FGO-batch RMSE (mean of 3) is ≤ 1.5 × the smaller (4/4).
- **E-3 (H-T1's rule applied to the new track):** the IPLS-UKF per-gap hindsight gain (UKF live − IPLS-UKF) has
  condition medians strictly increasing from A to D.
- **Reported regardless:** per flight and condition RMSE for all hindsight tracks, iterations used, convergence,
  run time; the Experiment 4 check if run.

Reading, fixed now: if E-2 holds, the FGO batch's hindsight advantage over the RTS-UKF is attributed to re-linearising
over the whole trajectory rather than to the factor-graph formulation. If E-2 fails while E-1 holds, re-linearisation
narrows but does not close the gap. These are exploratory statements; no registered verdict changes.

## AMENDMENT 1 (2026-11-22, decision D153): the G3(b) cost check and the cost definition. Recorded after the stage 1 gates and BEFORE any Experiment 2 IPLS result was scored (no IPLS track has been compared with ground truth or with the RTS-UKF)

**What happened (stage 1, commits 789ee43 / 81cd26b; handover `docs/handovers/2026-11-22_ipls_stage1_d152.md`):**
- G1 and G2 PASS exactly on `T_A_r1` (max difference 0.0 m, 17272/17272 rows). G3(a) PASS (linear case reproduced to
  4.99e-10, one iteration).
- G3(b), the short nonlinear toy, was run by the stage-1 test to a 1e-6 m tolerance (a test setting, not the
  pre-registered stopping rule). Its cost trace was 1.3510 → 0.4420 → 0.4435: a rise of 0.0015 at iteration 2, where
  the trajectory moved 1.9e-8 m. Under the pre-registered 1 mm stopping rule the toy stops after iteration 1
  (1.351 → 0.442), with no increase. The real flight `T_A_r1`, run under the 1 mm rule, converged in 2 iterations with a
  monotonically decreasing cost (45242.78 → 44748.36 → 44287.78).
- Cause: IPLS's fixed point is not in general the minimum of the MAP objective evaluated with the exact nonlinear
  models (unscented statistical linear regression propagates E[f(x)], not f(E[x])), so once converged it can sit a
  hair above that minimum. A cost-monotonicity check is therefore not a property IPLS guarantees at sub-millimetre
  changes.

**Rulings (D153):**
1. **Cost definition, fixed as implemented:** the MAP objective (sum of squared whitened residuals of the prior, every
   process step and every accepted measurement) evaluated at the smoothed means with the exact nonlinear models.
2. **The cost-increase test (G3(b) and the §2 non-convergence clause) applies to the iterations the pre-registered
   stopping rule actually takes (1 mm, at most 10).** Under this reading G3(b) PASSES. Both readings and both traces
   are reported; this reading is chosen because the 1 mm rule is the one every real run uses, and the gate exists to
   catch a smoother whose cost grows while the trajectory is still moving.
3. Every real run still reports its full per-iteration cost and max-change trace, and any cost increase within the
   iterations taken labels that run non-converged, exactly as §2.
4. Nothing else changes: method, gates G1/G2, stopping rule, runs, predictions E-1 to E-3 and their rules stand.
