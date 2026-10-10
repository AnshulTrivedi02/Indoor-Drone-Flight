| bag / arm | metric | none | A only | B only | both (= final) | stored final | archived pre-final | ΔA (share) | ΔB (share) | interaction |
|---|---|---|---|---|---|---|---|---|---|---|
| fwdc_tex_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | evo_a_cruise | 0.079 | 0.057 | 0.079 | 0.057 | 0.057 | 0.079 | -0.022 (100 %) | 0.000 (-0 %) | 0.000 |
| fwdc_tex_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | yaw_max_deg | 2.956 | 0.397 | 2.956 | 0.397 | 0.397 | 2.956 | -2.560 (100 %) | 0.000 (-0 %) | 0.000 |
| fwdc_tex_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | headings_fused | 9480 | 9184 | 9480 | 9184 | 9184 | 9480 | -296.000 (100 %) | 0.000 (-0 %) | 0 |
| fwdc_tex_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | bgz_mean_dpm | -4.889 | -8.240 | -4.889 | -8.240 | -8.240 | -4.889 | -3.351 (100 %) | 0.000 (-0 %) | 0.000 |
| fwdplainc_tex_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | evo_a_cruise | 0.200 | 43.218 | 0.196 | 43.539 | 43.539 | 0.200 | 43.181 (100 %) | 0.158 (0 %) | 0.325 |
| fwdplainc_tex_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | yaw_max_deg | 8.326 | 179.998 | 8.326 | 179.934 | 179.934 | 8.326 | 171.639 (100 %) | -0.032 (-0 %) | -0.063 |
| fwdplainc_tex_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | headings_fused | 4981 | 19 | 4981 | 28 | 28 | 4981 | -4957.500 (100 %) | 4.500 (-0 %) | 9 |
| fwdplainc_tex_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | bgz_mean_dpm | -4.908 | -290.579 | -4.908 | -319.386 | -319.386 | -4.908 | -300.075 (95 %) | -14.404 (5 %) | -28.807 |
| fwdplainc_trans_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | evo_a_cruise | 1068.550 | 41.234 | 1070.678 | 36.926 | 36.926 | 1068.550 | -1030.534 (100 %) | -1.090 (0 %) | -6.436 |
| fwdplainc_trans_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | yaw_max_deg | 3.616 | 179.993 | 3.617 | 179.990 | 179.990 | 3.616 | 176.375 (100 %) | -0.001 (-0 %) | -0.002 |
| fwdplainc_trans_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | headings_fused | 7854 | 18 | 7854 | 19 | 19 | 7854 | -7835.500 (100 %) | 0.500 (-0 %) | 1 |
| fwdplainc_trans_r1/fgo_heading (FGO; A = noise only, B = cap gate only) | bgz_mean_dpm | -4.938 | 415.060 | -4.938 | 447.096 | 447.096 | -4.938 | 436.016 (96 %) | 16.018 (4 %) | 32.036 |
| O_r1 room_fgo (FGO; A = noise only, B = cap gate only) | fgo_batch_indoor_rmse | 0.328 | 0.558 | 0.329 | 0.589 |  |  | 0.245 (94 %) | 0.016 (6 %) | 0.030 |
| O_r1 room_fgo (FGO; A = noise only, B = cap gate only) | fgo_live_indoor_rmse | 0.975 | 1.110 | 0.821 | 0.828 |  |  | 0.071 (-49 %) | -0.218 (149 %) | -0.127 |
| O_r2 room_fgo (FGO; A = noise only, B = cap gate only) | fgo_batch_indoor_rmse | 0.332 | 0.555 | 0.332 | 0.590 |  |  | 0.240 (93 %) | 0.018 (7 %) | 0.034 |
| O_r2 room_fgo (FGO; A = noise only, B = cap gate only) | fgo_live_indoor_rmse | 1.008 | 1.187 | 0.843 | 0.859 |  |  | 0.097 (-65 %) | -0.246 (165 %) | -0.163 |
| O_r3b room_fgo (FGO; A = noise only, B = cap gate only) | fgo_batch_indoor_rmse | 0.330 | 0.554 | 0.330 | 0.588 |  |  | 0.241 (93 %) | 0.017 (7 %) | 0.033 |
| O_r3b room_fgo (FGO; A = noise only, B = cap gate only) | fgo_live_indoor_rmse | 1.172 | 1.257 | 0.935 | 0.893 |  |  | 0.022 (-8 %) | -0.300 (108 %) | -0.128 |

| run | 'both' vs stored final | 'none' vs archived pre-final |
|---|---|---|
| dsn_tex_r1/ukf | IDENTICAL | {'ukf_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} |
| dsn_tex_r2/ukf | {'ukf_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} | IDENTICAL |
| dsn_tex_r3/ukf | {'ukf_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} | {'ukf_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} |
| fwdc_tex_r1/ukf_heading | {'ukf_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} | {'ukf_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} |
| fwdc_tex_r1/ukf_baseline | {'ukf_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} | {'ukf_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} |
| dsn_tex_r1/fgo | IDENTICAL | {'fgo_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} |
| dsn_tex_r2/fgo | {'fgo_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} | {'fgo_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} |
| dsn_tex_r3/fgo | {'fgo_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} | {'fgo_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} |
| dsn_tex_r6/fgo | {'fgo_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} | {'fgo_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} |
| fwdc_tex_r1/fgo_heading | IDENTICAL | IDENTICAL |
| fwdc_tex_r1/fgo_baseline | {'fgo_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} | {'fgo_traj.tum': False, 'ground_truth.tum': False, 'bgz_series.txt': False, 'fwd_stats.json': False, 'metrics.txt(no timing)': False} |
| fwdplainc_tex_r1/fgo_heading | IDENTICAL | IDENTICAL |
| fwdplainc_trans_r1/fgo_heading | IDENTICAL | IDENTICAL |
| O_r1/room_fgo | IDENTICAL | IDENTICAL |
| O_r2/room_fgo | IDENTICAL | IDENTICAL |
| O_r3b/room_fgo | IDENTICAL | IDENTICAL |
