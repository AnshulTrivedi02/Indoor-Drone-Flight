# Handover: reader-facing figure set restyled to thesis standard (2026-11-02)

Branch `figs-restyle`, base commit `cf5be5b`. Scope: `docs/thesis/figures_thesis/` only. Data, scoring and verdicts
unchanged throughout; every generator's own cross-check total still passes (details below).

## Figure inventory (before -> after)

| id | file(s) | generator | what changed |
|---|---|---|---|
| METHODS_ARCH | `methods_architecture.{png,pdf}` | `eval/figs_thesis_methods.py` | removed the bold in-figure title; kept full A4-landscape size (RS-3); caption no longer carries the RS-3 process note (moved here) |
| F2 | `F2_heading_stops_sideways_drift.{png,pdf}` | `eval/figs_thesis.py` | removed suptitle, per-estimator annotate boxes, two explanatory notes; resized to 160 mm (RS-1); added `cite()` for the 9.58 m / ±10 m literals |
| F9 | `F9_heading_error_closed_loop.{png,pdf}` | `eval/figs_thesis.py` | removed suptitle, annotate boxes, grey-band note, inset's descriptive title (-> "with heading"); resized; legend/inset repositioned twice to stop overlap |
| R5 | `R5_drift_unaligned.{png,pdf}` | `eval/figs_thesis_drift.py` | removed suptitle, per-panel titles (-> (a)/(b)/(c)), two explanatory notes, per-estimator ATE from the legend ("score box"); one shared legend; resized; "Companion table: Table X (fitted and raw errors), to follow." added to the caption verbatim |
| R3 | `R3_trajectory_overlay.{png,pdf}` | `eval/figs_thesis_results.py` | removed suptitle, per-panel titles, duplicated per-panel "lateral axis stretched" note, per-arm ATE from the legend (same "score box" issue as R5); one shared `fig.legend()`; resized; ATE values moved to the caption |
| F5 | `F5_T_tags_known_positions.{png,pdf}` | `eval/figs_thesis.py` | removed the on-canvas PASS/FAIL hindsight-gain `fig.text()` block; dropped median-gap text from x-tick labels (already in caption); resized; added rd_si()==rd() self-consistency checks |
| F6 | `F6_O_outdoor_indoor.{png,pdf}` | `eval/figs_thesis.py` | shortened route-event labels (dropped multi-line descriptions and badge backgrounds), fixed y-label clipping, fixed "GNSS ON"/"outdoors" collision; resized |
| F7 | `F7_L_loop_closure.{png,pdf}` | `eval/figs_thesis.py` | per-panel titles -> (a)/(b); removed duplicated per-panel legend (one shared legend now); removed on-canvas lap5/lap1 text notes; resized |
| A1 | `A1_closed_loop_builds.png` | `eval/figs_thesis.py` (`table_page`/`save_table`) | `bold=False` (removes bold title + bold FAIL/MISS/NOT-met cell highlighting); shortened title so it no longer clips off the page edge; kept full A4-landscape table layout (RS-3) |
| A2 | `A2_H_and_safety_p{1,2,3}.png` | ″ | `bold=False`, same as A1; layout otherwise unchanged |
| A3 | `A3_F1_cost_ablations_p{1,2}.png` | ″ | `bold=False`, same as A1; layout otherwise unchanged |
| TA (new) | `docs/thesis/tables/TA_verdicts.md`, `figures_thesis/tables_extra/TA_verdicts.{png,pdf}` | `eval/ta_verdicts_check.py` | new: the single appendix verdict table (Table A.4), one row per hypothesis/check/part across Experiments 1-5/5S + extension E2-E6 + the exploratory ablation |

All byte-identical pre-restyle copies are at `docs/thesis/figures_thesis/working/` (verified by sha256 before any
generator ran).

## What was removed from each figure, and where it went

- **In-figure titles / synopsis headlines**: removed from every chart (`save()`'s `fig.suptitle()` call deleted;
  `methods_architecture`'s own `ax.text()` title deleted). The title string is still metadata (index/contents-page/
  combined-PDF heading) - not drawn on the image.
- **Explanatory notes/badges inside axes** (stretch-factor notes, "9 flights overlap", grey-band note, route-event
  descriptive clauses, "same y-scale" note): removed; the same information is in each figure's caption (verified by
  reading the caption after removal - nothing was dropped, only relocated once).
- **Duplicated per-panel legends/titles**: F7 (both panels had an identical live/hindsight legend) and R5 ((a) and
  (b) both had the same 3-estimator legend) now carry one shared legend. R3's two panels have genuinely different
  arms, so its shared legend lists every unique entry across both (truth, 3 estimators, no/with heading) instead.
