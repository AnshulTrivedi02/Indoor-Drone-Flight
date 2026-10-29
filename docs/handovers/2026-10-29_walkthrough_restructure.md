# Handover 2026-10-29: results walkthrough restructure and the E4 redesign

**Request:** the user's two tasks of 2026-10-29: (1) remove redundant plots from `results_walkthrough.pdf`, merge the Experiment 4
and Experiment 5 plots, and print the Metric / Pass rule / Result block once per experiment; (2) redesign the Extension E4 figure
as an honest compute-against-accuracy trade-off. No number, pass rule or registered verdict changed. Decisions D61 to D68 are in
`docs/thesis/tier1/decisions_log.md`.

## What changed
- **`eval/figs_results_walkthrough.py`** (composer): the page section is rewritten.
  - A setup section shows the corridor (world and `fl_1A_truth`) and the tag room (world and `fl_2_truth`, the 6 m square) once.
  - Every world is pictured once. The 1B world page now also carries the plain-wall corridor interior, so it covers the ablation too.
  - Each summary page's Metric / Pass rule / Result appears exactly once (asserted, 57/57).
  - The two merged figures get a text intro page (D62). The appendix holds the E3 verdict table, the E3 maps (optional) and the E4 change plot.
  - New checks: the exactly-once rule; no em-dash in any page text; exactly one FITTED / NOT FITTED label per plot page.
  - The world check now counts trial sets (15), not page groups (14).
- **`eval/figs_walkthrough_flights.py`** (all-flights plots):
  - New `fl_4_err`: 3 × 2 panels, live and hindsight, one y-scale, D64.
  - New checks: the 1B with-heading not-fitted maximum (0.54 m, D63) and its data identity.
  - The other 25 PNGs are byte-identical to HEAD.
- **`eval/figs_walkthrough_extra.py`** (new, CPU-light): `extra/ex_5_hold_drift.png` (D65) and `extra/ex_E4_tradeoff.png`
  (D66, D67), with `extra/index_extra.md` and `extra/checks.json`. Each printed number is rounded once by rd(). It must equal the
  thesis display string and, where summary pages 10, 11, 16 or 17 print it, that page's check row in `index_summary.md`.
- **Not touched:** `figs_thesis_summary.py`, `summary_plots.pdf`, `index_summary.md` (byte-identical), numbers.md, the frozen pack,
  `figures_thesis/`, `tables/`, and the tier-1 and ablation result files.

## Pages (37, was 58)
contents, how to read; setup: corridor world, corridor path, tag-room world, 6 m square; 1A: Fig 4.2a (block), raw error;
blank floor: world, table; 1B: world (1B + ablation), heading check table, Fig 4.2b (block), five-panel raw paths; 1C: world,
paths (block), heading error without; heading error with (block, 0.39 m sentence); 2: F5; 3: F7; 4: world, merged live +
hindsight; 5: world (5 and 5S), intro (blocks 10 + 11), two-panel figure; 5S: table; section; E2; E3 outcome; E4: intro
(blocks 16 + 17), trade-off figure; E5; ablation; appendix section; E3 verdicts; E3 maps; E4 change.

## Checks
| | before (b30f06d) | after |
|---|---|---|
| walkthrough verbatim | 183/183 | 91/91 |
| walkthrough MODIFIED | 20 | 5 |
| walkthrough NEW | 106 | 75 |
| walkthrough world check | 14/14 page groups | 15/15 trial sets |
| block printed exactly once | n/a | 57/57 |
| flights printed-number | 46/46 | 50/50 |
| flights data-identity | 152/152 | 153/153 |
| extra (new) | n/a | 59/59 |
| summary (untouched) | 196/196, 50/50, 86/86, 13/13 | same |
| PDF pages | 58 | 37 |

The verbatim, MODIFIED and NEW counts fall because each summary line is now printed once, not on every page, and because the PDF
now has 24 plot pages (was 41), 7 world pages (was 14) and 2 intro pages.

Other checks: `check_numbers_frozen.py` PASS; `check_claims_applied.py` 58/58; `check_discussion.py` 18/18; `check_ablation.py`
228/0. Every file sha256 record under `docs/thesis/` matches its file. The only exceptions are three rows that hash rd()'s source
text, not a file.

## Heavy step
- `figs_walkthrough_flights.py` was run twice through `heavy.py`, with nothing else running.
- The cache was `~/thesis_data/walkthrough_cache` (33 MB). The second run took 36 s with the cache warm.
- The cache was deleted afterwards (`rm -rf ~/thesis_data/walkthrough_cache`).

## Rebuild order
1. Run `~/venv-evo/bin/python eval/figs_walkthrough_flights.py --cache <dir>`. It needs the bags, so run it through `heavy.py`.
2. Run `python3 eval/figs_walkthrough_extra.py`.
3. Run `python3 eval/figs_results_walkthrough.py`.
4. Restore any pixel-identical `wt_00b_how_to_read.png` to HEAD bytes.
5. Re-verify the sha256 records.

## Flags for the user
- **1B "below about 0.5 m":** the stored largest with-heading raw error is 0.54 m (UKF, fwdc_tex_r3, near the end of the cruise), so
  the text says "about 0.5 m at most (largest 0.54 m)".
  - The old page 11c text "stays below about half a metre" was also slightly wrong.
- **E4 "about 20 times":** the per-flight ratio is 18.7 to 20.3, printed as "19 to 20 times".
- **E4 "about 14 ms" / "about 290 ms":** the stored values are 14.35–15.13 ms and 278.25–303.36 ms; the ranges are printed.
- **Delta plot:** the plot moved to the appendix is the current four-panel change plot (about ±0.009 m), not the pre-b30f06d ±0.001 m plot.
- **Standalone E4 compute-time page:** dropped; the left panel of the new figure replaces it.
- **Routes no longer drawn:** the outdoor–indoor route and the hold routes, since their "where the drone really flew" pages were removed.
- **Historical records:** `claims_applied.md` and `units.md` still name the old walkthrough page files and numbers. They are left as written.
- **Not merged.**
