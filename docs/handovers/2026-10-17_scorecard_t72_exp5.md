# Handover 2026-10-17: scorecard labels, the Table 7.2 bound, Experiment 5 verbatim wording (+ F9 caption)

One stage. It applies the user rulings of 2026-10-17 (METHODOLOGY.md "RULINGS (user, 2026-10-17)", l.14254ff in this
worktree) to `eval/figs_thesis.py` and `eval/figs_thesis_results.py`. Both generators were regenerated and their outputs
committed. Nothing was simulated, flown or re-run.

These files were not touched: `numbers.md`, `METHODOLOGY.md`, `eval/figs_thesis_methods.py`, `eval/figs_final_pack.py`,
and the final results pack and its index and corrections. No figure or table was renumbered. "Figure 4.1b (provisional)"
is kept as it was.

## VERDICT CHANGE (read first)

**Table 7.3 (R1) has one new scored part: H5.6, the jump criterion, "kept as worded". Its verdict is FAIL AS WORDED.**

- **Why it appears.** The S2/S3 pre-registration (M:10946, "before any S2/S3 flight") redefined only the re-lock time. It
  kept the jump criterion verbatim:

  > "Jump criterion: kept as worded (the largest single estimate step in the 2 s after re-lock ≤ the accumulated drift at
  > re-lock; UKF/FGO converge without reset)." (M:10957-10958)

  - The previous R1 row "H5.6 redefined primary: PASS" scored only the re-lock time.
- **Outcome.** The outcome was already recorded in numbers.md, and no new analysis was done:
  - final UKF port: "jump criterion AS WORDED fails in most losses (steps 5–30 mm against drifts 2–26 mm)" (numbers.md:644);
  - final FGO node: "jump AS WORDED fails in 4 of 12 losses" (numbers.md:646).
- **Effect on R1:**
  - 46 → 47 scored parts;
  - FAIL AS WORDED 3 → 4;
  - the other counts are unchanged (PASS 24, NOT MET 16, WITHDRAWN 1, DESCRIPTIVE 2).
- **Ruling needed:** keep this part, or drop it and record the jump criterion only in a note.

No other verdict changes. Every Experiment 5 verdict is the same under the verbatim wording (item 3 below), and so is
the UKF safety verdict (item 2).

## Item 1: scorecard labels (Table 7.1 = T1 in `figs_thesis.py`; Table 7.3 = R1 in `figs_thesis_results.py`)

**Rule applied.** An ordering label is printed only where a pre-registered decision rule was met. TIED is treated as an
ordering label because it claims equality.

**Result.** No T1 comparison met such a rule, so all 17 BEST / BEHIND / TIED labels are gone. The status words stay,
because they are not orderings:
- FAILED: does not bound position;
- PASSED: met its own pre-registered criteria;
- N/A: not run.

**Edits made in T1:**
- the caption;
- the "Categories" note and the "TIED where … BEHIND: …" note, now one note giving the reason per row;
- the footnote preface ("categories above are unchanged" is gone);
- the index.md scorecard paragraph;
- `CAT` (only the status words remain).

**Cell verdict strings reworded:**
- Experiment 4, EKF3: "H4.2 FAIL; 4.10 m jump" → "no live ordering claimed; 4.10 m jump". The old wording, in bold,
  read like the old BEHIND label.
- Experiment 4, UKF: "UKF ≈ FGO live" → "no live ordering claimed". It was an unregistered similarity claim.
- Experiment 4, FGO: "batch 0.59 = smoothed UKF" → "batch 0.59, within 1.5× of the smoothed UKF: H4.3 PASS".
- Experiment 1B, both cells: "C1.a descriptive" added.

