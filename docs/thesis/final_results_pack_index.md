# Final results pack: index (2026-10-11)

PDF: `docs/thesis/final_results_pack.pdf`. Figures: `plots/final_results_pack/`. Built by `eval/figs_final_pack.py` at commit `e6d9f74` (run with `~/venv-evo/bin/python`; analysis only, no replays). Tables: T1 from `docs/thesis/headline_claims_before_after.md`, T2 from `docs/thesis/final_results_pack_corrections.md`.

**Status key:** CURRENT = regenerated from the restated results and every check matches numbers.md / METHODOLOGY; FLAGGED = shows superseded values or a check mismatches (reason given); NOT REGENERATED = kept as is, reason given.

## Pack contents

| id | figure / table | status | source (script; inputs) | numbers.md rows supported | checks |
|---|---|---|---|---|---|
| F01 | `plots/final_results_pack/F01_closed_loop_paths_full.png`: Closed-loop true paths at full speed: EKF3 and UKF, with and without the camera heading | CURRENT | `eval/figs_final_pack.py`; paths: dataflash SIM of cl_a_tex, cl_bcpp_tex_r1–r3, cl_ukf_a_tex, cl_ukf_b_tex_r1–r3; contact times and B2: eval/results/closed_loop_<trial>.json | §15: no-heading contact EKF3/UKF full; with-heading flights passing; B2 max cross-track | 5/5 |
| F02 | `plots/final_results_pack/F02_closed_loop_heading_error_full.png`: Closed-loop heading error at full speed, with and without the camera heading | CURRENT | `eval/figs_final_pack.py`; curves: dataflash XKF1 / XUKO / SIM of the F01 trials; p95 and max: eval/results/closed_loop_<trial>.json (B3) | §15: B3 yaw-error p95 / max (EKF3 full C++, UKF full) | 2/2 |
| F03 | `plots/final_results_pack/F03_offline_textured_no_heading.png`: Offline accuracy, textured floor, no heading; the confirmatory EKF3 − FGO test | CURRENT | `eval/figs_final_pack.py`; eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json | §6.1 (r1–r3 values, means, medians, confirmatory test, standing row); claims 1a, 1b, 2 | 9/9 |
| F04 | `plots/final_results_pack/F04_offline_with_heading_C0.png`: Offline with the camera heading: FGO against UKF (C0) | CURRENT | `eval/figs_final_pack.py`; eval/results/phase4_fwdc_evo.json, phase4_fwdplainc_evo.json (UKF_heading, FGO_heading, EKF3); cross-checked against phase4_*_arms.json | §6.4 (EKF3 fwdc/fwdplainc); §6.6 (heading arms, C0, yaw RMS, conditional plain-wall benefit, NEES); claims 5, 6, 7, 9 | 7/7 |
| F05 | `plots/final_results_pack/F05_drift_decomposition.png`: Heading-driven against residual cross-track, with and without the camera heading | CURRENT (JSON only, unchecked) | `eval/figs_final_pack.py`; eval/results/phase5_analysis.json (decomposition: xtrack_head_m, xtrack_resid_m) | none (METHODOLOGY Phase 5 only; numbers.md §6.3 'not recomputed' note) | 0/0 |
| F06 | `plots/final_results_pack/F06_blank_flow_loss.png`: Loss of flow aiding on the blank floor | CURRENT | `eval/figs_final_pack.py`; eval/results/blank_behaviour.json (along_m, cross_m at +10/+30/+60/+120 s; EKF3 validity) | §6.2 (+10/+30/+60 s rows, end-of-cruise †, EKF3 invalid); claim 10 | 3/3 |
| F07 | `plots/final_results_pack/F07_f1_robust_tradeoff.png`: F1: robust heading weighting trade-off | CURRENT | `eval/figs_final_pack.py`; eval/results/f1_test.json | §15.2 F1 row; claim 27 | 4/4 |
| F08 | `plots/final_results_pack/F08_closed_loop_paths_half.png`: Closed-loop true paths at half speed: EKF3, UKF (original and v2), FGO (original, v3, robust) | CURRENT | `eval/figs_final_pack.py`; paths: dataflash SIM of the trials named in each panel title (cl_*_half, *_v2, *_v3); contact and B2: eval/results/closed_loop_<trial>.json | §15 rows (contact EKF3/UKF/FGO/FGO v3 half; B2); METHODOLOGY re-flight sections (UKF v2, FGO v3: no numbers.md row); claim 14 | 4/4 |
| F09 | `plots/final_results_pack/F09_T_hindsight_gain_vs_gap.png`: T: the hindsight gain grows with the gap for the FGO, not for the single-pass RTS-UKF | CURRENT | `eval/figs_final_pack.py`; eval/results/expT/T_*.json (gaps), t_aggregate.json | §16.1 (H-T1, P-T2); claim 17 | 3/3 |
| F10 | `plots/final_results_pack/F10_T_rmse_by_condition.png`: T: horizontal error by tag density, live and hindsight | CURRENT | `eval/figs_final_pack.py`; eval/results/expT/T_*.json (tracks.*.horiz_err_m.rmse); t_aggregate.json (means) | §16.1 table, P-T3, P-T4, condition D bullet; claims 17, 18 | 4/4 |
| F11 | `plots/final_results_pack/F11_O_indoor_hindsight.png`: O: indoor error with GNSS outside only; hindsight reconstruction and EKF3's return jump | CURRENT | `eval/figs_final_pack.py`; eval/results/expO/O_*.json; curves: O_r1 room_ukf/, room_fgo/ TUMs (FGO-only re-run outputs), dataflash XKF1 about EKF3's origin (gnss.npz), bag /imu/time_ref (clock map) | §16.2 table and bullets (H-O1, H-O2, P-O3, WITHDRAWN, partial attribution); §18; claims 19–22 | 8/8 |
| F12 | `plots/final_results_pack/F12_L_lap_by_lap.png`: L: tag re-identification bounds the drift lap by lap | CURRENT | `eval/figs_final_pack.py`; eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m) | §16.3 table and bullets; claims 23, 24 | 5/5 |
| F13 | `plots/final_results_pack/F13_L_compute_cost.png`: L: per-update solve time and wall time (diagnostic) | FLAGGED (check mismatch) | `eval/figs_final_pack.py`; ~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/stats.json (mtime 2026-10-10 19:00–21:35) | §16.3 'Computational cost' bullets (DIAGNOSTIC) | 0/3 |
| F14 | `plots/final_results_pack/F14_H_tag_loss_drift.png`: H: hold error and tag-loss drift per loss duration, EKF3 / UKF / FGO, shadow and flying | CURRENT | `eval/figs_final_pack.py`; eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s2_r*.json, s3v2_r*.json, s3_r*.json (losses[*].<est>.effective.drift_m, drift_end_m; hold_windows_vehicle) | §17 (S1 table; tag-loss drift table; P-H5, P-H7; ruling 6 note); claims 25, 26; METHODOLOGY S2/S3 and RE-FLY sections (no numbers.md rows) | 9/9 |
| F15a | `plots/final_results_pack/F15a_closed_loop_summary_corridor.png`: Closed-loop summary (1/2): corridor sets, every flown build | CURRENT | `eval/figs_final_pack.py`; eval/results/closed_loop_<trial>.json for cl_a_tex, cl_b_tex_r*, cl_bcpp_tex_r*(_half), cl_a_tex_half, cl_ukf_a_tex(_half)(_v2), cl_ukf_b_tex_r*(_half)(_v2), cl_fgo_a_tex_half(_v2)(_v3), cl_fgo_b_tex_r*_half(_v2)(_v3), cl_fgo_b_robust_tex_r*_half | §15 rows (contacts, B1–B5 counts, B2, B3); claim 14; METHODOLOGY re-flight sections | 5/5 |
| F15b | `plots/final_results_pack/F15b_closed_loop_summary_H_safety.png`: Closed-loop summary (2/2): H hold sets and the safety tests | CURRENT | `eval/figs_final_pack.py`; eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json; expH/safety_*.json | §17 (S1); claim 25; METHODOLOGY H S2/S3, safety RESULT sections | 4/4 |
| T1 | Headline claims before/after (36 rows) | CURRENT | rendered by `eval/figs_final_pack.py` from `docs/thesis/headline_claims_before_after.md` | all rows cited in its evidence column | 2/2 |
| T2 | Corrections summary (18 rows) | CURRENT | `docs/thesis/final_results_pack_corrections.md` (quotes METHODOLOGY, numbers.md, eval/results) | §6.1, §6.5, §6.6, §15, §16.2, §17, §18 | 1/1 |

