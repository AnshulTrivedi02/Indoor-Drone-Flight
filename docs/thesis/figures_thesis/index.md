# Thesis figures and tables: index (revision 2026-10-16; thesis numbering and names 2026-10-17)

Built by `eval/figs_thesis.py` at commit `d5da93a` (run with `/home/makerspace/venv-evo/bin/python`; plotting and tabulating only, no number recomputed). Combined PDF for the supervisor (in thesis order: chapter by chapter, figures before tables, then the appendix): `docs/thesis/figures_thesis/thesis_figures_combined.pdf`. Figures are here as `.pdf` and `.png`; tables are in `docs/thesis/tables/` as LaTeX (`.tex`, booktabs; NOT compiled on the build machine, which has no TeX: checked for ASCII, balanced braces and the column count of every row), markdown (`.md`) and a rendered page (`.png`). The frozen pack (`docs/thesis/final_results_pack.pdf`, `eval/figs_final_pack.py`) is untouched.

**Thesis numbering and names (2026-10-17).** Captions, titles, headers, cells and notes use the thesis vocabulary (`docs/thesis/thesis_vocabulary.md`): experiments 1–5 (1A/1B/1C, 5S), hypotheses H1.1–H5.7 (with C1.a and V3), criteria named in words, and the numbering by chapter of its §6 (Figure n.m, Table n.m, appendix Table A.m). **The output file names keep the internal ids** (F2, T1 … T8, A1 … A3), as §6 specifies ("The repository files keep their names. Only the printed captions take the new numbers."); the LaTeX `\label{tab:Tn}` keys also keep them. The appendix mapping at the end of this index leads from every thesis number and name back to the internal id or code and the output file. The Inputs, numbers.md rows and the check sources below are the data statement: they keep the record's own codes so each value can be found in the record.

**Revision 2026-10-16.** F1 (`F1_scorecard`) became table T1 (now Table 7.1); F3 (`F3_accuracy_without_and_with_heading`) became table T2 (now Table 4.1); F4 (`F4_blank_floor_flow_loss`) became table T3 (now Table 4.2); F8 (`F8_H_tag_loss_drift`) became table T5 (now Table 6.1). The old figure files are removed from this folder; they remain in the git history (commit `7778cd6`, `git show 7778cd6:docs/thesis/figures_thesis/<name>.png`). F2 (Figure 4.1) is now one panel (the heading-error panel moved to Table 4.3); F6 (Figure 5.3) is the time trace only (the per-flight RMSE moved to Table 5.1); F5 and F7 are unchanged. T7 (Table 7.2, failure behaviour) and T8 (Table 5.2, hindsight ratio) are new.

**Added 2026-10-17: F9, PROVISIONAL label "Figure 4.1b (provisional)"** (heading error against time on the same closed-loop flights as Figure 4.1, with a linear inset of the with-heading flights). By user ruling no figure or table is renumbered now: every existing number is unchanged, and the final number is assigned once, after the chapter plan is locked. The provisional label sorts directly after Figure 4.1. Note: the results-chapter trajectory figure R3 (`eval/figs_thesis_results.py`, `index_results.md`) also proposes "Figure 4.2" provisionally; both are resolved in that final numbering pass.

**Colour mapping (Okabe–Ito, colour-blind safe; fixed across every figure):** EKF3 #0072B2 (blue, circle) · UKF #009E73 (bluish green, triangle) · FGO #D55E00 (vermilion, square) · truth / references #999999 (grey). Solid lines / filled marks = live; dashed lines / open marks = hindsight. No log axes anywhere.

**Scorecard labels (Table 7.1; ruling 2026-10-17):** an ordering label (BEST / BEHIND / TIED) is printed only where a pre-registered decision rule was met; no comparison in the scorecard met one, so none is printed and the cells give the numbers and the verdict they rest on. Status words, not orderings: FAILED = does not bound position; PASSED = met its pre-registered criteria with no comparison (Experiment 3, FGO only); N/A = not run.

**Ordering footnotes (2026-10-17).** Every place a table or caption claims, or declines to claim, an ordering carries a lettered footnote ([a], [b], …) giving the metric and unit, n with its unit of replication, the pre-registered rule with its source line (each cited line is read at build time and checked to contain the quoted phrase; those checks are in the lists below as 'rule text …') and the result against the rule. Tables carry them as notes below the table; figures carry them below the caption (here as *Footnote* lines, and on the caption page of the combined PDF). Ordering verdicts used in the footnotes: RULE MET = a pre-registered rule was applied and met, so its ordering (or similarity) is claimed; case (i) TEST RUN, RULE NOT MET = a pre-registered decision rule with a 'no ordering' outcome was applied and gave that outcome; case (ii) FAILED AS WORDED = a pre-registered prediction of an ordering or a similarity was scored literally and is false, which does not by itself establish the opposite ordering; case (iii) NO COMPARATIVE TEST REGISTERED = values are descriptive. n always names its unit (flights, bags, losses). Definitions: `docs/thesis/thesis_vocabulary.md` §11 and `docs/thesis/methodology_definitions_draft.md` ('n' and 'Ordering verdicts').

| thesis no. | internal id | kind | files | title | status | checks | log-scale handling |
|---|---|---|---|---|---|---|---|
| Figure 4.1 | F2 | figure | `F2_heading_stops_sideways_drift.png`, `F2_heading_stops_sideways_drift.pdf` | The camera heading stops the sideways drift: without it every estimator flies into the west wall | CURRENT | 13/13 | none needed |
| Figure 4.1b (provisional) | F9 | figure | `F9_heading_error_closed_loop.png`, `F9_heading_error_closed_loop.pdf` | Without a heading source the heading error grows until the wall; with the camera heading it stays near zero | CURRENT | 23/23 | none needed |
| Table 4.1 | T2 | table | `T2_accuracy_heading.md`, `T2_accuracy_heading.tex`, `T2_accuracy_heading.png` | Position error without and with the camera heading (textured floor) | CURRENT | 26/26 | none needed (table) |
| Table 4.2 | T3 | table | `T3_blank_floor.md`, `T3_blank_floor.tex`, `T3_blank_floor.png` | Blank floor: position error after the loss of flow aiding | CURRENT | 8/8 | none needed (table) |
| Table 4.3 | T4 | table | `T4_closed_loop.md`, `T4_closed_loop.tex`, `T4_closed_loop.png` | Closed loop at half real-time (RTF 0.5): the final build of each estimator flying the vehicle | CURRENT | 17/17 | none needed (table) |
| Figure 5.1 | F5 | figure | `F5_T_tags_known_positions.png`, `F5_T_tags_known_positions.pdf` | Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm | CURRENT | 17/17 | none needed |
| Figure 5.2 | F7 | figure | `F7_L_loop_closure.png`, `F7_L_loop_closure.pdf` | Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps | CURRENT | 10/10 | none needed |
| Figure 5.3 | F6 | figure | `F6_O_outdoor_indoor.png`, `F6_O_outdoor_indoor.pdf` | Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight keeps the error near 1 m | CURRENT | 15/15 | none needed |
| Table 5.1 | T6 | table | `T6_O_indoor_rmse.md`, `T6_O_indoor_rmse.tex`, `T6_O_indoor_rmse.png` | Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off) | CURRENT | 14/14 | none needed (table) |
| Table 5.2 | T8 | table | `T8_hindsight_ratio.md`, `T8_hindsight_ratio.tex`, `T8_hindsight_ratio.png` | Hindsight: the FGO whole-flight batch against the smoothed UKF | CURRENT | 9/9 | none needed (table) |
| Table 6.1 | T5 | table | `T5_H_tag_loss_drift.md`, `T5_H_tag_loss_drift.tex`, `T5_H_tag_loss_drift.png` | Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators | CURRENT | 20/20 | none needed (table) |
| Table 7.1 | T1 | table | `T1_scorecard.md`, `T1_scorecard.tex`, `T1_scorecard_p1.png`, `T1_scorecard_p2.png`, `T1_scorecard_p3.png` | Which estimator wins where (scorecard of the restated verdicts) | CURRENT | 66/66 | none needed (table) |
| Table 7.2 | T7 | table | `T7_failure_behaviour.md`, `T7_failure_behaviour.tex`, `T7_failure_behaviour_p1.png`, `T7_failure_behaviour_p2.png` | Failure behaviour: blank-floor validity, the Experiment 4 return jump and the 5S safety tests | CURRENT | 21/21 | none needed (table) |
| Table A.1 | A1 | appendix | `A1_closed_loop_builds.png`, `A1_closed_loop_builds.pdf` | Closed loop: every flown build against the five closed-loop criteria and the contact window | CURRENT | 9/9 | none needed (table) |
| Table A.2 | A2 | appendix | `A2_H_and_safety_p1.png`, `A2_H_and_safety_p1.pdf`, `A2_H_and_safety_p2.png`, `A2_H_and_safety_p2.pdf`, `A2_H_and_safety_p3.png`, `A2_H_and_safety_p3.pdf` | Experiment 5 hold sets and the 5S safety tests (all runs) | CURRENT | 47/47 | none needed (table) |
| Table A.3 | A3 | appendix | `A3_F1_cost_ablations_p1.png`, `A3_F1_cost_ablations_p1.pdf`, `A3_F1_cost_ablations_p2.png`, `A3_F1_cost_ablations_p2.pdf` | The robust-weighting test (H1.4), the Experiment 3 compute cost and the build ablations | CURRENT | 11/11 | none needed (table) |

**Total: 326/326 checks match** (a check repeated in two items is counted in each). **EXACT comparison** (ruling 2026-10-16): the computed string is the stored full-precision value rounded once by `rd()` (half away from zero) at the printed precision, and it must equal the expected string character for character; no tolerance, no last-digit acceptance.

## Captions, sources and checks

### Figure 4.1 (internal F2, figure): The camera heading stops the sideways drift: without it every estimator flies into the west wall

- **Caption:** Textured corridor at half real-time (RTF 0.5; the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s), each estimator flying the vehicle (closed loop); true paths from the simulator, top-down, with the lateral (East) axis stretched 3.0× (stated on the figure). Colour = the flying estimator. Dashed: without a heading source (1 flight each), drawn up to the wall contact (X): EKF3 +242.1 s (after its pre-registered window), UKF +165.9 s, FGO +169.9 s. Solid: with the camera heading (3 flights each); all 9 stay within 0.39 m of the centreline and pass all five closed-loop criteria (mission completion and the cross-track, heading-error, lateral-speed and oscillation bounds), so they overlap on the centreline at this scale; no ordering between the estimators is claimed [a]. Heading-error statistics are in Table 4.3; the heading error over time, the cause of this drift, is in Figure 4.1b (provisional). Builds: the final UKF port (jitter-corrected) and the final FGO node (flown with the original FGO priors); earlier builds are in Table A.1. n = 1 flight per estimator without heading; closed-loop run-to-run variability is unmeasured; no comparison across real-time factors.
  - *Footnote:* [a] Ordering basis, Experiment 1C closed loop, EKF3, final UKF port and final FGO node. Metric: without heading: wall-contact time after cruise start against each estimator's own contact window, s; with heading: pass/fail of the five closed-loop criteria and the estimator-validity criterion, with max |cross-track| in cruise (m), heading error p95 and max (°) and max lateral speed (m/s). n = 1 flight per estimator without heading and 3 flights per estimator with heading (each estimator flew its own flights: separate, unpaired flights). Rule: per-estimator criteria only (H1.8 contact window and H1.9 the five criteria; METHODOLOGY.md:4948, METHODOLOGY.md:7513, METHODOLOGY.md:8995, METHODOLOGY.md:4951, METHODOLOGY.md:4966, METHODOLOGY.md:7362); no comparative test between the estimators was pre-registered, and the comparison across the with-heading sets is 'DESCRIPTIVE; separate flights, n = 3 each, no ordering claim' (METHODOLOGY.md:9355). Result: with heading 3/3 / 3/3 / 3/3 flights pass (EKF3 / UKF / FGO); max cross-track 0.24–0.33 / 0.22–0.25 / 0.03–0.39 m. Verdict: case (iii), NO COMPARATIVE TEST REGISTERED: values are descriptive.
  - *Footnote:* Ordering verdicts used in the footnotes: RULE MET = a pre-registered rule was applied and met, so its ordering (or similarity) is claimed; case (i) TEST RUN, RULE NOT MET = a pre-registered decision rule with a 'no ordering' outcome was applied and gave that outcome; case (ii) FAILED AS WORDED = a pre-registered prediction of an ordering or a similarity was scored literally and is false, which does not by itself establish the opposite ordering; case (iii) NO COMPARATIVE TEST REGISTERED = values are descriptive. n always names its unit (flights, bags, losses).
- **Inputs:** paths: dataflash SIM of cl_a_tex_half, cl_bcpp_tex_r1–r3_half, cl_ukf_a_tex_half_v2, cl_ukf_b_tex_r1–r3_half_v2, cl_fgo_a_tex_half_v3, cl_fgo_b_tex_r1–r3_half_v3; contact and B2: eval/results/closed_loop_<trial>.json
- **numbers.md rows:** §15 (contact rows, B2 row, re-flown B1/B2/B4 rows); claim 14

| check | computed | expected | source | match |
|---|---|---|---|---|
| no-heading wall contact EKF3 / final UKF port / final FGO node (s) | `+242.1 / +165.9 / +169.9` | `+242.1 / +165.9 / +169.9` | numbers.md §15 contact rows | yes |
| with heading, max cross-track per estimator EKF3 / final UKF port / final FGO node (m) | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | numbers.md §15 B2 row (EKF3 half) and re-flown rows | yes |
| plotted with-heading paths: max |x| in cruise vs scored max cross-track, all 9 flights, |Δ| <= 0.05 m | `ok` | `ok` | curve source (dataflash SIM) vs closed_loop_*.json B2 | yes |
| plotted no-heading paths end at the scored contact point, all 3, |Δ| <= 0.5 m | `ok` | `ok` | curve source (dataflash SIM, cut at cruise start + contact time) vs closed_loop_*.json contact | yes |
| closed loop, half real-time, with heading: flights passing all five criteria (+ estimator validity) | `3/3 / 3/3 / 3/3` | `3/3 / 3/3 / 3/3` | numbers.md §15 | yes |
| closed loop, half real-time, with heading: max cross-track range EKF3 / final UKF port / final FGO node (m) | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | numbers.md §15 B2 row (EKF3 half) and re-flown rows | yes |
| rule text METHODOLOGY.md:4948 contains the quoted phrase | `[+155, +215] s` | `[+155, +215] s` | METHODOLOGY.md:4948 (read at build time) | yes |
| rule text METHODOLOGY.md:7513 contains the quoted phrase | `[+146, +218] s` | `[+146, +218] s` | METHODOLOGY.md:7513 (read at build time) | yes |
| rule text METHODOLOGY.md:8995 contains the quoted phrase | `[+145, +196] s` | `[+145, +196] s` | METHODOLOGY.md:8995 (read at build time) | yes |
| rule text METHODOLOGY.md:4951 contains the quoted phrase | `B1.` | `B1.` | METHODOLOGY.md:4951 (read at build time) | yes |
| rule text METHODOLOGY.md:4966 contains the quoted phrase | `B5.` | `B5.` | METHODOLOGY.md:4966 (read at build time) | yes |
| rule text METHODOLOGY.md:7362 contains the quoted phrase | `S2 is the estimator valid throughout` | `S2 is the estimator valid throughout` | METHODOLOGY.md:7362 (read at build time) | yes |
| rule text METHODOLOGY.md:9355 contains the quoted phrase | `DESCRIPTIVE; separate flights, n = 3 each, no ordering claim` | `DESCRIPTIVE; separate flights, n = 3 each, no ordering claim` | METHODOLOGY.md:9355 (read at build time) | yes |