- **"Score boxes"** (per-arm/per-estimator cruise-ATE values embedded in the legend): removed from R3 and R5's
  legends; the same ATE values are stated in each caption instead, sourced from the same already-checked data
  (`PATHS`/`ATE3` in R3, `ev[TR]['est'][...]` in R5) - no new computation, no changed number.
- **On-canvas PASS/FAIL/verdict text**: F5's `fig.text()` hindsight-gain block (literally printed "H2.1 PASS" / "H2.2
  FAIL" on the image) removed; the gain numbers moved to the caption, the verdict words did not move anywhere on a
  plot (the appendix table carries them). This was the only on-canvas PASS/FAIL string found outside A1-A3.
- **PASS/FAIL/registered-window text already in the pre-existing caption/footnote prose** (`ob_cl()`, `obasis()`,
  `OCASE_KEY`, and the many "H-x.y PASS/FAIL" phrases already written into every caption before this restyle): left
  as is. These sit in the caption/footnote text block below the image (on the combined PDF's caption page and in
  `captions/*.md`), not on the plotted image itself, and reworking this pre-existing, heavily cross-checked pattern
  across the whole file was out of scope given the brief's specific examples (1C overlay, 1A drift, 1C heading
  error) never asked for caption-level verdict-word removal, only removal from the plotted panel. **Flag for the
  coordinator**: if "Verdicts go to an appendix table" is meant literally everywhere (not just on plots), this
  needs a second pass across every caption string in `eval/figs_thesis*.py` - a large, separate piece of work.

## RS decisions

- **RS-1**: text width = 160 mm / 6.30 in (A4, 25 mm margins). Constant: `eval/thesis_style.py:TEXT_WIDTH_IN`.
  Fonts: 9-10 pt tick/annotation, 10-11 pt axis label - already the house rcParams in `figs_thesis.py`, unchanged
  (`eval/thesis_style.py:RCPARAMS` documents them in one place without disturbing the existing block). All seven
  restyled chart PDFs (F2, F9, F5, F6, F7, R3, R5) now measure exactly 453.6 pt (6.30 in) wide
  (`pdfinfo *.pdf | grep "Page size"`), after fixing a `bbox_inches="tight"` bug that silently shrank some and grew
  others past the declared figsize (see "Width fix" below).
- **RS-2**: draft captions at `docs/thesis/figures_thesis/captions/<fid>.md` (`thesis_style.write_caption()`). Each
  points to its `TA_verdicts.md` row(s) by id. For F2/F9/F5/F6/F7/A1/A2/A3 this is a `verdict=` kwarg on
  `save()`/`save_table()`, folded into the caption text before it's stored, so the pointer shows on BOTH the
  standalone caption file and the combined PDF's own caption page (one source of truth). R3/R5/methods_architecture
  don't go through `save()`/`save_table()` (separate generators); their pointer is patched on by
  `eval/add_caption_verdict_pointers.py`, which must be re-run after any regeneration of those three (it's
  idempotent).
- **RS-3**: A1/A2/A3 (dense multi-column text tables) and `methods_architecture` (a ~7 pt-label block diagram) are
  kept at their existing full A4-landscape page size rather than resized to 160 mm - collapsing either to text width
  would make them illegible. `table_page()` is now called with `bold=False` for A1-A3, which removes the bold title
  and the bold FAIL/MISS/NOT-met cell highlighting (a real improvement in-scope for the no-bold-text rule), but the
  verdict WORDS themselves (PASS/FAIL/MISS/NOT met) are still printed in the cells as plain-weight text, and A1's
  footnote still ends "Verdict: case (iii), NO COMPARATIVE TEST REGISTERED: values are descriptive." **This is the
  one open compliance question left**: do A1-A3 need the verdict words stripped from the image entirely (not just
  de-bolded), given they're already inherently appendix tables (arguably the mechanism the "verdicts go to an
  appendix table" rule describes), or is de-bolding sufficient? I made the judgement call to de-bold only, given
  the risk of corrupting dense, heavily cross-checked tabular data by trying to excise words from `rowsA`/`rowsH`/
  `rowsS`/`rowsHC`/`rowsF`/`ABL` cell strings that are built programmatically from scored results.
- **RS-4**: `methods_architecture`'s box titles stay bold (diagramming convention, node headers - not narrative
  emphasis). Not changed from the original.

## Width fix (found via `advisor()` review, not in the original pass)

