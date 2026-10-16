# PENDING items that would appear in the thesis

*First written 2026-10-16 (branch `fwd-camera` at `6a0fa0f`). **Updated 2026-10-16 after the user's rulings on this list**
(METHODOLOGY "RULINGS (user, 2026-10-16): the pending items (`docs/thesis/pending_items.md`) and captions", M:14176-14196;
applied in `docs/handovers/2026-10-16_pending_rulings_applied.md`). "M" means `METHODOLOGY.md`, followed by its line number.*

**Status now:** **no Tier 1 item remains in the thesis.** Of the 4 literal PENDING items, three are CLOSED by ruling and the
fourth (the rung-1 first-leg length) is moved out of the thesis list: it stays open in the real-flight plan only. Of the 7
Tier 2 items, two are CLOSED (items 5 and 8), one was already ruled (item 11), and four still need a ruling or an action
(items 6, 7, 9, 10).

## Closed by the rulings of 2026-10-16

| # | item | ruling | what was done |
|---|---|---|---|
| 1 | Experiment H comparative criteria (H-H2, P-H3, H-H4) on the re-flown sets | item 1: the S2v2/S3v2 verdicts are PRIMARY; S2/S3 move to the appendix as superseded builds; "identical to the original-build verdicts"; PENDING removed | `numbers.md` §17.2 restated (old heading and "Not adopted" paragraph kept verbatim in "Superseded by the rulings of 2026-10-16"); T1 and T5 give the final-build verdicts with the "identical" wording; Appendix A2 has a new page with both sets side by side, the S2/S3 column labelled "superseded builds" (6 new cross-checks) |
| 2 | Scale-cause check "5a" | item 2: DROPPED; a limitation | `docs/thesis/limitations.md` created (no limitations list existed); `numbers.md` flags, resolved 4, and `methodology_index.md` (two places) mark it dropped. The `numbers.md` row in "Former sections 6–9" stays as it was (a verbatim superseded block) |
| 3 | Rounding rule for the four last-digit transcriptions | item 3: ADOPTED for thesis tables only, at generation time | `eval/figs_thesis.py` `rd()` rounds every printed number once, half away from zero, from the full-precision file value; `numbers.md` keeps full precision (flag 8 restated as adopted); the rule is in `methodology_definitions_draft.md`. Displayed values that changed: T condition A FGO batch (1.1 → **1.0** cm, in the T1 cell and the F5 caption) and L no-loop-closure live lower bound (26.2 → **26.3** cm, F7 caption). The other two (T condition C FGO live, confirmatory r5) are displayed in no table or caption |
| 4 | Rung-1 first-leg length | item 4: stays OPEN in the real-flight plan; not in the thesis results | removed from this thesis list. It appears only in `docs/rung1_flight_cards.md` (sortie step 3) and M:14169-14174; a grep finds it in no thesis results file, table, caption or PDF |
| 5 (Tier 2) | The UKF per-heading weight (claim 15) | item 6: DROPPED from all thesis-facing material | claim 15 removed from `headline_claims_before_after.md` (counts restated: CHANGED 15, 35 rows); `numbers.md` §15 row kept, marked NOT REPORTED (old row verbatim in the superseded block); `final_restatement_draft.md` §7 annotated. It was in no thesis table, figure or caption |
| 8 (Tier 2) | Which safety runs are "final" | item 5: the latest run of each test on the final build (UKF v3, FGO v4) | `numbers.md` §15 safety row restated with `H_safety_ukf_{a,b}_v3` and `H_safety_fgo_{a,b}_v4` (values from the four score files and M:13633-13635, M:13689-13692); the v2/v3 runs moved to the history row; both old rows kept verbatim. T7, A2 and A3 captions carry the sentence "The FGO safety re-tests (v4) used the NEW initial priors, while the flown FGO hold (S3v2) and corridor (v3) results used the OLD priors" |
| — | "half speed" in the F2, T4 and A1 captions | captions item | now "half real-time (RTF 0.5)" everywhere thesis-facing (captions, tables, both PDFs, the world index), with the one-line explanation "the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s" in the vocabulary (term 45) and the methodology draft |
| — | The 24 internal-code families in captions | captions item | removed from the figure and table captions, table notes and cells and both PDFs' caption text in the same pass; sources kept in `figures_thesis/index.md`. Residual hits: see the handover |
| — | `worlds_combined.pdf` citing the old figure numbers | (done earlier, commit `25e3b2b`) | regenerated again in this stage with the caption fixes |