## FLAGGED items

- **F05** (CURRENT (JSON only, unchecked)): . No numbers.md row: CURRENT against its JSON only.
- **F13** (FLAGGED (check mismatch)): L LC median (ms): computed `35–41`, expected `36–41` (numbers.md §16.3 (first final re-run)); L no-LC median (ms): computed `50–61`, expected `47–54` (numbers.md §16.3 (first final re-run)); L no-LC wall (s): computed `7276–9583`, expected `9868–11175` (numbers.md §16.3 (first final re-run)). Check mismatch is a numbers.md staleness (first final re-run vs FGO-only re-run), not a plotting error.
- **numbers.md §15 is behind METHODOLOGY:** it lists the ORIGINAL UKF half-speed heading set (2/3, r3 B4) and has no rows for the UKF v2 no-heading contact (+165.9 s) or the UKF v2 / FGO v2 / FGO v3 heading sets (all 3/3). F08 and F15a show both; numbers.md was not edited (out of scope).
- **Experiment H comparative criteria (H-H2, P-H3, H-H4) were adjudicated on S2/S3 (old builds) and NOT restated on S2v2/S3v2** (METHODOLOGY: "Comparative H-H2/P-H3 are updated in the final restatement"; the restatement draft does not contain them). F14 shows per-flight values without a verdict. S2/S2v2/S3/S3v2, the S1-far shadows and the safety tests have no numbers.md rows.
- **Rounding-boundary transcriptions in numbers.md (not superseded values; ≤ one unit in the last printed digit):** confirmatory d per flight r4–r9: file `-0.359 -0.488 +1.845 -0.498 -0.460 -0.164`, numbers.md `-0.359 -0.489 +1.845 -0.498 -0.460 -0.164`; T A: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m): file `0.039 0.037 0.020 0.014 0.010`, numbers.md `0.039 0.037 0.020 0.014 0.011`; T C: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m): file `0.074 0.076 0.054 0.039 0.019`, numbers.md `0.074 0.076 0.053 0.039 0.019`; L nolc live overall (m): file `0.263–0.361`, numbers.md `0.262–0.361`. Accepted as matches; listed for a later numbers.md tidy.
- **Historical supervisor figures** (below) carry superseded values or captions; they are kept unchanged as meeting records.

## Checks per figure (computed from the result files against the value typed from the cited source)

### F01: Closed-loop true paths at full speed: EKF3 and UKF, with and without the camera heading

| check | computed | expected | source | match |
|---|---|---|---|---|
| EKF3 full no-heading contact (s) | `+186.2` | `+186.2` | numbers.md §15 rows 1–2 | yes |
| UKF full no-heading contact (s) | `+163.0` | `+163.0` | numbers.md §15 rows 1–2 | yes |
| SIM path vs scored B2 (bag GT), max |Δ| over 6 flights <= 0.010 m | `ok` | `ok` | path-source cross-check | yes |
| EKF3 full C++ heading B2 range (m) | `0.23–0.34` | `0.23–0.34` | numbers.md §15 B2 row | yes |
| UKF full heading B2 range (m) | `0.16–0.29` | `0.16–0.29` | numbers.md §15 B2 row | yes |

### F02: Closed-loop heading error at full speed, with and without the camera heading

| check | computed | expected | source | match |
|---|---|---|---|---|
| EKF3 full B3 p95 / max (deg) | `0.28–0.31/0.40–0.42` | `0.28–0.31/0.40–0.42` | numbers.md §15 B3 row | yes |
| UKF full B3 p95 / max (deg) | `0.17–0.21/0.26–0.31` | `0.17–0.21/0.26–0.31` | numbers.md §15 B3 row | yes |

### F03: Offline accuracy, textured floor, no heading; the confirmatory EKF3 − FGO test

