# Handover 2026-10-16: the rulings on the open pending items, applied

**Stage:** one stage. It applies METHODOLOGY "RULINGS (user, 2026-10-16): the open pending items" (M:14198-14216): the
rounding check, items 6, 7, 9 and 10, and the stale `numbers.md` §10 heading. **No estimator result was recomputed.** Only
stored values were read, plus wording, display and the `numbers.md` rows the rulings order. METHODOLOGY.md and the result
files were not edited. The frozen pack is untouched.

Commits on `worktree-agent-aab9fd614b0018fbe` (based on `fwd-camera` `3927c3c`):
- `e727416`: generator and docs (`eval/figs_thesis.py`, `numbers.md`, `methodology_definitions_draft.md`);
- the following commit: regenerated outputs (stamped `e727416`), `pending_items.md` and this handover.

## Rounding check (first)

| displayed value | full-precision stored value (repr) | in cm | old display | now |
|---|---|---|---|---|
| T condition A, FGO batch | `0.010479623174296593` (`expT/t_aggregate.json` conditions.A.mean_rmse_m["FGO hindsight (whole-flight batch)"]) | 1.0479623174296593 (float ×100) = 1.047962317429659300 (Decimal ×100) | 1.1 | 1.0 |
| L no-LC live, lower bound | `0.262532619256968` (`expL/T_A_r2_t245.json` tracks["nolc live"].rmse_m; the minimum of r1–r3) | 26.2532619256968 (float) = 26.253261925696800 (Decimal) | 26.2 | 26.3 |

- **Verdict: NOT a binary-float artefact.** Both flips are the true decimal rounding: 1.048 is below the half-point, 26.253
  is above it. The float ×100 and the Decimal ×100 agree to every printed digit.
- **Cause of the old displays: double rounding.** They were rounded from the 4-dp intermediates 0.0105 and 0.2625
  (numbers.md flag 8), not from the stored value.
- **`rd()` is unchanged.** It already rounds `Decimal(str(float(x)))` with ROUND_HALF_UP. The ruling's trigger condition is
  not met.
- **Extra scan.** Every value `rd()` printed in a full build was checked: none lies within 1e-6 of a half-tie at its printed
  precision, so no displayed cell anywhere hinges on float representation.
- **Displayed cells changed by the rounding check: none.**

## Item 6: `eval/results/phase5_analysis.json`. Verdict YES (current); column kept and cross-checked

- **Writer.** `final_rerun2/pipeline.log` has `BEGIN phase5` 2026-10-10T14:06:50 and `DONE phase5` 14:09:29. The file's mtime
  is 14:08:20. The main checkout and the worktree copies have the same md5 (`ca6da132…`).
- **Inputs.** All 126 inputs exist and were written ≤ 14:06:13. None was rewritten after the stage:
  - `phase4_{fwdc,fwdplainc}_{arms,evo}.json`, 14:06:31–14:06:50;
  - `{ukf,fgo}_{baseline,heading,heading_yawrate}/timing_and_fwd.npz`;
  - `fwd_meas/*.npz`.
- **Later stages.** The F-test, f4 and sens_yaw0 stages wrote other arm directories, not these.
- **Commit.** The file was last written by `819caab` ("FGO-only re-run complete", 21:36). It postdates the final consolidated
  re-run (`425e824`, 05:15).
- **On "postdates 21:35".** The FGO-only run's 21:35 is the end of its last stage (L), which does not feed Phase 5. The file
  is that run's own Phase 5 output, built on that run's phase4 replays.
- **Read literally, the test fails.** The mtime (14:08) PRECEDES the 21:35 completion, so the user may overrule the YES
  verdict. The earlier `final_rerun` phase5 copy (2026-10-09 21:19–21:22) was overwritten by this one.
- **Action:**
  - new `numbers.md` §6.3 row, with the magnitudes of `xtrack_head_m` at 3 dp, provenance and the JSON key;
  - two T2 checks against it;
  - the T2 "not cross-checked" note and the index "Not cross-checkable" line removed.
- **No older Phase 5 decomposition row existed** (grep), so nothing moved to Superseded. The §6.3 "NOT RESTATED" row is
  unchanged: it lists other quantities, which are still not restated.

## Item 7: the far-spawn EKF3 row

**`numbers.md` §17, new "S1 far" table.** Values are drift per loss in mm (5 s / 15 s / 30 s / ~7 s move), effective then end
of loss:
- `H_s1far_r1`: 15 / 12 / 3 / 4; 15 / 10 / 3 / 7.
- `H_s1far_r2`: 17 / 12 / 26 / 20; 19 / 12 / 26 / 23.
- `H_s1far_r3b`: 11 / 17 / 11 / 13; 12 / 17 / 11 / 16.

**Sources:**
- `expH/s1far_r*.json` (`losses[*].EKF3.effective.drift_m`, `drift_end_m`);
- METHODOLOGY quotes the end-of-loss values at M:12112-12117 (r1, r2) and M:12203 (r3b). They match.

**Checks:** two T5 checks, one effective and one end of loss. The T5 note and the index line are removed.

## Item 9: not-recomputed rows

**Search scope:**
- the tables (`.md`/`.tex`);
- `figures_thesis/index.md` captions;
- the text of `thesis_figures_combined.pdf` and `worlds_combined.pdf`;
- `limitations.md`, `thesis_vocabulary.md`, `methodology_definitions_draft.md`;
- the world index.

The search used each row's values and terms: roll/pitch 0.26°/0.53°/5.2°; RTF 0.72–0.81/0.759/0.768; latency
14.5–24.9 ms, "5–10 ms", "~4 ms"; 71.87/71.44/+0.43 px/s; step-time ms.

