# Thesis figures: index (2026-10-15)

Built by `eval/figs_thesis.py` at commit `e9a6012` (run with `/home/makerspace/venv-evo/bin/python`; plotting only, no number recomputed). Combined PDF for the supervisor: `docs/thesis/figures_thesis/thesis_figures_combined.pdf`. Each figure is here as `.pdf` and `.png`. The frozen pack (`docs/thesis/final_results_pack.pdf`, `eval/figs_final_pack.py`) is untouched.

**Colour mapping (Okabe–Ito, colour-blind safe; fixed across every figure):** EKF3 #0072B2 (blue, circle) · UKF #009E73 (bluish green, triangle) · FGO #D55E00 (vermilion, square) · truth / references #999999 (grey). Solid lines / filled marks = live; dashed lines / open marks = hindsight. No log axes anywhere.

**Scorecard categories (F1):** BEST = a stated ordering puts it first; TIED = no ordering is claimed (or all pass the same criteria); BEHIND = a stated ordering or failed similarity verdict puts it below; FAILED = does not bound position; PASSED = met its pre-registered criteria with no comparison (L, FGO only); N/A = not run. BEHIND, PASSED and N/A are additions to the brief's best/tied/failed, used where those three do not fit (listed in the handover).

| id | files | takeaway title | status | checks | log-scale handling |
|---|---|---|---|---|---|
| F1 | `F1_scorecard.png` (+ .pdf) | Which estimator wins where: mostly ties; the FGO wins only with the camera heading; none survives a blank floor | CURRENT | 16/16 | none needed |
| F2 | `F2_heading_stops_sideways_drift.png` (+ .pdf) | The camera heading stops the sideways drift: without it every estimator flies into the wall | CURRENT | 8/8 | none needed |
| F3 | `F3_accuracy_without_and_with_heading.png` (+ .pdf) | Without a heading source all three drift by metres; with the camera heading the UKF and FGO stay within 25 cm | CURRENT | 9/9 | none needed |
| F4 | `F4_blank_floor_flow_loss.png` (+ .pdf) | On a blank floor nothing bounds position: the UKF and FGO dead-reckon away; EKF3 declares itself invalid | CURRENT | 6/6 | km-scale end-of-cruise runaway next to tens of metres: axis CUT at +60 s, the end values given as annotated arrows (†) |
| F5 | `F5_T_tags_known_positions.png` (+ .pdf) | Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm | CURRENT | 8/8 | none needed |
| F6 | `F6_O_outdoor_indoor.png` (+ .pdf) | Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight cuts the error to 0.6 m | CURRENT | 9/9 | none needed |
| F7 | `F7_L_loop_closure.png` (+ .pdf) | Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps | CURRENT | 5/5 | none needed |
| F8 | `F8_H_tag_loss_drift.png` (+ .pdf) | Holding on a wall tag, every flying estimator drifts at most ~3 cm while the tag is hidden, inside every band | CURRENT | 6/6 | bands up to 400 mm next to drifts ≤ 31 mm: linear axis clipped at 60 mm; off-scale bands drawn as arrows with their value |
| A1 | `A1_closed_loop_builds.png` (+ .pdf) | Closed loop: every flown build against B1–B5 and the contact window | CURRENT | 8/8 | none needed (table) |
| A2 | `A2_H_and_safety_p1.png`, `A2_H_and_safety_p2.png` (+ .pdf) | H hold sets and the safety tests (all runs) | CURRENT | 11/11 | none needed (table) |
| A3 | `A3_F1_cost_ablations_p1.png`, `A3_F1_cost_ablations_p2.png` (+ .pdf) | F1, the L compute cost and the build ablations | CURRENT | 8/8 | none needed (table) |

**Last-digit rounding matches (accepted, as in the pack):** T FGO batch A–D (m): file `0.010–0.028`, numbers.md `0.011–0.028`; O H-O2 live max/min ratio; largest = EKF3 in every flight: file `1.71–1.84; True`, numbers.md `1.72–1.84; True`; L live with / without loop closure (m): file `0.049–0.076 / 0.263–0.361`, numbers.md `0.049–0.076 / 0.262–0.361`; T 8 tags: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m): file `0.039 0.037 0.020 0.014 0.010`, numbers.md `0.039 0.037 0.020 0.014 0.011`; T 2 tags: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m): file `0.074 0.076 0.054 0.039 0.019`, numbers.md `0.074 0.076 0.053 0.039 0.019`; L nolc live overall (m): file `0.263–0.361`, numbers.md `0.262–0.361`.