| check | computed | expected | source | match |
|---|---|---|---|---|
| EKF3 dsn_tex mean r1–r3 (m) | `4.00` | `4.00` | numbers.md §6.1 / claims 1a | yes |
| EKF3 dsn_tex median r1–r9 (m) | `4.10` | `4.10` | numbers.md §6.1 standing row | yes |
| FGO dsn_tex mean r1–r3 (m) | `3.44` | `3.44` | numbers.md §6.1 / claims 1a | yes |
| FGO dsn_tex median r1–r9 (m) | `4.46` | `4.46` | numbers.md §6.1 standing row | yes |
| UKF dsn_tex mean r1–r3 (m) | `3.59` | `3.59` | numbers.md §6.1 / claims 1a | yes |
| UKF dsn_tex median r1–r9 (m) | `5.13` | `5.13` | numbers.md §6.1 standing row | yes |
| confirmatory verdict | `no ordering claimed` | `no ordering claimed` | numbers.md §6.1 confirmatory row | yes |
| confirmatory mean d, CI (m) | `-0.021 [-0.989, 0.947]` | `-0.021 [-0.989, 0.947]` | numbers.md §6.1 confirmatory row | yes |
| confirmatory d per flight r4–r9 | `-0.359 -0.488 +1.845 -0.498 -0.460 -0.164` | `-0.359 -0.489 +1.845 -0.498 -0.460 -0.164` | numbers.md §6.1 | yes (last-digit rounding) |

### F04: Offline with the camera heading: FGO against UKF (C0)

| check | computed | expected | source | match |
|---|---|---|---|---|
| evo vs arms json agreement (mismatches) | `0` | `0` | phase4_*_evo.json vs phase4_*_arms.json | yes |
| fwdc UKF +heading r1–r3 (m) | `0.13 / 0.13 / 0.14` | `0.13 / 0.13 / 0.14` | numbers.md §6.6 | yes |
| fwdc FGO +heading r1–r3 (m) | `0.06 / 0.06 / 0.06` | `0.06 / 0.06 / 0.06` | numbers.md §6.6 | yes |
| fwdplainc UKF +heading r1–r3 (m) | `0.19 / 0.15 / 0.25` | `0.19 / 0.15 / 0.25` | numbers.md §6.6 | yes |
| fwdplainc FGO +heading r1–r3 (m) | `0.15 / 0.09 / 0.22` | `0.15 / 0.09 / 0.22` | numbers.md §6.6 | yes |
| C0: FGO lower than UKF | `6/6` | `6/6` | numbers.md §6.6 C0 row; claim 7 | yes |
| EKF3 no-heading fwdc / fwdplainc r1–r3 (m) | `4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08` | `4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08` | numbers.md §6.4 | yes |

### F05: Heading-driven against residual cross-track, with and without the camera heading

| check | computed | expected | source | match |
|---|---|---|---|---|

### F06: Loss of flow aiding on the blank floor

| check | computed | expected | source | match |
|---|---|---|---|---|
| UKF +10/+30/+60 s ranges (m) | `6.4–8.2 / 27.3–36.5 / 60–108` | `6.4–8.2 / 27.3–36.5 / 60–108` | numbers.md §6.2 | yes |
| FGO +10/+30/+60 s ranges (m) | `6.4–8.2 / 28.0–37.0 / 154–204` | `6.4–8.2 / 28.0–37.0 / 154–204` | numbers.md §6.2 | yes |
| n flights | `11/11` | `11/11` | numbers.md §6.2 | yes |

### F07: F1: robust heading weighting trade-off

| check | computed | expected | source | match |
|---|---|---|---|---|
| F1 robust lower yaw max on | `6/6` | `6/6` | numbers.md §15.2 F1 row | yes |
| F1 lockouts FGO_robust = UKF_hard | `{"FGO_robust": 3, "UKF_hard": 3}` | `{"FGO_robust": 3, "UKF_hard": 3}` | numbers.md §15.2 F1 row | yes |
| F1 verdict robust_FGO_better | `False` | `False` | numbers.md §15.2: NOT met (lockout tie) | yes |
| FGO_hard plain-wall yaw max (deg) | `4.59–5.03` | `4.59–5.03` | numbers.md §15.2 F1 row | yes |

### F08: Closed-loop true paths at half speed: EKF3, UKF (original and v2), FGO (original, v3, robust)

| check | computed | expected | source | match |
|---|---|---|---|---|
| contacts EKF3 / UKF / UKF v2 / FGO / FGO v3 (s) | `+242.1 / +198.0 / +165.9 / +165.8 / +169.9` | `+242.1 / +198.0 / +165.9 / +165.8 / +169.9` | numbers.md §15 (EKF3, UKF, FGO, FGO v3); METHODOLOGY (UKF v2) | yes |
| UKF v2 heading B2 (m) | `0.231 / 0.253 / 0.219` | `0.231 / 0.253 / 0.219` | METHODOLOGY 'UKF heading set RE-FLOWN' | yes |
| FGO v3 heading B2 (m) | `0.118 / 0.033 / 0.392` | `0.118 / 0.033 / 0.392` | METHODOLOGY 'FGO heading set RE-FLOWN' (r3 B1/B2 0.392) | yes |
| EKF3 half / UKF orig / FGO hard / FGO robust B2 range (m) | `0.24–0.33 ; 0.13–0.53 ; 0.06–0.25 ; 0.05–0.14` | `0.24–0.33 ; 0.13–0.53 ; 0.06–0.25 ; 0.05–0.14` | numbers.md §15 B2 row | yes |

### F09: T: the hindsight gain grows with the gap for the FGO, not for the single-pass RTS-UKF

| check | computed | expected | source | match |
|---|---|---|---|---|
| H-T1 median gain A–D (m) | `0.010 / 0.011 / 0.023 / 0.052` | `0.010 / 0.011 / 0.023 / 0.052` | numbers.md §16.1 | yes |
| H-T1 rho, p, PASS | `+0.30 6e-06 True` | `+0.30 6e-06 True` | numbers.md §16.1 | yes |
| P-T2 gain A–D (m), PASS | `+0.020 / +0.032 / +0.037 / +0.029 False` | `+0.020 / +0.032 / +0.037 / +0.029 False` | numbers.md §16.1 | yes |

### F10: T: horizontal error by tag density, live and hindsight

