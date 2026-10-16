# Thesis figures and tables: index (revision 2026-10-16)

Built by `eval/figs_thesis.py` at commit `bf97f66` (run with `/home/makerspace/venv-evo/bin/python`; plotting and tabulating only, no number recomputed). Combined PDF for the supervisor (figures, then the tables rendered as pages, then the appendix): `docs/thesis/figures_thesis/thesis_figures_combined.pdf`. Figures are here as `.pdf` and `.png`; tables T1–T8 are in `docs/thesis/tables/` as LaTeX (`.tex`, booktabs; NOT compiled on the build machine, which has no TeX: checked for ASCII, balanced braces and the column count of every row), markdown (`.md`) and a rendered page (`.png`). The frozen pack (`docs/thesis/final_results_pack.pdf`, `eval/figs_final_pack.py`) is untouched.

**Revision 2026-10-16.** F1 (`F1_scorecard`) became table T1; F3 (`F3_accuracy_without_and_with_heading`) became table T2; F4 (`F4_blank_floor_flow_loss`) became table T3; F8 (`F8_H_tag_loss_drift`) became table T5. The old figure files are removed from this folder; they remain in the git history (commit `7778cd6`, `git show 7778cd6:docs/thesis/figures_thesis/<name>.png`). F2 is now one panel (the heading-error panel moved to table T4); F6 is the time trace only (the per-flight RMSE moved to table T6); F5 and F7 are unchanged. T7 (failure behaviour) and T8 (hindsight ratio) are new.

**Colour mapping (Okabe–Ito, colour-blind safe; fixed across every figure):** EKF3 #0072B2 (blue, circle) · UKF #009E73 (bluish green, triangle) · FGO #D55E00 (vermilion, square) · truth / references #999999 (grey). Solid lines / filled marks = live; dashed lines / open marks = hindsight. No log axes anywhere.

**Scorecard categories (T1):** BEST = a stated ordering puts it first; TIED = no ordering is claimed (or all pass the same criteria); BEHIND = a stated ordering or failed similarity verdict puts it below; FAILED = does not bound position; PASSED = met its pre-registered criteria with no comparison (L, FGO only); N/A = not run. BEHIND, PASSED and N/A are additions to best / tied / failed, used where those three do not fit.

| id | kind | files | title | status | checks | log-scale handling |
|---|---|---|---|---|---|---|
| F2 | figure | `F2_heading_stops_sideways_drift.png`, `F2_heading_stops_sideways_drift.pdf` | The camera heading stops the sideways drift: without it every estimator flies into the west wall | CURRENT | 4/4 | none needed |
| F5 | figure | `F5_T_tags_known_positions.png`, `F5_T_tags_known_positions.pdf` | Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm | CURRENT | 8/8 | none needed |
| F6 | figure | `F6_O_outdoor_indoor.png`, `F6_O_outdoor_indoor.pdf` | Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight keeps the error near 1 m | CURRENT | 4/4 | none needed |
| F7 | figure | `F7_L_loop_closure.png`, `F7_L_loop_closure.pdf` | Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps | CURRENT | 5/5 | none needed |
| T1 | table | `T1_scorecard.md`, `T1_scorecard.tex` | Which estimator wins where (scorecard of the restated verdicts) | CURRENT | 16/16 | none needed (table) |
| T2 | table | `T2_accuracy_heading.md`, `T2_accuracy_heading.tex` | Position error without and with the camera heading (textured floor) | CURRENT | 10/10 | none needed (table) |
| T3 | table | `T3_blank_floor.md`, `T3_blank_floor.tex` | Blank floor: position error after the loss of flow aiding | CURRENT | 6/6 | none needed (table) |
| T4 | table | `T4_closed_loop.md`, `T4_closed_loop.tex` | Closed loop at half real-time (RTF 0.5): the final build of each estimator flying the vehicle | CURRENT | 9/9 | none needed (table) |
| T5 | table | `T5_H_tag_loss_drift.md`, `T5_H_tag_loss_drift.tex` | Experiment H: drift while the wall tag is hidden, flying estimators | CURRENT | 6/6 | none needed (table) |
| T6 | table | `T6_O_indoor_rmse.md`, `T6_O_indoor_rmse.tex` | Experiment O: indoor horizontal RMSE per flight (123 s, GNSS off) | CURRENT | 7/7 | none needed (table) |
| T7 | table | `T7_failure_behaviour.md`, `T7_failure_behaviour.tex` | Failure behaviour: blank-floor validity, the O return jump and the safety tests | CURRENT | 9/9 | none needed (table) |
| T8 | table | `T8_hindsight_ratio.md`, `T8_hindsight_ratio.tex` | Hindsight: the FGO whole-flight batch against the RTS-smoothed UKF | CURRENT | 6/6 | none needed (table) |
| A1 | appendix | `A1_closed_loop_builds.png` | Closed loop: every flown build against B1–B5 and the contact window | CURRENT | 8/8 | none needed (table) |
| A2 | appendix | `A2_H_and_safety_p1.png`, `A2_H_and_safety_p2.png`, `A2_H_and_safety_p3.png` | H hold sets and the safety tests (all runs) | CURRENT | 17/17 | none needed (table) |
| A3 | appendix | `A3_F1_cost_ablations_p1.png`, `A3_F1_cost_ablations_p2.png` | F1, the L compute cost and the build ablations | CURRENT | 8/8 | none needed (table) |

**Total: 123/123 checks match** (a check repeated in two items is counted in each).