## Captions, sources and checks

### F1: Which estimator wins where: mostly ties; the FGO wins only with the camera heading; none survives a blank floor

- **Caption:** Scorecard of the restated verdicts (numbers.md; headline_claims_before_after.md), one row per estimator and one column per experiment, each cell with its key number. The categories come ONLY from the restated verdicts: no ordering is claimed between the three estimators on standard sensors (claim 2, confirmatory test 'no ordering claimed'; the UKF medians are descriptive, claim 1b), in T (ruling 7), in H (all drift bands PASS; the comparative criteria H-H2/P-H3/H-H4 FAIL as adjudicated, the same on the re-flown sets, PENDING a ruling) or in the closed loop (every set passes); the FGO is lower than the UKF with the camera heading on all 6 textured bags (C0, claim 7); in O the live errors are not similar (H-O2 FAIL), EKF3 being the largest in every flight, while the FGO batch equals the RTS-UKF (P-O3 PASS); L is an FGO-only capability; on the blank floor no estimator bounds position (claim 10).
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
| H comparative H-H2; P-H3; H-H4 15 s; H-H4 5 s (re-flown) | `FAIL; FAIL; FAIL; FAIL` | `FAIL; FAIL; FAIL; FAIL` | numbers.md §17.2 (PENDING ruling) | yes |
| closed loop half, with heading: B2 range EKF3 / UKF v2 / FGO v3 (m) | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | numbers.md §15 B2 row (EKF3 half) and re-flown rows (UKF v2 0.231/0.253/0.219; FGO v3 0.118/0.033/0.392) | yes |
| closed loop half, with heading: flights passing B1–B5 (+S2) | `3/3 / 3/3 / 3/3` | `3/3 / 3/3 / 3/3` | numbers.md §15 | yes |

### F2: The camera heading stops the sideways drift: without it every estimator flies into the wall

- **Caption:** Half-speed textured corridor (corridor_textured_half_fwdc), each estimator flying the vehicle (closed loop); true paths from the simulator (dataflash SIM), top-down; walls at x = ±10 m, dotted = the 9.58 m contact threshold. Left: without a heading source the flying estimator's yaw drifts and every vehicle reaches the west wall (X; EKF3 +242.1 s, after its pre-registered window, D21; UKF v2 +165.9 s; FGO v3 +169.9 s). Middle: with the camera heading all 9 flights stay within 0.39 m of the centreline and pass B1–B5. Right: the flying estimator's heading error on ONE shared scale; with the heading it stays inside ±0.7° (B3 p95 ≤ 0.38°). Builds: the jitter-corrected UKF port (v2) and the final FGO (v3), which flew the OLD FGO priors (initial yaw σ 1e-3 rad); earlier builds are in the appendix table. n = 1 per no-heading flight; closed-loop run-to-run variability is unmeasured; no cross-speed comparison.
- **Inputs:** paths: dataflash SIM of cl_a_tex_half, cl_bcpp_tex_r1–r3_half, cl_ukf_a_tex_half_v2, cl_ukf_b_tex_r1–r3_half_v2, cl_fgo_a_tex_half_v3, cl_fgo_b_tex_r1–r3_half_v3; heading error: dataflash XKF1 / XUKO / XFGO against SIM; contact, B2, B3: eval/results/closed_loop_<trial>.json
- **numbers.md rows:** §15 (contact rows, B2 row, re-flown B1/B2/B4 and B3 rows); claim 14

| check | computed | expected | source | match |
|---|---|---|---|---|
| no-heading wall contact EKF3 / UKF v2 / FGO v3 (s) | `+242.1 / +165.9 / +169.9` | `+242.1 / +165.9 / +169.9` | numbers.md §15 contact rows | yes |
| UKF v2 B2 r1/r2/r3 (m) | `0.231 / 0.253 / 0.219` | `0.231 / 0.253 / 0.219` | numbers.md §15 re-flown row | yes |
| FGO v3 B2 r1/r2/r3 (m) | `0.118 / 0.033 / 0.392` | `0.118 / 0.033 / 0.392` | numbers.md §15 re-flown row | yes |
| EKF3 half B2 range (m) | `0.24–0.33` | `0.24–0.33` | numbers.md §15 B2 row | yes |
| UKF v2 B3 p95/max/mean per flight (deg) | `0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250` | `0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250` | numbers.md §15 re-flown B3 row | yes |
| FGO v3 B3 p95/max/mean per flight (deg) | `0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187` | `0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187` | numbers.md §15 re-flown B3 row | yes |
| EKF3 half B3 p95 / max range (deg) | `0.28–0.32/0.33–0.39` | `0.28–0.32/0.33–0.39` | numbers.md §15 B3 row | yes |
| plotted heading-error curve max vs scored B3 max, all 9 flights, |Δ| <= 0.10° | `ok` | `ok` | curve source vs scorer | yes |