| check | computed | expected | source | match |
|---|---|---|---|---|
| T A: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m) | `0.039 0.037 0.020 0.014 0.010` | `0.039 0.037 0.020 0.014 0.011` | numbers.md §16.1 table | yes (last-digit rounding) |
| T B: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m) | `0.055 0.061 0.026 0.031 0.015` | `0.055 0.061 0.026 0.031 0.015` | numbers.md §16.1 table | yes |
| T C: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m) | `0.074 0.076 0.054 0.039 0.019` | `0.074 0.076 0.053 0.039 0.019` | numbers.md §16.1 table | yes (last-digit rounding) |
| T D: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m) | `0.096 0.131 0.083 0.109 0.028` | `0.096 0.131 0.083 0.109 0.028` | numbers.md §16.1 table | yes |

### F11: O: indoor error with GNSS outside only; hindsight reconstruction and EKF3's return jump

| check | computed | expected | source | match |
|---|---|---|---|---|
| O indoor RMSE EKF3 live (m) | `1.42–1.43` | `1.42–1.43` | numbers.md §16.2 table | yes |
| O indoor RMSE UKF live (m) | `0.77–0.84` | `0.77–0.84` | numbers.md §16.2 table | yes |
| O indoor RMSE FGO live (m) | `0.83–0.89` | `0.83–0.89` | numbers.md §16.2 table | yes |
| O indoor RMSE RTS-UKF (hindsight) (m) | `0.58–0.60` | `0.58–0.60` | numbers.md §16.2 table | yes |
| O indoor RMSE FGO batch (hindsight) (m) | `0.59–0.59` | `0.59–0.59` | numbers.md §16.2 table | yes |
| O cap-free RTS-UKF (m) | `0.60–0.62` | `0.60–0.62` | numbers.md §16.2 | yes |
| O EKF3 reset jump (m) | `4.10–4.10` | `4.10–4.10` | numbers.md §16.2 ('4.10 m, every flight') | yes |
| O_r1 curve indoor RMSE recomputed vs json, max |Δ| <= 0.05 m | `ok` | `ok` | curve source vs scorer | yes |

### F12: L: tag re-identification bounds the drift lap by lap

| check | computed | expected | source | match |
|---|---|---|---|---|
| L lc live overall (m) | `0.049–0.076` | `0.049–0.076` | numbers.md §16.3 | yes |
| L lc hindsight overall (m) | `0.017–0.027` | `0.017–0.027` | numbers.md §16.3 | yes |
| L nolc live overall (m) | `0.263–0.361` | `0.262–0.361` | numbers.md §16.3 | yes (last-digit rounding) |
| L nolc hindsight overall (m) | `0.221–0.266` | `0.221–0.266` | numbers.md §16.3 | yes |
| L lap5/lap1 lc live; nolc live | `0.16–0.43; 2.9–4.5` | `0.16–0.43; 2.9–4.5` | numbers.md §16.3 | yes |

### F13: L: per-update solve time and wall time (diagnostic)

| check | computed | expected | source | match |
|---|---|---|---|---|
| L LC median (ms) | `35–41` | `36–41` | numbers.md §16.3 (first final re-run) | **NO** |
| L no-LC median (ms) | `50–61` | `47–54` | numbers.md §16.3 (first final re-run) | **NO** |
| L no-LC wall (s) | `7276–9583` | `9868–11175` | numbers.md §16.3 (first final re-run) | **NO** |

### F14: H: hold error and tag-loss drift per loss duration, EKF3 / UKF / FGO, shadow and flying

| check | computed | expected | source | match |
|---|---|---|---|---|
| S1 EKF3 flying drift 5/15/30/move (mm, effective) | `13–27 | 6–25 | 3–11 | 7–31` | `13–27 | 6–25 | 3–11 | 7–31` | numbers.md §17 table | yes |
| S1 UKF shadow drift 5/15/30/move (mm, effective) | `11–19 | 5–22 | 4–9 | 8–19` | `11–19 | 5–22 | 4–9 | 8–19` | numbers.md §17 table | yes |
| S1 FGO shadow drift 5/15/30/move (mm, effective) | `9–18 | 4–20 | 1–8 | 0.5–8` | `9–18 | 4–20 | 1–8 | 0.5–8` | numbers.md §17 table | yes |
| S1 hold mean / max (mm) | `8 / 16–25` | `8 / 16–25` | numbers.md §17 S1 table | yes |
| S2v2 flying end-of-loss drift r1/r2/r3 (mm) | `5/7/8 | 19/7/26 | 6/10/10 | 26/4/5` | `5/7/8 | 19/7/26 | 6/10/10 | 26/4/5` | METHODOLOGY S2/S3 RE-FLY sections | yes |
| S3v2 flying end-of-loss drift r1/r2/r3 (mm) | `13/20/17 | 7/25/27 | 22/15/9 | 17/11/18` | `13/20/17 | 7/25/27 | 22/15/9 | 17/11/18` | METHODOLOGY S2/S3 RE-FLY sections | yes |
| S2v2 hold mean / max (mm) | `6.1–7.4 / 17–21` | `6.1–7.4 / 17–21` | METHODOLOGY S2 RE-FLY | yes |
| S3v2 hold mean / max (mm) | `8.1–9.0 / 18–28` | `8.1–9.0 / 18–28` | METHODOLOGY S3 RE-FLY | yes |
| lockouts in any loss | `0` | `0` | numbers.md §17 (P-H7 PASS); METHODOLOGY S2v2/S3v2 | yes |

### F15a: Closed-loop summary (1/2): corridor sets, every flown build

| check | computed | expected | source | match |
|---|---|---|---|---|
| EKF3 half contact MISS | `MISS` | `MISS` | numbers.md §15 (D21) | yes |
| UKF half orig heading pass | `2/3` | `2/3` | numbers.md §15 (r3 B4) | yes |
| UKF v2 / FGO v3 heading pass | `3/3 / 3/3` | `3/3 / 3/3` | METHODOLOGY re-flight sections | yes |
| FGO hard / robust heading pass (D28) | `3/3 / 3/3` | `3/3 / 3/3` | numbers.md §15 (D28) | yes |
| EKF3 full C++ / half heading pass | `3/3 / 3/3` | `3/3 / 3/3` | numbers.md §15 | yes |

### F15b: Closed-loop summary (2/2): H hold sets and the safety tests

