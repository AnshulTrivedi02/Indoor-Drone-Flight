# E6: map reuse ("map once, fly again"), results (Stage 2)

**Extension experiment E6, pre-registered (2026-10-31)** in `e6_preregistration.md` (committed `6c0365b` before any E6
run).
- This page records the numbers and the mechanical verdict that each pre-registered rule gives. The reading in §4 is
  plain language. No claim in it is stronger than its verdict.
- **Code:** branch `e6-map-reuse`, run from the worktree. 2a ran at `18da989` and 2b at `aabac1e`, which adds only the Stage 2 driver, its timing file, D95 and
  guard reports to `18da989` (no estimator or scorer code; `src_dirty` is empty in every `stats.json`).
- **Run:** 2026-10-31 23:16 to 2026-11-01 01:07 AEDT, serial, one `heavy.py` job at a time, thread variables at 1.
- **Every number below** was built by `e6/e6_tables.py` from the score jsons, rounded once. Positions are in m at 4 dp;
  ratios are at 2 dp. `e6/check_e6_prose.py` re-builds every table row and every hand-typed number and requires string
  equality in this file, in `e6_numbers.md` §Results and in the Stage 2 handover (0 mismatches).
- **Verdicts** are computed on the unrounded json values by `eval/e6_verdicts.py` (written in Stage 1, D93), which writes
  `scores/e6_verdicts.json`.
- **Pairing (D85, D94):** map from `E6M_fig8_r1b` → test flight `T_A_r1`, `E6M_fig8_r2` → `T_A_r2`, `E6M_fig8_r3` →
  `T_A_r3`.

## 1. Runs and gates

- **Runs:** 2a UKF (live + RTS) and 2b FGO (live + whole-flight batch), 6 runs each. All 12 exited 0. 2b had 0 keyframe
  failures, and every FGO whole-flight batch converged in 4 iterations. No replay was re-run (D95).
- **Map provenance:** in every new run, `stats.json:e6.tag_map_sha256` equals the sha256 of the map file used, and
  every non-gauge tag has a nonzero shift. For each flight, the FGO-map and UKF-map tracks differ.
- **Scorer gate S-E6:** re-run inside every scoring call, PASS 3/3 (max |diff| ≤ 4.09e-16 m, tolerance 1e-9 m).
- **Guard:** IDENTICAL before 2a, after 2a, after 2b and after scoring (§7).

## 2. Results table (horizontal RMSE over the lap window, m; world frame, no alignment)

"live" is the estimator's real-time output: the UKF filter, or the FGO 0.25 s fixed-lag smoother. "hindsight" is the
UKF RTS smoother, or the FGO whole-flight batch LM. For arm (iv) it is the stored loop-closure hindsight (Experiment 3
iSAM2 + 5 updates; E5 RTS). Arms (i) and (iv) are re-scored from stored results and were not re-run.

| estimator | arm | T_A_r1 live | T_A_r2 live | T_A_r3 live | T_A_r1 lap-1 live | T_A_r2 lap-1 live | T_A_r3 lap-1 live | T_A_r1 hindsight | T_A_r2 hindsight | T_A_r3 hindsight |
|---|---|---|---|---|---|---|---|---|---|---|
| FGO | (i) surveyed | 0.0214 | 0.0196 | 0.0190 | 0.0207 | 0.0170 | 0.0201 | 0.0106 | 0.0107 | 0.0101 |
| FGO | (ii) FGO map | 0.0457 | 0.0390 | 0.0289 | 0.0510 | 0.0356 | 0.0303 | 0.0441 | 0.0345 | 0.0287 |
| FGO | (iii) UKF map | 0.0446 | 0.0408 | 0.0464 | 0.0497 | 0.0406 | 0.0460 | 0.0428 | 0.0381 | 0.0453 |
| FGO | (iv) no map, LC online | 0.0574 | 0.0494 | 0.0760 | 0.1063 | 0.0818 | 0.1608 | 0.0198 | 0.0270 | 0.0172 |
| UKF | (i) surveyed | 0.0356 | 0.0362 | 0.0382 | 0.0351 | 0.0359 | 0.0400 | 0.0128 | 0.0141 | 0.0142 |
| UKF | (ii) FGO map | 0.0448 | 0.0407 | 0.0376 | 0.0471 | 0.0392 | 0.0389 | 0.0424 | 0.0310 | 0.0262 |
| UKF | (iii) UKF map | 0.0445 | 0.0471 | 0.0491 | 0.0476 | 0.0487 | 0.0497 | 0.0403 | 0.0367 | 0.0432 |
| UKF | (iv) no map, LC online | 0.1193 | 0.0911 | 0.1335 | 0.2240 | 0.1560 | 0.2565 | 0.0445 | 0.0461 | 0.0552 |

