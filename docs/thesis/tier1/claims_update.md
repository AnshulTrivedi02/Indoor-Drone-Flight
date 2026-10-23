# Claims update after the extension experiments E2–E5: PROPOSAL ONLY

**This is a proposal. Nothing has been changed.** No thesis document, table, figure generator, the claims table
(`docs/thesis/headline_claims_before_after.md`), `numbers.md` or the frozen results pack was edited. Each "where else"
list below names the places that would need to change if the user accepts a proposal. Those places were not touched.

- **Instruction:** `METHODOLOGY.md`, "INSTRUCTION (user, 2026-10-22): claims update after the extension experiments"
  (commit `3901b58`).
- **Every result cited here comes from extension experiments, pre-registered (2026-10-21; signed off with amendments
  2026-10-22).** The registration is `preregistration.md`. The results are `e2_results.md`, `e3_results.md`,
  `e4_results.md`, `e5_results.md` and `scores/*_verdicts.json`.
- **Names.** The tier-1 ids E2–E5 are extension experiments. They are not the thesis's Experiments 2–5. In thesis
  numbering (`docs/thesis/thesis_vocabulary.md:72-73`), Experiment 2 is known tags (repo "T") and Experiment 3 is loop
  closure (repo "L").
  - E2: loop closure with fewer tags.
  - E3: wrong re-identification.
  - E4: the live window sweep of the Experiment 2 FGO.
  - E5: a UKF with tag landmark states.
- **Rules applied** (`decisions_log.md`, rules 1–8):
  - No proposed wording is stronger than its verdict (rule 8). Verdicts are quoted as scored, with counts.
  - DESCRIPTIVE marks a result with no verdict. The E3 map-collapse diagnosis is descriptive, and its mechanism is
    stated as "consistent with", not proven.
  - Units: m for position error, ms for compute, s for timeline (`docs/thesis/units.md`).
- **Check:** `check_claims_update.py` verifies three things: every verbatim old-wording quote against its file and
  line, every number typed here against its source, and that no number in this file is unregistered. Its totals are in
  the handover.

## Summary

| id | claim | old → new (in brief) | status of the old wording | supporting verdicts |
|---|---|---|---|---|
| C1 | Loop closure is an FGO capability | "the filters have no loop-closure equivalent" / "Only the FGO can do this" → the thesis's EKF3 and UKF as configured have none; a UKF with tag landmark states does bound drift | **too strong** in its short forms; the hedged METHODOLOGY form ("without a different design") holds, and E5 is that design | E5: H-E5.1 PASS 3/3; H-E5.2 PASS 3/3; H-E5.3 PASS 3/3; P-E5.4 PASS 3/3; S-E5.5 PASS 3/3 and S-E5.6 PASS 3/3 (registered direction: UKF higher than the FGO; S-E5.6 against the FGO's iSAM2 hindsight, not an LM batch) |
| C2 | The loop-closure result rests on correct tag ids | "Tag ids make re-identification trivial" → the plain FGO's loop-closure advantage does not survive 1% wrong ids; a robust variant does not diverge and is no worse than the plain FGO | **incomplete**: the dependence on correct ids is not stated | E3 arm (a): H-E3.1 FAIL 0/9 (6 of 9 runs diverged); H-E3.2 FAIL 0/9; H-E3.3 FAIL 3/9; P-E3.4 FAIL 0/9; P-E3.5a FAIL 0/9; P-E3.5b FAIL 0/9; P-E3.5c PASS 9/9; P-E3.6 FAIL 0/3. Arm (b): P-E3b.1 PASS 9/9 at 1% and 9/9 at 5%; P-E3b.2 PASS 3/3 |
| C3 | Loop closure bounds live drift (8 tags) | 8 tags only → also 4 and 2 tags; D (1 tag) is the known-map case | **too narrow** (holds as worded) | E2: H-E2.1 PASS 3/3 in each of B, C, D (9/9); H-E2.2, H-E2.3, P-E2.4 PASS 3/3 in each; P-E2.5 FAIL (A ≤ B false) |
| C4 | The 0.25 s window choice | "largest window meeting" the 33 ms budget, "ONLY" at 0.25 s; "larger windows spend compute for no accuracy gain" → budget part scoped to the corridor; accuracy part restated as a pre-registered null result on the room world | budget part **too strong / not general**; accuracy part **without current support** until E4 | E4: P-E4.1 PASS 12/12; P-E4.2 PASS (12/12 at each window); H-E4.3 FAIL 7/12 (null result) |
| C5 | The 2-iteration LM cap is converged | verified at 0.25 s on one corridor bag → also at every window 0.25–5 s on two room flights | **too narrow** (holds as worded) | E4 convergence check (a qualifier, not a hypothesis): no flag at any window, 10/10 cap-10 runs |

