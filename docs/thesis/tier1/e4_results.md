# E4 results: live window sweep (Experiment 2 FGO)

**Extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22).** Pre-registration:
`preregistration.md` §3. Stage 2f, 2026-10-23 to 2026-10-24 (AEDT). All values come from `scores/E4_verdicts.json`, which
`~/thesis_data/tier1/stage2f/e4_verdicts.py` builds from each run's `stats.json`, `fgo_live.tum`, `stage2f/status/<job>.json` and
`scores/E4_<trial>_w<W>[_lm10].json` (`eval/tag_score.py`). Tables: `stage2f/make_tables.py`, with every value rounded once.

## 1. Summary

- **Runs:** 58 of 58 completed on the first try (rc 0, no re-run, no crash, no NOT RUN): 48 main runs and 10 LM-cap-10 runs.
  The 12 W = 0.25 s cap-2 runs are the Stage 2a G-E4 runs (byte-identical to the stored Experiment 2 FGO). **All 70 runs
  are status OK:** 0 keyframe failures and no non-finite value in any `fgo_live.tum`.
- **Verdicts:**
  - **P-E4.1 PASS 12/12.** The median step time after the anchor rises strictly with the window on every flight.
  - **P-E4.2 PASS.** 12/12 at 0.25 s (≤ 33 ms), and 12/12 at each of 1, 2 and 5 s (> 33 ms), on both median readings.
  - **H-E4.3 FAIL 7/12** (band ≥ 10/12). Live RMSE at 5 s was lower than at 0.25 s on all three D flights, two C flights,
    one B flight and one A flight. On the other five it was higher by +0.0000020 to +0.0003395 m.
- **Gain fraction (DESCRIPTIVE):** F(W) pooled is 0.01 / -0.00 / 0.02 / 0.02 at W = 0.5 / 1 / 2 / 5 s. A longer window
  recovers almost none of the gap between live and the stored whole-flight batch.
- **LM cap:** cap 2 is converged at every window on T_A_r1 and T_D_r1. The largest RMS reading is 0.0009 m, against the
  0.029 m threshold, so no flag is raised and H-E4.3 carries no qualifier.
- **Null result (§3):** a longer window does not buy live accuracy on these flights. That confirms the 0.25 s choice on the
  room world too, at a far lower compute cost: the median step after the anchor is 14.35–15.13 ms at 0.25 s and
  278.25–303.36 ms at 5 s.

## 2. How it was run

- **Driver:** `~/thesis_data/tier1/stage2f/driver.sh`, mirrored in `docs/thesis/tier1/stage2f/`.
  - Strictly one `heavy.py` job at a time (decision D1), nice 19, thread variables at 1 (TBB included).
  - Order (D10): flight-major with W ascending, then LM-10.
  - Hang guard (D11): min(48 h, time to the lock).
  - Code: every run's `stats.json` records commit `2eb6852` with empty `src_dirty`. That commit holds the driver, the job
    scripts and decisions D10–D15, and was made before the first job.
  - Start and end: 2026-10-23 11:28:45 AEDT to 2026-10-24 04:33:39 AEDT.
- **Job command:** `room_fgo_replay.py <trial> --no-batch --window <W> [--lm-iters 10] --out-root ~/thesis_data/tier1`.
  Output: `~/thesis_data/tier1/<trial>/room_fgo_w<W>[_lm10]/`.
- **Contamination check (DESCRIPTIVE):** the 1-minute load average at each job's start and end is logged in
  `stage2f/timing.tsv`.
  - No job waited on another lock: no `[heavy] waiting` line appears in any job log.
  - The largest 1-minute load was 4.27, on a 12-thread machine, from the end of `e4_T_A_r1_w5` to the start of
    `e4_T_A_r2_w0.5`. The second-largest was 2.91 (`e4_T_A_r2_w0.5`/`e4_T_A_r2_w1`). Every other reading is ≤ 2.
  - The source was not identified. It was not a `heavy.py` job, because none waited on BUILD_LOCK.
  - The P-E4.1 and P-E4.2 margins are far larger than any such effect: the medians at 0.25, 0.5 and 1 s (§3 table)
    sit well clear of one another and of the 33 ms line.
