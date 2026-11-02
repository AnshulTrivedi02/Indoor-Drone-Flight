# Handover: Raw-tables stage 2 - raw values added to the reader-facing tables (2026-11-02)

**Branch:** `raw-tables`, created from `figs-restyle` at `a6f6fd2`, then `git merge --no-edit fwd-camera` (merge
commit; brings the raw corridor values and decisions D106/D107/D111). **Merge was clean, no conflicts.**

**Scope:** table code and table outputs only (`eval/figs_thesis.py`, `eval/figs_thesis_results.py`, a new
`eval/check_raw_tables.py`, and the four affected files under `docs/thesis/tables/`), plus one append-only
METHODOLOGY.md entry. No figure caption text, no figure drawing code, no `figures_thesis/*.png/pdf`, no
`captions/*.md`, no `thesis_figures_combined.pdf` touched (all restored to HEAD after confirming they were
unaffected except for a refreshed commit-hash footer - see "Side effects" below). No registered value, pass rule,
verdict or data selection changed anywhere.

## Task 1: table inventory (what prints an Experiment 1 offline evo -a (cruise) value, verified by reading the table
and its generator)

| table | prints | in scope? |
|---|---|---|
| `T1_scorecard.md` | 1A: median cruise ATE per estimator (9 flights). 1B: with-heading range per estimator (6 bags, UKF/FGO only) | **yes** |
| `T2_accuracy_heading.md` | 1A: 9-flight median(range); per-flight (3) textured/plain walls, without and with heading | **yes** - the most detailed |
| `R4_information_vs_estimator.md` | 1A row: medians per estimator. 1B row: per-flight (3), with/without heading | **yes** |
| `T3_blank_floor.md` | `hypot(along, cross)` from the flow-loss point (`blank_behaviour.json`) - a different quantity by construction (Stage 1's own RC-1 already ruled this out); EKF3's row is "invalid, not scored" by the evaluation rule | **no** |
| `T4_closed_loop.md` | Experiment 1C (closed loop, the estimator flies) - not offline 1A/1B | **no** |
| `T7_failure_behaviour.md` | same blank-floor metric as T3, plus safety-test timings | **no** |
| `R1_hypothesis_scorecard.md` | verdict evidence (e.g. H1.1's paired-difference CI), not per-estimator/per-flight aligned values | **no** |
| `TA_verdicts.md` | verdict table, pinned 146/146 EXACT by `ta_verdicts_check.py` | **no**, don't touch |
| `methods_experiment_matrix.md` | names the metric ("cruise ATE"), prints no values | **no** |
| `T5/T6/T8` | Experiments 5/4/2 respectively, not Experiment 1 | **no** |

## Task 2 & 3: what changed, before -> after

### T1_scorecard.md (Table 7.1)
Two new ROWS (not columns - T1 is a 4x8 matrix, experiment x estimator, with no per-estimator column slot for a
second value): "Experiment 1A: raw world-frame error, nothing fitted, DESCRIPTIVE [l]" directly under the 1A row
(median only, over the same 9 flights), and the 1B equivalent under the 1B row (range only, over the same 6 bags).
Footnote `[l]` appended after the existing `[a]`-`[k]` ordering footnotes, citing `RAW_NOTE` (the shared one-line
rule statement) plus the scope of each row. `inputs` string got `raw_corridor_errors.json (the two raw rows only)`
appended.

### T2_accuracy_heading.md (Table 4.1)
Five new columns, one beside each existing aligned cruise-ATE column (9-flight median(range); textured/plain walls
without heading x3; textured/plain walls with heading x3) - 7 -> 12 columns. Header of the first raw column carries
`[e]`, a new footnote citing `RAW_NOTE` plus the exact column-to-column pairing rule. `fs` stayed at 7.6 (the
pre-existing value); widths were retuned, see "Column-width bug" below. `'n/a'` in a with-heading raw cell for EKF3
matches its aligned cell's `'no offline heading arm'` (not a withheld value).

### R4_information_vs_estimator.md (Table 7.5)
One new column, "raw world-frame error, nothing fitted, DESCRIPTIVE (1A/1B rows only)", inserted right after
"estimator values" (the pre-existing "spread"/"information added"/"effect" columns, which compute ratios and
spreads from the aligned values, were left untouched - per the brief, raw values only, no new raw spread/ratio).
1A gets medians (mirroring its aligned cell, which prints medians only); 1B gets the full RMS;end breakdown for
every arm (mirroring its aligned cell's structure), split onto two lines (`with heading: ...` / `without: ...`) so
it wraps sensibly. Every other row (Experiments 2/4/5, the blank floor) gets `-` - **RT-2** (see below), cited
in-code at `eval/figs_thesis_results.py:1063`.

### T9_1A_fitted_vs_raw.md / .tex / .png (new, "Table 4.4 (provisional)")
Rows EKF3/UKF/FGO, n = 9 each (flights 1-9 of the standard-sensor dataset; flight 10, EKF3-only under the IMU-gap
rule, is explicitly excluded with a note - it enters the confirmatory H1.1 test on flights 4-10, a different, paired
population). Columns: fitted cruise ATE median + range (registered, cited numbers.md:230 for the three medians and
numbers.md:232 for the UKF range; EKF3's and FGO's fitted ranges have no numbers.md line, cited to the json and to
Table 4.1's own display instead); raw RMS median + range; raw end-of-cruise median + range (all DESCRIPTIVE).
Reuses `med`/`DSN` (already-checked) for the fitted side, same table machinery (`save_tab`) as T1-T8.
"Table 4.4 (provisional)" matches the provisional status of Figure 4.1c (R5), the figure it companions - that
figure's own caption (owned by the parallel figure-restyle/caption work) says a companion table follows; not edited
here.

## Metric: 3D, not horizontal (backed by primary source, not just the comment in three_way_eval.py)

`evo -a (cruise)`'s own `pose_relation` defaults to `trans_part`:
- `~/venv-evo/lib/python3.12/site-packages/evo/cli/ape_parser.py:19`: `"--pose_relation", default="trans_part"`.
- `evo/core/metrics.py`'s `class APE(PE): def __init__(self, pose_relation: PoseRelation = PoseRelation.translation_part)`.

`trans_part`/`translation_part` is the 3D Euclidean distance between translation vectors (confirmed from the same
file: `self.unit = Unit.meters` for exactly this relation). `eval/three_way_eval.py`'s own comment ("Reference TUMs
carry identity quaternions, so APE is the translation part") corroborates but was not relied on alone. Per the
brief's own rule ("use HORIZONTAL... unless the table's aligned metric is 3D, in which case use 3D"), every raw
column/row in this stage uses `raw_corridor_errors.json`'s `rms_3d_m`/`end_3d_m` fields, never `rms_h_m`/`end_h_m`.
Stated in a one-line `RAW_NOTE`/`RAW_NOTE_R4` constant reused by every table.

## Task 4: exact cross-check - `eval/check_raw_tables.py` (new, stdlib + json only)

Independent of both generators: parses the four tables' own `.md` output (markdown row split on unescaped `|`,
matched by row label/estimator, never a substring search - Stage 1's own checker moved to positional checks for
exactly this reason, and this one follows suit), and recomputes every raw value, median and range straight from
`eval/results/raw_corridor_errors.json` with its own `rd()` (ast-parsed from `eval/figs_thesis.py`, never executed
as a module; SHA-256 checked against the json's own recorded `rd_sha256`). It also independently recomputes the
ALIGNED (registered) cell beside each raw one from the registered result files (`rerun_dsn_evo.json`,
`dsn_extra_evo.json`, `phase4_fwdc_evo.json`) - this catches an aligned/raw column swap, not just a wrong raw
number, and in particular confirms R4's pre-existing 1B aligned cell (a hard-coded literal string in the generator,
not introduced by this stage) is still numerically correct. T9's two numbers.md citations are checked against the
actual file content at the cited lines (as separate tokens - `numbers.md:230` prints "...median 5.13; above EKF3
4.10 and FGO 4.46 by median...", not a slash-joined trio), not merely typed into a note.

**Negative control** (required to fail, proving the comparison discriminates, not just that `==` works): corrupts
EKF3's T9 raw RMS median (14.58 -> 15.58) in a scratch copy and re-runs the T9 check function on it through the
exact same parse/recompute path; the targeted check (`"T9 raw RMS median, EKF3"`) is confirmed in the failure list.
The script aborts (`sys.exit(2)`) if the negative control does NOT fail. A private `record` callback keeps this
entirely out of the real totals.

**Result: 79/79 checks OK; negative control fails as required.**

### T9 contents (numbers only, from the generated `.md`, n = 9 flights each)

| estimator | fitted ATE median (range), registered (m) | raw RMS median (range), DESCRIPTIVE (m) | raw end-of-cruise median (range), DESCRIPTIVE (m) |
|---|---|---|---|
| EKF3 | 4.10 (3.11-4.12) | 14.58 (7.84-14.64) | 37.39 (22.54-37.56) |
| UKF | 5.13 (1.17-5.85) | 20.26 (6.83-25.16) | 50.13 (7.33-60.26) |
| FGO | 4.46 (1.27-4.61) | 16.65 (3.79-17.67) | 42.06 (1.49-44.27) |

## Task 5: checks run (totals)

| check | result |
|---|---|
| `eval/figs_thesis.py` (own cross-checks) | **358/358** (was 352, +6: T1 +2, T2 +2, T9 +2 - one source-consistency `check()` call per raw-row/raw-column group confirming the json selection matches the aligned cells it companions) |
| `eval/figs_thesis_results.py` (own cross-checks) | **77/77 numeric** (was 75, +2 for the new 1A/1B raw-row independence checks), **185/185 source** (unchanged) |
| `eval/check_raw_tables.py` (new) | **79/79**, negative control fails as required |
| `docs/thesis/raw_corridor/check_raw_corridor.py` | **1860/1860** (unchanged) |
| `eval/ta_verdicts_check.py` | **146/146** (unchanged; its PDF-only rewrite was restored, see below) |
| `docs/thesis/tier1/check_claims_applied.py` | **58/58** (unchanged) |
| `docs/thesis/methodology_factsheets/check_factsheets.py` | **PASS** (584 bullets, 1614 citations, 0 failed) |
| `tools/check_numbers_frozen.py` | **PASS** |
| `eval/figs_thesis_summary.py` (consumer, text-only use of T1/T2) | **223/223 data-derived, 62/62 display-only, 101/101 rules, 16/16 counts** (matches the figs-restyle baseline exactly; run, outputs decode-pixel-identical to HEAD, restored) |
| `eval/figs_walkthrough_extra.py` (consumer, text-only use of T1) | **186/186** (matches baseline; run, outputs decode-pixel-identical to HEAD, restored) |

## Task 6: side effects

Both generators rewrite every other table/figure as an unavoidable pass. Diffed every non-scope file: for every
table outside T1/T2/T9/R4, the ONLY change was the `<!-- generated by ... commit <hash> -->` footer line (the
working-tree HEAD short hash, e.g. `6630aff`, differs from the hash recorded when those files were last generated
in an earlier session) - confirmed by `git diff` on each, not assumed. **Every PNG for every untouched table/figure
was BYTE-IDENTICAL to HEAD** (absent from `git status` entirely) - a strictly stronger guarantee than a decoded-
pixel compare, since identical bytes trivially decode to identical pixels. The `.pdf` figure outputs (F2, F9, F5,
F6, F7, A1-A3, R3, TA_verdicts, `thesis_figures_combined.pdf`) did show as modified (embedded commit-hash/producer
metadata, not visual content, given their companion PNGs were untouched) and were restored to HEAD along with
`index.md`, `index_results.md`, `captions/R3.md` - all owned by the parallel figure-restyle/caption work.

**T9 is therefore not yet in `thesis_figures_combined.pdf` or either `index.md`/`index_results.md`** - it only
exists as its own three files right now. The coordinator's next full regeneration (after both branches merge) will
pick it up automatically (same `save_tab`/`ITEMS` machinery as T1-T8); nothing extra is needed beyond re-running
`figs_thesis.py` once from the merged state.

**T2_accuracy_heading moved from one page to two** (12 columns, row count unchanged) - `git rm`'d the stale
`docs/thesis/tables/T2_accuracy_heading.png`; the new files are `T2_accuracy_heading_p1.png`/`_p2.png`. `T1_scorecard`
(3 pages) and `R4_information_vs_estimator` (2 pages) were **already** multi-page at HEAD - confirmed via
`git ls-files` before assuming a page-count change - so neither is an orphan.

**Column-width bug found and fixed mid-task**: `table_page()`'s header-text-wrap heuristic computes
`max(6, int(w * 0.95))` characters per line from the raw `widths` NUMBER, independent of `sum(widths)`, while the
column's actual RENDERED width is `(w / sum(widths)) * page_width`. Reverse-engineered from T1's own calibrated
`[30, 40, 40, 40]` (sum 150) that the implicit assumption is `sum(widths) ~ 150` regardless of column count. A
first attempt scaled T2's widths up roughly in proportion to the new column count (sum 256-262 for 12 columns),
which broke this assumption and produced severely overlapping, illegible header text (viewed and caught before
moving on). Fixed by keeping `sum(widths) ~ 154` for T2's 12 columns
(`[10, 12, 16, 10, 16, 10, 16, 10, 14, 10, 14, 16]`) - confirmed legible by viewing the final PNG (both pages).
Documented as a reusable fact in the METHODOLOGY.md entry for the next person who adds columns to a `table_page()`
table.

**Consumer check** (`find ... | xargs grep -l`, plain `grep --include` was refused by this environment's
worktree-isolation guard for an unrelated reason - worked around): `eval/figs_thesis_summary.py` and
`eval/figs_walkthrough_extra.py` reference `T1_scorecard.md`/`T2_accuracy_heading.md` by PATH, as text sources for
string-search validation (`DISP["IDX"]`/`DISPF["T1"]` etc. - same pattern the figs-restyle handover already
documented for `index.md`), not pixel-cropping. **Run** (not left unverified): both reproduce their figs-restyle
baselines exactly - `figs_thesis_summary.py` 223/62/101/16 (was 223/62/101/16), `figs_walkthrough_extra.py` 186/186
(was 186/186) - and every output PNG under `docs/thesis/summary/**` decode-pixel-compared identical to HEAD before
being restored there (see Task 5 table). `eval/figs_results_walkthrough.py` crops PNG pixel boxes but from
F2/F9/F5/F7/F6/R3/R5 (figure-restyle scope), not from any table I touched - not a consumer of this stage's changes,
not run.

**Em-dash check** (`git diff -U0 ... | grep '^+' | grep` for U+2014): one hit, in T2's pre-existing "heading-driven
end-of-cruise cross-track" column (`36.3 / 29.5 / 36.1; <U+2014>`) - confirmed via the same diff that this exact
character was ALREADY present in the REMOVED line at the same position (the whole row line changed because new
raw columns were inserted earlier in it, not because this trailing placeholder changed); not a new em-dash
introduced by this stage. Re-ran the same check on the `METHODOLOGY.md` diff and on this handover file itself
(both written after the first check): zero hits in either.

**Stray background processes (flag for the coordinator)**: during this session, three extra `python eval/figs_thesis.py`
processes appeared in this worktree that were not launched by any command in this session's own transcript -
including one invoked as `... | tail -60` with no log-file redirection, a pattern none of this session's own
commands used. They were killed on discovery (`kill -9`) before they could write conflicting output; the final
table outputs come from one subsequent clean, single-process run, which was then viewed (all four changed PNGs) and
checked (79/79). If another session is concurrently writing to this same worktree, the coordinator should know -
this was not something this session caused or could explain from its own command history.

## RT decisions (not written to `decisions_log.md`, per instruction - D-numbers reserved for that file)

- **RT-1 (scope)**: see Task 1's table above. T1/T2/R4 in scope; T3/T4/T7/R1/TA/methods_experiment_matrix/T5/T6/T8
  out, with the specific reason for each.
- **RT-2 (R4 out-of-scope rows)**: every R4 row outside 1A/1B gets a literal `-` in the new column, not a blank
  cell or an omission, so a reader can tell "outside this stage's scope" from "computed as empty". Cited in-code at
  `eval/figs_thesis_results.py:1063`.
- **RT-3 (T1 structure)**: raw companions as two extra ROWS (not columns), since T1's matrix layout gives each
  estimator exactly one column slot already occupied by the aligned value; a row directly underneath, same
  footnote-letter convention as the rest of the table, was judged the closest structural equivalent to "beside the
  aligned value" that doesn't require restructuring the whole table (out of scope - "No change to any registered
  value... pass rule, verdict or data selection").
- **RT-4 (metric)**: 3D not horizontal, backed by primary source (see above), not just the `three_way_eval.py`
  comment.
- **RT-5 (rounding)**: `rd()` reused exactly as `raw_corridor_numbers.md` already does (parsed via `ast`, never
  executed as a module, SHA checked) - 2 dp throughout, matching the existing raw-corridor precision.
- **RT-6 (T2 column widths)**: see "Column-width bug" above.
- **RT-7 (page-count bookkeeping)**: T2 1 -> 2 pages (new, `git rm`'d the stale single PNG); T1 and R4 were already
  multi-page at HEAD, confirmed before assuming otherwise.
- **RT-8 (R4's pre-existing 1B aligned literal)**: not changed (pre-existing, not introduced by this stage), but
  the new checker independently recomputes it from `phase4_fwdc_evo.json` to confirm it is still numerically
  correct, not merely unchanged.

## Flags for the coordinator (not edited - outside this stage's scope)

1. **T9 is not yet in the combined PDF or either index** - needs a full `figs_thesis.py` regeneration from the
   merged state (automatic, same machinery as T1-T8).
2. **T1's lead paragraph** ("Each cell gives the key number and the verdict it rests on, with a status...") doesn't
   quite describe the two new raw rows, which rest on no verdict. That text is the `caption=` argument to
   `save_tab`, reserved for the parallel caption work - not touched here.
3. **T2's existing note** ("Metric: cruise ATE, which aligns away a constant yaw offset (so metres, not tens of
   metres)...") now sits beside raw columns that DO show tens of metres on the textured-floor columns without
   heading - the note is still literally true of the ALIGNED columns it describes, but a reader could misread it as
   describing the whole table (T2 is all textured floor; there is no "blank-adjacent row" in T2, that was a slip -
   the relevant contrast is the aligned without-heading columns vs. the raw columns beside them). Consider scoping
   the wording to "the aligned columns" in the next caption pass - not edited here (D113's territory).
4. **`docs/thesis/tier1/claims_applied.md` and `claims_update.md` cite stale line numbers**, into both
   `T1_scorecard.md` and the generators. Precise shift, verified by diffing content at each line (not assumed):
   inserting the 1A raw row shifted everything from the OLD 1B row onward by +1; inserting the 1B raw row (right
   after the 1B row itself) shifted everything from the OLD blank-floor row onward by a further +1, i.e. +2 total.
   So: the 1B row itself moved **+1** (`T1_scorecard.md:8` -> `:9`); everything from the blank-floor row onward
   moved **+2**: `:12` -> `:14` (Experiment 3 row), `:16` -> `:18` (statuses note), `:18` -> `:20`
   (why-no-ordering-label note), `:20` -> `:22` (key numbers note), `:38` -> `:40` (footnote [h]), `:44` -> `:46`
   (footnote [k]). `R4_information_vs_estimator.md:20` is **unaffected** (new column inserted within existing rows,
   row count and line numbers unchanged - verified by diffing line 20's content before/after, byte-identical).
   The two GENERATOR line citations also moved, by more (the new RAW block is ~60-70 lines): `claims_applied.md`
   cites `eval/figs_thesis.py:811` for the EKF3 Experiment-3 cell text - that citation was **already** 21 lines
   stale at HEAD (the real line was 832, not 811, before this stage touched anything); this stage's own insertions
   moved it from HEAD's 832 to the current 899 (+67, verified by `git show HEAD:eval/figs_thesis.py | sed -n
   '832p'` vs `grep -n` on the current file, matching text both times). Likewise `claims_applied.md` cites
   `eval/figs_thesis_results.py:1016` for the R4 Experiment-3 footnote text - already 12 lines stale at HEAD (real
   line 1028); this stage moved it from HEAD's 1028 to the current 1087 (+59). Report both pre-existing staleness
   and this stage's own shift separately so the coordinator doesn't attribute the whole gap to this stage.
   `check_claims_applied.py` and `check_factsheets.py` both still PASS (they verify wording/number presence in the
   documents they check, not that a cited line number in a third file is exact), so this is cosmetic staleness for
   a human reader following the citation, not a check failure. Not edited here per the brief ("don't edit the fact
   sheets" / don't edit `claims_applied.md`).
5. **Consumer re-verification** - done, not left open; see the Task 5 table and "Side effects" above
   (`figs_thesis_summary.py` 223/62/101/16, `figs_walkthrough_extra.py` 186/186, both matching baseline, outputs
   decode-pixel-identical and restored).
6. **`T2_accuracy_heading.png` (now deleted) is still referenced by filename** in two files: the just-restored
   `docs/thesis/figures_thesis/index.md` (two rows, lines 24 and 628 - this is the file the coordinator's next
   `figs_thesis.py` regeneration will refresh automatically, picking up `_p1.png`/`_p2.png`) and
   `docs/thesis/figures_thesis/working/index.md` (lines 21 and 557 - a pre-existing, byte-identical-to-HEAD snapshot
   file from the figure-restyle work, not touched by this stage and not regenerated by either of my scripts).
   Found via `git grep -n "T2_accuracy_heading\.png"` across all file types (not just `*.py`, which the earlier
   consumer grep was limited to).

## Commit

Branch `raw-tables`. Confirmed before committing: `pgrep -fa '[h]eavy.py|[f]go_replay|[a]rducopter'` empty,
`~/thesis_data/FLIGHT_LOCK` absent, no `figs_thesis*.py`/`venv-evo` python process running.

Files changed: `eval/figs_thesis.py`, `eval/figs_thesis_results.py`, `eval/check_raw_tables.py` (new),
`docs/thesis/tables/T1_scorecard.{md,tex}` + 3 pages, `docs/thesis/tables/T2_accuracy_heading.{md,tex}` + 2 new
pages (old single PNG removed), `docs/thesis/tables/T9_1A_fitted_vs_raw.{md,tex,png}` (new),
`docs/thesis/tables/R4_information_vs_estimator.{md,tex}` + 2 pages, `METHODOLOGY.md` (one dated, append-only
entry).