## C1. Loop closure is an FGO capability; the filters have no loop-closure equivalent (revised by E5)

**Old wording (verbatim).**
- The canonical pre-registration, which is hedged:

> "This is an **FGO capability**, not an FGO-vs-filter result. The filters have no loop-closure equivalent without a different design (e.g. EKF-SLAM with the tags in the state)." — `METHODOLOGY.md:10456-10457`

- The thesis-facing short forms, which dropped the hedge:

> "N/A: FGO capability only (the filters have no loop closure)" — `docs/thesis/tables/T1_scorecard.md:12`
> "N/A: no loop-closure equivalent (FGO capability only)" — `docs/thesis/tables/T1_scorecard.md:12`
> "This is an FGO capability, not an FGO-against-filter result (the filters have no loop-closure equivalent)" — `docs/thesis/figures_thesis/index.md:213`
> "Only the FGO can do this, so there is no comparison between estimators." — `docs/thesis/summary/index_summary.md:174`

**Status.** The short forms are **too strong**. They say that a filter cannot close loops at all. The METHODOLOGY form
holds as worded: it says a different design is needed. E5 built that design, a UKF with the tags in its state, and it
closed loops.

**Proposed new wording.**
> Loop closure over tags at unknown positions is not specific to the FGO. The thesis's EKF3 and UKF, as configured,
> have no landmark states, so they have no loop closure. In an extension experiment (pre-registered), a UKF variant with
> each tag in its state, re-identification and an RTS smoother bounded its live drift on 3/3 flights (H-E5.1 PASS 3/3;
> live lap 5 ÷ lap 1 0.27 / 0.42 / 0.30). Re-identification lowered its live and its smoothed error on 3/3 flights
> (H-E5.2 PASS 3/3, H-E5.3 PASS 3/3). On the same flights its error was higher than the keyframe FGO's, in the
> registered direction (S-E5.5 PASS 3/3 live; S-E5.6 PASS 3/3 hindsight, against the FGO's iSAM2 hindsight, not an
> LM batch; UKF ÷ FGO live 1.76–2.08, descriptive).

**Supporting results** (`e5_results.md` §1–§2; `scores/e5_verdicts.json:criteria`):

| id | criterion | values (T_A_r1 / r2 / r3) | verdict |
|---|---|---|---|
| H-E5.1 (PRIMARY) | UKF-LC live lap-5 ≤ 1.5 × lap-1 | ratio 0.27 / 0.42 / 0.30 | PASS 3/3 |
| H-E5.2 | UKF-LC live overall < UKF-no-LC live overall | 0.1193 < 0.8738; 0.0911 < 1.4112; 0.1335 < 0.9262 m | PASS 3/3 |
| H-E5.3 | UKF-LC RTS overall < UKF-no-LC RTS overall | 0.0445 < 0.9162; 0.0461 < 1.3349; 0.0552 < 1.0446 m | PASS 3/3 |
| P-E5.4 | UKF-no-LC live lap-5 > 1.5 × lap-1 | ratio 6.87 / 14.62 / 6.34 | PASS 3/3 |
| S-E5.5 (secondary) | UKF-LC live > stored FGO-LC live | 0.1193 > 0.0574; 0.0911 > 0.0494; 0.1335 > 0.0760 m | PASS 3/3 (direction held) |
| S-E5.6 (secondary) | UKF-LC RTS > stored FGO-LC hindsight | 0.0445 > 0.0198; 0.0461 > 0.0270; 0.0552 > 0.0172 m | PASS 3/3 (direction held) |

