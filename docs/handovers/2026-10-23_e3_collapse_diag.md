# Handover: E3 map-collapse diagnosis (descriptive), 2026-10-23

**Done. Nothing is running.** This stage was descriptive only and changed no E3 verdict, score or criterion. The full
write-up is `docs/thesis/tier1/e3_results.md` §7, and METHODOLOGY has a matching FINDING entry ("E3 map-collapse diagnosis
(descriptive)"). Decisions D5 and D6 are in `docs/thesis/tier1/decisions_log.md`.

## Cause (plain terms)

**The plain FGO trusts a tag factor (5 cm / 5°) far more than its own dead reckoning (flow noise of about 0.4376 m/s per
keyframe).** The collapse is consistent with a least-squares compromise; IMU and range costs were not evaluated, so the
global optimum is not shown.
- **One wrong id is costly.** At the true layout it costs about 7,700 (a residual of about 124σ).
- **Bending the map is cheaper.** The solver bends the trajectory and the map instead. Correct tag factors cannot stop
  this, because they are relative and move with their landmark.
- **The result is a shrunken map.** Each wrong id pulls two landmarks together, so the map shrinks. On T_A_r1 1% s0, the
  final estimate's tag cost plus approximate flow cost is 8,622 + 6,266 against 144,218 at the true layout.
- **No harness bug.** The injection swaps only the id (code read, plus an exact regeneration of the logged events).

## Evidence

- **Time course.** On T_A_r1 1% s0 the error does not move at the first-sighting mislabels (36.199 / 36.932 s).
  It jumps to 6.6477 m at the true tag 6's first correct sighting (59.332 s).
  - After that it is a per-lap sawtooth, which is low at the gauge tag.
  - On T_A_r3 5% s0 the step comes at a non-first wrong id (43.914 s).
- **Counterfactuals** (T_A_r1 1% s0, serial, each alone):
  - (i) First-sighting mislabels kept true: DIVERGED, onset 60.632 s. This was a failed prediction; I had predicted a
    later collapse.
  - (ii) Only the two first-sighting wrong factors left: 2.7707 m LC live (48× clean), with a distorted map.
  - The earlier cf2 runs have no first-sighting mislabels and still collapse (spread 1.063 and 1.103 m, against 3.674 m).
- **Which assumption failed.** The pre-registered "+20%" treated the correct factors of a pass or a landmark as an anchor.
  They are relative, so no wrong factor is isolated.

## Files

- **Scripts** (`docs/thesis/tier1/stage2e/diag_collapse/`): `reconstruct.py`, `analyse.py`, `status_cf.py`, `figs.py`,
  `check_prose_collapse.py` (exact prose check, 0 missing), `predictions.md`, and the job scripts.
- **Data** (`~/thesis_data/tier1/stage2e/diag_collapse/`): `summary.json`, `recon_*.json`, `status/`, `score_cf*.json`,
  `logs/`, `timing.tsv`, and the two counterfactual outputs under `T_A_r1/`.
- **Figures:** `docs/thesis/tier1/figs/e3_collapse_{timecourse,maps,counterfactuals}.png`.

## Machine time

91 s + 3419 s for the two replays (heavy.py wall-clock). Checksum guard verify after the runs: IDENTICAL, 13,253
files (`frozen_manifest_20261022T002851_verify_e3collapse_*.json`). No verify was run immediately before the replays (the
last was stage 2e's, 06:57); the replays wrote only under `~/thesis_data/tier1/stage2e/diag_collapse/` (decision D9). The read-only analysis took minutes.

## Open

- **Robust T_A_r2 5% s1.** Its higher Cauchy cost at the estimate than at the truth suggests a local minimum, but this
  was not tested by counterfactual.
- **IMU and range costs were not evaluated.** The flow cost is a proxy.
- **Next:** E4, strictly one job at a time (decisions D1, D2).
