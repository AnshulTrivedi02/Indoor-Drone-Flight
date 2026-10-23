# Handover: claims C1–C5, Q2, Q3 and the D17 cell applied to the thesis-facing outputs, 2026-10-24

**Done. Nothing is running.** CPU-light stage: generators re-run, no estimator, replay or simulation. No further
experiment stages are planned (user, 2026-10-24).

## Read this first (user-visible item, D19)
Q3's verbatim text says "the remaining 3 ended 51-85x the clean error". The 3 plain runs at 1% that did not diverge are
**51.26 / 65.59 / 75.23×** (51–75×). 51.26–85.49× is the range over **all 12** non-diverged plain runs (1% and 5%; the
85.49 is T_A_r2 5% s2). The sentence is kept verbatim as instructed, with a scope note giving both populations in the
same limitations row. If you prefer, change "51-85x" to "51-75x" (one edit in `limitations.md`; the checker would then
need its expected string changed).

## What changed
Full mapping, old → new and every location deliberately not edited: `docs/thesis/tier1/claims_applied.md`.
- **Generators:**
  - `eval/figs_thesis.py`: T1 Experiment 3 cells (EKF3, the D17 UKF cell, the FGO scope), the caption, the notes, and new
    footnote [k]; footnote [h] gains a scope clause; the F7 caption gains the C1/C2/C3 sentences (title unchanged).
  - `eval/figs_thesis_summary.py`: page 08 Metric and Result.
  - `eval/figs_thesis_results.py`: an R1 scope note and the R4 note.
- **Hand-written:**
  - `limitations.md`: item 3, verbatim.
  - `methodology_factsheets/3.3_estimators.md`: Q2/C4, C5.
  - `3.5_experiments.md`: C1, C2, C3.
- **Records:**
  - `decisions_log.md`: D19–D27.
  - `open_questions.md`: Q2, Q3, C1–C5 and D17 moved to Answered.
  - METHODOLOGY: appended "RULING (user, 2026-10-24): claims C1–C5 accepted; applied to thesis-facing outputs; see
    claims_applied.md", at the end so no cited line moves.
- **New checker:** `tier1/check_claims_applied.py`. It checks that the old wording is absent and the new wording present,
  recomputes the numbers from the verdict jsons with a single rounding, and runs the freeze check.

## Check totals (before → after)
| generator | before | after |
|---|---|---|
| figs_thesis | 336/336 (T1 66, F7 10) | 348/348 (T1 72, F7 16) |
| figs_thesis_results | numeric 71/71, source 185/185 | numeric 75/75, source 185/185 |
| figs_thesis_summary | numbers 85/85, display 18/18, rules 40/40, counts 5/5 | 85/85, 20/20, 40/40, 5/5 |
| figs_walkthrough_flights | printed 46/46, data-identity 152/152 | same |
| figs_results_walkthrough | verbatim 145/145, modified 20, new 84, world 9/9 | same |
| figs_thesis_drift | 9/9, frame 3/3 | same |
| figs_thesis_methods | sources 320/320, checks 31/31 | same |
| check_claims_applied.py | — | 56/56 (old absent 10, new present 21, numbers 24, frozen 1); 7/7 mutations caught |
| check_claims_update.py | 15/40/141, 0 mismatches (at 6a45af2, scratch export) | on HEAD: 5 quote mismatches, all replaced wording, by design (not edited: tier-1 file) |
| tools/check_numbers_frozen.py | PASS | PASS |

## Pages viewed
T1 p1–p3, R1 p8, R4 p2, summary page 08 (before and after), walkthrough pages 19 and 20, and the combined PDF page 8
(the F7 caption).

The first page-08 wording pushed the y-axis label into the footer. The footer was shortened, and the label now ends
above "Metric:", as it did before. No other overflow or collision was found.

## Open
Nothing blocks. Reversible choices for the user:
- D19: the 51-85x scope.
- D20: the en dash in the Q2 sentence.
- D22: the F7 title kept.
- D25: the proposal's "supports the 0.25 s choice" sentence omitted.
- D26: the locations left unedited.
