# E5: UKF with tag landmark states, results (Stage 2c)

**Extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22).**
- Pre-registration: `preregistration.md` §4. Design: `e5_design.md`.
- This page records the numbers and the mechanical verdict each pre-registered decision rule gives. It does not
  interpret them against the hypotheses beyond that.
- **Code:** `fwd-camera` at `e42b9ce`, run from the main checkout. The E5 code snapshot is
  `e5_code_manifest_20261022T011805.json` (4 files); it was verified IDENTICAL after the last E5 run.
- **Run:** 2026-10-22, 01:18–02:06 AEDT, serial, one `heavy.py` job at a time, thread variables at 1, `~/venv-evo`.
  The job mechanism is recorded in `numbers_tier1.md` §Deviations.
- **Every number below** was printed by `stage2c/crosscheck.py` (copy in `docs/thesis/tier1/stage2c/`) from the cited
  json, rounded once: positions to 4 dp in m, ratios to 2 dp, and V-E5 differences in µm. Verdicts are computed on the
  unrounded json values by `stage2c/e5_verdicts.py`, which writes `scores/e5_verdicts.json`.

## 1. Validation gates V-E5a/b/c (HARD gate; `e5_design.md` §8.4)

All 12 flights `T_{A,B,C,D}_r{1,2,3}` were run uncut, with the `/tags/sent` anchor and input. The order per flight was
world, then known-map, then augmented. Each run was judged by `eval/e5_val_compare.py --delta-rmse` against the stored
`~/thesis_data/trials/<trial>/room_ukf/`, and the judge's output is `scores/ve5{a,b,c}_<trial>.json`.

**Result: 36/36 PASS.** V-E5a 12/12, V-E5b 12/12, V-E5c 12/12.

| gate | PASS | rows 1:1 | `t_anchor`, `n_tag_fused` equal | byte-identical (live / RTS) | worst RMS in window (≤ 1000 µm) | worst max in window (≤ 2000 µm) | worst \|ΔRMSE\| vs GT (reported) | flips of a gated decision |
|---|---|---|---|---|---|---|---|---|
| V-E5a (world, `ukf_core`) | 12/12 | 12/12 | 12/12 | 12/12 / 12/12 | 0.000 µm | 0.000 µm | 0.000 µm | reference |
| V-E5b (known map, fixed landmarks) | 12/12 | 12/12 | 12/12 | 0/12 / 0/12 | 0.193 µm (`ve5b_T_D_r2.json:live.rms_window_m`) | 1.414 µm (`ve5b_T_D_r2.json:live.max_window_m`) | 0.004 µm (`ve5b_T_C_r2.json:live.rmse_vs_gt_m.abs_delta`) | 0 on 12/12 |
| V-E5c (known map, augmented at 1e-10) | 12/12 | 12/12 | 12/12 | 0/12 / 0/12 | 1.993 µm (`ve5c_T_B_r2.json:live.rms_window_m`) | 4.243 µm (`ve5c_T_B_r3.json:live.max_window_m`) | 1.278 µm (`ve5c_T_B_r3.json:live.rmse_vs_gt_m.abs_delta`) | 0 on 12/12 |

- "Worst" means the maximum over the 12 flights × {live, RTS}. The per-flight values are in each json (`live`, `rts`,
  `anchor_tagcount`, `gates`).
- V-E5a reproduces the stored Experiment 2 UKF byte for byte on all 24 files.
- V-E5b and V-E5c differ only at the 6-dp TUM quantum: 1.414 µm = √2 µm, and 4.243 µm = 3√2 µm. That is about
  500× inside the RMS bound and about 470× inside the max bound.
- No flow or range accept/reject decision differs from V-E5a on any flight (`gates.n_flips` 0).

## 2. Result runs (T_A_r1–r3, LC and no-LC, cut at anchor + 245 s)

**Outputs:** `~/thesis_data/tier1/T_A_r{1,2,3}/lc_ukf_{lc,nolc}_t245/`. All six exited 0.

**Scoring:** `eval/l_score.py <trial> --in-root ~/thesis_data/tier1 --prefix lc_ukf --suffix _t245`, under
`~/venv-evo`, writing `scores/e5_<trial>.json`.
- The lap bounds equal the stored Experiment 3 bounds (`lap_bounds_s`, identical lists; T_A_r1 29.52–269.57 s).
- The frame is tag 0's, and there is no alignment.

