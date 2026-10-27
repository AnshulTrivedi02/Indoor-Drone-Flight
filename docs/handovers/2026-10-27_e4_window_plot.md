# Handover 2026-10-27: E4 "window against error" page in the two summary PDFs

**Request (user, verbatim):** "can you reproduce the plot in the summary pdf with the fgo window vs error, it is hard to tell
how increasing the window affects error increase/decrease".

CPU-light. No estimator, replay or simulation was run. The plot comes from the stored score files only.

## What changed
- `eval/figs_thesis_summary.py`, page 17 (`summary_17_E4_accuracy.png`), now has four side-by-side panels, one per tag
  count (8 / 4 / 2 / 1). The panels share one y-scale.
  - **y:** the change in FGO live horizontal RMSE from its 0.25 s value, in m. 0 is marked, and the plot says "below 0 = more accurate".
  - **x:** the windows 0.25 / 0.5 / 1 / 2 / 5 s, evenly spaced and labelled "not to scale" (D57).
  - **Lines:** one per flight, in #D55E00 with filled markers (square, circle, triangle). Each flight is nudged ±0.12 of a step sideways (D58).
  - **Panel titles:** each gives the 0.25 s error range at 4 dp (D59).
  - **Source:** `docs/thesis/tier1/scores/E4_<trial>_w<W>.json`, track "FGO live", `horiz_err_m.rmse`, cap-2 runs only.
- The page title is unchanged, so the contents pages stay identical. "What this tests" and the Metric line are rewritten. The
  Result keeps H-E4.3 FAIL 7 of 12 and the LM-cap check (0 of 10). It adds one descriptive sentence (D60): with 8 or 4 tags
  the window changes the error by under 0.0003 m; with 2 tags by under 0.001 m either way; with 1 tag the changes are larger
  (up to about 0.009 m) and not in one direction. The old "A longer window did not buy live accuracy" sentence is dropped.
- `eval/figs_results_walkthrough.py`: `SUM_TOP["17"]` changes from 0.2540 to 0.3395, because the footer is now longer. The
  walkthrough page shows the whole plot with nothing cut off (checked by eye).
- Records: `docs/thesis/tier1/decisions_log.md` D57–D60. The page-17 entry in `index_summary.md` is rewritten.
- Not touched: numbers.md, the frozen pack, and the tier-1 and ablation result files.

## Pages
- summary_plots.pdf, PDF page 20 (summary page 17).
- results_walkthrough.pdf, PDF page 54 (walkthrough page 34).

## Checks
- **Summary checks:**
  - Numbers went from 174/174 to 196/196. Five checks were removed with the old labels, and 27 were added:
    - score files equal to E4_verdicts L0.25/L5;
    - 12 per-flight rows equal to `e4_results.md` at 4 dp;
    - 4 panel ranges;
    - 3 bounds plus 4 sign/strictness checks;
    - two spot values (T_D_r2 +0.0093144 and T_D_r1 −0.0067342 m at 1 s).
  - Display checks went from 49/49 to 50/50. Rules stay at 86/86 and counts at 13/13.
- **Walkthrough checks:** verbatim 183/183, modified 20, new 106 and worlds 14/14, all unchanged. No failures.
- **Pixel identity:**
  - Both PDFs were rendered at 60 dpi against HEAD, 80 pages in total. Only summary PDF page 20 and walkthrough PDF page 54 differ.
  - Every other PNG is pixel-identical and has been restored to HEAD bytes.
- **Hashes:** all 78 `(sha256 …)` records under `docs/thesis/` match their files.
- **Other checks:** `check_claims_applied.py` 58/58, `check_discussion.py` 18/18, `check_ablation.py` 228/0, and
  `check_numbers_frozen.py` PASS.

## Rebuild order (unchanged from 2026-10-25)
1. Run `figs_thesis_summary.py`.
2. Restore the pixel-identical summary PNGs.
3. Run `figs_results_walkthrough.py`.
4. Restore the pixel-identical `wt_*` PNGs.
5. Re-verify the sha256 records.

## Open for the user (reversible)
- D57: evenly spaced windows on this page only. D51 still governs page 16.
- D59: the panel titles are at 4 dp, not the prototype's 3 dp.
- D60: the bounds are in m, not mm, and the old closing sentence is dropped.
- Not merged.
