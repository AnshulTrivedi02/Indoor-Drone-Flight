# Correction attribution study: STOPPED, PARTIAL results (2026-10-10)

Stage agent, worktree branch `worktree-agent-aa585d74c0d14c66b`, from `fwd-camera` ef7a0a5. Rulings: METHODOLOGY
"RULING (user, 2026-10-09): correction ATTRIBUTION study" and "RULINGS (user, 2026-10-10)", item 12.

**Status: STOPPED by the user and NOT to be resumed.** 27 of the 64 planned replays finished. They cover the plain-wall
divergence, the O FGO batch and fwdc_tex_r1 FGO +heading fully (all four cells each). The dsn UKF/FGO cells and the
fwdc UKF cells were not run. **Every number below is PARTIAL, DIAGNOSTIC, and n = 1–3 bags.**

No simulator was run. No trial directory was written: `find ~/thesis_data/trials -newer <start marker>` is empty.
Every replay ran through `heavy.py`: one 3-job pilot, then one batch. The bags were read from sha256-checked scratch
copies (`zstd -d`, compared with `PACKED.txt`), so no original was unpacked or repacked. The O bags are stored unpacked
and were read in place. Outputs went to scratch (`UKF_OUT_ROOT` / `FGO_OUT_ROOT`). Before each heavy step, no flight
was running. At the stop: the batch's `xargs` was SIGTERMed and its runner SIGSTOPped, so BUILD_LOCK stayed held until
the 6 in-flight jobs had exited. The runner was then continued; it logged `STOPPED 27/64` and released the lock.

## 1. Toggles (OFF by default; diagnostic only, never in results)
| env | file | reverts |
|---|---|---|
| `ATTRIB_UKF_RAW_DEROT=1` | `ukf_replay.py`, `room_ukf_replay.py` | derotation correction (600b1d1): raw gyro average, no bias subtraction |
| `ATTRIB_UKF_OLD_JITTER=1` | `ukf_core.py` `_sigma_points` | jitter correction (47de1ca): 1e-12·I on every call, eigen-clip on failure |
| `ATTRIB_FGO_OLD_BINIT=1` | `fgo/fgo_core.py` `make_pim_params` | noise correction (2544585): `biasAccOmegaInt` = diag(0.2²×3, 0.043633²×3) |
| `ATTRIB_FGO_UNGATED_CAP=1` | `fgo/fgo_core.py` `keyframe` | yaw-cap gate (8dfb035): the 0.5 rad cap on every keyframe, no gate recursion |

- Each toggle prints an `ATTRIBUTION DIAGNOSTIC` line to stderr. Every toggled job's log carries it (canary checked).
- **Also added, off by default:**
  - `UKF_BAG_ROOT` in `ukf_replay.py`, the counterpart of `FGO_BAG_ROOT`;
  - `--est-root` in `eval/o_score.py`, which reads `room_ukf*`/`room_fgo` from a scratch root. With the flag unset,
    `E = D`, so the code path is unchanged.
- The C++ core is not touched.
- **Cells are named by the corrections APPLIED**, not by the toggles set:
  - UKF: `U_none`, `U_derot`, `U_jitter`, `U_both`;
  - FGO: `F_none`, `F_noise`, `F_cap`, `F_both`.
- `eval/attribution/make_jobs.py` → `attrib.jobs` (64 jobs);
  `eval/attribution/score.py` → `eval/results/attribution/attribution_partial.json`;
  `eval/attribution/table.py` → `attribution_partial_tables.md`.
- `score.py` uses `three_way_eval`'s own `cruise_window` / `crop` / `evo_ape_a`, because `--est` cannot read scratch.
  Run on the stored outputs alone, it reproduces every stored evo -a (cruise) value exactly (dsn, extra and phase4 JSONs)
  and the `f1_test.json` FGO_hard row of fwdplainc_tex_r1.

## 2. Default unchanged: byte-identity proof (PASS)
**Toggles unset (`*_both`) against the stored final re-run output, byte-identical** on `*_traj.tum`, `ground_truth.tum`,
`bgz_series.txt`, `fwd_stats.json`, and `metrics.txt` without the FGO's `step_*` wall-clock lines. The FGO TUMs for the
O bags are also byte-identical. `timing_and_fwd.npz` holds wall-clock times and is excluded.