| check | computed | expected | source | match |
|---|---|---|---|---|
| UKF (b) v2 S-A2 fails as worded | `False` | `False` | METHODOLOGY 'UKF safety (b) RE-TEST' | yes |
| UKF (b) v2 S-A2 delay (s) | `5.75` | `5.75` | METHODOLOGY | yes |
| FGO a_v3 / b_v3 / UKF a_v2 all S-A pass | `True` | `True` | METHODOLOGY RESULT sections | yes |
| S2v2 / S3v2 lockouts | `0 / 0` | `0 / 0` | METHODOLOGY | yes |

### T1: claims table

| check | computed | expected | source | match |
|---|---|---|---|---|
| claims table row count | `36` | `36` | headline_claims_before_after.md 'Counts' line | yes |
| claims HOLDS / CHANGED / WITHDRAWN | `17 / 16 / 3` | `17 / 16 / 3` | headline_claims 'Counts' line | yes |

### T2: corrections table

| check | computed | expected | source | match |
|---|---|---|---|---|
| corrections listed | `18` | `18` | final_results_pack_corrections.md | yes |

## Historical figures (not in the pack)

| file | replaced by | status |
|---|---|---|
| `plots/supervisor_2026-10-01/fig1_closed_loop_paths.png` | F01 | CURRENT values (same flights); superseded in the pack by F01 |
| `plots/supervisor_2026-10-01/fig2_closed_loop_heading_error.png` | F02 | CURRENT values (same flights); superseded in the pack by F02 |
| `plots/supervisor_2026-10-01/fig3_offline_textured_no_heading.png` | F03 | FLAGGED-superseded: 'confirmed EKF3 < FGO' (WITHDRAWN), UKF median 5.34, pre-final values |
| `plots/supervisor_2026-10-01/fig4_offline_with_heading_C0.png` | F04 | FLAGGED-superseded: pre-final heading-arm values; 'UKF lower yaw error 5/6' |
| `plots/supervisor_2026-10-01/fig5_drift_decomposition.png` | F05 | FLAGGED-superseded: pre-final decomposition |
| `plots/supervisor_2026-10-01/fig6_blank_flow_loss.png` | F06 | FLAGGED-superseded: pre-final runaway curves |
| `plots/supervisor_2026-10-01/fig7_corrections_table.png` | T2 | FLAGGED-superseded: stops at D15/D27; 'confirmatory −0.69 [−1.16, −0.21]' WITHDRAWN |
| `plots/supervisor_2026-10-01/fig8_f1_robust_tradeoff.png` | F07 | FLAGGED-superseded: 'UKF lower worst-case yaw on all 6' |
| `plots/supervisor_2026-10-01/fig9_closed_loop_summary.png` | F15a | FLAGGED-superseded: lacks the v2/v3 re-flights; '~5x per-heading weight' (claim 15 CHANGED) |
| `plots/supervisor_2026-10-01/fig10_closed_loop_paths_half.png` | F08 | FLAGGED-superseded: lacks the UKF v2 / FGO v3 re-flights |
| `plots/supervisor_2026-10-08/fig11_T_hindsight_gain_vs_gap.png` | F09 | FLAGGED-superseded: pre-final FGO values |
| `plots/supervisor_2026-10-08/fig12_T_rmse_by_condition.png` | F10 | FLAGGED-superseded: 'EKF3 lowest live in D' (claim 18 CHANGED), '11–34 mm' |
| `plots/supervisor_2026-10-08/fig13_O_indoor_hindsight.png` | F11 | FLAGGED-superseded: FGO batch '0.33 m', 'P-O3 FAIL', 'cap-free 0.97 m' |
| `plots/supervisor_2026-10-08/fig14_L_lap_by_lap.png` | F12 | FLAGGED-superseded: '4.5–5.5×', pre-final L values |
| `plots/supervisor_2026-10-08/fig15_L_compute_cost.png` | F13 | NOT REGENERATED: per-1000-keyframe logs (eval/results/expL/logs/, 2026-10-08) pre-date the final re-runs; replaced by the per-replay summary F13 |
| `plots/supervisor_2026-10-0{1,8}/figures.pdf` | this PDF | FLAGGED-superseded as a set (historical record of the supervisor meetings; kept unchanged) |
| `plots/*.png (top level: ate_by_condition, nomag_*, textured_*, ekf3_diag_*, ukf_diag_*, alongtrack_vs_travel, pn_vs_truey, ekf3_diag_4_flowresid_tilt; last committed 2026-08-01), plots/lateral_diag/ (2026-09-23), plots/phase5/ (2026-09-29)` | — | NOT REGENERATED, FLAGGED-superseded: pre-correction diagnostics (before the consolidated re-fly / final re-runs); their estimator values must not be quoted. plots/inlier_ratio_transition.png and the plots/fwd_camera/ frame grids are sensor-level/render records, unaffected |
| `plots/plainwall_trace/, plots/d22_plateau/ (2026-10-10)` | — | NOT REGENERATED, not superseded: recent single-purpose diagnostics (the D18 plain-wall trace cited in numbers.md §6.6/§18; the D22 plateau diagnostic). Kept as is |

## Captions

### F01: Closed-loop true paths at full speed: EKF3 and UKF, with and without the camera heading

- **Kind:** CONFIRMATORY (pre-registered closed-loop criteria)
- **Caption:** Simulator-truth paths (top-down) when EKF3 or the UKF is the vehicle's estimator: 0.5 m/s, textured corridor `corridor_textured_fwdc`. Walls are at x = ±10 m; the dotted line is the 9.58 m contact threshold. Without heading, both drift west into the wall: X marks the contact, and the shaded strip is the pre-registered contact window, mapped to distance at 0.5 m/s. With the camera heading, all six flights stay within 0.34 m of the centreline. n = 1 per no-heading flight and n = 3 per heading set; closed-loop run-to-run variability is unmeasured. The full-speed UKF here is the port BEFORE the jitter correction (flown 2026-10-01); it was not re-flown at full speed. The FGO flew at half speed only (F08). Same information within each estimator (heading on against off).
- **Inputs:** paths: dataflash SIM of cl_a_tex, cl_bcpp_tex_r1–r3, cl_ukf_a_tex, cl_ukf_b_tex_r1–r3; contact times and B2: eval/results/closed_loop_<trial>.json
- **Replaces:** plots/supervisor_2026-10-01/fig1_closed_loop_paths.png (same flights; bag GT replaced by dataflash SIM)

### F02: Closed-loop heading error at full speed, with and without the camera heading

