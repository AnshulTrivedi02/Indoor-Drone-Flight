# Candidate thesis figures, group A: setup and Experiment 1 (1A/1B/1C) (decision D124)

Built by `eval/figs_cand_a.py` at commit `b8812b6` (run with `/home/makerspace/venv-evo/bin/python`). These are CANDIDATES for the user to pick from - not inserted into the thesis figure set in `docs/thesis/figures_thesis/` itself. Stored outputs only: TUM files, eval/results/*.json, and a cache of dataflash/bag reads pre-populated by `eval/figs_walkthrough_flights.py --cache ~/thesis_data/cand_a_cache --extract-only` under `heavy.py` (that invocation writes nothing outside the cache directory). No estimator run, no simulation, no flight.

**Checks:** 78/78 EXACT (string equality after one rounding by `rd()`, parsed from `eval/figs_thesis.py`, sha256 of the source segment used to detect drift - see below).

**Style:** `eval/thesis_style.py` (160 mm / 6.30 in text width, Okabe-Ito palette, filled = live / open = hindsight, no in-figure titles, no verdict words, no bold text, panel labels (a)/(b)/... only where a figure has more than one panel). No two plots overlap; the F9 (Figure 4.1b) inset was split into its own stacked panel as part of this same group's brief (`eval/figs_thesis.py`, see docs/handovers/2026-11-04_cand_a.md).

## Candidates

| id | proposed title | source chart(s) | checks | verdict pointer |
|---|---|---|---|---|
| A01 | Where the drone really flew: Experiment 1A, 9 flights up the corridor | A01_1A_truth | 4/4 | Verdicts: Table A.4, none (descriptive). |
| A21 | Climb, cruise and landing: Experiment 1A, 9 flights up the corridor | A21_1A_height | 1/1 | Verdicts: Table A.4, none (descriptive). |
| A02 | Where the drone really flew: Experiment 1B, 3 flights with a roof and painted-line walls | A02_1B_truth | 4/4 | Verdicts: Table A.4, none (descriptive). |
| A22 | Climb, cruise and landing: Experiment 1B, 3 flights with a roof and painted-line walls | A22_1B_height | 1/1 | Verdicts: Table A.4, none (descriptive). |
| A03 | Where the drone really flew: the 12 tag-room flights of Experiments 2 and 3 | A03_2_truth | 2/2 | Verdicts: Table A.4, none (descriptive). |
| A04 | Where the drone really flew: the 3 outdoor-indoor flights of Experiment 4 | A04_4_truth | 3/3 | Verdicts: Table A.4, none (descriptive). |
| A05 | Where the drone really flew: the 12 hold flights of Experiment 5 | A05_5_truth | 2/2 | Verdicts: Table A.4, none (descriptive). |
| A06 | Where the drone really flew: the 4 final 5S safety runs | A06_5S_truth | 2/2 | Verdicts: Table A.4, none (descriptive). |
| A07 | Without a heading source the raw horizontal error grows to metres-to-tens-of-metres | walkthrough page 02 (fl_1A_unaligned_err.png) | 1/1 | Verdicts: Table A.4, rows H1.1. |
| A08 | The forward-camera heading check, by wall type and floor | summary page 03 / walkthrough page 04 | 8/8 | Verdicts: Table A.4, rows H1.2 heading and yaw rate, textured walls; H1.2 heading, plain walls over blank and transition floors; H1.2 heading, plain walls over the checkerboard floor. |
| A09 | With the camera heading the UKF and FGO paths stay on the true path | walkthrough page 05 (fl_1B_unaligned_paths.png, plots only) | 2/2 | Verdicts: Table A.4, none (descriptive). |
| A10 | Experiment 1B: registered score and raw maximum error, without and with the camera heading | walkthrough page 05 (fl_1B_unaligned_paths.png, in-figure table) | 11/11 | Verdicts: Table A.4, none (descriptive). |
| A11 | Without the camera heading the raw error grows through the cruise | walkthrough fl_1B_unaligned_err_noheading.png (generated, not composed into a numbered walkthrough page since D63) | 1/1 | Verdicts: Table A.4, none (descriptive). |
| A12 | With the camera heading the raw error stays close to the true path | walkthrough fl_1B_unaligned_err_heading.png (generated, not composed into a numbered walkthrough page since D63) | 1/1 | Verdicts: Table A.4, none (descriptive). |
| A13 | Without the camera heading the flying estimator drifts to the wall; with it the path stays straight | walkthrough page 07 (fl_1C_paths.png) | 9/9 | Verdicts: Table A.4, rows H1.8 EKF3, half real-time (RTF 0.5); H1.8 UKF; H1.8 FGO; H1.9 EKF3; H1.9 UKF; H1.9 FGO. |
| A14 | Without a heading source each estimator's heading error grew until the wall | walkthrough page 08 (fl_1C_head_off.png) | 3/3 | Verdicts: Table A.4, rows H1.8 EKF3, half real-time (RTF 0.5); H1.8 UKF; H1.8 FGO. |
| A15 | With the camera heading the heading error stayed inside the ±2.0° band on every flight | walkthrough page 09 (fl_1C_head_on.png) | 2/2 | Verdicts: Table A.4, rows H1.9 EKF3; H1.9 UKF; H1.9 FGO. |
| A16 | Without a heading source the true sideways position runs to the wall | walkthrough page 10 (fl_1C_side_off.png) | 4/4 | Verdicts: Table A.4, rows H1.8 EKF3, half real-time (RTF 0.5); H1.8 UKF; H1.8 FGO. |
| A17 | With the camera heading the true sideways position stays near the centre line | walkthrough page 11 (fl_1C_side_on.png) | 3/3 | Verdicts: Table A.4, rows H1.9 EKF3; H1.9 UKF; H1.9 FGO. |
| A18 | Without a heading source every estimator's wall contact fell near its pre-registered window | summary page 05 (new_page('05', ...)) | 4/4 | Verdicts: Table A.4, rows H1.8 EKF3, half real-time (RTF 0.5); H1.8 UKF; H1.8 FGO. |
| A19 | With the camera heading the largest sideways drift stayed well inside the 6.0 m limit | summary page 06 (new_page('06', ...)) | 4/4 | Verdicts: Table A.4, rows H1.9 EKF3; H1.9 UKF; H1.9 FGO. |
| A20 | Five more no-heading flights: every one also reached the west wall | extra/ex_1C_extra.png | 6/6 | Verdicts: Table A.4, none (descriptive). |

## Skipped (content already a figure/table in docs/thesis/figures_thesis/)

| source chart | already covered by | reason |
|---|---|---|
| walkthrough page 01, fl_1A_unaligned_paths.png (9-flight raw PATHS, one panel per estimator) | Figure 4.1d (internal R6) | identical data and layout: all 9 standard-sensor textured flights, per-estimator panel, raw (not fitted) top-down path, truth grey, equal scale (confirmed by reading both generators) |
| summary page 02 / walkthrough page 03, blank floor (1A/1B) | Table 4.2 (internal T3) | the summary page is a TABLE ONLY (no chart): estimator x {error 10 s after flow loss, 30 s after, end of cruise}, the exact content of T3 |
| summary page 04, 1B accuracy (with/without heading) | Table 4.1 (internal T2) | the summary page is a TABLE ONLY (no chart): painted-line/plain-wall cruise ATE without and with the camera heading, a subset of T2's own rows (same phase4_fwdc_evo.json / phase4_fwdplainc_evo.json source) |

## Judgement calls for the coordinator

- **A13 (`1C_paths`) and A14/A15/A16/A17 overlap F2/Figure 4.1 and F9/Figure 4.1b in DATA (the same 12 closed-loop flights), not in layout**: F2/F9 draw one combined overlay per figure; A13/A14/A16 (no-heading) and A15/A17 (with-heading) draw one panel PER ESTIMATOR, the layout the group brief and the user's own 2026-10-21 walkthrough request asked for ('I dont want the heading error graphs imposed on each other'). Kept as candidates per the group brief's explicit list; flagged here since 'same data, different layout' is a judgement call on the 'already a figure' skip rule, not a clean duplicate.
- **A18/A19 (summary page 05/06 charts)** are new chart TYPES (a window/contact dot chart; a max-cross-track bar chart) not drawn by any figures_thesis figure; both point at a SUBSET of F2/F9's H1.8/H1.9 rows (A18: H1.8 only, the no-heading condition; A19: H1.9 only, the with-heading condition) rather than all six, since each chart only shows that one condition.
- **A04/A05/A06 (4_truth/5_truth/5S_truth)** are setup/truth views of Experiments 4 and 5/5S, which are otherwise group B's and group C's scope; included here only because this group's brief explicitly lists them ('if they are setup views of other experiments: include them as setup candidates') and `eval/figs_walkthrough_flights.py` groups all truth pages together. If group B or C also produces a truth-page candidate for these experiments, the coordinator should keep one.
- **A08/A10 are rendered tables, not plots** (D113/common-brief rule: 'tables drawn inside a chart become a separate markdown table candidate'; A08 has no accompanying chart at all in its source page, A10 is the in-figure table split off A09's paths). Rendered at 160 mm width like a compact figure rather than full A4-landscape (RS-3 exempts only DENSE multi-column tables, these are 3-4 columns).
- **A01/A02 were originally one candidate each with two STACKED panels (top-down path; height against time)** - fix sweep, 2026-11-04. Re-checked against the checklist's 'stacked only on a shared scale': the two panels shared NEITHER axis (position in metres vs height against time in seconds), unlike the group's own F9 split (c2cad19), whose two panels share one time axis. Split into A01/A02 (top-down only) and NEW ids A21/A22 (height-against-time only, same flight sets). A04-A06 (room_cand()) are unaffected - one row of panels sharing one pair of axes throughout, never stacked at a different scale.