### 2.1 §5.3 invariants (a failure stops E5 before scoring): all MET

The source is `~/thesis_data/tier1/<trial>/lc_ukf_<mode>_t245/stats.json:invariants`. Each value is compared with the
stored `~/thesis_data/trials/<trial>/lc_fgo_<mode>_t245/stats.json`.

| flight | mode | `t_anchor` E5 = FGO (s) | landmarks E5 = FGO | tag measurements used E5 / FGO `landmark_factors` (reported) | pass |
|---|---|---|---|---|---|
| T_A_r1 | lc | 28.546 = 28.546 | 8 = 8 | 2145 / 2145 | yes |
| T_A_r1 | nolc | 28.546 = 28.546 | 41 = 41 | 2145 / 2145 | yes |
| T_A_r2 | lc | 28.975 = 28.975 | 8 = 8 | 2057 / 2057 | yes |
| T_A_r2 | nolc | 28.975 = 28.975 | 41 = 41 | 2057 / 2057 | yes |
| T_A_r3 | lc | 28.744 = 28.744 | 8 = 8 | 2038 / 2038 | yes |
| T_A_r3 | nolc | 28.744 = 28.744 | 41 = 41 | 2038 / 2038 | yes |

- The tag-measurement count matches exactly in all six runs, so there is no mismatch to explain.
- **Also from `stats.json` (descriptive):**
  - maximum state dimension 36 (LC) and 18 (no-LC);
  - no-LC landmarks dropped: 39 per flight;
  - Cholesky retries 0 and eigen fallbacks 0 in all six runs;
  - no flow or range rejections;
  - the RTS store stayed in RAM (no memmap spill; about 0.47 GB in LC).

### 2.2 Per-flight horizontal RMSE (m)

The source for each row is `json:docs/thesis/tier1/scores/e5_<trial>.json:tracks.<track>` (`rmse_m`, `max_m`,
`per_lap_rmse_m[0..4]`). "Hindsight" is the RTS over the augmented state.

| flight | track | overall RMSE | max | lap 1 | lap 2 | lap 3 | lap 4 | lap 5 | lap 5 / lap 1 |
|---|---|---|---|---|---|---|---|---|---|
| T_A_r1 | LC live | 0.1193 | 0.5559 | 0.2240 | 0.0908 | 0.0657 | 0.0690 | 0.0601 | 0.27 |
| T_A_r1 | LC RTS | 0.0445 | 0.0688 | 0.0466 | 0.0427 | 0.0439 | 0.0450 | 0.0444 | 0.95 |
| T_A_r1 | no-LC live | 0.8738 | 2.1130 | 0.2240 | 0.3488 | 0.4712 | 1.0266 | 1.5395 | 6.87 |
| T_A_r1 | no-LC RTS | 0.9162 | 2.0494 | 0.1355 | 0.3504 | 0.6661 | 1.0844 | 1.5608 | 11.51 |
| T_A_r2 | LC live | 0.0911 | 0.3859 | 0.1560 | 0.0734 | 0.0624 | 0.0604 | 0.0652 | 0.42 |
| T_A_r2 | LC RTS | 0.0461 | 0.0797 | 0.0478 | 0.0484 | 0.0434 | 0.0464 | 0.0445 | 0.93 |
| T_A_r2 | no-LC live | 1.4112 | 3.0375 | 0.1560 | 0.7522 | 1.2260 | 1.6324 | 2.2801 | 14.62 |
| T_A_r2 | no-LC RTS | 1.3349 | 2.9905 | 0.2253 | 0.5849 | 1.0476 | 1.5941 | 2.2087 | 9.80 |
| T_A_r3 | LC live | 0.1335 | 0.5132 | 0.2565 | 0.0874 | 0.0715 | 0.0692 | 0.0757 | 0.30 |
| T_A_r3 | LC RTS | 0.0552 | 0.0955 | 0.0563 | 0.0543 | 0.0553 | 0.0541 | 0.0560 | 0.99 |
| T_A_r3 | no-LC live | 0.9262 | 2.2633 | 0.2565 | 0.3332 | 0.5679 | 1.0709 | 1.6257 | 6.34 |
| T_A_r3 | no-LC RTS | 1.0446 | 2.3304 | 0.1628 | 0.4242 | 0.7820 | 1.2255 | 1.7709 | 10.88 |

Lap-1 LC live equals lap-1 no-LC live on every flight (0.2240 / 0.1560 / 0.2565), as the pre-registration expects:
lap 1 is dead reckoning from the anchor in both modes.