Source: `json:scores/e6_T_A_r{1,2,3}.json:tracks."<arm> | <estimator> <live|hindsight>".{rmse_m, per_lap_rmse_m[0]}`.
Max, every per-lap value and lap-5 ÷ lap-1 are in the same jsons.

**Map error (P1 input; 7 non-gauge tags, m).** Source: `json:scores/e6_verdicts.json:flights.<t>.map`, from
`~/thesis_data/tier1/e6/maps/<m>/map_errors.json`.

| test flight | mapping flight | FGO-map position RMS (m) | UKF-map position RMS (m) | UKF ÷ FGO |
|---|---|---|---|---|
| T_A_r1 | E6M_fig8_r1b | 0.0455 | 0.0448 | 0.98 |
| T_A_r2 | E6M_fig8_r2 | 0.0342 | 0.0401 | 1.17 |
| T_A_r3 | E6M_fig8_r3 | 0.0275 | 0.0476 | 1.73 |

## 3. Verdicts (as worded; `json:scores/e6_verdicts.json:criteria`)

| prediction | criterion (as pre-registered) | per flight (r1, r2, r3) | count | verdict |
|---|---|---|---|---|
| P1 | FGO-map position RMS < UKF-map position RMS, 3/3 mapping flights | no, yes, yes | 2/3 | **FAIL** |
| P2 (FGO) | FGO live RMSE on the FGO map within the surveyed band [0.016691, 0.023695] m, 3/3 | no, no, no | 0/3 | **FAIL** |
| P3 (FGO) | FGO live RMSE, FGO map < UKF map, 3/3 | no, yes, yes | 2/3 | **FAIL** |
| P4 (FGO) | FGO lap-1 live RMSE, FGO map < no map (iv), 3/3 | yes, yes, yes | 3/3 | **PASS** |
| P2 (UKF) | UKF live RMSE on the FGO map within the surveyed band [0.033011, 0.040785] m, 3/3 | no, yes, yes | 2/3 | **FAIL** |
| P3 (UKF) | UKF live RMSE, FGO map < UKF map, 3/3 | no, yes, yes | 2/3 | **FAIL** |
| P4 (UKF) | UKF lap-1 live RMSE, FGO map < no map (iv), 3/3 | yes, yes, yes | 3/3 | **PASS** |

**P2 detail.** The band is [min − R, max + R] of the stored arm (i) live repeats (D87), shown to 6 dp because it is
scored unrounded.

| estimator | surveyed band (m) | FGO-map live T_A_r1 / r2 / r3 (m) | inside |
|---|---|---|---|
| FGO | [0.016691, 0.023695] | 0.045712 / 0.038953 / 0.028876 | above, above, above |
| UKF | [0.033011, 0.040785] | 0.044822 / 0.040679 / 0.037572 | above, yes, yes |

**Headlines (pre-registered §5 form):**
- **P1: FAIL** (2/3). The FGO map is lower on `E6M_fig8_r2` and `E6M_fig8_r3` and higher on `E6M_fig8_r1b`
  (0.0455 m against 0.0448 m).
- **P2: FAIL (both).** FGO 0/3: all three values are above the band. UKF 2/3: `T_A_r1` is above the band (0.0448 m against an upper edge of 0.0408 m).
- **P3: FAIL (both)**, 2/3 for each estimator. On `T_A_r1` the FGO map gives the higher live error for both estimators.
- **P4: PASS (both)**, 3/3 for each estimator.

**Descriptive ratios (no verdict; §6 of the pre-registration):**