### Figure 4.1b (provisional) (internal F9, figure): Without a heading source the heading error grows until the wall; with the camera heading it stays near zero

- **Caption:** Heading error of the flying estimator (its own current yaw minus the simulator's true yaw; EKF3 from its logged state, the UKF and the FGO from their current-time outputs, the values the controller received) against time since cruise start, on the same closed-loop flights as Figure 4.1: textured corridor at half real-time (RTF 0.5; the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s). Colour = the flying estimator. Dashed (here: without heading, not hindsight): without a heading source (1 flight each), drawn to the wall contact (X): EKF3 +242.1 s (after its pre-registered window [+155, +215] s; numbers.md:470), UKF +165.9 s, FGO +169.9 s. Solid: with the camera heading (3 flights each). Mechanism: the controller flies the commanded path in the estimator's frame, so a heading error turns the forward motion by that angle and adds a sideways velocity of the flight speed times its sine; a positive error (estimate clockwise of truth) turns the vehicle west, and integrated over the cruise this is the westward drift into the wall in Figure 4.1. With the camera heading all 9 flights stay within a heading error p95 of 0.38° and a maximum of 0.68° (Table 4.3), inside the heading-error bound (p95 ≤ 1.0°, max ≤ 2.0°; grey band ±2.0°), so on the main axis their lines lie on zero; the inset (linear, y-axis ±1°, the same time axis) shows them alone. No ordering between the estimators is claimed [a]. Builds: the final UKF port and the final FGO node (original FGO priors), as in Figure 4.1. n = 1 flight per estimator without heading; closed-loop run-to-run variability is unmeasured; no comparison across real-time factors.
  - *Footnote:* [a] Ordering basis, Experiment 1C closed loop, EKF3, final UKF port and final FGO node. Metric: without heading: wall-contact time after cruise start against each estimator's own contact window, s; with heading: pass/fail of the five closed-loop criteria and the estimator-validity criterion, with max |cross-track| in cruise (m), heading error p95 and max (°) and max lateral speed (m/s). n = 1 flight per estimator without heading and 3 flights per estimator with heading (each estimator flew its own flights: separate, unpaired flights). Rule: per-estimator criteria only (H1.8 contact window and H1.9 the five criteria; METHODOLOGY.md:4948, METHODOLOGY.md:7513, METHODOLOGY.md:8995, METHODOLOGY.md:4951, METHODOLOGY.md:4966, METHODOLOGY.md:7362); no comparative test between the estimators was pre-registered, and the comparison across the with-heading sets is 'DESCRIPTIVE; separate flights, n = 3 each, no ordering claim' (METHODOLOGY.md:9355). Result: with heading 3/3 / 3/3 / 3/3 flights pass (EKF3 / UKF / FGO); max cross-track 0.24–0.33 / 0.22–0.25 / 0.03–0.39 m. Verdict: case (iii), NO COMPARATIVE TEST REGISTERED: values are descriptive.
  - *Footnote:* Ordering verdicts used in the footnotes: RULE MET = a pre-registered rule was applied and met, so its ordering (or similarity) is claimed; case (i) TEST RUN, RULE NOT MET = a pre-registered decision rule with a 'no ordering' outcome was applied and gave that outcome; case (ii) FAILED AS WORDED = a pre-registered prediction of an ordering or a similarity was scored literally and is false, which does not by itself establish the opposite ordering; case (iii) NO COMPARATIVE TEST REGISTERED = values are descriptive. n always names its unit (flights, bags, losses).
- **Inputs:** curves: dataflash XKF1 (core 0) / XUKO / XFGO and SIM, and bag /imu/time_ref (clock map), of cl_a_tex_half, cl_bcpp_tex_r1–r3_half, cl_ukf_a_tex_half_v2, cl_ukf_b_tex_r1–r3_half_v2, cl_fgo_a_tex_half_v3, cl_fgo_b_tex_r1–r3_half_v3; cruise window, contact, B3 and clock_map: eval/results/closed_loop_<trial>.json; heading-error bound: METHODOLOGY.md:4958
- **numbers.md rows:** §15 (contact rows, B3 row, re-flown B3 row); claim 14
- **Not cross-checkable:** the curves themselves are read from the flight records, not numbers.md rows; they are checked against the stored B3 p95/max, clock map and contact times (the 'ok' checks)

| check | computed | expected | source | match |
|---|---|---|---|---|
| no-heading wall contact EKF3 / final UKF port / final FGO node (s) | `+242.1 / +165.9 / +169.9` | `+242.1 / +165.9 / +169.9` | numbers.md §15 contact rows | yes |
| EKF3 no-heading contact at half real-time against its pre-registered window | `+242.1 (MISS), window [+155, +215]` | `+242.1 (MISS), window [+155, +215]` | numbers.md:470 ('+186.2 (PASS, window [+155, +215]) / +242.1 (MISS, D21)') | yes |
| rule text numbers.md:470 contains the quoted phrase | `window [+155, +215]` | `window [+155, +215]` | docs/thesis/numbers.md:470 (read at build time) | yes |
| rule text numbers.md:470 contains the quoted phrase | `+242.1 (MISS, D21)` | `+242.1 (MISS, D21)` | docs/thesis/numbers.md:470 (read at build time) | yes |
| with heading, all 9 flights: max of the heading error p95 / max of the heading error max (deg) | `0.38 / 0.68` | `0.38 / 0.68` | numbers.md §15 re-flown B3 row (final UKF port r1 p95 0.382; final FGO node r3 max 0.682) and B3 row (EKF3 half 0.28–0.32 / 0.33–0.39); Table 4.3 | yes |
| final UKF port heading error p95/max/mean per flight (deg) | `0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250` | `0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250` | numbers.md §15 re-flown B3 row | yes |
| final FGO node heading error p95/max/mean per flight (deg) | `0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187` | `0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187` | numbers.md §15 re-flown B3 row | yes |
| EKF3 half real-time heading error p95 / max range (deg) | `0.28–0.32/0.33–0.39` | `0.28–0.32/0.33–0.39` | numbers.md §15 B3 row | yes |
| rule text METHODOLOGY.md:4958 contains the quoted phrase | `95th percentile ≤ 1.0°, maximum ≤ 2.0°` | `95th percentile ≤ 1.0°, maximum ≤ 2.0°` | METHODOLOGY.md:4958 (read at build time) | yes |
| flights plotted: without / with heading, per estimator | `EKF3 1/3 / UKF 1/3 / FGO 1/3` | `EKF3 1/3 / UKF 1/3 / FGO 1/3` | numbers.md §15 (n = 1 per no-heading cell; 3 flights per heading set) | yes |
| plotted with-heading curves: |heading error| p95 and max in the stored cruise window vs stored B3, all 9 flights, |Δ| <= 0.001° | `ok` | `ok` | curve source (dataflash, read here) vs closed_loop_*.json B3 | yes |
| clock map rebuilt from /imu/time_ref vs stored clock_map, all 12 flights (rate ppm/1000 and offset ms), |Δ| <= 1e-6 | `ok` | `ok` | closed_loop_*.json clock_map | yes |
| plotted no-heading curves end within 0.1 s of the stored contact time, all 3 | `ok` | `ok` | curve source vs closed_loop_*.json contact.t_rel_cruise_s | yes |
| no-heading: drift side implied by the heading-error sign at contact (positive = estimate clockwise of truth, so the vehicle turns west) vs the stored contact wall | `west / west / west` | `west / west / west` | closed_loop_*.json contact.wall | yes |
| closed loop, half real-time, with heading: flights passing all five criteria (+ estimator validity) | `3/3 / 3/3 / 3/3` | `3/3 / 3/3 / 3/3` | numbers.md §15 | yes |
| closed loop, half real-time, with heading: max cross-track range EKF3 / final UKF port / final FGO node (m) | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | numbers.md §15 B2 row (EKF3 half) and re-flown rows | yes |
| rule text METHODOLOGY.md:4948 contains the quoted phrase | `[+155, +215] s` | `[+155, +215] s` | METHODOLOGY.md:4948 (read at build time) | yes |
| rule text METHODOLOGY.md:7513 contains the quoted phrase | `[+146, +218] s` | `[+146, +218] s` | METHODOLOGY.md:7513 (read at build time) | yes |
| rule text METHODOLOGY.md:8995 contains the quoted phrase | `[+145, +196] s` | `[+145, +196] s` | METHODOLOGY.md:8995 (read at build time) | yes |
| rule text METHODOLOGY.md:4951 contains the quoted phrase | `B1.` | `B1.` | METHODOLOGY.md:4951 (read at build time) | yes |
| rule text METHODOLOGY.md:4966 contains the quoted phrase | `B5.` | `B5.` | METHODOLOGY.md:4966 (read at build time) | yes |
| rule text METHODOLOGY.md:7362 contains the quoted phrase | `S2 is the estimator valid throughout` | `S2 is the estimator valid throughout` | METHODOLOGY.md:7362 (read at build time) | yes |
| rule text METHODOLOGY.md:9355 contains the quoted phrase | `DESCRIPTIVE; separate flights, n = 3 each, no ordering claim` | `DESCRIPTIVE; separate flights, n = 3 each, no ordering claim` | METHODOLOGY.md:9355 (read at build time) | yes |

### Table 4.1 (internal T2, table): Position error without and with the camera heading (textured floor)

- **Caption:** Without a heading source all three drift by metres and no ordering is claimed [a, b, d]; with the camera heading the UKF and the FGO stay within 0.25 m, the FGO lower on all 6 bags (C1.a) [c]. The heading-error decomposition of sideways drift attributes metres of the cross-track to each estimator's own heading error without the heading, and centimetres with it.
- **Inputs:** eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json; phase4_{fwdc,fwdplainc}_evo.json, cross-checked against phase4_*_arms.json; phase5_analysis.json (decomposition, xtrack_head_m)
- **numbers.md rows:** §6.1, §6.3 (Phase 5 decomposition), §6.4, §6.6; claims 1a, 1b, 2, 5, 7

| check | computed | expected | source | match |
|---|---|---|---|---|
| |heading-driven cross-track|, textured-wall camera dataset, textured floor, flights 1/2/3, EKF3 | UKF | FGO without heading (m) | `36.276 / 29.508 / 36.070 | 45.980 / 3.171 / 46.120 | 41.002 / 8.630 / 42.121` | `36.276 / 29.508 / 36.070 | 45.980 / 3.171 / 46.120 | 41.002 / 8.630 / 42.121` | numbers.md §6.3 Phase 5 decomposition row | yes |
| |heading-driven cross-track|, textured-wall camera dataset, textured floor, flights 1/2/3, UKF | FGO with heading (m) | `0.065 / 0.064 / 0.068 | 0.065 / 0.063 / 0.067` | `0.065 / 0.064 / 0.068 | 0.065 / 0.063 / 0.067` | numbers.md §6.3 Phase 5 decomposition row | yes |
| standard-sensor dataset, textured floor, median of flights 1–9, EKF3 / UKF / FGO (m) | `4.10 / 5.13 / 4.46` | `4.10 / 5.13 / 4.46` | numbers.md §6.1 standing row | yes |
| standard-sensor dataset, textured floor, mean of flights 1–3, EKF3 / UKF / FGO (m) | `4.00 / 3.59 / 3.44` | `4.00 / 3.59 / 3.44` | numbers.md §6.1; claim 1a | yes |
| standard-sensor dataset, textured floor, UKF flights 1–9 range (m) | `1.17–5.85` | `1.17–5.85` | numbers.md §6.1 D15 wording row | yes |
| H1.1 confirmatory mean d, CI (m) | `-0.021 [-0.989, 0.947]` | `-0.021 [-0.989, 0.947]` | numbers.md §6.1 | yes |
| no heading EKF3 textured-wall / plain-wall camera datasets, flights 1–3 (m) | `4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08` | `4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08` | numbers.md §6.4 | yes |
| no heading FGO textured-wall / plain-wall camera datasets, flights 1–3 (m) | `4.47 / 2.26 / 4.54 / 4.54 / 4.52 / 4.74` | `4.47 / 2.26 / 4.54 / 4.54 / 4.52 / 4.74` | numbers.md §6.4 | yes |
| no heading UKF textured-wall / plain-wall camera datasets, flights 1–3 (m) | `4.96 / 1.78 / 4.96 / 5.02 / 11.19 / 10.82` | `4.96 / 1.78 / 4.96 / 5.02 / 11.19 / 10.82` | numbers.md §6.4 | yes |
| with heading UKF textured-wall / plain-wall camera datasets, flights 1–3 (m) | `0.13 / 0.13 / 0.14 / 0.19 / 0.15 / 0.25` | `0.13 / 0.13 / 0.14 / 0.19 / 0.15 / 0.25` | numbers.md §6.6 | yes |
| with heading FGO textured-wall / plain-wall camera datasets, flights 1–3 (m) | `0.06 / 0.06 / 0.06 / 0.15 / 0.09 / 0.22` | `0.06 / 0.06 / 0.06 / 0.15 / 0.09 / 0.22` | numbers.md §6.6 | yes |
| 1B offline fusion: evo vs arms result files agreement (mismatches) | `0` | `0` | phase4_*_evo.json vs phase4_*_arms.json | yes |
| H1.1: flights in the test / usable for the FGO | `7 / 6` | `7 / 6` | numbers.md §6.1 confirmatory row ('r4–r10 … r10 unusable for FGO') | yes |
| H1.1: flights with d < 0 (EKF3 lower), of all flights | `5/7` | `5/7` | numbers.md §6.1 confirmatory row ('d < 0 on 5/7') | yes |
| H1.1 confirmatory EKF3 − FGO verdict | `no ordering claimed` | `no ordering claimed` | numbers.md §6.1 confirmatory row; claim 2 | yes |
| rule text METHODOLOGY.md:5650 contains the quoted phrase | `at least 6 of 7` | `at least 6 of 7` | METHODOLOGY.md:5650 (read at build time) | yes |
| rule text METHODOLOGY.md:5652 contains the quoted phrase | `the 95% t-interval (df 6) of mean `d` excludes 0` | `the 95% t-interval (df 6) of mean `d` excludes 0` | METHODOLOGY.md:5652 (read at build time) | yes |
| rule text METHODOLOGY.md:5653 contains the quoted phrase | `by the mirror rule` | `by the mirror rule` | METHODOLOGY.md:5653 (read at build time) | yes |
| rule text METHODOLOGY.md:5654 contains the quoted phrase | `Otherwise: no ordering is claimed` | `Otherwise: no ordering is claimed` | METHODOLOGY.md:5654 (read at build time) | yes |
| rule text METHODOLOGY.md:6237 contains the quoted phrase | `r10 has no FGO value, so it is counted as **NOT**` | `r10 has no FGO value, so it is counted as **NOT**` | METHODOLOGY.md:6237 (read at build time) | yes |
| rule text METHODOLOGY.md:6239 contains the quoted phrase | `the **6 usable** flights (df 5)` | `the **6 usable** flights (df 5)` | METHODOLOGY.md:6239 (read at build time) | yes |
| 1A: flights on which the UKF has the highest cruise ATE, of flights 1–9 | `6/9` | `6/9` | numbers.md §6.1 UKF standing row ('UKF highest on 6/9 flights') | yes |
| rule text METHODOLOGY.md:7187 contains the quoted phrase | `descriptive; no pre-registered UKF ordering test` | `descriptive; no pre-registered UKF ordering test` | METHODOLOGY.md:7187 (read at build time) | yes |
| C1.a with heading UKF / FGO range, 6 textured-floor bags (m) | `0.13–0.25 / 0.06–0.22` | `0.13–0.25 / 0.06–0.22` | numbers.md §6.6 heading-arm rows | yes |
| C1.a FGO lower than UKF | `6/6` | `6/6` | numbers.md §6.6 C0 row; claim 7 | yes |
| rule text METHODOLOGY.md:7892 contains the quoted phrase | `REPORT, no decision rule` | `REPORT, no decision rule` | METHODOLOGY.md:7892 (read at build time) | yes |

### Table 4.2 (internal T3, table): Blank floor: position error after the loss of flow aiding

- **Caption:** On a blank floor nothing bounds position [a]: the UKF and the FGO dead-reckon away to km-scale errors by the end of the cruise, and EKF3 flags its own position invalid, so it has no scored error. Behaviour under total loss of flow aiding, not accuracy. The blank-floor flights pool Experiment 1A (standard sensors) and 1B (forward camera).
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
| EKF3 blank invalid for (s of cruise), all 14 | `301–310 (n 14)` | `301–310 (n 14)` | numbers.md §6.2 ('blank from take-off (all 14), for 301–310 s') | yes |
| rule text METHODOLOGY.md:5551 contains the quoted phrase | `**Not accuracy comparisons** (ruling)` | `**Not accuracy comparisons** (ruling)` | METHODOLOGY.md:5551 (read at build time) | yes |

### Table 4.3 (internal T4, table): Closed loop at half real-time (RTF 0.5): the final build of each estimator flying the vehicle

- **Caption:** Without a heading source every flying estimator reaches the west wall; with the camera heading every flight passes all five closed-loop criteria (mission completion and the cross-track, heading-error, lateral-speed and oscillation bounds) and the estimator-validity criterion, with the per-flight cross-track, heading-error and lateral-speed values shown (flights 1 / 2 / 3). No ordering between the estimators is claimed [a].
- **Inputs:** eval/results/closed_loop_cl_a_tex_half.json, closed_loop_cl_bcpp_tex_r{1,2,3}_half.json, closed_loop_cl_ukf_{a,b}_tex*_half_v2.json, closed_loop_cl_fgo_{a,b}_tex*_half_v3.json
- **numbers.md rows:** §15 (contact rows, B1–B5 counts, B2, B3, B4 re-flown rows); claim 14

| check | computed | expected | source | match |
|---|---|---|---|---|
| closed loop, half real-time, with heading: flights passing all five criteria (+ estimator validity) | `3/3 / 3/3 / 3/3` | `3/3 / 3/3 / 3/3` | numbers.md §15 | yes |
| final UKF port max cross-track, flights 1/2/3 (m) | `0.231 / 0.253 / 0.219` | `0.231 / 0.253 / 0.219` | numbers.md §15 re-flown row | yes |
| final FGO node max cross-track, flights 1/2/3 (m) | `0.118 / 0.033 / 0.392` | `0.118 / 0.033 / 0.392` | numbers.md §15 re-flown row | yes |
| EKF3 half real-time max cross-track range (m) | `0.24–0.33` | `0.24–0.33` | numbers.md §15 B2 row | yes |
| final UKF port heading error p95/max/mean per flight (deg) | `0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250` | `0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250` | numbers.md §15 re-flown B3 row | yes |
| final FGO node heading error p95/max/mean per flight (deg) | `0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187` | `0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187` | numbers.md §15 re-flown B3 row | yes |
| EKF3 half real-time heading error p95 / max range (deg) | `0.28–0.32/0.33–0.39` | `0.28–0.32/0.33–0.39` | numbers.md §15 B3 row | yes |
| no-heading wall contact EKF3 / final UKF port / final FGO node (s) | `+242.1 / +165.9 / +169.9` | `+242.1 / +165.9 / +169.9` | numbers.md §15 contact rows | yes |
| final FGO node flight 3 max lateral speed (m/s) | `0.246` | `0.246` | numbers.md §15 re-flown row (closest call) | yes |
| closed loop, half real-time, with heading: max cross-track range EKF3 / final UKF port / final FGO node (m) | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | numbers.md §15 B2 row (EKF3 half) and re-flown rows | yes |
| rule text METHODOLOGY.md:4948 contains the quoted phrase | `[+155, +215] s` | `[+155, +215] s` | METHODOLOGY.md:4948 (read at build time) | yes |
| rule text METHODOLOGY.md:7513 contains the quoted phrase | `[+146, +218] s` | `[+146, +218] s` | METHODOLOGY.md:7513 (read at build time) | yes |
| rule text METHODOLOGY.md:8995 contains the quoted phrase | `[+145, +196] s` | `[+145, +196] s` | METHODOLOGY.md:8995 (read at build time) | yes |
| rule text METHODOLOGY.md:4951 contains the quoted phrase | `B1.` | `B1.` | METHODOLOGY.md:4951 (read at build time) | yes |
| rule text METHODOLOGY.md:4966 contains the quoted phrase | `B5.` | `B5.` | METHODOLOGY.md:4966 (read at build time) | yes |
| rule text METHODOLOGY.md:7362 contains the quoted phrase | `S2 is the estimator valid throughout` | `S2 is the estimator valid throughout` | METHODOLOGY.md:7362 (read at build time) | yes |
| rule text METHODOLOGY.md:9355 contains the quoted phrase | `DESCRIPTIVE; separate flights, n = 3 each, no ordering claim` | `DESCRIPTIVE; separate flights, n = 3 each, no ordering claim` | METHODOLOGY.md:9355 (read at build time) | yes |

### Figure 5.1 (internal F5, figure): Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm

- **Caption:** Experiment 2 (known tags; the tag room, 5 laps of a 6 m square, open loop on simulator truth): horizontal RMSE in the world frame, no alignment, against the tags sent (condition A all 8, B the 4 corners, C 2 diagonal, D 1 tag; median gap between fixes 4.3 / 10.1 / 22.0 / 46.3 s). Solid, filled = live; dashed, open = hindsight (the FGO whole-flight batch and the smoothed UKF); small marks = each of 3 flights, line = their mean. Live errors grow from 2–4 cm to 8–13 cm as tags thin out; no live ordering is claimed [a] (in condition D the FGO live 8.3 cm against EKF3 9.6 cm is descriptive, 3 flights). H2.3 (live errors similar) FAILS (live max/min 1.97 / 2.36 / 1.42 / 1.57). The FGO whole-flight batch stays at 1.0–2.8 cm; its hindsight gain grows with the gap (H2.1 PASS), the smoothed UKF's does not (H2.2 FAIL), and the ratio of the batch to the smoothed UKF is 1.31–3.89 (H2.4 FAIL) [b]. Same tag fixes for every estimator.
  - *Footnote:* [a] Ordering basis, Experiment 2 live tracks, EKF3, UKF and FGO (H2.3). Metric: horizontal RMSE over the 5 laps in the world frame, no alignment, mean of the flights in each condition, cm. n = 3 flights per condition, 4 conditions (12 flights; every estimator on the same flights, open loop on simulator truth, paired). Rule: H2.3 'live errors are similar': in every condition the largest live RMSE (mean over repeats) is ≤ 1.5 × the smallest (METHODOLOGY.md:10178, METHODOLOGY.md:10179); no ordering test was registered, and the condition-D ordering is 'descriptive only (n = 3)' (METHODOLOGY.md:12803). Result: max ÷ min 1.97 / 2.36 / 1.42 / 1.57 (conditions A / B / C / D): H2.3 FAILS (C inside the band); condition D: FGO 8.3, EKF3 9.6, UKF 13.1 cm, descriptive. Verdict: case (ii), FAILED AS WORDED: the registered prediction is false as written; a failed criterion does not by itself establish an ordering, so any ordering shown is descriptive.
  - *Footnote:* [b] Ordering basis, Experiment 2 hindsight, the FGO whole-flight batch against the smoothed UKF (H2.4). Metric: horizontal RMSE over the 5 laps in the world frame, mean of the flights in each condition, cm. n = 3 flights per condition, 4 conditions (both hindsight tracks from the same flights, paired). Rule: H2.4 'FGO hindsight ≈ RTS-UKF': in every condition the larger RMSE (mean over repeats) is ≤ 1.5 × the smaller (METHODOLOGY.md:10180, METHODOLOGY.md:10181); no ordering test was registered. Result: max ÷ min 1.31 / 2.14 / 2.06 / 3.89: H2.4 FAILS; the FGO whole-flight batch is the lower in every condition (descriptive). Verdict: case (ii), FAILED AS WORDED: the registered prediction is false as written; a failed criterion does not by itself establish an ordering, so any ordering shown is descriptive.
  - *Footnote:* Ordering verdicts used in the footnotes: RULE MET = a pre-registered rule was applied and met, so its ordering (or similarity) is claimed; case (i) TEST RUN, RULE NOT MET = a pre-registered decision rule with a 'no ordering' outcome was applied and gave that outcome; case (ii) FAILED AS WORDED = a pre-registered prediction of an ordering or a similarity was scored literally and is false, which does not by itself establish the opposite ordering; case (iii) NO COMPARATIVE TEST REGISTERED = values are descriptive. n always names its unit (flights, bags, losses).
- **Inputs:** eval/results/expT/T_{A,B,C,D}_r{1,2,3}.json (tracks.*.horiz_err_m.rmse), expT/t_aggregate.json
- **numbers.md rows:** §16.1 table and bullets (H-T1, P-T2, P-T3, P-T4, condition D); claims 17, 18

| check | computed | expected | source | match |
|---|---|---|---|---|
| Experiment 2 8 tags: EKF3 / UKF / FGO live / smoothed UKF / FGO whole-flight batch (m) | `0.039 0.037 0.020 0.014 0.010` | `0.039 0.037 0.020 0.014 0.010` | numbers.md §16.1 table | yes |
| Experiment 2 4 tags: EKF3 / UKF / FGO live / smoothed UKF / FGO whole-flight batch (m) | `0.055 0.061 0.026 0.031 0.015` | `0.055 0.061 0.026 0.031 0.015` | numbers.md §16.1 table | yes |
| Experiment 2 2 tags: EKF3 / UKF / FGO live / smoothed UKF / FGO whole-flight batch (m) | `0.074 0.076 0.054 0.039 0.019` | `0.074 0.076 0.054 0.039 0.019` | numbers.md §16.1 table | yes |
| Experiment 2 1 tag: EKF3 / UKF / FGO live / smoothed UKF / FGO whole-flight batch (m) | `0.096 0.131 0.083 0.109 0.028` | `0.096 0.131 0.083 0.109 0.028` | numbers.md §16.1 table | yes |
| Experiment 2 median gaps A–D (s) | `4.3 / 10.1 / 22.0 / 46.3` | `4.3 / 10.1 / 22.0 / 46.3` | numbers.md §16.1 table header | yes |
| tags per lap in condition B | `[0, 1, 2, 3]` | `[0, 1, 2, 3]` | T_B_r1.json gates (4 corner tags) | yes |
| H2.1 median gain A–D (m), rho, PASS | `0.010 / 0.011 / 0.023 / 0.052 +0.30 True` | `0.010 / 0.011 / 0.023 / 0.052 +0.30 True` | numbers.md §16.1 | yes |
| H2.2 gain A–D (m), PASS | `+0.020 / +0.032 / +0.037 / +0.029 False` | `+0.020 / +0.032 / +0.037 / +0.029 False` | numbers.md §16.1 | yes |
| H2.3 live max/min ratio A / B / C / D | `1.97 / 2.36 / 1.42 / 1.57` | `1.97 / 2.36 / 1.42 / 1.57` | numbers.md §16.1 P-T3 | yes |
| Experiment 2: flights per condition A / B / C / D | `3 / 3 / 3 / 3` | `3 / 3 / 3 / 3` | numbers.md §16.1 heading ('3 repeats per condition') | yes |
| Experiment 2 condition D live EKF3 / UKF / FGO (m) | `0.096 / 0.131 / 0.083` | `0.096 / 0.131 / 0.083` | numbers.md §16.1 table | yes |
| rule text METHODOLOGY.md:10178 contains the quoted phrase | `live errors are similar` | `live errors are similar` | METHODOLOGY.md:10178 (read at build time) | yes |
| rule text METHODOLOGY.md:10179 contains the quoted phrase | `is ≤ 1.5 × the smallest` | `is ≤ 1.5 × the smallest` | METHODOLOGY.md:10179 (read at build time) | yes |
| rule text METHODOLOGY.md:12803 contains the quoted phrase | `is descriptive only (n = 3)` | `is descriptive only (n = 3)` | METHODOLOGY.md:12803 (read at build time) | yes |
| H2.4 max/min ratio A / B / C / D | `1.31 / 2.14 / 2.06 / 3.89` | `1.31 / 2.14 / 2.06 / 3.89` | numbers.md §16.1 P-T4 | yes |
| rule text METHODOLOGY.md:10180 contains the quoted phrase | `FGO hindsight ≈ RTS-UKF` | `FGO hindsight ≈ RTS-UKF` | METHODOLOGY.md:10180 (read at build time) | yes |
| rule text METHODOLOGY.md:10181 contains the quoted phrase | `is ≤ 1.5 × the smaller` | `is ≤ 1.5 × the smaller` | METHODOLOGY.md:10181 (read at build time) | yes |

### Figure 5.2 (internal F7, figure): Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps

- **Caption:** Experiment 3 (loop closure): the keyframe FGO with AprilTags at UNKNOWN positions (each tag a landmark), flights 1–3, horizontal RMSE per 6 m lap in the first tag's frame, one shared linear axis. Left: with loop closure the live error falls after lap 1 (lap 5 ÷ lap 1 0.16–0.43; overall 4.9–7.6 cm live, 1.7–2.7 cm hindsight). Right: without re-identification it grows 2.9–4.5× over five laps (overall 26.3–36.1 cm live). H3.1, H3.2, H3.3 and H3.4 PASS 3/3 [a]. This is an FGO capability, not an FGO-against-filter result (the filters have no loop-closure equivalent); one estimator, so one colour, with live solid/filled and hindsight dashed/open. The estimator validation check (V3) is not re-scorable on the corrected FGO (its labels were never recorded).
  - *Footnote:* [a] Ordering basis, Experiment 3, the keyframe FGO with against without loop closure (H3.1–H3.4; one estimator, not a comparison of estimators). Metric: horizontal RMSE in the first tag's frame, overall and per 6 m lap, m. n = 3 flights (each flight replayed with and without loop closure, paired). Rule: H3.2 'LC live overall RMSE < no-LC live overall RMSE in 3/3 flights' (METHODOLOGY.md:10503); H3.3 the same for hindsight (METHODOLOGY.md:10504); H3.1 with loop closure lap 5 ≤ 1.5 × lap 1 in 3/3 (METHODOLOGY.md:10501); H3.4 without, lap 5 > 1.5 × lap 1 in 3/3 (METHODOLOGY.md:10505). Result: H3.1 / H3.2 / H3.3 / H3.4 pass on 3 / 3 / 3 / 3 of 3 flights (live 0.049–0.076 m with loop closure, 0.263–0.361 m without). Verdict: RULE MET: the ordering is claimed.
  - *Footnote:* Ordering verdicts used in the footnotes: RULE MET = a pre-registered rule was applied and met, so its ordering (or similarity) is claimed; case (i) TEST RUN, RULE NOT MET = a pre-registered decision rule with a 'no ordering' outcome was applied and gave that outcome; case (ii) FAILED AS WORDED = a pre-registered prediction of an ordering or a similarity was scored literally and is false, which does not by itself establish the opposite ordering; case (iii) NO COMPARATIVE TEST REGISTERED = values are descriptive. n always names its unit (flights, bags, losses).
- **Inputs:** eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m)
- **numbers.md rows:** §16.3 table and bullets; claims 23, 24