**Last-digit rounding matches (accepted, as in the pack):** T FGO batch A–D (m): file `0.010–0.028`, numbers.md `0.011–0.028`; O H-O2 live max/min ratio; largest = EKF3 in every flight: file `1.71–1.84; True`, numbers.md `1.72–1.84; True`; L live with / without loop closure (m): file `0.049–0.076 / 0.263–0.361`, numbers.md `0.049–0.076 / 0.262–0.361`; T 8 tags: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m): file `0.039 0.037 0.020 0.014 0.010`, numbers.md `0.039 0.037 0.020 0.014 0.011`; T 2 tags: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m): file `0.074 0.076 0.054 0.039 0.019`, numbers.md `0.074 0.076 0.053 0.039 0.019`; L nolc live overall (m): file `0.263–0.361`, numbers.md `0.262–0.361`; P-T4 max/min ratio A / B / C / D: file `1.31 / 2.14 / 2.06 / 3.89`, numbers.md `1.31 / 2.14 / 2.07 / 3.89`; T FGO batch A–D (m): file `0.010 / 0.015 / 0.019 / 0.028`, numbers.md `0.011 / 0.015 / 0.019 / 0.028`; O batch FGO vs cap-free RTS-UKF ratio, max/min per flight: file `1.01–1.05`, numbers.md `1.02–1.05`.

## Captions, sources and checks

### F2 (figure): The camera heading stops the sideways drift: without it every estimator flies into the west wall

- **Caption:** Textured corridor at half real-time (RTF 0.5; the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s), each estimator flying the vehicle (closed loop); true paths from the simulator, top-down, with the lateral (East) axis stretched 3.0× (stated on the figure). Colour = the flying estimator. Dashed: without a heading source (1 flight each), drawn up to the wall contact (X): EKF3 +242.1 s (after its pre-registered window), UKF v2 +165.9 s, FGO v3 +169.9 s. Solid: with the camera heading (3 flights each); all 9 stay within 0.39 m of the centreline and pass B1–B5, so they overlap on the centreline at this scale. Heading-error statistics (B3) are in Table T4. Builds: the jitter-corrected UKF port (v2) and the final FGO (v3, flown with the OLD FGO priors); earlier builds are in A1. n = 1 per no-heading flight; closed-loop run-to-run variability is unmeasured; no comparison across real-time factors.
- **Inputs:** paths: dataflash SIM of cl_a_tex_half, cl_bcpp_tex_r1–r3_half, cl_ukf_a_tex_half_v2, cl_ukf_b_tex_r1–r3_half_v2, cl_fgo_a_tex_half_v3, cl_fgo_b_tex_r1–r3_half_v3; contact and B2: eval/results/closed_loop_<trial>.json
- **numbers.md rows:** §15 (contact rows, B2 row, re-flown B1/B2/B4 rows); claim 14

| check | computed | expected | source | match |
|---|---|---|---|---|
| no-heading wall contact EKF3 / UKF v2 / FGO v3 (s) | `+242.1 / +165.9 / +169.9` | `+242.1 / +165.9 / +169.9` | numbers.md §15 contact rows | yes |
| with heading, B2 max cross-track per estimator EKF3 / UKF v2 / FGO v3 (m) | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | numbers.md §15 B2 row (EKF3 half) and re-flown rows | yes |
| plotted with-heading paths: max |x| in cruise vs scored B2, all 9 flights, |Δ| <= 0.05 m | `ok` | `ok` | curve source (dataflash SIM) vs closed_loop_*.json B2 | yes |
| plotted no-heading paths end at the scored contact point, all 3, |Δ| <= 0.5 m | `ok` | `ok` | curve source (dataflash SIM, cut at cruise start + contact time) vs closed_loop_*.json contact | yes |

### F5 (figure): Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm

- **Caption:** Experiment T (the tag room, 5 laps of a 6 m square, open loop on simulator truth): horizontal RMSE in the world frame, no alignment, against the tags sent (A all 8, B the 4 corners, C 2 diagonal, D 1 tag; median gap between fixes 4.3 / 10.1 / 22.0 / 46.3 s). Solid, filled = live; dashed, open = hindsight (the FGO whole-flight batch and the RTS-smoothed UKF); small marks = each of 3 flights, line = their mean. Live errors grow from 2–4 cm to 8–13 cm as tags thin out; no live ordering is claimed (in D the FGO live 8.3 cm against EKF3 9.6 cm is descriptive, n = 3). P-T3 FAILS (live max/min 1.97 / 2.36 / 1.42 / 1.58). The FGO batch stays at 1.0–2.8 cm; its hindsight gain grows with the gap (H-T1 PASS), the RTS-UKF's does not (P-T2 FAIL), and the batch-to-RTS ratio is 1.31–3.89 (P-T4 FAIL). Same tag fixes for every estimator.
- **Inputs:** eval/results/expT/T_{A,B,C,D}_r{1,2,3}.json (tracks.*.horiz_err_m.rmse), expT/t_aggregate.json
- **numbers.md rows:** §16.1 table and bullets (H-T1, P-T2, P-T3, P-T4, condition D); claims 17, 18

