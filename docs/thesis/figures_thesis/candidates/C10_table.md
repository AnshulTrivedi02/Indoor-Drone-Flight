# C10. E6 mapping flights: per-flight map position RMS (table candidate)

| pair | mapping flight | FGO map position RMS (m) | UKF map position RMS (m) |
|---|---|---|---|
| T_A_r1 | E6M_fig8_r1b | 0.0455 | 0.0448 |
| T_A_r2 | E6M_fig8_r2 | 0.0342 | 0.0401 |
| T_A_r3 | E6M_fig8_r3 | 0.0275 | 0.0476 |

Position RMS over the 7 non-gauge tags (the gauge tag is fixed to its surveyed position by definition), rounded once from docs/thesis/tier1/e6/maps/<mapping flight>/map_errors.json (errors.{fgo,ukf}.pos_rms_m), cross-checked by exact string equality against BOTH of docs/thesis/tier1/numbers_tier1.md's E6 map-error tables (the 'Map error per pair' table and the per-estimator 'landmark error against the surveyed map' table). Same data as candidate C09's chart.