- **Guard:** `verify` before the first job and after the last both returned **IDENTICAL**, exit 0, 13,253 files
  (`frozen_manifest_20261022T002851_verify_stage2f_pre_*.json`, `…_post_*.json`).
- **Status:** `stage2f/run_status.py` (`stage2f/status.tsv`, and `status_w0.25.tsv` for the Stage 2a runs).

## 3. Tables

### Run status and driver wall time (DIAGNOSTIC; 0.25 s cap 2 = Stage 2a G-E4 runs)

| W (s) | cap | runs completed | status OK / FAILED-ESTIMATOR | driver wall min–max (s) | mean (s) |
|---|---|---|---|---|---|
| 0.25 | 2 | 12/12 | 12 / 0 | 130.7–154.8 | 141.3 |
| 0.5 | 2 | 12/12 | 12 / 0 | 244.4–285.6 | 261.8 |
| 1 | 2 | 12/12 | 12 / 0 | 458.3–533.2 | 486.3 |
| 2 | 2 | 12/12 | 12 / 0 | 901.7–1051.5 | 964.8 |
| 5 | 2 | 12/12 | 12 / 0 | 2468.1–2917.0 | 2645.2 |
| 0.25 | 10 | 2/2 | 2 / 0 | 136.8–155.6 | 146.2 |
| 0.5 | 10 | 2/2 | 2 / 0 | 243.5–291.0 | 267.2 |
| 1 | 10 | 2/2 | 2 / 0 | 464.8–524.2 | 494.5 |
| 2 | 10 | 2/2 | 2 / 0 | 913.6–1059.6 | 986.6 |
| 5 | 10 | 2/2 | 2 / 0 | 2514.9–2887.4 | 2701.2 |

### Per-step time after the anchor, median / p95 (ms; DIAGNOSTIC: workstation Python, 1 thread, nice 19, serial)

| flight | W = 0.25 s | W = 0.5 s | W = 1 s | W = 2 s | W = 5 s | strictly increasing (P-E4.1) |
|---|---|---|---|---|---|---|
| T_A_r1 | 15.04 / 30.55 | 26.86 / 55.05 | 50.66 / 104.09 | 103.31 / 208.42 | 289.85 / 588.34 | yes |
| T_A_r2 | 14.96 / 30.27 | 27.97 / 57.51 | 52.74 / 108.68 | 107.12 / 217.73 | 303.36 / 584.62 | yes |
| T_A_r3 | 14.96 / 30.26 | 27.89 / 57.37 | 52.31 / 107.11 | 105.04 / 212.63 | 296.82 / 572.50 | yes |
| T_B_r1 | 14.81 / 29.85 | 27.47 / 55.25 | 50.47 / 103.27 | 102.29 / 207.65 | 288.78 / 560.50 | yes |
| T_B_r2 | 14.51 / 29.35 | 27.55 / 55.38 | 50.94 / 104.61 | 103.15 / 209.65 | 290.75 / 562.35 | yes |
| T_B_r3 | 14.76 / 30.11 | 28.07 / 56.61 | 51.10 / 105.49 | 102.29 / 212.98 | 289.89 / 569.60 | yes |
| T_C_r1 | 14.65 / 29.56 | 27.96 / 55.61 | 52.40 / 106.57 | 102.26 / 212.64 | 280.95 / 563.34 | yes |
| T_C_r2 | 14.64 / 29.53 | 27.48 / 54.55 | 51.56 / 104.61 | 101.14 / 205.16 | 281.04 / 546.49 | yes |
| T_C_r3 | 14.61 / 29.66 | 28.22 / 56.49 | 51.38 / 106.07 | 104.34 / 217.06 | 279.53 / 560.81 | yes |
| T_D_r1 | 14.35 / 27.69 | 26.95 / 52.92 | 50.58 / 100.25 | 100.05 / 197.90 | 278.25 / 537.95 | yes |
| T_D_r2 | 14.41 / 29.12 | 28.18 / 55.09 | 50.71 / 103.38 | 100.51 / 209.52 | 280.32 / 559.06 | yes |
| T_D_r3 | 15.13 / 30.05 | 27.38 / 53.54 | 51.36 / 103.87 | 101.23 / 201.73 | 282.74 / 547.54 | yes |