| check | computed | expected | source | match |
|---|---|---|---|---|
| T 8 tags: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m) | `0.039 0.037 0.020 0.014 0.010` | `0.039 0.037 0.020 0.014 0.011` | numbers.md §16.1 table | yes (last-digit rounding) |
| T 4 tags: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m) | `0.055 0.061 0.026 0.031 0.015` | `0.055 0.061 0.026 0.031 0.015` | numbers.md §16.1 table | yes |
| T 2 tags: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m) | `0.074 0.076 0.054 0.039 0.019` | `0.074 0.076 0.053 0.039 0.019` | numbers.md §16.1 table | yes (last-digit rounding) |
| T 1 tag: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m) | `0.096 0.131 0.083 0.109 0.028` | `0.096 0.131 0.083 0.109 0.028` | numbers.md §16.1 table | yes |
| T median gaps A–D (s) | `4.3 / 10.1 / 22.0 / 46.3` | `4.3 / 10.1 / 22.0 / 46.3` | numbers.md §16.1 table header | yes |
| tags per lap in B | `[0, 1, 2, 3]` | `[0, 1, 2, 3]` | T_B_r1.json gates (4 corner tags) | yes |
| H-T1 median gain A–D (m), rho, PASS | `0.010 / 0.011 / 0.023 / 0.052 +0.30 True` | `0.010 / 0.011 / 0.023 / 0.052 +0.30 True` | numbers.md §16.1 | yes |
| P-T2 gain A–D (m), PASS | `+0.020 / +0.032 / +0.037 / +0.029 False` | `+0.020 / +0.032 / +0.037 / +0.029 False` | numbers.md §16.1 | yes |

### F6 (figure): Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight keeps the error near 1 m

- **Caption:** Experiment O (outdoor → indoor → outdoor, open loop on simulator truth), flight 1: horizontal error against time in the world frame, no alignment. Indoor sensor set, the same for all three estimators: IMU (accelerometer and gyro), downward optical flow and the downward LiDAR rangefinder only; no GNSS (switched off at the entrance), no compass, no forward-camera heading (descoped) and no tags (none in the world). Route events (dotted): GNSS OFF at the entrance (0 s); the far end, 30 m inside, reached at ~60 s and held 3 s; the return in reverse at the same heading (no yaw turn) from 63 s; GNSS ON on re-crossing the entrance at 123 s. EKF3 resets to GNSS on return with a 4.10 m jump (every flight). Solid = live, dashed = hindsight. The per-flight indoor RMSE of all three flights is in Table T6 (H-O1 PASS 3/3; H-O2 FAIL; P-O3 PASS).
- **Inputs:** eval/results/expO/O_r1.json (markers_bag_s, max_step_after_return_m), O_r2.json, O_r3b.json; curves: O_r1 room_ukf/, room_fgo/ TUMs, dataflash XKF1 about EKF3's origin (gnss.npz), bag /imu/time_ref (clock map); design: METHODOLOGY 'Experiment O: pre-registration', sim/worlds/outdoor_indoor.sdf, fly_trial.py outback(), o_gnss.parm
- **numbers.md rows:** §16.2 table and bullets; claims 19–22

| check | computed | expected | source | match |
|---|---|---|---|---|
| O EKF3 reset jump (m) | `4.10–4.10` | `4.10–4.10` | numbers.md §16.2 ('4.10 m, every flight') | yes |
| O indoor duration (s) | `123` | `123` | numbers.md §16.2 heading ('123 s, GNSS off') | yes |
| O_r1 curve indoor RMSE recomputed vs json, max |Δ| <= 0.05 m | `ok` | `ok` | curve source vs scorer | yes |
| O_r1 bag has no tag topics | `0` | `0` | O design: no tags in outdoor_indoor.sdf | yes |

### F7 (figure): Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps

- **Caption:** Experiment L: the keyframe FGO with AprilTags at UNKNOWN positions (each tag a landmark), flights 1–3, horizontal RMSE per 6 m lap in the first tag's frame, one shared linear axis. Left: with loop closure the live error falls after lap 1 (lap 5 ÷ lap 1 0.16–0.43; overall 4.9–7.6 cm live, 1.7–2.7 cm hindsight). Right: without re-identification it grows 2.9–4.5× over five laps (overall 26.3–36.1 cm live). H-L1, H-L2, H-L3 and P-L4 PASS 3/3. This is an FGO capability, not an FGO-against-filter result (the filters have no loop-closure equivalent); one estimator, so one colour, with live solid/filled and hindsight dashed/open. V-L is not re-scorable on the corrected FGO (its labels were never recorded).
- **Inputs:** eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m)
- **numbers.md rows:** §16.3 table and bullets; claims 23, 24

| check | computed | expected | source | match |
|---|---|---|---|---|
| L lc live overall (m) | `0.049–0.076` | `0.049–0.076` | numbers.md §16.3 | yes |
| L lc hindsight overall (m) | `0.017–0.027` | `0.017–0.027` | numbers.md §16.3 | yes |
| L nolc live overall (m) | `0.263–0.361` | `0.262–0.361` | numbers.md §16.3 | yes (last-digit rounding) |
| L nolc hindsight overall (m) | `0.221–0.266` | `0.221–0.266` | numbers.md §16.3 | yes |
| L lap5/lap1 lc live; nolc live | `0.16–0.43; 2.9–4.5` | `0.16–0.43; 2.9–4.5` | numbers.md §16.3 | yes |

### T1 (table): Which estimator wins where (scorecard of the restated verdicts)

- **Caption:** Each cell gives the category, the key number and the verdict it rests on; the categories come only from the restated verdicts. Mostly ties: the FGO is best only with the camera heading, and no estimator bounds position on a blank floor.
- **Inputs:** eval/results/rerun_dsn_evo.json, dsn_extra_evo.json, dsn_paired_test.json, phase4_{fwdc,fwdplainc}_evo.json, blank_behaviour.json, expT/t_aggregate.json, expO/O_*.json, expL/T_A_r*_t245.json, expH/s1far_r*.json, expH/h_comparative_2026-10-11.json, closed_loop_cl_*_half(_v2/_v3).json
- **numbers.md rows:** §6.1, §6.2, §6.6, §15, §16.1–§16.3, §17.2; claims 1a, 1b, 2, 7, 10, 14, 17–19, 23, 25

