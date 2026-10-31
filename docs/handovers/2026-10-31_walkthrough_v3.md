# Handover 2026-10-31: results walkthrough, second restructure (v3)

**Request:** the user's instructions of 2026-10-31 (ALL FLIGHTS, RAW FIRST; SELF-EXPLANATORY PLOTS; TASKS 1 to 6). No number, pass
rule or registered verdict changed. Decisions D69 to D79 are in `docs/thesis/tier1/decisions_log.md`. Not merged.

## What changed
- **`eval/figs_walkthrough_flights.py`** (all-flights plots; needs bags, run through `heavy.py`):
  - New visual language: a one-line finding title, the raw / fitted tag on the figure, walls as labelled grey bands beyond ±10 m, the
    y label once (`supylabel`), verdict marks equal to the summary check rows (`sumrow`).
  - Global checks in `save()`: no em-dash, every axis linear, every text inside the figure (measured at 200 dpi).
  - `fl_1A_unaligned_paths`: all 9 flights, one panel per estimator, equal and symmetric axes, plus the registered cruise-ATE table
    (4.10 / 5.13 / 4.46 m) and the ranking verdict (NOT MET).
  - `fl_1A_unaligned_err`: restyled, the y label printed once.
  - `fl_1B_unaligned_paths`: six panels (the sixth is the closed-loop EKF3 with heading, D70), symmetric x axis, wall bands, and the
    table of registered cruise-ATE ranges and raw maxima (D73).
  - `fl_1C_paths`: one panel per estimator; no heading dashed, with heading solid; X at each contact with its time, window and verdict.
  - `fl_1C_head_off`, `fl_1C_head_on`, `fl_4_err`: restyled, with verdicts on the panels.
  - New `fl_E3_maps` (D75). New extractor `ex_xkf1()`.
  - Dropped: the five fitted figures and their PNGs (D79).
- **`eval/figs_walkthrough_extra.py`** (stored result files only):
  - Restyled `ex_5_hold_drift` and `ex_E4_tradeoff`.
  - New `ex_2_known_tags`, `ex_3_loop_closure`, `ex_E2_fewer_tags` (hindsight means, D74), `ex_E3_table` and `ex_E5_ukf_landmarks`.
  - The same global checks and the number guard as the flights script.
- **`eval/figs_results_walkthrough.py`** (composer): new page type `fpage()`.
  - Each page carries a grey experiment label, the figure and a caption of at most two sentences (asserted).
  - For a reused image only (blank-floor table, heading-check table, ablation, E3 verdicts), the composer draws the finding title and
    the tag.
  - A new "How to read" page.
  - A "Registered results" section holds every Metric / Pass rule / Result, verbatim, once (57/57).
  - The Experiment 5S page is unchanged.
  - New checks:
    - captions ≤ 2 sentences;
    - verdict words in the composer's text occur in the registered Result;
    - exactly one raw / fitted tag per figure page;
    - stale page images in `walkthrough/` fail the build.
  - `--no-dividers` drops the three section pages.

## Pages: 40 (was 37); 37 with `--no-dividers`
contents, how to read; setup (corridor world, corridor path, tag-room world, 6 m square); 1A paths + ATE table, 1A raw error; blank
world, blank table; 1B worlds, heading check, 1B six-panel paths + table; 1C world, 1C paths, 1C heading error without, with;
Experiment 2; Experiment 3; Experiment 4 world, Experiment 4; Experiment 5 world, Experiment 5; 5S (unchanged); [extension section];
E2; E3 table; E3 maps; E4; E5; ablation; [registered section]; 6 registered-results pages; [appendix section]; E3 verdicts.

## Checks
| | before (1519f4e) | after |
|---|---|---|
| flights printed-number | 50/50 | 95/95 (4 removed with the fitted figures, 49 added) |
| flights data identity | 153/153 | 167/167 (14 added) |
| extra | 59/59 | 130/130 (71 added) |
| walkthrough verbatim | 91/91 | 112/112 |
| walkthrough MODIFIED | 5 | 0 (back to verbatim, D72) |
| walkthrough NEW | 75 | 80 |
| world check | 15/15 | 16/16 (the closed-loop EKF3 panel's flights) |
| block printed exactly once | 57/57 | 57/57 |
| summary (untouched) | unchanged | unchanged |

`check_numbers_frozen.py` PASS; `check_claims_applied.py` 58/58; `check_discussion.py` 18/18; `check_ablation.py` 228/0.

sha256 records: 59 file records under `docs/thesis/` checked. All match except the three known rows that hash rd()'s source text, not
a file.

## Heavy step
- `figs_walkthrough_flights.py --extract-only`, then the plots, were run through `heavy.py` with nothing else running.
- The cache was `~/thesis_data/walkthrough_cache`. It was deleted afterwards (`rm -rf ~/thesis_data/walkthrough_cache`).

## Rebuild order
1. `python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "<desc>" -- ~/venv-evo/bin/python eval/figs_walkthrough_flights.py --cache <dir>`
2. `python3 eval/figs_walkthrough_extra.py`
3. `python3 eval/figs_results_walkthrough.py`, with `--no-dividers` for the version without the section pages.

## Also changed after review
- On-plot tags use plain phrases ("measured from the start tag", "against the room's known tag map"), not "start-tag frame" or "room frame".
- Restored on the plots: the Experiment 2 hindsight gain (0.010, 0.011, 0.023, 0.052 m), the Experiment 4 EKF3 reset (4.10 m) and the
  indoor time (123 s), and the 1C largest 95th percentile (0.38°).
- The E4 caption says the right panel is the error itself; the registered metric is its change.
- The ablation title carries its verdicts (P2 PASS; P1 and P3 FAIL).

## Not redrawn (reused images)
- The ablation chart (summary page 19) keeps its legend.
- The setup truth figures (`fl_1A_truth`, `fl_2_truth`) keep their hairline walls, the "dark bands" subtitle and the flight legend.
- The blank-floor, heading-check and E3 verdict tables are the summary images; the composer adds the title and tag.

## Open for the user
- Is the output for the thesis or the standalone walkthrough? This decides the divider pages.
- The thesis Figure 5.2 (F7) title still says "3–4×". The walkthrough's own Experiment 3 figure says "2.9 to 4.5 times".
- Stored E3 runs exist for further tag maps: all 36 wrong-ID runs and the 3 robust controls (see the final report).
