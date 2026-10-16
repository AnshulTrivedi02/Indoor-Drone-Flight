# PENDING items that would appear in the thesis

*2026-10-16. Branch `fwd-camera` at `6a0fa0f`. A new file; nothing else was edited. "M" means `METHODOLOGY.md`, followed by
its line number.*

**Search:** "PENDING" and "pending" in all of the following:
- METHODOLOGY.md;
- `docs/thesis/*.md`, `docs/thesis/tables/*`, `docs/thesis/figures_thesis/index.md`, `docs/thesis/world_images/index.md`;
- the two thesis PDFs (`pdftotext`: no PENDING in either);
- `docs/rung1_flight_cards.md`.

The items are in three tiers, so that the count stays honest:
- **Tier 1:** literally marked PENDING, in thesis-facing material or in the record the thesis cites.
- **Tier 2:** marked OPEN or NOT RESTATED, or flagged, and thesis-facing. Not PENDING-marked, but each needs a ruling or an
  action before the text is final.
- **Excluded:** PENDING markers in superseded blocks, with the reason.

**Counts:** Tier 1 = **4 items** (14 locations); Tier 2 = **7 items**; excluded = 6 locations.

## Tier 1: literally PENDING

### 1. Experiment H comparative criteria on the re-flown sets (H5.2, H5.3, H5.4a/b = H-H2, P-H3, H-H4)

**Where it appears:**
- `docs/thesis/numbers.md:631` (§17.2 heading, "PENDING user ruling") and `:633-663`;
- `docs/thesis/tables/T1_scorecard.md:18` and `T1_scorecard.tex:25`;
- `docs/thesis/tables/T5_H_tag_loss_drift.md:14` and `T5_H_tag_loss_drift.tex:22`;
- `docs/thesis/figures_thesis/index.md:113` (T1 check row);
- `docs/thesis/final_results_pack_index.md:34`, `:175`, `:344`;
- M:13547-13550.

**What it is:**
- The three comparative criteria were adjudicated FAIL on the earlier sets (S2, the old UKF; S3, the FGO ablation build).
- They were recomputed on 2026-10-11 on the final-build sets S2v2/S3v2 by `eval/h_comparative.py`, from the stored scores.
- All verdicts are the same (FAIL). Two wordings change: the FGO hold is now the *highest*, not tied, and EKF3's 15 s jump
  is now *strictly* the smallest (numbers.md:654-661).
- The table T1 cell "TIED" for H and the T5 note both rest on this.

**Ruling needed:** Which set carries the Experiment 5 comparative verdicts in the thesis?
- (a) adopt the re-flown S2v2/S3v2 verdicts and wording;
- (b) keep the adjudicated earlier-set verdicts, with the re-flown ones as supplementary;
- (c) report both side by side.

*Under every option the verdicts are FAIL. Only the wording and the build cited change.*

### 2. Scale-cause check ("bounded check 5a")

**Where it appears:** `docs/thesis/numbers.md:710-711` and `:904` ("PENDING; not yet defined in the record"); M:3196-3197;
`docs/thesis/methodology_index.md:916`.

**What it is:**
- A check of *why* EKF3 over-scales distance. The thesis-facing distance-scale rows are numbers.md:276-284 and claim 12
  (`headline_claims_before_after.md:28`): EKF3 along-track 0.972–0.979.
- The check has never been defined.
- Simulation results are frozen (M:13396-13399). The rule there is "no new result experiments or re-runs"; whether an
  offline analysis counts is not stated.

**Ruling needed:** What happens to check 5a?
- (a) define it now and run it as an offline analysis, if the freeze allows;
- (b) drop it and state the cause of the EKF3 scale as not investigated (a limitation);
- (c) leave it OPEN in the thesis with its scope written down.

### 3. Rounding rule for four last-digit transcriptions

**Where it appears:** `docs/thesis/numbers.md:737-752` ("Proposed, PENDING user ruling (not adopted)").

**Affected values in the thesis-facing captions and checks:**
- T condition A FGO batch: 0.011 against 0.010 in the file;
- T condition C FGO live: 0.053 against 0.054;
- L no-LC live lower bound: 0.262 against 0.263;
- confirmatory d r5: −0.489 against −0.488 under half-even rounding.

These are in `figures_thesis/index.md:31`, `:56-58`, `:88`, `:107`, `:111`, `:231` and in `final_results_pack_index.md:35`.

**What it is:**
- Four numbers.md values are double-rounded from a 4-dp intermediate.
- The figures print the file value. The checker accepts each pair as a "last-digit match".
- No verdict, range or ordering changes (numbers.md:751).

**Ruling needed:** Which value is printed in the thesis?
- (a) adopt the single-rounding rule (half away from zero), print the file value, and restate the four numbers.md cells;
- (b) keep numbers.md verbatim and accept that the text and the figures differ in the last digit;
- (c) print these four at one more decimal place.

### 4. Rung-1 first-leg length

**Where it appears:**
- M:14169-14174 ("RULING (user, 2026-10-13): the rung-1 first-leg length (PENDING the supervisor's room size)");
- `docs/rung1_flight_cards.md:267` (sortie step 3).

**It appears in no thesis figure, table, caption or PDF.** It matters only for the unnumbered "Towards real flights"
chapter (`thesis_vocabulary.md` §1, decision 3).

