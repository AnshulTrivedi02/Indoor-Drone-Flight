# Handover 2026-10-23: one unit per quantity across all thesis tables and figures

User ruling (verbatim): "Thesis tables use SI units, converted at generation time only; numbers.md stays exactly as is. Use one
unit per quantity, the same in a table as in its matching figure. SI prefixes are fine where they read better (e.g. drift in mm,
position error in m); pick the unit that keeps values readable and use it consistently. Keep the exact cross-check against the
stored values."

The choices, their reasons and where each quantity appears are in `docs/thesis/units.md`.

## Unit choices
| quantity | unit |
|---|---|
| position error (ATE, RMSE, blank-floor error, error after the GNSS return), cross-track, distances, heights | m |
| Experiment 5 hold quantities (hold error, tag-loss drift, re-lock jump, bands) | mm |
| 5S landing drift | m |
| compute times, step and sample periods, latencies | ms |
| flight times and durations | s |
| speeds | m/s |
| angles | ° |

- km values are printed in m, to the nearest 1000 m, with grouped digits (`29 000–40 000 m`).
- Verbatim pre-registration quotes keep their original units (listed in units.md).

## What changed
- `eval/figs_thesis.py`
  - Helpers:
    - New `grp()`/`NNBSP` (as in the summary).
    - New `mm_()`, an exact m → mm shift that replaces the `1e3 *` float multiplies in `drifts()`, `hE` and the band test.
    - `TEX_UNI` maps U+202F → `\,`.
  - T1: the Experiment 2 and 3 cells go cm → m, and the blank floor goes km → m. `ob_h23`/`ob_h24` now always print m (the `si`
    parameter is removed).
  - T2: the with-heading cross-track goes cm → m (3 dp), and its header gains "(m)". The caption says "hundredths of a metre".
  - T3: the end of cruise goes km → m, with the header "(m)". The caption says "errors of tens of thousands of metres".
  - T5: the caption says "about 30 mm" (was 3 cm).
  - T7: the end of cruise goes km → m, with a new check (T7 21 → 22).
  - T8: the RMSE columns go cm → m (3 dp), and footnote [c] says m.
  - A2: the hold, drift and jump return from m to mm (`hsum`, `hcomp`/`hctxt`, the note, `ob_h5`). A2 50 → 51 checks, because the
    mm hold check is now identical to the one in `ob_h5` and is counted once.
  - A3: the Experiment 3 step times return from s to ms, and the ablation hold/drift goes from m to mm.
- `eval/figs_thesis_results.py`
  - R4: the Experiment 2 RMSE goes cm → m, and the Experiment 4 error 10 s after return goes cm → m.
  - R1: "4 mm/s inside" becomes "0.004 m/s inside". A new `scheck()` checks it as the exact 0.25 − stored B4 max, against
    numbers.md:480 '4' × 10^-3.
- `eval/figs_thesis_summary.py`
  - Pages 10 and 11 go back to mm (axes, labels, bounds, metric and pass-rule text, and the index note).
  - New display check: hold limits 50 / 150 mm = the registered 0.05 / 0.15 m × 10^3.
  - Page 02's "shown in" check now looks for Table 4.2's grouped metres.
  - `drifts()` now uses an exact shift.
- `eval/figs_thesis_methods.py`: the predict period's s → ms conversion is now an exact shift. The output is unchanged.
- Regenerated:
  - tables T1, T2, T3, T5, T7, T8, R1 and R4;
  - figures A2 (p1, p3) and A3 (p1, p2);
  - summary pages 10 and 11, and walkthrough pages 24–26;
  - the indexes;
  - the combined PDFs `thesis_figures_combined.pdf`, `summary_plots.pdf` and `results_walkthrough.pdf`.
  - The summary and walkthrough PNGs that are pixel-identical were also kept, because `index_walkthrough.md` records their sha256.
  - Outputs whose only change was the commit line were restored: R2, T4, T6, the methods and realflight tables,
    `index_drift.md`, `index_methods.md`, `methods_architecture.*` and the unchanged figure PDFs.

## Checks (before → after)
| generator | before | after |
|---|---|---|
| figs_thesis | 336/336 | 336/336 (T7 +1, A2 −1 dedup) |
| figs_thesis_results | numeric 70/70, source 185/185 | numeric 71/71 (+scheck), source 185/185 |
| figs_thesis_summary | numbers 85/85, display 17/17, rules 40/40, counts 5/5 | numbers 85/85, display 18/18, rules 40/40, counts 5/5 |
| figs_walkthrough_flights | printed 46/46, data-identity 152/152 | same |
| figs_results_walkthrough | verbatim 145/145, modified 20, new 84, world 9/9 | same |
| figs_thesis_drift | 9/9, frame 3/3 | same |
| figs_thesis_methods | sources 320/320, checks 31/31 | same |

- Every converted number shows the same digits as before, with only the unit shifted. The word-diff of every table was reviewed.
- No stored number changed.
- `tools/check_numbers_frozen.py`: PASS.

## Notes for review
- Hold error is in mm, not m. This is the main judgement call; units.md gives the reasons. It reverses the 2026-10-22 SI pass for
  A.2 and summary pages 10 and 11.
- The values that read least well are:
  - 0.004 m/s (the lateral-speed margin);
  - 0.010–0.028 m (Experiment 2 hindsight);
  - 0.004–0.007 m (the Experiment 4 FGO error after the return);
  - 29 000–41 000 m (the blank-floor runaway).
- A.3 page 2 has a layout overlap: "Experiment 5 hold, window means" runs into the next column. The column is narrow, the text
  was already that long, and the overlap is unchanged by this pass.
