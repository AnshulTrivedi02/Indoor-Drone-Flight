# numbers_tier1: extension experiments E2–E5 (pre-registered)

**Partly filled (Stage 2c and 2d, 2026-10-22; Stage 2e, 2026-10-23): §Guard, §Gates, §E5, §E2 and §E3.** E4 has no results yet. Every result in this file is labelled **"extension experiment, pre-registered
(2026-10-21; signed off with amendments 2026-10-22)"**. The pre-registration is `docs/thesis/tier1/preregistration.md` and the E5 design is
`docs/thesis/tier1/e5_design.md`.

## Provenance rules (the same convention as `docs/thesis/numbers.md`)

- **Separate from numbers.md.** This file is never merged into `docs/thesis/numbers.md`, and no value here is copied
  into `numbers.md`, `METHODOLOGY.md`, the frozen pack or `eval/figs_thesis*.py`.
- **Columns.** Every row has quantity | value | unit | status | source.
  - **Status** is one of CURRENT, DIAGNOSTIC (timing on the workstation), DESCRIPTIVE (no verdict) or NOT RUN
    (not finished by the 2026-11-04 23:59 AEDT lock; counted separately, never NOT MET or FAIL). Scoring and
    reporting of completed runs may continue to 2026-11-06 23:59 AEDT.
  - **Source** is a `json:` path *and key* under `docs/thesis/tier1/scores/`, or a `tier1:` run directory under
    `~/thesis_data/tier1/` plus a file and key.
- **Exact cross-check.** Every value is re-computed from its cited source by a check script before it is typed here.
  The script and its output are recorded in the handover that adds the value. A value that does not match its source
  to the printed precision is not entered.
- **Precision.** Positions are printed to 4 dp in m; ratios to 2 dp. Comparisons use the unrounded json values.
- **Verdicts.** PASS, FAIL, NOT MET or NOT RUN, exactly as `preregistration.md` §0.5 defines them, judged on the
  pre-registered counts. No re-tuning and no early decisions.
- **Deviations.** Any departure from the pre-registration is recorded in §Deviations *before* the affected result is
  read.

## Guard

| check | when | result | source |
|---|---|---|---|
| snapshot | before the first run | 13,253 files, 10,115.4 MB (2026-10-22T00:28:51) | `frozen_manifest_20261022T002851.json` |
| verify after the Stage 2a gates | after G-E4 | IDENTICAL, exit 0 (changed 0, missing 0, added 0) | `frozen_manifest_20261022T002851_verify_stage2a.json` |
| verify after E5 (Stage 2c) | after the last E5 result run | IDENTICAL, exit 0 (13,253 files) | `frozen_manifest_20261022T002851_verify_stage2c_20261022T023631.json` |
| verify after E2 (Stage 2d) | after the last E2 run | IDENTICAL, exit 0 (13,253 files) | `frozen_manifest_20261022T002851_verify_stage2d_20261022T133243.json` |
| verify after E3 (Stage 2e) | after the last E3 run and its scoring | IDENTICAL, exit 0 (13,253 files) | `frozen_manifest_20261022T002851_verify_stage2e_20261023T065711.json` |
| verify after E4 / final | after each experiment | — | — |
| E5 code snapshot | immediately before the first V-E5a run (2026-10-22T01:18:05) | 4 files: `ukf_lm.py`, `lc_ukf_replay.py`, `test_ukf_lm.py`, `e5_val_compare.py` (repo commit `e42b9ce`) | `e5_code_manifest_20261022T011805.json` |
| E5 code verify | after the last E5 result run | IDENTICAL, exit 0 (4 files) | `e5_code_manifest_20261022T011805_verify_20261022T023631.json` |

## Gates

| gate | result | source |
|---|---|---|
| G0-L (i) default redirected, (ii) neutral new flags: byte-identical to the frozen `T_A_r1/lc_fgo_lc_t245` | **PASS**: 4/4 files IDENTICAL (`live.tum`, `hindsight.tum` × runs (i), (ii)) | `tier1:stage2a/compare.json` key `G0-L[*].status` (evidence page `stage2_gates.md` §3) |
| G0-UKF: 12/12 byte-identical to the stored `room_ukf` | **PASS**: 12/12 flights, 24/24 files IDENTICAL (also `ground_truth.tum`, `rts_cov.npz`, `stats.json`: 36/36, not gated) | `tier1:stage2a/compare.json` keys `G0-UKF[*].status`, `G0-UKF_extra[*].status` |
| G-E4: 0.25 s `fgo_live.tum` byte-identical to the stored `room_fgo`, 12/12 | **PASS**: 12/12 IDENTICAL | `tier1:stage2a/compare.json` key `G-E4[*].status` |
| V-E5a (world, `ukf_core`) against the stored `room_ukf/{ukf_live,ukf_rts}.tum` (`e5_design.md` §8.4) | **PASS 12/12**. Rows 1:1, `t_anchor` and `n_tag_fused` equal 12/12; byte-identical 12/12 live and 12/12 RTS (reported, not the gate); RMS and max difference 0.000 µm | `json:scores/ve5a_<trial>.json` keys `PASS`, `live/rts.{rows_match,byte_identical,rms_window_m,max_window_m}`, `anchor_tagcount.pass` |
| V-E5b (known map, fixed landmarks) | **PASS 12/12**. Rows 1:1 and anchor/tag count 12/12; worst RMS in window 0.193 µm (≤ 1000 µm), worst max 1.414 µm (≤ 2000 µm); 0 gate-decision flips against V-E5a; byte-identical 0/12 | `json:scores/ve5b_<trial>.json`; worst values `ve5b_T_D_r2.json:live.rms_window_m`, `ve5b_T_D_r2.json:live.max_window_m`; flips `gates.n_flips` |
| V-E5c (known map, landmarks augmented at variance 1e-10) | **PASS 12/12**. Rows 1:1 and anchor/tag count 12/12; worst RMS in window 1.993 µm, worst max 4.243 µm; 0 gate-decision flips; worst \|ΔRMSE\| vs GT 1.278 µm (reported) | `json:scores/ve5c_<trial>.json`; worst values `ve5c_T_B_r2.json:live.rms_window_m`, `ve5c_T_B_r3.json:live.max_window_m`, `ve5c_T_B_r3.json:live.rmse_vs_gt_m.abs_delta` |
| E5 result-run invariants: `t_anchor` and landmark counts (8 / 41) equal the stored FGO (`e5_design.md` §5.3) | **MET 6/6**: `t_anchor` 28.546 / 28.975 / 28.744 s; landmarks 8 (LC) and 41 (no-LC) on each flight; tag measurements used = `landmark_factors` exactly (2145 / 2057 / 2038; reported) | `tier1:T_A_r<i>/lc_ukf_<mode>_t245/stats.json` key `invariants` |

## E2: loop closure with fewer tags (B, C, D)

**Extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22).** 18/18 runs completed (rc 0, 0 keyframe failures, Stage 2d). Each flight used only its condition's tags (`--tag-ids`). Verdicts were judged on the unrounded json values. Full page: `e2_results.md`. Condition D is degenerate (preregistration §1): its only tag is the gauge tag, so LC on D is the known-map one-tag case and carries no claim about unknown landmarks.