| run | `both` vs stored final | `none` vs archived pre-final (`~/thesis_data/pre_final_trials`) |
|---|---|---|
| dsn_tex_r1 UKF | IDENTICAL | not run |
| dsn_tex_r1 FGO | IDENTICAL | not run |
| dsn_tex_r2 UKF | not run | **IDENTICAL** |
| fwdc_tex_r1 FGO +heading | IDENTICAL | IDENTICAL |
| fwdplainc_tex_r1 FGO +heading | IDENTICAL | IDENTICAL |
| fwdplainc_trans_r1 FGO +heading | IDENTICAL | IDENTICAL |
| O_r1 / O_r2 / O_r3b room_fgo (live + batch TUM) | IDENTICAL ×3 | IDENTICAL ×3 |

**So the reverts are faithful.** With both corrections reverted, every comparable archived pre-final output is reproduced
byte for byte. That includes the dsn/fwd FGO outputs of 2026-09-30 and the dsn UKF of 2026-10-01. The estimator commits
between those outputs and the corrections therefore did not change these paths. **Each old → new change in the
covered runs comes from the corrections alone.**

## 3. Results (PARTIAL; A and B as named per row; attribution = mean of the two orderings; shares sum to 100 %)
| run (estimator) | metric | none (= old) | A only | B only | both (= final) | ΔA (share) | ΔB (share) | interaction |
|---|---|---|---|---|---|---|---|---|
| **fwdplainc_tex_r1** FGO +heading (A noise, B cap gate) | evo -a (cruise), m | 0.200 | 43.218 | 0.196 | 43.539 | +43.18 (100 %) | +0.16 (0 %) | +0.33 |
| | yaw max, ° | 8.33 | 180.00 | 8.33 | 179.93 | +171.6 (100 %) | −0.03 | −0.06 |
| | headings fused / 6333 | 4981 | 19 | 4981 | 28 | −4958 (100 %) | +4.5 | +9 |
| | bgz mean, °/min | −4.9 | −290.6 | −4.9 | −319.4 | −300.1 (95 %) | −14.4 (5 %) | −28.8 |
| **fwdplainc_trans_r1** FGO +heading | yaw max, ° | 3.62 | 179.99 | 3.62 | 179.99 | +176.4 (100 %) | 0.00 | 0.00 |
| | headings fused / 8420 | 7854 | 18 | 7854 | 19 | −7836 (100 %) | +0.5 | +1 |
| | bgz mean, °/min | −4.9 | +415.1 | −4.9 | +447.1 | +436.0 (96 %) | +16.0 (4 %) | +32.0 |
| | evo -a (cruise), m (blank half diverges in every cell) | 1068.6 | 41.2 | 1070.7 | 36.9 | — | — | — |
| **fwdc_tex_r1** FGO +heading | evo -a (cruise), m | 0.079 | 0.057 | 0.079 | 0.057 | −0.022 (100 %) | 0.000 | 0.000 |
| | yaw max, ° / fused of 9539 / bgz °/min | 2.96 / 9480 / −4.9 | 0.40 / 9184 / −8.2 | 2.96 / 9480 / −4.9 | 0.40 / 9184 / −8.2 | all from the noise fix (100 %) | 0 | 0 |
| **O_r1** FGO hindsight (batch), indoor RMSE, m | | 0.328 | 0.558 | 0.329 | 0.589 | +0.245 (94 %) | +0.016 (6 %) | +0.030 |
| **O_r2** | | 0.332 | 0.555 | 0.332 | 0.590 | +0.240 (93 %) | +0.018 (7 %) | +0.034 |
| **O_r3b** | | 0.330 | 0.554 | 0.330 | 0.588 | +0.241 (93 %) | +0.017 (7 %) | +0.033 |
| O_r1 / O_r2 / O_r3b FGO live, indoor RMSE, m | | 0.975 / 1.008 / 1.172 | 1.110 / 1.187 / 1.257 | 0.821 / 0.843 / 0.935 | 0.828 / 0.859 / 0.893 | +0.07 / +0.10 / +0.02 | −0.22 / −0.25 / −0.30 | −0.13 / −0.16 / −0.13 |

- For the O live track, the two corrections push in opposite directions, so the shares are not meaningful (−49 … +165 %).
  The deltas are given instead.
