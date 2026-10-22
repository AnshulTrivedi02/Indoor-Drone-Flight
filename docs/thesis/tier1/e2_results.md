# E2 results: loop closure with fewer tags (conditions B, C, D)

**Extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22).** Pre-registration:
`preregistration.md` §1 (E2), with the general rules in §0 and §5–§9. Stage 2d ran on 2026-10-22, from the main checkout of `fwd-camera`.
Every run recorded commit `c8c42ec`, which is `dca1ddd` plus the §Deviations row only, with `src_dirty` empty.

- **Runs.** There were 18 replays, all completed with rc 0, one at a time under `heavy.py`. LC ran first (9), then no-LC (9).
  - Each flight used **only its condition's tags**: `--tag-ids` B = `0,1,2,3`, C = `0,2`, D = `0`. These are copied from each
    trial's `metadata.yaml`.
  - The configuration was otherwise the frozen Experiment 3 one (§0.2).
  - Outputs are in `~/thesis_data/tier1/T_<c>_r<i>/lc_fgo_{lc,nolc}_t245_tags<ids>/`.
- **Scoring.** `~/venv-tags/bin/python eval/l_score.py <trial> --in-root ~/thesis_data/tier1 --suffix _t245_tags<ids> --json
  docs/thesis/tier1/scores/E2_<trial>.json`, exactly as §1 states. Its output is in `stage2d/l_score.log`.
- **Verdicts.** `stage2d/e2_verdicts.py` writes `scores/E2_verdicts.json`.
  - Every input is stored there with its source key.
  - Comparisons use unrounded values.
- **Mechanism deviation.** This is the serial driver instead of `run_jobs_resumable.sh`, at nice 19, plus the `E2_` score file name.
  It was recorded in `numbers_tier1.md` §Deviations and committed (`c8c42ec`) before the first E2 run.
- **Precision.** Positions are in m to 4 dp and ratios to 2 dp. Every number below is generated from the jsons by
  `stage2d/make_results.py`, and the exact cross-check is `stage2d/crosscheck.py` → `stage2d/crosscheck.out`.

## 1. Per flight and condition (horizontal RMSE in tag 0's frame over the lap window, m)

Source: `scores/E2_<trial>.json`, keys `tracks.<mode> <track>.rmse_m`, `.max_m` and `.per_lap_rmse_m[0]`/`[4]`. The ratios come from
`scores/E2_verdicts.json:flights.<trial>`.

| flight | LC live | LC hindsight | no-LC live | no-LC hindsight | LC live max | no-LC live max | LC live lap 1 → lap 5 | LC live lap5/lap1 | no-LC live lap 1 → lap 5 | no-LC live lap5/lap1 |
|---|---|---|---|---|---|---|---|---|---|---|
| T_B_r1 | 0.0409 | 0.0267 | 0.1001 | 0.2573 | 0.1593 | 0.2081 | 0.0645 → 0.0289 | 0.45 | 0.0645 → 0.1143 | 1.77 |
| T_B_r2 | 0.0709 | 0.0156 | 0.4336 | 0.2760 | 0.2569 | 0.9485 | 0.1389 → 0.0213 | 0.15 | 0.1389 → 0.5935 | 4.27 |
| T_B_r3 | 0.0476 | 0.0185 | 0.3652 | 0.3146 | 0.1763 | 0.9316 | 0.0932 → 0.0212 | 0.23 | 0.0932 → 0.5500 | 5.90 |
| T_C_r1 | 0.0673 | 0.0272 | 0.2818 | 0.2881 | 0.2406 | 0.6604 | 0.1249 → 0.0396 | 0.32 | 0.1249 → 0.4338 | 3.47 |
| T_C_r2 | 0.0637 | 0.0231 | 0.2821 | 0.2221 | 0.2360 | 0.6867 | 0.1158 → 0.0528 | 0.46 | 0.1158 → 0.4137 | 3.57 |
| T_C_r3 | 0.0872 | 0.0237 | 0.3162 | 0.2627 | 0.3038 | 0.6487 | 0.1698 → 0.0553 | 0.33 | 0.1698 → 0.3541 | 2.08 |
| T_D_r1 | 0.0964 | 0.0282 | 0.4850 | 0.2462 | 0.2844 | 1.1536 | 0.1529 → 0.0674 | 0.44 | 0.1529 → 0.7038 | 4.60 |
| T_D_r2 | 0.0795 | 0.0271 | 0.3912 | 0.1980 | 0.1963 | 0.9584 | 0.1030 → 0.0691 | 0.67 | 0.1030 → 0.5255 | 5.10 |
| T_D_r3 | 0.0739 | 0.0293 | 0.2417 | 0.4148 | 0.1732 | 0.5703 | 0.0513 → 0.0695 | 1.35 | 0.0513 → 0.3293 | 6.42 |

LC ÷ no-LC (from `scores/E2_verdicts.json:flights.<trial>.lc live / nolc live` and `.lc hindsight / nolc hindsight`):

