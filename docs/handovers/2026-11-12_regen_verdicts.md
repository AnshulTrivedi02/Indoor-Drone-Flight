# Handover: thesis regeneration stage 2 -- TA_verdicts (Table A.4) and R1 (hypothesis scorecard)

Branch `regen-verdicts`, base `fwd-camera` at `e8381ef`. Scope per the common brief and coordinator assignment:
`eval/ta_verdicts_check.py` + `docs/thesis/tables/TA_verdicts.{md,tex,png}`; `eval/figs_thesis_results.py`'s R1 output
`docs/thesis/tables/R1_hypothesis_scorecard.*`; `docs/thesis/figures_thesis/index_results.md` (written by the R1
generator). T1 (Table 3.3/scorecard summary elsewhere), the captions, the fact sheets and `methods_noise_exceptions`
(row 23) are **out of scope for this stage** -- another stage handles them. This document is the ROW-ID MAP those
later stages (and this report) need.

## 1. Row-ID map (old ID -> new ID)

IDs below are the `label (part)` / `id` column value exactly as `eval/figs_thesis_results.py`/`eval/ta_verdicts_check.py`
render it (`lab + " " + part` for R1 rows; the `id` column for superseded-appendix rows). TA_verdicts.md's "ID" column
carries the same string for every row transcribed from R1.

