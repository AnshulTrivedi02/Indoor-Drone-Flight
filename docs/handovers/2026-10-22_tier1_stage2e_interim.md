# Handover (INTERIM, stage held): extension experiments, Stage 2e (E3), 2026-10-22

**Stage 2e is HELD on coordinator instruction, pending rulings. No E3 run has been scored.**
- 6 of 39 runs are done: arm (a) T_A_r1 at 1% and 5%, seeds 0–2.
- 4 diagnosis runs are done.
- Nothing is running. No driver is alive (`stage2e/HOLD.txt`).

## Commits

| commit | what |
|---|---|
| `cb713d3` | §Deviations row (serial driver, score names, effective-rate reporting). The first 6 runs recorded this commit. |
| `3f613f4` | `lc_fgo_replay.py --mislabel-keep` (diagnosis counterfactual, inert when unset) and the timeout deviation row (6 h → 24 h for jobs 3–39). |
| `4729be6` | `preregistration.md` §2.3 "Estimator failure" rule, the METHODOLOGY ruling entry, and copies of the stage scripts in `docs/thesis/tier1/stage2e/`. |

**Runs from now on record a different commit from the first 6.** Report the commit per segment. `src/` changed only by the
inert flag; G0-L re-checked at `3f613f4` gave 4/4 byte-identical (`stage2e/diag/g0l_recheck.txt`).

## Results so far (status only; no scores)

Source: `~/thesis_data/tier1/stage2e/status/<job>.json`, from `run_status.py`.
- **Status rule:** FAILED-ESTIMATOR iff `keyframe_failures` > 0 or a non-finite .tum value.
- **Excursion onset:** the first live row with |x| or |y| > 10 m. It is descriptive only.

| run | status | failures / attempts | first exception (s) | excursion onset (s) | wall (s, driver) |
|---|---|---|---|---|---|
| 1% s0 | OK | 0 / 7351 | — | — | 3090.7 |
| 1% s1 | FAILED-ESTIMATOR | 6634 / 7351 (0.9025) | 52.432 | 49.699 | 80.3 |
| 1% s2 | FAILED-ESTIMATOR | 6292 / 7351 (0.8559) | 63.832 | 59.699 | 111.8 |
| 5% s0 | OK | 0 | — | — | 6389.8 |
| 5% s1 | OK | 0 | — | — | 6207.9 |
| 5% s2 | OK | 0 | — | — | 7000.7 (row added by hand) |

**Diagnosis: genuine divergence.** Each failure is a divergence of the non-robust FGO set off by ONE wrong-id factor.
- **s1:** at 49.402 s a tag-5 detection was relabelled to tag 1, whose landmark already existed.
- **s2:** at 54.253 s a tag-2 detection was relabelled to tag 6. That was the first sighting of id 6, so the new landmark was
  created at the wrong place. The divergence came when the true tag 6 was first seen, at 59.30 s.
- **Counterfactual, one trigger kept:** the failure moved to the next wrong event (`cf_s1` 60.358 s, `cf_s2` 71.97 s).
- **Counterfactual, both triggers kept:** 0 failures on both seeds. `cf2_s1` shows a recovered 20 m excursion at 67.78 s.
- **Ruled out:** a yaw-wrap artefact (the offsets are 10–105°).
- **Downstream, not the cause:** the `map::at` cascade. `isam_keyframe` advances `k` and `lm_key` before `isam.update`.
- **The 5% runs of the same seeds,** which contain these events (nested sets), did not diverge, so divergence is
  path-dependent.
- **Records:** `stage2e/diag/` (jobs, logs, timing, status).

## Rulings needed before the stage can continue

All were sent to the coordinator.
1. Confirm the GENUINE classification. The literal "persists after one counterfactual = harness bug" test would say otherwise.
2. **Aggregation.** Should a FAILED-ESTIMATOR run make H-E3.1 NOT MET (as in §0.5), or count as not satisfying the
   criterion, so that H-E3.1 FAILs? This is open, as is the effect on H-E3.2–P-E3.6 and the arm (b) criteria. It is written
   "pending a ruling" in §2.3.
3. **The serial runtime pair:** proposed T_A_r2 1% s0, (a) then (b), with nothing else running.
4. **The coordinator's SI-units merge gap:** the machine is idle now.

## How to resume (after the rulings; idle check first)

1. Run `bash stage2e/serial_pair.sh` inside one `heavy.py` call:
   `python3 …/heavy.py --wait-s 1800 "tier1 stage2e E3 serial pair" -- bash ~/thesis_data/tier1/stage2e/serial_pair.sh`.
2. Then run `par_batch.sh 4` the same way, inside one `heavy.py` call. That covers 31 runs at width 4 or less. Before this,
   record the deviation: one `heavy.py` lock spans a parallel batch.
   - Each job goes through `one_job.sh`. It refuses if a flight is on, and gives one identical re-run on rc ≠ 0, moving the
     crashed output aside.
   - Results go to `par_timing.tsv` and `par_status.tsv`.
3. Waits must be liveness- and timeout-bounded.
4. Score: `stage2e/score.sh`.
5. Then `e3_verdicts.py`. **It must be updated first** for the aggregation ruling and to carry the FAILED-ESTIMATOR status.
   Currently it judges all runs on RMSE only.
6. Then `make_tables.py` and `crosscheck.py`.
7. Then the guard verify, `e3_results.md`, `numbers_tier1.md` §E3, and the final handover.
8. Runs 1–6 keep their recorded timing. Their wall times were serial, but they are not used for the runtime ratio.
