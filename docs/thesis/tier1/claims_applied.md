# Claims update applied to the thesis-facing outputs (C1–C5, Q2, Q3, the D17 cell)

- **Ruling (user, 2026-10-24, verbatim):** "C1-C5: accepted as proposed. Apply to the thesis files at the listed lines; the
  existing claims table and frozen documents are not edited (apply to thesis-facing outputs only, with a mapping note)."
  Q2, Q3 and the D17 follow-up are quoted in `open_questions.md` (Answered).
- **Proposal:** `claims_update.md` (commit `6a45af2`). Line numbers below are at this stage's commit unless marked "was".
- **Rules applied:** decisions D19–D27 (`decisions_log.md`). Rule 8: the D17 cell keeps the user's "~2x"; the measured
  1.76–2.08× (LC live, DESCRIPTIVE) is in its footnote [k]. Units: m for position error, ms for compute.
- **Checks:** generator cross-checks (before → after) and `check_claims_applied.py` (new); totals in the handover
  `docs/handovers/2026-10-24_claims_applied.md`. `check_numbers_frozen.py`: PASS.

## C1. Loop closure is not specific to the FGO (E5)

| location | old → new |
|---|---|
| `tables/T1_scorecard.md:12` (+ `.tex`, `_p1.png`), EKF3 cell; generator `eval/figs_thesis.py:811` | "N/A: FGO capability only (the filters have no loop closure)" → "N/A: no landmark states (the thesis EKF3 as configured has no loop closure; EKF3 with landmark states not tested)" |
| same row, UKF cell; generator `:819` (D17, user wording) | "N/A: no loop-closure equivalent (FGO capability only)" → "UKF with landmark states (extension E5): bounded; ~2x FGO error [k]" |
| `T1_scorecard.md:3` caption | adds "S-E5.5, the extension UKF variant's error higher than the FGO's, is met, but concerns an extension variant, not the thesis UKF, footnote [k]"; "(footnotes [a]–[j])" → "(footnotes [a]–[k])" |
| `T1_scorecard.md:16` statuses note | "(Experiment 3, FGO only: H3.1–H3.4); N/A = not run." → "(Experiment 3, the FGO: H3.1–H3.4); N/A = not run (Experiment 3: the thesis EKF3 has no landmark states)." |
| `T1_scorecard.md:18` by-row note | "Experiment 3, one estimator [h]" → "Experiment 3, one thesis estimator [h], the UKF cell an extension variant [k]" |
| `T1_scorecard.md:20` key numbers | "Experiment 3 = with loop closure" → "… with loop closure (the UKF cell: extension E5, footnote [k])" |
| `T1_scorecard.md:44` new footnote [k]; generator `ob_ext()` `:788` | new: names the variant (not the UKF used elsewhere), "bounded" = H-E5.1 PASS 3/3, "~2x FGO error" = UKF ÷ FGO live overall RMSE with loop closure 1.76–2.08× (LC live, descriptive), S-E5.5 held 3/3 with no ordering label, EKF3 with landmark states not tested; plus the C2/C3 scope (below) |
| `figures_thesis/index.md:213` F7 caption (+ `thesis_figures_combined.pdf` p. 8); generator `:1422` | "This is an FGO capability, not an FGO-against-filter result (the filters have no loop-closure equivalent); one estimator, …" → "The thesis's EKF3 and UKF, as configured, have no landmark states, so they have no loop closure; loop closure is not specific to the FGO: in an extension experiment (pre-registered), a UKF variant with each tag in its state bounded its live drift (H-E5.1 PASS 3/3), with a higher error than the FGO's (S-E5.5 PASS 3/3; UKF ÷ FGO live 1.76–2.08, descriptive). … One estimator, …" |
| `summary/index_summary.md:174`, page 08 PNG, `summary_plots.pdf`; generator `eval/figs_thesis_summary.py:651` | "Only the FGO can do this, so there is no comparison between estimators." → "Only the FGO has loop closure in the thesis (its EKF3 and UKF have no landmark states)." Result line adds "… and for a UKF with the tags in its state" |
| `summary/index_walkthrough.md:406`, `:424` (VERBATIM rows), `wt_19_3_truth.png`, `wt_20_3_loop_closure.png`, `results_walkthrough.pdf` | follow page 08 verbatim (regenerated; verbatim 145/145) |
| `tables/R4_information_vs_estimator.md:20` (+ `.tex`, `_p2.png`); generator `eval/figs_thesis_results.py:1016` | "Experiment 3 (loop closure) has one estimator and no spread" → "has one thesis estimator and no spread: the thesis EKF3 and UKF, as configured, have no landmark states; a UKF with tag landmark states (extension experiment E5, not in this table) also bounded its live drift (H-E5.1 PASS 3/3)" |
| `methodology_factsheets/3.5_experiments.md:86` | "An FGO capability test, not FGO vs filter (M:10456-10457)." → "A test of the FGO's loop closure, not FGO vs filter (M:10456-10457). Loop closure … is not specific to the FGO … (H-E5.1 PASS 3/3) … (S-E5.5 PASS 3/3; UKF ÷ FGO live 1.76–2.08, descriptive). EKF3 with landmark states was not tested …" |

