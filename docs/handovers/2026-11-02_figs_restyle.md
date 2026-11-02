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

## Layout fixes (2026-11-02, branch `figs-restyle-fix`, head `a6f6fd2`)

Stored outputs only; no flight, replay or simulation at any point. Three named layout issues fixed, plus hardening
found via `advisor()` review along the way.

### 1. R5 (`eval/figs_thesis_drift.py`) - panel (a) narrower than (b)/(c); (b)/(c) y-labels collided

Both symptoms had the same root cause: `ax0.set_aspect(STRETCH, adjustable="box")` (STRETCH = 1.0, a declared
equal-scale choice, not changeable) shrinks panel (a)'s axes BOX in figure-fraction coordinates to hit the 1:1
aspect, leaving it narrower than the unconstrained (b)/(c). Fix: removed the `set_aspect()` call; instead, after
`fig.tight_layout()` fixes the column layout (so all three panels share the same left/right edges, with nothing
aspect-shrinking panel (a) any more), panel (a)'s Y-LIMITS are computed from its now-known, full-width box geometry
to hit the same 1:1 aspect by construction - `needed_yr = bb0.height * x_range / (STRETCH * bb0.width)`, centred on
the original data range. The original row 0 height (figure 5.6 in, height_ratios `[1.45, 1.0, 1.0]`) wasn't tall
enough to show the full ~56 m drift range at a true 1:1 aspect using the now-full-width box; raised to figure height
7.0 in, height_ratios `[1.9, 1.0, 1.0]`, hspace 0.5 -> 0.75 (also fixes the label collision, see below). An `assert
abs(bb0.x0 - bb1.x0) < 0.01 ...` confirms the edges actually match; the pre-existing stretch check (now comparing
against the geometry-derived ylim rather than an aspect-adjusted box) still passes exactly.

