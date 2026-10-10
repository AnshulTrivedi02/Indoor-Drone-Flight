# Handover, 2026-10-10: restatement rulings 1–5 applied; ruling 6 lockout check

**Stage:** doc editing and light analysis only. No replays, no METHODOLOGY or code edits. The worktree branch was reset to
`fwd-camera` `50edcf4` at the start, because it had been made from the unrelated root. Rulings: METHODOLOGY "RULINGS
(user, 2026-10-10): the restatement after the FGO-only re-run". The docs cite them as **"restatement ruling n"**, because
the earlier 2026-10-10 set also has a ruling 3, 4 and 8.

## 1. Rulings 1–5 applied

**`docs/thesis/numbers.md`:** 8 wording rows replaced and 2 rows added. No value changed. The replaced rows are kept
verbatim in a new last block, "Superseded by the restatement rulings (2026-10-10, items 1–5)".
- **Header:** one bullet listing rulings 1–5.
- **§8 `fwdc` / `fwdplainc` (ruling 1):** 7/9 and 7/9, reported as computed, with the extended caveat. The transition band
  is built from FGO runaway ratios on the blank half, so it is uninformative whether wide ([1.41, 49.07]) or narrow
  ([15.91, 19.16]). The flips reflect runaway size, not sensing quality. The §7 band row now points to this caveat.
- **§15.2 F3c (ruling 2):** (b) TRUE, accepted as worded, flagged FRAGILE.
- **§6.6 C0 (ruling 3):** "FGO lower on all 6", margin 0.03–0.06 m.
  - At 0.1 rad the FGO is still lower on all 4 covered heading bags: plain r1 0.174 vs 0.208, r2 0.731 vs 0.747, r3
    5.695 vs 5.705 m; `fwdc_tex_r1` 0.057 vs 0.127 m.
  - The plain-wall margin shrinks to 0.01–0.03 m.
  - `fwdc_tex_r2` and `r3` were not in the check.
  - The row states that C0 is an estimator comparison, not a heading-benefit claim.
- **§6.6, new row (ruling 4): the plain-wall heading benefit is CONDITIONAL and linked to Phase 3.**
  - The 0.1 rad-affected bags are `fwdplainc_tex_r2` and `r3`, both on the **checkerboard floor**.
  - Heading FAILED Phase 3 validation on that floor: 0/3 bags, including r1. Availability was 60.5% and outliers 13.6%,
    because the floor lines outvote the wall junctions. **No heading benefit is claimed there.**
  - The transition floor passed validation (3/3). Its heading-arm yaw barely responds to the 0.1 rad σ: yaw max
    3.92 → 4.76° on r1, unchanged on r2 and r3.
- **§6.6, new row: plain walls over the BLANK floor (validated 3/3), reported separately.** Source:
  `phase4_fwdplainc_arms.json` and `blank_behaviour.json`.
  - **The benefit is in yaw only.** Heading-arm yaw RMS is 0.050–0.052° for the UKF and 0.051–0.053° for the FGO,
    against baselines of 20.7–23.6°. End yaw is ≤ 0.58°, and ~99% of headings are fused.
  - **Position is still not bounded.** At +60 s the error is 51–78 m for the UKF and 137–166 m for the FGO; evo is
    7.5–10.6 km (†).
  - **The 0.1 rad check did not cover the blank floor.** It had no blank-floor bags.
- **§18 sensitivity row:** the Phase 3 link and the C0 result at 0.1 rad are appended.
- **§6.1 standing row (ruling 5):** labelled DESCRIPTIVE ONLY, next to the confirmatory "no ordering claimed" (mean d
  −0.021 m, CI [−0.989, +0.947]).

**`docs/thesis/headline_claims_before_after.md`:** rows 1a, 5, 7, 27, 31, 32 and 34 are re-worded, along with the
header, the counts sentence and the 0.1 rad footer.
- **Counts unchanged:** HOLDS 17 · CHANGED 16 · WITHDRAWN 3 · PENDING 0.
- **Row 5 stays HOLDS.** Its claim is about `fwdc`, which the 0.1 rad check left unchanged. The conditional plain-wall
  content is in its evidence column.