- **Kind:** CONFIRMATORY (pre-registered B3 bands)
- **Caption:** Heading error of the flying estimator against simulator truth (EKF3: XKF1; UKF: its current-time output XUKO), from cruise start, on the full-speed closed-loop flights of F01. Left: no heading, drift until wall contact. Right: with the camera heading, bounded well inside the pre-registered B3 bands (p95 ≤ 1.0°, max ≤ 2.0°). The y-scales differ between the columns. Same flights as F01 (UKF = the pre-jitter-correction port).
- **Inputs:** curves: dataflash XKF1 / XUKO / SIM of the F01 trials; p95 and max: eval/results/closed_loop_<trial>.json (B3)
- **Replaces:** plots/supervisor_2026-10-01/fig2_closed_loop_heading_error.png (same flights, same method)

### F03: Offline accuracy, textured floor, no heading; the confirmatory EKF3 − FGO test

- **Kind:** CONFIRMATORY (right panel); DESCRIPTIVE (left)
- **Caption:** Left: evo -a (cruise) per flight for the three estimators on the same open-loop dsn_tex flights (same information). Descriptive only: mean of r1–r3 FGO 3.44 < UKF 3.59 < EKF3 4.00 m (n = 3, driven by the bimodal r2; restatement ruling 5); median of r1–r9 UKF 5.13 > FGO 4.46 > EKF3 4.10 m. Right: the pre-registered paired test on the new flights r4–r10 (d = EKF3 − FGO; r10 is unusable for the FGO and counts against both directions). With the corrected FGO the verdict is "no ordering claimed": the former "EKF3 beats the FGO" (6/7, CI [−1.16, −0.21]) used the mis-specified FGO noise model and is WITHDRAWN (ruling 2, 2026-10-10). It is driven by r6 (FGO 1.27 against EKF3 3.11 m). UKF/FGO after all corrections, including the FGO-only re-run.
- **Inputs:** eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json
- **Replaces:** plots/supervisor_2026-10-01/fig3_offline_textured_no_heading.png (FLAGGED: title says 'confirmed EKF3 < FGO', UKF median 5.34)

### F04: Offline with the camera heading: FGO against UKF (C0)

- **Kind:** DESCRIPTIVE (C0 report)
- **Caption:** Heading arms of the offline UKF and FGO on the same six textured-floor bags with the same camera headings (σ 0.148° / 0.126°, 3σ gate), evo -a (cruise). FGO lower on 6/6: line-textured walls 0.06 against 0.13–0.14 m; plain walls 0.09–0.22 against 0.15–0.25 m (margin 0.03–0.06 m). C0 compares the two estimators; it is not a heading-benefit claim. On the plain-wall bags (checkerboard floor, shaded) the heading failed Phase 3 validation, so NO heading benefit is claimed there: at a 0.1 rad initial yaw σ r3 rises to 5.70 m for both estimators (numbers.md §18). With heading the yaw error is UKF ≈ FGO on both wall types (fwdc 0.07–0.08°; fwdplainc 3.08–3.39° against 3.07–3.41°): the former "UKF about 2× lower yaw error" no longer holds (claim 6). Both estimators are equally over-confident on plain walls (NEES UKF 13.41, FGO 13.95). Open grey circles: EKF3 WITHOUT heading (3.60–4.09 m), shown only as a reference; not a same-information comparison.
- **Inputs:** eval/results/phase4_fwdc_evo.json, phase4_fwdplainc_evo.json (UKF_heading, FGO_heading, EKF3); cross-checked against phase4_*_arms.json
- **Replaces:** plots/supervisor_2026-10-01/fig4_offline_with_heading_C0.png (FLAGGED: values 0.08–0.61 / 0.61–0.94 m; 'UKF lower yaw error 5/6')

### F05: Heading-driven against residual cross-track, with and without the camera heading

- **Kind:** DESCRIPTIVE (Phase 5 analysis)
- **Caption:** Lateral-error decomposition (Phase 5) on fwdc_tex r1–r3 (n = 3 per row): the part of the end-of-cruise cross-track explained by the estimator's own heading error (filled) against the residual (open). Without heading, the heading error drives 3.2–46.1 m of cross-track. With the camera heading the heading-driven part falls to ≤ 0.07 m, leaving mean residuals of UKF 0.13 m and FGO 0.05 m. EKF3 has no offline heading arm (closed loop only). Values from the final re-runs; numbers.md has no Phase 5 decomposition row (§6.3 lists the related residual-partition rows as NOT RESTATED), so this figure is checked against its JSON only.
- **Inputs:** eval/results/phase5_analysis.json (decomposition: xtrack_head_m, xtrack_resid_m)
- **Replaces:** plots/supervisor_2026-10-01/fig5_drift_decomposition.png (FLAGGED: caption values pre-final re-run, e.g. UKF residual 1.78 m)

### F06: Loss of flow aiding on the blank floor

- **Kind:** DESCRIPTIVE
- **Caption:** Position error magnitude after flow is lost on the blank floor, UKF and FGO baselines (thin lines: each of the 11 flights, dsn, p1c, fwdc and fwdplainc blank; thick: median). UKF 6.4–8.2 / 27.3–36.5 / 60–108 m and FGO 6.4–8.2 / 28.0–37.0 / 154–204 m at +10 / +30 / +60 s. EKF3 has no curve: its position is flagged invalid for the whole flight and it outputs the origin, which is not scored. Behaviour under total loss, not accuracy. † From +60 s the curves are runaway magnitudes (end of cruise UKF 29–40 km, FGO 22–41 km): evidence of divergence with its order of magnitude, not precise values (not bit-reproducible across BLAS builds; numbers.md †). The heading does not bound position without flow either (claim 10).
- **Inputs:** eval/results/blank_behaviour.json (along_m, cross_m at +10/+30/+60/+120 s; EKF3 validity)
- **Replaces:** plots/supervisor_2026-10-01/fig6_blank_flow_loss.png (curves pre-final re-run)

### F07: F1: robust heading weighting trade-off