**Not edited (C1):** `METHODOLOGY.md:10456-10457` (append-only; its hedge holds; the forward pointer is the appended
RULING entry at the end of METHODOLOGY); `final_results_pack_index.md:316` and `eval/figs_final_pack.py:661` (frozen; not
edited; superseded by the T1 footnote [k] and the F7 caption); claims table row 23 (`headline_claims_before_after.md:38`,
frozen; superseded by this note); `eval/figs_TLO.py:170` (log-scale supervisor figure, not thesis-facing; its hedged form
holds) and `plots/supervisor_2026-10-08/INDEX.md:29` (dated supervisor pack); `figures_thesis/index_methods.md:362`
(a source-quote check of the METHODOLOGY line, which is unchanged).

## C2. The loop-closure result rests on correct tag IDs (E3) — and Q3

| location | old → new |
|---|---|
| `limitations.md:11`, new row 3 (Q3) | new, **verbatim**: "The FGO as configured (plain least squares, tag readings ungated) is not robust to wrong tag IDs: at 1% wrong IDs, 6 of 9 runs diverged and the remaining 3 ended 51-85x the clean error (H-E3.1 FAIL, 0/9). A robust-weighted variant avoided divergence in all 21 runs, though one collapsed. The landmark UKF (E5) was not tested with wrong IDs." The "where the value lives" cell carries the scope note (D19) |
| F7 caption, `index.md:213` | adds "The result assumes correct tag IDs: with wrong IDs in 1% of the eligible detections (extension experiment), the FGO as built lost its loop-closure advantage (H-E3.1 FAIL 0/9; 6 of 9 runs diverged)." The F7 **title is unchanged** (D22) |
| T1 FGO cell `:12`, footnotes [h] `:38` and [k] `:44` | FGO cell "(H3.1–H3.4 PASS 3/3)" → "(H3.1–H3.4 PASS 3/3; 8 tags, correct tag IDs [k])"; [h] adds "scope: all 8 tags and correct tag IDs; extensions in footnote [k]" (F7 footnote [a]: "(extensions in the caption)"); [k] states the E3 result |
| summary page 08 Result, `index_summary.md:176` | adds "with wrong IDs in 1% of eligible detections the FGO lost this advantage" |
| `R1_hypothesis_scorecard.md:68` (+ `.tex`, `_p8.png`), new note; generator `:642` | "Experiment 3 scope (claims C2 and C3 …; the H3.1–H3.4 verdicts are unchanged) …" (D23: a note, no new rows) |
| `3.5_experiments.md:87` (new sub-bullet) | the C2 (a)/(b) wording: H-E3.1 FAIL 0/9, 6 of 9 runs diverged; robust variant 0 of 21 diverged, P-E3b.1 PASS 9/9 at 1% and 9/9 at 5%; no LC-vs-no-LC claim for it (D16) |

**Scope note (D19).** The user's "51-85x" is kept verbatim. 51.26–85.49× (`e3_results.md:136`) is the range over all
12 plain runs that did not diverge, at 1% and at 5%. The 3 runs at 1% are 51.26–75.23× (`e3_results.md` §3 table:
65.59 / 75.23 / 51.26). Both are checked exactly by `check_claims_applied.py`. "One collapsed" is the robust run
T_A_r2 5% s1 (live 4.1849 m; `e3_results.md:190`). Not checked by any run: the landmark UKF with wrong IDs (as stated).

**Not edited (C2):** `METHODOLOGY.md:10458-10459` (append-only; forward pointer appended); `figures_thesis/index.md:25`
and `:211` (the F7 title, D22); claims row 23 and `numbers.md` §16.3 (frozen; superseded by limitations item 3 and this note).

## C3. Loop closure bounds live drift with 4 and 2 tags as well (E2)

| location | old → new |
|---|---|
| T1 footnote [k] `:44` and FGO cell `:12` | "with 4 tags and with 2 tags (E2), loop closure also bounded live drift (H-E2.1 PASS 3/3 in each)"; the cell names the 8-tag scope |
| F7 caption `index.md:213` | adds "With 4 and with 2 tags, the FGO's loop closure also bounded live drift (extension experiment, H-E2.1 PASS 3/3 in each)." |
| summary page 08 Result `index_summary.md:176` | adds "Extension tests: also bounded with 4 tags and with 2 tags" |
| R1 note `:68` | as under C2 (H3.1 scope: 8 tags) |
| `3.5_experiments.md:88` (new sub-bullet) | the C3 wording, D as the known-map case, P-E2.5 FAIL so no monotone tag-density claim |

**Not edited (C3):** `figures_thesis/index.md:211` (the F7 title; holds as worded, "too narrow"); claims row 23 and
`numbers.md` §16.3 (frozen).

## C4 and Q2. The 0.25 s window (E4)

