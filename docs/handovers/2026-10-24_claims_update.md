# Handover: claims update after the extension experiments (proposal only), 2026-10-24

**Done. Nothing is running.** This stage only wrote documents. No estimator, replay or simulation was run, and no
thesis document, claims table, figure generator, `numbers.md` or frozen pack file was edited.

## What was written

- **`docs/thesis/tier1/claims_update.md`:** the proposal requested by the METHODOLOGY instruction of 2026-10-22
  (commit `3901b58`). It proposes five changed claims:
  - **C1 (E5).** "Loop closure is an FGO capability; the filters have no loop-closure equivalent." The short forms
    (T1 scorecard, F7 caption, summary page 08) are too strong. The thesis EKF3/UKF have no landmark states, but a UKF
    variant with tag landmark states bounds drift: H-E5.1 PASS 3/3, H-E5.2/H-E5.3/P-E5.4 PASS 3/3, and S-E5.5/S-E5.6
    PASS 3/3 (UKF higher than the FGO, the registered direction).
  - **C2 (E3).** The loop-closure result rests on correct ids. The plain FGO's advantage does not survive 1% wrong ids:
    H-E3.1 FAIL 0/9, with 6 of 9 runs diverged. The robust variant diverged on 0 of 21 runs and was no worse than the
    plain FGO (P-E3b.1 PASS 9/9 at each rate; P-E3b.2 PASS 3/3). No claim is made that it keeps the LC advantage
    (D16). The map-collapse mechanism is "consistent with", and descriptive.
  - **C3 (E2).** Loop closure bounds live drift with 4 and 2 tags as well (H-E2.1 PASS 3/3 in each of B, C, D). D is the
    known-map case. P-E2.5 FAIL is kept visible.
  - **C4 (E4).** The 0.25 s window. The "largest window meeting the budget" wording is not general: 0.5 s fits on the
    room world, descriptively. "No accuracy gain" is restated as a null result: H-E4.3 FAIL 7/12, with P-E4.1 PASS 12/12
    and P-E4.2 PASS.
  - **C5 (E4).** The LM cap 2 convergence, widened to every window on two room flights (no flag, 10/10 cap-10 runs).
- **`docs/thesis/tier1/check_claims_update.py`:** the read-only exact check. It covers the verbatim quotes, the verdicts
  against `scores/*_verdicts.json`, and the numbers against their source files, plus a completeness scan for any
  unregistered number.
- **`decisions_log.md`:** D16 (robust-arm wording per the verdicts), D17 (C1 names the UKF variant, not "the filters")
  and D18 (scope-widening results count as changed claims).
- **`open_questions.md`:** Q2 (scope the "largest window" wording) and Q3 (C2 as a ruled limitation).

## Check totals (`python3 docs/thesis/tier1/check_claims_update.py`, rc 0)

| check | total | mismatches |
|---|---|---|
| verbatim old-wording quotes (file:line span) | 15 | 0 |
| verdict checks against the verdict jsons (incl. per-condition E2, per-window P-E4.2, E4 convergence) | 40 | 0 |
| numbers registered and checked (94 tokens + 45 context phrases) | 139 | 0 |
| unregistered numeric tokens (completeness scan) | 0 | — |

**Mutation test (scratch copies only):** each of five deliberate edits made the checker fail. The edits were a changed
value, a changed count, a changed quote word, a changed range end and a changed n.

**Limit of the check:** a value token is matched as a bounded string anywhere in its cited source file, not in its exact
row. The verdicts and counts are checked against the jsons directly.

## Open (for the user)

- D16: the robust-arm wording deliberately falls short of the instruction's example.
- Q2: C4's scoping of "largest window".
- Q3: C2 as a limitation.
- C1: whether the T1 Experiment 3 UKF cell should name the variant (D17, open point 4).
- S-E5.6 compares with the iSAM2 hindsight, not an LM batch.
- The P-E4.2 json shows "0/12" at 0.5 s, meaning 0/12 flights above 33 ms.

## Next

- If the user accepts any proposal, each "where else" list in `claims_update.md` names the files and lines to change.
- Frozen material (`numbers.md`, the claims table, the final results pack) changes only by the erratum route.