| check | computed | expected | source | match |
|---|---|---|---|---|
| Experiment 3 with loop closure, live overall (m) | `0.049–0.076` | `0.049–0.076` | numbers.md §16.3 | yes |
| Experiment 3 with loop closure, hindsight overall (m) | `0.017–0.027` | `0.017–0.027` | numbers.md §16.3 | yes |
| Experiment 3 without loop closure, live overall (m) | `0.263–0.361` | `0.263–0.361` | numbers.md §16.3 | yes |
| Experiment 3 without loop closure, hindsight overall (m) | `0.221–0.266` | `0.221–0.266` | numbers.md §16.3 | yes |
| Experiment 3 lap5/lap1, live with loop closure; live without | `0.16–0.43; 2.9–4.5` | `0.16–0.43; 2.9–4.5` | numbers.md §16.3 | yes |
| Experiment 3 H3.1 / H3.2 / H3.3 / H3.4: flights passing, of 3 | `3/3 3/3 3/3 3/3` | `3/3 3/3 3/3 3/3` | numbers.md §16.3 ('H-L1 (primary), H-L2, H-L3 and P-L4: PASS 3/3') | yes |
| rule text METHODOLOGY.md:10503 contains the quoted phrase | `LC live overall RMSE < no-LC live overall RMSE in 3/3 flights` | `LC live overall RMSE < no-LC live overall RMSE in 3/3 flights` | METHODOLOGY.md:10503 (read at build time) | yes |
| rule text METHODOLOGY.md:10504 contains the quoted phrase | `LC hindsight overall RMSE < no-LC hindsight overall RMSE in 3/3 flights` | `LC hindsight overall RMSE < no-LC hindsight overall RMSE in 3/3 flights` | METHODOLOGY.md:10504 (read at build time) | yes |
| rule text METHODOLOGY.md:10501 contains the quoted phrase | `the lap-5 RMSE is ≤ 1.5 × the lap-1 RMSE in 3/3` | `the lap-5 RMSE is ≤ 1.5 × the lap-1 RMSE in 3/3` | METHODOLOGY.md:10501 (read at build time) | yes |
| rule text METHODOLOGY.md:10505 contains the quoted phrase | `lap 5 > 1.5 × lap 1 in 3/3 flights` | `lap 5 > 1.5 × lap 1 in 3/3 flights` | METHODOLOGY.md:10505 (read at build time) | yes |