| check | computed | expected | source | match |
|---|---|---|---|---|
| dsn_tex median r1–r9 EKF3 / UKF / FGO (m) | `4.10 / 5.13 / 4.46` | `4.10 / 5.13 / 4.46` | numbers.md §6.1 standing row | yes |
| confirmatory EKF3 − FGO verdict | `no ordering claimed` | `no ordering claimed` | numbers.md §6.1 confirmatory row; claim 2 | yes |
| C0 with heading UKF / FGO range, 6 textured bags (m) | `0.13–0.25 / 0.06–0.22` | `0.13–0.25 / 0.06–0.22` | numbers.md §6.6 heading-arm rows | yes |
| C0 FGO lower than UKF | `6/6` | `6/6` | numbers.md §6.6 C0 row; claim 7 | yes |
| blank end-of-cruise UKF / FGO (km) † | `29–40 / 22–41` | `29–40 / 22–41` | numbers.md §6.2 | yes |
| EKF3 blank invalid for (s of cruise), all 14 | `301–310 (n 14)` | `301–310 (n 14)` | numbers.md §6.2 ('blank from take-off (all 14), for 301–310 s') | yes |
| T condition D live EKF3 / UKF / FGO (m) | `0.096 / 0.131 / 0.083` | `0.096 / 0.131 / 0.083` | numbers.md §16.1 table | yes |
| T FGO batch A–D (m) | `0.010–0.028` | `0.011–0.028` | numbers.md §16.1 table | yes (last-digit rounding) |
| O indoor live RMSE EKF3 / UKF / FGO (m) | `1.42–1.43 / 0.77–0.84 / 0.83–0.89` | `1.42–1.43 / 0.77–0.84 / 0.83–0.89` | numbers.md §16.2 table | yes |
| O H-O2 live max/min ratio; largest = EKF3 in every flight | `1.71–1.84; True` | `1.72–1.84; True` | numbers.md §16.2 H-O2 bullet | yes (last-digit rounding) |
| O FGO batch / RTS-UKF indoor (m) | `0.59–0.59 / 0.58–0.60` | `0.59–0.59 / 0.58–0.60` | numbers.md §16.2 table | yes |
| L live with / without loop closure (m) | `0.049–0.076 / 0.263–0.361` | `0.049–0.076 / 0.262–0.361` | numbers.md §16.3 | yes (last-digit rounding) |
| H run-mean hold error EKF3 (S1 far) / UKF (S2v2) / FGO (S3v2) (mm) | `7.8–7.9 / 6.4–7.1 / 8.3–8.6` | `7.8–7.9 / 6.4–7.1 / 8.3–8.6` | numbers.md §17.2 table | yes |
| H comparative H-H2; P-H3; H-H4 15 s; H-H4 5 s (re-flown) | `FAIL; FAIL; FAIL; FAIL` | `FAIL; FAIL; FAIL; FAIL` | numbers.md §17.2 (final-build sets primary, ruling 2026-10-16) | yes |
| closed loop half, with heading: B2 range EKF3 / UKF v2 / FGO v3 (m) | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | numbers.md §15 B2 row (EKF3 half) and re-flown rows (UKF v2 0.231/0.253/0.219; FGO v3 0.118/0.033/0.392) | yes |
| closed loop half, with heading: flights passing B1–B5 (+S2) | `3/3 / 3/3 / 3/3` | `3/3 / 3/3 / 3/3` | numbers.md §15 | yes |

### T2 (table): Position error without and with the camera heading (textured floor)

- **Caption:** Without a heading source all three drift by metres and no ordering is claimed; with the camera heading the UKF and the FGO stay within 0.25 m, the FGO lower on all 6 bags (C0). The Phase 5 decomposition attributes metres of cross-track to each estimator's own heading error without the heading, and centimetres with it.
- **Inputs:** eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json; phase4_{fwdc,fwdplainc}_evo.json, cross-checked against phase4_*_arms.json; phase5_analysis.json (decomposition, xtrack_head_m)
- **numbers.md rows:** §6.1, §6.4, §6.6; claims 1a, 1b, 2, 5, 7
- **Not cross-checkable:** Phase 5 decomposition column: JSON only, no numbers.md row (§6.3 'NOT RESTATED')

| check | computed | expected | source | match |
|---|---|---|---|---|
| dsn_tex median r1–r9 EKF3 / UKF / FGO (m) | `4.10 / 5.13 / 4.46` | `4.10 / 5.13 / 4.46` | numbers.md §6.1 standing row | yes |
| dsn_tex mean r1–r3 EKF3 / UKF / FGO (m) | `4.00 / 3.59 / 3.44` | `4.00 / 3.59 / 3.44` | numbers.md §6.1; claim 1a | yes |
| dsn_tex UKF r1–r9 range (m) | `1.17–5.85` | `1.17–5.85` | numbers.md §6.1 D15 wording row | yes |
| confirmatory mean d, CI (m) | `-0.021 [-0.989, 0.947]` | `-0.021 [-0.989, 0.947]` | numbers.md §6.1 | yes |
| no heading EKF3 fwdc / fwdplainc r1–r3 (m) | `4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08` | `4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08` | numbers.md §6.4 | yes |
| no heading FGO fwdc / fwdplainc r1–r3 (m) | `4.47 / 2.26 / 4.54 / 4.54 / 4.52 / 4.74` | `4.47 / 2.26 / 4.54 / 4.54 / 4.52 / 4.74` | numbers.md §6.4 | yes |
| no heading UKF fwdc / fwdplainc r1–r3 (m) | `4.96 / 1.78 / 4.96 / 5.02 / 11.19 / 10.82` | `4.96 / 1.78 / 4.96 / 5.02 / 11.19 / 10.82` | numbers.md §6.4 | yes |
| with heading UKF fwdc / fwdplainc r1–r3 (m) | `0.13 / 0.13 / 0.14 / 0.19 / 0.15 / 0.25` | `0.13 / 0.13 / 0.14 / 0.19 / 0.15 / 0.25` | numbers.md §6.6 | yes |
| with heading FGO fwdc / fwdplainc r1–r3 (m) | `0.06 / 0.06 / 0.06 / 0.15 / 0.09 / 0.22` | `0.06 / 0.06 / 0.06 / 0.15 / 0.09 / 0.22` | numbers.md §6.6 | yes |
| phase4 evo vs arms json agreement (mismatches) | `0` | `0` | phase4_*_evo.json vs phase4_*_arms.json | yes |