| estimator | flight | FGO map ÷ surveyed (live) | UKF map ÷ surveyed (live) | FGO map ÷ UKF map (live) | FGO map ÷ no map (live, overall; P4-overall) | FGO map ÷ surveyed (hindsight) | UKF map ÷ surveyed (hindsight) |
|---|---|---|---|---|---|---|---|
| FGO | T_A_r1 | 2.14 | 2.09 | 1.02 | 0.80 | 4.14 | 4.02 |
| FGO | T_A_r2 | 1.98 | 2.08 | 0.95 | 0.79 | 3.23 | 3.56 |
| FGO | T_A_r3 | 1.52 | 2.44 | 0.62 | 0.38 | 2.84 | 4.49 |
| UKF | T_A_r1 | 1.26 | 1.25 | 1.01 | 0.38 | 3.31 | 3.15 |
| UKF | T_A_r2 | 1.12 | 1.30 | 0.86 | 0.45 | 2.20 | 2.61 |
| UKF | T_A_r3 | 0.98 | 1.29 | 0.77 | 0.28 | 1.84 | 3.04 |

- **P4-overall** (descriptive): the FGO map's overall live error is lower than arm (iv)'s on 3/3 flights for each
  estimator (ratio 0.38–0.80 for the FGO and 0.28–0.45 for the UKF).

## 4. Plain-language reading

- **A map from one earlier flight is much better than no map at the start of a flight.** On lap 1, before the
  loop-closure estimators have re-observed any tag, the FGO map gives lap-1 live errors of 0.0303–0.0510 m for the FGO,
  against 0.0818–0.1608 m with no map. For the UKF it gives 0.0389–0.0471 m, against 0.1560–0.2565 m. This is P4, PASS for both
  estimators.
- **It does not replace the survey at survey accuracy.** The estimated maps are off by 0.0275–0.0455 m (FGO map) and
  0.0401–0.0476 m (UKF map) RMS per tag. With the map used as exact, that error becomes a fixed bias near each tag.
  - FGO estimator: on the FGO map, the live error is 1.52–2.14 times the surveyed-map value and outside the
    surveyed-map band on every flight (P2 FAIL, 0/3).
  - UKF estimator: its surveyed-map live error is larger to begin with (0.0356–0.0382 m), and on the FGO map it is
    0.98–1.26 times that. It still left the band on one flight (P2 FAIL, 2/3). The cause of the smaller relative
    cost was not diagnosed.
  - The hindsight tracks do not recover surveyed-map accuracy either. The FGO whole-flight batch on the FGO map reaches
    0.0287–0.0441 m, against 0.0101–0.0107 m on the surveyed map.
- **The FGO's map was better on two of the three mapping flights, not on all three** (P1 FAIL, 2/3). Descriptively,
  on every flight the live error ranked the two maps the same way as their map error did: the per-flight outcomes of
  P1, P3 (FGO) and P3 (UKF) are identical (no, yes, yes).
  Where the FGO map was the better map (r2, r3), both estimators flew better on it. On r1b the two maps were within
  0.0007 m of each other and the FGO map was slightly worse, and so were the live errors (P3 FAIL for both).
- **Hindsight is different (descriptive, no verdict).** The FGO that estimates its own map online (arm (iv), iSAM2
  hindsight, 0.0172–0.0270 m) beat the FGO whole-flight batch on either fixed estimated map (0.0287–0.0453 m) on
  3/3 flights. The UKF did not show this: arm (iv) RTS gives 0.0445–0.0552 m, against 0.0262–0.0424 m on the FGO
  map. The P4 confound (different estimators in arm (iv)) applies here too.
- **In short, for the live tracks:** "map once, fly again" works as a replacement for surveying in the sense of
  beating no map (P4), but not as a like-for-like replacement for a surveyed map (P2). The pre-registered expectation that the FGO's map is
  consistently the better one (P1, P3) did not hold on all three flights.

## 5. Limitations

- **Simulation only.** Rendered tags and simulator-truth flight paths, with no lighting change or tag wear between the
  mapping and test flights. The map's only error source is the estimator.
- **n = 3.** There are three mapping flights and three test flights, in fixed pairs. Bands built from three repeats are
  coarse, and P1, P3 and P4 are direction-only.
