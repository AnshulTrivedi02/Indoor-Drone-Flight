# Handover 2026-10-25: extension experiments and the ablation in the two summary PDFs

**Request (user, verbatim):** "yes add the extension section, include the ablation page".

CPU-light. No estimator, replay or simulation was run. Plots come from stored score and verdict files only.

## What changed
- `eval/figs_thesis_summary.py`: a block appended after page 12.
  - New summary pages 13–19, a section page (`summary_ext_section.png`), the contents page re-laid out (also saved as
    `summary_00_contents.png`), and new index entries.
  - New display keys: the E2–E5 result files, the tier-1 pre-registration, the ablation numbers and pre-registration,
    and `discussion_material.md`.
- `eval/figs_results_walkthrough.py`: walkthrough pages 29–36, five new world pages, the section page placed full page,
  the contents re-laid out with a heading row, and new index entries.
  - `sum_src(pid, gap)`: a 10-row gap for the new pages only (D55).
- Records: `docs/thesis/tier1/decisions_log.md` D47–D55.
- Not touched: numbers.md, the frozen pack, and the tier-1 and ablation result files.

## New pages
| summary page (PDF page) | walkthrough page (PDF page) | content |
|---|---|---|
| section (15) | section (45) | "Extension experiments (pre-registered)" |
| 13 (16) | 29 (47), world 46 | E2: lap-5 error against tags (8/4/2/1), live and hindsight; H-E2.1–P-E2.4 PASS 9/9, P-E2.5 FAIL |
| 14 (17) | 30 (49), 31 maps (50), world 48 | E3: every run, plain vs robust, 1% / 5% / control; diverged / collapsed* (DESCRIPTIVE) |
| 15 (18) | 32 (51) | E3: every registered verdict (H-E3.1 FAIL 0/9 … P-E3b.1 PASS 9/9 + 9/9, P-E3b.2 PASS 3/3) |
| 16 (19) | 33 (53), world 52 | E4: step time against window, 33 ms line; P-E4.1 PASS 12/12, P-E4.2 PASS |
| 17 (20) | 34 (54) | E4: L(5) − L(0.25) per flight; H-E4.3 FAIL 7/12; LM-cap check: no flag (0 of 10) |
| 18 (21) | 35 (56), world 55 | E5: UKF with landmark states (not the UKF used elsewhere), with the FGO; all PASS 3/3; S-E5.6 is against iSAM2 hindsight |
| 19 (22) | 36 (58), world 57 | Ablation (EXPLORATORY): FGO per rung r0–r7 on the 3 line-textured bags, UKF band; P1 FAIL, P2 PASS 3/3, P3 FAIL; Result = the ruled paragraph, verbatim |

The world pages for E2–E5 show the tag room. The ablation world page shows both forward-camera corridors and their
onboard frames.

## Checks
- **Summary checks:** numbers 85/85 → 174/174, display-only 20/20 → 49/49, rules 40/40 → 86/86, counts 5/5 → 13/13.
- **Walkthrough checks:** verbatim 145/145 → 183/183, MODIFIED 20 → 20, NEW 84 → 106, worlds 9/9 → 14/14, failures none.
- **Pixel identity:**
  - Every existing PNG is pixel-identical to HEAD (80/80), except `wt_00a_contents.png`.
  - The PDFs were rendered page by page at 60 dpi. In `summary_plots.pdf` (14 → 22 pages) and `results_walkthrough.pdf`
    (44 → 58 pages), only page 1 (contents) differs among the existing pages.
- **Hashes:** the regenerated PNGs differ from HEAD in bytes but not in pixels, so the pixel-identical ones were restored
  to HEAD bytes before the final walkthrough run. All 78 `(sha256 …)` records under `docs/thesis/` match their files.
- **Other checks:** `check_numbers_frozen.py` PASS; `check_claims_applied.py` 58/58; `check_discussion.py` 18/18;
  `check_ablation.py` 228 passed, 0 mismatches.

## Rebuild order (important)
1. Run `python3 eval/figs_thesis_summary.py`.
2. Restore the pixel-identical existing `summary_0*`–`summary_12*` PNGs to HEAD. Never restore the index.
3. Run `python3 eval/figs_results_walkthrough.py`.
4. Restore the pixel-identical existing `wt_*` PNGs.
5. Re-verify the sha256 records.

## Open for the user (reversible)
- D49: the "collapsed" label follows `e3_results.md`'s grouping, split by arm (plain maps shrunk, consistent with a least-squares compromise; the robust map folded, a wrong basin); no threshold was invented.
- D50: the extension pages print FAIL where the main pages say NOT MET. The section page defines the word.
- D53: D46 ("tables only") is superseded. The retention R is not plotted.
- Not merged.
