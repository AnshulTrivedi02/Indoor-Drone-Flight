# Handover: attribution ablation, Step 0 (2026-10-24)

**Stage:** Step 0 only, READ-ONLY. Nothing was replayed or simulated, and no estimator code was changed. The ablation is
EXPLORATORY. The pre-registration is a **DRAFT awaiting the user's sign-off. Do not run anything before that.**

## What was produced (`docs/thesis/ablation/`)

- `step0_report.md`: answers to Step 0 items 1–4, with file:line for every code claim (code pinned at `2683ab4`; GTSAM
  from the 4.2.1 source tarball), the verified gap values, the cost table, the locked constants, "Needs code: stopped",
  and open questions Q1–Q6.
- `preregistration_draft.md`: rungs r0–r7 with exact commands, output roots, metric, noise band, P1–P3 with pass rules,
  the interpretation table, scheduling, checks, and the limitations. Marked DRAFT — NOT SIGNED OFF — DO NOT RUN.
- `ablation_numbers.md`: structure only, every section labelled EXPLORATORY, no values.
- `score_ablation.py`: a read-only scorer (analysis code). It reuses `eval/three_way_eval.py`'s cruise window and
  `evo_ape -a`, for any output root. Its gate `--gate` gave **24/24 EQUAL** against the stored phase4 values
  (`scorer_gate.json`).
- `check_step0.py`: verifies every quoted number, json key, file:line quote (repo at the pinned commit, GTSAM tarball,
  logs) and the cost arithmetic, then runs the numbers.md freeze check. **238 passed, 0 failed.** One deliberate
  mutation of the report made it fail, as it should.
- `machine_step0.txt`: `free -g` / `nproc` at Step 0.
- Decisions D28–D35 appended to `docs/thesis/tier1/decisions_log.md`. They are the "decisions_log D28" series, distinct
  from the earlier METHODOLOGY "D28".

## Key findings

1. **Knobs without code:**
   - window (`argv[2]`; the CLI default is 1.0, so always pass 0.25);
   - LM cap (`argv[3]`);
   - a one-keyframe window (any W < 1/30 s; it works as a two-keyframe iterated filter);
   - `F_ROBUST` on the heading factor only, which also removes the heading χ² gate;
   - `F_BATCH`.

   Need code: keyframe rate (hard-coded 1/30 s), LM tolerances, iteration logging, robust loss on any other factor,
   gate-kept Huber, a clean batch without the yaw-cap anchors.
2. **Marginalisation:** a marginal prior IS carried forward, as `LinearContainerFactor`s frozen at their creation
   linearisation point. Inferred from the code: the FEJ "enforceConsistency" branch is inert in 4.2.1, because
   `linearValues_` is never filled.
3. **Gaps:** the user's values match `numbers.md:291-292,294-295,299` exactly. Scope notes: all six bags are
   checkerboard-floor; the plain-wall heading failed Phase 3 there; the plain-wall margin is fragile to the initial yaw σ.
4. **Cost:** the ladder is 13.9 h serial (upper bound); the full batch would add 9.9 h, so it is not cheap and not run
   by default.
5. **E4** answered the window and cap question for the room without heading only. The with-heading, below-0.25 s,
   one-keyframe-iteration and robust rungs are new.

## Next stage (only after the user signs off)

1. Apply the user's answers to Q1–Q6 to the draft. Copy it to `preregistration.md` (signed, dated) and commit it before
   any run.
2. Write the serial driver under `~/thesis_data/ablation/`, in the stage2f style, NOT `eval/run_jobs_resumable.sh`
   (its state dir is guard-covered).
3. Run the pre-run checks (prereg §9), then r0 and the identity gate (12/12 byte-identical, else STOP), then the
   remaining rungs.
4. Score with `score_ablation.py`, fill `ablation_numbers.md`, give the verdicts, verify, and commit when nothing is
   running.

## State at hand-off

- Nothing running; no FLIGHT_LOCK.
- `~/thesis_data/ablation/` does not exist yet.
- `numbers.md` is untouched (`tools/check_numbers_frozen.py` exit 0).
