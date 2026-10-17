# Handover 2026-10-17: Figure 4.1c (provisional, R5), offline standard-sensor drift, UNALIGNED

**Done.** `eval/figs_thesis_drift.py` (new file; run with `~/venv-evo/bin/python`) writes
`docs/thesis/figures_thesis/R5_drift_unaligned.{png,pdf}` and `docs/thesis/figures_thesis/index_drift.md`
(caption, inputs, frame-check table, cross-check table). It uses stored outputs only: no estimator run, no simulation.
Flight: `dsn_tex_r3`. The R3 rule is recomputed and asserted to give flight 3.

**Frame check: PASS 3/3.**
- Each estimate's horizontal position at take-off is 0, and so is truth's.
- Over the first 5 m of true cruise travel, each estimate's heading is within 2° of truth's: EKF3 +0.23°, UKF +0.82°, FGO +0.37° relative to truth.
- The UKF/FGO frame needed a FIXED relabelling, not a fit, as (N, E) = (x, −y):
  - Both estimators start at yaw 0, so x is the take-off heading (`ukf_core.py:318`, `fgo_core.py:120`).
  - The spawn yaw is 90° ENU, which is North (`sim/worlds/corridor_textured.sdf:218`).
  - `eval/phase5_analysis.py:12-14` uses the same map.
- EKF3's (N, E, D) file is used as stored.

**Cross-checks: 9/9 EXACT.**
- The recomputed evo -a cruise ATE equals the stored value to 6 dp for all three estimators.
- The displayed ATEs 4.10 / 5.17 / 4.48 match `numbers.md:221/225/223`.
- Also checked: 9 flights, flight 3, and the stretch factor.

**For a user ruling (non-blocking):**
1. Is the fixed UKF/FGO relabelling (yaw-0 frame onto truth North) acceptable for "unaligned"? It is by construction, not fitted, but it does rely on knowing that the take-off heading is North.
2. The stretch factor is 1.0×, i.e. equal scale: the 36–48 m sideways drift needs no stretching. The brief asked for a stretched lateral axis.
3. Finding: `ukf_replay.py:239-289` and the FGO `metrics.txt` read TUM column 1 as East, but that column is along the take-off heading (North). The stored `metrics.txt` fields `along_pN`, `cross_track` and `ate_apparatus` are therefore axis-swapped for the UKF and FGO. For example, `dsn_tex_r3/ukf` stores `cross_track=135.057`, which is really the along-track displacement. Check whether any thesis number comes from these fields (`plots/rerun_batch.py`, `plots/fgo_batch.py` read them).
4. The unaligned end-of-cruise errors (sideways about 36/48/41 m for EKF3/UKF/FGO; along-track about −8/−16/−10 m) are NOT printed on the figure, because numbers.md has no row for them.

Nothing renumbered. No frozen file, METHODOLOGY.md, numbers.md, figs_thesis.py, figs_thesis_results.py or figs_thesis_methods.py edited.