### Median step time over ALL keyframes (ms; DIAGNOSTIC; P-E4.2 second reading, D13)

| flight | W = 0.25 s | W = 0.5 s | W = 1 s | W = 2 s | W = 5 s |
|---|---|---|---|---|---|
| T_A_r1 | 15.08 | 26.86 | 50.58 | 103.11 | 288.82 |
| T_A_r2 | 15.01 | 28.00 | 52.68 | 106.88 | 302.97 |
| T_A_r3 | 15.01 | 27.92 | 52.19 | 104.86 | 296.31 |
| T_B_r1 | 14.83 | 27.49 | 50.51 | 102.28 | 288.44 |
| T_B_r2 | 14.52 | 27.57 | 50.97 | 103.16 | 290.46 |
| T_B_r3 | 14.79 | 28.08 | 51.08 | 102.38 | 289.12 |
| T_C_r1 | 14.67 | 27.98 | 52.44 | 102.28 | 280.94 |
| T_C_r2 | 14.66 | 27.51 | 51.63 | 101.19 | 281.05 |
| T_C_r3 | 14.63 | 28.24 | 51.39 | 104.38 | 279.39 |
| T_D_r1 | 14.36 | 26.97 | 50.61 | 100.09 | 278.21 |
| T_D_r2 | 14.43 | 28.18 | 50.74 | 100.54 | 280.24 |
| T_D_r3 | 15.14 | 27.40 | 51.40 | 101.27 | 282.72 |

### FGO live horizontal RMSE in the lap window (m; world frame, no alignment) and the stored batch B_i

| flight | W = 0.25 s | W = 0.5 s | W = 1 s | W = 2 s | W = 5 s | stored batch B_i | L(5) < L(0.25) (H-E4.3; L(5) − L(0.25), unrounded) |
|---|---|---|---|---|---|---|---|
| T_A_r1 | 0.0214 | 0.0214 | 0.0214 | 0.0214 | 0.0214 | 0.0106 | no (+0.0000035 m) |
| T_A_r2 | 0.0196 | 0.0196 | 0.0196 | 0.0196 | 0.0196 | 0.0107 | yes (-0.0000010 m) |
| T_A_r3 | 0.0190 | 0.0190 | 0.0190 | 0.0190 | 0.0190 | 0.0101 | no (+0.0000020 m) |
| T_B_r1 | 0.0233 | 0.0230 | 0.0233 | 0.0232 | 0.0231 | 0.0144 | yes (-0.0001880 m) |
| T_B_r2 | 0.0292 | 0.0292 | 0.0292 | 0.0292 | 0.0292 | 0.0142 | no (+0.0000108 m) |
| T_B_r3 | 0.0252 | 0.0252 | 0.0252 | 0.0252 | 0.0252 | 0.0153 | no (+0.0000082 m) |
| T_C_r1 | 0.0538 | 0.0546 | 0.0542 | 0.0540 | 0.0542 | 0.0194 | no (+0.0003395 m) |
| T_C_r2 | 0.0502 | 0.0501 | 0.0495 | 0.0497 | 0.0497 | 0.0191 | yes (-0.0004784 m) |
| T_C_r3 | 0.0565 | 0.0564 | 0.0559 | 0.0561 | 0.0562 | 0.0188 | yes (-0.0003000 m) |
| T_D_r1 | 0.0931 | 0.0901 | 0.0863 | 0.0890 | 0.0887 | 0.0272 | yes (-0.0043321 m) |
| T_D_r2 | 0.0813 | 0.0814 | 0.0906 | 0.0803 | 0.0798 | 0.0261 | yes (-0.0015134 m) |
| T_D_r3 | 0.0745 | 0.0743 | 0.0739 | 0.0738 | 0.0738 | 0.0309 | yes (-0.0006587 m) |

