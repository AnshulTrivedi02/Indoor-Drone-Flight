# Closed loop with heading: per-flight values (thesis-facing numbers addendum)

Read-only extraction from the stored score files `eval/results/closed_loop_<trial>.json` (written by `eval/closed_loop_score.py`; nothing re-scored), by `eval/cl_heading_perflight.py`. numbers.md is content-frozen and gives these sets only as ranges (§15, lines 476-485); this file adds the per-flight values. Rounding: `rd()` of `eval/figs_thesis.py`, once (m and degrees to 2 dp, m/s to 3 dp). Experiment 1C, textured corridor, 0.5 m/s, 300 s cruise. Every set below is CURRENT as recorded (the B5 window is D28's).

**Heading-node build of each EKF3 set**, from each trial's own `metadata.yaml`: `cl_bcpp_tex_r1–r3` and `cl_bcpp_tex_r1–r3_half` record `impl: cpp` (the C++ heading node); `cl_b_tex_r1–r3` have no `impl` field: their metadata (2026-09-29 23:52) predates the commit that added the C++ port and the field (`f12bed2`, 2026-09-30 00:18), so they flew the Python heading node, the only one that existed. This confirms D70's `cl_bcpp_tex_r1..r3_half` as the C++ node.

| set | flight | B2 max \|cross-track\| in cruise (m) | B3 heading error p95 (°) | B3 heading error max (°) | B4 max lateral speed (m/s) | B1–B5 | S2 |
|---|---|---|---|---|---|---|---|
| EKF3, full speed (RTF 1.0), Python heading node | 1 (`cl_b_tex_r1`) | 0.27 | 0.36 | 0.54 | 0.033 | all pass | — |
| EKF3, full speed (RTF 1.0), Python heading node | 2 (`cl_b_tex_r2`) | 0.31 | 0.28 | 0.31 | 0.019 | all pass | — |
| EKF3, full speed (RTF 1.0), Python heading node | 3 (`cl_b_tex_r3`) | 0.29 | 0.28 | 0.34 | 0.017 | all pass | — |
| EKF3, full speed (RTF 1.0), C++ heading node | 1 (`cl_bcpp_tex_r1`) | 0.25 | 0.31 | 0.42 | 0.140 | all pass | — |
| EKF3, full speed (RTF 1.0), C++ heading node | 2 (`cl_bcpp_tex_r2`) | 0.23 | 0.28 | 0.40 | 0.027 | all pass | — |
| EKF3, full speed (RTF 1.0), C++ heading node | 3 (`cl_bcpp_tex_r3`) | 0.34 | 0.29 | 0.42 | 0.021 | all pass | — |
| EKF3, half real time (RTF 0.5), C++ heading node | 1 (`cl_bcpp_tex_r1_half`) | 0.33 | 0.32 | 0.39 | 0.181 | all pass | — |
| EKF3, half real time (RTF 0.5), C++ heading node | 2 (`cl_bcpp_tex_r2_half`) | 0.25 | 0.28 | 0.34 | 0.044 | all pass | — |
| EKF3, half real time (RTF 0.5), C++ heading node | 3 (`cl_bcpp_tex_r3_half`) | 0.24 | 0.29 | 0.33 | 0.027 | all pass | — |
| original FGO, hard-gated, half real time | 1 (`cl_fgo_b_tex_r1_half`) | 0.06 | 0.26 | 1.44 | 0.037 | all pass | — |
| original FGO, hard-gated, half real time | 2 (`cl_fgo_b_tex_r2_half`) | 0.08 | 0.26 | 1.28 | 0.013 | all pass | — |
| original FGO, hard-gated, half real time | 3 (`cl_fgo_b_tex_r3_half`) | 0.25 | 0.38 | 1.88 | 0.120 | all pass | — |
| original FGO, robust weighting, half real time | 1 (`cl_fgo_b_robust_tex_r1_half`) | 0.08 | 0.26 | 0.86 | 0.014 | all pass | — |
| original FGO, robust weighting, half real time | 2 (`cl_fgo_b_robust_tex_r2_half`) | 0.14 | 0.29 | 0.95 | 0.019 | all pass | — |
| original FGO, robust weighting, half real time | 3 (`cl_fgo_b_robust_tex_r3_half`) | 0.05 | 0.30 | 1.15 | 0.040 | all pass | — |

*B3 uses EKF3's yaw for the EKF3 sets and the FGO's current-time yaw for the FGO sets (`--est fgo`). Bounds: B2 ≤ 6.0 m; B3 p95 ≤ 1.0°, max ≤ 2.0°; B4 ≤ 0.25 m/s. S2 (estimator validity) is scored for the FGO sets only where the score file carries it.*

*Checks (EXACT): 25/25 — every value against its score file; the half real-time EKF3 row against Table 4.3; the per-set min–max against numbers.md's recorded ranges; the heading-node build against each trial's metadata.yaml.*