| flight | LC live / no-LC live | LC hindsight / no-LC hindsight |
|---|---|---|
| T_B_r1 | 0.41 | 0.10 |
| T_B_r2 | 0.16 | 0.06 |
| T_B_r3 | 0.13 | 0.06 |
| T_C_r1 | 0.24 | 0.09 |
| T_C_r2 | 0.23 | 0.10 |
| T_C_r3 | 0.28 | 0.09 |
| T_D_r1 | 0.20 | 0.11 |
| T_D_r2 | 0.20 | 0.14 |
| T_D_r3 | 0.31 | 0.07 |

## 2. Mechanical verdicts (judged on unrounded values; 3/3 completed runs per condition, no gate failures)

| criterion | B | C | D | source |
|---|---|---|---|---|
| **H-E2.1 (PRIMARY)**: LC live lap-5 ≤ 1.5 × lap-1 | **PASS** 3/3 | **PASS** 3/3 | **PASS** 3/3 | `E2_verdicts.json:criteria.H-E2.1` |
| H-E2.2: LC live < no-LC live (overall) | **PASS** 3/3 | **PASS** 3/3 | **PASS** 3/3 | `criteria.H-E2.2` |
| H-E2.3: LC hindsight < no-LC hindsight (overall) | **PASS** 3/3 | **PASS** 3/3 | **PASS** 3/3 | `criteria.H-E2.3` |
| P-E2.4: no-LC live lap-5 > 1.5 × lap-1 | **PASS** 3/3 | **PASS** 3/3 | **PASS** 3/3 | `criteria.P-E2.4` |

- **H-E2.1 headline:** "PASS in B, C and D (9/9)". That is the full E2 headline as §1 words it.
  - The LC live lap-5/lap-1 ratios run from 0.15 to 1.35.
  - The largest is T_D_r3 at 1.35, the boundary case §1 anticipated for D: its lap 1 (0.0513 m) is unusually small.
- **P-E2.4:** the smallest no-LC ratio is T_B_r1 at 1.77 (> 1.5).
- **P-E2.5 (graded, one check): FAIL.** The mean LC live lap-5 RMSE should not decrease along A → B → C → D. It does
  decrease from A to B:
  - A = 0.0317 (stored Experiment 3, `eval/results/expL/T_A_r<i>_t245.json:tracks.lc live.per_lap_rmse_m[4]`);
  - B = 0.0238;
  - C = 0.0492;
  - D = 0.0687 m (`E2_verdicts.json:P-E2.5.means`).

  The steps are A ≤ B False, B ≤ C True, C ≤ D True. So the registered ordering does not hold at its first step, while B < C < D does.
  This is a null result for the prediction and is reported with the same prominence as a PASS (§0.5). P-E2.5 is a prediction and does
  not carry the E2 headline. With n = 3 per condition, no claim is made about why lap 5 in B is below A. The three B lap-5 values
  are 0.0289 / 0.0213 / 0.0212 m, against A's 0.034 / 0.035 / 0.026 m (§0.4).

**Null-result wording (§1):** none of H-E2.1, H-E2.2 or H-E2.3 failed in any condition. Loop closure bounded the live drift lap on lap,
and re-identification gave an accuracy gain, on every tag set tested.

## 3. Condition D is degenerate (stated, §1)

- **D with LC:** the only tag is the gauge tag, which is the origin by definition. So LC on D is the **known-map, one-tag** case: one
  landmark (`landmarks` = 1 on 3/3), with a loop closure to the origin on each pass.
- **D without LC:** each of tag 0's 6 passes becomes a new free landmark (`landmarks` = 6 on 3/3). It is dead reckoning plus
  within-pass constraints.
- D's verdicts are reported above but carry **no claim about unknown landmarks**. As expected, D's LC results are close to the
  Experiment 2 known-map one-tag FGO (§4).

## 4. Comparison with the existing known-map results (DESCRIPTIVE ONLY; no hypothesis, no verdict)

Experiment 2's values come from `eval/results/expT/T_<c>_r<i>.json`:
- `tracks.FGO live.horiz_err_m.rmse`;
- `tracks.FGO hindsight (whole-flight batch).horiz_err_m.rmse`.

Their condition means are the N:526-529 rows of `docs/thesis/numbers.md` (§16.1): FGO live / batch is B 0.026 / 0.015, C 0.054 / 0.019,
D 0.083 / 0.028 m. The ratios are in `E2_verdicts.json:known_map_descriptive.<trial>`.

| flight | E2 LC live | Exp. 2 FGO live | ratio | E2 LC hindsight | Exp. 2 FGO batch | ratio |
|---|---|---|---|---|---|---|
| T_B_r1 | 0.0409 | 0.0233 | 1.75 | 0.0267 | 0.0144 | 1.86 |
| T_B_r2 | 0.0709 | 0.0292 | 2.43 | 0.0156 | 0.0142 | 1.10 |
| T_B_r3 | 0.0476 | 0.0252 | 1.89 | 0.0185 | 0.0153 | 1.21 |
| T_C_r1 | 0.0673 | 0.0538 | 1.25 | 0.0272 | 0.0194 | 1.40 |
| T_C_r2 | 0.0637 | 0.0502 | 1.27 | 0.0231 | 0.0191 | 1.21 |
| T_C_r3 | 0.0872 | 0.0565 | 1.54 | 0.0237 | 0.0188 | 1.26 |
| T_D_r1 | 0.0964 | 0.0931 | 1.04 | 0.0282 | 0.0272 | 1.03 |
| T_D_r2 | 0.0795 | 0.0813 | 0.98 | 0.0271 | 0.0261 | 1.04 |
| T_D_r3 | 0.0739 | 0.0745 | 0.99 | 0.0293 | 0.0309 | 0.95 |