### T3 (table): Blank floor: position error after the loss of flow aiding

- **Caption:** On a blank floor nothing bounds position: the UKF and the FGO dead-reckon away to km-scale errors by the end of the cruise, and EKF3 flags its own position invalid, so it has no scored error. Behaviour under total loss of flow aiding, not accuracy.
- **Inputs:** eval/results/blank_behaviour.json (along_m, cross_m at +10/+30/+60 s and end; EKF3_invalid_period; valid_frames_in_cruise)
- **numbers.md rows:** §6.2; claim 10

| check | computed | expected | source | match |
|---|---|---|---|---|
| UKF +10/+30/+60 s ranges (m) | `6.4–8.2 / 27.3–36.5 / 60–108` | `6.4–8.2 / 27.3–36.5 / 60–108` | numbers.md §6.2 | yes |
| FGO +10/+30/+60 s ranges (m) | `6.4–8.2 / 28.0–37.0 / 154–204` | `6.4–8.2 / 28.0–37.0 / 154–204` | numbers.md §6.2 | yes |
| n flights UKF / FGO | `11/11` | `11/11` | numbers.md §6.2 | yes |
| end of cruise UKF / FGO (km) † | `29–40 / 22–41` | `29–40 / 22–41` | numbers.md §6.2 | yes |
| EKF3 invalid, s of cruise, all 14 blank | `301–310` | `301–310` | numbers.md §6.2 | yes |
| valid airborne flow frames in cruise, all blank bags | `max 0 over 14` | `max 0 over 14` | numbers.md §6.2 ('0', all 14 blank bags) | yes |

### T4 (table): Closed loop at half real-time (RTF 0.5): the final build of each estimator flying the vehicle

- **Caption:** Without a heading source every flying estimator reaches the west wall; with the camera heading every flight passes B1–B5 (+S2), with the per-flight cross-track, heading-error and lateral-speed values shown (flights 1 / 2 / 3). No ordering between the estimators is claimed.
- **Inputs:** eval/results/closed_loop_cl_a_tex_half.json, closed_loop_cl_bcpp_tex_r{1,2,3}_half.json, closed_loop_cl_ukf_{a,b}_tex*_half_v2.json, closed_loop_cl_fgo_{a,b}_tex*_half_v3.json
- **numbers.md rows:** §15 (contact rows, B1–B5 counts, B2, B3, B4 re-flown rows); claim 14

| check | computed | expected | source | match |
|---|---|---|---|---|
| closed loop half, with heading: flights passing B1–B5 (+S2) | `3/3 / 3/3 / 3/3` | `3/3 / 3/3 / 3/3` | numbers.md §15 | yes |
| UKF v2 B2 r1/r2/r3 (m) | `0.231 / 0.253 / 0.219` | `0.231 / 0.253 / 0.219` | numbers.md §15 re-flown row | yes |
| FGO v3 B2 r1/r2/r3 (m) | `0.118 / 0.033 / 0.392` | `0.118 / 0.033 / 0.392` | numbers.md §15 re-flown row | yes |
| EKF3 half B2 range (m) | `0.24–0.33` | `0.24–0.33` | numbers.md §15 B2 row | yes |
| UKF v2 B3 p95/max/mean per flight (deg) | `0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250` | `0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250` | numbers.md §15 re-flown B3 row | yes |
| FGO v3 B3 p95/max/mean per flight (deg) | `0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187` | `0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187` | numbers.md §15 re-flown B3 row | yes |
| EKF3 half B3 p95 / max range (deg) | `0.28–0.32/0.33–0.39` | `0.28–0.32/0.33–0.39` | numbers.md §15 B3 row | yes |
| no-heading wall contact EKF3 / UKF v2 / FGO v3 (s) | `+242.1 / +165.9 / +169.9` | `+242.1 / +165.9 / +169.9` | numbers.md §15 contact rows | yes |
| FGO v3 r3 B4 (m/s) | `0.246` | `0.246` | numbers.md §15 re-flown row (closest call) | yes |

### T5 (table): Experiment H: drift while the wall tag is hidden, flying estimators

- **Caption:** Holding on a wall tag, every flying estimator drifts at most about 3 cm while the tag is hidden, inside every pre-registered band, and none locks out; each cell gives the maximum drift / its band in mm, with the range over the losses. The comparative criteria (H-H2, P-H3, H-H4) FAIL on these final-build sets, identical to the original-build verdicts (superseded builds: Table A2), so no ordering is claimed. The FGO safety re-tests (v4) used the NEW initial priors, while the flown FGO hold (S3v2) and corridor (v3) results used the OLD priors.
- **Inputs:** eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s3v2_r*.json (losses[*].<est>.effective.drift_m, drift_end_m, lockout)
- **numbers.md rows:** §17 (S1 table, P-H5, P-H7), §17.1 (S2v2, S3v2), §17.2; claims 25, 26
- **Not cross-checkable:** S1-far EKF3 drifts (3 of the 6 EKF3 flights): METHODOLOGY only, no numbers.md row

