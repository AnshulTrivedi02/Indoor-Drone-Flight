# E3 map-collapse diagnosis: Part 2 predictions (written BEFORE launch, 2026-10-23)

Descriptive diagnosis only; no E3 verdict, score or criterion changes. Runs: T_A_r1, 1%, seed 0, arm (a), `--mislabel-keep`
(inert when unset; G0-L byte-identical at `3f613f4`). Keep stamps are the DETECTION stamps from
`stats.json:tier1.mislabel.events_t_true_new`, pre-verified with `reconstruct.py --keep` against the original run's
injection stream (expected wrong factors and first-sighting tids below).

Part 1 reading being tested: the collapse is a least-squares trade between wrong tag factors (about 124 sigma each at the
true layout) and dead reckoning that is weak (flow sigma 0.25 rad/s x h_cam about 1.75 m = about 0.44 m/s per keyframe);
first-sighting mislabels set the ONSET on s0 (the step comes at the true tag's first sighting, 59.332 s and 65.999 s),
but existing cf2_s1/cf2_s2 (0 first-sighting mislabels) also collapsed, so they are not necessary.

| run | kept (true id restored) | remaining wrong factors | first-sighting tids | prediction | contradicts Part 1 if |
|---|---|---|---|---|---|
| cf (i) | 36.169, 36.928 (the 2 first-sighting mislabels) | 17 (all to existing landmarks) | [] | no step at 59.332 s / 65.999 s; the map still collapses later (landmark spread well below the true 3.674 m, LC live well above 2 x clean); onset at or after a remaining wrong event (first: 59.995 s, 6->5) | it ends near clean (LC live <= 2 x clean 0.0574 m) with a true-size map: then first-sighting mislabels would be necessary, contradicting cf2 |
| cf (ii) | the other 17 | 2 (both first-sighting, tids 3 and 6) | [3, 6] | identical to the original up to the first kept event (59.995 s), so the same step at 59.332 s; afterwards a distorted map in which at least L(3), L(6) stay pulled toward tag 4's place; LC live well above 2 x clean; whether ALL landmarks collapse is open | no step at 59.332 s, or it ends near clean with a true-size map |
