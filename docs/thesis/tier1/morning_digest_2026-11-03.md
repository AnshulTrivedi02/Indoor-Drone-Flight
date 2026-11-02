# Morning digest, 2026-11-03 (overnight run 2026-11-02 19:30 to 2026-11-03 01:15)

Everything requested overnight is merged into `fwd-camera` and pushed to GitHub. Nothing is pending. No STOP condition was hit; no agent stalled past the restart rule.

## What merged

| merge | what | key checks |
|---|---|---|
| `cf5be5b`, `0f567f1` (before 19:30, for reference) | E4 live error against compute time (walkthrough page 17e, summary page 21; D110); raw world-frame corridor errors, all 154 Experiment 1 cells (D106, D107, D111) | evo -a reproduced 154/154 to 6 dp; check_raw_corridor 1860/1860; summary 223/62/101/16; walkthrough 45 pp |
| `dd8f67a` | figure restyle to thesis standard (11 figures), layout fixes, captions without verdict text, each ending "Verdicts: Table A.4, rows ..." (D113, D116, D117); new appendix Table A.4 `TA_verdicts.md` (88 rows) | figs_thesis 352/352; drift 9/9 + 3/3; results 75/75 + 185/185; ta_verdicts 146/146; caption check 21/21 |
| `793ffd6` | stage 2: raw columns beside the registered fitted values in T1, T2 and R4; new companion Table 4.4 (provisional, T9) for Figure 4.1c (D119) | check_raw_tables 79/79; T9 recomputed independently by the coordinator, all values match |
| `0d9cf8d` | post-merge pass: F5 caption ordering wording removed, F2/F9 labels raised to 9 pt, R5 caption names Table 4.4, combined PDF rebuilt with T9 (29 pages) (D118, D120) | figs_thesis 358/358; results 77/77 + 185/185 |

Table 4.4 (median, range over flights 1-9 of the textured floor, m): fitted cruise ATE (registered) EKF3 4.10 (3.11-4.12), UKF 5.13 (1.17-5.85), FGO 4.46 (1.27-4.61); raw RMS (descriptive) EKF3 14.58 (7.84-14.64), UKF 20.26 (6.83-25.16), FGO 16.65 (3.79-17.67); raw end of cruise EKF3 37.39 (22.54-37.56), UKF 50.13 (7.33-60.26), FGO 42.06 (1.49-44.27). Raw values are 3D, matching evo -a's own translation-part metric.

Decisions logged overnight: D113-D120 (`tier1/decisions_log.md`). New open questions ON-1 to ON-5 (`tier1/open_questions.md`), none blocking.

## Pending

Nothing from the overnight list. Open, for you: ON-1 (stale line citations in two dated records: leave as snapshots, recommended), ON-2 (R3 spare space under its legend), ON-3 (caption check catches literal words only), ON-5 (provisional numbering, as standing).

## Guard and cross-check status (final, on the merged tree)

- Checksum guard: all 13,253 frozen files IDENTICAL; the only difference reported is the new descriptive file `eval/results/raw_corridor_errors.json` (ADDED), as anticipated by D112.
- `tools/check_numbers_frozen.py`: PASS.
- check_raw_corridor 1860/1860; check_raw_tables 79/79; ta_verdicts 146/146; caption_verdict_check 21/21; check_claims_applied 58/58; check_discussion 18/18; check_e6_prose 0 mismatches; check_factsheets PASS (584 bullets, 0 failures).
- Generators: figs_thesis 358/358; figs_thesis_drift 9/9 + frame 3/3; figs_thesis_results 77/77 + 185/185; summary 223/62/101/16; extras 186/186; walkthrough 45 pages, failures none. Summary and walkthrough pages are pixel-identical to before the restyle.

## Files changed since 19:30, for re-upload to the writing project

Paths under `docs/thesis/`. Re-upload these:

- `tables/T1_scorecard.md`, `tables/T2_accuracy_heading.md`, `tables/R4_information_vs_estimator.md` (raw columns added)
- `tables/T9_1A_fitted_vs_raw.md` (new, Table 4.4 provisional)
- `tables/TA_verdicts.md` (new, Table A.4, the appendix verdict table)
- `figures_thesis/captions/*.md` (11 new draft captions)
- `figures_thesis/*.pdf` (restyled figures) and `figures_thesis/thesis_figures_combined.pdf` (29 pages, captions under each figure)
- `figures_thesis/index.md`, `index_drift.md`, `index_results.md`, `index_methods.md` (provenance and checks)
- Changed shortly BEFORE 19:30, so re-upload if your copy predates yesterday evening: `summary/summary_plots.pdf` (24 pages, new page 21), `summary/results_walkthrough.pdf` (45 pages, new page 17e), `limitations.md` (item 5), `methodology_factsheets/3.6_metrics_statistics.md` (the fit justification), `raw_corridor/raw_corridor_numbers.md` (new)

Not for upload (records and tooling): `tier1/decisions_log.md`, `tier1/open_questions.md`, `tier1/check_claims_applied.py`, `METHODOLOGY.md` (two dated entries appended), `figures_thesis/working/` (the old annotated figures, kept for reference), `eval/*.py`, `docs/handovers/`.

Full list: `git diff --name-only 0f567f1..fwd-camera` (114 files, including 33 unchanged reference copies in `figures_thesis/working/`).
