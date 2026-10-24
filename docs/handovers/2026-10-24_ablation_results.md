# Handover: attribution ablation, run and results (2026-10-24)

**Stage:** the signed-off attribution ablation, run and scored. EXPLORATORY throughout. Nothing is running.

## What was done

1. **Step A (commit `41941cf`, before any run):** `docs/thesis/ablation/preregistration.md` = the draft with the
   user's sign-off edits (header "SIGNED OFF by the user 2026-10-24 with edits; committed before any run"; Q1–Q7 table;
   Huber as "robust weighting replacing the heading gate" citing the F1 robust arm `eval/f1_eval.py:2,6,22`,
   `batches/final_rerun/F.jobs:6-11`; full batch NOT RUN; P1 weak-test sentence; converged-rung label; the user's
   interpretation row verbatim; 12/12 byte-identity gate, else STOP). The draft is unchanged. Ruling + D37–D42 in
   `docs/thesis/tier1/decisions_log.md`; METHODOLOGY ruling entry; guard pre-verify IDENTICAL.
2. **Runs:** serial driver under `~/thesis_data/ablation/` (copy in `docs/thesis/ablation/harness/`). First launch
   failed at bag open (bags stored packed): harness bug, fixed with verified copies via `FGO_BAG_ROOT` (D43). Gate PASS
   (12/12 byte-identical, 12/12 scores equal), then 72 more jobs. 84/84 OK, 0 retries, 8.3 h.
3. **Scoring:** `score_ablation.py` per rung (`~/thesis_data/ablation/scores/`), `ablation_results.py` (tables,
   verdicts), results in `docs/thesis/ablation/ablation_numbers.md` only. `check_ablation.py`: 228 passed, 0 mismatches
   (one deliberate mutation made it fail). Guard post-verify IDENTICAL; numbers.md freeze PASS; run code unchanged.

## Results (exploratory)

- P1 FAIL (r1–r3 5/6 via `fwdplainc_tex_r3`, ~0.4 m lower no-heading error at one keyframe; r4/r5 6/6 on the weak
  `fwdc` band), P2 PASS 3/3 (R(r3) 1.01 / 0.97 / 0.98), P3 FAIL (r6 4/6, r7 2/6; plain walls worse without the gate).
- Reading: the with-heading gap on line-textured walls persists at one keyframe and at 1 s / 2 s; iterations do not
  matter (≤ 0.000060 m). Not window, history or iterations; the residual is attributable to the remaining differences,
  which this ablation cannot separate. Qualified by P1.

## Open questions (in `ablation_numbers.md` §5)

Q8 (P1 plain-wall failure: accept qualification or investigate), Q9 (follow-up to separate the remaining
differences needs code), Q10 (whether any of this enters thesis text).

## State

- Nothing running; no FLIGHT_LOCK. `~/thesis_data/ablation/bags/` holds ~19 GB of decompressed bag copies (scratch,
  verified against PACKED.txt); safe to delete when no longer needed (not deleted: the user decides).
- numbers.md, the frozen pack and tier-1 result files untouched.