### F3: Without a heading source all three drift by metres; with the camera heading the UKF and FGO stay within 25 cm

- **Caption:** Left (m): position error, evo -a (cruise), without any heading source: the standard-sensor flights dsn_tex r1–r9 (bar = median) and the 6 forward-camera textured bags (fwdc / fwdplainc r1–r3) with their heading unused. No ordering is claimed: the pre-registered EKF3 − FGO test on r4–r10 gives 'no ordering claimed' (the former 'EKF3 beats the FGO' is WITHDRAWN); the UKF medians are descriptive (n = 9). Right (cm): the UKF and FGO with the camera heading on the same 6 bags: line-textured walls UKF 13–14, FGO 6 cm; plain walls UKF 15–25, FGO 9–22 cm (C0: FGO lower on 6/6, margin 3–6 cm on plain walls). On the plain-wall bags (checkerboard floor) the heading failed Phase 3 validation, so no heading benefit is claimed there (conditional on the initial yaw σ). Phase 5 decomposition (fwdc_tex): without heading the estimator's own heading error drives 3–46 m of end-of-cruise cross-track; with the heading ≤ 7 cm (checked against its JSON only; numbers.md has no row). evo -a aligns away a constant yaw offset, so it is metres, not tens of metres.
- **Inputs:** eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json; phase4_{fwdc,fwdplainc}_evo.json, cross-checked against phase4_*_arms.json; phase5_analysis.json (decomposition)
- **numbers.md rows:** §6.1, §6.4, §6.6; claims 1a, 1b, 2, 5, 7
- **Not cross-checkable:** Phase 5 decomposition magnitudes (caption only): JSON only, no numbers.md row (§6.3 'NOT RESTATED')

| check | computed | expected | source | match |
|---|---|---|---|---|
| dsn_tex mean r1–r3 EKF3 / UKF / FGO (m) | `4.00 / 3.59 / 3.44` | `4.00 / 3.59 / 3.44` | numbers.md §6.1; claim 1a | yes |
| dsn_tex UKF r1–r9 range (m) | `1.17–5.85` | `1.17–5.85` | numbers.md §6.1 D15 wording row | yes |
| confirmatory mean d, CI (m) | `-0.021 [-0.989, 0.947]` | `-0.021 [-0.989, 0.947]` | numbers.md §6.1 | yes |
| no heading EKF3 fwdc / fwdplainc r1–r3 (m) | `4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08` | `4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08` | numbers.md §6.4 | yes |
| no heading FGO fwdc / fwdplainc r1–r3 (m) | `4.47 / 2.26 / 4.54 / 4.54 / 4.52 / 4.74` | `4.47 / 2.26 / 4.54 / 4.54 / 4.52 / 4.74` | numbers.md §6.4 | yes |
| no heading UKF fwdc / fwdplainc r1–r3 (m) | `4.96 / 1.78 / 4.96 / 5.02 / 11.19 / 10.82` | `4.96 / 1.78 / 4.96 / 5.02 / 11.19 / 10.82` | numbers.md §6.4 | yes |
| with heading UKF fwdc / fwdplainc r1–r3 (m) | `0.13 / 0.13 / 0.14 / 0.19 / 0.15 / 0.25` | `0.13 / 0.13 / 0.14 / 0.19 / 0.15 / 0.25` | numbers.md §6.6 | yes |
| with heading FGO fwdc / fwdplainc r1–r3 (m) | `0.06 / 0.06 / 0.06 / 0.15 / 0.09 / 0.22` | `0.06 / 0.06 / 0.06 / 0.15 / 0.09 / 0.22` | numbers.md §6.6 | yes |
| phase4 evo vs arms json agreement (mismatches) | `0` | `0` | phase4_*_evo.json vs phase4_*_arms.json | yes |

### F4: On a blank floor nothing bounds position: the UKF and FGO dead-reckon away; EKF3 declares itself invalid