## Still open (thesis-facing; each needs a ruling or an action)

| # | where | what | ruling needed: question and options |
|---|---|---|---|
| 6 | `T2_accuracy_heading.md` (Phase 5 column); `numbers.md` §6.3 ("NOT RESTATED") | Table T2 prints the Phase 5 heading-driven cross-track from the Phase 5 analysis file (FGO-only re-run). numbers.md says the §6.3 rows "must be recomputed before being cited" | Keep the column? (a) restate a numbers.md row from the file, then cite it; (b) keep the column with the "not cross-checked" note, as now; (c) remove the column |
| 7 | `T5_H_tag_loss_drift.md` (note 2); `figures_thesis/index.md` T5 "not cross-checkable" | Three of the six EKF3 flights in T5 (the far-spawn set) have drifts recorded only in METHODOLOGY, with no numbers.md row, so they are not cross-checked | (a) add a numbers.md row; (b) cite METHODOLOGY directly; (c) show the near-spawn set only (3 flights) |
| 9 | `numbers.md` "Rows elsewhere in this file affected by the corrections but NOT recomputed" | §1 cruise roll/pitch and camera-dataset RTF; §2 P2 latencies; §11 the ceiling effect size (+0.43 px/s), which a standing rule requires in any ceiling-vs-`dsn` transition comparison; §14 timing | For each: (a) recompute offline, if the freeze allows; (b) cite as pre-correction, labelled; (c) omit. **The ceiling effect size needs a decision** |
| 10 | `T7_failure_behaviour.md` (the ‡ marks, formerly ⚑) | S-A4 shows FAIL in two early score files (UKF (a) run 1, FGO (b) run 1). METHODOLOGY calls these not applicable or not scored (M:11490, M:11827): scorer artefacts | Show S-A4 as (a) "not applicable / not scored", following METHODOLOGY; or (b) "FAIL in the score file", with the footnote, as now |
| 11 | `numbers.md` §18; M:13300 | The questions the partial attribution study did not answer | **Already ruled "listed in the thesis"** (M:13300); now on `docs/thesis/limitations.md`, item 2. No ruling needed |

**Documentation, not a ruling (still open):** `numbers.md` §10 is headed "results still running" and says "No Phase 4
results exist". It is stale, because §6.6 has them.

**Out of the thesis list (real-flight plan only):** the rung-1 first-leg length (3 m if the capture volume allows the 2 m
clearance at both ends, otherwise ≥ 2 m), pending the supervisor's room size. If the "Towards real flights" chapter is
written before the answer, it states the rule and marks the length open.

## Excluded (PENDING markers in superseded or frozen blocks; not thesis-facing)

| location | text | why excluded |
|---|---|---|
| `numbers.md` "Superseded values" (receipt-stamp UKF/FGO rows) | "SUPERSEDED (pending restatement)" | superseded block; the restated values are in §6.2 |
| `numbers.md` "Former sections 6–9", §6.5 row | "Scale-cause check … PENDING; not yet defined in the record" | a verbatim superseded block ("kept verbatim, not edited"); check 5a is now DROPPED (above) |
| `numbers.md` "Superseded by the FGO-only re-run" | "trace pending", "attribution PENDING" | superseded; done or ruled |
| `numbers.md` header | "pending one consolidated re-run" | a header note about the superseded receipt-stamp values; the re-run was done |
| `numbers.md` "Superseded by the rulings of 2026-10-16" | the old §17.2 heading, flag 4 and flag 8 sentences | verbatim copies of the replaced text, by convention |
| `headline_claims_before_after.md` counts line | "PENDING 0"; "row 8 PENDING → WITHDRAWN, row 22 PENDING → CHANGED" | a count of zero, and a history of closed items |
| `methodology_definitions_draft.md`, "PENDING" section | the definition of the label | a definition, not an item |
| `docs/thesis/final_results_pack_index.md`, `final_results_pack.pdf` | PENDING (H comparatives), "half-speed" | the FROZEN pack (not regenerated; superseded for the thesis by `figures_thesis/`) |
| M:12833, M:14169-14174 | earlier counts; the rung-1 ruling | the record, not thesis text |