### Figure 5.3 (internal F6, figure): Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight keeps the error near 1 m

- **Caption:** Experiment 4 (outdoor–indoor: outdoor → indoor → outdoor, open loop on simulator truth), flight 1: horizontal error against time in the world frame, no alignment. Indoor sensor set, the same for all three estimators: IMU (accelerometer and gyro), downward optical flow and the downward LiDAR rangefinder only; no GNSS (switched off at the entrance), no compass, no forward-camera heading (descoped) and no tags (none in the world). Route events (dotted): GNSS OFF at the entrance (0 s); the far end, 30 m inside, reached at ~60 s and held 3 s; the return in reverse at the same heading (no yaw turn) from 63 s; GNSS ON on re-crossing the entrance at 123 s. EKF3 resets to GNSS on return with a 4.10 m jump (every flight) [d]. Solid = live, dashed = hindsight. The per-flight indoor RMSE of all three flights is in Table 5.1 (H4.1 PASS 3/3 [a]; H4.2 FAIL [b]; H4.3 PASS [c]).
  - *Footnote:* [a] Ordering basis, Experiment 4, the FGO whole-flight batch (hindsight) against the EKF3 and UKF live tracks (H4.1). Metric: indoor horizontal RMSE in the world frame, no alignment, m. n = 3 flights (same flights, paired). Rule: H4.1: PASS iff in 3/3 flights the FGO-batch indoor RMSE is < both EKF3's and the UKF's live indoor RMSE (METHODOLOGY.md:10358, METHODOLOGY.md:10359). Result: lower than both in 3 of 3 flights: H4.1 PASSES (a hindsight track against live tracks, not like with like). Verdict: RULE MET: the ordering is claimed.
  - *Footnote:* [b] Ordering basis, Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2). Metric: indoor horizontal RMSE in the world frame, no alignment, over the 123 s without GNSS, m. n = 3 flights (every estimator on the same flights, open loop on simulator truth, paired). Rule: H4.2 'live indoor errors are similar': in every flight the largest live indoor RMSE is ≤ 1.5 × the smallest (METHODOLOGY.md:10360, METHODOLOGY.md:10361); no ordering test was registered. Result: max ÷ min 1.71–1.84: H4.2 FAILS; EKF3 largest in 3 of 3 flights; UKF 0.77–0.84 m and FGO 0.83–0.89 m (both descriptive). Verdict: case (ii), FAILED AS WORDED: the registered prediction is false as written; a failed criterion does not by itself establish an ordering, so any ordering shown is descriptive.
  - *Footnote:* [c] Ordering basis, Experiment 4, the FGO whole-flight batch against the smoothed UKF (H4.3). Metric: indoor horizontal RMSE in the world frame, no alignment, m. n = 3 flights (same flights, paired). Rule: H4.3: the two RMSEs within 1.5× of each other in every flight (METHODOLOGY.md:10362). Result: max ÷ min 1.01–1.02: H4.3 PASSES; which is lower changes between flights (descriptive). Verdict: RULE MET: the similarity is claimed (no ordering).
  - *Footnote:* [d] Ordering basis, Experiment 4, the jump on the return to GNSS. Metric: largest position step in the 10 s after GNSS returns, m. n = 3 flights (same flights for every estimator). Rule: none: EKF3's jump is 'Reported regardless' (METHODOLOGY.md:10365); no comparative test was pre-registered. Result: EKF3 4.10–4.10, UKF 2.30–2.44, FGO 2.14–2.28 m. Verdict: case (iii), NO COMPARATIVE TEST REGISTERED: values are descriptive.
  - *Footnote:* Ordering verdicts used in the footnotes: RULE MET = a pre-registered rule was applied and met, so its ordering (or similarity) is claimed; case (i) TEST RUN, RULE NOT MET = a pre-registered decision rule with a 'no ordering' outcome was applied and gave that outcome; case (ii) FAILED AS WORDED = a pre-registered prediction of an ordering or a similarity was scored literally and is false, which does not by itself establish the opposite ordering; case (iii) NO COMPARATIVE TEST REGISTERED = values are descriptive. n always names its unit (flights, bags, losses).
- **Inputs:** eval/results/expO/O_r1.json (markers_bag_s, max_step_after_return_m), O_r2.json, O_r3b.json; curves: O_r1 room_ukf/, room_fgo/ TUMs, dataflash XKF1 about EKF3's origin (gnss.npz), bag /imu/time_ref (clock map); design: METHODOLOGY 'Experiment O: pre-registration', sim/worlds/outdoor_indoor.sdf, fly_trial.py outback(), o_gnss.parm
- **numbers.md rows:** §16.2 table and bullets; claims 19–22

| check | computed | expected | source | match |
|---|---|---|---|---|
| Experiment 4 EKF3 reset jump (m) | `4.10–4.10` | `4.10–4.10` | numbers.md §16.2 ('4.10 m, every flight') | yes |
| Experiment 4 indoor duration (s) | `123` | `123` | numbers.md §16.2 heading ('123 s, GNSS off') | yes |
| flight 1 curve indoor RMSE recomputed vs json, max |Δ| <= 0.05 m | `ok` | `ok` | curve source vs scorer | yes |
| flight 1 bag has no tag topics | `0` | `0` | O design: no tags in outdoor_indoor.sdf | yes |
| H4.1: FGO whole-flight batch below both filters' live tracks, flights | `3/3` | `3/3` | numbers.md §16.2 (H-O1 PASS 3/3) | yes |
| rule text METHODOLOGY.md:10358 contains the quoted phrase | `PASS iff in 3/3` | `PASS iff in 3/3` | METHODOLOGY.md:10358 (read at build time) | yes |
| rule text METHODOLOGY.md:10359 contains the quoted phrase | `is < both EKF3` | `is < both EKF3` | METHODOLOGY.md:10359 (read at build time) | yes |
| Experiment 4 H4.2 live max/min ratio; largest = EKF3 in every flight | `1.71–1.84; True` | `1.71–1.84; True` | numbers.md §16.2 H-O2 bullet | yes |
| Experiment 4: flights in which EKF3 live has the largest indoor RMSE | `3/3` | `3/3` | numbers.md §16.2 H-O2 bullet (EKF3 largest in every flight) | yes |
| rule text METHODOLOGY.md:10360 contains the quoted phrase | `live indoor errors are similar` | `live indoor errors are similar` | METHODOLOGY.md:10360 (read at build time) | yes |
| rule text METHODOLOGY.md:10361 contains the quoted phrase | `is ≤ 1.5 × the smallest` | `is ≤ 1.5 × the smallest` | METHODOLOGY.md:10361 (read at build time) | yes |
| Experiment 4 FGO whole-flight batch vs smoothed UKF ratio, max/min per flight (capped) | `1.01–1.02` | `1.01–1.02` | numbers.md §16.2 P-O3 | yes |
| rule text METHODOLOGY.md:10362 contains the quoted phrase | `within 1.5× of each other in every` | `within 1.5× of each other in every` | METHODOLOGY.md:10362 (read at build time) | yes |
| Experiment 4 largest step in 10 s after return EKF3 / UKF / FGO live (m) | `4.10–4.10 / 2.30–2.44 / 2.14–2.28` | `4.10–4.10 / 2.30–2.44 / 2.14–2.28` | numbers.md §16.2 table | yes |
| rule text METHODOLOGY.md:10365 contains the quoted phrase | `Reported regardless` | `Reported regardless` | METHODOLOGY.md:10365 (read at build time) | yes |

### Table 5.1 (internal T6, table): Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off)

- **Caption:** Indoors without GNSS the live errors are 0.8–1.4 m and not similar across estimators (EKF3 largest in every flight, H4.2 FAIL) [a]; the two hindsight tracks agree at 0.58–0.60 m (H4.3 PASS) [b].
- **Inputs:** eval/results/expO/O_r1.json, O_r2.json, O_r3b.json (tracks.*.indoor_rmse_m)
- **numbers.md rows:** §16.2 table and bullets; claims 19–22

| check | computed | expected | source | match |
|---|---|---|---|---|
| Experiment 4 indoor RMSE EKF3 live (m) | `1.42–1.43` | `1.42–1.43` | numbers.md §16.2 table | yes |
| Experiment 4 indoor RMSE UKF live (m) | `0.77–0.84` | `0.77–0.84` | numbers.md §16.2 table | yes |
| Experiment 4 indoor RMSE FGO live (m) | `0.83–0.89` | `0.83–0.89` | numbers.md §16.2 table | yes |
| Experiment 4 indoor RMSE smoothed UKF (hindsight) (m) | `0.58–0.60` | `0.58–0.60` | numbers.md §16.2 table | yes |
| Experiment 4 indoor RMSE FGO whole-flight batch (hindsight) (m) | `0.59–0.59` | `0.59–0.59` | numbers.md §16.2 table | yes |
| Experiment 4 H4.2 live max/min ratio; largest = EKF3 in every flight | `1.71–1.84; True` | `1.71–1.84; True` | numbers.md §16.2 H-O2 bullet | yes |
| H4.1: FGO whole-flight batch below both filters' live tracks, flights | `3/3` | `3/3` | numbers.md §16.2 (H-O1 PASS 3/3) | yes |
| Experiment 4: flights in which EKF3 live has the largest indoor RMSE | `3/3` | `3/3` | numbers.md §16.2 H-O2 bullet (EKF3 largest in every flight) | yes |
| rule text METHODOLOGY.md:10360 contains the quoted phrase | `live indoor errors are similar` | `live indoor errors are similar` | METHODOLOGY.md:10360 (read at build time) | yes |
| rule text METHODOLOGY.md:10361 contains the quoted phrase | `is ≤ 1.5 × the smallest` | `is ≤ 1.5 × the smallest` | METHODOLOGY.md:10361 (read at build time) | yes |
| Experiment 4 FGO whole-flight batch vs smoothed UKF ratio, max/min per flight (capped) | `1.01–1.02` | `1.01–1.02` | numbers.md §16.2 P-O3 | yes |
| rule text METHODOLOGY.md:10362 contains the quoted phrase | `within 1.5× of each other in every` | `within 1.5× of each other in every` | METHODOLOGY.md:10362 (read at build time) | yes |
| rule text METHODOLOGY.md:10358 contains the quoted phrase | `PASS iff in 3/3` | `PASS iff in 3/3` | METHODOLOGY.md:10358 (read at build time) | yes |
| rule text METHODOLOGY.md:10359 contains the quoted phrase | `is < both EKF3` | `is < both EKF3` | METHODOLOGY.md:10359 (read at build time) | yes |

### Table 5.2 (internal T8, table): Hindsight: the FGO whole-flight batch against the smoothed UKF

- **Caption:** With tags at known positions (Experiment 2) the FGO whole-flight batch is below the smoothed UKF in every condition, by 1.3–3.9× (largest with 1 tag; H2.4 FAIL as pre-registered) [a]; indoors without GNSS (Experiment 4) the two hindsight tracks are equal within 1–2% (H4.3 PASS) [b].
- **Inputs:** eval/results/expT/t_aggregate.json (conditions.*.mean_rmse_m, 'P-T4 hindsight ratio max/min'); expO/O_r1.json, O_r2.json, O_r3b.json (tracks.*.indoor_rmse_m)
- **numbers.md rows:** §16.1 (table, P-T4), §16.2 (table, P-O3); claims 18, 21