- **Perfect tag IDs.** No tag was misidentified in the mapping or test flights (E3 studied wrong IDs separately).
- **The same-route caveat does NOT apply.** The mapping flights are out-of-sample figures of eight on a different route
  from the test flights' square laps (pre-registration §1.3, §3.1). They re-observe tags 4 and 6 twice per circuit and
  the others once, over 3 circuits.
- **One surveyed tag registers the frame** (tag 0, pre-registration §1.2), so "replacing the survey" here means
  replacing the survey of the other 7 tags.
- **P4 confound.** Arm (iv) uses different estimators (the iSAM2 keyframe FGO and the landmark UKF) and every central
  detection. The map arms use the thesis estimators on one fix per frame.
- **The FGO map is the Experiment 3 iSAM2 hindsight** (5 extra updates), not an LM batch.
- **No map uncertainty is propagated:** the map is used as exact, as the user designed it.
- **Same world, same day, same tags.** Map reuse over time (moved or replaced tags) is not tested.

## 6. Run timings (DIAGNOSTIC, workstation, serial; `e6/stage2_timing.tsv`)

| run | start (AEDT) | wall (s) | exit |
|---|---|---|---|
| 2a_ukf_T_A_r1_fgomap | 2026-10-31 23:16 | 52.7 | 0 |
| 2a_ukf_T_A_r1_ukfmap | 2026-10-31 23:17 | 52.3 | 0 |
| 2a_ukf_T_A_r2_fgomap | 2026-10-31 23:18 | 51.9 | 0 |
| 2a_ukf_T_A_r2_ukfmap | 2026-10-31 23:21 | 52.5 | 0 |
| 2a_ukf_T_A_r3_fgomap | 2026-10-31 23:22 | 53.6 | 0 |
| 2a_ukf_T_A_r3_ukfmap | 2026-10-31 23:24 | 53.3 | 0 |
| 2b_fgo_T_A_r1_fgomap | 2026-10-31 23:25 | 995.2 | 0 |
| 2b_fgo_T_A_r1_ukfmap | 2026-10-31 23:44 | 1026.7 | 0 |
| 2b_fgo_T_A_r2_fgomap | 2026-11-01 00:01 | 998.8 | 0 |
| 2b_fgo_T_A_r2_ukfmap | 2026-11-01 00:18 | 1005.0 | 0 |
| 2b_fgo_T_A_r3_fgomap | 2026-11-01 00:34 | 981.4 | 0 |
| 2b_fgo_T_A_r3_ukfmap | 2026-11-01 00:51 | 965.2 | 0 |

- FGO whole-flight batch alone: 810.3–869.2 s per run (`stats.json:batch_s`). That is well below the pre-registered upper
  bound of 2,961 s, which was a 6-parallel figure.

## 7. Guard (`frozen_manifest_20261022T002851.json`, 13,253 files)

| check | result | report |
|---|---|---|
| before Stage 2 (2026-10-31 23:15 AEDT) | **IDENTICAL**, 13,253 files | `frozen_manifest_20261022T002851_verify_e6_stage2_pre_20261031T231449.json` |
| after 2a (UKF replays) (2026-10-31 23:25 AEDT) | **IDENTICAL**, 13,253 files | `frozen_manifest_20261022T002851_verify_e6_stage2a_post_20261031T232514.json` |
| after 2b (FGO replays) (2026-11-01 01:08 AEDT) | **IDENTICAL**, 13,253 files | `frozen_manifest_20261022T002851_verify_e6_stage2b_post_20261101T010819.json` |
| after scoring and verdicts (2026-11-01 01:10 AEDT) | **IDENTICAL**, 13,253 files | `frozen_manifest_20261022T002851_verify_e6_stage2c_scoring_post_20261101T010959.json` |
| after the results write-up (2026-11-01 01:13 AEDT) | **IDENTICAL**, 13,253 files | `frozen_manifest_20261022T002851_verify_e6_stage2d_docs_post_20261101T011235.json` |
| after the final cross-check revision (2026-11-01 01:15 AEDT) | **IDENTICAL**, 13,253 files | `frozen_manifest_20261022T002851_verify_e6_stage2e_final_post_20261101T011531.json` |