- **Validation.** All 36 validation gates passed (V-E5a, V-E5b and V-E5c, 12/12 each). V-E5a reproduces the stored
  Experiment 2 UKF byte for byte.
- **Ratios (DESCRIPTIVE).** UKF ÷ FGO is 2.08 / 1.84 / 1.76 (LC live) and 2.25 / 1.71 / 3.21 (LC hindsight).

**Caveats.**
- The UKF variant is an extension estimator. It is not the thesis UKF and not EKF3. EKF3 with landmark states was not
  tested, so the new wording names the variant and does not say "the filters".
- n = 3 flights, all with condition A (8 tags).
- S-E5.6's FGO side is the Experiment 3 hindsight, iSAM2's full-graph estimate after 5 extra updates, not an LM batch
  (`e5_results.md` §2.3).
- The UKF ÷ FGO magnitudes are descriptive. Only the direction was registered.

**Where else the wording would need to change (NOT edited):**
- Generated tables and figures:
  - `docs/thesis/tables/T1_scorecard.md:12` (the EKF3 and UKF cells of the Experiment 3 row), `:16` ("Experiment 3, FGO
    only"), `:18` ("Experiment 3, one estimator [h]") and `:38` (footnote [h]). Their generator is
    `eval/figs_thesis.py:767` and `:775`.
  - `docs/thesis/figures_thesis/index.md:213` (the F7 caption). Its generator is `eval/figs_thesis.py:1377-1378`.
- Summary pages:
  - `docs/thesis/summary/index_summary.md:174`, generated by `eval/figs_thesis_summary.py:646`.
  - `docs/thesis/summary/index_walkthrough.md:406` and `:424` (the VERBATIM checks of that sentence).
- Other thesis documents:
  - `docs/thesis/tables/R4_information_vs_estimator.md:20` ("Experiment 3 (loop closure) has one estimator").
  - `docs/thesis/methodology_factsheets/3.5_experiments.md:86`.
  - `METHODOLOGY.md:10456-10457` would need only a forward pointer to E5; its hedge already holds.
- **Frozen (erratum route only):**
  - `docs/thesis/final_results_pack_index.md:316` and its generator `eval/figs_final_pack.py:661` ("An FGO capability,
    not an FGO-against-filter result").
  - The claims table, row 23 (`headline_claims_before_after.md:38`).

## C2. The loop-closure result rests on correct tag ids (bounded by E3)

**Old wording (verbatim).**
> "Tag ids make re-identification trivial, so this tests whether the estimator *uses* loop closures, not place recognition." — `METHODOLOGY.md:10458-10459`

**Status.** This is **incomplete**, though not wrong. With correct ids, re-identification is trivial. Neither this text
nor the Experiment 3 claim (claims row 23) says that the result depends on those ids being correct. E3 shows that it
does for the FGO as built.

**Proposed new wording.**
> (a) Experiment 3's loop-closure result assumes correct re-identification. In an extension experiment
> (pre-registered), wrong ids were injected into 1% of the eligible detections (effective overall rate 0.71%). The
> keyframe FGO as built, with no robust weighting on tag factors, then lost its loop-closure advantage: its live error
> with loop closure was below the stored no-loop-closure live error on 0/9 runs (H-E3.1 FAIL 0/9), and 6 of 9 runs
> diverged. At 5% (effective overall rate 3.58%), 0 of 9 runs diverged, but none beat no loop closure either (P-E3.5a
> FAIL 0/9).
>
> (b) A variant with Cauchy-robust tag factors (k = 2.385) diverged on 0 of 21 runs. It was no worse than the plain
> FGO (P-E3b.1 PASS 9/9 at 1% and 9/9 at 5%; 6 of the 1% runs are counted as satisfied, flagged, because the plain run
> diverged), and it cost nothing measurable on clean data (P-E3b.2 PASS 3/3). No registered criterion compares the
> robust variant with no loop closure. Descriptively, its hindsight recovered on 17 of 18 mislabelled runs, while its
> live track paid for the wrong ids in the early laps.

**Supporting results** (`e3_results.md` §1–§4; `scores/E3_verdicts.json:criteria_a`, `criteria_b`):

| id | criterion | verdict | count | diverged runs |
|---|---|---|---|---|
| H-E3.1 (PRIMARY) | 1%: LC live < the same flight's stored no-LC live | FAIL | 0/9 | 6 of 9 |
| H-E3.2 | 1%: LC hindsight < stored no-LC hindsight | FAIL | 0/9 | 6 of 9 |
| H-E3.3 | 1%: LC live lap-5 ≤ 1.5 × lap-1 | FAIL | 3/9 | 6 of 9 (the 3 runs that did not diverge pass) |
| P-E3.4 | 1%: LC live ≤ 2 × clean LC live (×2: judgement, not derived from data) | FAIL | 0/9 | 6 of 9 |
| P-E3.5a / b / c | 5%: the H-E3.1 / H-E3.2 / H-E3.3 criteria | FAIL / FAIL / PASS | 0/9 / 0/9 / 9/9 | 0 of 9 |
| P-E3.6 | dose–response per flight | FAIL | 0/3 | — |
| P-E3b.1 | robust LC live ≤ 1.10 × arm (a), per run (+10%: judgement, not derived from data) | PASS | 9/9 (1%), 9/9 (5%) | 0 of 21 robust runs |
| P-E3b.2 | rate 0: robust LC live within ±10% of clean LC live (±10%: judgement, not derived from data) | PASS | 3/3 | — |

- **Arm (a), runs that did not diverge.** LC live 3.7161–4.2231 m against the stored no-LC live 0.3494 / 0.2625 /
  0.3608 m and the clean LC live 0.0574 / 0.0494 / 0.0760 m. That is 51.26–85.49× clean and 10.77–16.09× no-LC.
- **Arm (a), runs that diverged.** Live divergence onsets 49.699–61.795 s, each after a wrong-id event (§1).
- **Arm (b) (DESCRIPTIVE).**
  - Hindsight: 0.0114–0.0179 m at 1% and 0.0763–0.1072 m at 5%.
  - Live: the error in the early laps reaches 3.6419 m (lap 1), and some runs end above the no-LC live, for example
    T_A_r2 1% s0 at 1.4769 m against 0.2625 m.
  - One robust run collapsed: T_A_r2 5% s1, with live 4.1849 m and hindsight 4.2233 m.
- **Mechanism (§7; DESCRIPTIVE, `consistent with`, not proven).** The collapse of the plain FGO's map is consistent
  with a non-robust least-squares compromise, not a harness bug.
  - On T_A_r1 1% s0, the tag cost plus the approximate flow cost at the estimate is 8,622 + 6,266, against 144,218 at
    the true layout.
  - The landmark spread is 1.224 m, against a true 3.674 m.
  - IMU and range costs were not evaluated, so neither a global optimum nor a solver effect is shown.
  - The failed pre-registered assumption is that correct tag factors act as an anchor (§7.6).

**Caveats.**
- Condition A only, n = 3 flights, 3 seeds each.
- The injected rates are an error model, not a measured detector error rate.
- The divergence classification of four of the six runs was by triage, not counterfactual-tested (decision D4).
- **Decision D16.** The wording does not say "the robust arm keeps the loop-closure advantage". That would exceed the
  verdicts (see D16 and open point 1).

**Where else the wording would need to change (NOT edited):**
- `METHODOLOGY.md:10458-10459`: add the dependence on correct ids.
- `docs/thesis/figures_thesis/index.md:25`, `:211` and `:213`, with the generator at `eval/figs_thesis.py:1371-1378`.
  The F7 title "Re-identifying tags at unknown positions keeps the FGO's error flat" would need "with correct ids" or a
  caption sentence.
- `docs/thesis/summary/index_summary.md:175-176`.
- `docs/thesis/tables/R1_hypothesis_scorecard.md:37-40` (H3.1–H3.4: a scope note only, the verdicts are unchanged).
- `docs/thesis/methodology_factsheets/3.5_experiments.md:87`.
- `docs/thesis/limitations.md`. That file lists only ruled items, so a new limitation row needs a user ruling (open
  point 2).
- Frozen: claims row 23 (`headline_claims_before_after.md:38`) and `numbers.md` §16.3. Erratum route only.

## C3. Loop closure bounds live drift: scope widened from 8 tags to 4 and 2 tags (E2)

**Old wording (verbatim).**
> "**L:** loop closure keeps live error bounded; H-L1, H-L2, H-L3, P-L4 PASS 3/3" — `docs/thesis/headline_claims_before_after.md:38`
> "Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps" — `docs/thesis/figures_thesis/index.md:211`

**Status.** **Too narrow; it holds as worded.** The claim was tested with all 8 tags (condition A). E2 supports it with 4
tags (B) and 2 tags (C). Condition D (tag 0 only) is the known-map one-tag case and carries no claim about unknown
landmarks (`preregistration.md` §1).

**Proposed new wording.**
> With tags at unknown positions, the keyframe FGO's loop closure bounded its live drift with all 8 tags (Experiment 3,
> H3.1 PASS 3/3) and, in an extension experiment (pre-registered), also with 4 tags (B) and with 2 tags (C) (H-E2.1
> PASS 3/3 in each; live lap 5 ÷ lap 1 0.15–0.46). With 4 and with 2 tags, the live and the hindsight errors with
> re-identification were lower than without it on every flight (H-E2.2 and H-E2.3 PASS 3/3 in each of B and C).
> Condition D (tag 0 only) is the known-map one-tag case: its verdicts also PASS 3/3, but it makes no claim about
> unknown landmarks. The predicted ordering of lap-5 error with tag density did not hold at its first step (P-E2.5
> FAIL), so no monotone tag-density claim is made.

**Supporting results** (`e2_results.md` §1–§2; `scores/E2_verdicts.json:criteria`, `P-E2.5`):
- **H-E2.1 (PRIMARY):** PASS 3/3 in B, C and D (9/9). The LC live lap-5/lap-1 ratios run from 0.15 to 1.35. The
  largest, 1.35 on T_D_r3, is the D boundary case.
- **H-E2.2, H-E2.3, P-E2.4:** PASS 3/3 in each of B, C and D. LC live ÷ no-LC live is 0.13–0.41.
- **P-E2.5 (graded, one check): FAIL.** The mean LC live lap-5 RMSE is A 0.0317, B 0.0238, C 0.0492 and D 0.0687 m:
  A ≤ B is false, while B < C < D. n = 3, so no reason for B < A is claimed.
- **Comparison with the known map (DESCRIPTIVE).** In B and C, E2 LC live is 1.25–2.43× the known-map FGO live.

**Caveats.**
- D's verdicts are reported, but D is not evidence about unknown landmarks.
- E2 uses all central detections in `/tags/raw`, while Experiment 2 uses `/tags/sent`, so the known-map comparison is
  descriptive.
- C2 applies here too: the result assumes correct ids.

**Where else the wording would need to change (NOT edited):**
- `docs/thesis/tables/R1_hypothesis_scorecard.md:37` (H3.1).
- `docs/thesis/tables/T1_scorecard.md:12` (the FGO cell, "PASSED") and `:38` (footnote [h]).
- `docs/thesis/figures_thesis/index.md:213`.
- `docs/thesis/summary/index_summary.md:176`.
- Frozen: claims row 23 (`headline_claims_before_after.md:38`) and `numbers.md` §16.3.

## C4. The 0.25 s window choice (budget part scoped; accuracy part restated as a null result, E4)

**Old wording (verbatim).**
> "**0.25 s selected as the largest window meeting that budget** (0.5 s = 48 ms is over)." — `METHODOLOGY.md:708-709`
> "**The FGO meets the 33 ms deployability budget ONLY in its short-window (0.25 s) configuration — a real result, not a footnote:**" — `METHODOLOGY.md:720-721`
> "larger windows spend compute for no accuracy gain." — `METHODOLOGY.md:722-723`
> "It is the largest window that met the 33 ms deployability budget" — `docs/thesis/methodology_factsheets/3.3_estimators.md:66`
> "The window-sweep ATEs (M:L701), which are the evidence that ATE does not depend on the window, are pre-correction, receipt-stamp values and are listed in the superseded section." — `docs/thesis/numbers.md:457-458`

**Status.**
- **Budget part: too strong / not general.** It rests on the corridor sweep of 96 / 48 / 27 ms, which is DIAGNOSTIC and
  pre-thread-fix (`numbers.md:444`). In E4, on the room world, run serially after the fix, W = 0.5 s also fitted the
  budget on 12/12 flights (descriptive under P-E4.2). The old wording is not refuted for the corridor. It does not
  transfer to the room world. Step time is world-dependent.
- **Accuracy part: without current support until E4.** The "no accuracy gain" evidence is superseded
  (`numbers.md:457-458`). E4 now gives a pre-registered null result on the 12 Experiment 2 flights. It is not a proof
  that accuracy is independent of the window.

**Proposed new wording.**
> The fixed-lag window of 0.25 s is a declared configuration choice. In the corridor window sweep (DIAGNOSTIC,
> measured before the thread-limit fix) it was the largest window under the 33 ms budget. In an extension experiment
> (pre-registered) on the 12 Experiment 2 flights, the median step time rose strictly with the window on every flight
> (P-E4.1 PASS 12/12). It was within the budget at 0.25 s and over it at 1, 2 and 5 s on 12/12 flights (P-E4.2 PASS);
> 0.5 s also fitted (descriptive). A longer window did not improve live accuracy at the registered count (H-E4.3 FAIL
> 7/12, a null result), and it recovered almost none of the gap between the live track and the whole-flight batch
> (descriptive). This supports the 0.25 s choice on the room world at a far lower compute cost.

**Supporting results** (`e4_results.md` §1, §3–§4; `scores/E4_verdicts.json`):
- **P-E4.1:** PASS 12/12.
- **P-E4.2:** PASS, 12/12 at each of 0.25, 1, 2 and 5 s, on both median readings (D13).
- **Median step after the anchor (DIAGNOSTIC: workstation Python, 1 thread, nice 19, serial):**
  - 14.35–15.13 ms at 0.25 s;
  - 26.86–28.22 ms at 0.5 s (inside the budget on 12/12, descriptive);
  - 278.25–303.36 ms at 5 s.
- **H-E4.3:** FAIL 7/12 (band ≥ 10/12: judgement, not derived from data).
  - The five failing flights are higher at 5 s by +0.0000020 to +0.0003395 m.
  - All three D flights are lower at 5 s, which is a descriptive observation from three flights.
- **Gain fraction F(W), pooled (DESCRIPTIVE):** 0.01 / -0.00 / 0.02 / 0.02 at W = 0.5 / 1 / 2 / 5 s.

**Caveats.**
- The room world, not the corridor.
- A FAIL of a directional hypothesis does not show equality. The A and B flights are flat in W to a few tenths of a
  millimetre, while the D flights move both ways.
- Iteration counts were not logged.

**Where else the wording would need to change (NOT edited):**
- `METHODOLOGY.md:708-712` and `:720-723` (forward pointer only).
- `docs/thesis/methodology_factsheets/3.3_estimators.md:66`: scope "largest window" to the corridor sweep.
- Frozen: `numbers.md:444` and `:457-458` (erratum route only, if at all).
- The user's decision is asked in open point 3 (`open_questions.md` Q2).

## C5. The 2-iteration LM cap is converged: scope widened (E4)

**Old wording (verbatim).**
> "verified against full-LM at 0.25 s — max position difference 0.11 m" — `METHODOLOGY.md:723-724`
> "Against full LM, the cap changes position by at most 0.11 m, RMS 0.029 m (numbers.md:452)." — `docs/thesis/methodology_factsheets/3.3_estimators.md:64`

**Status.** **Too narrow; it holds as worded.** It was verified at 0.25 s on one corridor bag only.

**Proposed new wording (an addition).**
> In an extension experiment (pre-registered), cap 2 was also compared with cap 10 at every window from 0.25 to 5 s on
> two room flights (T_A_r1, T_D_r1). No convergence flag was raised: the largest RMS reading was 0.0009 m, against the
> 0.029 m threshold.

**Supporting result.** This is the E4 convergence check (`e4_results.md` §3, "LM cap 2 vs cap 10"; decision D12). It is
a qualifier on H-E4.3, not a hypothesis with a verdict: no flag at any window, 10/10 cap-10 runs.

**Caveat.** Cap 10 is not full LM. The FGO stats did not log LM iteration counts, so "converges within two iterations"
is inferred from wall time only.

**Where else the wording would need to change (NOT edited):**
- `docs/thesis/methodology_factsheets/3.3_estimators.md:65`.
- `docs/thesis/tables/methods_estimator_design.md:10` (optional).
- Frozen: `numbers.md:452`.

## Claims unchanged but checked

- **Experiment 3 values** (claims row 23; `numbers.md` §16.3). E3's serial 0% pair reproduced the stored LC `live.tum`
  and `hindsight.tum` byte for byte, and G0-L is byte-identical. The verdicts and magnitudes are unchanged. Only the
  scope wording changes (C2, C3).
- **Experiment 2 (known tags)** (claims rows 17 and 18; T1, R4 and T8 rows):
  - G-E4 made the 0.25 s FGO live tracks byte-identical on 12/12 flights.
  - V-E5a reproduced the stored UKF byte for byte.
  - No Experiment 2 verdict or value changes.
  - The E5 secondary direction (S-E5.5, S-E5.6) matches the Experiment 2 descriptive ordering, but it is a different
    estimator and adds no ordering claim to Experiment 2.
- **H2.1, the FGO hindsight gain grows with the gap** (`R1_hypothesis_scorecard.md:32`). Unchanged. E4's gain fraction
  is consistent with it, which is descriptive.
- **The tag module's "0 wrong ids"** (`numbers.md:597`). Unchanged. That is a measured property of the detector in the
  hold world. E3's rates are injected.
- **FGO step times on the corridor** (`numbers.md` §14) and the closed-loop real-time statement
  (`tables/realflight_compute.md:13`). Unchanged. E4 is offline and on another world.
- **V3 / V-L withdrawn** (claims row 24). Unchanged. No extension experiment re-scores it.
- **Experiments 4 and 5, the corridor and the closed loop.** No extension experiment touches these.
- **`numbers.md` Errata** (below `## Errata`, read only). A search for loop closure, FGO capability, window, LM and
  §16.3 found no erratum that concerns C1–C5. The single "window" hit (`numbers.md:1449`) is the blank-floor flow-loss
  window. So no erratum changes any old wording quoted here.

## Open points

1. **Robust arm wording (D16).** The instruction's example ("while the robust arm does") would say that the robust
   variant keeps the loop-closure advantage. No registered criterion tests that. Its live error ends above the no-LC
   live on some runs, so C2(b) states only what P-E3b.1, P-E3b.2 and the descriptive values support. The user may
   rule otherwise.
2. **C2 as a limitation.** `limitations.md` holds only ruled items. Should "loop closure assumes correct
   re-identification; the plain FGO is not robust to 1% wrong ids" be added? That needs a ruling (`open_questions.md`
   Q3).
3. **C4 restatement** (`open_questions.md` Q2). Should the factsheet and METHODOLOGY "largest window" wording be scoped
   to the corridor sweep, given that 0.5 s also fits the budget on the room world?
4. **T1 scorecard, Experiment 3 row.** Should the UKF cell stay N/A (the thesis UKF), with a footnote to the E5 variant,
   or name the variant? This is a structural choice for the user (D17).
5. **S-E5.6 maps "batch" to the iSAM2 hindsight**, not an LM batch. Any thesis sentence on E5 hindsight must say so.
6. **P-E4.2 json.** `scores/E4_verdicts.json` `P-E4.2.per_window."0.5"` shows "0/12", meaning 0/12 flights above 33 ms.
   It was not regenerated (stage 2f handover).
7. **Not diagnosed.**
   - The robust run T_A_r2 5% s1 collapse, which is a suspected local minimum.
   - The D-flight window effect in E4.
   - LM iteration counts.