| check | computed | expected | source | match |
|---|---|---|---|---|
| H2.4 max/min ratio A / B / C / D | `1.31 / 2.14 / 2.06 / 3.89` | `1.31 / 2.14 / 2.06 / 3.89` | numbers.md §16.1 P-T4 | yes |
| Table 5.2 ratio = stored H2.4 ratio, all 4 conditions | `True` | `True` | t_aggregate.json P-T4 vs mean_rmse_m | yes |
| Experiment 2 smoothed UKF A–D (m) | `0.014 / 0.031 / 0.039 / 0.109` | `0.014 / 0.031 / 0.039 / 0.109` | numbers.md §16.1 table | yes |
| Experiment 2 FGO whole-flight batch A–D (m) | `0.010 / 0.015 / 0.019 / 0.028` | `0.010 / 0.015 / 0.019 / 0.028` | numbers.md §16.1 table | yes |
| Experiment 4 FGO whole-flight batch vs smoothed UKF ratio, max/min per flight (capped) | `1.01–1.02` | `1.01–1.02` | numbers.md §16.2 P-O3 | yes |
| Experiment 4 FGO whole-flight batch vs cap-free smoothed UKF ratio, max/min per flight | `1.01–1.05` | `1.01–1.05` | numbers.md §16.2 P-O3 (cap-free) | yes |
| rule text METHODOLOGY.md:10180 contains the quoted phrase | `FGO hindsight ≈ RTS-UKF` | `FGO hindsight ≈ RTS-UKF` | METHODOLOGY.md:10180 (read at build time) | yes |
| rule text METHODOLOGY.md:10181 contains the quoted phrase | `is ≤ 1.5 × the smaller` | `is ≤ 1.5 × the smaller` | METHODOLOGY.md:10181 (read at build time) | yes |
| rule text METHODOLOGY.md:10362 contains the quoted phrase | `within 1.5× of each other in every` | `within 1.5× of each other in every` | METHODOLOGY.md:10362 (read at build time) | yes |

### Table 6.1 (internal T5, table): Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators

- **Caption:** Holding on a wall tag, every flying estimator drifts at most about 3 cm while the tag is hidden, inside every pre-registered band, and none locks out; each cell gives the maximum drift / its band in mm, with the range over the losses. The comparative hypotheses (H5.2, H5.3, H5.4a–b) FAIL on these final-build sets, identical to the original-build verdicts (superseded builds: Table A.2), so no ordering is claimed [a]. The FGO safety re-tests (corrected-priors node) used the corrected initial priors; the flown FGO hold and closed-loop corridor results (final FGO node) used the original priors.
- **Inputs:** eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s3v2_r*.json (losses[*].<est>.effective.drift_m, drift_end_m, lockout)
- **numbers.md rows:** §17 (S1 table, S1 far row, P-H5, P-H7), §17.1 (S2v2, S3v2), §17.2; claims 25, 26

| check | computed | expected | source | match |
|---|---|---|---|---|
| EKF3-flying hold set (near spawn) drift 5/15/30/move (mm, effective) | `13–27 | 6–25 | 3–11 | 7–31` | `13–27 | 6–25 | 3–11 | 7–31` | numbers.md §17 table | yes |
| EKF3-flying hold set (far spawn) drift, flights 1 | 2 | 3, 5 s/15 s/30 s/move (mm, effective) | `15/12/3/4 | 17/12/26/20 | 11/17/11/13` | `15/12/3/4 | 17/12/26/20 | 11/17/11/13` | numbers.md §17 S1 far row (ruling 2026-10-16, open items 7) | yes |
| EKF3-flying hold set (far spawn) drift, flights 1 | 2 | 3, 5 s/15 s/30 s/move (mm, end of loss) | `15/10/3/7 | 19/12/26/23 | 12/17/11/16` | `15/10/3/7 | 19/12/26/23 | 12/17/11/16` | numbers.md §17 S1 far row (ruling 2026-10-16, open items 7) | yes |
| UKF-flying hold set (final build): end-of-loss drift, flights 1/2/3 (mm) | `5/7/8 | 19/7/26 | 6/10/10 | 26/4/5` | `5/7/8 | 19/7/26 | 6/10/10 | 26/4/5` | numbers.md §17.1 table | yes |
| FGO-flying hold set (final build): end-of-loss drift, flights 1/2/3 (mm) | `13/20/17 | 7/25/27 | 22/15/9 | 17/11/18` | `13/20/17 | 7/25/27 | 22/15/9 | 17/11/18` | numbers.md §17.1 table | yes |
| effective vs end-of-loss drift, max |Δ| at printed (mm) precision | `≤ 5 mm` | `≤ 5 mm` | numbers.md §17.1 ('differ by ≤ 5 mm'); unrounded 5.1 mm (S2v2 r1, move loss) | yes |
| every drift inside its pre-registered drift band (H5.5) | `True` | `True` | numbers.md §17, §17.1 (every band PASSES) | yes |
| lockouts in any loss (flying estimators) | `0` | `0` | numbers.md §17 (P-H7 PASS) | yes |
| docs/tag_hold_design.md:176-188 (§e hypotheses) identical at c11fcf3 (2026-10-08 15:17) and at build time | `True` | `True` | git show c11fcf3:docs/tag_hold_design.md | yes |
| Experiment 5 (final-build sets): flights with the FGO / the UKF lowest mean hold error | `0/3 / 3/3` | `0/3 / 3/3` | numbers.md §17.2 criteria table (H-H2: 'FAIL (0/3): UKF lowest 3/3') | yes |
| Experiment 5 hold UKF / FGO / EKF3, final-build sets (mm) | `6.4–7.1 / 8.3–8.6 / 7.8–7.9` | `6.4–7.1 / 8.3–8.6 / 7.8–7.9` | numbers.md §17.2 criteria table (re-flown) | yes |
| H5.3 / H5.4b max/min, final-build sets | `2.40–2.58 / 3.2–7.7` | `2.40–2.58 / 3.2–7.7` | numbers.md §17.2 criteria table | yes |
| H5.4a EKF3 15 s re-lock jump per flight (mm) | `5 / 5 / 7` | `5 / 5 / 7` | numbers.md §17.2 criteria table (H-H4 (15 s)) | yes |
| Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds) | `FAIL; FAIL; FAIL; FAIL` | `FAIL; FAIL; FAIL; FAIL` | numbers.md §17.2 (final-build sets primary, ruling 2026-10-16) | yes |
| verbatim quote tag_hold_design.md:180 | `H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.` | `H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.` | docs/tag_hold_design.md:180-180 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:183 | `P-H3 (smoothness, prediction): gyro activity in the hold windows within 1.5× across estimators.` | `P-H3 (smoothness, prediction): gyro activity in the hold windows within 1.5× across estimators.` | docs/tag_hold_design.md:183-183 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:185–186 | `After the 15 s occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's and the FGO's in 3/3 flights.` | `After the 15 s occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's and the FGO's in 3/3 flights.` | docs/tag_hold_design.md:185-186 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:187 | `After the 5 s occlusion (no timeout), the jumps are within 1.5× of each other.` | `After the 5 s occlusion (no timeout), the jumps are within 1.5× of each other.` | docs/tag_hold_design.md:187-187 (read at build time; emphasis and bullets removed) | yes |
| rule text METHODOLOGY.md:12236 contains the quoted phrase | `H-H2 FAILS` | `H-H2 FAILS` | METHODOLOGY.md:12236 (read at build time) | yes |
| rule text METHODOLOGY.md:13549 contains the quoted phrase | `ALL FAIL` | `ALL FAIL` | METHODOLOGY.md:13549 (read at build time) | yes |

### Table 7.1 (internal T1, table): Which estimator wins where (scorecard of the restated verdicts)

- **Caption:** Each cell gives the key number and the verdict it rests on, with a status word (FAILED, PASSED, N/A) where one applies. No ordering label is printed: an ordering (BEST / BEHIND / TIED) is shown only where a pre-registered decision rule was met, and no comparison in this table met one; any ordering visible in the numbers is descriptive (footnotes [a]–[j]). No estimator bounds position on a blank floor. The blank-floor row pools the standard-sensor flights (1A) with the forward-camera flights (1B: the camera calibration flights and both camera datasets).
- **Inputs:** eval/results/rerun_dsn_evo.json, dsn_extra_evo.json, dsn_paired_test.json, phase4_{fwdc,fwdplainc}_evo.json, blank_behaviour.json, expT/t_aggregate.json, expO/O_*.json, expL/T_A_r*_t245.json, expH/s1far_r*.json, expH/h_comparative_2026-10-11.json, closed_loop_cl_*_half(_v2/_v3).json
- **numbers.md rows:** §6.1, §6.2, §6.6, §15, §16.1–§16.3, §17.2; claims 1a, 1b, 2, 7, 10, 14, 17–19, 23, 25