| row | cell(s) | before | after | justification (pre-registration line) |
|---|---|---|---|---|
| 1A standard sensors | EKF3, FGO | TIED | no label | H1.1: test run, rule not met. M:5649-5654: "Otherwise: no ordering is claimed"; outcome numbers.md:227 |
| 1A | UKF | TIED | no label | no test registered: M:7187, "descriptive; no pre-registered UKF ordering test" |
| 1B camera heading | UKF | BEHIND | no label | C1.a has no decision rule: M:7892, "REPORT, no decision rule" |
| 1B | FGO | BEST | no label | same (M:7892) |
| 1B | EKF3 | N/A | N/A (kept) | not run; not an ordering |
| blank floor | all three | FAILED | FAILED (kept) | an absolute status, not an ordering. No rule backs it: the blank floor is ruled "Not accuracy comparisons" (M:5551). **Flagged** |
| Experiment 2 live | all three | TIED | no label | H2.3 FAILS (M:10178-10179; numbers.md:536); no ordering test registered; condition D descriptive (M:12803) |
| Experiment 4 live | EKF3 | BEHIND | no label | H4.2 FAILS (M:10360-10361); no ordering test registered |
| Experiment 4 | UKF, FGO | TIED | no label | as above. H4.3 PASSES (M:10362), but it compares the hindsight tracks, not the live key number |
| Experiment 3 | EKF3, UKF | N/A | N/A (kept) | not run |
| Experiment 3 | FGO | PASSED | PASSED (kept) | H3.1–H3.4 met (M:10501-10505); one estimator, not an ordering |
| Experiment 5 | all three | TIED | no label | H5.2 / H5.3 / H5.4a–b FAIL (tag_hold_design.md:180-187; M:12236, M:13549) |
| 1C closed loop | all three | TIED | no label | no comparative test: M:9355, "DESCRIPTIVE; separate flights, n = 3 each, no ordering claim" |

**R1 (Table 7.3) has no ordering labels.** Its five categories (PASS, FAIL AS WORDED, NOT MET, WITHDRAWN, DESCRIPTIVE) are
verdicts. C1.a's "FGO lower on all 6" is quoted from numbers.md:299 and is categorised DESCRIPTIVE. There is no appendix
in `figs_thesis_results.py`.