`bbox_inches="tight"` on `fig.savefig()` crops to content and silently defeats a declared `figsize` - it shrank some
figures below 6.30 in (F2 was 5.66 in) and grew others past it (R3 was 6.80 in, because its now-removed-then-partially-restored
legend once overflowed the axes). Fixed by replacing `bbox_inches="tight"` with `fig.tight_layout()` before saving
(fits the internal margins to the DECLARED canvas) and dropping `bbox_inches` from `savefig()` (default `None`
preserves the full figsize). Applied in `save()` (figs_thesis.py), and the R3/R5 savefig calls. All seven PDFs now
measure exactly 453.6 pt wide. This also surfaced and fixed a real bug: a figure-level `fig.legend()` anchored at
`bbox_to_anchor` y > 1.0 (R3's first attempt) is silently clipped off the saved page once `bbox_inches="tight"` no
longer auto-expands to include it - moved to y <= 1.0 with `tight_layout(rect=...)` reserving the space instead.

## Font-size floor

Several legends/annotations were initially set below the 9 pt floor (down to 7.0 pt) to avoid overlaps while
figures were still the wrong width. After the width fix, all were raised back to >= 9 pt (`grep -n
"fontsize=[0-8]\." eval/figs_thesis*.py` finds only the two pre-existing, untouched combined-PDF caption-page
footnote/cross-check lines at 7.0/7.2 pt, which sit below the image, not inside a plot's axes, and predate this
restyle). F9's inset and legend needed two rounds of repositioning (figure height 3.1 -> 3.7 -> 4.3 in, legend
ncol 1 -> 2 -> back to 1, inset moved from bottom-right to upper-right and back) before the legend, inset and
estimator-name annotate labels stopped colliding at 9 pt. F6's y-axis label was being clipped by `tight_layout()`
at the old narrower width; shortened to "horizontal error (m)" (the "world frame, no alignment" detail is already
in the caption) and the problem went away.

## Caption-pointer corrections (found via `advisor()` review)

The first pass of pointers over-claimed in three places, now fixed:
- **R3 and R5** no longer claim a verdict row. R3 shows a single representative flight (flight 3); H1.1's
  registered sample is flights 4-10 of a paired test, a different population, so R3 is not H1.1 evidence. Both
  captions now say "no verdict row attaches to this figure (descriptive)".
- **A3** no longer points at the EXPLORATORY attribution-ablation rows (P1-P3) in TA_verdicts.md - those score a
  *different* study (which correction caused which numeric change) from A3's own "build ablations" page (earlier
  build vs. final build, no pre-registered hypothesis id of its own). A3's pointer is now H1.4 only, with an
  explicit note not to confuse the two ablation studies.
- **F7** no longer lists every H-E2.x/H-E3.x/H-E5.x extension row; narrowed to exactly the four ids F7's own
  caption text cites (H-E2.1, H-E3.1, H-E5.1, S-E5.5).

## Checks (all re-run after every regeneration round; final state)