| check | computed | expected | source | match |
|---|---|---|---|---|
| standard-sensor dataset, textured floor, median of flights 1–9, EKF3 / UKF / FGO (m) | `4.10 / 5.13 / 4.46` | `4.10 / 5.13 / 4.46` | numbers.md §6.1 standing row | yes |
| H1.1 confirmatory EKF3 − FGO verdict | `no ordering claimed` | `no ordering claimed` | numbers.md §6.1 confirmatory row; claim 2 | yes |
| C1.a with heading UKF / FGO range, 6 textured-floor bags (m) | `0.13–0.25 / 0.06–0.22` | `0.13–0.25 / 0.06–0.22` | numbers.md §6.6 heading-arm rows | yes |
| C1.a FGO lower than UKF | `6/6` | `6/6` | numbers.md §6.6 C0 row; claim 7 | yes |
| blank end-of-cruise UKF / FGO (km) † | `29–40 / 22–41` | `29–40 / 22–41` | numbers.md §6.2 | yes |
| EKF3 blank invalid for (s of cruise), all 14 | `301–310 (n 14)` | `301–310 (n 14)` | numbers.md §6.2 ('blank from take-off (all 14), for 301–310 s') | yes |
| Experiment 2 condition D live EKF3 / UKF / FGO (m) | `0.096 / 0.131 / 0.083` | `0.096 / 0.131 / 0.083` | numbers.md §16.1 table | yes |
| Experiment 2 FGO whole-flight batch A–D (m) | `0.010–0.028` | `0.010–0.028` | numbers.md §16.1 table | yes |
| Experiment 4 indoor live RMSE EKF3 / UKF / FGO (m) | `1.42–1.43 / 0.77–0.84 / 0.83–0.89` | `1.42–1.43 / 0.77–0.84 / 0.83–0.89` | numbers.md §16.2 table | yes |
| Experiment 4 H4.2 live max/min ratio; largest = EKF3 in every flight | `1.71–1.84; True` | `1.71–1.84; True` | numbers.md §16.2 H-O2 bullet | yes |
| Experiment 4 FGO whole-flight batch / smoothed UKF indoor (m) | `0.59–0.59 / 0.58–0.60` | `0.59–0.59 / 0.58–0.60` | numbers.md §16.2 table | yes |
| Experiment 3 live with / without loop closure (m) | `0.049–0.076 / 0.263–0.361` | `0.049–0.076 / 0.263–0.361` | numbers.md §16.3 | yes |
| Experiment 5 run-mean hold error EKF3 (far spawn) / final UKF port / final FGO node (mm) | `7.8–7.9 / 6.4–7.1 / 8.3–8.6` | `7.8–7.9 / 6.4–7.1 / 8.3–8.6` | numbers.md §17.2 table | yes |
| Experiment 5 comparative H5.2; H5.3; H5.4a (15 s); H5.4b (5 s) (final builds) | `FAIL; FAIL; FAIL; FAIL` | `FAIL; FAIL; FAIL; FAIL` | numbers.md §17.2 (final-build sets primary, ruling 2026-10-16) | yes |
| closed loop, half real-time, with heading: max cross-track range EKF3 / final UKF port / final FGO node (m) | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | `0.24–0.33 / 0.22–0.25 / 0.03–0.39` | numbers.md §15 B2 row (EKF3 half) and re-flown rows (UKF v2 0.231/0.253/0.219; FGO v3 0.118/0.033/0.392) | yes |
| closed loop, half real-time, with heading: flights passing all five criteria (+ estimator validity) | `3/3 / 3/3 / 3/3` | `3/3 / 3/3 / 3/3` | numbers.md §15 | yes |
| H1.1: flights in the test / usable for the FGO | `7 / 6` | `7 / 6` | numbers.md §6.1 confirmatory row ('r4–r10 … r10 unusable for FGO') | yes |
| H1.1: flights with d < 0 (EKF3 lower), of all flights | `5/7` | `5/7` | numbers.md §6.1 confirmatory row ('d < 0 on 5/7') | yes |
| H1.1 confirmatory mean d, CI (m) | `-0.021 [-0.989, 0.947]` | `-0.021 [-0.989, 0.947]` | numbers.md §6.1 | yes |
| rule text METHODOLOGY.md:5650 contains the quoted phrase | `at least 6 of 7` | `at least 6 of 7` | METHODOLOGY.md:5650 (read at build time) | yes |
| rule text METHODOLOGY.md:5652 contains the quoted phrase | `the 95% t-interval (df 6) of mean `d` excludes 0` | `the 95% t-interval (df 6) of mean `d` excludes 0` | METHODOLOGY.md:5652 (read at build time) | yes |
| rule text METHODOLOGY.md:5653 contains the quoted phrase | `by the mirror rule` | `by the mirror rule` | METHODOLOGY.md:5653 (read at build time) | yes |
| rule text METHODOLOGY.md:5654 contains the quoted phrase | `Otherwise: no ordering is claimed` | `Otherwise: no ordering is claimed` | METHODOLOGY.md:5654 (read at build time) | yes |
| rule text METHODOLOGY.md:6237 contains the quoted phrase | `r10 has no FGO value, so it is counted as **NOT**` | `r10 has no FGO value, so it is counted as **NOT**` | METHODOLOGY.md:6237 (read at build time) | yes |
| rule text METHODOLOGY.md:6239 contains the quoted phrase | `the **6 usable** flights (df 5)` | `the **6 usable** flights (df 5)` | METHODOLOGY.md:6239 (read at build time) | yes |
| 1A: flights on which the UKF has the highest cruise ATE, of flights 1–9 | `6/9` | `6/9` | numbers.md §6.1 UKF standing row ('UKF highest on 6/9 flights') | yes |
| rule text METHODOLOGY.md:7187 contains the quoted phrase | `descriptive; no pre-registered UKF ordering test` | `descriptive; no pre-registered UKF ordering test` | METHODOLOGY.md:7187 (read at build time) | yes |
| rule text METHODOLOGY.md:7892 contains the quoted phrase | `REPORT, no decision rule` | `REPORT, no decision rule` | METHODOLOGY.md:7892 (read at build time) | yes |
| n flights UKF / FGO | `11/11` | `11/11` | numbers.md §6.2 | yes |
| rule text METHODOLOGY.md:5551 contains the quoted phrase | `**Not accuracy comparisons** (ruling)` | `**Not accuracy comparisons** (ruling)` | METHODOLOGY.md:5551 (read at build time) | yes |
| H2.3 live max/min ratio A / B / C / D | `1.97 / 2.36 / 1.42 / 1.57` | `1.97 / 2.36 / 1.42 / 1.57` | numbers.md §16.1 P-T3 | yes |
| Experiment 2: flights per condition A / B / C / D | `3 / 3 / 3 / 3` | `3 / 3 / 3 / 3` | numbers.md §16.1 heading ('3 repeats per condition') | yes |
| rule text METHODOLOGY.md:10178 contains the quoted phrase | `live errors are similar` | `live errors are similar` | METHODOLOGY.md:10178 (read at build time) | yes |
| rule text METHODOLOGY.md:10179 contains the quoted phrase | `is ≤ 1.5 × the smallest` | `is ≤ 1.5 × the smallest` | METHODOLOGY.md:10179 (read at build time) | yes |
| rule text METHODOLOGY.md:12803 contains the quoted phrase | `is descriptive only (n = 3)` | `is descriptive only (n = 3)` | METHODOLOGY.md:12803 (read at build time) | yes |
| Experiment 4: flights in which EKF3 live has the largest indoor RMSE | `3/3` | `3/3` | numbers.md §16.2 H-O2 bullet (EKF3 largest in every flight) | yes |
| rule text METHODOLOGY.md:10360 contains the quoted phrase | `live indoor errors are similar` | `live indoor errors are similar` | METHODOLOGY.md:10360 (read at build time) | yes |
| rule text METHODOLOGY.md:10361 contains the quoted phrase | `is ≤ 1.5 × the smallest` | `is ≤ 1.5 × the smallest` | METHODOLOGY.md:10361 (read at build time) | yes |
| Experiment 4 FGO whole-flight batch vs smoothed UKF ratio, max/min per flight (capped) | `1.01–1.02` | `1.01–1.02` | numbers.md §16.2 P-O3 | yes |
| rule text METHODOLOGY.md:10362 contains the quoted phrase | `within 1.5× of each other in every` | `within 1.5× of each other in every` | METHODOLOGY.md:10362 (read at build time) | yes |
| Experiment 3 H3.1 / H3.2 / H3.3 / H3.4: flights passing, of 3 | `3/3 3/3 3/3 3/3` | `3/3 3/3 3/3 3/3` | numbers.md §16.3 ('H-L1 (primary), H-L2, H-L3 and P-L4: PASS 3/3') | yes |
| Experiment 3 with loop closure, live overall (m) | `0.049–0.076` | `0.049–0.076` | numbers.md §16.3 | yes |
| Experiment 3 without loop closure, live overall (m) | `0.263–0.361` | `0.263–0.361` | numbers.md §16.3 | yes |
| rule text METHODOLOGY.md:10503 contains the quoted phrase | `LC live overall RMSE < no-LC live overall RMSE in 3/3 flights` | `LC live overall RMSE < no-LC live overall RMSE in 3/3 flights` | METHODOLOGY.md:10503 (read at build time) | yes |
| rule text METHODOLOGY.md:10504 contains the quoted phrase | `LC hindsight overall RMSE < no-LC hindsight overall RMSE in 3/3 flights` | `LC hindsight overall RMSE < no-LC hindsight overall RMSE in 3/3 flights` | METHODOLOGY.md:10504 (read at build time) | yes |
| rule text METHODOLOGY.md:10501 contains the quoted phrase | `the lap-5 RMSE is ≤ 1.5 × the lap-1 RMSE in 3/3` | `the lap-5 RMSE is ≤ 1.5 × the lap-1 RMSE in 3/3` | METHODOLOGY.md:10501 (read at build time) | yes |
| rule text METHODOLOGY.md:10505 contains the quoted phrase | `lap 5 > 1.5 × lap 1 in 3/3 flights` | `lap 5 > 1.5 × lap 1 in 3/3 flights` | METHODOLOGY.md:10505 (read at build time) | yes |
| docs/tag_hold_design.md:176-188 (§e hypotheses) identical at c11fcf3 (2026-10-08 15:17) and at build time | `True` | `True` | git show c11fcf3:docs/tag_hold_design.md | yes |
| Experiment 5 (final-build sets): flights with the FGO / the UKF lowest mean hold error | `0/3 / 3/3` | `0/3 / 3/3` | numbers.md §17.2 criteria table (H-H2: 'FAIL (0/3): UKF lowest 3/3') | yes |
| Experiment 5 hold UKF / FGO / EKF3, final-build sets (mm) | `6.4–7.1 / 8.3–8.6 / 7.8–7.9` | `6.4–7.1 / 8.3–8.6 / 7.8–7.9` | numbers.md §17.2 criteria table (re-flown) | yes |
| H5.3 / H5.4b max/min, final-build sets | `2.40–2.58 / 3.2–7.7` | `2.40–2.58 / 3.2–7.7` | numbers.md §17.2 criteria table | yes |
| H5.4a EKF3 15 s re-lock jump per flight (mm) | `5 / 5 / 7` | `5 / 5 / 7` | numbers.md §17.2 criteria table (H-H4 (15 s)) | yes |
| Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds) | `FAIL; FAIL; FAIL; FAIL` | `FAIL; FAIL; FAIL; FAIL` | numbers.md §17.2 (final-build sets primary, ruling 2026-10-16) | yes |
| verbatim quote tag_hold_design.md:180 | `H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.` | `H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.` | docs/tag_hold_design.md:180-180 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:183 | `P-H3 (smoothness, prediction): gyro activity in the hold windows within 1.5× across estimators.` | `P-H3 (smoothness, prediction): gyro activity in the hold windows within 1.5× across estimators.` | docs/tag_hold_design.md:183-183 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:185–186 | `After the 15 s occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's and the FGO's in 3/3 flights.` | `After the 15 s occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's and the FGO's in 3/3 flights.` | docs/tag_hold_design.md:185-186 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:187 | `After the 5 s occlusion (no timeout), the jumps are within 1.5× of each other.` | `After the 5 s occlusion (no timeout), the jumps are within 1.5× of each other.` | docs/tag_hold_design.md:187-187 (read at build time; emphasis and bullets removed) | yes |
| rule text METHODOLOGY.md:12236 contains the quoted phrase | `H-H2 FAILS` | `H-H2 FAILS` | METHODOLOGY.md:12236 (read at build time) | yes |
| rule text METHODOLOGY.md:13549 contains the quoted phrase | `ALL FAIL` | `ALL FAIL` | METHODOLOGY.md:13549 (read at build time) | yes |
| rule text METHODOLOGY.md:4948 contains the quoted phrase | `[+155, +215] s` | `[+155, +215] s` | METHODOLOGY.md:4948 (read at build time) | yes |
| rule text METHODOLOGY.md:7513 contains the quoted phrase | `[+146, +218] s` | `[+146, +218] s` | METHODOLOGY.md:7513 (read at build time) | yes |
| rule text METHODOLOGY.md:8995 contains the quoted phrase | `[+145, +196] s` | `[+145, +196] s` | METHODOLOGY.md:8995 (read at build time) | yes |
| rule text METHODOLOGY.md:4951 contains the quoted phrase | `B1.` | `B1.` | METHODOLOGY.md:4951 (read at build time) | yes |
| rule text METHODOLOGY.md:4966 contains the quoted phrase | `B5.` | `B5.` | METHODOLOGY.md:4966 (read at build time) | yes |
| rule text METHODOLOGY.md:7362 contains the quoted phrase | `S2 is the estimator valid throughout` | `S2 is the estimator valid throughout` | METHODOLOGY.md:7362 (read at build time) | yes |
| rule text METHODOLOGY.md:9355 contains the quoted phrase | `DESCRIPTIVE; separate flights, n = 3 each, no ordering claim` | `DESCRIPTIVE; separate flights, n = 3 each, no ordering claim` | METHODOLOGY.md:9355 (read at build time) | yes |

### Table 7.2 (internal T7, table): Failure behaviour: blank-floor validity, the Experiment 4 return jump and the 5S safety tests