### Fraction of the batch gain recovered (DESCRIPTIVE, no band)

| W (s) | F(W) pooled, 12 flights | F A | F B | F C | F D | median f_i | f_i min–max | flights |
|---|---|---|---|---|---|---|---|---|
| 0.5 | 0.01 | 0.00 | 0.01 | -0.00 | 0.02 | 0.00 | -0.02–0.05 | 12 |
| 1 | -0.00 | 0.00 | 0.00 | 0.01 | -0.01 | 0.00 | -0.17–0.10 | 12 |
| 2 | 0.02 | -0.00 | 0.00 | 0.01 | 0.04 | 0.01 | -0.00–0.06 | 12 |
| 5 | 0.02 | -0.00 | 0.00 | 0.00 | 0.04 | 0.00 | -0.01–0.07 | 12 |

LM-cap-10 rows (f_i, L_i(0.25) = the cap-2 0.25 s run): T_A_r1 W 0.25: 0.00, W 0.5: 0.00, W 1: -0.00, W 2: -0.00, W 5: -0.00; T_D_r1 W 0.25: -0.00, W 0.5: 0.04, W 1: 0.10, W 2: 0.06, W 5: 0.07

### LM cap 2 vs cap 10 (D12; flag iff any RMS reading > 0.029 m)

| flight, W (s) | paired rows (unmatched) | horiz RMS / max, all (m) | 3D RMS / max, all (m) | horiz RMS, lap (m) | 3D RMS, lap (m) | live RMSE cap 2 / cap 10 (m) | Δ RMSE (m) | flag |
|---|---|---|---|---|---|---|---|---|
| T_A_r1, 0.25 | 7774 (0) | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.0214 / 0.0214 | -0.0000 | converged |
| T_A_r1, 0.5 | 7774 (0) | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.0214 / 0.0214 | -0.0000 | converged |
| T_A_r1, 1 | 7774 (0) | 0.0000 / 0.0002 | 0.0000 / 0.0002 | 0.0000 | 0.0000 | 0.0214 / 0.0214 | -0.0000 | converged |
| T_A_r1, 2 | 7774 (0) | 0.0000 / 0.0015 | 0.0000 / 0.0016 | 0.0000 | 0.0000 | 0.0214 / 0.0214 | -0.0000 | converged |
| T_A_r1, 5 | 7774 (0) | 0.0000 / 0.0017 | 0.0000 / 0.0017 | 0.0000 | 0.0000 | 0.0214 / 0.0214 | -0.0000 | converged |
| T_D_r1, 0.25 | 7755 (0) | 0.0000 / 0.0001 | 0.0000 / 0.0001 | 0.0000 | 0.0000 | 0.0931 / 0.0931 | +0.0000 | converged |
| T_D_r1, 0.5 | 7755 (0) | 0.0001 / 0.0056 | 0.0009 / 0.0206 | 0.0000 | 0.0000 | 0.0901 / 0.0901 | +0.0000 | converged |
| T_D_r1, 1 | 7755 (0) | 0.0001 / 0.0057 | 0.0002 / 0.0207 | 0.0000 | 0.0000 | 0.0863 / 0.0863 | +0.0000 | converged |
| T_D_r1, 2 | 7755 (0) | 0.0001 / 0.0051 | 0.0002 / 0.0206 | 0.0000 | 0.0000 | 0.0890 / 0.0890 | +0.0000 | converged |
| T_D_r1, 5 | 7755 (0) | 0.0001 / 0.0051 | 0.0002 / 0.0205 | 0.0000 | 0.0000 | 0.0887 / 0.0887 | +0.0000 | converged |