**The inputs differ, so this stays descriptive** (§1):
- E2 uses every central detection of the condition's tags in `/tags/raw`. On T_B_r1 that is 2370 central − 1057 filtered = 1313,
  as §1 states.
- Experiment 2 uses `/tags/sent`, at most one fix per camera frame.
- The solvers differ too: retained-history iSAM2 with a 5-update hindsight, against a fixed-lag 0.25 s smoother with a whole-flight
  LM batch.
- The frames differ only by a translation, and the windows are identical.

Pattern (descriptive):
- In B and C, E2 LC live is 1.25–2.43× the known-map FGO live, and LC hindsight is 1.10–1.86× the batch.
- In D (the known-map case) both ratios are 0.95–1.04.
- For reference, condition A's stored ratios (§1) are 2.69 / 2.52 / 3.99 (live) and 1.86 / 2.53 / 1.70 (hindsight).

## 5. Invariants and run checks (reported)

Source: `E2_verdicts.json:flights.<trial>.stats` and `.invariants`, from each run's `stats.json`.

| flight | t_anchor (s) | landmarks LC / no-LC | landmark factors | central / filtered out | keyframe failures LC, no-LC | wall LC / no-LC (s, stats.json) |
|---|---|---|---|---|---|---|
| T_B_r1 | 30.559 | 4 / 21 | 1042 | 2370 / 1057 | 0, 0 | 121.7 / 3012.7 |
| T_B_r2 | 28.546 | 4 / 21 | 995 | 2340 / 1062 | 0, 0 | 174.9 / 4095.1 |
| T_B_r3 | 28.777 | 4 / 21 | 1073 | 2341 / 1000 | 0, 0 | 144.0 / 4952.8 |
| T_C_r1 | 28.777 | 2 / 11 | 545 | 2314 / 1503 | 0, 0 | 138.0 / 3327.1 |
| T_C_r2 | 28.711 | 2 / 11 | 577 | 2328 / 1499 | 0, 0 | 142.7 / 4091.6 |
| T_C_r3 | 30.526 | 2 / 11 | 617 | 2374 / 1485 | 0, 0 | 144.0 / 4308.1 |
| T_D_r1 | 29.206 | 1 / 6 | 313 | 2308 / 1731 | 0, 0 | 150.8 / 5080.0 |
| T_D_r2 | 29.536 | 1 / 6 | 356 | 2351 / 1708 | 0, 0 | 149.8 / 4293.5 |
| T_D_r3 | 29.14 | 1 / 6 | 329 | 2288 / 1691 | 0, 0 | 155.6 / 4484.8 |

- **`t_anchor`:** equal between LC and no-LC on 9/9 flights. Tag 0, the gauge, is kept in every condition, so the anchor is the first
  central tag-0 sighting.
- **Landmarks:** LC = number of condition tags (4 / 2 / 1) on 9/9. No-LC = 21 / 11 / 6 on 9/9, equal to the pass counts expected in
  §8 (tag 0: 6 passes, each other tag: 5).
- **Recorded data:**
  - recorded `tier1.tag_ids` equals the condition's on 18/18;
  - `raw_detections` and `central` are equal between modes on 9/9;
  - `n_filtered_out_by_tag_ids` > 0 on every run (1000–1731).
- **Lap 1:** LC live = no-LC live exactly on 9/9 (bit-equal floats). This is the §0.4 property that lap 1 is dead reckoning in
  both modes.
- **Keyframe failures:** 0 on 18/18.
- **`src_dirty`:** empty on 18/18. The commit is `c8c42ec` on 18/18.

## 6. Wall time (DIAGNOSTIC; serial, single-threaded, nice 19, workstation)

Driver wall per run (`stage2d/timing.tsv`, including `heavy.py` start-up):
- LC: 124.1–177.2 s (9 runs, 1,341.8 s);
- no-LC: 3,014.9–5,082.3 s (9 runs, 37,666.4 s);
- total: 39,008.2 s (10.84 h).

All were within the §8 upper bounds (LC ≤ 521 s, no-LC ≤ 9,584 s), and no 6 h job timeout was hit. Contrary to §8's guess, no-LC on
D (6 landmarks) was not faster than on B (21 landmarks).

## 7. Guard

After the last E2 run, `python3 tools/tier1_checksum_guard.py verify docs/thesis/tier1/frozen_manifest_20261022T002851.json`
returned **IDENTICAL, exit 0** (13,253 files). Report: `frozen_manifest_20261022T002851_verify_stage2d_20261022T133243.json`.