- **Caption:** Position error after the loss of flow aiding on the blank floor (UKF and FGO baselines; 11 flights: dsn, p1c, fwdc and fwdplainc blank), linear axis cut at +60 s: UKF 6.4–8.2 / 27.3–36.5 / 60–108 m and FGO 6.4–8.2 / 28.0–37.0 / 154–204 m at +10 / +30 / +60 s. Beyond +60 s both run away to km scale (end of cruise UKF 29–40 km, FGO 22–41 km, †: evidence of divergence with its order of magnitude, not bit-reproducible values), shown by the arrows rather than a log axis. EKF3 has no curve because its position is flagged invalid for the whole cruise (301–310 s) on every blank flight and its held-origin output is not scored (evaluation rule). Behaviour under total loss, not accuracy. With the camera heading the yaw is held but position still is not (+60 s UKF 40–89, FGO 135–190 m †; claim 10).
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

### F5: Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm

- **Caption:** Experiment T (room_tags, 5 laps of a 6 m square, open loop on simulator truth): horizontal RMSE in the world frame, no alignment, against the tags sent (A all 8, B the 4 corners, C 2 diagonal, D 1 tag; median gap between fixes 4.3 / 10.1 / 22.0 / 46.3 s). Solid, filled = live; dashed, open = hindsight (the FGO whole-flight batch and the RTS-smoothed UKF); small marks = each of 3 flights, line = their mean. Live errors grow from 2–4 cm to 8–13 cm as tags thin out; no live ordering is claimed (in D the FGO live 8.3 cm against EKF3 9.6 cm is descriptive, n = 3; ruling 7). P-T3 FAILS (live max/min 1.97 / 2.36 / 1.42 / 1.58). The FGO batch stays at 1.1–2.8 cm; its hindsight gain grows with the gap (H-T1 PASS), the RTS-UKF's does not (P-T2 FAIL), and the batch-to-RTS ratio is 1.31–3.89 (P-T4 FAIL). Same tag fixes for every estimator.
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

### F6: Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight cuts the error to 0.6 m

- **Caption:** Experiment O (outdoor → indoor → outdoor, open loop on simulator truth). Indoor sensor set, the same for all three estimators: IMU (accelerometer and gyro), downward optical flow and the downward LiDAR rangefinder only; no GNSS (switched off at the entrance), no compass, no forward-camera heading (descoped) and no tags (none in the world). Route: 15 m GNSS yaw-alignment run outdoors, then 0.5 m/s north through the entrance (GNSS OFF) to the far end 30 m inside (reached ~60 s after OFF), a 3 s hold, and back in reverse at the same heading (no yaw turn), re-crossing the entrance at GNSS ON (123 s indoors). Left: O_r1 horizontal error, world frame; EKF3 resets to GNSS on return with a 4.10 m jump (every flight). Right: indoor RMSE, 3 flights. H-O1 PASS 3/3 (FGO batch below both filters' live tracks); H-O2 FAIL (live max/min 1.72–1.84, EKF3 largest); P-O3 PASS (FGO batch 0.59 m = RTS-UKF 0.58–0.60 m within 1–5%). The former 'FGO batch ~2× better than the RTS-UKF' is WITHDRAWN (a noise-model artefact). Same GNSS samples for every estimator.
- **Inputs:** eval/results/expO/O_*.json; curves: O_r1 room_ukf/, room_fgo/ TUMs, dataflash XKF1 about EKF3's origin (gnss.npz), bag /imu/time_ref (clock map); route from markers_bag_s; design: METHODOLOGY 'Experiment O: pre-registration', sim/worlds/outdoor_indoor.sdf, fly_trial.py outback(), o_gnss.parm
- **numbers.md rows:** §16.2 table and bullets; claims 19–22

| check | computed | expected | source | match |
|---|---|---|---|---|
| O indoor RMSE EKF3 live (m) | `1.42–1.43` | `1.42–1.43` | numbers.md §16.2 table | yes |
| O indoor RMSE UKF live (m) | `0.77–0.84` | `0.77–0.84` | numbers.md §16.2 table | yes |
| O indoor RMSE FGO live (m) | `0.83–0.89` | `0.83–0.89` | numbers.md §16.2 table | yes |
| O indoor RMSE RTS-UKF (hindsight) (m) | `0.58–0.60` | `0.58–0.60` | numbers.md §16.2 table | yes |
| O indoor RMSE FGO batch (hindsight) (m) | `0.59–0.59` | `0.59–0.59` | numbers.md §16.2 table | yes |
| O EKF3 reset jump (m) | `4.10–4.10` | `4.10–4.10` | numbers.md §16.2 ('4.10 m, every flight') | yes |
| O indoor duration (s) | `123` | `123` | numbers.md §16.2 heading ('123 s, GNSS off') | yes |
| O_r1 curve indoor RMSE recomputed vs json, max |Δ| <= 0.05 m | `ok` | `ok` | curve source vs scorer | yes |
| O_r1 bag has no tag topics | `0` | `0` | O design: no tags in outdoor_indoor.sdf | yes |

### F7: Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps

- **Caption:** Experiment L: the keyframe FGO with AprilTags at UNKNOWN positions (each tag a landmark), T_A_r1–r3, horizontal RMSE per 6 m lap in the first tag's frame, one shared linear axis. Left: with loop closure the live error falls after lap 1 (lap 5 ÷ lap 1 0.16–0.43; overall 4.9–7.6 cm live, 1.7–2.7 cm hindsight). Right: without re-identification it grows 2.9–4.5× over five laps (overall 26.2–36.1 cm live). H-L1, H-L2, H-L3 and P-L4 PASS 3/3. This is an FGO capability, not an FGO-against-filter result (the filters have no loop-closure equivalent); one estimator, so one colour, with live solid/filled and hindsight dashed/open. V-L is not re-scorable on the corrected FGO (ruling 6).
- **Inputs:** eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m)
- **numbers.md rows:** §16.3 table and bullets; claims 23, 24

