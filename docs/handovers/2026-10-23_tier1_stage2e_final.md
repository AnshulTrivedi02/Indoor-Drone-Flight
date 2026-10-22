# Handover (FINAL): extension experiments, Stage 2e (E3), 2026-10-23

**Stage 2e is complete. All 39 registered E3 runs completed, were scored and have verdicts; the guard verify is
IDENTICAL.** Nothing is running. Next stage: E4 (strictly one job at a time; not part of this stage).

## Commits

| commit | what |
|---|---|
| `5f485e6` | User rulings R1–R4, committed before any run of this segment. `preregistration.md` §2.3 has the R2 terminology clarification, with the old text marked superseded; §2.4 has the runtime-pair clarification. A METHODOLOGY entry was added. `numbers_tier1.md` got 3 deviation rows (the parallel batch in one `heavy.py` call; the 0% pair plus an extra timing-only arm (a) run; the verdict rule). The stage scripts were updated: `e3_verdicts.py`, `crosscheck.py` and `make_tables.py` for R2; `serial_pair.sh` for the 0% pair; `par_order.txt` to 32 runs; job `e3a_T_A_r2_0`. The pair and the 32 batch runs recorded this commit. |
| `6e7a3e7` | The P-E3b.1 clarification of R2 (user ruling 2026-10-23, before any scoring). If only arm (a) diverged, the run is SATISFIED, flagged, with no ratio. Covered by `preregistration.md` §2.3, METHODOLOGY, a deviation row, and the script updates (mock-tested). It also commits the batch records. |
| (this commit) | Scores (`scores/E3*.json`), `E3_verdicts.json`, `e3_results.md`, `numbers_tier1.md` §E3 and §Guard, the guard verify report, the stage records and this handover. |

Runs 1–6 recorded `cb713d3`. `src_dirty` is empty for all runs.

## What ran

- **Serial 0% pair on T_A_r2, alone on the machine.**
  - Arm (a) `e3a_T_A_r2_0` (extra, timing-only; `tier1/T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7/`): `wall_s` 153.5 s.
    Its .tum files are **byte-IDENTICAL** to the stored `trials/T_A_r2/lc_fgo_lc_t245`.
  - Arm (b) `e3b_T_A_r2_0`: 121.2 s.
  - Ratio 0.79 (DESCRIPTIVE).
- **Parallel batch.** 32 runs at width 4, from 2026-10-23 00:08 to 06:55 AEDT. All had rc 0 on try 1, with no REFUSED
  and no re-run. Records: `stage2e/par_timing.tsv` and `stage2e/par_status.tsv`.
- **Status (run_status.py on all 39 runs → `stage2e/status_all.tsv`).** 6 are FAILED-ESTIMATOR: arm (a) 1% seeds 1 and 2 on
  T_A_r1, r2 and r3. The other 33 are OK. The 4 new failures were triaged during the batch (`stage2e/triage.md`): in
  each, a wrong-id event comes first, then a live jump, then the excursion, then the exception. That is divergence, not a
  harness bug.

## Verdicts

The sources are `scores/E3_verdicts.json` and `e3_results.md` §2.

| criterion | verdict | count | divergence |
|---|---|---|---|
| H-E3.1 (PRIMARY) | FAIL | 0/9 | 2 of 3 per flight |
| H-E3.2 | FAIL | 0/9 | 2 of 3 per flight |
| H-E3.3 | FAIL | 3/9 | 2 of 3 per flight |
| P-E3.4 | FAIL | 0/9 | 2 of 3 per flight |
| P-E3.5a | FAIL | 0/9 | 0 |
| P-E3.5b | FAIL | 0/9 | 0 |
| P-E3.5c | PASS | 9/9 | 0 |
| P-E3.6 | FAIL | 0/3 | 2 of 6 per flight |
| P-E3b.1 1% | PASS | 9/9 | 6 SATISFIED, flagged ((a) diverged, (b) OK) |
| P-E3b.1 5% | PASS | 9/9 | 0 |
| P-E3b.2 | PASS | 3/3 | 0 |

**Divergence times** (onset is the headline; first exception in brackets):

| run | onset (s) | first exception (s) |
|---|---|---|
| T_A_r1 1% s1 | 49.699 | 52.432 |
| T_A_r1 1% s2 | 59.699 | 63.832 |
| T_A_r2 1% s1 | 61.795 | 62.595 |
| T_A_r2 1% s2 | 59.928 | 60.695 |
| T_A_r3 1% s1 | 56.248 | 60.548 |
| T_A_r3 1% s2 | 60.314 | 65.614 |

**Effective rates.** Pooled 1%: 0.97% among eligible, 0.71% overall. Pooled 5%: 4.91% among eligible, 3.58% overall.

## Checks

- **Exact cross-check:** `stage2e/crosscheck.py` → `crosscheck.out`, rc 0, 0 mismatches.
- **Guard verify:** IDENTICAL, exit 0, 13,253 files (`frozen_manifest_20261022T002851_verify_stage2e_20261023T065711.json`).
- **Frozen numbers:** `check_numbers_frozen.py` passes.
- **Scorer survival dry run** before scoring (`stage2e/dryrun_scorer_check/`): `l_score.py` handles the diverged runs
  (inf/NaN). It is not a registered score.

## Open

- **Map collapse.** The non-diverged arm (a) runs end at 3.7–4.2 m LC live, with a collapsed landmark map. That reading is
  descriptive, from `landmarks_final`, and was not diagnosed by counterfactual.
- **The robust arm is not always protected.** Robust T_A_r2 5% s1 also ended at 4.18 m.
- **Mechanism inferred.** The four new divergences were triaged against the T_A_r1 mechanism, not re-diagnosed by
  counterfactual.
- **Parallel slowdown** (observation only). Each non-diverged arm (a) job ran about 3.6× slower at 1%, and about 1.6–2.1×
  slower at 5%, than serial. These are cross-flight comparisons.
