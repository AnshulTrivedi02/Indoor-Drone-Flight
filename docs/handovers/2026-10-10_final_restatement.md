# Handover, 2026-10-10: final re-run, old → new flags verified and the restatement drafted

**Stage:** analysis only. No replays, no heavy jobs, no estimator edits and no data deletion. `numbers.md`,
METHODOLOGY and `rerun_compare.py` were NOT edited.

**Deliverable:** `docs/thesis/final_restatement_draft.md`, a DRAFT for the user's review. It contains:
- every headline UKF/FGO number, old → new, with flags;
- the confirmatory test;
- the bands and counts;
- the contact prediction (post-hoc) and D27 item 3;
- V-L;
- the sensitivity rows;
- the L slowdown;
- 12 ruling questions;
- an appendix classifying all 95 flags.

## Sources
- **Old:** `~/thesis_ws/eval/results_pre_final/` (main checkout, untracked snapshot). For H/O, also
  `~/thesis_data/batches/final_rerun/prescore/`, which is identical for every value read.
- **New:** `eval/results/` at `425e824`.
- **Logs:** `~/thesis_data/batches/final_rerun/` (`d26gate_*`, `core_*`, `final_cl_pred.txt`, `sens_*.txt`,
  `pipeline.log`), `~/thesis_data/batches/final_L/logs/`.
- **Old L logs:** `eval/results_pre_final/expL/logs/`.
- **Scratch scripts** (`a1`–`a16.py`, `flags.py`) are in this session's scratchpad. They are not committed.

## Findings (details in the draft)
1. **Flags:** 95 in total (86 DIRECTION + 9 VERDICT).
   - **88 REAL:** 10 verdict flips; 38 real but carrying no ordering; 1 trivial.
   - **7 ARTEFACT:** the 6.4 transition ratios ×4 and the section 8 per-trial verdicts ×3.
   - **0 unclear.**
   - **Cause of the artefacts.** `rerun_compare.py` reads the superseded pre-re-fly `fwdc_evo`/`fwdplainc_evo`/
     `p1c_evo`/`*_score.json` and hard-coded bands as "old" in sections 6.4, 7 and 8. Proof: the EKF3 values differ
     between those files and the new ones, although every EKF3 gate shows 0 differences.
   - **Corrected values are in the draft (§1.1).** They expose two real, unflagged count changes: fwdc 6/9 → 8/9 and
     fwdplainc 8/9 → 9/9.
2. **New failure:** the corrected FGO with heading and the hard gate diverges in yaw on plain walls (fwdplainc
   textured and transition).
   - bgz runs away (−267 … −480 / +447 deg/min); about 20 headings fused; evo 43 m.
   - The same failure appears as F1/F4 FGO_hard yaw max ~180°.
   - C0 reverses on plain walls.
   - The robust FGO is the best arm there.
   - Mechanism untraced.
3. **Confirmatory test:** d = EKF3 − FGO. Verdict "EKF3 lower" → **"no ordering claimed"** (5/7 negative, mean
   −0.040 m, CI [−0.934, +0.853]). Driven by r6 (FGO 1.43 m).
4. **Verdict flips:**
   - F2 NOT met → MET;
   - F3c (b) TRUE → FALSE;
   - O P-O3 FAIL → PASS (the FGO batch worsened, 0.33 → 0.59 m).
   - Near-flips: F1 (now fails only on a lockout tie, 3 = 3); F3's Δ30 lockout is gone.
5. **H:** the shadows now drift at EKF3's scale (30 s loss: UKF 0.27–0.29 m → 3–25 mm).
6. **The P4 FGO textured band is degenerate:** [−0.614, 7.017] m.
7. **Contact prediction (post-hoc, n = 8 of 10):** the walls split 4 west / 3 east / 1 none. The registered window
   still scores U3 PASS for the flown +169.9 s.
8. **D27 item 3 (FGO, `_v3`):** predicted σ at the gate is a median 0.57° (window median, not per-heading), so the
   per-heading weight is ≈ 1.3 % (was 15.9 %). The UKF side is OPEN.
9. **Sensitivity rows** (`*_final`): all estimators ≤ 0.013 m on textured flights. The old rows were on pre-re-fly
   bags (EKF3 differs too), so they are not like-for-like.
10. **L nolc slowdown:** 1,044–2,996 → 9,868–11,175 s.
    - Graph size, median step and p99 step are unchanged.
    - The excess is in rare steps beyond p99, from about keyframe 3,000–4,000.
    - Cause untraced.

## Open / next
- The user's rulings on the 12 questions (draft §10).
- Only after the rulings: update `numbers.md`/METHODOLOGY. Optionally, fix `rerun_compare.py`'s 6.4/7/8 mapping
  and regenerate.
- The attribution study was not run.

## State
- No flight was running at commit (`pgrep -fa '[a]rducopter'` empty; no `~/thesis_data/FLIGHT_LOCK`).
- No locks were taken.
- The worktree branch was reset to `fwd-camera` `425e824` at the start, because it had been created from the
  unrelated root.
- Committed on the worktree branch; not merged.