| check | computed | expected | source | match |
|---|---|---|---|---|
| L lc live overall (m) | `0.049–0.076` | `0.049–0.076` | numbers.md §16.3 | yes |
| L lc hindsight overall (m) | `0.017–0.027` | `0.017–0.027` | numbers.md §16.3 | yes |
| L nolc live overall (m) | `0.263–0.361` | `0.262–0.361` | numbers.md §16.3 | yes (last-digit rounding) |
| L nolc hindsight overall (m) | `0.221–0.266` | `0.221–0.266` | numbers.md §16.3 | yes |
| L lap5/lap1 lc live; nolc live | `0.16–0.43; 2.9–4.5` | `0.16–0.43; 2.9–4.5` | numbers.md §16.3 | yes |

### F8: Holding on a wall tag, every flying estimator drifts at most ~3 cm while the tag is hidden, inside every band

- **Caption:** Experiment H (marker-relative hold on a wall tag, forward camera), FLYING estimators only: the drift at re-acquisition after each tag loss (5, 15, 30 s in the hover; ~7 s during a move), each mark one loss in one flight, EFFECTIVE metric (last fix → first returning fix; the end-of-loss metric of numbers.md §17.1 differs by ≤ 5 mm). EKF3 = S1 near-spawn (r1–r3) and S1 far-spawn (r1, r2, r3b; METHODOLOGY only, no numbers.md row); UKF = the jitter-corrected port (S2v2); FGO = the final C++ node (S3v2, flown with the OLD FGO priors). Pre-registered bands (P-H5): EKF3 and FGO ≤ 50 / 100 / 200 / 150 mm, UKF ≤ 100 / 200 / 400 / 300 mm; bands above the 60 mm axis are shown as arrows with their value. Every loss is inside its band and no estimator locked out (P-H5, P-H7 PASS). The comparative criteria (H-H2, P-H3, H-H4) FAIL as adjudicated, with the same verdicts on these re-flown sets (PENDING a ruling). Each estimator flew its own flights: pairing by run index, not trajectory.
- **Inputs:** eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s3v2_r*.json (losses[*].<est>.effective.drift_m, drift_end_m, lockout)
- **numbers.md rows:** §17 (S1 table, P-H5, P-H7), §17.1 (S2v2, S3v2), §17.2; claims 25, 26
- **Not cross-checkable:** S1-far EKF3 drifts (3 of the 6 EKF3 flights): METHODOLOGY only, no numbers.md row