- **Kind:** EXPLORATORY (descriptive bars; pre-registered decision NOT met)
- **Caption:** Same camera headings (σ 0.148° / 0.126°) on the plain-wall bags (whole cruise) and the textured end-wall region (y > 140 m). The pre-registered F1 decision is NOT met (lockout tie; ruling 8): the robust FGO has the lower worst-case yaw on 6/6 bags, but its lockouts equal the UKF's (3 = 3). The hard-gated FGO no longer diverges on plain walls (yaw max 4.59–5.03°, = UKF to 0.01°; was ~180°). Its F1 lockouts rose 14 → 33 but are not part of the rule. 'Rejected' for the robust arm = weight < 0.5 (it still contributes). The textured end-wall 'wrong accepted' rates rest on very few wrong headings.
- **Inputs:** eval/results/f1_test.json
- **Replaces:** plots/supervisor_2026-10-01/fig8_f1_robust_tradeoff.png (FLAGGED: caption 'UKF lower worst-case yaw on all 6')

### F08: Closed-loop true paths at half speed: EKF3, UKF (original and v2), FGO (original, v3, robust)

- **Kind:** CONFIRMATORY (pre-registered closed-loop criteria)
- **Caption:** Simulator-truth paths, half-speed textured corridor `corridor_textured_half_fwdc` (cruise 0.5 m/s; walls at x = ±10 m; dotted = 9.58 m contact threshold). Without heading every estimator drifts west into the wall (X = contact; shaded = the pre-registered window). EKF3 reached it after its window (+242.1 s, MISS; D21; no cross-speed comparison is claimed). With the camera heading, every flight shown stays near the centreline. The re-flights: UKF v2 (jitter-corrected port) contact +165.9 s, heading set 3/3 (the original r3 failed B4, D22); FGO v3 (noise fix + gated yaw cap) contact +169.9 s, heading set 3/3 (r3 B4 0.246 m/s, the closest call; D22 recurrence). The FGO v2 (noise fix only) ablation is in F15. ALL flown FGO results used the OLD FGO priors (initial yaw σ 1e-3 rad, roll/pitch 2°); they were not re-flown before the freeze. n = 1 per no-heading flight. Dashed = robust heading weighting (plan step 2(b)).
- **Inputs:** paths: dataflash SIM of the trials named in each panel title (cl_*_half, *_v2, *_v3); contact and B2: eval/results/closed_loop_<trial>.json
- **Replaces:** plots/supervisor_2026-10-01/fig10_closed_loop_paths_half.png (FLAGGED: lacks the UKF v2 and FGO v3 re-flights)

### F09: T: the hindsight gain grows with the gap for the FGO, not for the single-pass RTS-UKF

- **Kind:** CONFIRMATORY (pre-registered H-T1, P-T2)
- **Caption:** Per gap between consecutive tag fixes (12 flights, 213 gaps; dots), the mean live horizontal error minus the mean hindsight error over the gap; diamonds = condition medians (A all 8 tags, B corners, C 2 diagonal, D 1 tag; median gaps 4.3 / 10.1 / 22.0 / 46.3 s). Left: the FGO whole-flight batch against its own fixed-lag live estimate, the pre-registered primary H-T1: medians 0.010 / 0.011 / 0.023 / 0.052 m, strictly increasing, ρ = +0.30, PASS. Right: the RTS-smoothed UKF against the live UKF (P-T2, FAIL): +0.020 / +0.032 / +0.037 / +0.029 m, all positive now but not increasing. Same tag fixes for every estimator. Restated after the FGO-only re-run.
- **Inputs:** eval/results/expT/T_*.json (gaps), t_aggregate.json
- **Replaces:** plots/supervisor_2026-10-08/fig11_T_hindsight_gain_vs_gap.png (pre-final re-run values)

### F10: T: horizontal error by tag density, live and hindsight

- **Kind:** CONFIRMATORY (pre-registered P-T3, P-T4)
- **Caption:** Horizontal RMSE in the world frame (no alignment) over the 5-lap window; 3 repeats per condition (each marker one flight). Filled = live, open = hindsight; marker shape = estimator. The FGO live track is lowest of the live tracks in every condition (in D, 0.083 against EKF3 0.096 m, descriptive only, n = 3; ruling 7). Live max/min ratios 1.97 / 2.36 / 1.42 / 1.58 (P-T3 FAIL). The FGO batch stays at 11–28 mm; batch FGO against RTS-UKF ratios 1.31 / 2.14 / 2.07 / 3.89 (P-T4 FAIL). Log scale.
- **Inputs:** eval/results/expT/T_*.json (tracks.*.horiz_err_m.rmse); t_aggregate.json (means)
- **Replaces:** plots/supervisor_2026-10-08/fig12_T_rmse_by_condition.png (FLAGGED: caption 'EKF3 lowest live with the sparsest (D)', '11–34 mm')

### F11: O: indoor error with GNSS outside only; hindsight reconstruction and EKF3's return jump

- **Kind:** CONFIRMATORY (pre-registered H-O1, H-O2, P-O3)
- **Caption:** Left: horizontal error against time for O_r1, outdoor → indoor (grey, GNSS off, 123 s) → outdoor; world frame, no alignment. The live tracks drift indoors and EKF3 jumps 4.10 m when it resets to GNSS on return. Right: indoor RMSE for all 3 flights (filled = live, open = hindsight). H-O1 PASS 3/3 (the FGO batch is below both filters' live tracks). H-O2 FAIL (live ratio 1.72–1.84×). P-O3 PASS (batch FGO against RTS-UKF 1.01–1.02, cap-free 1.02–1.05; flip accepted, ruling 5). The FGO batch is now 0.59 m (was 0.33 m): the former "FGO batch ~2× better than the RTS-UKF" was largely an artefact of the mis-specified FGO noise model and is WITHDRAWN. Partial attribution (ruled): ~93% noise fix, ~7% yaw cap, +0.03 m interaction. Same GNSS samples for every estimator.
- **Inputs:** eval/results/expO/O_*.json; curves: O_r1 room_ukf/, room_fgo/ TUMs (FGO-only re-run outputs), dataflash XKF1 about EKF3's origin (gnss.npz), bag /imu/time_ref (clock map)
- **Replaces:** plots/supervisor_2026-10-08/fig13_O_indoor_hindsight.png (FLAGGED: '0.33 m', 'P-O3 FAIL', 'cap-free 0.97 m')

### F12: L: tag re-identification bounds the drift lap by lap

- **Kind:** CONFIRMATORY (pre-registered H-L1, H-L2, H-L3, P-L4)
- **Caption:** Keyframe FGO with tags at UNKNOWN positions, T_A_r1–r3 (3 lines per style), RMSE per 6 m lap in the first tag's frame. With loop closure the live error falls after lap 1 (lap 5 ÷ lap 1 0.16–0.43; overall 0.049–0.076 m live, 0.017–0.027 m hindsight). Without it the live error grows 2.9–4.5× over five laps (overall 0.262–0.361 m). H-L1, H-L2, H-L3 and P-L4 PASS 3/3; the magnitudes moved in the FGO-only re-run (initial-uncertainty correction; not attributed individually), the result did not. An FGO capability, not an FGO-against-filter result. V-L is not re-scorable on the corrected FGO (ruling 6, 2026-10-09). Log scale.
- **Inputs:** eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m)
- **Replaces:** plots/supervisor_2026-10-08/fig14_L_lap_by_lap.png (FLAGGED: caption '4.5–5.5×', '0.02–0.04 m')