(b)/(c)'s y-labels ("along-track error (m)" / "sideways error (m)") were colliding at the shared left edge because
the two rotated labels, each taller than its own panel's vertical gap to its neighbour, ran into each other - visible
at 2x zoom as the bottom of "along-track error (m)" touching the top of "sideways error (m)". Fixed with
`fig.align_ylabels([ax0, ax1, ax2])` (aligns all three labels' x-position so none juts out further than the others)
plus the larger hspace above (now enough room that the labels don't reach each other even un-aligned).

**Advisor-found correctness bug, fixed before it shipped**: the first version of the y-limit solver re-centred
silently (`if ylo > YL0: ...`) whenever the geometrically-needed range was smaller than the data's own range - which
would have clipped part of the plotted data (including the truth line at y=0) while the stretch check still passed,
because the check only compares aspect ratios, not data coverage. Replaced with
`assert needed_yr >= YL1 - YL0, "row 0 too short for a 1:1 aspect over the full data range"` - fails loudly instead
of quietly cropping. Did not fire in the actual run (figure height 7.0 in gives enough headroom).

**Verified**: 9/9 cross-checks, 3/3 frame check (both unchanged from the pre-fix baseline); PDF still exactly 453.6 pt
(6.30 in) wide; viewed `R5_drift_unaligned.png` directly - panel (a) now shares (b)/(c)'s left/right edges exactly,
(b)/(c) labels no longer touch.

### 2. R3 (`eval/figs_thesis_results.py`) - both panels used about half the 160 mm width

Same underlying cause as R5: `ax.set_aspect(3.0, adjustable="box")`, applied identically to both panels (same x/y
range), shrank both boxes to a fraction of the column width. Fixed the same way: removed `set_aspect()`; after
`fig.tight_layout(rect=(0, 0, 1, 0.86))` fixes the column layout (shared legend reserved above, unchanged), computed
the y-range that gives the now-full-width box the SAME 3.0x lateral stretch the original design used (an
`assert bb0.width/x0 match bb1's` confirms both panels still share one width). Needed figure height raised from 5.6
to 8.0 in to fit the full data range (`lat` ~= 13.2 m) at full width and exactly 3.0x (iterated empirically: 7.3 in
gave 2.65x, 8.0 in gives exactly 3.00x). STRETCH is no longer forced by `set_aspect()`, so it's now pinned with
`assert rd(STRETCH, 1) == "3.0"` (advisor-suggested hardening) so a future height edit can't silently drift the
caption's stated "3.0x" without the script itself catching it.

**Verified**: 75/75 numeric + 185/185 source checks unchanged; PDF still exactly 453.6 pt wide; viewed
`R3_trajectory_overlay.png` directly - both panels now fill the full width, shared legend above, no empty margins.

**Not done (flagged, in scope but low value for the time budget)**: about 0.7-0.8 in of the 8.0 in height is
blank space between the legend and panel (a), from the fixed `rect=(0, 0, 1, 0.86)`; computing that rect's top from
the legend's own drawn height (rather than a fixed fraction) would likely give the same 3.0x stretch in a shorter
figure. Left as a follow-up, not attempted here.

### 3. F2 (`eval/figs_thesis.py`) - lower "wall" label sat on the bottom axis line

`ax.text(163, -10.05, "wall", ha="right", va="top", ...)`: with `va="top"`, the text's glyphs (no descenders, so
most of their height sits below the anchor point) ran from y=-10.05 down past the bottom spine at y=-10.6 and sat on
top of it, visibly struck through at 3x zoom - the *top* "wall" label (`va="bottom"` at y=10.05, extending upward
into blank space) had no such problem, which is why only the bottom one needed fixing. Fixed by moving the anchor to
the centre of the wall band itself (`ax.text(163, -10.0, ..., va="center", ...)`), well clear of the spine 0.6 units
below. Also gave both "wall" labels a white stroke halo (`patheffects.withStroke(linewidth=2.5, foreground=SURF)`,
advisor-suggested) since the band colour (`WALL`, `#5e5e5e`) and the label colour (`INK2`, `#4d4d4d`) are close in
value and the dotted contact line / band edge can still run behind the glyphs.

**Verified**: 352/352 total checks unchanged (figs_thesis.py's own run); viewed `F2_heading_stops_sideways_drift.png`
directly at 3x zoom - the "wall" label now sits cleanly inside the grey band, clear of both the dotted line and the
spine.

**Flagged, not fixed (out of scope for this pass)**: re-checked the original restyle's "all text >= 9 pt" claim
while in this figure - it's not true of F2. The wall labels are 8 pt and the estimator-name annotate() labels are
8.6 pt, both below RS-1's stated 9 pt floor; the old `grep -n "fontsize=[0-8]\."` check that found none below 9 pt
misses bare `fontsize=8` (no decimal point) entirely. Not changed here (not one of the three named issues, and R3/R5
already consumed the time budget); worth a follow-up pass on F2 specifically.

### Coordinator rulings on the four open items (handover list above)

1. **R5 = "1A drift paths"**: accepted. R5 (`R5_drift_unaligned.png`) is the figure meant by "1A drift paths (3
   panels, 9 flights)" - no further search of other branches needed.
2. **A1-A3 verdict words in cells**: accepted as-is (de-bolded only, words kept) - appendix tables are where verdicts
   belong (this is now also the explicit wording of ruling D113 below, which carves the same exemption out for the
   caption-stripping pass).
3. **Provisional labels** (R5 "Figure 4.1c (provisional)", F9 similarly, R3's un-marked "Figure 4.2"): unchanged
   until the chapter plan is locked - standing user ruling, not revisited this pass.
4. **Verdict prose in caption footnotes**: **superseded by D113 below**, actioned in the same commit as these layout
   fixes rather than left open.

## D113 (2026-11-02, coordinator ruling): captions carry no verdict wording, only a Table A.4 pointer

Added to this same branch/commit after the three layout fixes above, per a mid-task instruction. Ruling: every
reader-facing caption carries NO verdict sentences or verdict labels (PASS / FAIL / NOT MET / MET / MISS / "verdict"
wording, check counts, registered-window text) anywhere in its body, and ENDS with a pointer to its
`docs/thesis/tables/TA_verdicts.md` row(s), in the exact form `Verdicts: Table A.4, rows <ids>.` (or, for a
descriptive figure with no row of its own, `Verdicts: Table A.4, none (descriptive).`). A1-A3 and TA_verdicts.md
itself keep their verdict cells (appendix tables are where verdicts belong) - not touched.

**Scope, read narrowly on purpose**: the brief's own wording ("every `docs/thesis/figures_thesis/captions/*.md`")
is literally the restyle's existing 11-file set; A1/A2/A3 are explicitly exempted by the same ruling, leaving 8
files: F2, F5, F6, F7, F9 (via `eval/figs_thesis.py`'s `save()`), R3 (`eval/figs_thesis_results.py`), R5
(`eval/figs_thesis_drift.py`), methods_architecture (`eval/figs_thesis_methods.py`). The `ob_*()`/`obasis()`/
`OCASE_KEY` footnote-generator FUNCTIONS themselves were NOT redefined or removed - T1 (Table 7.1, 72 checks) and
the other T-tables (all outside `figures_thesis/captions/`, all unaffected by this restyle) use the same functions
in their own notes and still print PASS/FAIL/NOT met there, by design (those are body tables, not captions on a
plotted figure). Only the 5 call sites inside `save()` (F2/F9/F5/F6/F7) and the 3 strings in
`add_caption_verdict_pointers.py` (R3/R5/methods_architecture) changed.

**What changed, per figure** (all in the caption text only; no plotted pixel, no number, no check's PASS/FAIL
*verdict* changed - only how that already-checked data is worded in prose):
- **F2/F9**: dropped `(after its pre-registered window)` / `(after its pre-registered window {F9W} s; {F9SRC})` (the
  window number and citation are still computed and still checked by their own `check()`/`cite()` calls - just no
  longer quoted into the caption); dropped the `[a]` footnote marker and the `foot=[ob_cl("a"), OCASE_KEY]` list (now
  `foot=[]`); `ob_cl("a")` is still CALLED, as a bare statement, immediately before `save()`, so its own `check()`
  calls still run (2 checks + several `cite()` calls per figure) - only the verdict-bearing string it RETURNS is no
  longer placed in the caption. `verdict=` kwarg changed from a prose sentence to the exact pointer form, with every
  TA_verdicts.md row id this figure's content covers (H1.8/H1.9, EKF3/UKF/FGO, half real-time).
- **F5**: dropped `(H2.1 PASS, ...)`, `(H2.2 FAIL, ...)`, `(H2.4 FAIL)`, "FAILS", the `[a]`/`[b]` markers and the
  stray mid-body "Verdict rows: see docs/thesis/tables/TA_verdicts.md." sentence; every number that sat inside those
  parentheticals (the gain values, the 1.31-3.89 ratio, the live max/min range) is kept, just without the verdict
  word next to it. `ob_h23("a")`/`ob_h24("b")` still called bare for their `check()` side effects.
- **F6**: dropped `(every flight) [d]` -> `(every flight)`, and the whole `(H4.1 PASS 3/3 [a]; H4.2 FAIL [b]; H4.3
  PASS [c])` parenthetical (its only content beyond the verdict words, "3/3", isn't load-bearing - the per-flight
  RMSE values it was glossing are already in Table 5.1, which the same sentence already points to).
- **F7**: the most text - dropped the "H3.1, H3.2, H3.3 and H3.4 PASS 3/3 [a]" sentence entirely (its content, the
  per-lap ratios, is already stated two sentences earlier); for H-E5.1/S-E5.5/H-E3.1, replaced
  `f"{verdict} {count}"` interpolation with `{count}` alone (e.g. "bounded its live drift in 3/3 flights" instead of
  "(H-E5.1 PASS 3/3)"). **The first H-E3.1 reword here was wrong and is superseded - see "Correction, same session"
  below for the corrected wording and why.** Also reworded "pass all five closed-loop criteria" (F2) - "pass" as a
  bare word is banned the same as "PASS" by the checker below (word-boundary, case-insensitive), even used as an
  ordinary verb; **this clause was later dropped entirely, not reworded - see "Correction, same session" below.**
  `ext_checks()` was already being called unconditionally for its own `check()` side effects (unchanged); `ob_l("a")`
  added as a bare call for the same reason.
- **R3**: dropped the trailing "No verdict row attaches to this figure (descriptive; ...)" sentence from the caption
  body (`figs_thesis_results.py`'s `CAP3`); the equivalent pointer is now appended by
  `add_caption_verdict_pointers.py` in the new form.
- **R5, methods_architecture**: no body change needed (neither had verdict wording in its own generator-written
  text); only `add_caption_verdict_pointers.py`'s appended pointer line changed form.
- **`save()`'s default `verdict=` string** (used when a caller passes none - none of the 5 actual calls do, but kept
  consistent for any future figure) changed from `"Verdict: see docs/thesis/tables/TA_verdicts.md."` to
  `"Verdicts: Table A.4, none (descriptive)."`. `save_table()`'s own default (A1-A3 only) is untouched.

**Checks preserved by calling the `ob_*()`/`ext_checks()` functions bare (for their `check()`/`cite()` side effects)
instead of deleting the calls**: this is why the overall `figs_thesis.py` total stayed 352/352 rather than dropping
by the ~8-12 checks those calls perform - the instruction was explicit that doing this was preferred over losing
checks. Re-confirmed: F2 15/15, F9 23/23, F5 21/21, F6 15/15, F7 16/16 (all per-figure totals unchanged from the
pre-D113 baseline in this same session).

**New checker, `eval/caption_verdict_check.py`** (standalone, not folded into any existing script, per the
instruction): scans every `docs/thesis/figures_thesis/captions/*.md` except A1/A2/A3 (exempt) and checks, per file:
(a) the last non-empty line is exactly `Verdicts: Table A.4, (none (descriptive)|rows <ids>)\.` (regex-matched); (b)
every id named in that line is a real `docs/thesis/tables/TA_verdicts.md` ID-column value (read live from the
table, not hard-coded - a real cross-check against the data, per the advisor's suggestion that this is the natural
replacement for the checks that used to assert verdict sentences); (c) nothing above that line matches
`\b(pass(es|ed|ing)?|fail(s|ed|ing)?|not met|met|miss(es|ed|ing)?|verdicts?)\b`, whole-word and case-insensitive (so
it does NOT flag "Passive estimators" or "committee", but DOES flag a bare "pass"/"met" used as an ordinary verb -
which is why F2's "pass all five closed-loop criteria" needed rewording, see above). Multiple ids in one pointer
line are `;`-separated, not `,`-separated, because some TA_verdicts.md ids contain their own comma (e.g. "H1.8 EKF3,
half real-time (RTF 0.5)"). Result: **21/21** (8 files x up to 3 checks each; R3/R5/methods_architecture have no id
check since they're "none (descriptive)").

**`docs/thesis/tier1/check_claims_applied.py` - 2 of its existing checks directly asserted verdict-bearing substrings
in F7's caption** (`C2 F7 caption`: "H-E3.1 FAIL 0/9; 6 of 9 runs diverged"; `C3 F7 caption`: "H-E2.1 PASS 3/3 in
each" - both pre-existing, pre-dating this restyle). Per the instruction ("if a check asserted a verdict sentence in
a caption, change it to assert the pointer line instead"), these 2 rows were reworded to assert the SAME claim with
the SAME numbers, minus the verdict word: `"loop-closure advantage in 0/9 runs (6 of 9 runs diverged)"` and
`"loop closure also bounded live drift in 3/3 flights in each"` respectively (both are substrings of F7's actual new
caption text, confirmed). **Total unchanged: 58/58** (was already 58/58 before this change; the two rows were
failing immediately after the caption edit and passing again after the reword - no net change to the total, reported
as instructed). T1's own "H3.1-H3.4 PASS 3/3; 8 tags, correct tag IDs [k]" cell (checked against `T1_scorecard.md`,
not a caption) was NOT touched - T1 is a body table, out of this ruling's scope, see above.

**Combined PDF rebuilt last** (`eval/figs_thesis.py`, after `eval/add_caption_verdict_pointers.py`, per
`combine_extra_items()`'s dependency on the already-pointer-appended caption files on disk) - confirmed via
`pdftotext thesis_figures_combined.pdf -` that all 8 pointer lines appear verbatim on their caption pages (one
`grep -n "Verdicts: Table A.4"` per figure, all 8 found, none truncated or duplicated).

### Correction, same session, found by `advisor()` review of the committed D113 work (commit `1c6f46c`)

Three wording problems found after the D113 commit above, fixed in a NEW commit (not an amend) immediately after:

1. **F7's H-E3.1 reword was backwards - a real correctness bug, not just a style issue.** The first D113 pass wrote
   "the FGO as built lost its loop-closure advantage in 0/9 runs (6 of 9 runs diverged)". `count` ("0/9") is the
   number of runs where the criterion "LC live overall < no-LC live overall" was TRUE (confirmed from
   `tier1/scores/E3_verdicts.json`'s `per_run` dict: all 9 entries `False`) - i.e. loop closure was better in 0 of 9
   runs, so the advantage was lost in effectively all of them. "Lost its advantage in 0/9 runs" reads as "almost
   never lost it" - the opposite meaning. Reworded to attach the count to the criterion it actually measures: "...
   its live error with loop closure was below the no-loop-closure error on the same flight in 0/9 runs (6 of 9 runs
   diverged)." `check_claims_applied.py`'s C2 row (which asserts this exact substring) was updated to the corrected
   string and now documents the original bug in its own `detail` field, so it can't silently regress. The other
   three reworded fragments (H-E5.1 "bounded ... in 3/3 flights", S-E5.5 "higher error ... in 3/3 flights", H-E2.1
   "bounded live drift in 3/3 flights in each") were checked against the same direction logic and are correct as
   written - `count` there is the count of flights where the stated (non-inverted) description holds.
2. **F2's "inside all five closed-loop criteria (mission completion and the cross-track, heading-error, lateral-speed
   and oscillation bounds)" restated the H1.9 verdict in different words**, which the word-list checker can't catch
   (D113 bans verdict sentences, not just the literal words). Dropped the clause; H1.9 is already in F2's pointer
   line, and the sentence still carries its real content ("all 9 stay within 0.39 m of the centreline, so they
   overlap on the centreline at this scale").
3. **F5's "live max/min across conditions is 1.97 / 2.36 / 1.42 / 1.57" left four per-condition values unlabelled**,
   reading as one aggregate number. Relabelled "the live max/min ratio, condition A to D: ..." to match how the
   adjacent gains sentence already labels the same four-condition structure.

Re-ran `eval/figs_thesis.py` (352/352), `eval/caption_verdict_check.py` (21/21), `docs/thesis/tier1/
check_claims_applied.py` (58/58), `tools/check_numbers_frozen.py` (PASS); confirmed via `pdftotext` that all three
corrected sentences appear in the rebuilt combined PDF; `docs/thesis/tables/**` regenerated again (16 files,
provenance-line-only diffs) and reverted to HEAD again.

**Open items raised, not resolved, for the coordinator to decide** (flagging per the advisor's recommendation, not
fixed unilaterally):
- `eval/caption_verdict_check.py` enforces the banned-word list only; it cannot detect a verdict restated in other
  words (item 2 above is exactly that failure mode, caught by eye/advisor, not by the automated checker). Treat the
  21/21 result as "no banned word found", not "no verdict stated".
- F7 still carries the C2/C3 extension-experiment outcomes (user ruling 2026-10-24, claims C1-C5) in verdict-free
  prose in its own caption body, which is in tension with D113's "describe what is shown, verdicts go in Table A.4"
  - those sentences exist in F7's caption specifically BECAUSE claims C1-C5 require that content to appear there.
  Whether C2/C3's content should move out of F7's caption entirely (into the pointer line only, like every other
  figure) is a decision for the coordinator/user, not made here.
- F7 keeps "(pre-registered)" on the extension-experiment mentions - states that a rule was fixed in advance, not an
  outcome; kept for the same reason.
- F5's title and body still read "no live ordering claimed"/"no live ordering is claimed" - F2 and F9 had the
  equivalent "no ordering between the estimators is claimed [a]" sentence DROPPED entirely (its footnote marker made
  it unambiguously part of the removed verdict apparatus), but F5's phrasing was left as plain prose describing what
  is NOT claimed (arguably the opposite of a verdict, not a verdict), and its title in particular may be separately
  user-approved wording from an earlier session. Flagged rather than changed either way - the coordinator should say
  whether this is consistent with F2/F9's treatment or needs the same clause dropped.
(F9's own former open item - "inside the heading-error bound" restating H1.9 - was found and fixed in the third
correction below; no longer open.)

### Second correction, same session: the combined PDF's caption pages didn't end at the pointer either

A second `advisor()` review (after the fixes above were committed as `a3f155b`) found that D113's "ends with the
pointer" requirement was still violated on every one of the 8 figure pages in `thesis_figures_combined.pdf` - just
not inside `captions/*.md` (which `eval/caption_verdict_check.py` scans and which were correct), but in a SEPARATE
line `caption_page()` draws below every item's caption text: `"Cross-check against the results record: N/M values
match. The sources, the rows they are checked against and the build are listed in the figure index."` - a check
COUNT, one of D113's own named banned categories, printed unconditionally regardless of `kind`. `eval/
caption_verdict_check.py` only reads the standalone `captions/*.md` files, which don't include this line (it's
drawn directly onto the combined-PDF page from `it["checks"]`, not stored in `it["caption"]`), and the earlier
`pdftotext | grep "Verdicts: Table A.4"` only confirmed the pointer was PRESENT, not that nothing followed it - so
neither check this session had already run would have caught it.

**Fixed** in `caption_page()` (`eval/figs_thesis.py`): the check-count line (and its `else` sibling, "Cross-checked
by its own generator, not duplicated here: ...", used for the 3 items that come from another script) is now only
drawn `if it["kind"] != "figure"`. Confirmed this is exactly equivalent to "skip for the 8 D113 figures and nothing
else": `kind == "figure"` applies to exactly F2/F9/F5/F6/F7 (via `save()`) and METHODS_ARCH/R5/R3 (via
`combine_extra_items()`) across the whole script - every other item in the combined PDF is `kind == "table"` or
`"appendix"` (T1-T8, R1/R2/R4, A1-A3, TA), which are out of D113's scope and keep the line unchanged. Re-ran
`eval/figs_thesis.py` (352/352, unchanged); `pdftotext thesis_figures_combined.pdf -` confirmed all 8 figure blocks
now end exactly at their `Verdicts: Table A.4, ...` line, with the next line starting the following item
("Figure 4.1b (provisional). Heading error ..." etc., or a table's own unchanged "Cross-check against the results
record: ..." line) - checked by eye against the full extracted text, not just a presence grep this time.
`docs/thesis/tables/**` regenerated again (16 files, provenance-line-only) and reverted to HEAD again. Correction to
the wording two paragraphs up: the 5 figures' standalone chart `.pdf` files (F2/F5/F6/F7/F9, and A1-A3's) ARE
re-saved by every `eval/figs_thesis.py` run regardless of any caption change (matplotlib re-embeds a fresh
`CreationDate`/`ModDate` each time, exactly as A1-A3's already did before this session), so `git status` correctly
shows them modified after every regeneration in this handover - this is expected churn for the actual deliverable
figure files, not something to revert. Only the standalone chart `.png` files were confirmed pixel-identical (and
thus didn't show as modified) across all three of this session's `eval/figs_thesis.py` runs, since no plotted pixel
changed, only caption text and the combined-PDF caption-page layout.

### Third correction, same session: the cover page's own description was now inaccurate, and F9 had the same
### restated-verdict problem as F2

A third `advisor()` pass, after the check-count fix above, found two more items:

1. **The combined PDF's cover page** (the intro paragraph on page 1 of `thesis_figures_combined.pdf`) said "Each
   caption gives its cross-check count; the sources are in the figure index" and "Lettered footnotes [a], [b], …
   under each table AND CAPTION give the metric, n, the pre-registered rule and the result..." - both no longer true
   for the 8 D113 figures (no check count, no lettered footnotes, on any figure caption any more). Reworded to "Each
   table caption gives its cross-check count; a figure's cross-checks, and every item's sources, are in the figure
   index. Figure captions end with a pointer to their scored hypothesis/check row(s) in Table A.4
   (docs/thesis/tables/TA_verdicts.md)." and restricted the footnote sentence to "under each table".
2. **F9 still had F2's exact problem**: "...a maximum of 0.68° (Table 4.3), inside the heading-error bound (p95 ≤
   1.0°, max ≤ 2.0°; grey band ±2.0°)..." restates H1.9's B3 criterion as met, in different words than the banned
   word list (checked first: no `check()` anywhere asserts this literal phrase, confirmed by grep, so safe to
   reword). Changed to describe the drawn grey band without stating the threshold is satisfied: "...a maximum of
   0.68° (Table 4.3), so on the main axis their lines lie on zero (grey band: the ±2.0° heading-error bound); ...".
   F9 is removed from the open-items list below as a result.

Re-ran `eval/figs_thesis.py` (352/352, unchanged); `pdftotext` confirmed both new sentences; re-ran
`eval/caption_verdict_check.py` (21/21) and `docs/thesis/tier1/check_claims_applied.py` (58/58); also ran the three
other read-only checks the original handover's own table names, none of which touch generator logic this session
changed but whose inputs (captions, `index.md`) did: `docs/thesis/ablation/check_discussion.py` **18/18** (unchanged
from baseline), `docs/thesis/tier1/e6/check_e6_prose.py` **68 checks, 100 pairs, 0 mismatches** (unchanged),
`docs/thesis/methodology_factsheets/check_factsheets.py` **584 bullets, 1614 citations, 0 failed, PASS** (unchanged
- run from this worktree, which D109 already fixed to resolve citations correctly from inside `.claude/`
worktrees). `docs/thesis/tables/**` regenerated again and reverted to HEAD.

### Judgement calls made this session, for the coordinator to assign D-numbers to (not self-numbered here)

- The `;` (not `,`) separator between multiple ids in a `Verdicts: Table A.4, rows ...` pointer line, because some
  TA_verdicts.md ids contain their own comma (e.g. "H1.8 EKF3, half real-time (RTF 0.5)").
- The "Verdicts: Table A.4, none (descriptive)." wording for R3/R5/methods_architecture (no row of their own).
- Skipping the check-count line in the combined PDF for `kind == "figure"` only (not a new global rule - tables and
  appendix pages keep it).
- The two `check_claims_applied.py` C2/C3 reword strings (asserting the same claim/numbers without the verdict word).

### Final totals (this session, after the layout fixes, D113 and all three corrections above)

| check | result |
|---|---|
| `eval/figs_thesis.py` | 352/352 (unchanged throughout) |
| `eval/figs_thesis_drift.py` (R5) | 9/9 cross-checks, 3/3 frame check (unchanged) |
| `eval/figs_thesis_results.py` (R3) | 75/75 numeric, 185/185 source (unchanged) |
| `eval/ta_verdicts_check.py` | 146/146 EXACT (unchanged) |
| `docs/thesis/tier1/check_claims_applied.py` | 58/58 (2 rows reworded, total unchanged) |
| `tools/check_numbers_frozen.py` | PASS (unchanged) |
| `eval/caption_verdict_check.py` (new) | 21/21 |
| `docs/thesis/ablation/check_discussion.py` | 18/18 (unchanged) |
| `docs/thesis/tier1/e6/check_e6_prose.py` | 68 checks, 100 pairs, 0 mismatches (unchanged) |
| `docs/thesis/methodology_factsheets/check_factsheets.py` | 584 bullets, 1614 citations, 0 failed, PASS (unchanged) |

No existing total changed at any point in this session - every number above was already at this value before the
layout fixes, D113, or any of the three corrections began.

`docs/thesis/tables/**` regenerated as the usual unavoidable side effect of `eval/figs_thesis.py`, three separate
times (34, then 16, then 16 files - fewer each time as fewer scripts needed re-running), each time a 2-line diff per
file (only the embedded commit-hash provenance line changed) and the PNGs under it confirmed pixel-identical
(decoded-pixel comparison) before `git checkout HEAD -- docs/thesis/tables/`, every time. `docs/thesis/summary/**`
was not touched this session (its three consumer scripts were not re-run - nothing to restore).

Confirmed `pgrep -fa '[h]eavy.py|[f]go_replay|[a]rducopter'` empty and `~/thesis_data/FLIGHT_LOCK` absent before each
of the three commits.