- **Caption:** How each estimator fails: EKF3 declares its blank-floor position invalid while the UKF and the FGO run away with no invalid period recorded [a]; on the return to GNSS EKF3 jumps 4.1 m [b]; in the hold safety tests (5S) the final run of each test (the latest on the final build: the final UKF port's re-test, the FGO corrected-priors node) passes as worded except the UKF node-kill test's position-lost declaration, which fails as worded in both final-port runs (a relay-drain timing fault in the bound) [c]. The FGO safety re-tests (corrected-priors node) used the corrected initial priors; the flown FGO hold and closed-loop corridor results (final FGO node) used the original priors.
- **Inputs:** eval/results/blank_behaviour.json; expO/O_r1.json, O_r2.json, O_r3b.json (max_step_after_return_m); expH/safety_*.json
- **numbers.md rows:** §6.2, §15 safety and history rows, §16.2; METHODOLOGY 'H safety test …' entries, 2d, rulings 2026-10-11, 'Band C … FGO safety re-tests'

| check | computed | expected | source | match |
|---|---|---|---|---|
| METHODOLOGY.md:11490 and :11827 (the single-landing reasons cited in Table 7.2) | `- **S-A4:** not applicable (an (a) run). | - **S-A4:** not scored (no touchdown). One LAND entry, no conflict between the two paths.` | `- **S-A4:** not applicable (an (a) run). | - **S-A4:** not scored (no touchdown). One LAND entry, no conflict between the two paths.` | METHODOLOGY.md lines 11490, 11827 (read at build time) | yes |
| EKF3 blank invalid (s of cruise); valid airborne flow frames | `301–310; max 0` | `301–310; max 0` | numbers.md §6.2 | yes |
| Experiment 4 largest step in 10 s after return EKF3 / UKF / FGO live (m) | `4.10–4.10 / 2.30–2.44 / 2.14–2.28` | `4.10–4.10 / 2.30–2.44 / 2.14–2.28` | numbers.md §16.2 table | yes |
| UKF node-kill test, earlier final-build run / final re-test: position-lost delay (s), verdict | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | numbers.md §15 history row (v2) and safety row (v3, final) | yes |
| UKF forced-invalid test, earlier final-build run / final re-test: verdict | `ALL PASS / ALL PASS` | `ALL PASS / ALL PASS` | numbers.md §15 history row (v2) and safety row (v3, final) | yes |
| corrected-priors node: forced-invalid position-lost delay / drift; node-kill | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | numbers.md §15 safety row (v4, final); METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS' | yes |
| final FGO node runs: forced-invalid position-lost delay / drift; node-kill | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | numbers.md §15 history row (v3, earlier final-build run) | yes |
| FGO node-kill first run safe landing; UKF forced-invalid first run position lost / safe landing | `False; False / False` | `False; False / False` | numbers.md §15 history row (S-A3 FAIL; S-A2 FAIL as worded, S-A3 FAIL) | yes |
| EKF3 reference drift (m) | `1.40` | `1.40` | numbers.md §15 history row | yes |
| rule text METHODOLOGY.md:11298 contains the quoted phrase | `FGO: within **0.75 s** of the kill` | `FGO: within **0.75 s** of the kill` | METHODOLOGY.md:11298 (read at build time) | yes |
| rule text METHODOLOGY.md:11299 contains the quoted phrase | `UKF (a): within **0.1 s** of TFAIL` | `UKF (a): within **0.1 s** of TFAIL` | METHODOLOGY.md:11299 (read at build time) | yes |
| rule text METHODOLOGY.md:11300 contains the quoted phrase | `UKF (b): within **5.5 s** of the kill` | `UKF (b): within **5.5 s** of the kill` | METHODOLOGY.md:11300 (read at build time) | yes |
| n flights UKF / FGO | `11/11` | `11/11` | numbers.md §6.2 | yes |
| EKF3 blank invalid for (s of cruise), all 14 | `301–310 (n 14)` | `301–310 (n 14)` | numbers.md §6.2 ('blank from take-off (all 14), for 301–310 s') | yes |
| rule text METHODOLOGY.md:5551 contains the quoted phrase | `**Not accuracy comparisons** (ruling)` | `**Not accuracy comparisons** (ruling)` | METHODOLOGY.md:5551 (read at build time) | yes |
| rule text METHODOLOGY.md:10365 contains the quoted phrase | `Reported regardless` | `Reported regardless` | METHODOLOGY.md:10365 (read at build time) | yes |
| rule text METHODOLOGY.md:11295 contains the quoted phrase | `S-A1 (attitude correct, not frozen)` | `S-A1 (attitude correct, not frozen)` | METHODOLOGY.md:11295 (read at build time) | yes |
| rule text METHODOLOGY.md:11297 contains the quoted phrase | `S-A2 (trigger)` | `S-A2 (trigger)` | METHODOLOGY.md:11297 (read at build time) | yes |
| rule text METHODOLOGY.md:11300 contains the quoted phrase | `within **5.5 s** of the kill` | `within **5.5 s** of the kill` | METHODOLOGY.md:11300 (read at build time) | yes |
| rule text METHODOLOGY.md:11301 contains the quoted phrase | `S-A3 (safe landing)` | `S-A3 (safe landing)` | METHODOLOGY.md:11301 (read at build time) | yes |
| rule text METHODOLOGY.md:11307 contains the quoted phrase | `S-A4 (b runs only)` | `S-A4 (b runs only)` | METHODOLOGY.md:11307 (read at build time) | yes |

### Table A.1 (internal A1, appendix): Closed loop: every flown build against the five closed-loop criteria and the contact window

- **Caption:** Pass/fail of every closed-loop corridor set, computed from the closed-loop score files, with the build ablations labelled: the UKF earlier build (pre-jitter fix) against the final UKF port; the FGO earlier build (original, hard-gated and robust), the ablation build (noise fix only) and the final FGO node (original priors); no ordering between builds or estimators is claimed [a].
- **Inputs:** eval/results/closed_loop_<trial>.json
- **numbers.md rows:** §15 (contacts, B1–B5 counts, B2, B3, re-flown sets); claim 14

| check | computed | expected | source | match |
|---|---|---|---|---|
| EKF3 half real-time contact MISS | `MISS` | `MISS` | numbers.md §15 (D21) | yes |
| UKF earlier build, half real-time, with-heading set | `2/3` | `2/3` | numbers.md §15 (r3 B4 0.296 m/s) | yes |
| final UKF port / final FGO node with-heading sets | `3/3 PASS / 3/3 PASS` | `3/3 PASS / 3/3 PASS` | numbers.md §15 (re-flown sets) | yes |
| FGO ablation build with-heading set | `3/3 PASS` | `3/3 PASS` | numbers.md §15 | yes |
| FGO earlier build, hard-gated / robust with-heading sets | `3/3 PASS / 3/3 PASS` | `3/3 PASS / 3/3 PASS` | numbers.md §15 (D28) | yes |
| contacts UKF earlier build (half real-time) / final UKF port / FGO earlier build / FGO ablation build / final FGO node (s) | `+198.0 / +165.9 / +165.8 / +169.6 / +169.9` | `+198.0 / +165.9 / +165.8 / +169.6 / +169.9` | numbers.md §15 contact rows | yes |
| real-time no-heading contact: EKF3; UKF earlier build | `+186.2; +163.0` | `+186.2; +163.0` | numbers.md §15 rows 1–2 | yes |
| UKF earlier build (half real-time) / FGO earlier build heading error p95/max ranges | `0.18–0.21° / 0.28–1.32°; 0.26–0.38° / 1.28–1.88°` | `0.18–0.21° / 0.28–1.32°; 0.26–0.38° / 1.28–1.88°` | numbers.md §15 B3 row (original builds) | yes |
| rule text METHODOLOGY.md:9355 contains the quoted phrase | `no ordering claim` | `no ordering claim` | METHODOLOGY.md:9355 (read at build time) | yes |

### Table A.2 (internal A2, appendix): Experiment 5 hold sets and the 5S safety tests (all runs)

- **Caption:** Experiment 5 hold sets (EKF3-flying, near and far spawn; UKF-flying, earlier and final builds; FGO-flying, ablation and final builds) with hold error, drift, lockouts and the drift bands (H5.5), and every 5S safety-test run with its as-worded verdict; the final runs are the re-tests of the final UKF port and of the FGO corrected-priors node (corrected priors). The FGO safety re-tests (corrected-priors node) used the corrected initial priors; the flown FGO hold and closed-loop corridor results (final FGO node) used the original priors. The comparative criteria page gives the final-build sets (primary) beside the superseded builds; the final-build verdicts are identical to the original-build verdicts (all FAIL) [a]; the safety verdicts are per run [b].
- **Inputs:** eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json, safety_*.json
- **numbers.md rows:** §15 safety rows, §17, §17.1; METHODOLOGY 2d and 'Band C … FGO safety re-tests'

| check | computed | expected | source | match |
|---|---|---|---|---|
| hold window means, UKF-flying earlier / final build; FGO-flying ablation / final build (mm) | `4.9–6.3 ; 6.1–7.4 ; 7.6–8.2 ; 8.1–9.0` | `4.9–6.3 ; 6.1–7.4 ; 7.6–8.2 ; 8.1–9.0` | numbers.md §17.1 table | yes |
| lockouts, EKF3-flying near / far spawn; UKF-flying final; FGO-flying final | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | numbers.md §17, §17.1 | yes |
| rule text METHODOLOGY.md:11298 contains the quoted phrase | `FGO: within **0.75 s** of the kill` | `FGO: within **0.75 s** of the kill` | METHODOLOGY.md:11298 (read at build time) | yes |
| rule text METHODOLOGY.md:11299 contains the quoted phrase | `UKF (a): within **0.1 s** of TFAIL` | `UKF (a): within **0.1 s** of TFAIL` | METHODOLOGY.md:11299 (read at build time) | yes |
| rule text METHODOLOGY.md:11300 contains the quoted phrase | `UKF (b): within **5.5 s** of the kill` | `UKF (b): within **5.5 s** of the kill` | METHODOLOGY.md:11300 (read at build time) | yes |
| score-file bound_s differs from the pre-registered S-A2 bound only for the final UKF port's forced-invalid runs | `safety_ukf_a_v2, safety_ukf_a_v3` | `safety_ukf_a_v2, safety_ukf_a_v3` | eval/results/expH/safety_*.json (S-A2 bound_s) against METHODOLOGY.md:11298-11300; M:14263-14264 (scored with the 0.75 s bound) | yes |
| UKF forced-invalid, final UKF port runs: position-lost delay (s) against the pre-registered 0.1 s; verdict unchanged | `0.00 ≤ 0.1: True, score file True / 0.00 ≤ 0.1: True, score file True` | `0.00 ≤ 0.1: True, score file True / 0.00 ≤ 0.1: True, score file True` | M:11299; numbers.md §15 safety and history rows ('trigger 0.00 s from effect') | yes |
| UKF node-kill test, earlier final-build run / final re-test: position-lost delay (s), verdict | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | `5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED` | numbers.md §15 history row (v2) and safety row (v3, final) | yes |
| UKF forced-invalid test, earlier final-build run / final re-test: verdict | `ALL PASS / ALL PASS` | `ALL PASS / ALL PASS` | numbers.md §15 history row (v2) and safety row (v3, final) | yes |
| final FGO node runs: forced-invalid position-lost delay / drift; node-kill | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | `0.54 s / 0.83 m; 0.25 s / 1.19 m` | numbers.md §15 history row (v3, earlier final-build run) | yes |
| corrected-priors node: forced-invalid position-lost delay / drift; node-kill | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | `0.60 s / 1.45 m; 0.62 s / 0.21 m` | numbers.md §15 safety row (v4, final); METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS' | yes |
| corrected-priors node forced-invalid / node-kill verdict | `ALL PASS / ALL PASS` | `ALL PASS / ALL PASS` | numbers.md §15 safety row (v4, final) | yes |
| FGO ablation build forced-invalid / node-kill: position-lost delay s, drift m | `0.29 s, 0.78 m; 0.43 s, 1.27 m` | `0.29 s, 0.78 m; 0.43 s, 1.27 m` | numbers.md §15 history row | yes |
| history: drift (m) UKF forced-invalid re-run / UKF node-kill / FGO forced-invalid / FGO node-kill (2 m hold); UKF node-kill position-lost delay (s) | `0.42 / 0.28 / 0.37 / 1.25; 4.81` | `0.42 / 0.28 / 0.37 / 1.25; 4.81` | numbers.md §15 history row | yes |
| FGO node-kill first run safe landing; UKF forced-invalid first run position lost / safe landing | `False; False / False` | `False; False / False` | numbers.md §15 history row (S-A3 FAIL; S-A2 FAIL as worded, S-A3 FAIL) | yes |
| EKF3 reference drift (m) | `1.40` | `1.40` | numbers.md §15 history row | yes |
| verbatim quote tag_hold_design.md:180 | `H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.` | `H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.` | docs/tag_hold_design.md:180-180 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:183 | `P-H3 (smoothness, prediction): gyro activity in the hold windows within 1.5× across estimators.` | `P-H3 (smoothness, prediction): gyro activity in the hold windows within 1.5× across estimators.` | docs/tag_hold_design.md:183-183 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:185–186 | `After the 15 s occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's and the FGO's in 3/3 flights.` | `After the 15 s occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's and the FGO's in 3/3 flights.` | docs/tag_hold_design.md:185-186 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:187 | `After the 5 s occlusion (no timeout), the jumps are within 1.5× of each other.` | `After the 5 s occlusion (no timeout), the jumps are within 1.5× of each other.` | docs/tag_hold_design.md:187-187 (read at build time; emphasis and bullets removed) | yes |
| docs/tag_hold_design.md:176-188 (§e hypotheses) identical at c11fcf3 (2026-10-08 15:17) and at build time | `True` | `True` | git show c11fcf3:docs/tag_hold_design.md | yes |
| verbatim quote METHODOLOGY.md:10687–10688 | `H-H1 (primary, EKF3 flying): mean hold error ≤ 0.05 m and max ≤ 0.15 m in every pre-loss hold window, 3/3 flights.` | `H-H1 (primary, EKF3 flying): mean hold error ≤ 0.05 m and max ≤ 0.15 m in every pre-loss hold window, 3/3 flights.` | METHODOLOGY.md:10687-10688 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote METHODOLOGY.md:10689–10692 | `P-H5 (drift during loss, per estimator): EKF3 and FGO: drift at the end of the 5 / 15 / 30 s hover losses ≤ 0.05 / 0.10 / 0.20 m. UKF: ≤ 2× those. Loss during the move (12 s): ≤ 0.15 m for EKF3 and FGO, 0.30 m for the UKF.` | `P-H5 (drift during loss, per estimator): EKF3 and FGO: drift at the end of the 5 / 15 / 30 s hover losses ≤ 0.05 / 0.10 / 0.20 m. UKF: ≤ 2× those. Loss during the move (12 s): ≤ 0.15 m for EKF3 and FGO, 0.30 m for the UKF.` | METHODOLOGY.md:10689-10692 (read at build time; emphasis and bullets removed) | yes |
| rule text METHODOLOGY.md:10969 contains the quoted phrase | `These are the S1 bands.` | `These are the S1 bands.` | METHODOLOGY.md:10969 (read at build time) | yes |
| verbatim quote METHODOLOGY.md:10700 | `P-H7 (lockout): no estimator locks out the returning tag in any loss.` | `P-H7 (lockout): no estimator locks out the returning tag in any loss.` | METHODOLOGY.md:10700-10700 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:176–177 | `H-H1 (primary): every estimator holds within tag-fix accuracy. Mean hold error ≤ 0.05 m and max ≤ 0.15 m in 3/3 flights per estimator.` | `H-H1 (primary): every estimator holds within tag-fix accuracy. Mean hold error ≤ 0.05 m and max ≤ 0.15 m in 3/3 flights per estimator.` | docs/tag_hold_design.md:176-177 (read at build time; emphasis and bullets removed) | yes |
| verbatim quote tag_hold_design.md:188 | `P-H5 (drift during loss, prediction): GT drift during the 15 s occlusion ≤ 0.3 m for every estimator.` | `P-H5 (drift during loss, prediction): GT drift during the 15 s occlusion ≤ 0.3 m for every estimator.` | docs/tag_hold_design.md:188-188 (read at build time; emphasis and bullets removed) | yes |
| every hold window of every flying hold set: mean ≤ 50 mm and max ≤ 150 mm (H5.1 under either wording) | `True` | `True` | numbers.md §17, §17.1 (H-H1 PASS) | yes |
| 15 s loss drift of the flying final-build sets ≤ 0.3 m (H5.5, design-draft wording) | `True` | `True` | METHODOLOGY.md:12243 ('P-H5 PASSES: every estimator drifted ≤ 30 mm over the 15 s loss (≤ 0.3 m)') | yes |
| Experiment 5 comparative verdicts, final-build sets (primary) / superseded builds | `FAIL ; FAIL ; FAIL ; FAIL / FAIL ; FAIL ; FAIL ; FAIL` | `FAIL ; FAIL ; FAIL ; FAIL / FAIL ; FAIL ; FAIL ; FAIL` | numbers.md §17.2 criteria table (both sets) | yes |
| Experiment 5 hold UKF / FGO / EKF3, final-build sets (mm) | `6.4–7.1 / 8.3–8.6 / 7.8–7.9` | `6.4–7.1 / 8.3–8.6 / 7.8–7.9` | numbers.md §17.2 criteria table (re-flown) | yes |
| Experiment 5 hold UKF, superseded builds (mm) | `5.5–6.1` | `5.5–6.1` | numbers.md §17.2 criteria table (earlier sets) | yes |
| H5.3 max/min, final-build / superseded | `2.40–2.58 / 2.37–2.43` | `2.40–2.58 / 2.37–2.43` | numbers.md §17.2 criteria table | yes |
| H5.4b max/min, final-build / superseded | `3.2–7.7 / 3.4–5.9` | `3.2–7.7 / 3.4–5.9` | numbers.md §17.2 criteria table | yes |
| final safety runs: drift to touchdown, UKF forced-invalid / UKF node-kill / FGO forced-invalid / FGO node-kill (m) | `0.58 / 1.07 / 1.45 / 0.21` | `0.58 / 1.07 / 1.45 / 0.21` | numbers.md §15 safety row (final runs, restated 2026-10-16) | yes |
| raw single-landing entries in the early score files (PASS, LAND entries, disarm recorded) | `safety_ukf_a: False, 1, None, safety_fgo_b: False, 1, None` | `safety_ukf_a: False, 1, None, safety_fgo_b: False, 1, None` | eval/results/expH/safety_ukf_a.json, safety_fgo_b.json (the score files) | yes |
| Experiment 5 (final-build sets): flights with the FGO / the UKF lowest mean hold error | `0/3 / 3/3` | `0/3 / 3/3` | numbers.md §17.2 criteria table (H-H2: 'FAIL (0/3): UKF lowest 3/3') | yes |
| H5.3 / H5.4b max/min, final-build sets | `2.40–2.58 / 3.2–7.7` | `2.40–2.58 / 3.2–7.7` | numbers.md §17.2 criteria table | yes |
| H5.4a EKF3 15 s re-lock jump per flight (mm) | `5 / 5 / 7` | `5 / 5 / 7` | numbers.md §17.2 criteria table (H-H4 (15 s)) | yes |
| Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds) | `FAIL; FAIL; FAIL; FAIL` | `FAIL; FAIL; FAIL; FAIL` | numbers.md §17.2 (final-build sets primary, ruling 2026-10-16) | yes |
| rule text METHODOLOGY.md:12236 contains the quoted phrase | `H-H2 FAILS` | `H-H2 FAILS` | METHODOLOGY.md:12236 (read at build time) | yes |
| rule text METHODOLOGY.md:13549 contains the quoted phrase | `ALL FAIL` | `ALL FAIL` | METHODOLOGY.md:13549 (read at build time) | yes |
| rule text METHODOLOGY.md:11295 contains the quoted phrase | `S-A1 (attitude correct, not frozen)` | `S-A1 (attitude correct, not frozen)` | METHODOLOGY.md:11295 (read at build time) | yes |
| rule text METHODOLOGY.md:11297 contains the quoted phrase | `S-A2 (trigger)` | `S-A2 (trigger)` | METHODOLOGY.md:11297 (read at build time) | yes |
| rule text METHODOLOGY.md:11300 contains the quoted phrase | `within **5.5 s** of the kill` | `within **5.5 s** of the kill` | METHODOLOGY.md:11300 (read at build time) | yes |
| rule text METHODOLOGY.md:11301 contains the quoted phrase | `S-A3 (safe landing)` | `S-A3 (safe landing)` | METHODOLOGY.md:11301 (read at build time) | yes |
| rule text METHODOLOGY.md:11307 contains the quoted phrase | `S-A4 (b runs only)` | `S-A4 (b runs only)` | METHODOLOGY.md:11307 (read at build time) | yes |

### Table A.3 (internal A3, appendix): The robust-weighting test (H1.4), the Experiment 3 compute cost and the build ablations