**What it is:**
- The first leg is 3 m if the mocap volume allows the 2 m clearance at both ends, otherwise ≥ 2 m.
- The purpose is that the U10 G5 start-aligned drift can be computed.

**Ruling needed (supervisor input, not a user choice):** What is the capture-volume size? With it:
- (a) a 3 m first leg; or
- (b) ≥ 2 m (state the actual length).

If the real-flight chapter is written before the answer, it should state the rule and mark the length PENDING.

## Tier 2: OPEN, NOT RESTATED or flagged, and thesis-facing

| # | where | what | ruling needed: question and options |
|---|---|---|---|
| 5 | `numbers.md:479` (status "UKF OPEN"); claim 15, `headline_claims_before_after.md:31` | Closed-loop per-heading weight. FGO ≈ 1.3–1.4 % on the final-build flights; the UKF side is OPEN, so no FGO/UKF ratio is stated | State the UKF weight? (a) compute it from the stored UKF final-build closed-loop logs (offline, if the freeze allows); (b) report the FGO value only and keep the UKF OPEN; (c) drop claim 15 from the thesis |
| 6 | `T2_accuracy_heading.md:5, 15` (Phase 5 column, "JSON-only … §6.3 'NOT RESTATED'"); `numbers.md:262`; `figures_thesis/index.md:122` | Table 4.1 (T2) prints the Phase 5 heading-driven cross-track (from `phase5_analysis.json`, FGO-only re-run). numbers.md says the §6.3 rows "must be recomputed before being cited" | Keep the column? (a) restate a numbers.md row from the JSON, then cite it; (b) keep the column, with the JSON-only caveat as now; (c) remove the column |
| 7 | `T5_H_tag_loss_drift.md:16`; `figures_thesis/index.md:175` | Three of the six EKF3 flights in Table 6.1 (T5), the S1-far set, have drifts recorded only in METHODOLOGY, with no numbers.md row, so they are not cross-checked | (a) add a numbers.md row; (b) cite METHODOLOGY directly; (c) show S1 near-spawn only (3 flights) |
| 8 | `T7_failure_behaviour.md:11`; `A2_H_and_safety_p2.png` note; `numbers.md:482` | Final safety runs. T7 and A2 cite the UKF v3 and FGO v4 re-tests (METHODOLOGY only), while numbers.md §15 lists v2/v3 as final | Which runs are "final" in the thesis? (a) restate numbers.md §15 with v3 (UKF) and v4 (FGO); (b) present v2/v3 as final and v3/v4 as supplementary re-tests; (c) both, labelled |
| 9 | `numbers.md:344-352` | Rows affected by the corrections but not recomputed: §1 cruise roll/pitch and camera-dataset RTF; §2 P2 latencies; §11 the ceiling effect size (+0.43 px/s), which CLAUDE.md:126-128 requires in any ceiling-vs-`dsn` transition comparison; §14 timing | For each: (a) recompute offline, if the freeze allows; (b) cite as pre-correction, labelled; (c) omit. **The ceiling effect size needs a decision**, because a standing rule requires it |
| 10 | `T7_failure_behaviour.md:8-9, 13` (⚑) | S-A4 shows FAIL in two early score files (UKF (a) run 1, FGO (b) run 1). METHODOLOGY calls these not applicable or not scored (M:11490, M:11827), so they are scorer artefacts | Show S-A4 as (a) "not applicable / not scored", following METHODOLOGY; or (b) "FAIL in the score file", with the footnote, as now |
| 11 | `numbers.md:677`; M:13300 | Questions the partial attribution study did not answer: the `dsn_tex_r6` flip, the main corridor changes, the textured-wall UKF heading gain, the textured-wall FGO baseline. Status OPEN (stopped by ruling) | **Already ruled "listed in the thesis"** (M:13300). No ruling is needed; recorded here so that the list is not forgotten |

**Not PENDING, but needs fixing before the captions are final** (documentation, not a ruling):
- "half speed" in the F2, T4 and A1 captions should read "half real-time factor (RTF 0.5)" (`thesis_vocabulary.md` term 45).
- `worlds_combined.pdf` and `world_images/index.md` still cite the old figure numbers F1/F3/F4/F8 (glossary_flags.md:45).
- `numbers.md:354-357` §10 is headed "results still running" and says "No Phase 4 results exist". This is stale, because
  §6.6 has them.

## Excluded (PENDING markers in superseded blocks; not thesis-facing)

| location | text | why excluded |
|---|---|---|
| `numbers.md:772-779` | "SUPERSEDED (pending restatement)" (receipt-stamp UKF/FGO rows) | in "Superseded values (do not cite as current)" (numbers.md:756). The restated values are in §6.2 |
| `numbers.md:1139-1143` | "trace pending" | in "Superseded by the FGO-only re-run". The trace was done (numbers.md:295, 673) |
| `numbers.md:1159`, `:1163` | "attribution PENDING" | superseded. The partial attribution was ruled (numbers.md:556, 674) |
| `numbers.md:22` | "pending one consolidated re-run" | a header note about the superseded receipt-stamp values. The re-run was done |
| `headline_claims_before_after.md:53, 55` | "PENDING 0"; "row 8 PENDING → WITHDRAWN, row 22 PENDING → CHANGED" | a count of zero, and a history of closed items |
| M:12833 | "PENDING 2" in an earlier count of the claims table | superseded by the current count (PENDING 0) |