| location | old → new |
|---|---|
| `methodology_factsheets/3.3_estimators.md:67` (was :66) | "It is the largest window that met the 33 ms deployability budget (numbers.md:209, 440; M:702-709)." → "In the corridor configuration, 0.25 s was the largest window within the 33 ms budget; on the tag-room flights 0.5 s also fitted (27–28 ms) (… ruling 2026-10-24, Q2; 27–28 ms [NOT IN numbers.md: tier1/e4_results.md:169 …; DIAGNOSTIC])." En dash per house style (D20) |
| `3.3_estimators.md:68-69` (new sub-bullets) | the corridor sweep is DIAGNOSTIC and pre-thread-fix; "No general claim is made about the largest window"; E4: P-E4.1 PASS 12/12, P-E4.2 PASS, H-E4.3 FAIL 7/12 (a null result, not a proof of independence) |

- **27–28 ms source:** the 12 E4 W = 0.5 s medians after the anchor, 26.86–28.22 ms (`E4_verdicts.json` runs
  `step_median_ms_after_anchor`), rounded once to integers.
- **Not included (D25):** the proposal's "This supports the 0.25 s choice on the room world at a far lower compute cost".
- **Not edited (C4):** `METHODOLOGY.md:708-712`, `:720-723` (append-only; forward pointer appended); `numbers.md:444`,
  `:457-458` (frozen); `methodology_index.md:274` (an index into METHODOLOGY, not thesis text; D26). No generator prints
  the "largest window" wording (searched `eval/`).

## C5. The LM cap 2 (E4)

| location | old → new |
|---|---|
| `3.3_estimators.md:65` (new sub-bullet under :64) | "cap 2 was also compared with cap 10 at every window from 0.25 to 5 s on two room flights (T_A_r1, T_D_r1). No convergence flag was raised: the largest RMS reading was 0.0009 m, against the 0.029 m threshold. Cap 10 is not full LM" |

**Not edited (C5):** `tables/methods_estimator_design.md:10` (optional in the proposal; the cell states the
configuration, not the convergence claim; D26); `numbers.md:452` (frozen); `METHODOLOGY.md:723-724` (append-only).

## The D17 cell

The Experiment 3 UKF cell of Table 7.1 reads, verbatim, "UKF with landmark states (extension E5): bounded; ~2x FGO
error [k]". Footnote [k] says it is an extension variant, not the UKF used elsewhere, and gives the measured range
1.76–2.08× (UKF ÷ FGO, LC live, DESCRIPTIVE; per flight 2.08 / 1.84 / 1.76, `e5_verdicts.json`). Each ratio rounds once
to 2 (checked). In TeX the tilde is emitted as `\textasciitilde{}`.

## Outputs regenerated (real changes only)

- Tables: T1 (`.md`, `.tex`, `_p1`–`_p3`), R1 (`.md`, `.tex`, `_p8`), R4 (`.md`, `.tex`, `_p2`).
- Figures: none of the figure PNG/PDFs changed (the F7 plot and title are unchanged; only its caption, which is in the
  index and the combined PDF).
- Indexes: `figures_thesis/index.md`, `index_results.md`, `summary/index_summary.md`, `summary/index_walkthrough.md`.
- PDFs: `thesis_figures_combined.pdf`, `summary_plots.pdf`, `results_walkthrough.pdf`.
- Summary/walkthrough pages: `summary_08_3_loop_closure.png`, `wt_19_3_truth.png`, `wt_20_3_loop_closure.png`.
- Every other regenerated output differed only in its "built at commit" line (or PDF metadata) and was restored.

## Q4 correction (user ruling, 2026-10-24, applied after the merge)

| location | old → new | reason |
|---|---|---|
| `docs/thesis/limitations.md` item 3, claim text | "the remaining 3 ended 51-85x the clean error" → "the remaining 3 ended 51-75x the clean error" | the 3 non-diverged 1% plain runs are 51.26 / 65.59 / 75.23× clean; 51-85x was mis-scoped in the coordinator's 24 Oct digest |
| `docs/thesis/limitations.md` item 3, provenance cell | "wording verbatim" → "wording verbatim except the range, corrected … by the user's Q4 ruling" | records the change; the D19 scope note (51.26–85.49× over all 12 non-diverged runs at 1% and 5%) is kept |

**Search for "51-85" / "51–85" in all thesis-facing material.** Only the limitations.md instance above described the 1% runs
alone. Not changed, because each describes all 12 non-diverged plain runs (1% and 5%) and is correct: METHODOLOGY.md:14571
(append-only, "the E3 runs that did not diverge"), `tier1/e3_results.md:136`, `tier1/claims_update.md:143`,
`decisions_log.md` D3, the 2026-10-23 stage 2e handover. Records that quote the original Q3 text (D19, D20, the
claims-applied handover, the Q3 answer in open_questions.md, this file's Q3 row) are historical and kept as written.

**Checkers.** `check_claims_applied.py`: the Q3 text check uses "51-75x"; the range check is now the 3 runs at 1%
(integers 51-75); new checks that "51-85x" is absent from the item 3 claim cell and that the 12-run integer range is
51-85. 58/58. `check_claims_update.py` is pinned to commit 181f156 (header documents it) and reads every file from
that commit, so it passes 15 quotes / 40 verdicts / 141 numbers with 0 mismatches on the current tree.