- The full per-cell metrics (yaw RMS, correct-rejected, lockouts, displacement ratio) are in the JSON.
- On fwdplainc_tex_r1 the gated cap fires 0 of 2019 checks with the old noise (`F_cap`) and 4 of 2019 in the final
  model (`F_both`). The ungated cells add it on all 10097 keyframes.
- The gate alone (`F_cap`) leaves those runs essentially unchanged (evo 0.200 → 0.196 m, yaw max identical).

## 4. Answers
1. **Plain-wall FGO divergence: caused by the NOISE correction (`setBiasAccOmegaInit` → 0), not the yaw-cap gate.**
   - With the noise correction alone, the hard-gated FGO +heading diverges as in the final run on both plain-wall bags:
     - yaw max 180°;
     - 18–19 of 6333/8420 headings fused;
     - bgz −291 / +415 °/min.
   - With the gate alone it is unchanged from the old run.
   - The gate adds only about 5 % to the bias runaway's size.
   - (This is consistent with binit0's own note: the tighter IMU noise made the heading gate stricter, 9480 → 9184
     fused on fwdc.)
   - **Scope:** 2 bags, hard gate only. The robust arm and the r2/r3 bags were not run.
2. **O FGO batch worsening (0.33 → 0.59 m): about 93–94 % from the noise correction (+0.24 m), about 6–7 % from the
   gate (+0.02 m), plus an interaction of +0.03 m.** Same on all 3 flights.
   - The gate on its own does not move the batch (0.328 → 0.329).
   - On the LIVE FGO, the gate is the dominant effect and an improvement (−0.22 to −0.30 m). The noise correction alone
     worsens it slightly.
3. **The 2.5 m non-reproduction of stored `dsn_tex_r2` UKF with derotation off: CONFIRMED to come from the jitter fix
   (by elimination).**
   - `U_none` (raw derotation + old jitter) reproduces the archived `dsn_tex_r2/ukf` **byte for byte**. evo -a (cruise)
     is 2.135 m, against a stored 2.135 m.
   - The derotation handover's fresh run at a966d7d was raw derotation + NEW jitter, i.e. this study's `U_jitter`
     configuration. That run did not reproduce (max 2.53 m).
   - The only difference between the two is the jitter rule.
   - The `U_jitter` cell itself was not re-run here.
4. **dsn_tex_r6 confirmatory flip (FGO 1.43 m): NOT ANSWERED.** Its jobs never ran.

**What this cannot say:**
- the split of the dsn UKF and FGO changes (r1–r3, r6) between their corrections;
- the fwdc UKF heading improvement (0.61 → 0.13 m);
- the fwdc FGO baseline arm;
- anything about plain-wall bags other than tex_r1 and trans_r1, or about the robust arm.

## 5. Coverage (`~/thesis_data/batches/attrib_2026-10-10/`, copied to `eval/results/attribution/batch_jobs.log`)
- **DONE (27):**
  - all 4 FGO cells on O_r1, O_r2 and O_r3b (12);
  - fwdplainc_tex_r1 and fwdplainc_trans_r1 heading (8);
  - fwdc_tex_r1 heading (4);
  - pilot: `F_both` dsn_tex_r1, `U_both` dsn_tex_r1 and `U_none` dsn_tex_r2.
- **NOT RUN (37):**
  - FGO fwdc_tex_r1 baseline;
  - FGO dsn_tex_r1/r2/r3/r6, the remaining cells;
  - every UKF cell except the two pilot cells.
- **Not to be resumed (user ruling).** For the record: the same command
  (`heavy.py … run_batch.sh eval/attribution/attrib.jobs attrib_2026-10-10 6`, from this worktree) would skip the DONE
  jobs. Its scratch bag copies are not kept.

## 6. Files
- **Committed:**
  - the toggles in `src/estimators/{ukf_core,ukf_replay,room_ukf_replay}.py`, `src/estimators/fgo/fgo_core.py` and
    `eval/o_score.py`;
  - `eval/attribution/` (job generator, job list, scorer, table maker);
  - `eval/results/attribution/` (JSON, tables, batch log);
  - this handover.
- **Scratch only:** the replay outputs (`…/scratchpad/attrib/out/`). The bag copies are deleted.