| check | computed | expected | source | match |
|---|---|---|---|---|
| S1 EKF3 flying drift 5/15/30/move (mm, effective) | `13–27 | 6–25 | 3–11 | 7–31` | `13–27 | 6–25 | 3–11 | 7–31` | numbers.md §17 table | yes |
| S2v2 UKF flying end-of-loss drift r1/r2/r3 (mm) | `5/7/8 | 19/7/26 | 6/10/10 | 26/4/5` | `5/7/8 | 19/7/26 | 6/10/10 | 26/4/5` | numbers.md §17.1 table | yes |
| S3v2 FGO flying end-of-loss drift r1/r2/r3 (mm) | `13/20/17 | 7/25/27 | 22/15/9 | 17/11/18` | `13/20/17 | 7/25/27 | 22/15/9 | 17/11/18` | numbers.md §17.1 table | yes |
| effective vs end-of-loss drift, max |Δ| at printed (mm) precision | `≤ 5 mm` | `≤ 5 mm` | numbers.md §17.1 ('differ by ≤ 5 mm'); unrounded 5.1 mm (S2v2 r1, move loss) | yes |
| every plotted drift inside its pre-registered band (P-H5) | `True` | `True` | numbers.md §17, §17.1 (every band PASSES) | yes |
| lockouts in any loss | `0` | `0` | numbers.md §17 (P-H7 PASS) | yes |

### A1: Closed loop: every flown build against B1–B5 and the contact window

- **Caption:** Pass/fail of every closed-loop corridor set (replaces pack F15a), computed from the closed-loop score files, with the build ablations labelled: UKF v1 (pre-jitter fix) against v2 (final); FGO original, robust, v2 (noise fix only, ABLATION) and v3 (final, OLD priors).
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

### A2: H hold sets and the safety tests (all runs)

- **Caption:** Experiment H sets (S1, S1 far, S2/S2v2, S3/S3v2) with hold error, drift, lockouts and the P-H5 bands, and every safety-test run with its as-worded verdict, including the v3 (UKF) and v4 (FGO, NEW priors) re-tests (replaces pack F15b).
- **Inputs:** eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json, safety_*.json
- **numbers.md rows:** §15 safety rows, §17, §17.1; METHODOLOGY 2d and 'Band C … FGO safety re-tests'

| check | computed | expected | source | match |
|---|---|---|---|---|
| S2 / S2v2 / S3 / S3v2 hold window means (mm) | `4.9–6.3 ; 6.1–7.4 ; 7.6–8.2 ; 8.1–9.0` | `4.9–6.3 ; 6.1–7.4 ; 7.6–8.2 ; 8.1–9.0` | numbers.md §17.1 table | yes |
| lockouts S1 / S1far / S2v2 / S3v2 | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | numbers.md §17, §17.1 | yes |
| UKF (b) v2 / v3 S-A2 delay (s), verdict | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | numbers.md §15 safety row (v2); METHODOLOGY 2d (v3) | yes |
| UKF (a) v2 / v3 verdict | `ALL PASS / ALL PASS` | `ALL PASS / ALL PASS` | numbers.md §15 (v2); METHODOLOGY rulings 2026-10-11 item 3 (v3) | yes |
| FGO (a) v3 S-A2 / disp; (b) v3 | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | numbers.md §15 safety row | yes |
| FGO (a) v4 S-A2 / disp; (b) v4 | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS' | yes |
| FGO v4 a / b verdict | `ALL PASS / ALL PASS` | `ALL PASS / ALL PASS` | METHODOLOGY (v4: S-A1–S-A4 PASS as worded) | yes |
| FGO v2 ablation a / b: S-A2 s, disp m | `0.29 s, 0.78 m; 0.43 s, 1.27 m` | `0.29 s, 0.78 m; 0.43 s, 1.27 m` | numbers.md §15 history row | yes |
| history: UKF a rerun / UKF b / FGO a / FGO b2 disp (m); UKF b S-A2 (s) | `0.42 / 0.28 / 0.37 / 1.25; 4.81` | `0.42 / 0.28 / 0.37 / 1.25; 4.81` | numbers.md §15 history row | yes |
| FGO (b) first run S-A3; UKF (a) first run S-A2 / S-A3 | `False; False / False` | `False; False / False` | numbers.md §15 history row (S-A3 FAIL; S-A2 FAIL as worded, S-A3 FAIL) | yes |
| EKF3 reference drift (m) | `1.40` | `1.40` | numbers.md §15 history row | yes |

### A3: F1, the L compute cost and the build ablations

- **Caption:** Pass/fail table for the F1 robust-weighting test (replaces pack F07), the L compute cost (diagnostic, replaces F13; linear values, no plot) and the build ablations: UKF v1 against v2; FGO v2 (noise fix only) against v3 (final) and the v4 node; the flown-FGO OLD-priors note.
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