| check | computed | expected | source | match |
|---|---|---|---|---|
| S1 EKF3 flying drift 5/15/30/move (mm, effective) | `13–27 | 6–25 | 3–11 | 7–31` | `13–27 | 6–25 | 3–11 | 7–31` | numbers.md §17 table | yes |
| S2v2 UKF flying end-of-loss drift r1/r2/r3 (mm) | `5/7/8 | 19/7/26 | 6/10/10 | 26/4/5` | `5/7/8 | 19/7/26 | 6/10/10 | 26/4/5` | numbers.md §17.1 table | yes |
| S3v2 FGO flying end-of-loss drift r1/r2/r3 (mm) | `13/20/17 | 7/25/27 | 22/15/9 | 17/11/18` | `13/20/17 | 7/25/27 | 22/15/9 | 17/11/18` | numbers.md §17.1 table | yes |
| effective vs end-of-loss drift, max |Δ| at printed (mm) precision | `≤ 5 mm` | `≤ 5 mm` | numbers.md §17.1 ('differ by ≤ 5 mm'); unrounded 5.1 mm (S2v2 r1, move loss) | yes |
| every drift inside its pre-registered band (P-H5) | `True` | `True` | numbers.md §17, §17.1 (every band PASSES) | yes |
| lockouts in any loss (flying estimators) | `0` | `0` | numbers.md §17 (P-H7 PASS) | yes |

### T6 (table): Experiment O: indoor horizontal RMSE per flight (123 s, GNSS off)

- **Caption:** Indoors without GNSS the live errors are 0.8–1.4 m and not similar across estimators (EKF3 largest in every flight, H-O2 FAIL); the two hindsight tracks agree at 0.58–0.60 m (P-O3 PASS).
- **Inputs:** eval/results/expO/O_r1.json, O_r2.json, O_r3b.json (tracks.*.indoor_rmse_m)
- **numbers.md rows:** §16.2 table and bullets; claims 19–22

| check | computed | expected | source | match |
|---|---|---|---|---|
| O indoor RMSE EKF3 live (m) | `1.42–1.43` | `1.42–1.43` | numbers.md §16.2 table | yes |
| O indoor RMSE UKF live (m) | `0.77–0.84` | `0.77–0.84` | numbers.md §16.2 table | yes |
| O indoor RMSE FGO live (m) | `0.83–0.89` | `0.83–0.89` | numbers.md §16.2 table | yes |
| O indoor RMSE RTS-UKF (hindsight) (m) | `0.58–0.60` | `0.58–0.60` | numbers.md §16.2 table | yes |
| O indoor RMSE FGO batch (hindsight) (m) | `0.59–0.59` | `0.59–0.59` | numbers.md §16.2 table | yes |
| O H-O2 live max/min ratio; largest = EKF3 in every flight | `1.71–1.84; True` | `1.72–1.84; True` | numbers.md §16.2 H-O2 bullet | yes (last-digit rounding) |
| H-O1: FGO batch below both filters' live tracks, flights | `3/3` | `3/3` | numbers.md §16.2 (H-O1 PASS 3/3) | yes |

### T7 (table): Failure behaviour: blank-floor validity, the O return jump and the safety tests

- **Caption:** How each estimator fails: EKF3 declares its blank-floor position invalid while the UKF and the FGO run away with no invalid period recorded; on the return to GNSS EKF3 jumps 4.1 m; in the hold safety tests the final run of each test (the latest on the final build: UKF v3, FGO v4) passes as worded except UKF (b) S-A2, which fails as worded in v2 and v3 (a relay-drain timing fault in the bound). The FGO safety re-tests (v4) used the NEW initial priors, while the flown FGO hold (S3v2) and corridor (v3) results used the OLD priors.
- **Inputs:** eval/results/blank_behaviour.json; expO/O_r1.json, O_r2.json, O_r3b.json (max_step_after_return_m); expH/safety_*.json
- **numbers.md rows:** §6.2, §15 safety and history rows, §16.2; METHODOLOGY 'H safety test …' entries, 2d, rulings 2026-10-11, 'Band C … FGO safety re-tests'

| check | computed | expected | source | match |
|---|---|---|---|---|
| S-A4 FAIL in the early score files (no disarm recorded: rearmed_after_disarm null) | `safety_ukf_a: None, safety_fgo_b: None` | `safety_ukf_a: None, safety_fgo_b: None` | eval/results/expH/safety_ukf_a.json, safety_fgo_b.json; METHODOLOGY L11490 ('S-A4: not applicable (an (a) run)'), L11827 ('S-A4: not scored (no touchdown)') | yes |
| EKF3 blank invalid (s of cruise); valid airborne flow frames | `301–310; max 0` | `301–310; max 0` | numbers.md §6.2 | yes |
| O largest step in 10 s after return EKF3 / UKF / FGO live (m) | `4.10–4.10 / 2.30–2.44 / 2.14–2.28` | `4.10–4.10 / 2.30–2.44 / 2.14–2.28` | numbers.md §16.2 table | yes |
| UKF (b) v2 / v3 S-A2 delay (s), verdict | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | numbers.md §15 history row (v2) and safety row (v3, final) | yes |
| UKF (a) v2 / v3 verdict | `ALL PASS / ALL PASS` | `ALL PASS / ALL PASS` | numbers.md §15 history row (v2) and safety row (v3, final) | yes |
| FGO (a) v4 S-A2 / disp; (b) v4 | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | numbers.md §15 safety row (v4, final); METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS' | yes |
| FGO (a) v3 S-A2 / disp; (b) v3 | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | numbers.md §15 history row (v3, earlier final-build run) | yes |
| FGO (b) first run S-A3; UKF (a) first run S-A2 / S-A3 | `False; False / False` | `False; False / False` | numbers.md §15 history row (S-A3 FAIL; S-A2 FAIL as worded, S-A3 FAIL) | yes |
| EKF3 reference drift (m) | `1.40` | `1.40` | numbers.md §15 history row | yes |

