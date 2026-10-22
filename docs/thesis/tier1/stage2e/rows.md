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