| # | old ID (fwd-camera HEAD) | status | new ID(s) |
|---|---|---|---|
| 1 | `H1.8 EKF3, real time (RTF 1.0)` | kept, labelled | **unchanged ID.** Result text gained " -- as recorded (n = 1; flight 1 of the n = 3 cell, D149(b))". New sibling row added (see #19). |
| 2 | `H1.8 EKF3, half real-time (RTF 0.5)` | kept, labelled | **unchanged ID.** Same treatment as #1. New sibling row added (see #20). Verdict word unchanged (NOT MET; the record still reads "MISS" in its own text, as recorded -- the *new* n = 3 row never uses the word "miss", per D149(a)). |
| 3 | `H1.8 UKF (real time; half real-time, final UKF port)` | **split** | **`H1.8 UKF, half real-time (final UKF port, abb0357d)`** (kept, labelled "as recorded"; this is the half-speed `+165.9 s` value only -- the real-time `+163.0 s` value is a DIFFERENT, superseded port). The real-time value moved to the superseded appendix as `H1.8 UKF, full real time` (#24). New sibling rows added (see #21, #22). |
| 4 | `H1.8 FGO (half real-time, final FGO node)` | **removed from the main table** | No "as recorded" row survives for FGO (D149(b) lists EKF3 full/half and UKF half only for that treatment). Moved wholesale to the superseded appendix as `H1.8 FGO, half real-time` (#25). Replaced in the main table by the new n = 3 row (#23). |
| 5 | `H1.9 EKF3` | unchanged | unchanged (not part of this re-fly). |
| 6 | `H1.9 UKF (final UKF port, half real-time)` | unchanged | unchanged (not part of this re-fly). |
| 7 | `H1.9 FGO (final FGO node, half real-time)` | **renamed, content replaced** | **`H1.9 FGO (corrected priors, 4c07374b/HEAD, half real-time)`**. Verdict unchanged (PASS, 3/3); values replaced with the corrected-prior re-fly (max lateral speed 0.119/0.0076/0.196 m/s, comfortably inside the band, vs the superseded original-prior reading's 0.246 m/s at 4 mm/s margin). Original-prior values moved to the superseded appendix as `H1.9 FGO, half real-time` (#26). |
| 8 | `H5.1` | kept, narrowed | **unchanged ID.** Result text no longer mentions the FGO-flying set at all (that reading moved to #27/#28). Primary verdict (EKF3 flying) unaffected. |
| 9 | `H5.2` | kept, values replaced | **unchanged ID.** Verdict unchanged (NOT MET / FAIL both). FGO values replaced with the corrected-prior reading (7.3-8.3 mm, highest in only 1 of 3 runs) vs the superseded original-prior reading (8.3-8.6 mm, highest in all 3) at #29. |
| 10 | `H5.3` | kept, re-derived | **unchanged ID.** Numerically unchanged (not driven by the FGO); original-prior reading superseded at #30. |
| 11 | `H5.4a` | kept, values replaced | **unchanged ID.** FGO jump narrowed to 7.1-24.0 mm; superseded original-prior reading (7-30 mm) at #31. |
| 12 | `H5.4b` | kept, values replaced | **unchanged ID.** Ratio range narrowed to 2.1-5.1; superseded original-prior reading (max/min 3.2-7.7) at #32. |
| 13 | `H5.5` (primary, part `""`) | kept, citation updated | **unchanged ID.** FGO citation now the corrected-prior re-fly; superseded original-prior reading (generic "every FGO band PASSES") at #33. |
| 14 | `H5.5 S2/S3 directional prediction (UKF- and FGO-flying hold sets, final builds)` | **renamed, recomputed** | **`H5.5 S2/S3 directional prediction (UKF-flying hold set, final port; FGO-flying hold set, corrected priors)`**. Verdict unchanged (NOT MET both). FGO recomputed with `s3rp_r*.json` via the SAME registered method (`_h5d()`): n_fgo 9 of 12 -> 6 of 12, r_fgo 7-27 mm -> 1-28 mm. Superseded original-prior computation at #34. |
| 15 | `H5.6 as pre-registered (EKF3-flying hold set)` | unchanged | unchanged (EKF3-flying only; not part of the FGO re-fly). |
| 16 | `H5.6 redefined primary (UKF- and FGO-flying hold sets)` | **renamed, values replaced** | **`H5.6 redefined primary (UKF-flying hold set, final port; FGO-flying hold set, corrected priors)`**. Verdict unchanged (PASS). FGO range unchanged in substance (2.8-30.3 ms vs the superseded 0.002-0.032 s, i.e. the same ~2-32 ms range) at #35. |
| 17 | `H5.6 jump criterion, kept as worded (UKF- and FGO-flying hold sets)` | **renamed, values replaced** | **`H5.6 jump criterion, kept as worded (UKF-flying hold set, final port; FGO-flying hold set, corrected priors)`**. Verdict unchanged (FAIL AS WORDED; no set threshold either way). FGO fail count 4 of 12 -> 8 of 12 (descriptive only). Superseded original-prior reading at #36. |
| 18 | `H5.7` | kept, re-confirmed | **unchanged ID.** Result text gained a note that the corrected-prior FGO-flying hold set was also checked (no lockout). |
| 19 | -- (new) | new row | `H1.8 n = 3 EKF3, full real time (RTF 1.0)` -- k/3 = 3/3. New category "REPORTED k/3 (no set rule)". |
| 20 | -- (new) | new row | `H1.8 n = 3 EKF3, half real-time (RTF 0.5)` -- k/3 = 1/3 (never "a miss"). |
| 21 | -- (new) | new row | `H1.8 n = 3 UKF, full real time (final port, abb0357d)` -- k/3 = 2/3. |
| 22 | -- (new) | new row | `H1.8 n = 3 UKF, half real-time (final port, abb0357d)` -- k/3 = 3/3. |
| 23 | -- (new) | new row | `H1.8 n = 3 FGO, half real-time (corrected priors, 4c07374b/HEAD)` -- PRIMARY k/3 = 2/3. |
| -- | -- | new row | `H5.1 (FGO-flying) corrected priors, 2026-11-12 regeneration` -- "H5.1 bounds applied to the FGO-flying set (as for S3v2)" (D150), PASS, not the primary H5.1 verdict. |
| -- | -- | new rows | `1B-H1`, `1B-H2`, `1B-H3` -- EKF3 + camera heading via Replay (DESCRIPTIVE, no verdict; D149(d)). Grouped under a new "Experiment 1B" heading in TA_verdicts.md (parallel to "Extension E2"-"E6"). |
| 24 | -- | superseded appendix | `H1.8 UKF, full real time` -- reason "superseded: earlier build" (`cl_ukf_a_tex`, pre-jitter-correction port). |
| 25 | -- | superseded appendix | `H1.8 FGO, half real-time` -- reason "superseded: original priors" (`cl_fgo_a_tex_half_v3`). |
| 26 | -- | superseded appendix | `H1.9 FGO, half real-time` -- reason "superseded: original priors". |
| 27-36 | -- | superseded appendix | `H5.1 (FGO-flying)`, `H5.2`, `H5.3`, `H5.4a`, `H5.4b`, `H5.5, drift band (FGO)`, `H5.5, S2/S3 directional prediction (FGO)`, `H5.6, redefined primary (FGO)`, `H5.6, jump as worded (FGO)` -- each "superseded: original priors" (`H5.3`'s row says "(numerically unchanged)"). |

**Important for stage 3 (captions):** the superseded appendix lives in a **separate markdown table**, under its own
`id` column, in both `R1_hypothesis_scorecard.md` and `TA_verdicts.md`. `eval/caption_verdict_check.py` only scans the
MAIN table's `ID` column (confirmed by running it, below) -- a caption pointer naming a superseded-only ID (e.g. the
bare string `H1.8 FGO`) will not resolve, by design.

## 2. Caption pointers broken by this renaming (`eval/caption_verdict_check.py`, not edited -- stage 3's job)

Ran `eval/caption_verdict_check.py` after the regeneration: **137/143** (confirmed **143/143** on the pre-regeneration
`TA_verdicts.md`, by temporarily restoring it to `fwd-camera` HEAD and re-running the checker, then restoring the
regenerated file and regenerating; both checks run from this same branch, nothing else changed). All 6 failures are
the same cause, the string `H1.8 FGO`, which no
longer appears as a MAIN-table ID (it only survives, textually, inside the superseded appendix's own `id` column,
which the checker does not scan):

- **F2** (`docs/thesis/figures_thesis/captions/F2.md:5`) -- live caption, in the current thesis figure set. Cites
  `"...; H1.8 UKF; H1.8 FGO; H1.9 EKF3; ..."`. Needs updating to point at the new counted ID
  (`H1.8 n = 3 FGO, half real-time (corrected priors, 4c07374b/HEAD)`), and/or the superseded one, and/or both,
  labelled -- stage 3's call.
- **F9** (`docs/thesis/figures_thesis/captions/F9.md:5`) -- same line, same fix needed.
- **A13, A14, A16, A18** (candidates) -- these were **already flagged stale** in the common brief's own instructions
  ("list stale candidate captions A13/A14/A16/A18 in your report, do not rebuild"), independent of this
  regeneration. Not rebuilt, per instruction.

`H1.8 EKF3, half real-time (RTF 0.5)` and `H1.8 UKF` (bare, no parenthetical) in the SAME F2/F9 caption lines still
resolve, because those ID strings are still an exact or prefix match in the main table (the EKF3 row kept its exact
ID; the only surviving `H1.8 UKF`-prefixed main-table ID is `H1.8 UKF, half real-time (final UKF port, abb0357d)`,
which the checker evidently matches on prefix). Only the FGO pointer fails.

## 3. Category totals, old -> new (D149(e): must reconcile between TA_verdicts and R1 -- they do, see below)

**R1 (Table 7.3), caption counts:**

| category | old (48 parts, 35 labels) | new (56 parts, 40 labels) | delta |
|---|---|---|---|
| PASS | 24 | 24 | 0 |
| FAIL AS WORDED | 4 | 4 | 0 |
| NOT MET | 17 | 17 | 0 |
| WITHDRAWN | 1 | 1 | 0 |
| DESCRIPTIVE | 2 | 5 | **+3** (1B-H1, 1B-H2, 1B-H3) |
| REPORTED k/3 (no set rule) | -- | 5 | **+5** (new category; the five n = 3 cells) |
| **total** | **48** | **56** | **+8** |

Superseded appendix: **12 rows**, not counted in any category above.

**TA_verdicts (Table A.4), main table (computed from the generated file, not hand-counted):**

| category | old (88 rows) | new (96 rows) | delta |
|---|---|---|---|
| PASS | 46 | 46 | 0 |
| FAIL (tier-1/ablation's own word) | 16 | 16 | 0 |
| FAIL AS WORDED | 5 | 5 | 0 |
| NOT MET | 17 | 17 | 0 |
| WITHDRAWN | 1 | 1 | 0 |
| DESCRIPTIVE | 3 | 6 | **+3** |
| REPORTED k/3 (no set rule) | -- | 5 | **+5** |
| **total** | **88** | **96** | **+8** |

Superseded appendix: **12 rows**, not counted. **Reconciliation: TA_verdicts' delta (+8: +3 DESCRIPTIVE, +5 REPORTED
k/3) exactly matches R1's delta** (R1's 8 new parts are the only thing TA_verdicts' Experiments 1-5 section
transcribes) -- no existing category count moved in either table, confirming no verdict WORD changed anywhere in
this regeneration, only values, citations and row identities (consistent with `numbers_refly.md` §5's own "No" for
every comparative criterion, and `numbers_extras.md`'s unchanged n = 1 verdicts).

## 4. What this stage did NOT touch (explicitly out of scope, per the common brief)

- T1 / Table 3.3, `limitations.md`, the methods fact sheets, `methods_noise_exceptions` row 23 (the FGO gating count)
  -- another stage's assignment.
- `docs/thesis/numbers.md` -- frozen, untouched, `tools/check_numbers_frozen.py` PASSES.
- Captions (F2, F9, and any other file naming a changed row) -- stage 3's job; see section 2.
- `docs/thesis/numbers_cl_heading_perflight.md` (the per-flight with-heading values addendum) -- read, but **not**
  folded into any new TA_verdicts/R1 row. It is purely descriptive per-flight detail for the EKF3 and (superseded)
  original-prior FGO with-heading sets, with no new verdict of its own; it most naturally feeds T1/the fact sheets
  (out of scope) rather than the verdict tables. Flagged for the coordinator in case this is wanted as a dedicated
  row later.
- `docs/thesis/diagnostics/numbers_fgo_gate_count.md` (the FGO gating count) -- read enough to confirm it carries no
  pre-registered hypothesis/verdict of its own (it is a DIAGNOSTIC count feeding Table 3.3 item 5 / the limitations
  entry, per the common brief's own framing); correctly out of scope for TA_verdicts/R1.

## 5. Discipline / checks run

- Snapshot sha256 of every R1/R2/R3/R4/TA_verdicts/index_results.md output taken before any generator run.
- `eval/figs_thesis_results.py`: 97/97 numeric, 239/239 source checks (was 77/77, 185/185).
- `eval/ta_verdicts_check.py`: 180/180 checks (new section added: quote verification against the new pre-registration
  and numbers files, using the previously-unused `must_contain()` helper -- extends the quote-verification pattern
  the common brief asked for).
- `tools/check_numbers_frozen.py`: PASS.
- `eval/caption_verdict_check.py`: 137/143 (6 failures, all `H1.8 FGO`; see section 2).
- Reverted stamp-only diffs: `R2_corrections_by_discovery.{md,tex}`, `R4_information_vs_estimator.{md,tex}`,
  `R3_trajectory_overlay.pdf` (each differed only in the embedded `commit <hash>` stamp / PDF `CreationDate`; `git
  checkout --` to HEAD). Re-ran `eval/add_caption_verdict_pointers.py` after each `figs_thesis_results.py` run (it
  strips F3's caption's... actually R3's own "Verdicts: Table A.4, none (descriptive)." pointer line every time R1/R3
  are regenerated in the same process, the same gotcha flagged for `figs_thesis_methods.py`'s Figure 3.1); its own
  side effect on `captions/R6.md` (a duplicated pointer line, an idempotency bug in that script, unrelated to this
  task) was reverted, not left in.
- Final `git status`: only `eval/ta_verdicts_check.py`, `eval/figs_thesis_results.py`,
  `docs/thesis/tables/R1_hypothesis_scorecard.*`, `docs/thesis/tables/TA_verdicts.*`,
  `docs/thesis/figures_thesis/index_results.md` and `docs/thesis/figures_thesis/tables_extra/TA_verdicts.{pdf,png}`
  changed.