### T8 (table): Hindsight: the FGO whole-flight batch against the RTS-smoothed UKF

- **Caption:** With tags at known positions (T) the FGO batch is below the RTS-UKF in every condition, by 1.3–3.9× (largest with 1 tag; P-T4 FAIL as pre-registered); indoors without GNSS (O) the two hindsight tracks are equal within 1–2% (P-O3 PASS).
- **Inputs:** eval/results/expT/t_aggregate.json (conditions.*.mean_rmse_m, 'P-T4 hindsight ratio max/min'); expO/O_r1.json, O_r2.json, O_r3b.json (tracks.*.indoor_rmse_m)
- **numbers.md rows:** §16.1 (table, P-T4), §16.2 (table, P-O3); claims 18, 21

| check | computed | expected | source | match |
|---|---|---|---|---|
| P-T4 max/min ratio A / B / C / D | `1.31 / 2.14 / 2.06 / 3.89` | `1.31 / 2.14 / 2.07 / 3.89` | numbers.md §16.1 P-T4 | yes (last-digit rounding) |
| T8 table ratio = stored P-T4 ratio, all 4 conditions | `True` | `True` | t_aggregate.json P-T4 vs mean_rmse_m | yes |
| T RTS-UKF A–D (m) | `0.014 / 0.031 / 0.039 / 0.109` | `0.014 / 0.031 / 0.039 / 0.109` | numbers.md §16.1 table | yes |
| T FGO batch A–D (m) | `0.010 / 0.015 / 0.019 / 0.028` | `0.011 / 0.015 / 0.019 / 0.028` | numbers.md §16.1 table | yes (last-digit rounding) |
| O batch FGO vs RTS-UKF ratio, max/min per flight (capped) | `1.01–1.02` | `1.01–1.02` | numbers.md §16.2 P-O3 | yes |
| O batch FGO vs cap-free RTS-UKF ratio, max/min per flight | `1.01–1.05` | `1.02–1.05` | numbers.md §16.2 P-O3 (cap-free) | yes (last-digit rounding) |

### A1 (appendix): Closed loop: every flown build against B1–B5 and the contact window

- **Caption:** Pass/fail of every closed-loop corridor set, computed from the closed-loop score files, with the build ablations labelled: UKF v1 (pre-jitter fix) against v2 (final); FGO original, robust, v2 (noise fix only, ABLATION) and v3 (final, OLD priors).
- **Inputs:** eval/results/closed_loop_<trial>.json
- **numbers.md rows:** §15 (contacts, B1–B5 counts, B2, B3, re-flown sets); claim 14

| check | computed | expected | source | match |
|---|---|---|---|---|
| EKF3 half contact MISS | `MISS` | `MISS` | numbers.md §15 (D21) | yes |
| UKF v1 half heading set | `2/3` | `2/3` | numbers.md §15 (r3 B4 0.296 m/s) | yes |
| UKF v2 / FGO v3 heading sets | `3/3 PASS / 3/3 PASS` | `3/3 PASS / 3/3 PASS` | numbers.md §15 (re-flown sets) | yes |
| FGO v2 ablation heading set | `3/3 PASS` | `3/3 PASS` | numbers.md §15 | yes |
| FGO original hard / robust heading sets (D28) | `3/3 PASS / 3/3 PASS` | `3/3 PASS / 3/3 PASS` | numbers.md §15 (D28) | yes |
| contacts UKF v1 half / UKF v2 / FGO orig / FGO v2 / FGO v3 (s) | `+198.0 / +165.9 / +165.8 / +169.6 / +169.9` | `+198.0 / +165.9 / +165.8 / +169.6 / +169.9` | numbers.md §15 contact rows | yes |
| EKF3 full no-heading contact; UKF v1 full contact | `+186.2; +163.0` | `+186.2; +163.0` | numbers.md §15 rows 1–2 | yes |
| UKF v1 half / FGO original B3 p95/max ranges | `0.18–0.21° / 0.28–1.32°; 0.26–0.38° / 1.28–1.88°` | `0.18–0.21° / 0.28–1.32°; 0.26–0.38° / 1.28–1.88°` | numbers.md §15 B3 row (original builds) | yes |

### A2 (appendix): H hold sets and the safety tests (all runs)

- **Caption:** Experiment H sets (S1, S1 far, S2/S2v2, S3/S3v2) with hold error, drift, lockouts and the P-H5 bands, and every safety-test run with its as-worded verdict; the final runs are the v3 (UKF) and v4 (FGO, NEW priors) re-tests. The FGO safety re-tests (v4) used the NEW initial priors, while the flown FGO hold (S3v2) and corridor (v3) results used the OLD priors. The comparative criteria page gives the final-build sets (primary) beside the superseded builds; the final-build verdicts are identical to the original-build verdicts (all FAIL).
- **Inputs:** eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json, safety_*.json
- **numbers.md rows:** §15 safety rows, §17, §17.1; METHODOLOGY 2d and 'Band C … FGO safety re-tests'