### F13: L: per-update solve time and wall time (diagnostic)

- **Kind:** DIAGNOSTIC (not a pre-registered metric)
- **Caption:** Per-replay cost of the keyframe FGO (30 Hz keyframes, retained history), T_A_r1–r3, from the CURRENT outputs (FGO-only re-run, 2026-10-10): median solve time LC 35.3–41.3 ms, no-LC 50.2–60.6 ms; no-LC p99 1096–1742 ms; no-LC wall time 7276–9583 s. numbers.md §16.3 quotes the FIRST final re-run (LC 36–41, no-LC 47–54 ms, wall 9,868–11,175 s); the FGO-only re-run values differ (FLAGGED, diagnostic only; results unaffected). Workstation Python with parallel jobs: says nothing about onboard feasibility. Replaces the per-1000-keyframe curve, whose logs pre-date the final re-runs.
- **Inputs:** ~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/stats.json (mtime 2026-10-10 19:00–21:35)
- **Replaces:** plots/supervisor_2026-10-08/fig15_L_compute_cost.png (NOT REGENERATED: its progress logs eval/results/expL/logs/ pre-date the final re-runs)

### F14: H: hold error and tag-loss drift per loss duration, EKF3 / UKF / FGO, shadow and flying

- **Kind:** DESCRIPTIVE (per-flight values; pre-registered bands all PASS)
- **Caption:** Bottom: drift at re-acquisition after each tag loss (5, 15, 30 s in the hover; ~7 s during a move), per flight, in mm, EFFECTIVE metric (from the last fix to the first returning fix; numbers.md §17's metric). Filled = the estimator flying the vehicle: EKF3 in S1 (near spawn, r1–r3) and the S1 far-spawn re-fly (r1, r2, r3b); the UKF port in S2v2 (jitter-corrected); the C++ FGO in S3v2 (noise fix + gated yaw cap; OLD priors). Open = shadow: the UKF and FGO replayed offline on the S1 flights (final re-runs), and EKF3 running passively on the S2v2/S3v2 flights. Faint = earlier builds (S2 old UKF port with jitter; S3 FGO noise fix only), shown as ablations. Every value is inside its pre-registered band (UKF ≤ 100 / 200 / 400 / 300 mm, FGO ≤ 50 / 100 / 200 / 150 mm); no lockout (P-H7 PASS). The shadows now drift at EKF3's scale: "there is no gap between the shadow and the flying estimators" (ruling 6; claim 26). Top: vehicle hold error (window means). The comparative criteria H-H2 / P-H3 / H-H4 were adjudicated on S2/S3 (old builds) and have NOT been restated on S2v2/S3v2; the per-flight values are shown without a verdict. Each estimator flew its own flights: pairing is by run index, not trajectory. METHODOLOGY quotes S2v2/S3v2 with the end-of-loss metric; the two differ by ≤ 5 mm (index cross-check).
- **Inputs:** eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s2_r*.json, s3v2_r*.json, s3_r*.json (losses[*].<est>.effective.drift_m, drift_end_m; hold_windows_vehicle)
- **Replaces:** — (new)

### F15a: Closed-loop summary (1/2): corridor sets, every flown build

- **Kind:** SUMMARY (pre-registered criteria)
- **Caption:** What flew in the textured corridor and how it scored, computed from the closed-loop score files. Original sets and the corrected re-flights are both shown (labelled by build). The UKF v2 set passes 3/3 where the original failed r3 on B4; the FGO v2 (noise fix only) and v3 (final) sets pass 3/3, with the heading excursions of the original (B3 max 1.28–1.88°) gone and a small steady offset (B3 mean 0.19–0.24°). The per-heading weight comparison is CHANGED: FGO ≈ 1.3–1.4 % on the v3 flights, UKF side OPEN, no ratio stated (claim 15).
- **Inputs:** eval/results/closed_loop_<trial>.json for cl_a_tex, cl_b_tex_r*, cl_bcpp_tex_r*(_half), cl_a_tex_half, cl_ukf_a_tex(_half)(_v2), cl_ukf_b_tex_r*(_half)(_v2), cl_fgo_a_tex_half(_v2)(_v3), cl_fgo_b_tex_r*_half(_v2)(_v3), cl_fgo_b_robust_tex_r*_half
- **Replaces:** plots/supervisor_2026-10-01/fig9_closed_loop_summary.png (FLAGGED: lacks the re-flights; caption '~5x per-heading weight' superseded)

### F15b: Closed-loop summary (2/2): H hold sets and the safety tests

- **Kind:** SUMMARY (pre-registered criteria)
- **Caption:** Verdicts: H-H1 PASS on every set; P-H5 and P-H7 PASS; P-H6 FAILS as worded; H-H2, P-H3 and H-H4 FAIL as adjudicated on S2/S3 (old builds) and are NOT restated on S2v2/S3v2. H: per flight set, the vehicle hold error, the effective tag-loss drift over all four losses, the re-lock time after the first returning fix (negative for the UKF: event-time stamping) and lockouts, computed from the H score files. Safety: the final run of each test and its history. UKF (b) fails S-A2 as worded (the FC declared position lost 5.75 s after the kill against a 5.5 s bound; 0.71 s of relay drain after the SIGKILL; the watcher had already commanded the landing). The EKF3 reference drifted 1.40 m against a prediction of ≤ 0.5 m (the prediction was wrong; no breach). The FGO safety re-tests flew the final FGO with the OLD priors.
- **Inputs:** eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json; expH/safety_*.json
- **Replaces:** — (new)