| quantity | value | unit | status | source |
|---|---|---|---|---|
| T_B_r1 LC live overall RMSE | 0.0409 | m | CURRENT | `json:scores/E2_T_B_r1.json:tracks.lc live.rmse_m` |
| T_B_r1 LC live lap 1 / lap 5 RMSE | 0.0645 / 0.0289 | m | CURRENT | `json:scores/E2_T_B_r1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_B_r1 LC hindsight overall RMSE | 0.0267 | m | CURRENT | `json:scores/E2_T_B_r1.json:tracks.lc hindsight.rmse_m` |
| T_B_r1 LC hindsight lap 1 / lap 5 RMSE | 0.0271 / 0.0254 | m | CURRENT | `json:scores/E2_T_B_r1.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_B_r1 no-LC live overall RMSE | 0.1001 | m | CURRENT | `json:scores/E2_T_B_r1.json:tracks.nolc live.rmse_m` |
| T_B_r1 no-LC live lap 1 / lap 5 RMSE | 0.0645 / 0.1143 | m | CURRENT | `json:scores/E2_T_B_r1.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_B_r1 no-LC hindsight overall RMSE | 0.2573 | m | CURRENT | `json:scores/E2_T_B_r1.json:tracks.nolc hindsight.rmse_m` |
| T_B_r1 no-LC hindsight lap 1 / lap 5 RMSE | 0.1570 / 0.1273 | m | CURRENT | `json:scores/E2_T_B_r1.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_B_r1 LC live lap-5 / lap-1 | 0.45 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_B_r1.ratio lc live lap5/lap1` |
| T_B_r1 no-LC live lap-5 / lap-1 | 1.77 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_B_r1.ratio nolc live lap5/lap1` |
| T_B_r1 E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | 1.75 / 1.86 | ratio | DESCRIPTIVE | `json:scores/E2_verdicts.json:known_map_descriptive.T_B_r1` |
| T_B_r2 LC live overall RMSE | 0.0709 | m | CURRENT | `json:scores/E2_T_B_r2.json:tracks.lc live.rmse_m` |
| T_B_r2 LC live lap 1 / lap 5 RMSE | 0.1389 / 0.0213 | m | CURRENT | `json:scores/E2_T_B_r2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_B_r2 LC hindsight overall RMSE | 0.0156 | m | CURRENT | `json:scores/E2_T_B_r2.json:tracks.lc hindsight.rmse_m` |
| T_B_r2 LC hindsight lap 1 / lap 5 RMSE | 0.0185 / 0.0125 | m | CURRENT | `json:scores/E2_T_B_r2.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_B_r2 no-LC live overall RMSE | 0.4336 | m | CURRENT | `json:scores/E2_T_B_r2.json:tracks.nolc live.rmse_m` |
| T_B_r2 no-LC live lap 1 / lap 5 RMSE | 0.1389 / 0.5935 | m | CURRENT | `json:scores/E2_T_B_r2.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_B_r2 no-LC hindsight overall RMSE | 0.2760 | m | CURRENT | `json:scores/E2_T_B_r2.json:tracks.nolc hindsight.rmse_m` |
| T_B_r2 no-LC hindsight lap 1 / lap 5 RMSE | 0.1452 / 0.3279 | m | CURRENT | `json:scores/E2_T_B_r2.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_B_r2 LC live lap-5 / lap-1 | 0.15 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_B_r2.ratio lc live lap5/lap1` |
| T_B_r2 no-LC live lap-5 / lap-1 | 4.27 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_B_r2.ratio nolc live lap5/lap1` |
| T_B_r2 E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | 2.43 / 1.10 | ratio | DESCRIPTIVE | `json:scores/E2_verdicts.json:known_map_descriptive.T_B_r2` |
| T_B_r3 LC live overall RMSE | 0.0476 | m | CURRENT | `json:scores/E2_T_B_r3.json:tracks.lc live.rmse_m` |
| T_B_r3 LC live lap 1 / lap 5 RMSE | 0.0932 / 0.0212 | m | CURRENT | `json:scores/E2_T_B_r3.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_B_r3 LC hindsight overall RMSE | 0.0185 | m | CURRENT | `json:scores/E2_T_B_r3.json:tracks.lc hindsight.rmse_m` |
| T_B_r3 LC hindsight lap 1 / lap 5 RMSE | 0.0197 / 0.0191 | m | CURRENT | `json:scores/E2_T_B_r3.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_B_r3 no-LC live overall RMSE | 0.3652 | m | CURRENT | `json:scores/E2_T_B_r3.json:tracks.nolc live.rmse_m` |
| T_B_r3 no-LC live lap 1 / lap 5 RMSE | 0.0932 / 0.5500 | m | CURRENT | `json:scores/E2_T_B_r3.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_B_r3 no-LC hindsight overall RMSE | 0.3146 | m | CURRENT | `json:scores/E2_T_B_r3.json:tracks.nolc hindsight.rmse_m` |
| T_B_r3 no-LC hindsight lap 1 / lap 5 RMSE | 0.1832 / 0.2882 | m | CURRENT | `json:scores/E2_T_B_r3.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_B_r3 LC live lap-5 / lap-1 | 0.23 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_B_r3.ratio lc live lap5/lap1` |
| T_B_r3 no-LC live lap-5 / lap-1 | 5.90 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_B_r3.ratio nolc live lap5/lap1` |
| T_B_r3 E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | 1.89 / 1.21 | ratio | DESCRIPTIVE | `json:scores/E2_verdicts.json:known_map_descriptive.T_B_r3` |
| T_C_r1 LC live overall RMSE | 0.0673 | m | CURRENT | `json:scores/E2_T_C_r1.json:tracks.lc live.rmse_m` |
| T_C_r1 LC live lap 1 / lap 5 RMSE | 0.1249 / 0.0396 | m | CURRENT | `json:scores/E2_T_C_r1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_C_r1 LC hindsight overall RMSE | 0.0272 | m | CURRENT | `json:scores/E2_T_C_r1.json:tracks.lc hindsight.rmse_m` |
| T_C_r1 LC hindsight lap 1 / lap 5 RMSE | 0.0270 / 0.0232 | m | CURRENT | `json:scores/E2_T_C_r1.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_C_r1 no-LC live overall RMSE | 0.2818 | m | CURRENT | `json:scores/E2_T_C_r1.json:tracks.nolc live.rmse_m` |
| T_C_r1 no-LC live lap 1 / lap 5 RMSE | 0.1249 / 0.4338 | m | CURRENT | `json:scores/E2_T_C_r1.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_C_r1 no-LC hindsight overall RMSE | 0.2881 | m | CURRENT | `json:scores/E2_T_C_r1.json:tracks.nolc hindsight.rmse_m` |
| T_C_r1 no-LC hindsight lap 1 / lap 5 RMSE | 0.1750 / 0.1857 | m | CURRENT | `json:scores/E2_T_C_r1.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_C_r1 LC live lap-5 / lap-1 | 0.32 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_C_r1.ratio lc live lap5/lap1` |
| T_C_r1 no-LC live lap-5 / lap-1 | 3.47 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_C_r1.ratio nolc live lap5/lap1` |
| T_C_r1 E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | 1.25 / 1.40 | ratio | DESCRIPTIVE | `json:scores/E2_verdicts.json:known_map_descriptive.T_C_r1` |
| T_C_r2 LC live overall RMSE | 0.0637 | m | CURRENT | `json:scores/E2_T_C_r2.json:tracks.lc live.rmse_m` |
| T_C_r2 LC live lap 1 / lap 5 RMSE | 0.1158 / 0.0528 | m | CURRENT | `json:scores/E2_T_C_r2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_C_r2 LC hindsight overall RMSE | 0.0231 | m | CURRENT | `json:scores/E2_T_C_r2.json:tracks.lc hindsight.rmse_m` |
| T_C_r2 LC hindsight lap 1 / lap 5 RMSE | 0.0222 / 0.0264 | m | CURRENT | `json:scores/E2_T_C_r2.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_C_r2 no-LC live overall RMSE | 0.2821 | m | CURRENT | `json:scores/E2_T_C_r2.json:tracks.nolc live.rmse_m` |
| T_C_r2 no-LC live lap 1 / lap 5 RMSE | 0.1158 / 0.4137 | m | CURRENT | `json:scores/E2_T_C_r2.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_C_r2 no-LC hindsight overall RMSE | 0.2221 | m | CURRENT | `json:scores/E2_T_C_r2.json:tracks.nolc hindsight.rmse_m` |
| T_C_r2 no-LC hindsight lap 1 / lap 5 RMSE | 0.1440 / 0.1415 | m | CURRENT | `json:scores/E2_T_C_r2.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_C_r2 LC live lap-5 / lap-1 | 0.46 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_C_r2.ratio lc live lap5/lap1` |
| T_C_r2 no-LC live lap-5 / lap-1 | 3.57 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_C_r2.ratio nolc live lap5/lap1` |
| T_C_r2 E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | 1.27 / 1.21 | ratio | DESCRIPTIVE | `json:scores/E2_verdicts.json:known_map_descriptive.T_C_r2` |
| T_C_r3 LC live overall RMSE | 0.0872 | m | CURRENT | `json:scores/E2_T_C_r3.json:tracks.lc live.rmse_m` |
| T_C_r3 LC live lap 1 / lap 5 RMSE | 0.1698 / 0.0553 | m | CURRENT | `json:scores/E2_T_C_r3.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_C_r3 LC hindsight overall RMSE | 0.0237 | m | CURRENT | `json:scores/E2_T_C_r3.json:tracks.lc hindsight.rmse_m` |
| T_C_r3 LC hindsight lap 1 / lap 5 RMSE | 0.0196 / 0.0291 | m | CURRENT | `json:scores/E2_T_C_r3.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_C_r3 no-LC live overall RMSE | 0.3162 | m | CURRENT | `json:scores/E2_T_C_r3.json:tracks.nolc live.rmse_m` |
| T_C_r3 no-LC live lap 1 / lap 5 RMSE | 0.1698 / 0.3541 | m | CURRENT | `json:scores/E2_T_C_r3.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_C_r3 no-LC hindsight overall RMSE | 0.2627 | m | CURRENT | `json:scores/E2_T_C_r3.json:tracks.nolc hindsight.rmse_m` |
| T_C_r3 no-LC hindsight lap 1 / lap 5 RMSE | 0.1645 / 0.1353 | m | CURRENT | `json:scores/E2_T_C_r3.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_C_r3 LC live lap-5 / lap-1 | 0.33 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_C_r3.ratio lc live lap5/lap1` |
| T_C_r3 no-LC live lap-5 / lap-1 | 2.08 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_C_r3.ratio nolc live lap5/lap1` |
| T_C_r3 E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | 1.54 / 1.26 | ratio | DESCRIPTIVE | `json:scores/E2_verdicts.json:known_map_descriptive.T_C_r3` |
| T_D_r1 LC live overall RMSE | 0.0964 | m | CURRENT | `json:scores/E2_T_D_r1.json:tracks.lc live.rmse_m` |
| T_D_r1 LC live lap 1 / lap 5 RMSE | 0.1529 / 0.0674 | m | CURRENT | `json:scores/E2_T_D_r1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_D_r1 LC hindsight overall RMSE | 0.0282 | m | CURRENT | `json:scores/E2_T_D_r1.json:tracks.lc hindsight.rmse_m` |
| T_D_r1 LC hindsight lap 1 / lap 5 RMSE | 0.0258 / 0.0306 | m | CURRENT | `json:scores/E2_T_D_r1.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_D_r1 no-LC live overall RMSE | 0.4850 | m | CURRENT | `json:scores/E2_T_D_r1.json:tracks.nolc live.rmse_m` |
| T_D_r1 no-LC live lap 1 / lap 5 RMSE | 0.1529 / 0.7038 | m | CURRENT | `json:scores/E2_T_D_r1.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_D_r1 no-LC hindsight overall RMSE | 0.2462 | m | CURRENT | `json:scores/E2_T_D_r1.json:tracks.nolc hindsight.rmse_m` |
| T_D_r1 no-LC hindsight lap 1 / lap 5 RMSE | 0.1689 / 0.1704 | m | CURRENT | `json:scores/E2_T_D_r1.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_D_r1 LC live lap-5 / lap-1 | 0.44 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_D_r1.ratio lc live lap5/lap1` |
| T_D_r1 no-LC live lap-5 / lap-1 | 4.60 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_D_r1.ratio nolc live lap5/lap1` |
| T_D_r1 E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | 1.04 / 1.03 | ratio | DESCRIPTIVE | `json:scores/E2_verdicts.json:known_map_descriptive.T_D_r1` |
| T_D_r2 LC live overall RMSE | 0.0795 | m | CURRENT | `json:scores/E2_T_D_r2.json:tracks.lc live.rmse_m` |
| T_D_r2 LC live lap 1 / lap 5 RMSE | 0.1030 / 0.0691 | m | CURRENT | `json:scores/E2_T_D_r2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_D_r2 LC hindsight overall RMSE | 0.0271 | m | CURRENT | `json:scores/E2_T_D_r2.json:tracks.lc hindsight.rmse_m` |
| T_D_r2 LC hindsight lap 1 / lap 5 RMSE | 0.0350 / 0.0334 | m | CURRENT | `json:scores/E2_T_D_r2.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_D_r2 no-LC live overall RMSE | 0.3912 | m | CURRENT | `json:scores/E2_T_D_r2.json:tracks.nolc live.rmse_m` |
| T_D_r2 no-LC live lap 1 / lap 5 RMSE | 0.1030 / 0.5255 | m | CURRENT | `json:scores/E2_T_D_r2.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_D_r2 no-LC hindsight overall RMSE | 0.1980 | m | CURRENT | `json:scores/E2_T_D_r2.json:tracks.nolc hindsight.rmse_m` |
| T_D_r2 no-LC hindsight lap 1 / lap 5 RMSE | 0.1522 / 0.1468 | m | CURRENT | `json:scores/E2_T_D_r2.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_D_r2 LC live lap-5 / lap-1 | 0.67 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_D_r2.ratio lc live lap5/lap1` |
| T_D_r2 no-LC live lap-5 / lap-1 | 5.10 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_D_r2.ratio nolc live lap5/lap1` |
| T_D_r2 E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | 0.98 / 1.04 | ratio | DESCRIPTIVE | `json:scores/E2_verdicts.json:known_map_descriptive.T_D_r2` |
| T_D_r3 LC live overall RMSE | 0.0739 | m | CURRENT | `json:scores/E2_T_D_r3.json:tracks.lc live.rmse_m` |
| T_D_r3 LC live lap 1 / lap 5 RMSE | 0.0513 / 0.0695 | m | CURRENT | `json:scores/E2_T_D_r3.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_D_r3 LC hindsight overall RMSE | 0.0293 | m | CURRENT | `json:scores/E2_T_D_r3.json:tracks.lc hindsight.rmse_m` |
| T_D_r3 LC hindsight lap 1 / lap 5 RMSE | 0.0172 / 0.0241 | m | CURRENT | `json:scores/E2_T_D_r3.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_D_r3 no-LC live overall RMSE | 0.2417 | m | CURRENT | `json:scores/E2_T_D_r3.json:tracks.nolc live.rmse_m` |
| T_D_r3 no-LC live lap 1 / lap 5 RMSE | 0.0513 / 0.3293 | m | CURRENT | `json:scores/E2_T_D_r3.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_D_r3 no-LC hindsight overall RMSE | 0.4148 | m | CURRENT | `json:scores/E2_T_D_r3.json:tracks.nolc hindsight.rmse_m` |
| T_D_r3 no-LC hindsight lap 1 / lap 5 RMSE | 0.2125 / 0.3867 | m | CURRENT | `json:scores/E2_T_D_r3.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_D_r3 LC live lap-5 / lap-1 | 1.35 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_D_r3.ratio lc live lap5/lap1` |
| T_D_r3 no-LC live lap-5 / lap-1 | 6.42 | ratio | CURRENT | `json:scores/E2_verdicts.json:flights.T_D_r3.ratio nolc live lap5/lap1` |
| T_D_r3 E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | 0.99 / 0.95 | ratio | DESCRIPTIVE | `json:scores/E2_verdicts.json:known_map_descriptive.T_D_r3` |
| P-E2.5 mean LC live lap-5 RMSE, A / B / C / D | 0.0317 / 0.0238 / 0.0492 / 0.0687 | m | CURRENT | `json:scores/E2_verdicts.json:P-E2.5.means.<c>.mean_m` (A from `eval/results/expL/T_A_r<i>_t245.json:tracks.lc live.per_lap_rmse_m[4]`) |

Verdicts: H-E2.1 (PRIMARY) per condition, H-E2.2, H-E2.3, P-E2.4, P-E2.5. Known-map comparison (DESCRIPTIVE).

| criterion | B | C | D | source |
|---|---|---|---|---|
| **H-E2.1 (PRIMARY)**: LC live lap-5 ≤ 1.5 × lap-1 | **PASS** 3/3 | **PASS** 3/3 | **PASS** 3/3 | `json:scores/E2_verdicts.json:criteria.H-E2.1` |
| H-E2.2: LC live < no-LC live (overall) | **PASS** 3/3 | **PASS** 3/3 | **PASS** 3/3 | `json:scores/E2_verdicts.json:criteria.H-E2.2` |
| H-E2.3: LC hindsight < no-LC hindsight (overall) | **PASS** 3/3 | **PASS** 3/3 | **PASS** 3/3 | `json:scores/E2_verdicts.json:criteria.H-E2.3` |
| P-E2.4: no-LC live lap-5 > 1.5 × lap-1 | **PASS** 3/3 | **PASS** 3/3 | **PASS** 3/3 | `json:scores/E2_verdicts.json:criteria.P-E2.4` |
| P-E2.5 (graded, one check): mean LC live lap-5 non-decreasing A → B → C → D | **FAIL** (A ≤ B False, B ≤ C True, C ≤ D True) | | | `json:scores/E2_verdicts.json:P-E2.5` |

P-E2.5 FAILs at its first step: the B mean lap-5 (4 tags) is below the stored A mean (8 tags). The ordering B < C < D holds. This is a null result for the registered ordering and is reported with the same prominence as a PASS (preregistration §0.5).

Invariants (reported; `json:scores/E2_verdicts.json:flights.<t>.invariants`): `t_anchor` equal between LC and no-LC on 9/9 flights; landmarks LC = 4 / 2 / 1 and no-LC = 21 / 11 / 6 (B / C / D) on every flight, as §8 expects; recorded `tag_ids` equal the condition's on 18/18; lap-1 LC live = lap-1 no-LC live exactly on 9/9; T_B_r1 central detections used = 2370 − 1057 = 1313, as §1 states.

## E3: wrong re-identification (T_A, 1% / 5%, seeds 0–2)

**Stage 2e, 2026-10-23.** 39/39 registered runs completed (rc 0; no crash, no re-run), plus one extra timing-only run. Commits: runs 1–6 `cb713d3`, the rest `5f485e6`; scored at `6e7a3e7`. Rows are generated by `stage2e/make_tables.py` from `scores/E3_verdicts.json`, rounded once. The exact cross-check `stage2e/crosscheck.py` (→ `stage2e/crosscheck.out`) gave 0 mismatches. **Headline (ruling R2):** arm (a) at 1%: **6 of 9 runs diverged, 2 of 3 on each flight** (seeds 1 and 2); at 5%: 0 of 9; arm (b): 0 of 21. **H-E3.1 (PRIMARY) FAILs (0/9)**, a null result reported with the same prominence as a PASS. Narrative and per-run tables: `docs/thesis/tier1/e3_results.md`.

### Arm (a): FGO as-is (PRIMARY)

| quantity | value | unit | status | source |
|---|---|---|---|---|
| T_A_r1 1% s0 LC live / hindsight overall RMSE | 3.7618 / 3.5648 | m | CURRENT | `json:scores/E3a_T_A_r1_0.01_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 1% s0 LC live lap 1 / lap 5 RMSE | 3.4551 / 3.7449 | m | CURRENT | `json:scores/E3a_T_A_r1_0.01_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 1% s0 LC live lap-5 / lap-1 | 1.08 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.01_s0.ratio lc live lap5/lap1` |
| T_A_r1 1% s0 injected / eligible non-gauge / all central calls (whole bag) | 19 / 1770 / 2423 | count | CURRENT | `tier1:T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s0/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.01_s0.covariates.mislabel`) |
| T_A_r1 1% s0 rate among eligible / effective overall rate | 1.07 / 0.78 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.01_s0.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r1 1% s1 run status | **FAILED-ESTIMATOR (diverged)**: live divergence onset 49.699 s; first exception 52.432 s; failure fraction 0.9025 (6634 / 7351; inflated: no recovery after a throw) | s / ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.01_s1.run_status` (from `tier1:stage2e/status/e3a_T_A_r1_0.01_s1.json`) |
| T_A_r1 1% s1 injected / eligible non-gauge / all central calls (whole bag) | 19 / 1770 / 2423 | count | CURRENT | `tier1:T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s1/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.01_s1.covariates.mislabel`) |
| T_A_r1 1% s1 rate among eligible / effective overall rate | 1.07 / 0.78 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.01_s1.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r1 1% s2 run status | **FAILED-ESTIMATOR (diverged)**: live divergence onset 59.699 s; first exception 63.832 s; failure fraction 0.8559 (6292 / 7351; inflated: no recovery after a throw) | s / ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.01_s2.run_status` (from `tier1:stage2e/status/e3a_T_A_r1_0.01_s2.json`) |
| T_A_r1 1% s2 injected / eligible non-gauge / all central calls (whole bag) | 14 / 1770 / 2423 | count | CURRENT | `tier1:T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s2/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.01_s2.covariates.mislabel`) |
| T_A_r1 1% s2 rate among eligible / effective overall rate | 0.79 / 0.58 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.01_s2.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r1 5% s0 LC live / hindsight overall RMSE | 4.1295 / 3.9498 | m | CURRENT | `json:scores/E3a_T_A_r1_0.05_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 5% s0 LC live lap 1 / lap 5 RMSE | 4.4370 / 4.0068 | m | CURRENT | `json:scores/E3a_T_A_r1_0.05_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 5% s0 LC live lap-5 / lap-1 | 0.90 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.05_s0.ratio lc live lap5/lap1` |
| T_A_r1 5% s0 injected / eligible non-gauge / all central calls (whole bag) | 90 / 1770 / 2423 | count | CURRENT | `tier1:T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s0/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.05_s0.covariates.mislabel`) |
| T_A_r1 5% s0 rate among eligible / effective overall rate | 5.08 / 3.71 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.05_s0.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r1 5% s1 LC live / hindsight overall RMSE | 4.0830 / 3.9531 | m | CURRENT | `json:scores/E3a_T_A_r1_0.05_s1.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 5% s1 LC live lap 1 / lap 5 RMSE | 4.3625 / 4.0126 | m | CURRENT | `json:scores/E3a_T_A_r1_0.05_s1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 5% s1 LC live lap-5 / lap-1 | 0.92 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.05_s1.ratio lc live lap5/lap1` |
| T_A_r1 5% s1 injected / eligible non-gauge / all central calls (whole bag) | 86 / 1770 / 2423 | count | CURRENT | `tier1:T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s1/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.05_s1.covariates.mislabel`) |
| T_A_r1 5% s1 rate among eligible / effective overall rate | 4.86 / 3.55 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.05_s1.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r1 5% s2 LC live / hindsight overall RMSE | 4.1469 / 3.9388 | m | CURRENT | `json:scores/E3a_T_A_r1_0.05_s2.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 5% s2 LC live lap 1 / lap 5 RMSE | 4.6374 / 4.0035 | m | CURRENT | `json:scores/E3a_T_A_r1_0.05_s2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 5% s2 LC live lap-5 / lap-1 | 0.86 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.05_s2.ratio lc live lap5/lap1` |
| T_A_r1 5% s2 injected / eligible non-gauge / all central calls (whole bag) | 85 / 1770 / 2423 | count | CURRENT | `tier1:T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s2/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.05_s2.covariates.mislabel`) |
| T_A_r1 5% s2 rate among eligible / effective overall rate | 4.80 / 3.51 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r1_0.05_s2.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r2 1% s0 LC live / hindsight overall RMSE | 3.7161 / 3.5968 | m | CURRENT | `json:scores/E3a_T_A_r2_0.01_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 1% s0 LC live lap 1 / lap 5 RMSE | 3.9786 / 3.5885 | m | CURRENT | `json:scores/E3a_T_A_r2_0.01_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 1% s0 LC live lap-5 / lap-1 | 0.90 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.01_s0.ratio lc live lap5/lap1` |
| T_A_r2 1% s0 injected / eligible non-gauge / all central calls (whole bag) | 19 / 1695 / 2328 | count | CURRENT | `tier1:T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s0/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.01_s0.covariates.mislabel`) |
| T_A_r2 1% s0 rate among eligible / effective overall rate | 1.12 / 0.82 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.01_s0.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r2 1% s1 run status | **FAILED-ESTIMATOR (diverged)**: live divergence onset 61.795 s; first exception 62.595 s; failure fraction 0.8627 (6342 / 7351; inflated: no recovery after a throw) | s / ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.01_s1.run_status` (from `tier1:stage2e/status/e3a_T_A_r2_0.01_s1.json`) |
| T_A_r2 1% s1 injected / eligible non-gauge / all central calls (whole bag) | 14 / 1695 / 2328 | count | CURRENT | `tier1:T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s1/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.01_s1.covariates.mislabel`) |
| T_A_r2 1% s1 rate among eligible / effective overall rate | 0.83 / 0.60 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.01_s1.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r2 1% s2 run status | **FAILED-ESTIMATOR (diverged)**: live divergence onset 59.928 s; first exception 60.695 s; failure fraction 0.8705 (6399 / 7351; inflated: no recovery after a throw) | s / ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.01_s2.run_status` (from `tier1:stage2e/status/e3a_T_A_r2_0.01_s2.json`) |
| T_A_r2 1% s2 injected / eligible non-gauge / all central calls (whole bag) | 14 / 1695 / 2328 | count | CURRENT | `tier1:T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s2/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.01_s2.covariates.mislabel`) |
| T_A_r2 1% s2 rate among eligible / effective overall rate | 0.83 / 0.60 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.01_s2.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r2 5% s0 LC live / hindsight overall RMSE | 4.1379 / 3.9387 | m | CURRENT | `json:scores/E3a_T_A_r2_0.05_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 5% s0 LC live lap 1 / lap 5 RMSE | 4.3695 / 3.9365 | m | CURRENT | `json:scores/E3a_T_A_r2_0.05_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 5% s0 LC live lap-5 / lap-1 | 0.90 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.05_s0.ratio lc live lap5/lap1` |
| T_A_r2 5% s0 injected / eligible non-gauge / all central calls (whole bag) | 88 / 1695 / 2328 | count | CURRENT | `tier1:T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s0/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.05_s0.covariates.mislabel`) |
| T_A_r2 5% s0 rate among eligible / effective overall rate | 5.19 / 3.78 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.05_s0.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r2 5% s1 LC live / hindsight overall RMSE | 4.1610 / 3.9120 | m | CURRENT | `json:scores/E3a_T_A_r2_0.05_s1.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 5% s1 LC live lap 1 / lap 5 RMSE | 4.4566 / 3.9583 | m | CURRENT | `json:scores/E3a_T_A_r2_0.05_s1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 5% s1 LC live lap-5 / lap-1 | 0.89 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.05_s1.ratio lc live lap5/lap1` |
| T_A_r2 5% s1 injected / eligible non-gauge / all central calls (whole bag) | 78 / 1695 / 2328 | count | CURRENT | `tier1:T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s1/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.05_s1.covariates.mislabel`) |
| T_A_r2 5% s1 rate among eligible / effective overall rate | 4.60 / 3.35 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.05_s1.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r2 5% s2 LC live / hindsight overall RMSE | 4.2231 / 3.9123 | m | CURRENT | `json:scores/E3a_T_A_r2_0.05_s2.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 5% s2 LC live lap 1 / lap 5 RMSE | 4.6830 / 3.9500 | m | CURRENT | `json:scores/E3a_T_A_r2_0.05_s2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 5% s2 LC live lap-5 / lap-1 | 0.84 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.05_s2.ratio lc live lap5/lap1` |
| T_A_r2 5% s2 injected / eligible non-gauge / all central calls (whole bag) | 75 / 1695 / 2328 | count | CURRENT | `tier1:T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s2/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.05_s2.covariates.mislabel`) |
| T_A_r2 5% s2 rate among eligible / effective overall rate | 4.42 / 3.22 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r2_0.05_s2.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r3 1% s0 LC live / hindsight overall RMSE | 3.8960 / 3.7711 | m | CURRENT | `json:scores/E3a_T_A_r3_0.01_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 1% s0 LC live lap 1 / lap 5 RMSE | 3.4195 / 4.0654 | m | CURRENT | `json:scores/E3a_T_A_r3_0.01_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 1% s0 LC live lap-5 / lap-1 | 1.19 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.01_s0.ratio lc live lap5/lap1` |
| T_A_r3 1% s0 injected / eligible non-gauge / all central calls (whole bag) | 20 / 1683 / 2314 | count | CURRENT | `tier1:T_A_r3/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s0/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.01_s0.covariates.mislabel`) |
| T_A_r3 1% s0 rate among eligible / effective overall rate | 1.19 / 0.86 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.01_s0.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r3 1% s1 run status | **FAILED-ESTIMATOR (diverged)**: live divergence onset 56.248 s; first exception 60.548 s; failure fraction 0.8701 (6396 / 7351; inflated: no recovery after a throw) | s / ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.01_s1.run_status` (from `tier1:stage2e/status/e3a_T_A_r3_0.01_s1.json`) |
| T_A_r3 1% s1 injected / eligible non-gauge / all central calls (whole bag) | 17 / 1683 / 2314 | count | CURRENT | `tier1:T_A_r3/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s1/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.01_s1.covariates.mislabel`) |
| T_A_r3 1% s1 rate among eligible / effective overall rate | 1.01 / 0.73 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.01_s1.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r3 1% s2 run status | **FAILED-ESTIMATOR (diverged)**: live divergence onset 60.314 s; first exception 65.614 s; failure fraction 0.8494 (6244 / 7351; inflated: no recovery after a throw) | s / ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.01_s2.run_status` (from `tier1:stage2e/status/e3a_T_A_r3_0.01_s2.json`) |
| T_A_r3 1% s2 injected / eligible non-gauge / all central calls (whole bag) | 14 / 1683 / 2314 | count | CURRENT | `tier1:T_A_r3/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s2/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.01_s2.covariates.mislabel`) |
| T_A_r3 1% s2 rate among eligible / effective overall rate | 0.83 / 0.61 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.01_s2.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r3 5% s0 LC live / hindsight overall RMSE | 4.0904 / 3.9350 | m | CURRENT | `json:scores/E3a_T_A_r3_0.05_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 5% s0 LC live lap 1 / lap 5 RMSE | 4.2765 / 4.0537 | m | CURRENT | `json:scores/E3a_T_A_r3_0.05_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 5% s0 LC live lap-5 / lap-1 | 0.95 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.05_s0.ratio lc live lap5/lap1` |
| T_A_r3 5% s0 injected / eligible non-gauge / all central calls (whole bag) | 94 / 1683 / 2314 | count | CURRENT | `tier1:T_A_r3/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s0/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.05_s0.covariates.mislabel`) |
| T_A_r3 5% s0 rate among eligible / effective overall rate | 5.59 / 4.06 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.05_s0.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r3 5% s1 LC live / hindsight overall RMSE | 4.0395 / 3.9140 | m | CURRENT | `json:scores/E3a_T_A_r3_0.05_s1.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 5% s1 LC live lap 1 / lap 5 RMSE | 4.1280 / 4.0386 | m | CURRENT | `json:scores/E3a_T_A_r3_0.05_s1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 5% s1 LC live lap-5 / lap-1 | 0.98 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.05_s1.ratio lc live lap5/lap1` |
| T_A_r3 5% s1 injected / eligible non-gauge / all central calls (whole bag) | 82 / 1683 / 2314 | count | CURRENT | `tier1:T_A_r3/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s1/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.05_s1.covariates.mislabel`) |
| T_A_r3 5% s1 rate among eligible / effective overall rate | 4.87 / 3.54 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.05_s1.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| T_A_r3 5% s2 LC live / hindsight overall RMSE | 4.0864 / 3.8532 | m | CURRENT | `json:scores/E3a_T_A_r3_0.05_s2.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 5% s2 LC live lap 1 / lap 5 RMSE | 4.5171 / 3.9602 | m | CURRENT | `json:scores/E3a_T_A_r3_0.05_s2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 5% s2 LC live lap-5 / lap-1 | 0.88 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.05_s2.ratio lc live lap5/lap1` |
| T_A_r3 5% s2 injected / eligible non-gauge / all central calls (whole bag) | 80 / 1683 / 2314 | count | CURRENT | `tier1:T_A_r3/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s2/stats.json:tier1.mislabel` (copied to `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.05_s2.covariates.mislabel`) |
| T_A_r3 5% s2 rate among eligible / effective overall rate | 4.75 / 3.46 | % | CURRENT | `json:scores/E3_verdicts.json:runs.E3a_T_A_r3_0.05_s2.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |
| pooled 1% (9 runs): rate among eligible / effective overall rate | 0.97 / 0.71 | % | CURRENT | `json:scores/E3_verdicts.json:effective_rates.a 0.01.pooled_rate_among_eligible`, `.pooled_effective_overall_rate` |
| pooled 5% (9 runs): rate among eligible / effective overall rate | 4.91 / 3.58 | % | CURRENT | `json:scores/E3_verdicts.json:effective_rates.a 0.05.pooled_rate_among_eligible`, `.pooled_effective_overall_rate` |
| T_A_r1 P-E3.6 | not satisfied (diverged: E3a_T_A_r1_0.01_s1, E3a_T_A_r1_0.01_s2); seed means not computed | — | CURRENT | `json:scores/E3_verdicts.json:criteria_a.P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight.per_flight.T_A_r1` |
| T_A_r2 P-E3.6 | not satisfied (diverged: E3a_T_A_r2_0.01_s1, E3a_T_A_r2_0.01_s2); seed means not computed | — | CURRENT | `json:scores/E3_verdicts.json:criteria_a.P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight.per_flight.T_A_r2` |
| T_A_r3 P-E3.6 | not satisfied (diverged: E3a_T_A_r3_0.01_s1, E3a_T_A_r3_0.01_s2); seed means not computed | — | CURRENT | `json:scores/E3_verdicts.json:criteria_a.P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight.per_flight.T_A_r3` |