| not-recomputed row | thesis-facing places citing it (after this stage) |
|---|---|
| §1 cruise roll / pitch statistics | none |
| §1 camera-dataset RTF | none (the "half real-time (RTF 0.5)" / "RTF 1.0" mentions are the world-file setting, not a measured RTF) |
| §2 P2 latencies | none (vocabulary term 19 names "latency bands" as a definition, citing no value) |
| §11 ceiling effect size (+0.43 px/s) | none; **no ceiling-vs-`dsn` transition comparison exists** in thesis-facing material (T2 compares textured only; T3 pools blank-floor flights), so the standing rule is not triggered |
| §14 timing | none (A3's L compute cost is §16.3, restated 2026-10-11, not §14) |

- **Nothing needed a label.**
- **The rule is written down** (label text, "never unaffected", the withdrawn flow reasoning, the ceiling standing rule) as a
  new section in `methodology_definitions_draft.md`.
- **`numbers.md` §9's last bullet** ("These must be recomputed … before being cited") is replaced with the ruling. The old
  bullet is verbatim in the new superseded block.
- **No wording describing these rows as unaffected was found**, so none was removed.

## Item 10: S-A4

- **T7.** UKF (a) run 1 reads "S-A4 not applicable ‡" and FGO (b) run 1 reads "S-A4 not scored ‡". Each follows the record
  for its run, rather than one combined label.
- **‡ footnote.** It quotes METHODOLOGY.md:11490 ("- **S-A4:** not applicable (an (a) run).") and METHODOLOGY.md:11827
  ("- **S-A4:** not scored (no touchdown). One LAND entry, no conflict between the two paths.") with file:line. Both lines
  were verified, and a new T7 check reads them at build time (exact match).
- **A2 safety page.** The criteria cell now reads "A4 FAIL (score file: rearmed_after_disarm null) ‡". The note gives the
  raw entries (S-A4 FAIL, one LAND entry, `rearmed_after_disarm` null) and says T7 shows them as the record does.
- **Checks.** The raw-entry check moved from T7 to A2 and now checks `PASS`, `n_land_entries_after_t_f` and
  `rearmed_after_disarm` against the two score files.

## §10 heading

The heading is now "## 10. Phase 4 pre-registered values (the results are in §6.6)", with a one-paragraph pointer. The old
heading and paragraph are verbatim in "Superseded by the rulings of 2026-10-16 (open items)" at the end of `numbers.md`.

## Regenerated and cross-check

- **Regenerated:**
  - T1–T8 (`.md`/`.tex`/`.png`), F2/F5/F6/F7, A1–A3 and `thesis_figures_combined.pdf`;
  - `figures_thesis/index.md`, stamped `e727416`;
  - `pending_items.md` (closed table added; the former "Still open" table kept, marked ALL CLOSED).
  - The worlds PDF and world index were not touched (nothing in them changed).
- **Cross-check: 128/128 match** (was 123). The +5 are 2 in T2, 2 in T5 and 1 in A2. In T7 one check was replaced. No
  mismatch, none forced.
- **Baseline.** Before any edit, an unchanged rebuild reproduced every committed table and caption except the commit stamp.

## Every displayed change (against the committed outputs at `3927c3c`)

- **Numbers: none.**
- **Text:**
  - T2 Phase 5 note: "It has no restated row … not cross-checked" became "(the final estimator builds)".
  - T5 note: the "far-spawn drifts have no row … not cross-checked" clause is removed.
  - T7 cells: "S-A4 FAIL in the score file ‡" became "S-A4 not applicable ‡" (UKF (a) v1 run 1) and "S-A4 not scored ‡" (FGO
    (b) original run 1).
  - T7 ‡ footnote rewritten, with quotes and file:line.
  - A2 p2: the A4 cells of the two runs and the note.
  - The index: the "Not cross-checkable" lines for T2 and T5 are removed, and the check counts are updated.

## Residual grep (thesis-facing outputs)

- **"unaffected" / "do not depend" / "independent of the correction" / "not affected": 0 hits** in the tables, the index, both
  PDFs' text, `limitations.md`, the vocabulary and the world index.
- **Intended hits:** `methodology_definitions_draft.md:224-225` (the new rule itself: "Never describe one as unaffected …
  WITHDRAWN").
- **Other hits, none about the four not-recomputed rows, so left unchanged:**
  - **`headline_claims_before_after.md`, which is thesis-facing** (the previous stage removed claim 15 from it as
    thesis-facing material). It has three hits:
    - `:21`: "The claim (`fwdc`) is unaffected by the 0.1 rad check".
    - `:42`: "the FGO_hard F1 lockouts … are not in the rule …, so the verdict is unaffected", about the F1 decision rule.
    - `:61`: "`fwdc` and `dsn` are unaffected beyond the FGO noise floor", about the 0.1 rad initial-yaw sensitivity check.
  - **`final_restatement_draft.md:438`**, a record draft: "Results are unaffected: all H-L verdicts are unchanged", about the
    L wall-time slowdown.
- **New code-family hits, intended by ruling 10** (the captions ruling had removed such codes):
  - "METHODOLOGY.md:11490" and "METHODOLOGY.md:11827" in the T7 footnote (`.md`/`.tex`/png/PDF);
  - `rearmed_after_disarm` in A2 p2 (cells and note).

## Not done / for the user

- **T7 wording.** The two runs use the record's own words, "not applicable" and "not scored". The ruling's combined phrase
  "not applicable / not scored" can be used instead if preferred.
- **`.tex` was not compiled** (no TeX here). ‡ maps to `\textdaggerdbl{}` as before.
