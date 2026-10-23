# Handover (FINAL): extension experiments, Stage 2f (E4 live window sweep), 2026-10-24

**Stage 2f is complete.** All 58 registered E4 runs completed and were scored, and every verdict is in. Both guard
verifies are IDENTICAL. Nothing is running.

## Commits

| commit | what |
|---|---|
| `2eb6852` | Made before the first job: the driver, the job scripts, `run_status.py`, `projection.py`, decisions D10–D15, the Stage 2f deviation row, the pre-run guard verify, and the 12 W = 0.25 s scores (12/12 equal the stored `expT` FGO live RMSE). Every E4 run records this commit, with empty `src_dirty`. |
| (this commit) | Scores (`scores/E4_*.json`, `E4_verdicts.json`), `e4_results.md`, `numbers_tier1.md` §E4 and §Guard, the post-run guard verify report, the stage records (`docs/thesis/tier1/stage2f/`) and this handover. |

## What ran

- **Mechanism:** strictly one `heavy.py` job at a time (D1), via the serial driver `~/thesis_data/tier1/stage2f/driver.sh`.
- **Order:** flight-major with W ascending (D10), then LM-10 on T_A_r1 and then T_D_r1.
- **Timing:** 2026-10-23 11:28 to 2026-10-24 04:33 AEDT.
- **Outcome:** 58/58 completed on try 1 (rc 0), with no re-run, no crash, no timeout and no NOT RUN. All 58, plus the 12
  Stage 2a 0.25 s runs, are status OK: 0 keyframe failures and all values finite.
- **Lock projection:** first logged after the first 5 s run, with an end time of about 2026-10-24 16:19 AEDT. It never came
  close to the lock. The progress message was sent to the coordinator after the first 5 s run.
- **Per-window wall times:** see `e4_results.md` §3. The 5 s means were 2,645.2 s at cap 2 and 2,701.2 s at cap 10.

## Verdicts

| criterion | verdict | count |
|---|---|---|
| P-E4.1 (median step after the anchor strictly increasing with W) | PASS | 12/12 |
| P-E4.2 (≤ 33 ms at 0.25 s; > 33 ms at 1, 2 and 5 s; both median readings) | PASS | 12/12 at each |
| **H-E4.3** (live RMSE at 5 s < at 0.25 s, ≥ 10/12) | **FAIL** (null result) | 7/12 |

- **Step time:** the median step after the anchor is 14.35–15.13 ms at 0.25 s and 278.25–303.36 ms at 5 s.
- **H-E4.3:**
  - The five failing flights are higher at 5 s by +0.0000020 to +0.0003395 m.
  - All three D flights are lower at 5 s.
  - Scored as worded on the unrounded values. No claim goes beyond the verdict.
- **Gain fraction (DESCRIPTIVE):** pooled F = 0.01 / -0.00 / 0.02 / 0.02 at W = 0.5 / 1 / 2 / 5 s; per condition, see
  `e4_results.md`. A longer window recovers essentially none of the live-to-batch gap.
- **LM convergence:** no flag at any window on T_A_r1 or T_D_r1. The largest RMS reading is 0.0009 m, against the 0.029 m
  threshold. Cap 10 cost about the same wall time as cap 2.

## Checks

- **Exact cross-check and prose check:** `stage2f/crosscheck.py` → `crosscheck.out`, rc 0, 0 mismatches. It recomputes every
  value independently from `stats.json`, `fgo_live.tum`, the tag_score jsons, the stored `expT` and `timing.tsv`, and
  matches the exact strings in `e4_results.md`, `numbers_tier1.md` and this handover.
- **Guard:** `verify` before the first job and after the last both returned IDENTICAL, exit 0, 13,253 files.
- **Frozen numbers:** `check_numbers_frozen.py` passes.

## Decisions

- **D10–D15** were all taken before the first job: order, hang guard, convergence metric, P-E4.2 median reading,
  failed-run rule, and lm10 naming. No decision was needed after any result was read.
- **No STOP condition arose,** and nothing was added to `open_questions.md`.

## Open

- **Descriptive only, not diagnosed.** On T_D_r1 the cap-2 and cap-10 tracks differ by up to about 0.02 m in 3D outside the
  lap window, but by 0.0000 m RMS inside it. The FGO stats did not log LM iteration counts, so "LM converges within two
  iterations" is inferred from wall time only.