| criterion | verdict | count | divergence (k of 3 runs diverged, per flight) | source |
|---|---|---|---|---|
| H-E3.1 (PRIMARY) 1%: LC live < stored no-LC live | **FAIL** | 0/9 | T_A_r1: 2 of 3 runs diverged; T_A_r2: 2 of 3 runs diverged; T_A_r3: 2 of 3 runs diverged (total 6 of 9 runs diverged) | `json:scores/E3_verdicts.json:criteria_a.H-E3.1 (PRIMARY) 1%: LC live < stored no-LC live` |
| H-E3.2 1%: LC hindsight < stored no-LC hindsight | **FAIL** | 0/9 | T_A_r1: 2 of 3 runs diverged; T_A_r2: 2 of 3 runs diverged; T_A_r3: 2 of 3 runs diverged (total 6 of 9 runs diverged) | `json:scores/E3_verdicts.json:criteria_a.H-E3.2 1%: LC hindsight < stored no-LC hindsight` |
| H-E3.3 1%: LC live lap5 <= 1.5 x lap1 | **FAIL** | 3/9 | T_A_r1: 2 of 3 runs diverged; T_A_r2: 2 of 3 runs diverged; T_A_r3: 2 of 3 runs diverged (total 6 of 9 runs diverged) | `json:scores/E3_verdicts.json:criteria_a.H-E3.3 1%: LC live lap5 <= 1.5 x lap1` |
| P-E3.4 1%: LC live <= 2 x stored clean LC live (x2: judgement, not derived from data) | **FAIL** | 0/9 | T_A_r1: 2 of 3 runs diverged; T_A_r2: 2 of 3 runs diverged; T_A_r3: 2 of 3 runs diverged (total 6 of 9 runs diverged) | `json:scores/E3_verdicts.json:criteria_a.P-E3.4 1%: LC live <= 2 x stored clean LC live (x2: judgement, not derived from data)` |
| P-E3.5a 5%: H-E3.1 criterion | **FAIL** | 0/9 | T_A_r1: 0 of 3 runs diverged; T_A_r2: 0 of 3 runs diverged; T_A_r3: 0 of 3 runs diverged (total 0 of 9 runs diverged) | `json:scores/E3_verdicts.json:criteria_a.P-E3.5a 5%: H-E3.1 criterion` |
| P-E3.5b 5%: H-E3.2 criterion | **FAIL** | 0/9 | T_A_r1: 0 of 3 runs diverged; T_A_r2: 0 of 3 runs diverged; T_A_r3: 0 of 3 runs diverged (total 0 of 9 runs diverged) | `json:scores/E3_verdicts.json:criteria_a.P-E3.5b 5%: H-E3.2 criterion` |
| P-E3.5c 5%: H-E3.3 criterion | **PASS** | 9/9 | T_A_r1: 0 of 3 runs diverged; T_A_r2: 0 of 3 runs diverged; T_A_r3: 0 of 3 runs diverged (total 0 of 9 runs diverged) | `json:scores/E3_verdicts.json:criteria_a.P-E3.5c 5%: H-E3.3 criterion` |
| P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight | **FAIL** | 0/3 | T_A_r1: 2 of 6 runs diverged; T_A_r2: 2 of 6 runs diverged; T_A_r3: 2 of 6 runs diverged (total 6 of 18 runs diverged) | `json:scores/E3_verdicts.json:criteria_a.P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight` |

