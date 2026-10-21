# Handover 2026-10-21: walkthrough, 1B not-fitted pages and FITTED / NOT FITTED labels

**Request (user, verbatim, 2026-10-21):** "yes add the unaligned 1B pages and fix the wording. Also make it clear which ones have
fitted, maybe put it in bold and also explain briefly in the about the plot what the fitting is doing and trying to show".

## What was done
- `eval/figs_walkthrough_flights.py`: the 1A not-fitted computation is now a shared function `unaligned()` (frame map
  (N, E) = (x, −y) for UKF/FGO, EKF3 NED, frame check of `eval/figs_thesis_drift.py`); the 1A figures are byte-identical
  (sha256 unchanged in `flights/index_flights.md`). New 1B not-fitted figures for fwdc_tex_r1–r3, all five arms, from take-off:
  `fl_1B_unaligned_paths` (five panels, shared axes, equal scale), `fl_1B_unaligned_err_noheading` (3 rows),
  `fl_1B_unaligned_err_heading` (2 rows; a separate page because its y-scale is much finer).
- New data-identity rows (`1B_unaligned`, 46): per flight-arm, the plotted not-fitted path reproduces the stored cruise-window
  `failure.final_disp` and `failure.true_travel` of `phase4_fwdc_evo.json` (eval/three_way_eval.py `failure_metrics`) to 6 dp,
  and the plotted end-of-cruise error equals a direct recomputation from the raw TUM rows to 6 dp; frame check 15/15 at 10°
  (13/15 at R5's 2.0°: fwdc_tex_r2 UKF_baseline −3.00°, FGO_baseline −2.45°).
- `eval/figs_results_walkthrough.py`: every plot page now has exactly one bold label as the first line of its About block
  (FITTED (aligned) / NOT FITTED (...)); FITTED pages explain the fit in plain words; NOT FITTED pages say what is raw. A NEW
  "This plot shows:" line on every page whose plot differs from the registered Metric line (Metric kept unchanged). The 1B
  Result line's "(see the previous page)" is MODIFIED on 1B pages 2–7 to "(see the heading-check page just before this
  experiment)". 1B is now 7 plot pages (ids 08–11, 11a–11c); its world page follows 11c.
- Totals: flights checks 46/46 printed numbers, 152/152 data identity; composer verbatim 137/137, 18 MODIFIED, 80 NEW (number
  guard PASS), worlds 9/9; `tools/check_numbers_frozen.py` PASS; **42 PDF pages**.

## Worth knowing
- With-heading not-fitted error jumps at the start of the cruise (to about 0.07 m on two flights, about 0.33 m on one) and then
  grows slowly; this is in the stored TUMs, not a plotting artefact (the fitted pages remove the constant part).
- Blank floor (page 06) is labelled NOT FITTED (raw, from the moment the camera stops): blank_behaviour.py re-references each
  estimate to the truth at the camera-loss instant (a shift only, no fit), so "from take-off" would have been wrong.
- Regenerate: `~/venv-evo/bin/python eval/figs_walkthrough_flights.py --cache <scratchpad>/wtcache`, then
  `python3 eval/figs_results_walkthrough.py`.
