# Handover 2026-10-17: results/discussion tables and the trajectory figure (one stage)

**Built (new files only; nothing in numbers.md, METHODOLOGY, results, the frozen pack, `eval/figs_thesis.py`, the combined PDF or
`figures_thesis/index.md` was touched):**
- Generator `eval/figs_thesis_results.py` (run with `~/venv-evo/bin/python`). It takes `rd()`, the table helpers, the palette and the
  plot style from `eval/figs_thesis.py` by parsing that file with `ast` (it is NOT executed); the SHA-256 of `rd()` is in the index.
- `docs/thesis/tables/R1_hypothesis_scorecard.*` — proposed **Table 7.3**.
- `docs/thesis/tables/R2_corrections_by_discovery.*` — proposed **Table 7.4** (could move to the appendix as A.4).
- `docs/thesis/figures_thesis/R3_trajectory_overlay.{png,pdf}` — proposed **Figure 4.2**.
- `docs/thesis/tables/R4_information_vs_estimator.*` — proposed **Table 7.5**.
- `docs/thesis/figures_thesis/index_results.md` — captions, inputs, the cross-check tables, the selection rule and the gaps.

**Checks:** 60/60 numeric cross-checks EXACT (stored value rounded once by `rd()` = the typed numbers.md string, which must also occur in
the cited line; for the figure, every plotted path's RMSE = its stored cruise ATE to 6 dp); 157/157 source checks (every quoted
pre-registration and outcome string found, in order, at its cited lines). Every output was rendered and viewed.

**Scorecard:** 46 scored parts over the 35 labels (32 H + C1.a, X1.b, V3): PASS 24, FAIL AS WORDED 3, NOT MET 16, WITHDRAWN 1,
DESCRIPTIVE 2. Category rule (stated in the table note): the record's own word decides; FAIL AS WORDED only where a source says "as
worded" (H1.3 (b), H1.7a via M:9742, H5.6 in S1).

**Corrections:** the pack's 18 plus 19 (D10, the FGO trajectory-writer quaternion typo) and 20 (re-lock time redefined). Display and
transcription fixes of 2026-10-16 are excluded, with the reason in the table note. 1–13, 19 and 20 predate the claims table's
"before" state (07f9f56), so they map to no claims row.

**Figure rule (fixed before plotting):** (a) the median of standard-sensor textured flights 1–9 by cross-estimator mean cruise ATE ->
`dsn_tex_r3`; (b) the same repeat index in the textured-wall camera dataset -> `fwdc_tex_r3`. Paths are drawn after the cruise-ATE
alignment, the lateral axis is stretched 3.0×, and both panels share the same axes.

**Gaps (in the index):** H1.3 was not re-scored after the final re-runs; X1.b's exploratory values are not restated; V3 is not
re-scorable; H5.2–H5.4b exist only in the design draft; there is no with-GNSS RMSE for Experiment 4 (the error 10 s after return is
used and labelled); Experiment 5 has no like-for-like no-tag metric; blank-floor ratios at +30 s only (the later values are †).

**Next:** integrate into the combined PDF and the main index once the other agents' edits to `figs_thesis.py` and `index.md` land.
The user should confirm the proposed numbers and the verdict-category rule.