### 2.3 Mechanical verdicts

The source is `json:docs/thesis/tier1/scores/e5_verdicts.json:criteria.<id>`. Each verdict was judged on 3/3
completed runs that passed their gates. Every input value is listed in that json under `flights.<trial>.values` with its
source key. The stored FGO values come from `json:eval/results/expL/T_A_r<i>_t245.json:tracks.lc {live,hindsight}.rmse_m`.

| id | criterion | per flight (r1 / r2 / r3) | count | verdict |
|---|---|---|---|---|
| **H-E5.1 (PRIMARY)** | UKF-LC live lap-5 ≤ 1.5 × lap-1 | ratio 0.27 / 0.42 / 0.30 | 3/3 | **PASS** |
| H-E5.2 | UKF-LC live overall < UKF-no-LC live overall | 0.1193 < 0.8738; 0.0911 < 1.4112; 0.1335 < 0.9262 | 3/3 | **PASS** |
| H-E5.3 | UKF-LC RTS overall < UKF-no-LC RTS overall | 0.0445 < 0.9162; 0.0461 < 1.3349; 0.0552 < 1.0446 | 3/3 | **PASS** |
| P-E5.4 | UKF-no-LC live lap-5 > 1.5 × lap-1 | ratio 6.87 / 14.62 / 6.34 | 3/3 | **PASS** |
| S-E5.5 (secondary, registered direction) | UKF-LC live overall > stored FGO-LC live overall | 0.1193 > 0.0574; 0.0911 > 0.0494; 0.1335 > 0.0760 | 3/3 | **PASS** (direction held) |
| S-E5.6 (secondary, registered direction) | UKF-LC RTS overall > stored FGO-LC hindsight overall | 0.0445 > 0.0198; 0.0461 > 0.0270; 0.0552 > 0.0172 | 3/3 | **PASS** (direction held) |

**S-E5.6 mapping of "batch":** the FGO side is the Experiment 3 hindsight, iSAM2's full-graph estimate after 5 extra
updates (DEVIATION, M:10557), not an LM batch.

**Descriptive only (no verdict)**, from `e5_verdicts.json:flights.<trial>`:

| flight | UKF ÷ FGO, LC live | LC hindsight | no-LC live | no-LC hindsight | UKF LC ÷ no-LC, live | RTS |
|---|---|---|---|---|---|---|
| T_A_r1 | 2.08 | 2.25 | 2.50 | 4.15 | 0.14 | 0.05 |
| T_A_r2 | 1.84 | 1.71 | 5.38 | 5.45 | 0.06 | 0.03 |
| T_A_r3 | 1.76 | 3.21 | 2.57 | 3.93 | 0.14 | 0.05 |

## 3. Guard verifies (after the last E5 run)

| manifest | result | report |
|---|---|---|
| `frozen_manifest_20261022T002851.json` (13,253 files) | **IDENTICAL**, exit 0 | `frozen_manifest_20261022T002851_verify_stage2c_20261022T023631.json` |
| `e5_code_manifest_20261022T011805.json` (4 E5 files) | **IDENTICAL**, exit 0 | `e5_code_manifest_20261022T011805_verify_20261022T023631.json` |

## 4. Wall times (DIAGNOSTIC; driver-measured around `heavy.py`, from `stage2c/timing.tsv`)

| run | n | per run (s) | total (s) | §8 planning figure |
|---|---|---|---|---|
| V-E5a (world) | 12 | 49.6–53.2 | 612.9 | ≤ 126 |
| V-E5b (known-map) | 12 | 50.1–55.1 | 616.8 | ≤ 126 |
| V-E5c (augmented) | 12 | A 135.5–138.7; B 90.7–93.4; C 69.1–70.7; D 59.9–61.6 | 1,081.1 | ≤ 126 (exceeded on A and B, as the implementation handover predicted) |
| E5 LC | 3 | 115.6–117.6 | 350.0 | ≤ 630 |
| E5 no-LC | 3 | 54.1–54.6 | 162.9 | ≤ 189 |
| 36 judges | 36 | 0.9–1.0 | 33 | — |

- **Total, first job start to last job end:** 01:18:25–02:06:20, about 48 min.
- The V-E5 total of 2,311 s is inside §8's 1.3 h for the E5 validation, even though V-E5c on A and B exceeds the
  per-run planning figure.