### Verdicts

| criterion | verdict | count |
|---|---|---|
| P-E4.1: median step (after the anchor) strictly increasing 0.25 < 0.5 < 1 < 2 < 5 s, 12/12 | **PASS** | 12/12 |
| P-E4.2: median ≤ 33 ms at 0.25 s and > 33 ms at W ≥ 1 s, 12/12 at each (both readings, D13) | **PASS** | 0.25 s: 12/12, 1 s: 12/12, 2 s: 12/12, 5 s: 12/12; 0.5 s (DESCRIPTIVE, on the budget): 12/12 ≤ 33 ms |
| **H-E4.3**: live RMSE at 5 s < at 0.25 s, ≥ 10/12 (≥ 10/12: judgement, not derived from data) | **FAIL** | 7/12 |

Notes on reading the tables:
- **Gain fractions.** A printed `-0.00` is a small negative value rounded once to 2 dp. f_i < 0 means live is worse than at
  0.25 s.
- **Live RMSE is flat in W on the A and B flights.** It moves by at most a few tenths of a millimetre. The largest changes
  are on the D flights, where the fixes are sparsest. They go both ways:
  T_D_r2 is worse at 1 s (0.0906 m) and better at 5 s (0.0798 m). This is descriptive; no criterion covers W = 1 s accuracy.
- **Cap 2 vs cap 10.** The 3D maximum differences of about 0.02 m on T_D_r1 lie outside the lap window: inside it, the
  horizontal and 3D RMS are 0.0000 m at 4 dp. None of the four RMS readings comes near 0.029 m.
- **Run time.** Driver wall time scales roughly linearly with W. Cap 10 cost about the same as cap 2 at every window (wall
  means in the first table), so LM appears to converge within two iterations here. This is an inference from wall time
  only; iteration counts were not logged.

## 4. Verdicts against the registered wording

- **P-E4.1** ("the median step time (after the anchor) increases strictly with W: 0.25 < 0.5 < 1 < 2 < 5 s", 12/12):
  **PASS, 12/12.**
- **P-E4.2** ("the median is ≤ 33 ms at W = 0.25 s and > 33 ms at W ≥ 1 s", 12/12 at each): **PASS.**
  - Both the all-keyframe and the after-anchor medians pass on 12/12 at 0.25, 1, 2 and 5 s (D13).
  - W = 0.5 s is descriptive. It was predicted at about 31–33 ms; it measured 26.86–28.22 ms after the anchor, inside the
    budget on 12/12.
- **H-E4.3** ("live RMSE at W = 5 s < live RMSE at W = 0.25 s", ≥ 10/12; the band is judgement, not derived from data):
  **FAIL, 7/12.**
  - Scored on the unrounded values, as registered.
  - The five failing flights (T_A_r1, T_A_r3, T_B_r2, T_B_r3, T_C_r1) are higher at 5 s by +0.0000020 to +0.0003395 m.
  - All three D flights are lower at 5 s (by 0.0043321, 0.0015134 and 0.0006587 m).
  - No claim beyond the verdict is made. The data do not show that a longer window improves live accuracy at the
    registered count. The D-flight direction is a descriptive observation from three flights.
- **Convergence flags:** none at any window (D12: flag iff any RMS reading > 0.029 m).

## 5. Decisions and deviations

- **Decisions:** D10–D15 (`decisions_log.md`) were all taken before the first job. No decision was needed after any result
  was read.
- **Deviations:** one row in `numbers_tier1.md` §Deviations, the Stage 2f mechanism, written before the first job.
- **Diagnosis:** none. No result is more than 10× off its pre-registered estimate. The §8 planning figure for 5 s (2,910 s)
  compares with a measured mean of 2,645.2 s. The LM-10 runs were budgeted at ≤ 5× cap 2 and measured about 1×.