| check | result |
|---|---|
| `eval/figs_thesis.py` (F2, F9, F5, F6, F7, A1, A2, A3, T1-T8, R1-R4 — the last two out of figure-restyle scope but regenerated as an unavoidable side effect, then reverted) | 352/352 (was 348; +4 new checks this restyle added: 2x `cite()` for F2's 9.58 m/±10 m, 2x F5 rd_si()==rd() assertions) |
| `eval/figs_thesis_drift.py` (R5) | 9/9 cross-checks, 3/3 frame check |
| `eval/figs_thesis_results.py` (R3, + R1/R2/R4) | 75/75 numeric, 185/185 source |
| `eval/figs_thesis_methods.py` (methods_architecture, + methods/realflight tables) | sources 320/320, checks 31/31 |
| `eval/ta_verdicts_check.py` (new, TA_verdicts.md) | 146/146 EXACT |
| `docs/thesis/tier1/check_claims_applied.py` | 58/58 (F7-title check repointed from `index.md` to `captions/F7.md`, same quoted string) |
| `docs/thesis/ablation/check_discussion.py` | 18/18 |
| `docs/thesis/tier1/e6/check_e6_prose.py` | 68 checks, 100 pairs, 0 mismatches |
| `docs/thesis/methodology_factsheets/check_factsheets.py` | PASS (584 bullets, 1614 citations, 0 failed) |
| `tools/check_numbers_frozen.py` | PASS |

## Verdict table (TA_verdicts.md / Table A.4)

88 rows. Built by a general-purpose subagent (not me) from: `docs/thesis/tables/R1_hypothesis_scorecard.md`
(parsed programmatically, 48 parts, Experiments 1-5/5S... actually 5S's 5 rows are sourced separately from
`eval/results/expH/safety_*.json`, since R1 explicitly excludes the 5S safety criteria), `docs/thesis/tier1/scores/
{E2,E3,E4,e5,e6}_verdicts.json` (32 rows, labelled "Extension E2"-"Extension E6" to avoid confusion with the
thesis's own Experiment 2/3), and `docs/thesis/ablation/ablation_results.json` (3 rows, labelled EXPLORATORY).
Verdict vocabulary kept exactly as each source words it (PASS / FAIL AS WORDED / NOT MET / WITHDRAWN / DESCRIPTIVE
for the Experiment 1-5/5S rows; the extension/ablation sources use the literal word "FAIL", kept as-worded rather
than harmonised - stated in the table's own footnote so it doesn't read as an inconsistency).

Row-id groups useful for future caption work:
- 1C closed-loop corridor: `H1.8` (×4 parts: EKF3 real-time, EKF3 half, UKF, FGO) and `H1.9` (×3: EKF3, UKF, FGO).
- Experiment 2 known tags (F5): `H2.1`, `H2.2`, `H2.3`, `H2.4`.
- Experiment 3 loop closure (F7): `V3`, `H3.1`-`H3.4`; extension rows under "Extension E2"/"Extension E3"/
  "Extension E5".
- Experiment 4 outdoor-indoor (F6): `H4.1`, `H4.2`, `H4.3`.
- Experiment 5 / 5S (A2): `H5.1`-`H5.7` + the five 5S safety rows.
- H1.4 (A3): the robust-weighting test row.

## Consumers repointed (step 5)

- `eval/figs_results_walkthrough.py`: `FIGD` repointed to `figures_thesis/working/` (it crops fixed pixel boxes out
  of F2/F9/F5/F7/F6/R3/R5 at the pre-restyle resolution and asserts specific rows are blank at those exact pixel
  offsets - would break entirely against the resized restyled images). Re-ran: verbatim 118/118, modified 0, new 88,
  world checks 17/17, pages 45, failures: none - identical to before. All 45 output PNGs pixel-identical to HEAD
  (decoded-pixel diff).
- `eval/figs_thesis_summary.py`: `DISP["IDX"]` repointed to `figures_thesis/working/index.md` (it string-searches
  index.md for specific number/phrase occurrences as a validation corpus). `DNAME["IDX"]` left unchanged so the
  printed source name is unchanged. Re-ran: 223/223 data-derived, 62/62 display-only, 101/101 rule, 16/16 counts -
  identical. All 24 output PNGs pixel-identical to HEAD.
- `eval/figs_walkthrough_extra.py`: `DISPF["FI"]` repointed the same way. Re-ran: 186/186 - identical. All 10
  output PNGs pixel-identical to HEAD.
- `eval/figs_walkthrough_flights.py`: **not run**. It needs `pymavlink`/`rosbags` (reads bags directly) and
  references no `figures_thesis/` path at all (`grep -n "figures_thesis\|FIGD"` finds nothing), so it is entirely
  unaffected by this restyle and there was nothing to repoint or re-verify.
- All three consumers' regenerated output files (`docs/thesis/summary/**`) were reverted to HEAD after
  verification (`git checkout HEAD -- docs/thesis/summary/`) - they are separate reader documents and must not
  change; the regeneration was only to prove pixel-identical output, and the embedded commit-hash in each index.md's
  provenance line is the only thing that would have differed otherwise.
- `docs/thesis/tables/**` (T1-T8, R1-R4, methods_*, realflight_*) is regenerated as an unavoidable side effect every
  time `eval/figs_thesis.py` / `eval/figs_thesis_methods.py` runs (they build both directories in one pass). Spot-
  checked several PNGs and one `.md` diff after each run - pixel-identical / commit-hash-only differences - and
  reverted with `git checkout HEAD -- docs/thesis/tables/` every time. Final state: clean except the new, genuinely
  new `TA_verdicts.md`.

## Combined PDF

`thesis_figures_combined.pdf` rebuilt, 27 pages. `eval/figs_thesis.py` now has a `combine_extra_items()` step
(right before the final `ITEMS.sort()`) that reads back the already-rendered PNG + caption text that
`figs_thesis_methods.py` / `figs_thesis_drift.py` / `figs_thesis_results.py` / `eval/ta_verdicts_check.py` already
produced and checked, and inserts them into the same `ITEMS` list this script already uses for its own pages - no
number is recomputed, this is pure assembly. New TNUM entries: `"METHODS_ARCH": "Figure 3.1"`, `"R5": "Figure 4.1c
(provisional)"`, `"R3": "Figure 4.2"`, `"TA": "Table A.4"`. Thesis order (chapter, figures before tables, appendix
last) now reads: 3.1 (methods) -> 4.1 (F2) -> 4.1b (F9) -> 4.1c (R5) -> 4.2 (R3) -> 4.1-4.3 tables -> 5.1-5.3
(F5/F7/F6) -> 5.1-5.2 tables -> 6.1 table -> 7.1-7.2 tables -> A.1-A.4. Fixed one layout bug along the way: the
cover page's "Colours" heading used a fixed y-coordinate that assumed a fixed intro-paragraph line count; adding
Figures 3.1/4.1c/4.2 to the printed figure list wrapped the intro one line longer and collided with "Colours" -
now computed from the actual wrapped line count.

**Not done**: `Figure 4.2` (R3) and `Table A.4` (TA) are not marked "(provisional)" the way F9/R5 are, even though
index_results.md's own prose already calls R3 provisional and TA is a brand-new, not-yet-finally-numbered table.
Flagged by `advisor()` as minor; I judged the blast radius of renaming "Figure 4.2" too large for the remaining
time budget (the exact string "Figure 4.2" and "as in Figure 4.2" appear in several other captions/footnotes
across `figs_thesis.py` and `figs_thesis_drift.py` that would all need updating in lockstep, and the
`combine_extra_items()` prefix-stripping logic depends on an exact string match against what `write_caption()`
wrote). Left as an open item rather than a half-applied rename.

## Open questions for the coordinator

1. **Which figure is "1A drift paths (3 panels, 9 flights)"?** I matched it to R5 (`R5_drift_unaligned.png`, 3
   panels (a)/(b)/(c), tied to the 9-flight standard-sensor dataset via its selection rule) - the only figure in
   scope with 3 panels. `advisor()` flagged this as worth re-confirming against `working/R5_drift_unaligned.png`
   (the pre-restyle original, which I did view - it matches the description reasonably but not with full
   certainty) and checking whether another branch (`raw-corridor`, `ext-pages`, `answers-applied` were visible in
   `git branch -a`) has a more literal match, given the brief's own phrase "score box, ranking-rule box" doesn't
   correspond to any single element I could find in R5. I did not go hunting on other branches - flagging instead
   of guessing further. If the real figure is elsewhere, the content I removed from R5 (legend ATE values, per-
   panel titles, notes) still stands on its own merits per the global rules, independent of which figure the brief
   meant.
2. **RS-3 depth**: see the paragraph under RS-3 above - should A1-A3's verdict WORDS (not just the bold weight) be
   removed from the rendered image?
3. **R3's unmarked "(provisional)"** - see "Not done" above.
4. **Global-rule scope**: pre-existing caption/footnote PASS/FAIL prose (the `ob_*()`/`obasis()`/`OCASE_KEY`
   machinery, used across essentially every figure's caption) was left untouched - see the "removed... and where it
   went" section above for the reasoning. If this needs to change too, it's a second, separate, larger pass.

## Commit

Branch `figs-restyle`, nothing uncommitted outside the paths listed in `git status --porcelain` at hand-off time:
`docs/thesis/figures_thesis/*.{png,pdf}` (the 8 restyled charts + index.md/index_drift.md/index_methods.md/
index_results.md + thesis_figures_combined.pdf), `docs/thesis/figures_thesis/captions/` (new), `docs/thesis/
figures_thesis/working/` (new, pre-restyle snapshot), `docs/thesis/figures_thesis/tables_extra/` (new, TA_verdicts
render), `docs/thesis/tables/TA_verdicts.md` (new), `docs/thesis/tier1/check_claims_applied.py`,
`eval/figs_thesis.py`, `eval/figs_thesis_drift.py`, `eval/figs_thesis_methods.py`, `eval/figs_thesis_results.py`,
`eval/figs_thesis_summary.py`, `eval/figs_walkthrough_extra.py`, `eval/figs_results_walkthrough.py`,
`eval/thesis_style.py` (new), `eval/add_caption_verdict_pointers.py` (new), `eval/ta_verdicts_check.py` (new),
`METHODOLOGY.md` (append-only, one new dated entry). No uncommitted changes anywhere else in the tree; confirmed
`pgrep -fa '[h]eavy.py|[f]go_replay|[a]rducopter'` empty and `~/thesis_data/FLIGHT_LOCK` absent before committing.