### Arm (b): robust tag factors, Cauchy k = 2.385 (ESTIMATOR VARIANT)

| quantity | value | unit | status | source |
|---|---|---|---|---|
| T_A_r1 robust rate 0 (control) LC live / hindsight overall RMSE | 0.0581 / 0.0201 | m | CURRENT | `json:scores/E3b_T_A_r1_0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 robust rate 0 (control) LC live lap 1 / lap 5 RMSE | 0.1080 / 0.0329 | m | CURRENT | `json:scores/E3b_T_A_r1_0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 robust rate 0 (control) LC live lap-5 / lap-1 | 0.30 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.ratio lc live lap5/lap1` |
| T_A_r1 robust rate 0: LC live ÷ stored clean LC live | 1.01 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.lc live / stored clean lc live` |
| T_A_r1 robust 1% s0 LC live / hindsight overall RMSE | 0.8694 / 0.0139 | m | CURRENT | `json:scores/E3b_T_A_r1_0.01_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 robust 1% s0 LC live lap 1 / lap 5 RMSE | 1.9222 / 0.0281 | m | CURRENT | `json:scores/E3b_T_A_r1_0.01_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 robust 1% s0 LC live lap-5 / lap-1 | 0.01 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.01_s0.ratio lc live lap5/lap1` |
| T_A_r1 robust 1% s0 LC live ÷ arm (a) LC live | 0.23 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.01_s0.b live / a live` |
| T_A_r1 robust 1% s1 LC live / hindsight overall RMSE | 0.1758 / 0.0154 | m | CURRENT | `json:scores/E3b_T_A_r1_0.01_s1.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 robust 1% s1 LC live lap 1 / lap 5 RMSE | 0.3645 / 0.0275 | m | CURRENT | `json:scores/E3b_T_A_r1_0.01_s1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 robust 1% s1 LC live lap-5 / lap-1 | 0.08 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.01_s1.ratio lc live lap5/lap1` |
| T_A_r1 robust 1% s1 P-E3b.1 | (a) diverged at 49.699 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not finite | — | CURRENT | `json:scores/E3_verdicts.json:criteria_b.P-E3b.1 0.01: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data).satisfied, flagged.E3b_T_A_r1_0.01_s1` |
| T_A_r1 robust 1% s2 LC live / hindsight overall RMSE | 0.3902 / 0.0149 | m | CURRENT | `json:scores/E3b_T_A_r1_0.01_s2.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 robust 1% s2 LC live lap 1 / lap 5 RMSE | 0.8693 / 0.0296 | m | CURRENT | `json:scores/E3b_T_A_r1_0.01_s2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 robust 1% s2 LC live lap-5 / lap-1 | 0.03 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.01_s2.ratio lc live lap5/lap1` |
| T_A_r1 robust 1% s2 P-E3b.1 | (a) diverged at 59.699 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not finite | — | CURRENT | `json:scores/E3_verdicts.json:criteria_b.P-E3b.1 0.01: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data).satisfied, flagged.E3b_T_A_r1_0.01_s2` |
| T_A_r1 robust 5% s0 LC live / hindsight overall RMSE | 1.0698 / 0.0914 | m | CURRENT | `json:scores/E3b_T_A_r1_0.05_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 robust 5% s0 LC live lap 1 / lap 5 RMSE | 2.3285 / 0.0961 | m | CURRENT | `json:scores/E3b_T_A_r1_0.05_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 robust 5% s0 LC live lap-5 / lap-1 | 0.04 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.05_s0.ratio lc live lap5/lap1` |
| T_A_r1 robust 5% s0 LC live ÷ arm (a) LC live | 0.26 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.05_s0.b live / a live` |
| T_A_r1 robust 5% s1 LC live / hindsight overall RMSE | 1.7538 / 0.0826 | m | CURRENT | `json:scores/E3b_T_A_r1_0.05_s1.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 robust 5% s1 LC live lap 1 / lap 5 RMSE | 3.6419 / 0.0871 | m | CURRENT | `json:scores/E3b_T_A_r1_0.05_s1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 robust 5% s1 LC live lap-5 / lap-1 | 0.02 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.05_s1.ratio lc live lap5/lap1` |
| T_A_r1 robust 5% s1 LC live ÷ arm (a) LC live | 0.43 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.05_s1.b live / a live` |
| T_A_r1 robust 5% s2 LC live / hindsight overall RMSE | 1.0040 / 0.0870 | m | CURRENT | `json:scores/E3b_T_A_r1_0.05_s2.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r1 robust 5% s2 LC live lap 1 / lap 5 RMSE | 2.2157 / 0.0917 | m | CURRENT | `json:scores/E3b_T_A_r1_0.05_s2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 robust 5% s2 LC live lap-5 / lap-1 | 0.04 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.05_s2.ratio lc live lap5/lap1` |
| T_A_r1 robust 5% s2 LC live ÷ arm (a) LC live | 0.24 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r1_0.05_s2.b live / a live` |
| T_A_r2 robust rate 0 (control) LC live / hindsight overall RMSE | 0.0484 / 0.0263 | m | CURRENT | `json:scores/E3b_T_A_r2_0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 robust rate 0 (control) LC live lap 1 / lap 5 RMSE | 0.0811 / 0.0341 | m | CURRENT | `json:scores/E3b_T_A_r2_0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 robust rate 0 (control) LC live lap-5 / lap-1 | 0.42 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.ratio lc live lap5/lap1` |
| T_A_r2 robust rate 0: LC live ÷ stored clean LC live | 0.98 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.lc live / stored clean lc live` |
| T_A_r2 robust 1% s0 LC live / hindsight overall RMSE | 1.4769 / 0.0179 | m | CURRENT | `json:scores/E3b_T_A_r2_0.01_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 robust 1% s0 LC live lap 1 / lap 5 RMSE | 3.0925 / 0.0285 | m | CURRENT | `json:scores/E3b_T_A_r2_0.01_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 robust 1% s0 LC live lap-5 / lap-1 | 0.01 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.01_s0.ratio lc live lap5/lap1` |
| T_A_r2 robust 1% s0 LC live ÷ arm (a) LC live | 0.40 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.01_s0.b live / a live` |
| T_A_r2 robust 1% s1 LC live / hindsight overall RMSE | 0.0496 / 0.0154 | m | CURRENT | `json:scores/E3b_T_A_r2_0.01_s1.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 robust 1% s1 LC live lap 1 / lap 5 RMSE | 0.0904 / 0.0271 | m | CURRENT | `json:scores/E3b_T_A_r2_0.01_s1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 robust 1% s1 LC live lap-5 / lap-1 | 0.30 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.01_s1.ratio lc live lap5/lap1` |
| T_A_r2 robust 1% s1 P-E3b.1 | (a) diverged at 61.795 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not finite | — | CURRENT | `json:scores/E3_verdicts.json:criteria_b.P-E3b.1 0.01: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data).satisfied, flagged.E3b_T_A_r2_0.01_s1` |
| T_A_r2 robust 1% s2 LC live / hindsight overall RMSE | 0.2287 / 0.0151 | m | CURRENT | `json:scores/E3b_T_A_r2_0.01_s2.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 robust 1% s2 LC live lap 1 / lap 5 RMSE | 0.4342 / 0.0256 | m | CURRENT | `json:scores/E3b_T_A_r2_0.01_s2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 robust 1% s2 LC live lap-5 / lap-1 | 0.06 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.01_s2.ratio lc live lap5/lap1` |
| T_A_r2 robust 1% s2 P-E3b.1 | (a) diverged at 59.928 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not finite | — | CURRENT | `json:scores/E3_verdicts.json:criteria_b.P-E3b.1 0.01: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data).satisfied, flagged.E3b_T_A_r2_0.01_s2` |
| T_A_r2 robust 5% s0 LC live / hindsight overall RMSE | 1.6147 / 0.0856 | m | CURRENT | `json:scores/E3b_T_A_r2_0.05_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 robust 5% s0 LC live lap 1 / lap 5 RMSE | 3.4054 / 0.0877 | m | CURRENT | `json:scores/E3b_T_A_r2_0.05_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 robust 5% s0 LC live lap-5 / lap-1 | 0.03 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.05_s0.ratio lc live lap5/lap1` |
| T_A_r2 robust 5% s0 LC live ÷ arm (a) LC live | 0.39 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.05_s0.b live / a live` |
| T_A_r2 robust 5% s1 LC live / hindsight overall RMSE | 4.1849 / 4.2233 | m | CURRENT | `json:scores/E3b_T_A_r2_0.05_s1.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 robust 5% s1 LC live lap 1 / lap 5 RMSE | 3.7542 / 4.2488 | m | CURRENT | `json:scores/E3b_T_A_r2_0.05_s1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 robust 5% s1 LC live lap-5 / lap-1 | 1.13 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.05_s1.ratio lc live lap5/lap1` |
| T_A_r2 robust 5% s1 LC live ÷ arm (a) LC live | 1.01 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.05_s1.b live / a live` |
| T_A_r2 robust 5% s2 LC live / hindsight overall RMSE | 1.0706 / 0.0763 | m | CURRENT | `json:scores/E3b_T_A_r2_0.05_s2.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r2 robust 5% s2 LC live lap 1 / lap 5 RMSE | 2.3746 / 0.0790 | m | CURRENT | `json:scores/E3b_T_A_r2_0.05_s2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 robust 5% s2 LC live lap-5 / lap-1 | 0.03 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.05_s2.ratio lc live lap5/lap1` |
| T_A_r2 robust 5% s2 LC live ÷ arm (a) LC live | 0.25 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r2_0.05_s2.b live / a live` |
| T_A_r3 robust rate 0 (control) LC live / hindsight overall RMSE | 0.0760 / 0.0175 | m | CURRENT | `json:scores/E3b_T_A_r3_0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 robust rate 0 (control) LC live lap 1 / lap 5 RMSE | 0.1614 / 0.0250 | m | CURRENT | `json:scores/E3b_T_A_r3_0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 robust rate 0 (control) LC live lap-5 / lap-1 | 0.15 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.ratio lc live lap5/lap1` |
| T_A_r3 robust rate 0: LC live ÷ stored clean LC live | 1.00 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.lc live / stored clean lc live` |
| T_A_r3 robust 1% s0 LC live / hindsight overall RMSE | 0.8356 / 0.0145 | m | CURRENT | `json:scores/E3b_T_A_r3_0.01_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 robust 1% s0 LC live lap 1 / lap 5 RMSE | 1.8504 / 0.0250 | m | CURRENT | `json:scores/E3b_T_A_r3_0.01_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 robust 1% s0 LC live lap-5 / lap-1 | 0.01 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.01_s0.ratio lc live lap5/lap1` |
| T_A_r3 robust 1% s0 LC live ÷ arm (a) LC live | 0.21 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.01_s0.b live / a live` |
| T_A_r3 robust 1% s1 LC live / hindsight overall RMSE | 0.1984 / 0.0120 | m | CURRENT | `json:scores/E3b_T_A_r3_0.01_s1.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 robust 1% s1 LC live lap 1 / lap 5 RMSE | 0.4147 / 0.0265 | m | CURRENT | `json:scores/E3b_T_A_r3_0.01_s1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 robust 1% s1 LC live lap-5 / lap-1 | 0.06 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.01_s1.ratio lc live lap5/lap1` |
| T_A_r3 robust 1% s1 P-E3b.1 | (a) diverged at 56.248 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not finite | — | CURRENT | `json:scores/E3_verdicts.json:criteria_b.P-E3b.1 0.01: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data).satisfied, flagged.E3b_T_A_r3_0.01_s1` |
| T_A_r3 robust 1% s2 LC live / hindsight overall RMSE | 0.1259 / 0.0114 | m | CURRENT | `json:scores/E3b_T_A_r3_0.01_s2.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 robust 1% s2 LC live lap 1 / lap 5 RMSE | 0.2767 / 0.0238 | m | CURRENT | `json:scores/E3b_T_A_r3_0.01_s2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 robust 1% s2 LC live lap-5 / lap-1 | 0.09 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.01_s2.ratio lc live lap5/lap1` |
| T_A_r3 robust 1% s2 P-E3b.1 | (a) diverged at 60.314 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not finite | — | CURRENT | `json:scores/E3_verdicts.json:criteria_b.P-E3b.1 0.01: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data).satisfied, flagged.E3b_T_A_r3_0.01_s2` |
| T_A_r3 robust 5% s0 LC live / hindsight overall RMSE | 1.0551 / 0.1072 | m | CURRENT | `json:scores/E3b_T_A_r3_0.05_s0.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 robust 5% s0 LC live lap 1 / lap 5 RMSE | 2.3084 / 0.1143 | m | CURRENT | `json:scores/E3b_T_A_r3_0.05_s0.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 robust 5% s0 LC live lap-5 / lap-1 | 0.05 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.05_s0.ratio lc live lap5/lap1` |
| T_A_r3 robust 5% s0 LC live ÷ arm (a) LC live | 0.26 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.05_s0.b live / a live` |
| T_A_r3 robust 5% s1 LC live / hindsight overall RMSE | 1.6546 / 0.0872 | m | CURRENT | `json:scores/E3b_T_A_r3_0.05_s1.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 robust 5% s1 LC live lap 1 / lap 5 RMSE | 3.4348 / 0.0955 | m | CURRENT | `json:scores/E3b_T_A_r3_0.05_s1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 robust 5% s1 LC live lap-5 / lap-1 | 0.03 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.05_s1.ratio lc live lap5/lap1` |
| T_A_r3 robust 5% s1 LC live ÷ arm (a) LC live | 0.41 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.05_s1.b live / a live` |
| T_A_r3 robust 5% s2 LC live / hindsight overall RMSE | 0.9776 / 0.0824 | m | CURRENT | `json:scores/E3b_T_A_r3_0.05_s2.json:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |
| T_A_r3 robust 5% s2 LC live lap 1 / lap 5 RMSE | 2.1636 / 0.0902 | m | CURRENT | `json:scores/E3b_T_A_r3_0.05_s2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 robust 5% s2 LC live lap-5 / lap-1 | 0.04 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.05_s2.ratio lc live lap5/lap1` |
| T_A_r3 robust 5% s2 LC live ÷ arm (a) LC live | 0.24 | ratio | CURRENT | `json:scores/E3_verdicts.json:runs.E3b_T_A_r3_0.05_s2.b live / a live` |
| **runtime, serial 0% pair on T_A_r2 (headline): arm (b) ÷ arm (a) wall** | 0.79 (121.2 / 153.5 s) | ratio | DESCRIPTIVE (DIAGNOSTIC timing) | `json:scores/E3_verdicts.json:runtime_descriptive.0.T_A_r2` |
| runtime (b)/(a), 1%: median (min–max) of 3 pairs without a diverged run | 0.07 (0.04–0.16) | ratio | DESCRIPTIVE, NOT LIKE FOR LIKE (parallel batch) | `json:scores/E3_verdicts.json:runtime_descriptive.0.01` |
| runtime (b)/(a), 5%: median (min–max) of 9 pairs without a diverged run | 0.04 (0.03–0.08) | ratio | DESCRIPTIVE, NOT LIKE FOR LIKE (parallel batch) | `json:scores/E3_verdicts.json:runtime_descriptive.0.05` |
| T_A_r1 runtime rate-0 control ÷ G0-L (i) (serial; arm (b) in the parallel batch) | 1.62 (206.2 / 127.2 s) | ratio | DESCRIPTIVE, NOT LIKE FOR LIKE | `json:scores/E3_verdicts.json:runtime_descriptive.0.T_A_r1` |
| T_A_r3 runtime rate-0 control ÷ stored clean wall (6 parallel; arm (b) in the parallel batch) | 0.75 (387.3 / 518.6 s) | ratio | DESCRIPTIVE, NOT LIKE FOR LIKE | `json:scores/E3_verdicts.json:runtime_descriptive.0.T_A_r3` |

| criterion | verdict | count | divergence (k of 3 runs diverged, per flight) | source |
|---|---|---|---|---|
| P-E3b.1 0.01: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data) [satisfied, flagged ((a) diverged, (b) OK; no ratio): E3b_T_A_r1_0.01_s1, E3b_T_A_r1_0.01_s2, E3b_T_A_r2_0.01_s1, E3b_T_A_r2_0.01_s2, E3b_T_A_r3_0.01_s1, E3b_T_A_r3_0.01_s2] | **PASS** | 9/9 | T_A_r1: arm (a): 2 of 3 runs diverged; arm (b): 0 of 3 runs diverged; T_A_r2: arm (a): 2 of 3 runs diverged; arm (b): 0 of 3 runs diverged; T_A_r3: arm (a): 2 of 3 runs diverged; arm (b): 0 of 3 runs diverged (total 6 of 18 runs diverged) | `json:scores/E3_verdicts.json:criteria_b.P-E3b.1 0.01: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data)` |
| P-E3b.1 0.05: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data) | **PASS** | 9/9 | T_A_r1: arm (a): 0 of 3 runs diverged; arm (b): 0 of 3 runs diverged; T_A_r2: arm (a): 0 of 3 runs diverged; arm (b): 0 of 3 runs diverged; T_A_r3: arm (a): 0 of 3 runs diverged; arm (b): 0 of 3 runs diverged (total 0 of 18 runs diverged) | `json:scores/E3_verdicts.json:criteria_b.P-E3b.1 0.05: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data)` |
| P-E3b.2 rate 0: |robust LC live / stored clean LC live - 1| <= 0.10 (±10%: judgement, not derived from data) | **PASS** | 3/3 | T_A_r1: 0 of 1 runs diverged; T_A_r2: 0 of 1 runs diverged; T_A_r3: 0 of 1 runs diverged (total 0 of 3 runs diverged) | `json:scores/E3_verdicts.json:criteria_b.P-E3b.2 rate 0: |robust LC live / stored clean LC live - 1| <= 0.10 (±10%: judgement, not derived from data)` |

## E4: live window sweep (12 T bags; W = 0.25 / 0.5 / 1 / 2 / 5 s)

| quantity | value | unit | status | source |
|---|---|---|---|---|

Verdicts: P-E4.1, P-E4.2, H-E4.3 (live at 5 s < live at 0.25 s, ≥ 10/12). Fraction of the batch gain recovered
f_i(W) and pooled F(W): DESCRIPTIVE. LM-cap convergence flags.

## E5: UKF with tag landmark states (T_A, LC / no-LC)

| quantity | value | unit | status | source |
|---|---|---|---|---|
| T_A_r1 LC live overall RMSE | 0.1193 | m | CURRENT | `json:scores/e5_T_A_r1.json:tracks.lc live.rmse_m` |
| T_A_r1 LC live lap 1 / lap 5 RMSE | 0.2240 / 0.0601 | m | CURRENT | `json:scores/e5_T_A_r1.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 LC RTS hindsight overall RMSE | 0.0445 | m | CURRENT | `json:scores/e5_T_A_r1.json:tracks.lc hindsight.rmse_m` |
| T_A_r1 LC RTS hindsight lap 1 / lap 5 RMSE | 0.0466 / 0.0444 | m | CURRENT | `json:scores/e5_T_A_r1.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 no-LC live overall RMSE | 0.8738 | m | CURRENT | `json:scores/e5_T_A_r1.json:tracks.nolc live.rmse_m` |
| T_A_r1 no-LC live lap 1 / lap 5 RMSE | 0.2240 / 1.5395 | m | CURRENT | `json:scores/e5_T_A_r1.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 no-LC RTS hindsight overall RMSE | 0.9162 | m | CURRENT | `json:scores/e5_T_A_r1.json:tracks.nolc hindsight.rmse_m` |
| T_A_r1 no-LC RTS hindsight lap 1 / lap 5 RMSE | 0.1355 / 1.5608 | m | CURRENT | `json:scores/e5_T_A_r1.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 LC live overall RMSE | 0.0911 | m | CURRENT | `json:scores/e5_T_A_r2.json:tracks.lc live.rmse_m` |
| T_A_r2 LC live lap 1 / lap 5 RMSE | 0.1560 / 0.0652 | m | CURRENT | `json:scores/e5_T_A_r2.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 LC RTS hindsight overall RMSE | 0.0461 | m | CURRENT | `json:scores/e5_T_A_r2.json:tracks.lc hindsight.rmse_m` |
| T_A_r2 LC RTS hindsight lap 1 / lap 5 RMSE | 0.0478 / 0.0445 | m | CURRENT | `json:scores/e5_T_A_r2.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 no-LC live overall RMSE | 1.4112 | m | CURRENT | `json:scores/e5_T_A_r2.json:tracks.nolc live.rmse_m` |
| T_A_r2 no-LC live lap 1 / lap 5 RMSE | 0.1560 / 2.2801 | m | CURRENT | `json:scores/e5_T_A_r2.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r2 no-LC RTS hindsight overall RMSE | 1.3349 | m | CURRENT | `json:scores/e5_T_A_r2.json:tracks.nolc hindsight.rmse_m` |
| T_A_r2 no-LC RTS hindsight lap 1 / lap 5 RMSE | 0.2253 / 2.2087 | m | CURRENT | `json:scores/e5_T_A_r2.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 LC live overall RMSE | 0.1335 | m | CURRENT | `json:scores/e5_T_A_r3.json:tracks.lc live.rmse_m` |
| T_A_r3 LC live lap 1 / lap 5 RMSE | 0.2565 / 0.0757 | m | CURRENT | `json:scores/e5_T_A_r3.json:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 LC RTS hindsight overall RMSE | 0.0552 | m | CURRENT | `json:scores/e5_T_A_r3.json:tracks.lc hindsight.rmse_m` |
| T_A_r3 LC RTS hindsight lap 1 / lap 5 RMSE | 0.0563 / 0.0560 | m | CURRENT | `json:scores/e5_T_A_r3.json:tracks.lc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 no-LC live overall RMSE | 0.9262 | m | CURRENT | `json:scores/e5_T_A_r3.json:tracks.nolc live.rmse_m` |
| T_A_r3 no-LC live lap 1 / lap 5 RMSE | 0.2565 / 1.6257 | m | CURRENT | `json:scores/e5_T_A_r3.json:tracks.nolc live.per_lap_rmse_m[0]`, `[4]` |
| T_A_r3 no-LC RTS hindsight overall RMSE | 1.0446 | m | CURRENT | `json:scores/e5_T_A_r3.json:tracks.nolc hindsight.rmse_m` |
| T_A_r3 no-LC RTS hindsight lap 1 / lap 5 RMSE | 0.1628 / 1.7709 | m | CURRENT | `json:scores/e5_T_A_r3.json:tracks.nolc hindsight.per_lap_rmse_m[0]`, `[4]` |
| T_A_r1 UKF-LC live lap-5 / lap-1 | 0.27 | ratio | CURRENT | `json:scores/e5_verdicts.json:flights.T_A_r1.ratio lc live lap5/lap1` |
| T_A_r1 UKF-no-LC live lap-5 / lap-1 | 6.87 | ratio | CURRENT | `json:scores/e5_verdicts.json:flights.T_A_r1.ratio nolc live lap5/lap1` |
| T_A_r1 UKF ÷ stored FGO, LC live / LC hindsight | 2.08 / 2.25 | ratio | DESCRIPTIVE | `json:scores/e5_verdicts.json:flights.T_A_r1.descriptive ratios UKF/FGO` |
| T_A_r2 UKF-LC live lap-5 / lap-1 | 0.42 | ratio | CURRENT | `json:scores/e5_verdicts.json:flights.T_A_r2.ratio lc live lap5/lap1` |
| T_A_r2 UKF-no-LC live lap-5 / lap-1 | 14.62 | ratio | CURRENT | `json:scores/e5_verdicts.json:flights.T_A_r2.ratio nolc live lap5/lap1` |
| T_A_r2 UKF ÷ stored FGO, LC live / LC hindsight | 1.84 / 1.71 | ratio | DESCRIPTIVE | `json:scores/e5_verdicts.json:flights.T_A_r2.descriptive ratios UKF/FGO` |
| T_A_r3 UKF-LC live lap-5 / lap-1 | 0.30 | ratio | CURRENT | `json:scores/e5_verdicts.json:flights.T_A_r3.ratio lc live lap5/lap1` |
| T_A_r3 UKF-no-LC live lap-5 / lap-1 | 6.34 | ratio | CURRENT | `json:scores/e5_verdicts.json:flights.T_A_r3.ratio nolc live lap5/lap1` |
| T_A_r3 UKF ÷ stored FGO, LC live / LC hindsight | 1.76 / 3.21 | ratio | DESCRIPTIVE | `json:scores/e5_verdicts.json:flights.T_A_r3.descriptive ratios UKF/FGO` |

Verdicts: H-E5.1 (PRIMARY), H-E5.2, H-E5.3, P-E5.4. Secondary (landmark UKF vs FGO, registered direction plus
descriptive ratios): S-E5.5 (live), S-E5.6 (hindsight: RTS vs the FGO's iSAM2 hindsight).

**Extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22).** Verdicts were judged on
the unrounded json values, 3/3 completed runs, all gates passed. Full page: `e5_results.md`.

| criterion | verdict | count | source |
|---|---|---|---|
| **H-E5.1 (PRIMARY)**: UKF-LC live lap-5 ≤ 1.5 × lap-1 | **PASS** | 3/3 | `json:scores/e5_verdicts.json:criteria.H-E5.1` |
| H-E5.2: UKF-LC live < UKF-no-LC live | **PASS** | 3/3 | `json:scores/e5_verdicts.json:criteria.H-E5.2` |
| H-E5.3: UKF-LC RTS < UKF-no-LC RTS | **PASS** | 3/3 | `json:scores/e5_verdicts.json:criteria.H-E5.3` |
| P-E5.4: UKF-no-LC live lap-5 > 1.5 × lap-1 | **PASS** | 3/3 | `json:scores/e5_verdicts.json:criteria.P-E5.4` |
| S-E5.5 (secondary, direction): UKF-LC live > stored FGO-LC live | **PASS** (direction held) | 3/3 | `json:scores/e5_verdicts.json:criteria.S-E5.5`; FGO from `json:eval/results/expL/T_A_r<i>_t245.json:tracks.lc live.rmse_m` |
| S-E5.6 (secondary, direction): UKF-LC RTS > stored FGO-LC hindsight. The FGO side is the iSAM2 full estimate after 5 extra updates (DEVIATION, M:10557), not an LM batch | **PASS** (direction held) | 3/3 | `json:scores/e5_verdicts.json:criteria.S-E5.6`; FGO from `json:eval/results/expL/T_A_r<i>_t245.json:tracks.lc hindsight.rmse_m` |

The stored FGO values sit under `eval/results/expL/` (frozen, guard-covered). `e5_verdicts.json` records each one
with that source key, so every comparison input is cited from `scores/`.

## NOT RUN at the lock (counted separately; future work)

| run | experiment | reason |
|---|---|---|

## Deviations

| date | deviation | affected | recorded before reading results? |
|---|---|---|---|
| 2026-10-22 | Jobs were not queued through `eval/run_jobs_resumable.sh <jobs> tier1_<exp> 1` (§8). That runner writes under `~/thesis_data/batches/`, which the guard's `batches` group covers, so `verify` would report ADDED (STOP). Instead a serial `heavy.py` driver ran one job at a time, with its state under `~/thesis_data/tier1/<stage>/` (`stage2a/`, `stage2c/`). The thread variables were at 1 (TBB included). `heavy.py` runs at nice 19, not the frozen jobs' nice 10; nice affects scheduling only, never the arithmetic. Mechanism only; the pre-registered intent (serial, single-threaded) is kept. | Stage 2a gates; Stage 2c (V-E5a/b/c and the E5 result runs) | yes: Stage 2a recorded it in `stage2_gates.md` §2 before its gates were read; this row was written on 2026-10-22 before the first V-E5 or E5 run was started |
| 2026-10-22 | Stage 2d (E2): the same mechanism as Stage 2a/2c. A serial driver `~/thesis_data/tier1/stage2d/driver.sh` runs one `heavy.py` job at a time (nice 19, not nice 10; thread variables at 1, TBB included), each wrapped in `timeout 21600` (6 h; a timeout stops the driver and is reported, never auto-re-run), not `eval/run_jobs_resumable.sh`. Score files are named `scores/E2_<trial>.json` exactly as §1 of the pre-registration states (the stage brief wrote `e2_*`); the scorer is run with `~/venv-tags/bin/python` as §1 states. Verdicts are computed by `stage2d/e2_verdicts.py` into `scores/E2_verdicts.json`. Mechanism and naming only; the pre-registered configuration, flags and scorer are unchanged. | E2 (all 18 runs and their scores) | yes: written on 2026-10-22 before the first E2 run was started |
| 2026-10-22 | Stage 2e (E3 arms (a) and (b)): the same mechanism as Stage 2a/2c/2d. A serial driver `~/thesis_data/tier1/stage2e/driver.sh` runs one `heavy.py --wait-s 1800` job at a time (nice 19, not nice 10; thread variables at 1, TBB included), each wrapped in `timeout 21600` (6 h; a timeout or any non-zero rc stops the driver and is reported, never auto-re-run), not `eval/run_jobs_resumable.sh`. Order: arm (a) 18 runs (T_A_r1..r3 × rate 0.01, 0.05 × seed 0, 1, 2), then arm (b) 21 runs (the 3 rate-0 controls, then the 18 mislabelled runs in the same order). Arm (a) has no rate-0 run: §2 makes the clean reference the stored Experiment 3 LC result. **Score file names:** §2.2 fixes `E3a_<trial>_<rate>_s<seed>.json`; `<rate>` is written as in the run suffix (`%g`: `0.01`, `0.05`). §2.4 names no arm (b) files; they are `scores/E3b_<trial>_<rate>_s<seed>.json` and, for the rate-0 control, `scores/E3b_<trial>_0.json`. Scorer: `~/venv-tags/bin/python eval/l_score.py` with `--suffix _t245<run_suffix>` (arm (b) control: `_t245_tags0-1-2-3-4-5-6-7_robcauchy2.385`, no `--mislabel-*` flags, as §2.4 states). Verdicts by `stage2e/e3_verdicts.py` into `scores/E3_verdicts.json`. **Effective rates:** reported exactly as §2.1 defines them from `stats.json:tier1.mislabel` (`n_mislabelled / n_eligible_non_gauge` and `n_mislabelled / n_calls`, per run and pooled over the 9 runs of a rate). These counters cover the WHOLE bag (every central detection that passes the filter, including those before the anchor and after the 245 s cut). As an added DESCRIPTIVE covariate only (not replacing the ruled rates), the injections with t in [t_anchor, t_anchor + 245 s] are also counted from `events_t_true_new`. Mechanism, naming and an extra descriptive count only; the pre-registered configuration, flags, scorer and decision rules are unchanged. | E3 (all 39 runs, their scores and verdicts) | yes: written on 2026-10-22 before the first E3 run was started |
| 2026-10-22 (written 14:31 AEDT, after E3 run 1 of 39 finished and while run 2 ran; before any 5% run) | Stage 2e: the per-job hang guard was raised from `timeout 21600` (6 h) to `timeout 86400` (24 h) in the 37 job scripts not yet started (`stage2e/jobs/*.sh`; runs 1 `e3a_T_A_r1_0.01_s0` and 2 `e3a_T_A_r1_0.01_s1` keep 6 h). Reason: run 1 took 3,091 s of driver wall time (`stage2e/timing.tsv`; clean G0-L 127 s). The 5% runs carry about 5× the wrong factors and could plausibly approach 6 h; a run killed by the guard 13 days before the lock would be none of §0.5's statuses (completed, crashed, NOT RUN). 24 h is a hang guard only, well above any projected run; the 2026-11-04 23:59 AEDT lock rule is unchanged. `driver.sh` was not edited. Mechanism only; flags, configuration, scorer and decision rules are unchanged. This row was written uncommitted, and is committed with the stage, so that every E3 run records the same commit (`cb713d3`; `lc_fgo_replay.py` reads `HEAD` at the end of a run). | E3 runs 3–39 (job wrapper only) | yes: written before any 5% run started and before any E3 score was computed |
| 2026-10-22 (after 6 of 39 E3 runs; before any E3 score) | Stage 2e, user ruling R4: the remaining 32 E3 runs run as a **parallel batch at width ≤ 4 inside ONE `heavy.py` call** (`heavy.py --wait-s 1800 "tier1 stage2e E3 parallel batch" -- bash ~/thesis_data/tier1/stage2e/par_batch.sh 4`), not one `heavy.py` call per job as in the serial driver row above. One BUILD_LOCK therefore spans the whole batch, and `xargs -P 4` runs `stage2e/one_job.sh` once per entry of `stage2e/par_order.txt`. Each job is still single-threaded (thread variables at 1, TBB included), nice 19, `timeout 86400`. `one_job.sh` refuses to start a job while a flight is on (FLIGHT_LOCK, arducopter, gz sim; exit 75, re-queued by hand). On rc ≠ 0 it gives the one identical re-run of §0.5, after moving the crashed output aside to `<dir>.CRASHED_try1`. Timing goes to `stage2e/par_timing.tsv` and status (`run_status.py`) to `stage2e/par_status.tsv`. **Consequence:** the per-run `wall_s` and every runtime ratio from these runs are measured under co-load and are **not like for like** (§2.4's "both are serial runs" no longer holds for them). They are reported, labelled so; only the serial 0% pair (next row) is the headline runtime ratio. Mechanism and timing only; flags, configuration, scorer and decision rules are unchanged. | E3: the 32 batch runs (arm (a) T_A_r2 and T_A_r3; arm (b) all except `e3b_T_A_r2_0`), their `wall_s` and the descriptive runtime ratios | yes: written before the batch was launched and before any E3 score |
| 2026-10-22 (same time) | Stage 2e, user ruling R3: the serial runtime pair is **T_A_r2 at rate 0**, not the proposed T_A_r2 1% s0 pair. `stage2e/serial_pair.sh` runs, inside one `heavy.py` call and with nothing else running, (1) an **extra, timing-only arm (a) run** `e3a_T_A_r2_0` = `lc_fgo_replay.py T_A_r2 --mode lc --t-max 245 --tag-ids 0,1,2,3,4,5,6,7 --out-root ~/thesis_data/tier1`, output `~/thesis_data/tier1/T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7/` (the arm (b) control command without `--tag-robust`; `--tag-ids 0..7` is a no-op on T_A, shown byte-identical by G0-L (ii); the tier-1 path guard refuses any output under `~/thesis_data/trials/` or an existing non-empty directory), then (2) the registered control `e3b_T_A_r2_0`. The extra run is not scored and enters no criterion. Its `live.tum` and `hindsight.tum` are compared (`cmp -s`) with the stored Experiment 3 `trials/T_A_r2/lc_fgo_lc_t245/`, and the result is reported. The headline runtime ratio is `e3b_T_A_r2_0` `wall_s` ÷ `e3a_T_A_r2_0` `wall_s`, DESCRIPTIVE. `e3a_T_A_r2_0.01_s0` and `e3b_T_A_r2_0.01_s0` move into the parallel batch. Every E3 run from now on records the commit that adds this row; runs 1–6 recorded `cb713d3`. | E3 runtime ratio (descriptive); one extra timing-only run | yes: written before the pair was launched |
| 2026-10-22 (same time) | Stage 2e, user ruling R2 (terminology clarification, `preregistration.md` §2.3): `stage2e/e3_verdicts.py` now reads each run's `stage2e/status/<job>.json` (FAILED-ESTIMATOR iff `keyframe_failures` > 0 or a non-finite .tum value). A diverged run counts as **not satisfying** any criterion that needs it (FAIL, never NOT MET): H-E3.1–H-E3.3, P-E3.4, P-E3.5, P-E3.6 (a flight with any diverged arm (a) run fails) and P-E3b.1 / P-E3b.2 (P-E3b.1 read literally: it also fails when the matched arm (a) run diverged; SUPERSEDED by the user ruling of 2026-10-23, next row). Verdicts carry "k of 3 runs diverged" per flight, with the live divergence onset (headline), first exception time and failure fraction (inflated: no recovery after a throw). `crosscheck.py` re-derives the status independently from `stats.json` and the .tum files. A ruling applied before scoring, not a change of criteria or bands. | E3 verdicts (all criteria) | yes: before any E3 score was computed |
| 2026-10-23 (during the parallel batch, 24 of 39 E3 runs finished; before any E3 score) | Stage 2e, user ruling on P-E3b.1 (clarification of R2; `preregistration.md` §2.3, METHODOLOGY): if the matched arm (a) run diverged and the robust arm (b) run did not, that P-E3b.1 run counts as SATISFIED, flagged, reported as "(a) diverged at t s, (b) OK" with no (b)/(a) ratio (arm (a)'s error is not finite). A diverged arm (b) run still fails. `stage2e/e3_verdicts.py`, `crosscheck.py` and `make_tables.py` were updated (no running job uses them) and re-tested on the mock tree. | E3 P-E3b.1 (both rates) | yes: before any E3 score was computed |