| check | computed | expected | source | match |
|---|---|---|---|---|
| S2 / S2v2 / S3 / S3v2 hold window means (mm) | `4.9–6.3 ; 6.1–7.4 ; 7.6–8.2 ; 8.1–9.0` | `4.9–6.3 ; 6.1–7.4 ; 7.6–8.2 ; 8.1–9.0` | numbers.md §17.1 table | yes |
| lockouts S1 / S1far / S2v2 / S3v2 | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | numbers.md §17, §17.1 | yes |
| UKF (b) v2 / v3 S-A2 delay (s), verdict | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | numbers.md §15 history row (v2) and safety row (v3, final) | yes |
| UKF (a) v2 / v3 verdict | `ALL PASS / ALL PASS` | `ALL PASS / ALL PASS` | numbers.md §15 history row (v2) and safety row (v3, final) | yes |
| FGO (a) v3 S-A2 / disp; (b) v3 | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | numbers.md §15 history row (v3, earlier final-build run) | yes |
| FGO (a) v4 S-A2 / disp; (b) v4 | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | numbers.md §15 safety row (v4, final); METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS' | yes |
| FGO v4 a / b verdict | `ALL PASS / ALL PASS` | `ALL PASS / ALL PASS` | numbers.md §15 safety row (v4, final) | yes |
| FGO v2 ablation a / b: S-A2 s, disp m | `0.29 s, 0.78 m; 0.43 s, 1.27 m` | `0.29 s, 0.78 m; 0.43 s, 1.27 m` | numbers.md §15 history row | yes |
| history: UKF a rerun / UKF b / FGO a / FGO b2 disp (m); UKF b S-A2 (s) | `0.42 / 0.28 / 0.37 / 1.25; 4.81` | `0.42 / 0.28 / 0.37 / 1.25; 4.81` | numbers.md §15 history row | yes |
| FGO (b) first run S-A3; UKF (a) first run S-A2 / S-A3 | `False; False / False` | `False; False / False` | numbers.md §15 history row (S-A3 FAIL; S-A2 FAIL as worded, S-A3 FAIL) | yes |
| EKF3 reference drift (m) | `1.40` | `1.40` | numbers.md §15 history row | yes |
| H comparative verdicts, final-build sets (primary) / superseded builds | `FAIL ; FAIL ; FAIL ; FAIL / FAIL ; FAIL ; FAIL ; FAIL` | `FAIL ; FAIL ; FAIL ; FAIL / FAIL ; FAIL ; FAIL ; FAIL` | numbers.md §17.2 criteria table (both sets) | yes |
| H hold UKF / FGO / EKF3, final-build sets (mm) | `6.4–7.1 / 8.3–8.6 / 7.8–7.9` | `6.4–7.1 / 8.3–8.6 / 7.8–7.9` | numbers.md §17.2 criteria table (re-flown) | yes |
| H hold UKF, superseded builds (mm) | `5.5–6.1` | `5.5–6.1` | numbers.md §17.2 criteria table (earlier sets) | yes |
| P-H3 max/min, final-build / superseded | `2.40–2.58 / 2.37–2.43` | `2.40–2.58 / 2.37–2.43` | numbers.md §17.2 criteria table | yes |
| H-H4 (5 s) max/min, final-build / superseded | `3.2–7.7 / 3.4–5.9` | `3.2–7.7 / 3.4–5.9` | numbers.md §17.2 criteria table | yes |
| final safety runs: drift to touchdown UKF (a) v3 / UKF (b) v3 / FGO (a) v4 / FGO (b) v4 (m) | `0.58 / 1.07 / 1.45 / 0.21` | `0.58 / 1.07 / 1.45 / 0.21` | numbers.md §15 safety row (final runs, restated 2026-10-16) | yes |

### A3 (appendix): F1, the L compute cost and the build ablations

- **Caption:** Pass/fail table for the F1 robust-weighting test, the L compute cost (diagnostic; linear values, no plot) and the build ablations: UKF v1 against v2; FGO v2 (noise fix only) against v3 (final) and the v4 node; the flown-FGO OLD-priors note. The FGO safety re-tests (v4) used the NEW initial priors, while the flown FGO hold (S3v2) and corridor (v3) results used the OLD priors.
- **Inputs:** eval/results/f1_test.json; ~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/stats.json; closed_loop_*, expH/*
- **numbers.md rows:** §15.2 F1 row; §16.3 cost bullets; §15, §17.1

| check | computed | expected | source | match |
|---|---|---|---|---|
| F1 robust lower yaw max on | `6/6` | `6/6` | numbers.md §15.2 F1 row | yes |
| F1 lockouts FGO_robust = UKF_hard | `{"FGO_robust": 3, "UKF_hard": 3}` | `{"FGO_robust": 3, "UKF_hard": 3}` | numbers.md §15.2 | yes |
| F1 verdict robust_FGO_better | `False` | `False` | numbers.md §15.2 (NOT met, lockout tie) | yes |
| FGO_hard plain-wall yaw max (deg) | `4.59–5.03` | `4.59–5.03` | numbers.md §15.2 F1 row | yes |
| L LC median (ms) | `35–41` | `35–41` | numbers.md §16.3 (restated 2026-10-11) | yes |
| L no-LC median (ms) | `50–61` | `50–61` | numbers.md §16.3 | yes |
| L LC p99 (ms) | `80–94` | `80–94` | numbers.md §16.3 | yes |
| L no-LC wall (s) | `7276–9583` | `7276–9583` | numbers.md §16.3 | yes |