**Rule met but no label added.** H4.1 is met (M:10358-10359: FGO batch below both filters' live tracks, 3/3), and it is
an ordering. But it compares a hindsight track with live tracks, and it is not a T1 key number, so it is only mentioned
in the T1 note.

## Item 2: the UKF bound in Table 7.2 (T7) and Table A.2 (A2)

**The pre-registration, verified.** METHODOLOGY.md:11299 reads `    - UKF (a): within **0.1 s** of TFAIL;`. Line 11298
is the FGO's 0.75 s and line 11300 is UKF (b)'s 5.5 s.

**What the tables showed before:**
- **A2:** each score file's `bound_s`. The final UKF port's forced-invalid files (`safety_ukf_a_v2`, `_v3`) record 0.75,
  because they were scored with the FGO bound on instruction (M:14263-14264). So both rows showed "0.00 s (bound 0.75)".
- **T7:** the bound appears only in the notes. They gave "(0.75 s; UKF node-kill test 5.5 s)" and "0.75 s in the later
  runs, shown as recorded".

**What they show now:**
- A new `A2PRE` table sets the S-A2 bound exactly as pre-registered: FGO 0.75, UKF (a) 0.1, UKF (b) 5.5.
- It is used by the A2 rows (`srow`) and by T7 (`sfail`).
- **A2:** the UKF forced-invalid final-port rows now show "0.00 s (bound 0.10)". A new note on page 2 quotes all three
  registered bounds with their lines and explains the 0.75 in the score files.
- **T7 notes:** the three bounds are quoted with their lines (11298, 11299, 11300). The UKF forced-invalid note quotes
  'UKF (a): within 0.1 s of TFAIL' (METHODOLOGY.md:11299).

**Verdict confirmed unchanged.** Both final-port delays are 0.00 s, which is ≤ 0.1, and the score files say PASS. This
is checked at build time.

**New checks:**
- the score-file bound differs from the registered bound only for `safety_ukf_a_v2` and `_v3`;
- delay ≤ 0.1 and the verdict is PASS for both;
- three cited-line checks.

**Score files are unchanged.**

**Disclosure:** numbers.md §15 (l.490-491) still says "bound 0.75 s" for UKF (a), in the frozen content. The tables now
differ from numbers.md on this one displayed bound, as the ruling intends. An erratum may be wanted; I did not add one.

## Item 3: the Experiment 5 hypotheses, verbatim

**Where each wording comes from:**
- **H5.1, H5.5, H5.6 (as pre-registered), H5.7:** the S0/S1 pre-registration, M:10623 ("written before any H flight"),
  l.10687-10700.
- **The H5.6 redefinition and its kept jump criterion:** the S2/S3 pre-registration, M:10946 ("before any S2/S3 flight"),
  l.10948-10958.
- **H5.2–H5.4b:** only `docs/tag_hold_design.md` §e (l.180, 183, 185-187), headed "Hypotheses (draft)". Their §e text
  (l.176-188) is identical at commit `c11fcf3` (2026-10-08 15:17) and now. This is checked at build time with
  `git show`. That commit predates the first H flight: `H_s1_r1` is dated 2026-10-08 21:50 and `H_s2_r1` 2026-10-09 02:28.

**Edits made:**
- **R1 (Table 7.3):** every H5 prediction is now the full verbatim text:
  - H5.5 and H5.6 had ellipses. H5.6 had dropped the clause "After the 15 s and 30 s losses (posTimeout), the first fix
    resets position … within 0.02 m of it".
  - The H5.6 redefinition now includes its band (≤ 0.1 s) and the definition text.
  - H5.2's annotation "(design draft …)" was inside the quotation marks and is now outside.
  - Final full stops were restored.
  - A new strict check, `vfound`, confirms each H5 quote occurs unbroken in the cited lines (bullets and markdown
    removed).
  - The note now gives the sources, the two-wording issue and the directional prediction.
- **figs_thesis.py:**
  - **Footnote [i] (`ob_h5`, used by T1, T5 and A2):** the four comparative hypotheses are now quoted verbatim (`vquote`
    checks). They were partial before.
  - **A2 page 3:** the "pre-registered wording" column (`HCW`) was a paraphrase. It is now the verbatim text with its
    line.
  - **A2 page 1:** a new note quotes H5.1, H5.5 and H5.7 verbatim, plus the design-draft wordings of H5.1 and H5.5.

**Verdicts against the verbatim wording:**
- H5.1, H5.2, H5.3, H5.4a, H5.4b, H5.5 and H5.7 are unchanged.
- H5.6 as pre-registered is unchanged (FAIL AS WORDED). Under the full wording, EKF3's 15/30 s jumps match the prediction
  (M:10841-10842), but the re-lock time still fails.
- H5.6 redefined is unchanged (PASS) for the re-lock time. The new jump-criterion part fails as worded (see the top of
  this handover).

**Ambiguities, flagged rather than chosen silently:**
1. **Two wordings of H5.1.**
   - The design draft (tag_hold_design.md:176-177) says "every estimator … in 3/3 flights per estimator".
   - The METHODOLOGY pre-registration (M:10687-10688) says "EKF3 flying … in every pre-loss hold window".
   - Both predate the runs. METHODOLOGY's is scored, as before.
   - Under the draft wording it also PASSES: every hold window of every flying set has mean ≤ 50 mm and max ≤ 150 mm
     (checked).
2. **Two wordings of H5.5.**
   - The draft (l.188) says "GT drift during the 15 s occlusion ≤ 0.3 m for every estimator".
   - METHODOLOGY (M:10689-10692) gives per-estimator bands, and the S2/S3 table (M:10962-10969) gives the same bands for
     the flying UKF and FGO.
   - METHODOLOGY's is scored. M:12243 itself scored the draft wording (PASS). Both PASS.
3. **H5.2–H5.4b exist only in a document headed "draft".** No METHODOLOGY line pre-registers them. They are quoted from
   it with its line numbers, as before.
4. **The S2/S3 directional prediction is not scored.** It reads "both flying estimators drift more than flying EKF3 did
   (3–31 mm)" (M:10971).
   - It was judged "NOT borne out" only on the superseded builds (M:12244-12245).
   - Judging it on the final builds needs a comparison that has not been made.
   - It is named in the R1 note only.
5. The S2/S3 FGO yaw-wander criterion (≤ 3°, M:10970; PASS, numbers.md:646) has no H label and is not in the
   scorecard. That is unchanged.

## Extra item (coordinator, 2026-10-17): the F9 caption ("Figure 4.1b (provisional)")

- The caption now reads: "EKF3 +242.1 s (after its pre-registered window [+155, +215] s; numbers.md:470)".
- New checks:
  - an exact check of `"+242.1 (MISS), window [+155, +215]"`, computed from the stored contact time and `WIN`;
  - two cited-line checks that numbers.md:470 contains "window [+155, +215]" and "+242.1 (MISS, D21)".
- No number changed. The figure image is unchanged; the caption appears in index.md and the combined PDF.

## Cross-check totals

| generator | before (HEAD d5da93a) | after |
|---|---|---|
| figs_thesis.py | 307 / 307 | **326 / 326** |
| figs_thesis_results.py, numeric | 60 / 60 | **60 / 60** |
| figs_thesis_results.py, source (quote) checks | 157 / 157 | **177 / 177** |

**Where the figs_thesis.py checks were added:**
- F9: 20 → 23;
- T7: 18 → 21;
- A2: 34 → 47;
- the other tables and figures are unchanged (T1 66, T5 20).

`tools/check_numbers_frozen.py`: PASS.

## Numeric diff against HEAD (every regenerated .md/.tex and both indexes)

Only these displayed values changed:
- **Table A.2 page 2 (PNG/PDF only; A2 writes no .md/.tex):** `H_safety_ukf_a_v2` and `H_safety_ukf_a_v3`, "0.00 s
  (bound 0.75)" → "0.00 s (bound 0.10)". This is intended (item 2). All other A2 rows are unchanged; checked by
  recomputing both forms for all 16 safety files.
- **Table 7.3 (R1):**
  - one new row (H5.6 jump criterion), whose values are quoted from numbers.md:644 and 646;
  - the caption counts 46 → 47 parts;
  - the FAIL AS WORDED count 3 → 4.

**Everything else is not a data value:**
- quoted pre-registration numbers (bounds, bands, windows, line numbers, dates);
- check counts in the indexes;
- the T1 notes;
- T1 data cells: unchanged values, labels removed;
- T2–T6, T8, R2 and R4: no numeric change; only the commit hash in their generated comment changed.

**Layout:**
- the A2 page-2 font is 7.0 → 6.8 pt, so the new bound note fits without an overflow page (A2 stays 3 pages);
- R1 is now 8 PNG pages (new `R1_hypothesis_scorecard_p8.png`).

## Open items needing a user ruling

1. Keep or drop the new R1 part "H5.6 jump criterion, kept as worded: FAIL AS WORDED" (see the top of this handover).
2. Keep "FAILED" on the T1 blank-floor row? It is a status, not an ordering, but no pre-registered rule backs it (M:5551).
3. The T1 title "Which estimator wins where (scorecard of the restated verdicts)" now contradicts a table with no
   ordering labels. I did not retitle it. A suggested title: "Scorecard of the restated verdicts by experiment and
   estimator".
4. numbers.md §15 (l.490-491) says "bound 0.75 s" for UKF (a), while the tables now show the registered 0.1 s. Add a dated
   erratum?
5. Which wording of H5.1 and H5.5 to score: METHODOLOGY's (current) or the design draft's. Both PASS.
6. The S2/S3 directional prediction is not scored on the final builds.