- **Caption:** Pass/fail table for the robust-weighting test (H1.4), the Experiment 3 compute cost (diagnostic; linear values, no plot) and the build ablations: the UKF earlier build against the final UKF port; the FGO ablation build (noise fix only) against the final FGO node and the corrected-priors node; the note on the original priors flown by the FGO. H1.4 NOT met [a]; ablations descriptive [b]. The FGO safety re-tests (corrected-priors node) used the corrected initial priors; the flown FGO hold and closed-loop corridor results (final FGO node) used the original priors.
- **Inputs:** eval/results/f1_test.json; ~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/stats.json; closed_loop_*, expH/*
- **numbers.md rows:** §15.2 F1 row; §16.3 cost bullets; §15, §17.1

| check | computed | expected | source | match |
|---|---|---|---|---|
| H1.4 robust FGO lower yaw max on | `6/6` | `6/6` | numbers.md §15.2 F1 row | yes |
| H1.4 lockouts robust FGO = hard-gated UKF | `{"FGO_robust": 3, "UKF_hard": 3}` | `{"FGO_robust": 3, "UKF_hard": 3}` | numbers.md §15.2 | yes |
| H1.4 verdict (robust FGO better) | `False` | `False` | numbers.md §15.2 (NOT met, lockout tie) | yes |
| hard-gated FGO plain-wall yaw max (deg) | `4.59–5.03` | `4.59–5.03` | numbers.md §15.2 F1 row | yes |
| Experiment 3 with loop closure, median (ms) | `35–41` | `35–41` | numbers.md §16.3 (restated 2026-10-11) | yes |
| Experiment 3 without loop closure, median (ms) | `50–61` | `50–61` | numbers.md §16.3 | yes |
| Experiment 3 with loop closure, p99 (ms) | `80–94` | `80–94` | numbers.md §16.3 | yes |
| Experiment 3 without loop closure, wall time (s) | `7276–9583` | `7276–9583` | numbers.md §16.3 | yes |
| H1.4 bags in the test | `6` | `6` | numbers.md §15.2 F1 row (over the 6 bags) | yes |
| rule text METHODOLOGY.md:7921 contains the quoted phrase | `robust FGO better than hard-gated UKF` | `robust FGO better than hard-gated UKF` | METHODOLOGY.md:7921 (read at build time) | yes |
| rule text METHODOLOGY.md:7922 contains the quoted phrase | `episodes in total AND a lower yaw-error max on ≥ 4 of 6` | `episodes in total AND a lower yaw-error max on ≥ 4 of 6` | METHODOLOGY.md:7922 (read at build time) | yes |

## Appendix mapping: thesis label → internal code → output file

Generated from the item list and the printed text of each item (no hand-typed "used in" cell). Source of every thesis name: `docs/thesis/thesis_vocabulary.md` (row cited). The internal codes in this section are the point of the section: they are the trace back to the repository, the results record (`docs/thesis/numbers.md`) and METHODOLOGY.

### 1. Figures and tables

| thesis label | internal id | output files | title |
|---|---|---|---|
| Figure 4.1 | F2 | `F2_heading_stops_sideways_drift.png`, `F2_heading_stops_sideways_drift.pdf` | The camera heading stops the sideways drift: without it every estimator flies into the west wall |
| Figure 4.1b (provisional) | F9 | `F9_heading_error_closed_loop.png`, `F9_heading_error_closed_loop.pdf` | Without a heading source the heading error grows until the wall; with the camera heading it stays near zero |
| Table 4.1 | T2 | `T2_accuracy_heading.md`, `T2_accuracy_heading.tex`, `T2_accuracy_heading.png` | Position error without and with the camera heading (textured floor) |
| Table 4.2 | T3 | `T3_blank_floor.md`, `T3_blank_floor.tex`, `T3_blank_floor.png` | Blank floor: position error after the loss of flow aiding |
| Table 4.3 | T4 | `T4_closed_loop.md`, `T4_closed_loop.tex`, `T4_closed_loop.png` | Closed loop at half real-time (RTF 0.5): the final build of each estimator flying the vehicle |
| Figure 5.1 | F5 | `F5_T_tags_known_positions.png`, `F5_T_tags_known_positions.pdf` | Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm |
| Figure 5.2 | F7 | `F7_L_loop_closure.png`, `F7_L_loop_closure.pdf` | Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps |
| Figure 5.3 | F6 | `F6_O_outdoor_indoor.png`, `F6_O_outdoor_indoor.pdf` | Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight keeps the error near 1 m |
| Table 5.1 | T6 | `T6_O_indoor_rmse.md`, `T6_O_indoor_rmse.tex`, `T6_O_indoor_rmse.png` | Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off) |
| Table 5.2 | T8 | `T8_hindsight_ratio.md`, `T8_hindsight_ratio.tex`, `T8_hindsight_ratio.png` | Hindsight: the FGO whole-flight batch against the smoothed UKF |
| Table 6.1 | T5 | `T5_H_tag_loss_drift.md`, `T5_H_tag_loss_drift.tex`, `T5_H_tag_loss_drift.png` | Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators |
| Table 7.1 | T1 | `T1_scorecard.md`, `T1_scorecard.tex`, `T1_scorecard_p1.png`, `T1_scorecard_p2.png`, `T1_scorecard_p3.png` | Which estimator wins where (scorecard of the restated verdicts) |
| Table 7.2 | T7 | `T7_failure_behaviour.md`, `T7_failure_behaviour.tex`, `T7_failure_behaviour_p1.png`, `T7_failure_behaviour_p2.png` | Failure behaviour: blank-floor validity, the Experiment 4 return jump and the 5S safety tests |
| Table A.1 | A1 | `A1_closed_loop_builds.png`, `A1_closed_loop_builds.pdf` | Closed loop: every flown build against the five closed-loop criteria and the contact window |
| Table A.2 | A2 | `A2_H_and_safety_p1.png`, `A2_H_and_safety_p1.pdf`, `A2_H_and_safety_p2.png`, `A2_H_and_safety_p2.pdf`, `A2_H_and_safety_p3.png`, `A2_H_and_safety_p3.pdf` | Experiment 5 hold sets and the 5S safety tests (all runs) |
| Table A.3 | A3 | `A3_F1_cost_ablations_p1.png`, `A3_F1_cost_ablations_p1.pdf`, `A3_F1_cost_ablations_p2.png`, `A3_F1_cost_ablations_p2.pdf` | The robust-weighting test (H1.4), the Experiment 3 compute cost and the build ablations |

### 2. Experiments, datasets, criteria, labels and builds

| thesis label | internal code(s) | used in | vocabulary row |
|---|---|---|---|
| Experiment 1, corridor comparison | (no single code: the `dsn` / `fwdc` / `fwdplainc` datasets, Phases 3–5, the F tests, the closed-loop "Part 2") | Table 7.1 | §1; §2 row 1 |
| Experiment 1A, standard-sensor comparison | `dsn_*` batch | Table 4.2, Table 7.1, Table 7.2 | §2 row 6 |
| Experiment 1B, camera-heading studies | Phase 3, 4, 5; F1–F3c; plan step 2 | Table 4.2, Table 7.1, Table 7.2 | §2 row 7 |
| Experiment 1C, closed-loop corridor flights | `cl_*`; "Part 2" | Figure 4.1, Figure 4.1b (provisional), Table 4.3, Table 7.1, Table A.1 | §2 row 8 |
| Experiment 2, known tags | Experiment T | Figure 5.1, Table 5.2, Table 7.1 | §2 row 2 |
| Experiment 3, loop closure | Experiment L | Figure 5.2, Table 5.2, Table 7.1, Table A.3 | §2 row 3 |
| Experiment 4, outdoor–indoor | Experiment O | Figure 5.3, Table 5.1, Table 5.2, Table 7.1, Table 7.2, Table A.3 | §2 row 4 |
| Experiment 5, tag hold | Experiment H | Table 6.1, Table 7.1, Table A.2, Table A.3 | §2 row 5 |
| 5S safety tests | `H_safety_*`; safety (a) / (b) | Table 7.2, Table A.2 | §2 row 9 |
| condition A–D (8 / 4 / 2 / 1 tags; kept as letters) | Experiment T conditions A–D; `T_A` … `T_D` | Figure 5.1, Table 5.2, Table 7.1 | §8.1 row 29; §10 row 21 |
| standard-sensor dataset | `dsn` | Table 4.1, Table 4.2, Table 7.1 | §2 row 11 |
| heading-error decomposition of sideways drift | Phase 5 decomposition (`plots/lateral_checks.py` method) | Table 4.1 | §5 (under H1.3) |
| thesis-nav position-lost path (the Copter landing trigger) | `thesis_nav_check` | Table 7.2, Table A.2 | §8.3 |
| textured-wall camera dataset (upper bound) | `fwdc` | Table 4.1, Table 4.2, Table 7.1, Table A.3 | §2 row 13 |
| plain-wall camera dataset (featureless case) | `fwdplainc` | Table 4.1, Table 4.2, Table 7.1, Table A.3 | §2 row 14 |
| camera calibration flights | `p1c_*` | Table 4.2, Table 7.1 | §2 row 15 |
| cruise ATE | `evo -a (cruise)` | Table 4.1, Table 7.1 | §3 row 17 |
| contact window | closed-loop set (a) PRIMARY window; U3 | Figure 4.1, Figure 4.1b (provisional), Table 4.3, Table 7.1, Table A.1 | §3 row 20 |
| mission completion | B1 | Figure 4.1, Table 4.3, Table A.1, Table A.3 | §3 row 23 |
| cross-track bound | B2 | Figure 4.1, Figure 4.1b (provisional), Table 4.3, Table 7.1, Table A.1, Table A.3 | §3 row 24 |
| heading-error bound | B3 | Figure 4.1, Figure 4.1b (provisional), Table 4.3, Table 7.1, Table A.1, Table A.3 | §3 row 25 |
| lateral-speed bound | B4 | Figure 4.1, Figure 4.1b (provisional), Table 4.3, Table 7.1, Table A.1, Table A.3 | §3 row 26 |
| oscillation bound | B5 | Figure 4.1, Table 4.3, Table A.1, Table A.3 | §3 row 27 |
| estimator-validity criterion | closed-loop S2 ("+S2") | Figure 4.1, Figure 4.1b (provisional), Table 4.3, Table 7.1, Table A.1 | §3 row 28 |
| drift band | P-H5 | Table 6.1, Table 7.1, Table A.2 | §3 row 30 |
| lockout criterion (no lockout) | P-H7 | Table 6.1 | §3 row 32 |
| attitude criterion | S-A1 | Table 7.2, Table A.2 | §3 row 33 |
| position-lost declaration | S-A2 | Table 7.2, Table A.2 | §3 row 34 |
| safe landing | S-A3 | Table 7.2, Table A.2 | §3 row 35 |
| single landing | S-A4 | Table 7.2, Table A.2 | §3 row 35 |
| forced-invalid test | safety (a) PARAM (the FGO's (a) is a node kill) | Table 7.2, Table A.2, Table A.3 | §4 row 46 |
| node-kill test | safety (b) KILL | Table 7.2, Table A.2, Table A.3 | §4 row 46 |
| with / without heading | closed-loop set (b) / set (a) | Figure 4.1, Figure 4.1b (provisional), Table 4.1, Table 4.2, Table 4.3, Table 7.1, Table A.1, Table A.3 | §4 set letters |
| with / without loop closure | LC / no-LC / `nolc` | Figure 5.2, Table 7.1, Table A.3 | §8.1 row 31 |
| smoothed UKF | RTS-UKF | Figure 5.1, Figure 5.3, Table 5.1, Table 5.2, Table 7.1 | §4 row 38 |
| FGO whole-flight batch (hindsight) | FGO batch | Figure 5.1, Figure 5.3, Table 5.1, Table 5.2, Table 7.1 | §4 row 37; §8.1 row 33 |
| hard-gated FGO / hard-gated UKF / robust FGO | `FGO_hard` / `UKF_hard` / `FGO_robust` | Table A.1, Table A.3 | §8.1 row 34 |
| final build (final UKF port / final FGO node) | UKF v2 (`_v2`); FGO v3 (`_v3`); hold sets S2v2 / S3v2 | Figure 4.1, Figure 4.1b (provisional), Table 4.3, Table 6.1, Table 7.1, Table 7.2, Table A.1, Table A.2, Table A.3 | §4 row 40 |
| ablation build | FGO v2 (`_v2`); hold set S3; ABLATION | Table 7.2, Table A.1, Table A.2, Table A.3 | §4 row 41 |
| earlier build | UKF v1 ("old UKF"); original FGO; hold set S2 | Figure 4.1, Table 7.2, Table A.1, Table A.2, Table A.3 | §4 row 42 |
| corrected-priors node | FGO v4 (`4c07374b`) | Table 6.1, Table 7.2, Table A.2, Table A.3 | §4 row 43 |
| original / corrected priors (initial-uncertainty correction) | OLD / NEW priors; D18 model correction | Figure 4.1, Figure 4.1b (provisional), Table 4.3, Table 6.1, Table 7.1, Table 7.2, Table A.1, Table A.2, Table A.3 | §4 row 44 |
| EKF3-flying hold set (near / far spawn) | H stage S1 / S1 far | Table 6.1, Table 7.1, Table A.2 | §8.1 row 18 |
| UKF-flying hold set (earlier / final build) | H stage S2 / S2v2 | Table 6.1, Table A.2 | §8.1 row 18 |
| FGO-flying hold set (ablation / final build) | H stage S3 / S3v2 | Table 6.1, Table A.2, Table A.3 | §8.1 row 18 |
| half real-time (RTF 0.5) | `_half`; "half speed" (banned) | Figure 4.1, Figure 4.1b (provisional), Table 4.3, Table 7.1, Table A.1 | §4 row 45 |
| runaway magnitude (†) | † | Table 4.2, Table 7.1, Table 7.2 | §4 row 47 |
| EKF3 with the Python / C++ heading node | Python / C++ bridge; `bcpp` | Table A.1 | §8.1 row 40 |
| safety watcher | watcher | Table 7.2, Table A.2 | §8.1 row 41 |

### 3. Hypotheses and comparisons (thesis_vocabulary.md §5)

| thesis label | name in words | internal code | used in |
|---|---|---|---|
| H1.1 | standard-sensor ordering, EKF3 vs FGO (confirmatory) | the r4–r10 paired test | Table 4.1, Table 7.1 |
| H1.2 | heading-measurement validation | Phase 3 validation | Table 4.1, Table 7.1 |
| H1.3 | heading-fusion prediction (judged on the heading-error decomposition of sideways drift) | Phase 5 prediction; Phase 5 decomposition | Table 4.1 |
| C1.a | FGO vs UKF with heading (comparison, no decision rule) | C0 | Table 4.1, Table 7.1 |
| H1.4 | robust-weighting test | F1 (pre-registered) | Table A.1, Table A.3 |
| H2.1 | FGO hindsight gain grows with the gap | H-T1 | Figure 5.1, Table 7.1 |
| H2.2 | the same for the smoothed UKF | P-T2 | Figure 5.1 |
| H2.3 | live errors similar | P-T3 | Figure 5.1, Table 7.1 |
| H2.4 | FGO hindsight ≈ smoothed UKF | P-T4 | Figure 5.1, Table 5.2 |
| V3 | estimator validation check | V-L | Figure 5.2 |
| H3.1 | loop closure bounds live drift | H-L1 | Figure 5.2, Table 7.1 |
| H3.2 | live error lower with loop closure | H-L2 | Figure 5.2, Table 7.1 |
| H3.3 | hindsight error lower with loop closure | H-L3 | Figure 5.2, Table 7.1 |
| H3.4 | without loop closure, drift grows lap on lap | P-L4 | Figure 5.2, Table 7.1 |
| H4.1 | FGO hindsight beats the filters' live tracks indoors | H-O1 | Figure 5.3, Table 5.1, Table 7.1 |
| H4.2 | live indoor errors similar | H-O2 | Figure 5.3, Table 5.1, Table 7.1 |
| H4.3 | FGO batch ≈ smoothed UKF | P-O3 | Figure 5.3, Table 5.1, Table 5.2, Table 7.1 |
| H5.2 | FGO holds tightest | H-H2 | Table 6.1, Table 7.1, Table A.2 |
| H5.3 | smoothness similar | P-H3 | Table 6.1, Table 7.1, Table A.2 |
| H5.4a | after a 15 s loss, EKF3 jumps most | H-H4 (15 s) | Table 6.1, Table 7.1, Table A.2 |
| H5.4b | after a 5 s loss, jumps similar | H-H4 (5 s) | Table 6.1, Table 7.1, Table A.2 |
| H5.5 | drift band | P-H5 | Table 6.1, Table A.2 |
| H5.7 | no lockout | P-H7 | Table 6.1, Table A.2 |