## 2. Ruling 6 check: does the FGO_hard lockout rise affect a stated claim? **No stated claim affected.**

| criterion | uses which lockouts | now (`eval/results`) | 1st re-run (`results_pre_final2`) | verdict |
|---|---|---|---|---|
| F1 decision | UKF_hard vs FGO_robust totals only (plus yaw max ≥ 4/6) | 3 = 3; robust lower yaw max 6/6 | 3 = 3; 6/6 | NOT met (lockout tie), **unchanged** |
| F1 FGO_hard (descriptive, not in the rule) | — | 12 / 11 / 10 = **33** | 5 / 5 / 4 = 14 | not stated anywhere as a claim |
| 2(a) P1 / S1 / S2 | none (yaw max, wrong accepted, cross-track) | 7/12 FAIL, 5/6 PASS, 5/12 FAIL | identical | **unchanged** (the `decision` blocks differ only in the descriptive `lockout_total` FGO_hard, 23 → 61) |
| 2(a) lockout totals (reported, no decision) | descriptive | 6 / 61 / 6 (FGO_hard 8, 18, 9, 14, 12 per plain-wall flight) | 6 / 23 / 6 | already restated in numbers.md §15.1 |
| F3 "at Δ60 both lock out" | F3's own convergence metric (not lockout episodes) | FGO_d60 224.5 / None / 221.5 s, UKF 212.5 / None / 207.0 s | FGO 226.8 / None / 223.0 s | holds; decision False → False |
| P-H7 "no lockout in any loss" | expH `lockout` flags | 0 of 176 lockout flags True | 0 | PASS, **unchanged** |

The cause of the rise is **not traced**, as ruling 6 requires. One older reading is now outdated: METHODOLOGY's 2(a)
RESULT prose says "the hard-gated FGO's ~4% (3)", the lowest lockout count of the three arms. That is reference text,
not a verdict, and numbers.md §15.1 already carries the current totals.

## 3. Daily summary items (restatement ruling 6)

- **FGO_hard lockout rise:**
  - 2(a): 23 → 61 (8–18 per plain-wall flight, against the UKF's 1–2).
  - F1: 14 → 33.
  - Cause untraced. **No stated claim is affected:** F1's rule uses UKF_hard vs FGO_robust (3 = 3), and 2(a)'s
    P1/S1/S2 have no lockout term.
  - The FGO_hard now matches the UKF in yaw: max within 0.03° on 2(a), and 4.59–5.03° on the F1 plain-wall bags.
- **End wall, 2 of 48 wrong headings fused** (> 3°) by the `fwdplainc` FGO with heading:
  - one each on `fwdplainc_trans_r1` (max 4.30°) and `trans_r3` (4.21°); the UKF fused 0/48;
  - the old 0/48 came from the lockout, when the FGO fused only ~20 headings per bag (`phase5_analysis.json`).
- **The r3 sensitivity detail** (`fwdplainc_tex_r3`, checkerboard floor, where heading failed Phase 3 validation):
  - with the initial yaw σ at 0.1 rad instead of 1°, the heading arms go 0.250 / 0.221 → 5.705 / 5.695 m (UKF / FGO);
  - yaw max 4.59 → 61.3°; headings fused 781 / 778 → 232 / 229;
  - the FGO heading arm is then worse than its own baseline (4.85 m);
  - r2 moves less (0.75 / 0.73 m, yaw max 14.5°), and r1 hardly at all;
  - the ordering is unchanged (the FGO is still lower by 0.01–0.02 m).

## State

- Before the commit there was no flight running (`pgrep -fa '[a]rducopter'` was empty) and no
  `~/thesis_data/FLIGHT_LOCK`.
- Committed on the worktree branch; not merged.
- The scratch scripts (`rr_numbers.py`, `rr_claims.py`) are in the session scratchpad and are not committed.
