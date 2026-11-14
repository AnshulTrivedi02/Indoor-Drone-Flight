# Experiment 4: indoor window check (numbers addendum, newly computed)

Source: `eval/results/expO_window_check/window_check.json`, written by `eval/o_window_check.py` (commit `81c805e`), read-only from the stored tracks (bags, dataflash, `room_ukf/ukf_live.tum`, `room_fgo/fgo_live.tum`); no replay, flight or re-scoring. numbers.md is content-frozen and is not changed; no existing verdict or number changes.

**Status of the values.** The 'from the switch' RMSEs and both H4.2 ratios per flight are **newly computed by this check; they are not stored in `eval/results/expO/<trial>.json`**. The 'registered window' RMSEs equal the stored `tracks.<track>.indoor_rmse_m` in `eval/results/expO/<trial>.json` exactly (the check asserts float equality; `checks` = PASS for all three flights). Values are quoted as recorded in the JSON, unrounded.

**Windows.** Registered window: GNSS OFF marker to GNSS ON marker (as `eval/o_score.py`). Check window: from EKF3's source-set change after GNSS off (first change to source set 1 in `ekf3.source_set_changes`) to GNSS ON, applied to all three live tracks. H4.2 ratio = largest ÷ smallest live indoor RMSE (EKF3, UKF, FGO) per flight.

| flight | switch minus OFF marker (s) | EKF3 live indoor RMSE, registered window (m) | EKF3 live indoor RMSE, from the switch (m) | H4.2 ratio, registered window | H4.2 ratio, from the switch | largest / smallest, registered | largest / smallest, from the switch |
|---|---|---|---|---|---|---|---|
| O_r1 | 4.373659467185959 | 1.4226897349785146 | 1.4481724746539366 | 1.7160112419763964 | 1.7152596886983251 | EKF3 live / FGO live | EKF3 live / FGO live |
| O_r2 | 4.373653966750965 | 1.42247558762901 | 1.447956914339454 | 1.7146033263374372 | 1.7140118870701566 | EKF3 live / UKF live | EKF3 live / UKF live |
| O_r3b | 4.338722622687172 | 1.4261968179253368 | 1.4517187266735447 | 1.8424970782938659 | 1.8421674789936302 | EKF3 live / UKF live | EKF3 live / UKF live |

Keys (per flight, in the JSON): `<trial>.ss_change_minus_off_marker_s`, `<trial>.indoor_rmse_full_m.'EKF3 live'`, `<trial>.indoor_rmse_from_ss_change_m.'EKF3 live'`, `<trial>.live_max_over_min_full`, `<trial>.live_max_over_min_from_ss_change`, `<trial>.live_largest_*` / `live_smallest_*`.

UKF and FGO live indoor RMSE behind each ratio (m), as recorded:

| flight | window | UKF live | FGO live |
|---|---|---|---|
| O_r1 | registered | 0.8380727245736178 | 0.8290678406861414 |
| O_r1 | from the switch | 0.8533805062586649 | 0.8442875934156212 |
| O_r2 | registered | 0.829623718663581 | 0.8587789742890028 |
| O_r2 | from the switch | 0.8447764716582664 | 0.8745343549745357 |
| O_r3b | registered | 0.7740564881904621 | 0.8946165868233533 |
| O_r3b | from the switch | 0.7880492643734074 | 0.910901735358561 |

Recorded summary (`summary` in the JSON): registered window ratio range 1.7146033263374372 to 1.8424970782938659, `H-O2_pass_every_flight_le_1.5` = False, `ekf3_largest_every_flight` = True; from the switch 1.7140118870701566 to 1.8421674789936302, `H-O2_pass_every_flight_le_1.5` = False, `ekf3_largest_every_flight` = True.

**Summary.** Starting the window at EKF3's switch raises EKF3's indoor RMSE by about 0.025 m per flight, and the H4.2 ratio moves by less than 0.001. H4.2 stays NOT MET (the ratio exceeds 1.5 in every flight under both windows), and EKF3 stays the largest live indoor RMSE in every flight. The registered verdict and the stored range (1.71–1.84) are unchanged.

Related: the switch delay itself is explained in `eval/results/expO_switch_delay/switch_delay.json` (`eval/o_switch_delay.py`, commit `a833b53`): about 0.3 s of simulated GPS latency plus the harness switching script's 4.0 s vote.

