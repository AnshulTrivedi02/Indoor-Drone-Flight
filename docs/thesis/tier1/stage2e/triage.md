# Stage 2e: triage of new FAILED-ESTIMATOR runs during the parallel batch (read-only on outputs)
Test (advisor/coordinator plan): the live excursion onset precedes the first exception, AND a wrong-id event
(stats.json tier1.mislabel.events_t_true_new) falls shortly before the excursion. Both hold → divergence (not a harness bug).

| run | wrong-id event(s) before onset (t, true→new) | live jump | excursion onset (s) | first exception (s) | verdict |
|---|---|---|---|---|---|
| e3a_T_A_r2_0.01_s2 | 59.302 (6→5); next 60.358 (6→7) | 59.028 → 59.362: (6.08, 3.66) → (2.92, −0.62) m | 59.928 | 60.695 (RuntimeError) | divergence; batch continues |
| e3a_T_A_r2_0.01_s1 | 55.342 (2→1): live jump 55.228 → 55.362 s, x 6.05 → −1.53 m, not recovered; then 61.513 (6→2) | 61.362 → 61.695: (−2.64, 7.76) → (3.68, 0.90) m | 61.795 | 62.595 (RuntimeError) | divergence; batch continues |
| e3a_T_A_r3_0.01_s1 | 55.012 (2→1) | 54.814 → 55.014: x 6.05 → −1.29 m, oscillating, then blows up | 56.248 | 60.548 (RuntimeError) | divergence; batch continues |
| e3a_T_A_r3_0.01_s2 | 56.101 (2→6), a mislabelled FIRST sighting of id 6 (landmarks_first_sighting_mislabelled = 2), so L(6) is created at the wrong place | 59.981 → 60.048: y 3.23 → 1.20 m, then wild (no wrong-id event in between; inferred to be the true tag 6 contradicting the misplaced L(6), the mechanism diagnosed for T_A_r1 1% s2; not separately verified) | 60.314 | 65.614 (RuntimeError) | divergence; batch continues |
